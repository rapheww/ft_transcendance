from alembic import op

revision = "NEW_REVISION"
down_revision = "073b04d4176f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("users", "board_color")


def downgrade() -> None:
    # Restore the old column if we downgrade.
    import sqlalchemy as sa

    op.add_column(
        "users",
        sa.Column("board_color",
                  sa.String(length=7),
                  nullable=False,
                  server_default="#2C5563"))
