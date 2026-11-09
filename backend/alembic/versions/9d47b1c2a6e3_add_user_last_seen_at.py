"""add user last seen timestamp

Revision ID: 9d47b1c2a6e3
Revises: d41672085aed, f9d4c82a17b1
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d47b1c2a6e3"
down_revision: Union[str, Sequence[str], None] = (
    "d41672085aed",
    "f9d4c82a17b1",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_seen_at")
