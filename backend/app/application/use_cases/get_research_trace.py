import uuid

from app.infrastructure.db.repositories.agent_trace_repository import (
    AgentTraceRepository,
)
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)
from app.infrastructure.observability.langsmith_trace_reader import (
    LangSmithTraceReader,
)


class ResearchTraceNotFoundError(Exception):
    """Raised when a trace does not exist or is not owned by the user."""


async def get_research_trace(
    *,
    research_run_repository: ResearchRunRepository,
    agent_trace_repository: AgentTraceRepository,
    trace_reader: LangSmithTraceReader,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
):
    research_run = await research_run_repository.get_for_user(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if research_run is None:
        raise ResearchTraceNotFoundError

    trace_rows = trace_reader.read_for_research_run(research_run_id)

    if not trace_rows:
        existing_rows = await agent_trace_repository.list_for_user_research_run(
            research_run_id=research_run_id,
            user_id=user_id,
        )

        if not existing_rows:
            raise ResearchTraceNotFoundError

        return existing_rows

    for row in trace_rows:
        await agent_trace_repository.upsert(
            research_run_id=research_run_id,
            langsmith_run_id=row["langsmith_run_id"],
            agent_name=row["agent_name"],
            tool_calls=row["tool_calls"],
            token_usage=row["token_usage"],
            latency_ms=row["latency_ms"],
            status=row["status"],
            error=row["error"],
        )

    await agent_trace_repository.session.commit()

    return await agent_trace_repository.list_for_user_research_run(
        research_run_id=research_run_id,
        user_id=user_id,
    )