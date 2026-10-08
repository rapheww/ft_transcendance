from sqlalchemy.orm import Session
from backend.models.user import User
from backend.models.matchmaking import MatchmakingQueue


class MatchmakingRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, entry: MatchmakingQueue) -> MatchmakingQueue:
        self.db.add(entry)
        self.db.flush()
        self.db.refresh(entry)
        return entry

    def get_by_user_id(self, user_id: int) -> MatchmakingQueue | None:
        return (self.db.query(MatchmakingQueue).filter(
            MatchmakingQueue.user_id == user_id).first())

    def get_closest_compatible(self, user_id: int,
                               initial_time_seconds: int | None,
                               increment_seconds: int, min_elo: int,
                               max_elo: int,
                               player_elo: int) -> MatchmakingQueue | None:

        entries = (self.db.query(MatchmakingQueue, User.elo).join(
            User, MatchmakingQueue.user_id == User.id).filter(
                MatchmakingQueue.user_id != user_id,
                MatchmakingQueue.initial_time_seconds == initial_time_seconds,
                MatchmakingQueue.increment_seconds == increment_seconds,
                User.elo >= min_elo, User.elo <= max_elo).all())

        if not entries:
            return None

        entry, _ = min(entries, key=lambda pair: abs(pair[1] - player_elo))
        return entry

    def delete(self, entry: MatchmakingQueue) -> None:
        self.db.delete(entry)
        self.db.flush()
