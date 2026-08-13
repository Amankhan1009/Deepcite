import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.research_run import ResearchRun


class ReportRepository:
    """Database access for generated research reports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        research_run_id: uuid.UUID,
        content_markdown: str,
        executive_summary: str | None = None,
        overall_confidence_score: Decimal | None = None,
    ) -> Report:
        report = Report(
            research_run_id=research_run_id,
            content_markdown=content_markdown,
            executive_summary=executive_summary,
            overall_confidence_score=overall_confidence_score,
        )

        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)

        return report

    async def get_for_research_run(
        self,
        research_run_id: uuid.UUID,
    ) -> Report | None:
        result = await self.session.execute(
            select(Report).where(Report.research_run_id == research_run_id)
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        research_run_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Report | None:
        result = await self.session.execute(
            select(Report)
            .join(ResearchRun, Report.research_run_id == ResearchRun.id)
            .where(
                Report.research_run_id == research_run_id,
                ResearchRun.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_for_user_by_id(
        self,
        *,
        report_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Report | None:
        result = await self.session.execute(
            select(Report)
            .join(
                ResearchRun,
                Report.research_run_id == ResearchRun.id,
            )
            .where(
                Report.id == report_id,
                ResearchRun.user_id == user_id,
                ResearchRun.deleted_at.is_(None),
            )
        )

        return result.scalar_one_or_none()