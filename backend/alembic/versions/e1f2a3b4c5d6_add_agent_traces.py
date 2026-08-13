"""add agent traces

Revision ID: e1f2a3b4c5d6
Revises: d4e8f6a12b30
Create Date: 2026-08-09 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e1f2a3b4c5d6"
down_revision: str | None = "d4e8f6a12b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_traces",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "research_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "agent_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "langsmith_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tool_calls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "token_usage",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "latency_ms",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "error",
            sa.Text(),
            nullable=True,
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
            ["research_run_id"],
            ["research_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("langsmith_run_id"),
    )

    op.create_index(
        "ix_agent_traces_research_run_id",
        "agent_traces",
        ["research_run_id"],
    )

    op.create_index(
        "ix_agent_traces_agent_name",
        "agent_traces",
        ["agent_name"],
    )

    op.create_index(
        "ix_agent_traces_langsmith_run_id",
        "agent_traces",
        ["langsmith_run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_traces_langsmith_run_id",
        table_name="agent_traces",
    )
    op.drop_index(
        "ix_agent_traces_agent_name",
        table_name="agent_traces",
    )
    op.drop_index(
        "ix_agent_traces_research_run_id",
        table_name="agent_traces",
    )
    op.drop_table("agent_traces")