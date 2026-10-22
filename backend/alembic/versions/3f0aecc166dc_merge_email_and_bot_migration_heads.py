"""merge email and bot migration heads

Revision ID: 3f0aecc166dc
Revises: abb14f9cc624, d41672085aed
Create Date: 2026-10-10 16:01:09.529137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f0aecc166dc'
down_revision: Union[str, Sequence[str], None] = ('abb14f9cc624', 'd41672085aed')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
