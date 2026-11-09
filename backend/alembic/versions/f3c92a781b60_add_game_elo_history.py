"""Record post-game Elo without reconstructing past ratings.

Revision ID: f3c92a781b60
Revises: e6a821f90d34
"""

from alembic import op
import sqlalchemy as sa

revision = "f3c92a781b60"
down_revision = "e6a821f90d34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("games", sa.Column("white_elo_after", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("black_elo_after", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("games", "black_elo_after")
    op.drop_column("games", "white_elo_after")
