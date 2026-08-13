"""add claim confidence scores and citations

Revision ID: b7c4e3a21f90
Revises: 2690083e058f
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c4e3a21f90"
down_revision: Union[str, None] = "2690083e058f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "claims",
        sa.Column(
            "confidence_score",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_table(
        "citations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("claim_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("inline_marker", sa.String(length=50), nullable=False),
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
            ["report_id"],
            ["reports.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["claims.id"],
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
        "ix_citations_report_id",
        "citations",
        ["report_id"],
    )
    op.create_index(
        "ix_citations_claim_id",
        "citations",
        ["claim_id"],
    )
    op.create_index(
        "ix_citations_source_id",
        "citations",
        ["source_id"],
    )

    op.alter_column(
        "claims",
        "confidence_score",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_citations_source_id",
        table_name="citations",
    )
    op.drop_index(
        "ix_citations_claim_id",
        table_name="citations",
    )
    op.drop_index(
        "ix_citations_report_id",
        table_name="citations",
    )
    op.drop_table("citations")
    op.drop_column("claims", "confidence_score")