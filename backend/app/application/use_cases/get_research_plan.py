import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.research_plan import ResearchPlan
from app.infrastructure.db.repositories.research_plan_repository import (
    ResearchPlanRepository,
)
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)


class ResearchRunNotFoundError(Exception):
    """Raised when a research run is missing or not owned by the user."""


async def get_research_plan(
    db: AsyncSession,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ResearchPlan | None:
    """Retrieve the generated research plan and strategy for a research run."""
    run_repository = ResearchRunRepository(db)
    run = await run_repository.get_for_user(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if run is None or run.deleted_at is not None:
        raise ResearchRunNotFoundError

    plan_repository = ResearchPlanRepository(db)
    return await plan_repository.get_for_research_run(research_run_id)

