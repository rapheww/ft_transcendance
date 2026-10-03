"""add draw offer to games

Revision ID: 466c3a88890f
Revises: 59f05cfb7393
Create Date: 2026-10-01 22:09:29.915005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '466c3a88890f'
down_revision: Union[str, Sequence[str], None] = '59f05cfb7393'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games",
                  sa.Column("draw_offer_by", sa.Integer(), nullable=True))

    op.create_foreign_key("fk_games_draw_offer_by_users", "games", "users",
                          ["draw_offer_by"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_games_draw_offer_by_users",
                       "games",
                       type_="foreignkey")

    op.drop_column("games", "draw_offer_by")
