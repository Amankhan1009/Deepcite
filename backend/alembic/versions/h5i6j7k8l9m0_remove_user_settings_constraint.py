"""remove redundant user settings unique constraint

Revision ID: h5i6j7k8l9m0
Revises: g4h5i6j7k8l9
"""

from collections.abc import Sequence

from alembic import op


revision: str = "h5i6j7k8l9m0"
down_revision: str | None = "g4h5i6j7k8l9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "user_settings_user_id_key",
        "user_settings",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "user_settings_user_id_key",
        "user_settings",
        ["user_id"],
    )