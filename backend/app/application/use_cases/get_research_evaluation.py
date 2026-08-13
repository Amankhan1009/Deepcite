import uuid

from app.infrastructure.db.models.evaluation import Evaluation
from app.infrastructure.db.repositories.evaluation_repository import (
    EvaluationRepository,
)


class ResearchEvaluationNotFoundError(Exception):
    """Raised when a run has no accessible evaluation data."""


async def get_research_evaluation(
    repository: EvaluationRepository,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[Evaluation]:
    """Return evaluations for one research run owned by the user."""

    evaluations = await repository.list_for_user_research_run(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if not evaluations:
        raise ResearchEvaluationNotFoundError

    return evaluations
