from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)

    white_player_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                                 nullable=False)

    black_player_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                        nullable=True)

    status: Mapped[str] = mapped_column(String(20),
                                        nullable=False,
                                        default="waiting")

    result: Mapped[str | None] = mapped_column(String(20), nullable=True)

    current_fen: Mapped[str] = mapped_column(Text, nullable=False)

    pgn: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False,
                                                 server_default=func.now())

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
