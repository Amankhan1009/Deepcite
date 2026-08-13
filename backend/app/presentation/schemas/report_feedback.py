import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReportFeedbackRequest(BaseModel):
    decision: Literal["approved", "rejected"] | None = None
    comment: str | None = Field(default=None, max_length=2000)
    rating: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def require_feedback_value(self):
        if (
            self.decision is None
            and self.comment is None
            and self.rating is None
        ):
            raise ValueError(
                "Provide a decision, comment, or rating",
            )

        return self


class ReportFeedbackResponse(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    user_id: uuid.UUID
    decision: str | None
    comment: str | None
    rating: int | None
    created_at: datetime

    model_config = {"from_attributes": True}