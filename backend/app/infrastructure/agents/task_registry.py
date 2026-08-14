import asyncio
import logging
from collections.abc import Awaitable

logger = logging.getLogger(__name__)

_research_run_tasks: dict[str, asyncio.Task] = {}


def _task_done(task: asyncio.Task) -> None:
    research_run_id = task.get_name().removeprefix("research-")

    try:
        exception = task.exception()
    except asyncio.CancelledError:
        logger.info("Research task cancelled: %s", research_run_id)
        return

    if exception is not None:
        logger.exception(
            "Research task failed: %s",
            research_run_id,
            exc_info=exception,
        )
    else:
        logger.info("Research task completed: %s", research_run_id)


def register(research_run_id: str, coro: Awaitable) -> asyncio.Task:
    task = asyncio.create_task(
        coro,
        name=f"research-{research_run_id}",
    )
    task.add_done_callback(_task_done)

    _research_run_tasks[research_run_id] = task
    return task


def cancel(research_run_id: str) -> bool:
    task = _research_run_tasks.get(research_run_id)

    if task is None:
        return False

    task.cancel()
    return True


def discard(research_run_id: str) -> None:
    _research_run_tasks.pop(research_run_id, None)