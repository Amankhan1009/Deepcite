import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.citation import Citation
from app.infrastructure.db.models.claim import Claim
from app.infrastructure.db.models.source import Source


class CitationRepository:
    """Database access for report citations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        report_id: uuid.UUID,
        claim_id: uuid.UUID,
        source_id: uuid.UUID,
        inline_marker: str,
    ) -> Citation:
        citation = Citation(
            report_id=report_id,
            claim_id=claim_id,
            source_id=source_id,
            inline_marker=inline_marker,
        )

        self.session.add(citation)
        await self.session.commit()
        await self.session.refresh(citation)

        return citation

    async def list_for_report(
        self,
        report_id: uuid.UUID,
    ) -> list[Citation]:
        result = await self.session.execute(
            select(Citation)
            .where(Citation.report_id == report_id)
            .order_by(Citation.created_at)
        )

        return list(result.scalars().all())

    async def list_details_for_report(
        self,
        report_id: uuid.UUID,
    ) -> list[dict]:
        result = await self.session.execute(
            select(Citation, Claim, Source)
            .join(Claim, Claim.id == Citation.claim_id)
            .join(Source, Source.id == Citation.source_id)
            .where(Citation.report_id == report_id)
            .order_by(Citation.created_at)
        )

        details = []

        for citation, claim, source in result.all():
            details.append(
                {
                    "id": citation.id,
                    "inline_marker": citation.inline_marker,
                    "claim_id": claim.id,
                    "claim_text": claim.text,
                    "confidence_score": claim.confidence_score,
                    "fact_check_status": claim.fact_check_status,
                    "source_id": source.id,
                    "source_url": source.url,
                    "source_title": source.title,
                    "source_reliability_score": source.reliability_score,
                }
            )

        return details