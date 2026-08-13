"""add user settings

Revision ID: g4h5i6j7k8l9
Revises: f3a4b5c6d7e8
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "g4h5i6j7k8l9"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "display_name",
            sa.String(length=120),
            nullable=True,
        ),
        sa.Column(
            "timezone",
            sa.String(length=64),
            server_default="UTC",
            nullable=False,
        ),
        sa.Column(
            "theme",
            sa.String(length=20),
            server_default="system",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_index(
        "ix_user_settings_user_id",
        "user_settings",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_settings_user_id",
        table_name="user_settings",
    )
    op.drop_table("user_settings")