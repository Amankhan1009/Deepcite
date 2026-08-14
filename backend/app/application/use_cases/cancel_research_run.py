import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.agents.task_registry import cancel as cancel_task
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)

CANCELLABLE_STATUSES = {
    "planning",
    "researching",
    "verifying",
    "reasoning",
    "fact_checking",
    "awaiting_approval",
    "generating_report",
}


class CancellableResearchRunNotFoundError(Exception):
    """Raised when a cancellable run is missing or owned by another user."""


class ResearchRunNotCancellableError(Exception):
    """Raised when the run is already in a terminal state."""


async def cancel_research_run(
    db: AsyncSession,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ResearchRun:
    """Cancel an active or approval-paused research run."""

    repository = ResearchRunRepository(db)

    run = await repository.get_for_user(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if run is None:
        raise CancellableResearchRunNotFoundError

    if run.status not in CANCELLABLE_STATUSES:
        raise ResearchRunNotCancellableError

    run.status = "cancelled"
    await db.commit()
    await db.refresh(run)

    cancel_task(str(run.id))

    return run