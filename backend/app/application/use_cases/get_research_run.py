import uuid

from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)


class ResearchRunStatusNotFoundError(Exception):
    """Raised when a research run is missing or not owned by the user."""


async def get_research_run(
    repository: ResearchRunRepository,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ResearchRun:
    run = await repository.get_for_user(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if run is None or run.deleted_at is not None:
        raise ResearchRunStatusNotFoundError

    return run