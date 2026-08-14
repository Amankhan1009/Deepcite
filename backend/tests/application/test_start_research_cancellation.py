import uuid
from unittest.mock import AsyncMock

from sqlalchemy import delete, select

from app.application.use_cases.start_research_run import execute_research_run
from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.session import AsyncSessionLocal


async def test_execute_research_run_keeps_cancelled_terminal(monkeypatch):
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="hashed",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Cancellation terminal workspace",
        )
        session.add(workspace)
        await session.flush()

        run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="Should this cancelled run complete?",
            status="cancelled",
        )
        session.add(run)
        await session.commit()

        run_id = run.id
        workspace_id = workspace.id
        user_id = user.id

    monkeypatch.setattr(
        "app.application.use_cases.start_research_run.run_research_graph",
        AsyncMock(
            return_value={
                "plan": {
                    "sub_questions": ["q1", "q2", "q3"],
                    "strategy": "s",
                },
                "report": {
                    "content_markdown": "# Report",
                    "executive_summary": "Summary",
                },
            }
        ),
    )

    await execute_research_run(
        research_run_id=str(run_id),
        question="Should this cancelled run complete?",
    )

    async with AsyncSessionLocal() as session:
        persisted = await session.get(ResearchRun, run_id)
        assert persisted is not None
        assert persisted.status == "cancelled"

        report = (
            await session.execute(
                select(Report).where(Report.research_run_id == run_id)
            )
        ).scalar_one_or_none()
        assert report is None

        await session.execute(delete(ResearchRun).where(ResearchRun.id == run_id))
        await session.execute(delete(Workspace).where(Workspace.id == workspace_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
