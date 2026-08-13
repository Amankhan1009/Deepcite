import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UpdateSettingsRequest(BaseModel):
    display_name: str | None = Field(
        default=None,
        max_length=120,
    )
    timezone: str = Field(
        default="UTC",
        max_length=64,
    )
    theme: str = Field(
        default="system",
        pattern="^(light|dark|system)$",
    )


class UserSettingsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str | None
    timezone: str
    theme: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchHistoryItemResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    question: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    report_id: uuid.UUID | None