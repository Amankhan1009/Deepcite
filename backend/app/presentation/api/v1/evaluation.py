import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.get_evaluation_summary import (
    get_evaluation_summary,
)
from app.application.use_cases.get_research_evaluation import (
    ResearchEvaluationNotFoundError,
    get_research_evaluation,
)
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.evaluation_repository import (
    EvaluationRepository,
)
from app.infrastructure.db.session import get_db
from app.presentation.api.v1.deps import get_current_user
from app.presentation.schemas.evaluation import (
    EvaluationResponse,
    EvaluationSummaryItem,
    EvaluationSummaryResponse,
)

router = APIRouter(tags=["evaluation"])


@router.get(
    "/research/{research_run_id}/evaluation",
    response_model=list[EvaluationResponse],
)
async def get_run_evaluation(
    research_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repository = EvaluationRepository(db)

    try:
        evaluations = await get_research_evaluation(
            repository=repository,
            research_run_id=research_run_id,
            user_id=current_user.id,
        )
    except ResearchEvaluationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        ) from error

    return [
        EvaluationResponse.model_validate(evaluation)
        for evaluation in evaluations
    ]


@router.get(
    "/evaluation/summary",
    response_model=EvaluationSummaryResponse,
)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repository = EvaluationRepository(db)

    summary = await get_evaluation_summary(
        repository=repository,
        user_id=current_user.id,
    )

    return EvaluationSummaryResponse(
        dimensions=[
            EvaluationSummaryItem.model_validate(item)
            for item in summary
        ]
    )
