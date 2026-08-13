from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.workspace_repository import WorkspaceRepository


async def list_workspaces(repo: WorkspaceRepository, user_id) -> list[Workspace]:
    return await repo.list_for_user(user_id)