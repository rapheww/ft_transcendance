import io
import chess
import chess.pgn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.models.game import Game
from backend.repositories.game_repository import GameRepository
from backend.services import user_service
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable, GameNotActive, NotAPlayer, NotYourTurn, IllegalMove


def create_game(db: Session, user_id: int) -> Game:
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
                    pgn=str(game_pgn))

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

        board = chess.Board(game.current_fen)
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
            game.status = "finished"
            game.result = "1-0" if board.turn == chess.BLACK else "0-1"
            game.finished_at = datetime.now(timezone.utc)

        elif board.is_stalemate():
            game.status = "finished"
            game.result = "1/2-1/2"
            game.finished_at = datetime.now(timezone.utc)

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
