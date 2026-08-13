"""add evaluations table

Revision ID: c8d91f4e27a1
Revises: b7c4e3a21f90
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d91f4e27a1"
down_revision: Union[str, None] = "b7c4e3a21f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("research_run_id", sa.UUID(), nullable=False),
        sa.Column("dimension", sa.String(length=50), nullable=False),
        sa.Column(
            "score",
            sa.Numeric(precision=5, scale=4),
            nullable=False,
        ),
        sa.Column("details", sa.JSON(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "research_run_id",
            "dimension",
            name="uq_evaluations_run_dimension",
        ),
    )

    op.create_index(
        "ix_evaluations_research_run_id",
        "evaluations",
        ["research_run_id"],
    )

    op.create_index(
        "ix_evaluations_dimension",
        "evaluations",
        ["dimension"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evaluations_dimension",
        table_name="evaluations",
    )
    op.drop_index(
        "ix_evaluations_research_run_id",
        table_name="evaluations",
    )
    op.drop_table("evaluations")