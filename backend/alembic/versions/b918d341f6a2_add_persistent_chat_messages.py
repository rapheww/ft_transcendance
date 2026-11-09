"""add persistent chat messages

Revision ID: b918d341f6a2
Revises: 3f0aecc166dc
Create Date: 2026-10-22 21:09:19.244+02:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b918d341f6a2'
down_revision: Union[str, Sequence[str], None] = '3f0aecc166dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chat_messages_game_id'),
                    'chat_messages', ['game_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_game_id'),
                  table_name='chat_messages')
    op.drop_table('chat_messages')
