import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.workspace import Workspace


class ResearchRunRepository:
    """Database access for ownership-scoped research runs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_user(
        self,
        research_run_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ResearchRun | None:
        result = await self.session.execute(
            select(ResearchRun).where(
                ResearchRun.id == research_run_id,
                ResearchRun.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_workspace(
        self,
        *,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> list[tuple[ResearchRun, uuid.UUID | None]]:
        result = await self.session.execute(
            select(ResearchRun, Report.id)
            .join(
                Workspace,
                Workspace.id == ResearchRun.workspace_id,
            )
            .outerjoin(
                Report,
                Report.research_run_id == ResearchRun.id,
            )
            .where(
                ResearchRun.user_id == user_id,
                ResearchRun.workspace_id == workspace_id,
                ResearchRun.deleted_at.is_(None),
                Workspace.user_id == user_id,
                Workspace.deleted_at.is_(None),
            )
            .order_by(desc(ResearchRun.created_at))
        )

        return list(result.all())

    async def list_completed_for_user(
        self,
        user_id: uuid.UUID,
    ) -> list[ResearchRun]:
        result = await self.session.execute(
            select(ResearchRun).where(
                ResearchRun.user_id == user_id,
                ResearchRun.status == "completed",
                ResearchRun.deleted_at.is_(None),
            )
        )

        return list(result.scalars().all())