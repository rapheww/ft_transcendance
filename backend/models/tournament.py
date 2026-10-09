from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


class Tournament(Base):
    __tablename__ = "tournaments"
    __table_args__ = (Index("ix_tournament_status", "status"), )

    id: Mapped[int] = mapped_column(primary_key=True)

    status: Mapped[str] = mapped_column(String(20),
                                        nullable=False,
                                        default="registration")

    organizer_type: Mapped[str] = mapped_column(String(10),
                                                nullable=False,
                                                default="player")
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                   nullable=True)
    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    next_round_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    current_round: Mapped[int] = mapped_column(nullable=False, default=0)

    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                  nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 nullable=False,
                                                 server_default=func.now())


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    __table_args__ = (UniqueConstraint("tournament_id",
                                       "user_id",
                                       name="uq_tournament_participant"),
                      Index("ix_tournament_participant_user", "user_id"))

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
    __table_args__ = (UniqueConstraint("tournament_id",
                                       "round",
                                       "slot",
                                       name="uq_tournament_match_slot"),
                      Index("ix_tournament_match_game", "game_id"))

    is_bye: Mapped[bool] = mapped_column(Boolean,
                                         nullable=False,
                                         default=False)

    id: Mapped[int] = mapped_column(primary_key=True)

    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"),
                                               nullable=False)

    round: Mapped[int] = mapped_column(nullable=False)
    slot: Mapped[int] = mapped_column(nullable=False)

    player1_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                   nullable=True)

    player2_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                   nullable=True)

    game_id: Mapped[int | None] = mapped_column(ForeignKey("games.id"),
                                                nullable=True)

    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),
                                                  nullable=True)
