import uuid
from decimal import Decimal

from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.evaluation import Evaluation
from app.infrastructure.db.models.research_run import ResearchRun


class EvaluationRepository:
    """Database access for per-run evaluation scores."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        research_run_id: uuid.UUID,
        dimension: str,
        score: Decimal | float,
        details: dict,
    ) -> Evaluation:
        evaluation = Evaluation(
            research_run_id=research_run_id,
            dimension=dimension,
            score=score,
            details=details,
        )

        self.session.add(evaluation)
        await self.session.commit()
        await self.session.refresh(evaluation)

        return evaluation

    async def list_for_research_run(
        self,
        research_run_id: uuid.UUID,
    ) -> list[Evaluation]:
        result = await self.session.execute(
            select(Evaluation)
            .where(Evaluation.research_run_id == research_run_id)
            .order_by(Evaluation.created_at),
        )

        return list(result.scalars().all())

    async def list_for_user_research_run(
        self,
        *,
        research_run_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[Evaluation]:
        result = await self.session.execute(
            select(Evaluation)
            .join(
                ResearchRun,
                ResearchRun.id == Evaluation.research_run_id,
            )
            .where(
                Evaluation.research_run_id == research_run_id,
                ResearchRun.user_id == user_id,
                ResearchRun.deleted_at.is_(None),
            )
            .order_by(Evaluation.created_at),
        )

        return list(result.scalars().all())

    async def aggregate_for_user(
        self,
        user_id: uuid.UUID,
    ) -> list[dict]:
        result = await self.session.execute(
            select(
                Evaluation.dimension,
                cast(
                    func.avg(Evaluation.score),
                    Numeric(5, 4),
                ).label("average_score"),
                func.count(Evaluation.id).label("run_count"),
            )
            .join(
                ResearchRun,
                ResearchRun.id == Evaluation.research_run_id,
            )
            .where(
                ResearchRun.user_id == user_id,
                ResearchRun.status == "completed",
                ResearchRun.deleted_at.is_(None),
            )
            .group_by(Evaluation.dimension)
            .order_by(Evaluation.dimension),
        )

        return [
            {
                "dimension": row.dimension,
                "average_score": row.average_score,
                "run_count": row.run_count,
            }
            for row in result
        ]
