import uuid

from app.application.use_cases.get_workspace import get_workspace
from app.infrastructure.db.repositories.workspace_repository import WorkspaceRepository


async def delete_workspace(
    repo: WorkspaceRepository, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    workspace = await get_workspace(repo, workspace_id, user_id)  # raises if not found/not owned
    await repo.soft_delete(workspace)