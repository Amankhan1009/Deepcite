import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.export_report import (
    ReportExportNotFoundError,
    get_exportable_report,
)
from app.application.use_cases.submit_report_feedback import (
    ReportFeedbackTargetNotFoundError,
    submit_report_feedback,
)
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.citation_repository import (
    CitationRepository,
)
from app.infrastructure.db.repositories.report_asset_repository import (
    ReportAssetRepository,
)
from app.infrastructure.db.repositories.report_feedback_repository import (
    ReportFeedbackRepository,
)
from app.infrastructure.db.repositories.report_repository import ReportRepository
from app.infrastructure.db.session import get_db
from app.infrastructure.export.renderers import render_report_export
from app.presentation.api.v1.deps import get_current_user
from app.presentation.schemas.report_feedback import (
    ReportFeedbackRequest,
    ReportFeedbackResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/{report_id}/feedback",
    response_model=ReportFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_feedback(
    report_id: uuid.UUID,
    payload: ReportFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        feedback = await submit_report_feedback(
            report_repository=ReportRepository(db),
            feedback_repository=ReportFeedbackRepository(db),
            report_id=report_id,
            user_id=current_user.id,
            decision=payload.decision,
            comment=payload.comment,
            rating=payload.rating,
        )
    except ReportFeedbackTargetNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        ) from error

    return ReportFeedbackResponse.model_validate(feedback)


@router.get("/{report_id}/export")
async def export_report(
    report_id: uuid.UUID,
    export_format: Literal["markdown", "pdf", "docx"] = Query(
        default="markdown",
        alias="format",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        exportable = await get_exportable_report(
            report_repository=ReportRepository(db),
            asset_repository=ReportAssetRepository(db),
            citation_repository=CitationRepository(db),
            report_id=report_id,
            user_id=current_user.id,
        )
    except ReportExportNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        ) from error

    content, media_type, extension = render_report_export(
        exportable,
        export_format,
    )

    filename = f"deepcite-report-{report_id}.{extension}"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
        },
    )