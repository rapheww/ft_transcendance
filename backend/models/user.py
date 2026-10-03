from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


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
                                        default="default")

    board_color: Mapped[str] = mapped_column(String(7),
                                             nullable=False,
                                             default="#2C5563")
