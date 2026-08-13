import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.report_feedback import ReportFeedback


class ReportFeedbackRepository:
    """Database access for report feedback events."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        report_id: uuid.UUID,
        user_id: uuid.UUID,
        decision: str | None,
        comment: str | None,
        rating: int | None,
    ) -> ReportFeedback:
        feedback = ReportFeedback(
            report_id=report_id,
            user_id=user_id,
            decision=decision,
            comment=comment,
            rating=rating,
        )

        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)

        return feedback

    async def list_for_report(
        self,
        report_id: uuid.UUID,
    ) -> list[ReportFeedback]:
        result = await self.session.execute(
            select(ReportFeedback)
            .where(ReportFeedback.report_id == report_id)
            .order_by(ReportFeedback.created_at),
        )

        return list(result.scalars().all())