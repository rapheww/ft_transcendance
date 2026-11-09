"""Tournament ownership, persisted deadlines and brackets with byes."""
from alembic import op
import sqlalchemy as sa

revision = "a91f742dc630"
down_revision = "4ec7c4308dd0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tournaments",
        sa.Column("organizer_type",
                  sa.String(10),
                  nullable=False,
                  server_default="player"))
    op.add_column("tournaments",
                  sa.Column("creator_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_tournament_creator", "tournaments", "users",
                          ["creator_id"], ["id"])
    op.add_column(
        "tournaments",
        sa.Column("registration_deadline",
                  sa.DateTime(timezone=True),
                  nullable=True))
    op.add_column(
        "tournaments",
        sa.Column("next_round_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "tournaments",
        sa.Column("current_round",
                  sa.Integer(),
                  nullable=False,
                  server_default="0"))
    # The old player creator was always the first participant.
    op.execute("""UPDATE tournaments t SET creator_id = (
        SELECT p.user_id FROM tournament_participants p WHERE p.tournament_id=t.id
        ORDER BY p.joined_at, p.id LIMIT 1), registration_deadline = t.created_at + interval '30 minutes',
        current_round = COALESCE((SELECT MAX(m.round) FROM tournament_matches m WHERE m.tournament_id=t.id), 0)"""
               )
    op.execute(
        "UPDATE tournaments SET organizer_type='api' WHERE creator_id IS NULL")
    op.alter_column("tournaments", "registration_deadline", nullable=False)
    for name in ("player1_id", "player2_id", "game_id"):
        op.alter_column("tournament_matches",
                        name,
                        existing_type=sa.Integer(),
                        nullable=True)
    op.add_column(
        "tournament_matches",
        sa.Column("is_bye",
                  sa.Boolean(),
                  nullable=False,
                  server_default=sa.false()))
    op.create_unique_constraint("uq_tournament_match_slot",
                                "tournament_matches",
                                ["tournament_id", "round", "slot"])
    op.create_index("ix_tournament_participant_user",
                    "tournament_participants", ["user_id"])
    op.create_index("ix_tournament_match_game", "tournament_matches",
                    ["game_id"])
    op.create_index("ix_tournament_status", "tournaments", ["status"])


def downgrade():
    # Planned matches and exemptions cannot be represented in the old schema.
    op.execute("DELETE FROM tournament_matches WHERE game_id IS NULL")
    op.drop_index("ix_tournament_status", table_name="tournaments")
    op.drop_index("ix_tournament_match_game", table_name="tournament_matches")
    op.drop_index("ix_tournament_participant_user",
                  table_name="tournament_participants")
    op.drop_constraint("uq_tournament_match_slot",
                       "tournament_matches",
                       type_="unique")
    op.drop_column("tournament_matches", "is_bye")
    for name in ("player1_id", "player2_id", "game_id"):
        op.alter_column("tournament_matches",
                        name,
                        existing_type=sa.Integer(),
                        nullable=False)
    op.drop_constraint("fk_tournament_creator",
                       "tournaments",
                       type_="foreignkey")
    for name in ("organizer_type", "creator_id", "registration_deadline",
                 "next_round_at", "current_round"):
        op.drop_column("tournaments", name)
