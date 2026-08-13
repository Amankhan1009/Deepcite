import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.evidence import Evidence


class EvidenceRepository:
    """Database access for evidence extracted from research sources."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        research_run_id: uuid.UUID,
        source_id: uuid.UUID,
        claim_text: str,
    ) -> Evidence:
        evidence = Evidence(
            research_run_id=research_run_id,
            source_id=source_id,
            claim_text=claim_text,
        )

        self.session.add(evidence)
        await self.session.commit()
        await self.session.refresh(evidence)

        return evidence

    async def list_for_research_run(
        self,
        research_run_id: uuid.UUID,
    ) -> list[Evidence]:
        result = await self.session.execute(
            select(Evidence)
            .where(Evidence.research_run_id == research_run_id)
            .order_by(Evidence.created_at)
        )

        return list(result.scalars().all())