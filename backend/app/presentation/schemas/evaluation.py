import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class EvaluationResponse(BaseModel):
    id: uuid.UUID
    research_run_id: uuid.UUID
    dimension: str
    score: Decimal
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationSummaryItem(BaseModel):
    dimension: str
    average_score: Decimal
    run_count: int


class EvaluationSummaryResponse(BaseModel):
    dimensions: list[EvaluationSummaryItem]
