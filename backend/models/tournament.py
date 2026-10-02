from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)

    status: Mapped[str] = mapped_column(String(20),
                                        nullable=False,
                                        default="registration")

    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                  nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False,
                                                 server_default=func.now())


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    __table_args__ = (UniqueConstraint("tournament_id",
                                       "user_id",
                                       name="uq_tournament_participant"), )

    id: Mapped[int] = mapped_column(primary_key=True)

    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"),
                                               nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                         nullable=False)

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                nullable=False,
                                                server_default=func.now())


class TournamentMatch(Base):
    __tablename__ = "tournament_matches"

    id: Mapped[int] = mapped_column(primary_key=True)

    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"),
                                               nullable=False)

    round: Mapped[int] = mapped_column(nullable=False)
    slot: Mapped[int] = mapped_column(nullable=False)

    player1_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                            nullable=False)

    player2_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                            nullable=False)

    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"),
                                         nullable=False)

    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                  nullable=True)
