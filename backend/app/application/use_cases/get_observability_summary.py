import uuid
from decimal import Decimal
from typing import Any

from app.infrastructure.db.repositories.agent_trace_repository import (
    AgentTraceRepository,
)
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)
from app.infrastructure.observability.langsmith_trace_reader import (
    LangSmithTraceReader,
)


async def get_observability_summary(
    *,
    research_run_repository: ResearchRunRepository,
    agent_trace_repository: AgentTraceRepository,
    trace_reader: LangSmithTraceReader,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    completed_runs = await research_run_repository.list_completed_for_user(
        user_id,
    )

    all_rows = []

    for research_run in completed_runs:
        trace_rows = trace_reader.read_for_research_run(
            research_run.id,
        )

        for row in trace_rows:
            await agent_trace_repository.upsert(
                research_run_id=research_run.id,
                langsmith_run_id=row["langsmith_run_id"],
                agent_name=row["agent_name"],
                tool_calls=row["tool_calls"],
                token_usage=row["token_usage"],
                latency_ms=row["latency_ms"],
                status=row["status"],
                error=row["error"],
            )

        if trace_rows:
            all_rows.extend(trace_rows)

    await agent_trace_repository.session.commit()

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    total_cost = Decimal("0")
    total_latency_ms = 0
    total_retries = 0
    total_errors = 0

    for row in all_rows:
        token_usage = row["token_usage"]

        total_prompt_tokens += int(token_usage.get("prompt_tokens", 0))
        total_completion_tokens += int(
            token_usage.get("completion_tokens", 0),
        )
        total_tokens += int(token_usage.get("total_tokens", 0))
        total_cost += Decimal(
            str(token_usage.get("total_cost", "0")),
        )
        total_latency_ms += row["latency_ms"] or 0
        total_retries += int(token_usage.get("retry_count", 0))
        total_errors += int(row["error"] is not None)

    return {
        "research_run_count": len(completed_runs),
        "trace_count": len(all_rows),
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "total_latency_ms": total_latency_ms,
        "total_retries": total_retries,
        "total_errors": total_errors,
    }