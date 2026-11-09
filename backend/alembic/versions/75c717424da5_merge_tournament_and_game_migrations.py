"""merge tournament and game migrations

Revision ID: 75c717424da5
Revises: c74f9690f6c3, 466c3a88890f
Create Date: 2026-10-03 14:42:06.618591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75c717424da5'
down_revision: Union[str, Sequence[str], None] = ('c74f9690f6c3', '466c3a88890f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
