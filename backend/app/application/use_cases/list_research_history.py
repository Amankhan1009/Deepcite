import uuid

from app.infrastructure.db.repositories.research_run_repository import (
    ResearchRunRepository,
)


async def list_research_history(
    repository: ResearchRunRepository,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> list[dict]:
    rows = await repository.list_for_workspace(
        user_id=user_id,
        workspace_id=workspace_id,
    )

    return [
        {
            "id": research_run.id,
            "workspace_id": research_run.workspace_id,
            "question": research_run.question,
            "status": research_run.status,
            "created_at": research_run.created_at,
            "completed_at": research_run.completed_at,
            "report_id": report_id,
        }
        for research_run, report_id in rows
    ]