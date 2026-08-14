import asyncio
from collections.abc import Awaitable

_research_run_tasks: dict[str, asyncio.Task] = {}


def register(research_run_id: str, coro: Awaitable) -> asyncio.Task:
    task = asyncio.create_task(coro, name=f"research-{research_run_id}")
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
