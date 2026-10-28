import io
import chess
import chess.pgn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from backend.models.game import Game
from backend.repositories.game_repository import GameRepository
from backend.services import elo_service, user_service
from backend.exceptions.game import (
    CannotPlayAgainstSelf, GameNotFound, GameNotJoinable, GameNotActive,
    NotAPlayer, NotYourTurn, IllegalMove, CannotResignFinishedGame,
    DrawOfferAlreadyExists, NoDrawOffer, CannotAcceptOwnDrawOffer,
    DrawNotClaimable, NotAIGame, InvalidDifficulty, InvalidOpponent)


def _board_from_pgn(pgn: str) -> chess.Board:
    pgn_game = chess.pgn.read_game(io.StringIO(pgn))
    board = pgn_game.board()

    for move in pgn_game.mainline_moves():
        board.push(move)

    return board


def _finish_game(db: Session, game: Game, result: str) -> None:
    if game.opponent_type != "ai":
        game.white_elo_after, game.black_elo_after = elo_service.update_ratings(
            db, game.white_player_id, game.black_player_id, result)
    game.status = "finished"
    game.result = result
    game.finished_at = datetime.now(timezone.utc)


def _update_clock(game: Game, board: chess.Board, now: datetime) -> bool:
    if game.initial_time_seconds is None:
        return False

    if game.last_move_at is None:
        return False

    elapsed = int((now - game.last_move_at).total_seconds())
    if elapsed <= 0:
        return False

    if board.turn == chess.WHITE:
        game.white_time_remaining = max(0, game.white_time_remaining - elapsed)
        return game.white_time_remaining == 0

    game.black_time_remaining = max(0, game.black_time_remaining - elapsed)
    return game.black_time_remaining == 0


def create_game(db: Session,
                user_id: int,
                initial_time_seconds: int = None,
                increment_seconds: int = 0,
                opponent_type: str = "human",
                ai_difficulty: str = None) -> Game:
    if opponent_type not in ("human", "ai"):
        raise InvalidOpponent()
    if opponent_type == "human":
        ai_difficulty = None
    else:
        if ai_difficulty not in ("easy", "medium", "hard"):
            raise InvalidDifficulty()
    try:
        user_service.get_user_by_id(db, user_id)
        board = chess.Board()

        game_pgn = chess.pgn.Game()
        game_pgn.headers["Result"] = "*"

        status = "active" if opponent_type == "ai" else "waiting"

        game = Game(white_player_id=user_id,
                    black_player_id=None,
                    opponent_type=opponent_type,
                    ai_difficulty=ai_difficulty,
                    status=status,
                    result=None,
                    current_fen=board.fen(),
                    pgn=str(game_pgn),
                    initial_time_seconds=initial_time_seconds,
                    increment_seconds=increment_seconds,
                    white_time_remaining=initial_time_seconds,
                    black_time_remaining=initial_time_seconds,
                    last_move_at=(
                        datetime.now(timezone.utc)
                        if opponent_type == "ai"
                        and initial_time_seconds is not None else None))

        repository = GameRepository(db)
        repository.create(game)
        db.commit()

        return game

    except SQLAlchemyError:
        db.rollback()
        raise


def join_game(db: Session, game_id: int, user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id(game_id)

        if game is None:
            raise GameNotFound()

        user_service.get_user_by_id(db, user_id)

        if game.status != "waiting":
            raise GameNotJoinable()
        if game.white_player_id == user_id:
            raise CannotPlayAgainstSelf()

        game.black_player_id = user_id
        game.status = "active"

        if game.initial_time_seconds is not None:
            game.last_move_at = datetime.now(timezone.utc)

        repository.update(game)
        db.commit()

        return game

    except SQLAlchemyError:
        db.rollback()
        raise


def get_game(db: Session, game_id: int) -> Game:
    repository = GameRepository(db)
    game = repository.get_by_id(game_id)

    if game is None:
        raise GameNotFound()

    return game


def list_active_games(db: Session) -> list[Game]:
    return GameRepository(db).list_active_games()


def make_move(db: Session, game_id: int, user_id: int, move: str) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id_for_update(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise GameNotActive()
        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()

        board = _board_from_pgn(game.pgn)
        is_white = user_id == game.white_player_id

        if board.turn != is_white:
            raise NotYourTurn()

        now = datetime.now(timezone.utc)
        timed_out = _update_clock(game, board, now)

        if timed_out:
            result = "0-1" if board.turn == chess.WHITE else "1-0"
            _finish_game(db, game, result)

            repository.update(game)
            db.commit()

            return game

        try:
            chess_move = chess.Move.from_uci(move)
        except ValueError:
            raise IllegalMove()

        if chess_move not in board.legal_moves:
            raise IllegalMove()

        board.push(chess_move)
        game.draw_offer_by = None

        if game.initial_time_seconds is not None:
            if is_white:
                game.white_time_remaining += game.increment_seconds
            else:
                game.black_time_remaining += game.increment_seconds

            game.last_move_at = now

        if board.is_checkmate():
            result = "1-0" if board.turn == chess.BLACK else "0-1"
            _finish_game(db, game, result)

        elif (board.is_stalemate() or board.is_insufficient_material()
              or board.is_fivefold_repetition()
              or board.is_seventyfive_moves()):
            _finish_game(db, game, "1/2-1/2")

        pgn_game = chess.pgn.read_game(io.StringIO(game.pgn))
        pgn_node = pgn_game
        while pgn_node.variations:
            pgn_node = pgn_node.variations[0]

        pgn_node.add_main_variation(chess_move)
        game.current_fen = board.fen()
        game.pgn = str(pgn_game)

        repository.update(game)
        db.commit()

        return game

    except Exception:
        db.rollback()
        raise


def make_ai_move(db: Session, game_id: int, ai_move: chess.Move) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id_for_update(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise GameNotActive()
        if game.opponent_type != "ai":
            raise NotAIGame()

        board = _board_from_pgn(game.pgn)

        if board.turn != chess.BLACK:
            raise NotYourTurn()
        if ai_move not in board.legal_moves:
            raise IllegalMove()

        now = datetime.now(timezone.utc)
        if _update_clock(game, board, now):
            _finish_game(db, game, "1-0")
            repository.update(game)
            db.commit()
            return game

        board.push(ai_move)
        game.draw_offer_by = None

        if game.initial_time_seconds is not None:
            game.black_time_remaining += game.increment_seconds
            game.last_move_at = now

        if board.is_checkmate():
            result = "1-0" if board.turn == chess.BLACK else "0-1"
            _finish_game(db, game, result)

        elif (board.is_stalemate() or board.is_insufficient_material()
              or board.is_fivefold_repetition()
              or board.is_seventyfive_moves()):
            _finish_game(db, game, "1/2-1/2")

        pgn_game = chess.pgn.read_game(io.StringIO(game.pgn))
        pgn_node = pgn_game
        while pgn_node.variations:
            pgn_node = pgn_node.variations[0]

        pgn_node.add_main_variation(ai_move)
        game.current_fen = board.fen()
        game.pgn = str(pgn_game)

        repository.update(game)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return game


def resign(db: Session, game_id: int, user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id_for_update(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise CannotResignFinishedGame()
        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()

        now = datetime.now(timezone.utc)
        board = _board_from_pgn(game.pgn)
        _update_clock(game, board, now)

        if user_id == game.white_player_id:
            _finish_game(db, game, "0-1")
        else:
            _finish_game(db, game, "1-0")

        repository.update(game)
        db.commit()

        return game

    except Exception:
        db.rollback()
        raise


def offer_draw(db: Session, game_id: int, user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise GameNotActive()

        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()
        if game.draw_offer_by is not None:
            raise DrawOfferAlreadyExists()

        game.draw_offer_by = user_id
        repository.update(game)
        db.commit()

        return game

    except SQLAlchemyError:
        db.rollback()
        raise


def accept_draw(db: Session, game_id: int, user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id_for_update(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise GameNotActive()

        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()
        if game.draw_offer_by is None:
            raise NoDrawOffer()

        if game.draw_offer_by == user_id:
            raise CannotAcceptOwnDrawOffer()

        _update_clock(game, _board_from_pgn(game.pgn),
                      datetime.now(timezone.utc))
        _finish_game(db, game, "1/2-1/2")
        game.draw_offer_by = None

        repository.update(game)
        db.commit()

        return game

    except Exception:
        db.rollback()
        raise


def decline_draw(db: Session, game_id: int, user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise GameNotActive()

        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()
        if game.draw_offer_by is None:
            raise NoDrawOffer()

        if game.draw_offer_by == user_id:
            raise CannotAcceptOwnDrawOffer()

        game.draw_offer_by = None
        repository.update(game)
        db.commit()

        return game

    except SQLAlchemyError:
        db.rollback()
        raise


def claim_threefold_repetition(db: Session, game_id: int,
                               user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id_for_update(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise GameNotActive()
        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()

        board = _board_from_pgn(game.pgn)

        if not board.can_claim_threefold_repetition():
            raise DrawNotClaimable()

        _update_clock(game, board, datetime.now(timezone.utc))
        _finish_game(db, game, "1/2-1/2")
        game.draw_offer_by = None

        repository.update(game)
        db.commit()

        return game

    except Exception:
        db.rollback()
        raise


def claim_fifty_move(db: Session, game_id: int, user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id_for_update(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise GameNotActive()
        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()

        board = _board_from_pgn(game.pgn)

        if not board.can_claim_fifty_moves():
            raise DrawNotClaimable()

        _update_clock(game, board, datetime.now(timezone.utc))
        _finish_game(db, game, "1/2-1/2")
        game.draw_offer_by = None

        repository.update(game)
        db.commit()

        return game

    except Exception:
        db.rollback()
        raise


def create_human_game(db: Session, white_player_id: int, black_player_id: int,
                      initial_time_seconds: int | None,
                      increment_seconds: int) -> Game:
    board = chess.Board()

    game_pgn = chess.pgn.Game()
    game_pgn.headers["Result"] = "*"

    game = Game(white_player_id=white_player_id,
                black_player_id=black_player_id,
                opponent_type="human",
                ai_difficulty=None,
                status="active",
                result=None,
                current_fen=board.fen(),
                pgn=str(game_pgn),
                initial_time_seconds=initial_time_seconds,
                increment_seconds=increment_seconds,
                white_time_remaining=initial_time_seconds,
                black_time_remaining=initial_time_seconds,
                last_move_at=(datetime.now(timezone.utc)
                              if initial_time_seconds is not None else None))

    repository = GameRepository(db)
    repository.create(game)

    return game


def expire_clock(db: Session,
                 game_id: int,
                 now: datetime | None = None) -> dict | None:
    """Finish an expired timed game once; return a notification after commit."""
    try:
        game = GameRepository(db).get_by_id_for_update(game_id)
        if game is None or game.status != "active" or game.initial_time_seconds is None:
            db.rollback()
            return None
        now = now or datetime.now(timezone.utc)
        board = _board_from_pgn(game.pgn)
        reference = game.last_move_at
        if reference is None:
            db.rollback()
            return None
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        remaining = game.white_time_remaining if board.turn == chess.WHITE else game.black_time_remaining
        if (now - reference).total_seconds() < remaining:
            db.rollback()
            return None
        # Finish at the actual deadline, so round pauses don't depend on polling delay.
        deadline = reference + timedelta(seconds=remaining)
        game.last_move_at = reference
        _update_clock(game, board, now)
        result = "0-1" if board.turn == chess.WHITE else "1-0"
        _finish_game(db, game, result)
        game.finished_at = deadline
        game.draw_offer_by = None
        pgn_game = chess.pgn.read_game(io.StringIO(game.pgn))
        pgn_game.headers["Result"] = result
        game.pgn = str(pgn_game)
        notification = {
            "game_id": game.id,
            "fen": game.current_fen,
            "result": game.result
        }
        db.commit()
        return notification
    except Exception:
        db.rollback()
        raise
