from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.workspace_repository import WorkspaceRepository


async def create_workspace(
    repo: WorkspaceRepository, user_id, name: str, description: str | None
) -> Workspace:
    return await repo.create(user_id=user_id, name=name, description=description)