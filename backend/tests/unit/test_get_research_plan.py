import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.application.use_cases.get_research_plan import (
    ResearchRunNotFoundError,
    get_research_plan,
)
from app.infrastructure.db.models.research_plan import ResearchPlan
from app.infrastructure.db.models.research_run import ResearchRun


@pytest.mark.asyncio
async def test_get_research_plan_success():
    db = AsyncMock()
    run_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_run = ResearchRun(
        id=run_id,
        user_id=user_id,
        workspace_id=uuid.uuid4(),
        question="How does RAG mitigate hallucinations?",
        status="completed",
        deleted_at=None,
    )
    mock_plan = ResearchPlan(
        id=uuid.uuid4(),
        research_run_id=run_id,
        strategy="Synthesize empirical retrieval benchmarks",
        sub_questions=["What is hybrid search?", "How does reranking help?"],
    )

    with (
        patch(
            "app.application.use_cases.get_research_plan.ResearchRunRepository"
        ) as mock_run_repo_cls,
        patch(
            "app.application.use_cases.get_research_plan.ResearchPlanRepository"
        ) as mock_plan_repo_cls,
    ):
        mock_run_repo = AsyncMock()
        mock_run_repo.get_for_user.return_value = mock_run
        mock_run_repo_cls.return_value = mock_run_repo

        mock_plan_repo = AsyncMock()
        mock_plan_repo.get_for_research_run.return_value = mock_plan
        mock_plan_repo_cls.return_value = mock_plan_repo

        result = await get_research_plan(
            db=db,
            research_run_id=run_id,
            user_id=user_id,
        )

        assert result is not None
        assert result.strategy == "Synthesize empirical retrieval benchmarks"
        assert len(result.sub_questions) == 2


@pytest.mark.asyncio
async def test_get_research_plan_run_not_found():
    db = AsyncMock()
    run_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with patch(
        "app.application.use_cases.get_research_plan.ResearchRunRepository"
    ) as mock_run_repo_cls:
        mock_run_repo = AsyncMock()
        mock_run_repo.get_for_user.return_value = None
        mock_run_repo_cls.return_value = mock_run_repo

        with pytest.raises(ResearchRunNotFoundError):
            await get_research_plan(
                db=db,
                research_run_id=run_id,
                user_id=user_id,
            )
