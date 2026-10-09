from sqlalchemy import Integer, String, Index, func
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


Index("uq_users_email_lower", func.lower(User.email), unique=True)
