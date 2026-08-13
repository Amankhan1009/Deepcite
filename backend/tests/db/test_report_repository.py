import uuid

from sqlalchemy import delete

from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.report_repository import ReportRepository
from app.infrastructure.db.session import AsyncSessionLocal


async def test_report_repository_create_and_get():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Report Repository Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What are the risks of AI systems?",
            status="completed",
        )
        session.add(research_run)
        await session.flush()

        repository = ReportRepository(session)

        report = await repository.create(
            research_run_id=research_run.id,
            content_markdown="# AI Risks\n\nEvidence-backed finding [Source 1].",
            executive_summary="Evidence-backed AI risk summary [Source 1].",
        )

        loaded = await repository.get_for_research_run(research_run.id)

        assert loaded is not None
        assert loaded.id == report.id
        assert loaded.research_run_id == research_run.id
        assert "[Source 1]" in loaded.content_markdown

        await session.execute(
            delete(Report).where(Report.research_run_id == research_run.id)
        )
        await session.execute(
            delete(ResearchRun).where(ResearchRun.id == research_run.id)
        )
        await session.execute(
            delete(Workspace).where(Workspace.id == workspace.id)
        )
        await session.execute(
            delete(User).where(User.id == user.id)
        )
        await session.commit()


async def test_report_repository_returns_empty_for_unknown_run():
    async with AsyncSessionLocal() as session:
        repository = ReportRepository(session)

        result = await repository.get_for_research_run(uuid.uuid4())

        assert result is None