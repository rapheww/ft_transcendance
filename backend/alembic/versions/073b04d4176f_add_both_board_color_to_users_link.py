from alembic import op
import sqlalchemy as sa

revision = "073b04d4176f"
down_revision = "ac778d7a4503"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("board_light_color",
                  sa.String(length=7),
                  nullable=False,
                  server_default="#E3DDC5"))

    op.add_column(
        "users",
        sa.Column("board_dark_color",
                  sa.String(length=7),
                  nullable=False,
                  server_default="#2C5563"))


def downgrade() -> None:
    op.drop_column("users", "board_dark_color")
    op.drop_column("users", "board_light_color")
