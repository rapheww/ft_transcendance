"""Prevent duplicate registrations in a tournament.

Revision ID: 8b61e2a4d930
Revises: c74f9690f6c3
"""

from alembic import op

revision = "8b61e2a4d930"
down_revision = "c74f9690f6c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_tournament_participant",
                                "tournament_participants",
                                ["tournament_id", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_tournament_participant",
                       "tournament_participants",
                       type_="unique")
