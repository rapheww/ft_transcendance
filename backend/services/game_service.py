import chess
import chess.pgn
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from backend.models.game import Game
from backend.repositories.game_repository import GameRepository
from backend.services import user_service


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
