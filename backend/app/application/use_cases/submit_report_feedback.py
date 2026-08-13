import uuid

from app.infrastructure.db.models.report_feedback import ReportFeedback
from app.infrastructure.db.repositories.report_feedback_repository import (
    ReportFeedbackRepository,
)
from app.infrastructure.db.repositories.report_repository import ReportRepository


class ReportFeedbackTargetNotFoundError(Exception):
    """Raised when a report does not exist or is not owned by the user."""


async def submit_report_feedback(
    *,
    report_repository: ReportRepository,
    feedback_repository: ReportFeedbackRepository,
    report_id: uuid.UUID,
    user_id: uuid.UUID,
    decision: str | None,
    comment: str | None,
    rating: int | None,
) -> ReportFeedback:
    report = await report_repository.get_for_user_by_id(
        report_id=report_id,
        user_id=user_id,
    )

    if report is None:
        raise ReportFeedbackTargetNotFoundError

    return await feedback_repository.create(
        report_id=report_id,
        user_id=user_id,
        decision=decision,
        comment=comment,
        rating=rating,
    )