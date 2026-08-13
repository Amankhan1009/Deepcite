import uuid

from app.infrastructure.db.repositories.evaluation_repository import (
    EvaluationRepository,
)


async def get_evaluation_summary(
    repository: EvaluationRepository,
    user_id: uuid.UUID,
) -> list[dict]:
    """Return aggregate evaluation scores for the authenticated user."""

    return await repository.aggregate_for_user(user_id)
