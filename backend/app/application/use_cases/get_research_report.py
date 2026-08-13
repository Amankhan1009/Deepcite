import uuid

from app.infrastructure.db.models.report import Report
from app.infrastructure.db.repositories.report_repository import ReportRepository


class ReportNotFoundError(Exception):
    """Raised when a report does not exist or is not owned by the user."""


async def get_research_report(
    repository: ReportRepository,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Report:
    report = await repository.get_for_user(research_run_id, user_id)

    if report is None:
        raise ReportNotFoundError

    return report