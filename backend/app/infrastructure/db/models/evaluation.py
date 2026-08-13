import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    __table_args__ = (
        UniqueConstraint(
            "research_run_id",
            "dimension",
            name="uq_evaluations_run_dimension",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    research_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dimension: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    details: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )