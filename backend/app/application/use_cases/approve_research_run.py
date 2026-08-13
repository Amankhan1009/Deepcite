import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.persist_research_result import (
    persist_evaluation_results,
    persist_report_result,
)
from app.infrastructure.agents.graph import approve_research_graph
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)


class ResearchRunNotFoundError(Exception):
    """Raised when a run is missing or belongs to another user."""


class ResearchRunNotAwaitingApprovalError(Exception):
    """Raised when a run cannot currently be approved."""


async def approve_research_run(
    db: AsyncSession,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ResearchRun:
    """Approve and resume a paused research run."""

    repository = ResearchRunRepository(db)

    run = await repository.get_for_user(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if run is None:
        raise ResearchRunNotFoundError

    if run.status != "awaiting_approval":
        raise ResearchRunNotAwaitingApprovalError

    result = await approve_research_graph(str(run.id))

    if result.get("__interrupt__"):
        raise ResearchRunNotAwaitingApprovalError

    await persist_report_result(
        db=db,
        run=run,
        result=result,
    )
    await persist_evaluation_results(
        db=db,
        run=run,
        result=result,
    )
    run.status = "completed"

    await db.commit()
    await db.close()

    return run
