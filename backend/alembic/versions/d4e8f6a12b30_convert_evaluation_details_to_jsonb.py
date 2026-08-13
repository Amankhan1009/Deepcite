"""convert evaluation details from JSON to JSONB

Revision ID: d4e8f6a12b30
Revises: c8d91f4e27a1
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d4e8f6a12b30"
down_revision: Union[str, None] = "c8d91f4e27a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "evaluations",
        "details",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        postgresql_using="details::jsonb",
    )


def downgrade() -> None:
    op.alter_column(
        "evaluations",
        "details",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.JSON(),
        existing_nullable=False,
        postgresql_using="details::json",
    )