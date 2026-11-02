"""add friendships and private chat

Revision ID: f9d4c82a17b1
Revises: ef8ee62961ef
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9d4c82a17b1"
down_revision: Union[str, Sequence[str], None] = "ef8ee62961ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "friendships",
        sa.Column("user_low_id", sa.Integer(), nullable=False),
        sa.Column("user_high_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "user_low_id < user_high_id",
            name="ck_friendships_canonical_user_order",
        ),
        sa.ForeignKeyConstraint(
            ["user_high_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_low_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_low_id", "user_high_id"),
    )
    op.create_index("ix_friendships_user_high_id",
                    "friendships", ["user_high_id"], unique=False)

    op.create_table(
        "friend_requests",
        sa.Column("user_low_id", sa.Integer(), nullable=False),
        sa.Column("user_high_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending",
                  nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "user_low_id < user_high_id",
            name="ck_friend_requests_canonical_user_order",
        ),
        sa.CheckConstraint(
            "requested_by_id = user_low_id OR requested_by_id = user_high_id",
            name="ck_friend_requests_requester_in_pair",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'rejected')",
            name="ck_friend_requests_valid_status",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_high_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_low_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_low_id", "user_high_id"),
    )
    op.create_index(
        "ix_friend_requests_user_high_id_status",
        "friend_requests",
        ["user_high_id", "status"],
        unique=False,
    )

    op.create_table(
        "private_conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_low_id", sa.Integer(), nullable=False),
        sa.Column("user_high_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_low_id", "user_high_id"],
            ["friendships.user_low_id", "friendships.user_high_id"],
            ondelete="CASCADE",
            name="fk_private_conversations_friendship",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_low_id", "user_high_id",
            name="uq_private_conversations_participants",
        ),
    )

    op.create_table(
        "private_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["private_conversations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_private_messages_conversation_created",
        "private_messages",
        ["conversation_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_private_messages_conversation_created",
                  table_name="private_messages")
    op.drop_table("private_messages")
    op.drop_table("private_conversations")
    op.drop_index("ix_friend_requests_user_high_id_status",
                  table_name="friend_requests")
    op.drop_table("friend_requests")
    op.drop_index("ix_friendships_user_high_id", table_name="friendships")
    op.drop_table("friendships")
