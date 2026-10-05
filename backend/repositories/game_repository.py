from sqlalchemy import or_
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

    def get_by_id_for_update(self, game_id: int) -> Game | None:
        return (self.db.query(Game).filter(
            Game.id == game_id).populate_existing().with_for_update().first())

    def get_active_game_for_user(self, user_id: int) -> Game | None:
        return (self.db.query(Game).filter(
            Game.status == "active", Game.opponent_type == "human",
            or_(Game.white_player_id == user_id,
                Game.black_player_id == user_id)).order_by(
                    Game.created_at.desc()).first())

    def update(self, game: Game) -> Game:
        self.db.flush()
        self.db.refresh(game)
        return game
