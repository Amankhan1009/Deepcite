import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.approve_research_run import (
    ResearchRunNotAwaitingApprovalError,
    ResearchRunNotFoundError,
    approve_research_run,
)
from app.application.use_cases.get_research_report import (
    ReportNotFoundError,
    get_research_report,
)
from app.application.use_cases.get_research_run import (
    ResearchRunStatusNotFoundError,
    get_research_run,
)
from app.application.use_cases.resume_research_run import (
    ResearchRunNotResumableError,
    ResumableResearchRunNotFoundError,
    resume_research_run,
)
from app.application.use_cases.start_research_run import start_research_run
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.citation_repository import (
    CitationRepository,
)
from app.infrastructure.db.repositories.report_repository import ReportRepository
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)
from app.infrastructure.db.session import get_db
from app.presentation.api.v1.deps import get_current_user
from app.presentation.schemas.research import (
    ReportResponse,
    ResearchRunResponse,
    StartResearchRequest,
)

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/start", response_model=ResearchRunResponse, status_code=201)
async def start(
    payload: StartResearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run = await start_research_run(
        db,
        payload.workspace_id,
        current_user.id,
        payload.question,
    )

    return ResearchRunResponse.model_validate(run)


@router.post(
    "/{research_run_id}/approve",
    response_model=ResearchRunResponse,
)
async def approve(
    research_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        run = await approve_research_run(
            db=db,
            research_run_id=research_run_id,
            user_id=current_user.id,
        )
    except ResearchRunNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research run not found",
        ) from error
    except ResearchRunNotAwaitingApprovalError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Research run is not awaiting approval",
        ) from error

    return ResearchRunResponse.model_validate(run)


@router.post(
    "/{research_run_id}/resume",
    response_model=ResearchRunResponse,
)
async def resume(
    research_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        run = await resume_research_run(
            db=db,
            research_run_id=research_run_id,
            user_id=current_user.id,
        )
    except ResumableResearchRunNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research run not found",
        ) from error
    except ResearchRunNotResumableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Research run is not resumable",
        ) from error

    return ResearchRunResponse.model_validate(run)


@router.get(
    "/{research_run_id}",
    response_model=ResearchRunResponse,
)
async def get_status(
    research_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repository = ResearchRunRepository(db)

    try:
        run = await get_research_run(
            repository=repository,
            research_run_id=research_run_id,
            user_id=current_user.id,
        )
    except ResearchRunStatusNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research run not found",
        ) from error

    return ResearchRunResponse.model_validate(run)


@router.get(
    "/{research_run_id}/report",
    response_model=ReportResponse,
)
async def get_report(
    research_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repository = ReportRepository(db)

    try:
        report = await get_research_report(
            repository,
            research_run_id,
            current_user.id,
        )
    except ReportNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        ) from error

    citation_repository = CitationRepository(db)
    citations = await citation_repository.list_details_for_report(report.id)

    response = ReportResponse.model_validate(report)

    return response.model_copy(update={"citations": citations})