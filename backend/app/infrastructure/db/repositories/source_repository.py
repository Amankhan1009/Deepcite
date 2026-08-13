import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.source import Source


class SourceRepository:
    """Database access for sources belonging to a research run."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        research_run_id: uuid.UUID,
        url: str,
        title: str | None,
        raw_content_ref: str | None,
        reliability_score: float | None = None,
    ) -> Source:
        source = Source(
            research_run_id=research_run_id,
            url=url,
            title=title,
            raw_content_ref=raw_content_ref,
            reliability_score=reliability_score,
        )

        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)

        return source

    async def list_for_research_run(
        self,
        research_run_id: uuid.UUID,
    ) -> list[Source]:
        result = await self.session.execute(
            select(Source)
            .where(Source.research_run_id == research_run_id)
            .order_by(Source.created_at)
        )

        return list(result.scalars().all())