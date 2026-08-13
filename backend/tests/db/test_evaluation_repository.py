import uuid
from decimal import Decimal

from sqlalchemy import delete

from app.infrastructure.db.models.evaluation import Evaluation
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.evaluation_repository import (
    EvaluationRepository,
)
from app.infrastructure.db.session import AsyncSessionLocal


async def test_evaluation_repository_create_and_list():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Evaluation Repository Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What are AI risks?",
            status="completed",
        )
        session.add(research_run)
        await session.flush()

        repository = EvaluationRepository(session)

        evaluation = await repository.create(
            research_run_id=research_run.id,
            dimension="planning_quality",
            score=Decimal("0.9000"),
            details={"rationale": "Focused plan."},
        )

        evaluations = await repository.list_for_research_run(
            research_run.id,
        )

        assert len(evaluations) == 1
        assert evaluations[0].id == evaluation.id
        assert evaluations[0].dimension == "planning_quality"
        assert evaluations[0].score == Decimal("0.9000")
        assert evaluations[0].details["rationale"] == "Focused plan."

        await session.execute(
            delete(Evaluation).where(
                Evaluation.research_run_id == research_run.id,
            )
        )
        await session.execute(
            delete(ResearchRun).where(
                ResearchRun.id == research_run.id,
            )
        )
        await session.execute(
            delete(Workspace).where(
                Workspace.id == workspace.id,
            )
        )
        await session.execute(
            delete(User).where(
                User.id == user.id,
            )
        )
        await session.commit()


async def test_evaluation_repository_returns_empty_for_unknown_run():
    async with AsyncSessionLocal() as session:
        repository = EvaluationRepository(session)

        result = await repository.list_for_research_run(uuid.uuid4())

        assert result == []