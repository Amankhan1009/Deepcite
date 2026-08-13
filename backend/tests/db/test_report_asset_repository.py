import uuid

from sqlalchemy import delete

from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.report_asset import ReportAsset
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.report_asset_repository import (
    ReportAssetRepository,
)
from app.infrastructure.db.session import AsyncSessionLocal


async def test_report_asset_repository_create_and_list():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Report Asset Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What are production AI risks?",
            status="completed",
        )
        session.add(research_run)
        await session.flush()

        report = Report(
            research_run_id=research_run.id,
            content_markdown="# Report",
            executive_summary="Summary",
        )
        session.add(report)
        await session.flush()

        repository = ReportAssetRepository(session)

        asset = await repository.create(
            report_id=report.id,
            asset_type="chart",
            file_path="generated_assets/test.png",
            caption="Production AI Risks",
        )

        assets = await repository.list_for_report(report.id)

        assert len(assets) == 1
        assert assets[0].id == asset.id
        assert assets[0].asset_type == "chart"
        assert assets[0].file_path == "generated_assets/test.png"
        assert assets[0].caption == "Production AI Risks"

        await session.execute(
            delete(ReportAsset).where(
                ReportAsset.report_id == report.id
            )
        )
        await session.execute(
            delete(Report).where(
                Report.id == report.id
            )
        )
        await session.execute(
            delete(ResearchRun).where(
                ResearchRun.id == research_run.id
            )
        )
        await session.execute(
            delete(Workspace).where(
                Workspace.id == workspace.id
            )
        )
        await session.execute(
            delete(User).where(
                User.id == user.id
            )
        )
        await session.commit()