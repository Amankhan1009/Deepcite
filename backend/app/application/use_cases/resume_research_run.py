import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.persist_research_result import (
    persist_evaluation_results,
    persist_report_result,
    persist_research_artifacts,
)
from app.infrastructure.agents.graph import (
    ResearchRunCancelledError,
    resume_research_graph,
)
from app.infrastructure.agents.task_registry import discard as discard_task
from app.infrastructure.agents.task_registry import register as register_task
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

    graph_task = register_task(str(run.id), resume_research_graph(str(run.id)))

    try:
        result = await graph_task

        await db.refresh(run)

        if run.status == "cancelled":
            await db.commit()
            await db.close()
            return run

        await persist_research_artifacts(
            db=db,
            run=run,
            result=result,
        )

        await db.refresh(run)

        if run.status == "cancelled":
            await db.commit()
            await db.close()
            return run

        if result.get("__interrupt__"):
            run.status = "awaiting_approval"
        else:
            await db.refresh(run)

            if run.status == "cancelled":
                await db.commit()
                await db.close()
                return run

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

    except ResearchRunCancelledError:
        run.status = "cancelled"
        await db.commit()
        await db.close()
        return run

    except asyncio.CancelledError:
        if run.status != "cancelled":
            run.status = "cancelled"
            await db.commit()
        await db.close()
        raise

    except Exception:
        await db.refresh(run)

        if run.status != "cancelled":
            run.status = "paused"

        await db.commit()
        await db.close()
        raise

    finally:
        discard_task(str(run.id))

    await db.commit()
    await db.close()

    return run
