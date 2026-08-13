import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateWorkspaceRequest(BaseModel):
    name: str
    description: str | None = None


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}