import uuid

from sqlalchemy import delete, select

from app.application.use_cases.persist_research_result import (
    persist_evaluation_results,
)
from app.infrastructure.db.models.evaluation import Evaluation
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.session import AsyncSessionLocal


async def test_persist_evaluation_results_is_idempotent():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Evaluation Persistence Test",
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

        result = {
            "evaluations": [
                {
                    "dimension": "planning_quality",
                    "score": 0.9,
                    "details": {
                        "rationale": "The plan covers the question.",
                    },
                },
                {
                    "dimension": "search_quality",
                    "score": 0.8,
                    "details": {
                        "rationale": "The sources are relevant.",
                    },
                },
                {
                    "dimension": "source_reliability",
                    "score": 0.85,
                    "details": {
                        "source_count": 2,
                    },
                },
            ],
        }

        await persist_evaluation_results(
            db=session,
            run=research_run,
            result=result,
        )
        await persist_evaluation_results(
            db=session,
            run=research_run,
            result=result,
        )

        evaluations = list(
            (
                await session.execute(
                    select(Evaluation).where(
                        Evaluation.research_run_id == research_run.id,
                    )
                )
            ).scalars()
        )

        dimensions = {
            evaluation.dimension
            for evaluation in evaluations
        }

        assert len(evaluations) == 4
        assert dimensions == {
            "planning_quality",
            "search_quality",
            "source_reliability",
            "report_quality",
        }

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