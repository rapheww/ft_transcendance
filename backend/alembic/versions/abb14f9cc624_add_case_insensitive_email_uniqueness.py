"""add case insensitive email uniqueness

Revision ID: abb14f9cc624
Revises: a91f742dc630
Create Date: 2026-10-09 23:49:17.133416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'abb14f9cc624'
down_revision: Union[str, Sequence[str], None] = 'a91f742dc630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("uq_users_email_lower",
                    "users", [sa.text("lower(email)")],
                    unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_email_lower", table_name="users")
