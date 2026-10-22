from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)

    white_player_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                                 nullable=False)

    black_player_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                        nullable=True)

    white_player: Mapped["User"] = relationship(foreign_keys=[white_player_id])
    black_player: Mapped["User | None"] = relationship(
        foreign_keys=[black_player_id])

    opponent_type: Mapped[str] = mapped_column(String(20),
                                               nullable=False,
                                               default="human")

    ai_difficulty: Mapped[str | None] = mapped_column(String(20),
                                                      nullable=True,
                                                      default=None)

    status: Mapped[str] = mapped_column(String(20),
                                        nullable=False,
                                        default="waiting")

    result: Mapped[str | None] = mapped_column(String(20), nullable=True)

    white_elo_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    black_elo_after: Mapped[int | None] = mapped_column(Integer, nullable=True)

    current_fen: Mapped[str] = mapped_column(Text, nullable=False)

    pgn: Mapped[str] = mapped_column(Text, nullable=False)

    initial_time_seconds: Mapped[int | None] = mapped_column(Integer,
                                                             nullable=True,
                                                             default=None)

    increment_seconds: Mapped[int] = mapped_column(Integer,
                                                   nullable=False,
                                                   default=0)

    white_time_remaining: Mapped[int | None] = mapped_column(Integer,
                                                             nullable=True,
                                                             default=None)

    black_time_remaining: Mapped[int | None] = mapped_column(Integer,
                                                             nullable=True,
                                                             default=None)

    draw_offer_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                      nullable=True)

    last_move_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False,
                                                 server_default=func.now())

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
