"""merge bot and email migration heads

Revision ID: 7b595578ae73
Revises: abb14f9cc624, d41672085aed
Create Date: 2026-10-10 18:39:05.888576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b595578ae73'
down_revision: Union[str, Sequence[str], None] = ('abb14f9cc624', 'd41672085aed')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
