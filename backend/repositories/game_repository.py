from sqlalchemy.orm import Session
from backend.models.game import Game


class GameRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, game: Game) -> Game:
        self.db.add(game)
        self.db.flush()
        self.db.refresh(game)
        return game

    def get_by_id(self, game_id: int) -> Game | None:
        return (self.db.query(Game).filter(Game.id == game_id).first())

    def update(self, game: Game) -> Game:
        self.db.flush()
        self.db.refresh(game)
        return game
