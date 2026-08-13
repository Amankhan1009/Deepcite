import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.persist_research_result import (
    persist_evaluation_results,
    persist_report_result,
    persist_research_artifacts,
)
from app.infrastructure.agents.graph import run_research_graph
from app.infrastructure.db.models.research_run import ResearchRun


async def start_research_run(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    question: str,
) -> ResearchRun:
    run = ResearchRun(
        workspace_id=workspace_id,
        user_id=user_id,
        question=question,
        status="researching",
    )

    db.add(run)
    await db.flush()
    await db.refresh(run)
    await db.commit()

    try:
        result = await run_research_graph(str(run.id), question)

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
