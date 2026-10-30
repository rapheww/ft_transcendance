from datetime import datetime
from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index,
                        String, func)
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (
        CheckConstraint("user_low_id < user_high_id",
                        name="ck_friend_requests_canonical_user_order"),
        CheckConstraint(
            "requested_by_id = user_low_id OR requested_by_id = user_high_id",
            name="ck_friend_requests_requester_in_pair",
        ),
        CheckConstraint(
            "status IN ('pending', 'rejected')",
            name="ck_friend_requests_valid_status",
        ),
        Index("ix_friend_requests_user_high_id_status",
              "user_high_id", "status"),
    )

    user_low_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    user_high_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    requested_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending")
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
