import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.research_plan import ResearchPlan


class ResearchPlanRepository:
    """Database access for research plans."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        research_run_id: uuid.UUID,
        sub_questions: list[str],
        strategy: str,
    ) -> ResearchPlan:
        plan = ResearchPlan(
            research_run_id=research_run_id,
            sub_questions=sub_questions,
            strategy=strategy,
        )

        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)

        return plan

    async def get_for_research_run(
        self,
        research_run_id: uuid.UUID,
    ) -> ResearchPlan | None:
        result = await self.session.execute(
            select(ResearchPlan).where(
                ResearchPlan.research_run_id == research_run_id
            )
        )

        return result.scalar_one_or_none()