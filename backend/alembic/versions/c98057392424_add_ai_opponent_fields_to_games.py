"""add AI opponent fields to games

Revision ID: <new_revision>
Revises: e6a821f90d34
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "<new_revision>"
down_revision: Union[str, Sequence[str], None] = "e6a821f90d34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("opponent_type",
                  sa.String(length=20),
                  nullable=False,
                  server_default="human"))

    op.add_column(
        "games", sa.Column("ai_difficulty",
                           sa.String(length=20),
                           nullable=True))

    op.alter_column("games", "opponent_type", server_default=None)


def downgrade() -> None:
    op.drop_column("games", "ai_difficulty")
    op.drop_column("games", "opponent_type")
