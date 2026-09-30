import chess
import chess.pgn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from backend.models.game import Game
from backend.repositories.game_repository import GameRepository
from backend.services import user_service
from backend.exceptions.game import CannotPlayAgainstSelf, GameNotFound, GameNotJoinable


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

def make_move(db: Session, game_id: int, user_id: int, from_square: str, to_square: str) -> Game:
    repository = GameRepository(db)

    try:
        db.expire_all()
        
        game = repository.get_by_id(game_id)

        if game is None:
            raise GameNotFound()
        if game.status != "active":
            raise ValueError("Game is not active")
        if user_id != game.white_player_id and user_id != game.black_player_id:
            raise ValueError("You are not a player in this game")
        
        board = chess.Board(game.current_fen)
        if board.turn == chess.WHITE:
            if user_id != game.white_player_id:
                raise ValueError("Not your turn")
        else:
            if user_id != game.black_player_id:
                raise ValueError("Not your turn")
        move = chess.Move.from_uci(from_square + to_square)
        if move not in board.legal_moves:
            raise ValueError("Illegal move")

        board.push(move)
        game.current_fen = board.fen()

        repository.update(game)
        db.commit()

        return game
    except SQLAlchemyError:
        db.rollback()
        raise
