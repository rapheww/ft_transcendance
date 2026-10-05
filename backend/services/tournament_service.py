"""Single-elimination tournament bracket.

Each match is played as a real Game (see game_service), so this module never
touches chess rules directly. A round only advances once every match in it
has a winner; that check runs on read (get_tournament), not on a timer or a
webhook.

A drawn match is broken by material, then by remaining clock time.
If both are equal, or clocks are unavailable, a draw of lots decides.
"""

import random
from functools import wraps
import chess
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.exceptions.tournament import (AlreadyRegistered,
                                           InvalidParticipantCount,
                                           NotRegistered,
                                           TournamentAlreadyStarted,
                                           TournamentNotFound)
from backend.models.tournament import Tournament, TournamentMatch, TournamentParticipant
from backend.models.game import Game
from backend.repositories.tournament_repository import TournamentRepository
from backend.schemas.tournament import MatchResponse, TournamentResponse
from backend.services import game_service, user_service

# Each tournament player starts with 10 minutes and no increment.
TOURNAMENT_INITIAL_TIME_SECONDS = 600
TOURNAMENT_INCREMENT_SECONDS = 0

_PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


def _rollback_on_error(operation):

    @wraps(operation)
    def wrapped(db: Session, *args, **kwargs):
        try:
            return operation(db, *args, **kwargs)
        except Exception:
            # Business errors must release the row lock too, even when the
            # caller keeps its session open after catching the exception.
            db.rollback()
            raise

    return wrapped


def _is_power_of_two(count: int) -> bool:
    return count >= 2 and (count & (count - 1)) == 0


def _material_value(board: chess.Board, color: chess.Color) -> int:
    return sum(_PIECE_VALUES[piece.piece_type]
               for piece in board.piece_map().values() if piece.color == color)


def _winner_by_material(fen: str, match: TournamentMatch) -> int | None:
    board = chess.Board(fen)
    white_material = _material_value(board, chess.WHITE)
    black_material = _material_value(board, chess.BLACK)

    if white_material > black_material:
        return match.player1_id
    if black_material > white_material:
        return match.player2_id

    return None


def _winner_by_remaining_time(game: Game, match: TournamentMatch) -> int | None:
    white_time = game.white_time_remaining
    black_time = game.black_time_remaining

    if white_time is None or black_time is None:
        return None
    if white_time > black_time:
        return match.player1_id
    if black_time > white_time:
        return match.player2_id
    return None


def create_tournament(db: Session, creator_id: int) -> Tournament:
    user_service.get_user_by_id(db, creator_id)

    repository = TournamentRepository(db)
    tournament = repository.create(Tournament(status="registration"))

    repository.add_participant(
        TournamentParticipant(tournament_id=tournament.id, user_id=creator_id))

    db.commit()

    return tournament


@_rollback_on_error
def register(db: Session, tournament_id: int, user_id: int) -> Tournament:
    repository = TournamentRepository(db)
    tournament = repository.get_by_id_for_update(tournament_id)

    if tournament is None:
        raise TournamentNotFound()
    if tournament.status != "registration":
        raise TournamentAlreadyStarted()

    user_service.get_user_by_id(db, user_id)

    participants = repository.list_participants(tournament_id)
    if any(p.user_id == user_id for p in participants):
        raise AlreadyRegistered()

    try:
        repository.add_participant(
            TournamentParticipant(tournament_id=tournament_id,
                                  user_id=user_id))
        db.commit()
    except IntegrityError as error:
        db.rollback()
        # Another request may have registered this player since our first read.
        participants = repository.list_participants(tournament_id)
        if any(p.user_id == user_id for p in participants):
            raise AlreadyRegistered() from error
        raise

    return tournament


@_rollback_on_error
def start_tournament(db: Session, tournament_id: int,
                     user_id: int) -> Tournament:
    repository = TournamentRepository(db)
    tournament = repository.get_by_id_for_update(tournament_id)

    if tournament is None:
        raise TournamentNotFound()
    if tournament.status != "registration":
        raise TournamentAlreadyStarted()

    participant_ids = [
        p.user_id for p in repository.list_participants(tournament_id)
    ]

    if user_id not in participant_ids:
        raise NotRegistered()
    if not _is_power_of_two(len(participant_ids)):
        raise InvalidParticipantCount()

    random.shuffle(participant_ids)
    try:
        _create_round(db,
                      tournament_id,
                      round_number=1,
                      player_ids=participant_ids)

        tournament.status = "in_progress"
        repository.update(tournament)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return tournament


def _create_tournament_game(db: Session, white_id: int, black_id: int) -> int:
    # Game services commit internally. Bind them to our existing transaction
    # so their commits cannot persist an incomplete tournament operation.
    with Session(bind=db.connection(),
                 join_transaction_mode="rollback_only",
                 expire_on_commit=False) as game_db:
        game = game_service.create_game(
            game_db, white_id,
            initial_time_seconds=TOURNAMENT_INITIAL_TIME_SECONDS,
            increment_seconds=TOURNAMENT_INCREMENT_SECONDS)
        game_service.join_game(game_db, game.id, black_id)
        return game.id


def _create_round(db: Session, tournament_id: int, round_number: int,
                  player_ids: list[int]) -> None:
    repository = TournamentRepository(db)

    for slot, index in enumerate(range(0, len(player_ids), 2)):
        white_id, black_id = player_ids[index], player_ids[index + 1]

        game_id = _create_tournament_game(db, white_id, black_id)

        repository.create_match(
            TournamentMatch(tournament_id=tournament_id,
                            round=round_number,
                            slot=slot,
                            player1_id=white_id,
                            player2_id=black_id,
                            game_id=game_id))


def _resolve_match(db: Session, match: TournamentMatch) -> None:
    if match.winner_id is not None:
        return

    game = game_service.get_game(db, match.game_id)
    db.refresh(game)
    if game.status != "finished":
        return

    if game.result == "1-0":
        match.winner_id = match.player1_id
        return
    if game.result == "0-1":
        match.winner_id = match.player2_id
        return

    winner_id = _winner_by_material(game.current_fen, match)
    if winner_id is None:
        winner_id = _winner_by_remaining_time(game, match)
    if winner_id is None:
        winner_id = random.choice([match.player1_id, match.player2_id])
    match.winner_id = winner_id


def _advance_if_ready(db: Session, tournament: Tournament) -> None:
    repository = TournamentRepository(db)
    matches = repository.list_matches(tournament.id)
    current_round = max(match.round for match in matches)
    round_matches = repository.list_matches_for_round(tournament.id,
                                                      current_round)

    for match in round_matches:
        _resolve_match(db, match)

    if any(match.winner_id is None for match in round_matches):
        return

    winners = [match.winner_id for match in round_matches]

    if len(winners) == 1:
        tournament.winner_id = winners[0]
        tournament.status = "finished"
        repository.update(tournament)
        return

    _create_round(db,
                  tournament.id,
                  round_number=current_round + 1,
                  player_ids=winners)


@_rollback_on_error
def cancel_tournament(db: Session, tournament_id: int) -> None:
    repository = TournamentRepository(db)
    tournament = repository.get_by_id_for_update(tournament_id)

    if tournament is None:
        raise TournamentNotFound()
    if tournament.status != "registration":
        raise TournamentAlreadyStarted()

    repository.delete_participants(tournament_id)
    repository.delete(tournament)
    db.commit()


@_rollback_on_error
def get_tournament(db: Session, tournament_id: int) -> TournamentResponse:
    repository = TournamentRepository(db)
    tournament = repository.get_by_id_for_update(tournament_id)

    if tournament is None:
        raise TournamentNotFound()

    try:
        if tournament.status == "in_progress":
            _advance_if_ready(db, tournament)

        participants = repository.list_participants(tournament_id)
        matches = repository.list_matches(tournament_id)
        response = TournamentResponse(
            id=tournament.id,
            status=tournament.status,
            winner_id=tournament.winner_id,
            participants=[
                user_service.get_user_by_id(db, p.user_id).username
                for p in participants
            ],
            matches=[MatchResponse.model_validate(match) for match in matches])
        db.commit()
    except Exception:
        db.rollback()
        raise

    return response
