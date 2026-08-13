import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.workspace import Workspace


class WorkspaceRepository:
    """All DB access for Workspace. No auth/ownership logic here —
    callers (use cases) decide which rows they're allowed to touch."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: uuid.UUID, name: str, description: str | None) -> Workspace:
        workspace = Workspace(user_id=user_id, name=name, description=description)
        self.session.add(workspace)
        await self.session.commit()
        await self.session.refresh(workspace)
        return workspace

    async def list_for_user(self, user_id: uuid.UUID) -> list[Workspace]:
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.user_id == user_id, Workspace.deleted_at.is_(None)
            )
        )
        return list(result.scalars().all())

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        result = await self.session.execute(
            select(Workspace).where(
                Workspace.id == workspace_id, Workspace.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, workspace: Workspace) -> None:
        workspace.deleted_at = datetime.now(UTC)
        await self.session.commit()