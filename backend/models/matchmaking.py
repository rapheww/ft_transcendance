from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


class MatchmakingQueue(Base):
    __tablename__ = "matchmaking_queue"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                         nullable=False,
                                         unique=True)

    initial_time_seconds: Mapped[int | None] = mapped_column(Integer,
                                                             nullable=True)

    increment_seconds: Mapped[int] = mapped_column(Integer,
                                                   nullable=False,
                                                   default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False,
                                                 server_default=func.now())
