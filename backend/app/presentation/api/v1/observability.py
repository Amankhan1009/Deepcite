import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.get_observability_summary import (
    get_observability_summary,
)
from app.application.use_cases.get_research_trace import (
    ResearchTraceNotFoundError,
    get_research_trace,
)
from app.infrastructure.db.models.agent_trace import AgentTrace
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.agent_trace_repository import (
    AgentTraceRepository,
)
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)
from app.infrastructure.db.session import get_db
from app.infrastructure.observability.langsmith_trace_reader import (
    LangSmithTraceReader,
    ObservabilityUnavailableError,
)
from app.presentation.api.v1.deps import get_current_user
from app.presentation.schemas.observability import (
    ObservabilitySummaryResponse,
    ResearchTraceResponse,
    TraceRunResponse,
)

router = APIRouter(tags=["observability"])


def _build_trace_response(
    research_run_id: uuid.UUID,
    traces: list[AgentTrace],
) -> ResearchTraceResponse:
    total_tokens = 0
    total_cost = Decimal("0")
    total_latency_ms = 0
    total_retries = 0
    total_errors = 0

    for trace in traces:
        usage = trace.token_usage or {}

        total_tokens += int(usage.get("total_tokens", 0))
        total_cost += Decimal(str(usage.get("total_cost", "0")))
        total_latency_ms += trace.latency_ms or 0
        total_retries += int(usage.get("retry_count", 0))
        total_errors += int(trace.error is not None)

    return ResearchTraceResponse(
        research_run_id=research_run_id,
        trace_count=len(traces),
        total_tokens=total_tokens,
        total_cost=total_cost,
        total_latency_ms=total_latency_ms,
        total_retries=total_retries,
        total_errors=total_errors,
        runs=[
            TraceRunResponse.model_validate(trace)
            for trace in traces
        ],
    )


@router.get(
    "/research/{research_run_id}/trace",
    response_model=ResearchTraceResponse,
)
async def get_trace(
    research_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        trace_reader = LangSmithTraceReader()

        traces = await get_research_trace(
            research_run_repository=ResearchRunRepository(db),
            agent_trace_repository=AgentTraceRepository(db),
            trace_reader=trace_reader,
            research_run_id=research_run_id,
            user_id=current_user.id,
        )
    except ResearchTraceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research trace not found",
        ) from error
    except ObservabilityUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Observability service is not configured",
        ) from error

    return _build_trace_response(
        research_run_id,
        traces,
    )


@router.get(
    "/observability/summary",
    response_model=ObservabilitySummaryResponse,
)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        trace_reader = LangSmithTraceReader()

        summary = await get_observability_summary(
            research_run_repository=ResearchRunRepository(db),
            agent_trace_repository=AgentTraceRepository(db),
            trace_reader=trace_reader,
            user_id=current_user.id,
        )
    except ObservabilityUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Observability service is not configured",
        ) from error

    return ObservabilitySummaryResponse.model_validate(summary)