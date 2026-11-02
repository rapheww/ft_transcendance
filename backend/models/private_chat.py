from datetime import datetime
from sqlalchemy import (DateTime, ForeignKey, ForeignKeyConstraint, Index,
                        Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base


class PrivateConversation(Base):
    __tablename__ = "private_conversations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_low_id", "user_high_id"],
            ["friendships.user_low_id", "friendships.user_high_id"],
            ondelete="CASCADE",
            name="fk_private_conversations_friendship",
        ),
        UniqueConstraint("user_low_id", "user_high_id",
                         name="uq_private_conversations_participants"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_low_id: Mapped[int] = mapped_column(nullable=False)
    user_high_id: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())


class PrivateMessage(Base):
    __tablename__ = "private_messages"
    __table_args__ = (
        Index("ix_private_messages_conversation_created",
              "conversation_id", "created_at", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("private_conversations.id", ondelete="CASCADE"),
        nullable=False)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())
