"""make game timers optionals

Revision ID: 59f05cfb7393
Revises: 2df1d7831697
Create Date: 2026-09-29 17:04:45.619744

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '59f05cfb7393'
down_revision: Union[str, Sequence[str], None] = '2df1d7831697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("games", "initial_time_seconds", server_default=None)

    op.alter_column("games", "white_time_remaining", server_default=None)

    op.alter_column("games", "black_time_remaining", server_default=None)


def downgrade() -> None:
    op.alter_column("games", "initial_time_seconds", server_default="600")

    op.alter_column("games", "white_time_remaining", server_default="600")

    op.alter_column("games", "black_time_remaining", server_default="600")
