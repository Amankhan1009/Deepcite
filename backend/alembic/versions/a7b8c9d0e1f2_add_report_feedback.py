"""add report feedback

Revision ID: a7b8c9d0e1f2
Revises: f3a4b5c6d7e8
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f3a4b5c6d7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
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
        sa.CheckConstraint(
            "decision IN ('approved', 'rejected') OR decision IS NULL",
            name="ck_report_feedback_decision",
        ),
        sa.CheckConstraint(
            "rating IS NULL OR rating BETWEEN 1 AND 5",
            name="ck_report_feedback_rating",
        ),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["reports.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_report_feedback_report_id",
        "report_feedback",
        ["report_id"],
    )

    op.create_index(
        "ix_report_feedback_user_id",
        "report_feedback",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_report_feedback_user_id",
        table_name="report_feedback",
    )
    op.drop_index(
        "ix_report_feedback_report_id",
        table_name="report_feedback",
    )
    op.drop_table("report_feedback")