import uuid

from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.workspace_repository import WorkspaceRepository


class WorkspaceNotFoundError(Exception):
    pass


class WorkspaceAccessDeniedError(Exception):
    pass


async def get_workspace(
    repo: WorkspaceRepository, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> Workspace:
    workspace = await repo.get_by_id(workspace_id)
    if workspace is None:
        raise WorkspaceNotFoundError()
    if workspace.user_id != user_id:
        raise WorkspaceAccessDeniedError()
    return workspace