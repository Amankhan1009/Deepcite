import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.create_workspace import create_workspace
from app.application.use_cases.delete_workspace import delete_workspace
from app.application.use_cases.get_workspace import (
    WorkspaceAccessDeniedError,
    WorkspaceNotFoundError,
    get_workspace,
)
from app.application.use_cases.list_research_history import (
    list_research_history,
)
from app.application.use_cases.list_workspaces import list_workspaces
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)
from app.infrastructure.db.repositories.workspace_repository import (
    WorkspaceRepository,
)
from app.infrastructure.db.session import get_db
from app.presentation.api.v1.deps import get_current_user
from app.presentation.schemas.settings import ResearchHistoryItemResponse
from app.presentation.schemas.workspace import (
    CreateWorkspaceRequest,
    WorkspaceResponse,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = WorkspaceRepository(db)
    workspace = await create_workspace(repo, current_user.id, payload.name, payload.description)
    return WorkspaceResponse.model_validate(workspace)


@router.get("", response_model=list[WorkspaceResponse])
async def list_mine(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = WorkspaceRepository(db)
    workspaces = await list_workspaces(repo, current_user.id)
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.get(
    "/{workspace_id}/research",
    response_model=list[ResearchHistoryItemResponse],
)
async def list_research(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    history = await list_research_history(
        ResearchRunRepository(db),
        current_user.id,
        workspace_id,
    )

    return [
        ResearchHistoryItemResponse.model_validate(item)
        for item in history
    ]

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_one(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = WorkspaceRepository(db)
    try:
        workspace = await get_workspace(repo, workspace_id, current_user.id)
    except WorkspaceNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found") from e
    except WorkspaceAccessDeniedError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found") from e
    return WorkspaceResponse.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = WorkspaceRepository(db)
    try:
        await delete_workspace(repo, workspace_id, current_user.id)
    except WorkspaceNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found") from e
    except WorkspaceAccessDeniedError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found") from e