"""merge migration heads

Revision ID: 4ec7c4308dd0
Revises: 603ff42467bd, f3c92a781b60
Create Date: 2026-10-06 23:28:45.199498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ec7c4308dd0'
down_revision: Union[str, Sequence[str], None] = ('603ff42467bd', 'f3c92a781b60')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
