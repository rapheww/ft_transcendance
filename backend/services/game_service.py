import io
import chess
import chess.pgn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, timezone
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
        elo_service.update_ratings(db, game.white_player_id, game.black_player_id,
                                result)
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
        if ai_difficulty not in ("easy", "medium", "strong"):
            raise InvalidDifficulty()
        initial_time_seconds = None
        increment_seconds = 0
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
                    last_move_at=None)

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

        board.push(ai_move)
        game.draw_offer_by = None

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

        _update_clock(game, _board_from_pgn(game.pgn), datetime.now(timezone.utc))
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
