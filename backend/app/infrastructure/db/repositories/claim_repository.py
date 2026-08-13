import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.claim import Claim


class ClaimRepository:
    """Database access for reasoning claims."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        research_run_id: uuid.UUID,
        text: str,
        supporting_evidence_ids: list[str],
        contradicting_evidence_ids: list[str],
        fact_check_status: str = "unverified",
        confidence_score: float = 0.0,
    ) -> Claim:
        claim = Claim(
            research_run_id=research_run_id,
            text=text,
            supporting_evidence_ids=supporting_evidence_ids,
            contradicting_evidence_ids=contradicting_evidence_ids,
            fact_check_status=fact_check_status,
            confidence_score=confidence_score,
        )

        self.session.add(claim)
        await self.session.commit()
        await self.session.refresh(claim)

        return claim

    async def list_for_research_run(
        self,
        research_run_id: uuid.UUID,
    ) -> list[Claim]:
        result = await self.session.execute(
            select(Claim)
            .where(Claim.research_run_id == research_run_id)
            .order_by(Claim.created_at)
        )

        return list(result.scalars().all())