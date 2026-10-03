from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.models.game import Game


class StatsRepository:

    def __init__(self, db: Session):
        self.db = db

    def list_finished_for_player(self, user_id: int) -> list[Game]:
        return (self.db.query(Game).filter(Game.status == "finished").filter(
            or_(Game.white_player_id == user_id,
                Game.black_player_id == user_id)).order_by(
                    Game.finished_at.desc()).all())
