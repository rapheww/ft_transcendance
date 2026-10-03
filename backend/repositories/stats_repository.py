from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.models.game import Game
from backend.models.user import User


class StatsRepository:

    def __init__(self, db: Session):
        self.db = db

    def list_finished_for_player(self, user_id: int) -> list[Game]:
        return (self.db.query(Game).filter(Game.status == "finished").filter(
            or_(Game.white_player_id == user_id,
                Game.black_player_id == user_id)).order_by(
                    Game.finished_at.desc()).all())

    def get_players_for_update(self, player_ids: list[int]) -> list[User]:
        # All games acquire player locks in the same order to avoid deadlocks.
        # Refresh ratings cached before a competing transaction committed.
        return (self.db.query(User).filter(User.id.in_(player_ids)).order_by(
            User.id).populate_existing().with_for_update().all())
