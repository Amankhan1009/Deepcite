import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    research_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_runs.id", ondelete="CASCADE"),
        index=True,
    )

    agent_name: Mapped[str] = mapped_column(
        String(255),
        index=True,
    )

    langsmith_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        index=True,
    )

    tool_calls: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
    )

    token_usage: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="unknown",
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )