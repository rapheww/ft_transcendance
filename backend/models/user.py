from datetime import datetime
from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base
from backend.services.elo_service import INITIAL_ELO


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(String(50),
                                          unique=True,
                                          nullable=False)

    email: Mapped[str] = mapped_column(String(255),
                                       unique=True,
                                       nullable=False)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    avatar: Mapped[str] = mapped_column(String(500),
                                        nullable=False,
                                        default="https://shorturl.at/Jm5fo")

    board_light_color: Mapped[str] = mapped_column(String(7),
                                                   nullable=False,
                                                   default="#E3DDC5")

    board_dark_color: Mapped[str] = mapped_column(String(7),
                                                  nullable=False,
                                                  default="#2C5563")

    elo: Mapped[int] = mapped_column(Integer,
                                     nullable=False,
                                     default=INITIAL_ELO,
                                     server_default=str(INITIAL_ELO))

    is_bot: Mapped[bool] = mapped_column(Boolean,
                                         default=False,
                                         server_default="false",
                                         nullable=False)

    ai_level: Mapped[str | None] = mapped_column(String(20),
                                                 nullable=True)

    style: Mapped[str | None] = mapped_column(String(20),
                                              nullable=True)

    preferred_time_control: Mapped[str | None] = mapped_column(String(20),
                                                               nullable=True)

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)


Index("uq_users_email_lower", func.lower(User.email), unique=True)
