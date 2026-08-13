import uuid
from dataclasses import dataclass, field

from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.report_asset import ReportAsset
from app.infrastructure.db.repositories.citation_repository import (
    CitationRepository,
)
from app.infrastructure.db.repositories.report_asset_repository import (
    ReportAssetRepository,
)
from app.infrastructure.db.repositories.report_repository import ReportRepository


class ReportExportNotFoundError(Exception):
    """Raised when a report does not exist or is not owned by the user."""


@dataclass(frozen=True)
class ExportableReport:
    report: Report
    assets: list[ReportAsset]
    citations: list[dict] = field(default_factory=list)


async def get_exportable_report(
    *,
    report_repository: ReportRepository,
    asset_repository: ReportAssetRepository,
    citation_repository: CitationRepository,
    report_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ExportableReport:
    report = await report_repository.get_for_user_by_id(
        report_id=report_id,
        user_id=user_id,
    )

    if report is None:
        raise ReportExportNotFoundError

    assets = await asset_repository.list_for_report(report.id)
    citations = await citation_repository.list_details_for_report(report.id)

    return ExportableReport(
        report=report,
        assets=assets,
        citations=citations,
    )