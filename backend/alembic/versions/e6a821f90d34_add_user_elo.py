"""Add Elo ratings initialized at 1000 without replaying past games.

Revision ID: e6a821f90d34
Revises: NEW_REVISION
"""

from alembic import op
import sqlalchemy as sa

revision = "e6a821f90d34"
down_revision = "NEW_REVISION"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Freeze the initial rating in migration history, independent of future settings.
    op.add_column(
        "users",
        sa.Column("elo",
                  sa.Integer(),
                  nullable=False,
                  server_default=sa.text("1000")))


def downgrade() -> None:
    op.drop_column("users", "elo")
