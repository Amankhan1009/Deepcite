"""add evidence table

Revision ID: 3f1c8a7e9b20
Revises: 14c1e3c7e77d
Create Date: 2026-08-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3f1c8a7e9b20"
down_revision: Union[str, None] = "14c1e3c7e77d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("research_run_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["research_run_id"],
            ["research_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_evidence_research_run_id",
        "evidence",
        ["research_run_id"],
        unique=False,
    )

    op.create_index(
        "ix_evidence_source_id",
        "evidence",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_evidence_source_id", table_name="evidence")
    op.drop_index("ix_evidence_research_run_id", table_name="evidence")
    op.drop_table("evidence")