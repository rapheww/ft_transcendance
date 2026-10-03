"""add avatar and board color to users

Revision ID: ac778d7a4503
Revises: 75c717424da5
Create Date: 2026-10-03 15:12:06.677408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ac778d7a4503'
down_revision: Union[str, Sequence[str], None] = '75c717424da5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("avatar",
                  sa.String(length=500),
                  nullable=False,
                  server_default="default"))

    op.add_column(
        "users",
        sa.Column("board_color",
                  sa.String(length=7),
                  nullable=False,
                  server_default="#2C5563"))

    op.alter_column("users", "avatar", server_default=None)
    op.alter_column("users", "board_color", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "board_color")
    op.drop_column("users", "avatar")
