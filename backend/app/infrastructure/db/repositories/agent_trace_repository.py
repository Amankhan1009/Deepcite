import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.agent_trace import AgentTrace
from app.infrastructure.db.models.research_run import ResearchRun


class AgentTraceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        *,
        research_run_id: uuid.UUID,
        langsmith_run_id: uuid.UUID,
        agent_name: str,
        tool_calls: list[dict[str, Any]],
        token_usage: dict[str, Any],
        latency_ms: int | None,
        status: str,
        error: str | None,
    ) -> AgentTrace:
        result = await self.session.execute(
            select(AgentTrace).where(
                AgentTrace.langsmith_run_id == langsmith_run_id,
            )
        )
        trace = result.scalar_one_or_none()

        if trace is None:
            trace = AgentTrace(
                research_run_id=research_run_id,
                langsmith_run_id=langsmith_run_id,
                agent_name=agent_name,
            )
            self.session.add(trace)

        trace.tool_calls = tool_calls
        trace.token_usage = token_usage
        trace.latency_ms = latency_ms
        trace.status = status
        trace.error = error

        await self.session.flush()
        return trace

    async def list_for_user_research_run(
        self,
        *,
        research_run_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[AgentTrace]:
        result = await self.session.execute(
            select(AgentTrace)
            .join(
                ResearchRun,
                ResearchRun.id == AgentTrace.research_run_id,
            )
            .where(
                AgentTrace.research_run_id == research_run_id,
                ResearchRun.user_id == user_id,
                ResearchRun.deleted_at.is_(None),
            )
            .order_by(AgentTrace.created_at),
        )

        return list(result.scalars().all())

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[AgentTrace]:
        result = await self.session.execute(
            select(AgentTrace)
            .join(
                ResearchRun,
                ResearchRun.id == AgentTrace.research_run_id,
            )
            .where(
                ResearchRun.user_id == user_id,
                ResearchRun.deleted_at.is_(None),
            )
            .order_by(AgentTrace.created_at),
        )

        return list(result.scalars().all())