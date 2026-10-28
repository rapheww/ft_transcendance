"""merge notifications and chat migrations

Revision ID: ef8ee62961ef
Revises: 059e289964d1, b918d341f6a2
Create Date: 2026-10-28 18:48:59.349131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef8ee62961ef'
down_revision: Union[str, Sequence[str], None] = ('059e289964d1', 'b918d341f6a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
