"""normalize agent trace JSONB and unique index

Revision ID: f3a4b5c6d7e8
Revises: e1f2a3b4c5d6
Create Date: 2026-08-09 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "f3a4b5c6d7e8"
down_revision: str | None = "e1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        "ix_agent_traces_langsmith_run_id",
        table_name="agent_traces",
    )

    op.drop_constraint(
        "agent_traces_langsmith_run_id_key",
        "agent_traces",
        type_="unique",
    )

    op.create_index(
        "ix_agent_traces_langsmith_run_id",
        "agent_traces",
        ["langsmith_run_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_traces_langsmith_run_id",
        table_name="agent_traces",
    )

    op.create_unique_constraint(
        "agent_traces_langsmith_run_id_key",
        "agent_traces",
        ["langsmith_run_id"],
    )

    op.create_index(
        "ix_agent_traces_langsmith_run_id",
        "agent_traces",
        ["langsmith_run_id"],
    )