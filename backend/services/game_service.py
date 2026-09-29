import io
import chess
import chess.pgn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.models.game import Game
from backend.repositories.game_repository import GameRepository
from backend.services import user_service
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable, GameNotActive, NotAPlayer, NotYourTurn, IllegalMove, CannotResignFinishedGame


def _board_from_pgn(pgn: str) -> chess.Board:
    pgn_game = chess.pgn.read_game(io.StringIO(pgn))
    board = pgn_game.board()

    for move in pgn_game.mainline_moves():
        board.push(move)

    return board


def _finish_game(game: Game, result: str) -> None:
    game.status = "finished"
    game.result = result
    game.finished_at = datetime.now(timezone.utc)


def create_game(db: Session, user_id: int, initial_time_seconds: int = None,
                increment_seconds: int = 0) -> Game:
    try:
        user_service.get_user_by_id(db, user_id)
        board = chess.Board()

        game_pgn = chess.pgn.Game()
        game_pgn.headers["Result"] = "*"

        game = Game(white_player_id=user_id,
                    black_player_id=None,
                    status="waiting",
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
        game = repository.get_by_id(game_id)

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

        try:
            chess_move = chess.Move.from_uci(move)
        except ValueError:
            raise IllegalMove()

        if chess_move not in board.legal_moves:
            raise IllegalMove()

        board.push(chess_move)

        if board.is_checkmate():
            result = "1-0" if board.turn == chess.BLACK else "0-1"
            _finish_game(game, result)

        elif (board.is_stalemate() or board.is_insufficient_material()
              or board.is_fivefold_repetition()
              or board.is_seventyfive_moves()):
            _finish_game(game, "1/2-1/2")

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

    except SQLAlchemyError:
        db.rollback()
        raise


def resign(db: Session, game_id: int, user_id: int) -> Game:
    try:
        repository = GameRepository(db)
        game = repository.get_by_id(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise CannotResignFinishedGame()
        if user_id not in (game.white_player_id, game.black_player_id):
            raise NotAPlayer()

        if user_id == game.white_player_id:
            _finish_game(game, "0-1")
        else:
            _finish_game(game, "1-0")

        repository.update(game)
        db.commit()

        return game

    except SQLAlchemyError:
        db.rollback()
        raise
