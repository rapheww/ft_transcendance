"""Persisted single-elimination brackets, deadlines and organizer permissions."""
import random
from datetime import datetime, timedelta, timezone
from functools import wraps
import chess
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.exceptions.tournament import (
    AlreadyRegistered, InvalidParticipantCount, NotTournamentOrganizer,
    TournamentAlreadyStarted, TournamentExpired, TournamentNotFound)
from backend.models.tournament import Tournament, TournamentMatch, TournamentParticipant
from backend.models.game import Game
from backend.models.user import User
from backend.repositories.tournament_repository import TournamentRepository
from backend.schemas.tournament import MatchResponse, ParticipantResponse, TournamentResponse
from backend.services import game_service
from backend.services.player_availability import assert_available, lock_players

# Ten minutes per player, without increment.
TOURNAMENT_INITIAL_TIME_SECONDS = 10 * 60
TOURNAMENT_INCREMENT_SECONDS = 0
# The organizer must request a start within thirty minutes of creation.
TOURNAMENT_REGISTRATION_TIMEOUT_SECONDS = 30 * 60
# Pause before the first wave and after each completed wave.
TOURNAMENT_ROUND_DELAY_SECONDS = 60

_PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}


def _utc(value: datetime) -> datetime:
    return value.replace(
        tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(
            timezone.utc)


def _rollback_on_error(operation):

    @wraps(operation)
    def wrapped(db: Session, *args, **kwargs):
        try:
            return operation(db, *args, **kwargs)
        except Exception:
            db.rollback()
            raise

    return wrapped


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


def _winner_by_remaining_time(game: Game,
                              match: TournamentMatch) -> int | None:
    white_time = game.white_time_remaining
    black_time = game.black_time_remaining

    if white_time is None or black_time is None:
        return None
    if white_time > black_time:
        return match.player1_id
    if black_time > white_time:
        return match.player2_id
    return None


def _require_organizer(tournament: Tournament, user_id: int | None,
                       api_manager: bool) -> None:
    if api_manager:
        authorized = tournament.organizer_type == "api"
    else:
        authorized = tournament.organizer_type == "player" and tournament.creator_id == user_id
    if not authorized:
        raise NotTournamentOrganizer()


def _check_registration(db: Session, tournament: Tournament,
                        now: datetime) -> None:
    if tournament.status != "registration":
        raise TournamentAlreadyStarted()
    if _utc(tournament.registration_deadline) <= now:
        tournament.status = "cancelled"
        # Persist expiration even though the rejected request returns an error.
        db.commit()
        raise TournamentExpired()


@_rollback_on_error
def create_tournament(db: Session,
                      creator_id: int | None = None,
                      *,
                      api_manager: bool = False) -> Tournament:
    if not api_manager:
        lock_players(db, [creator_id])
        assert_available(db, creator_id)
    now = datetime.now(timezone.utc)
    repository = TournamentRepository(db)
    tournament = repository.create(
        Tournament(status="registration",
                   organizer_type="api" if api_manager else "player",
                   creator_id=None if api_manager else creator_id,
                   created_at=now,
                   registration_deadline=now +
                   timedelta(seconds=TOURNAMENT_REGISTRATION_TIMEOUT_SECONDS)))
    if not api_manager:
        repository.add_participant(
            TournamentParticipant(tournament_id=tournament.id,
                                  user_id=creator_id))
    db.commit()
    return tournament


@_rollback_on_error
def register(db: Session, tournament_id: int, user_id: int) -> Tournament:
    repository = TournamentRepository(db)
    tournament = repository.get_by_id_for_update(tournament_id)
    if tournament is None:
        raise TournamentNotFound()
    _check_registration(db, tournament, datetime.now(timezone.utc))
    lock_players(db, [user_id])
    _check_registration(db, tournament, datetime.now(timezone.utc))
    if any(p.user_id == user_id
           for p in repository.list_participants(tournament_id)):
        raise AlreadyRegistered()
    # Detect duplicates independently of the session's cached participant list.
    if db.query(TournamentParticipant).filter_by(tournament_id=tournament_id,
                                                 user_id=user_id).first():
        raise AlreadyRegistered()
    assert_available(db, user_id)
    try:
        repository.add_participant(
            TournamentParticipant(tournament_id=tournament_id,
                                  user_id=user_id))
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if db.query(TournamentParticipant).filter_by(
                tournament_id=tournament_id, user_id=user_id).first():
            raise AlreadyRegistered() from error
        raise
    return tournament


def _prepare_bracket(db: Session, tournament_id: int,
                     player_ids: list[int]) -> None:
    repository = TournamentRepository(db)
    random.shuffle(player_ids)
    size = 1 << (len(player_ids) - 1).bit_length()
    real_matches = len(player_ids) - size // 2
    first_round = [(player_ids[2 * i], player_ids[2 * i + 1])
                   for i in range(real_matches)]
    first_round += [(player, None) for player in player_ids[2 * real_matches:]]
    random.shuffle(first_round)
    for slot, (player1, player2) in enumerate(first_round):
        repository.create_match(
            TournamentMatch(tournament_id=tournament_id,
                            round=1,
                            slot=slot,
                            player1_id=player1,
                            player2_id=player2,
                            is_bye=player2 is None,
                            winner_id=player1 if player2 is None else None))
    round_number, slots = 2, size // 4
    while slots:
        for slot in range(slots):
            repository.create_match(
                TournamentMatch(tournament_id=tournament_id,
                                round=round_number,
                                slot=slot))
        round_number += 1
        slots //= 2


@_rollback_on_error
def start_tournament(db: Session,
                     tournament_id: int,
                     user_id: int | None = None,
                     *,
                     api_manager: bool = False) -> Tournament:
    repository = TournamentRepository(db)
    tournament = repository.get_by_id_for_update(tournament_id)
    if tournament is None:
        raise TournamentNotFound()
    _require_organizer(tournament, user_id, api_manager)
    now = datetime.now(timezone.utc)
    _check_registration(db, tournament, now)
    players = [p.user_id for p in repository.list_participants(tournament_id)]
    if len(players) < 2:
        raise InvalidParticipantCount()
    _prepare_bracket(db, tournament_id, players)
    tournament.status = "countdown"
    tournament.next_round_at = now + timedelta(
        seconds=TOURNAMENT_ROUND_DELAY_SECONDS)
    db.commit()
    return tournament


def _create_tournament_game(db: Session, white_id: int, black_id: int) -> int:
    return game_service.create_human_game(db, white_id, black_id,
                                          TOURNAMENT_INITIAL_TIME_SECONDS,
                                          TOURNAMENT_INCREMENT_SECONDS).id


def _launch_round(db: Session, tournament: Tournament) -> None:
    tournament.current_round += 1
    matches = TournamentRepository(db).list_matches_for_round(
        tournament.id, tournament.current_round)
    for match in matches:
        if not match.is_bye:
            if match.player1_id is None or match.player2_id is None:
                raise ValueError(
                    "Cannot launch an incomplete tournament pairing")
            match.game_id = _create_tournament_game(db, match.player1_id,
                                                    match.player2_id)
    tournament.status = "in_progress"
    tournament.next_round_at = None


def _resolve_match(db: Session, match: TournamentMatch) -> None:
    if match.winner_id is not None or match.game_id is None:
        return
    game = db.get(Game, match.game_id, populate_existing=True)
    if game.status != "finished":
        return
    if game.result == "1-0":
        match.winner_id = match.player1_id
    elif game.result == "0-1":
        match.winner_id = match.player2_id
    else:
        winner = _winner_by_material(game.current_fen, match)
        if winner is None:
            winner = _winner_by_remaining_time(game, match)
        match.winner_id = winner if winner is not None else random.choice(
            [match.player1_id, match.player2_id])


def _advance_if_ready(db: Session, tournament: Tournament) -> None:
    repository = TournamentRepository(db)
    matches = repository.list_matches_for_round(tournament.id,
                                                tournament.current_round)
    if not matches:
        raise ValueError("Running tournament has no current round")
    for match in matches:
        _resolve_match(db, match)
    if any(match.winner_id is None for match in matches):
        return
    if len(matches) == 1:
        tournament.winner_id = matches[0].winner_id
        tournament.status = "finished"
        tournament.next_round_at = None
        return
    winners = [match.winner_id for match in matches]
    following = repository.list_matches_for_round(tournament.id,
                                                  tournament.current_round + 1)
    # Old tournaments only stored played rounds; build their next wave as needed.
    if not following:
        for slot in range(len(winners) // 2):
            following.append(
                repository.create_match(
                    TournamentMatch(tournament_id=tournament.id,
                                    round=tournament.current_round + 1,
                                    slot=slot)))
    for index, match in enumerate(following):
        match.player1_id, match.player2_id = winners[2 * index:2 * index + 2]
    last_finish = max(
        _utc(db.get(Game, match.game_id).finished_at) for match in matches
        if match.game_id is not None)
    tournament.next_round_at = last_finish + timedelta(
        seconds=TOURNAMENT_ROUND_DELAY_SECONDS)
    tournament.status = "between_rounds"


@_rollback_on_error
def process_tournament(db: Session,
                       tournament_id: int,
                       now: datetime | None = None) -> None:
    tournament = TournamentRepository(db).get_by_id_for_update(tournament_id)
    if tournament is None:
        return
    now = _utc(now or datetime.now(timezone.utc))
    if tournament.status == "registration" and _utc(
            tournament.registration_deadline) <= now:
        tournament.status = "cancelled"
    elif tournament.status == "in_progress":
        _advance_if_ready(db, tournament)
    if tournament.status in ("countdown", "between_rounds") and _utc(
            tournament.next_round_at) <= now:
        _launch_round(db, tournament)
    db.commit()


@_rollback_on_error
def cancel_tournament(db: Session,
                      tournament_id: int,
                      user_id: int | None = None,
                      *,
                      api_manager: bool = False) -> None:
    tournament = TournamentRepository(db).get_by_id_for_update(tournament_id)
    if tournament is None:
        raise TournamentNotFound()
    _require_organizer(tournament, user_id, api_manager)
    _check_registration(db, tournament, datetime.now(timezone.utc))
    tournament.status = "cancelled"
    db.commit()


def get_tournament(db: Session,
                   tournament_id: int,
                   user_id: int | None = None) -> TournamentResponse:
    repository = TournamentRepository(db)
    tournament = repository.get_by_id(tournament_id)
    if tournament is None:
        raise TournamentNotFound()
    participants = repository.list_participants(tournament_id)
    matches = repository.list_matches(tournament_id)
    users = {
        user.id: user
        for user in db.query(User).filter(
            User.id.in_([p.user_id
                         for p in participants])).populate_existing().all()
    }
    games = {
        game.id: game
        for game in db.query(Game).filter(
            Game.id.in_([m.game_id for m in matches
                         if m.game_id])).populate_existing().all()
    }
    eliminated = {
        player
        for match in matches
        if match.winner_id is not None and not match.is_bye
        for player in (match.player1_id, match.player2_id)
        if player != match.winner_id
    }
    return TournamentResponse(
        id=tournament.id,
        status=tournament.status,
        organizer_type=tournament.organizer_type,
        creator_id=tournament.creator_id,
        winner_id=tournament.winner_id,
        created_at=_utc(tournament.created_at),
        registration_deadline=_utc(tournament.registration_deadline),
        next_round_at=_utc(tournament.next_round_at)
        if tournament.next_round_at else None,
        current_round=tournament.current_round,
        participant_count=len(participants),
        participants=[users[p.user_id].username for p in participants],
        participant_details=[
            ParticipantResponse(id=p.user_id,
                                username=users[p.user_id].username,
                                eliminated=p.user_id in eliminated)
            for p in participants
        ],
        matches=[
            MatchResponse(
                round=m.round,
                slot=m.slot,
                player1_id=m.player1_id,
                player2_id=m.player2_id,
                game_id=m.game_id,
                winner_id=m.winner_id,
                is_bye=m.is_bye,
                status="bye" if m.is_bye else
                games[m.game_id].status if m.game_id else "scheduled")
            for m in matches
        ],
        my_game_id=next(
            (m.game_id for m in matches
             if m.game_id and user_id in (m.player1_id, m.player2_id)
             and games[m.game_id].status == "active"), None)
        if user_id is not None else None)


def list_open_tournaments(db: Session) -> list[TournamentResponse]:
    now = datetime.now(timezone.utc)
    ids = [
        tid for tid, in db.query(Tournament.id).filter(
            Tournament.status == "registration",
            Tournament.registration_deadline > now).order_by(
                Tournament.created_at, Tournament.id).all()
    ]
    return [get_tournament(db, tournament_id) for tournament_id in ids]


def get_my_tournament(db: Session, user_id: int) -> TournamentResponse | None:
    from backend.services.player_availability import active_tournament_query
    tournament = active_tournament_query(db, user_id).first()
    return get_tournament(db, tournament.id, user_id) if tournament else None
