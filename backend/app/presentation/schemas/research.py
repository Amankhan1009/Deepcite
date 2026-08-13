import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class StartResearchRequest(BaseModel):
    workspace_id: uuid.UUID
    question: str


class ResearchRunResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    question: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CitationResponse(BaseModel):
    id: uuid.UUID
    inline_marker: str
    claim_id: uuid.UUID
    claim_text: str
    confidence_score: float
    fact_check_status: str
    source_id: uuid.UUID
    source_url: str
    source_title: str | None
    source_reliability_score: float | None


class ReportResponse(BaseModel):
    id: uuid.UUID
    research_run_id: uuid.UUID
    content_markdown: str
    executive_summary: str | None
    overall_confidence_score: Decimal | None
    citations: list[CitationResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}