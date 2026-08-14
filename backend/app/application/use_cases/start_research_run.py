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
    run_research_graph,
)
from app.infrastructure.agents.task_registry import discard as discard_task
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)
from app.infrastructure.db.session import AsyncSessionLocal

ACTIVE_RUN_STATUSES = {
    "planning",
    "researching",
    "verifying",
    "reasoning",
    "fact_checking",
    "awaiting_approval",
    "generating_report",
}


class ResearchRunAlreadyActiveError(Exception):
    """Raised when the user already has an active research run."""

# ============================================================
# CREATE RESEARCH RUN
# ============================================================

async def create_research_run(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    question: str,
) -> ResearchRun:
    repository = ResearchRunRepository(db)
    active_run = await repository.get_active_for_user(
        user_id=user_id,
        statuses=ACTIVE_RUN_STATUSES,
    )

    if active_run is not None:
        raise ResearchRunAlreadyActiveError

    run = ResearchRun(
        workspace_id=workspace_id,
        user_id=user_id,
        question=question,
        status="researching",
    )

    db.add(run)
    await db.commit()
    await db.refresh(run)

    return run


# ============================================================
# BACKGROUND RESEARCH EXECUTION
# ============================================================

async def execute_research_run(
    research_run_id: str,
    question: str,
) -> None:
    async with AsyncSessionLocal() as db:
        run = await db.get(
            ResearchRun,
            uuid.UUID(research_run_id),
        )

        if run is None:
            discard_task(research_run_id)
            return

        try:
            result = await run_research_graph(
                research_run_id,
                question,
            )

            await db.refresh(run)

            if run.status == "cancelled":
                return

            await persist_research_artifacts(
                db=db,
                run=run,
                result=result,
            )

            await db.refresh(run)

            if run.status == "cancelled":
                return

            if result.get("__interrupt__"):
                run.status = "awaiting_approval"
            else:
                await db.refresh(run)

                if run.status == "cancelled":
                    return

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

            await db.commit()

        except ResearchRunCancelledError:
            run.status = "cancelled"
            await db.commit()

        except asyncio.CancelledError:
            if run.status != "cancelled":
                run.status = "cancelled"
                await db.commit()
            raise

        except Exception:
            await db.refresh(run)

            if run.status != "cancelled":
                run.status = "paused"

            await db.commit()
            raise

        finally:
            discard_task(research_run_id)