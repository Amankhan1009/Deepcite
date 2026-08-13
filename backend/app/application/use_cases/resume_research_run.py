import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.persist_research_result import (
    persist_evaluation_results,
    persist_report_result,
    persist_research_artifacts,
)
from app.infrastructure.agents.graph import resume_research_graph
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)


class ResumableResearchRunNotFoundError(Exception):
    """Raised when a resumable run is missing or owned by another user."""


class ResearchRunNotResumableError(Exception):
    """Raised when the run is not paused or failed."""


async def resume_research_run(
    db: AsyncSession,
    research_run_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ResearchRun:
    """Resume a paused or failed run from its latest LangGraph checkpoint."""

    repository = ResearchRunRepository(db)

    run = await repository.get_for_user(
        research_run_id=research_run_id,
        user_id=user_id,
    )

    if run is None:
        raise ResumableResearchRunNotFoundError

    if run.status not in {"paused", "failed"}:
        raise ResearchRunNotResumableError

    try:
        result = await resume_research_graph(str(run.id))

        await persist_research_artifacts(
            db=db,
            run=run,
            result=result,
        )

        if result.get("__interrupt__"):
            run.status = "awaiting_approval"
        else:
            await persist_report_result(
                db=db,
                run=run,
                result=result,
            )
            await persist_evaluation_results(
                db=db,
                run=run,
                result=result,
            )
            run.status = "completed"

    except Exception:
        run.status = "paused"
        await db.commit()
        await db.close()
        raise

    await db.commit()
    await db.close()

    return run
