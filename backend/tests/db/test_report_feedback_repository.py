import uuid

from sqlalchemy import delete

from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.report_feedback import ReportFeedback
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.report_feedback_repository import (
    ReportFeedbackRepository,
)
from app.infrastructure.db.session import AsyncSessionLocal


async def test_report_feedback_repository_create_and_list():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Feedback Repository Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What are AI safety risks?",
            status="completed",
        )
        session.add(research_run)
        await session.flush()

        report = Report(
            research_run_id=research_run.id,
            content_markdown="# AI safety",
        )
        session.add(report)
        await session.flush()

        repository = ReportFeedbackRepository(session)

        feedback = await repository.create(
            report_id=report.id,
            user_id=user.id,
            decision="approved",
            comment="Clear and well cited.",
            rating=5,
        )

        loaded = await repository.list_for_report(report.id)

        assert len(loaded) == 1
        assert loaded[0].id == feedback.id
        assert loaded[0].decision == "approved"
        assert loaded[0].rating == 5

        await session.execute(
            delete(ReportFeedback).where(
                ReportFeedback.report_id == report.id,
            )
        )
        await session.execute(
            delete(Report).where(Report.id == report.id)
        )
        await session.execute(
            delete(ResearchRun).where(
                ResearchRun.id == research_run.id,
            )
        )
        await session.execute(
            delete(Workspace).where(Workspace.id == workspace.id)
        )
        await session.execute(
            delete(User).where(User.id == user.id)
        )
        await session.commit()