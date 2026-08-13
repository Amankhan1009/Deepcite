import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class TraceRunResponse(BaseModel):
    id: uuid.UUID
    agent_name: str
    langsmith_run_id: uuid.UUID
    tool_calls: list[dict[str, Any]]
    token_usage: dict[str, Any]
    latency_ms: int | None
    status: str
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchTraceResponse(BaseModel):
    research_run_id: uuid.UUID
    trace_count: int
    total_tokens: int
    total_cost: Decimal
    total_latency_ms: int
    total_retries: int
    total_errors: int
    runs: list[TraceRunResponse]


class ObservabilitySummaryResponse(BaseModel):
    research_run_count: int
    trace_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: Decimal
    total_latency_ms: int
    total_retries: int
    total_errors: int