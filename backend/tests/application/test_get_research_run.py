import uuid
from types import SimpleNamespace

import pytest

from app.application.use_cases.get_research_run import (
    ResearchRunStatusNotFoundError,
    get_research_run,
)


class FakeResearchRunRepository:
    def __init__(self, run):
        self.run = run

    async def get_for_user(self, research_run_id, user_id):
        return self.run


@pytest.mark.asyncio
async def test_get_research_run_returns_owned_run():
    run = SimpleNamespace(
        id=uuid.uuid4(),
        deleted_at=None,
    )

    result = await get_research_run(
        repository=FakeResearchRunRepository(run),
        research_run_id=run.id,
        user_id=uuid.uuid4(),
    )

    assert result is run


@pytest.mark.asyncio
async def test_get_research_run_rejects_missing_run():
    repository = FakeResearchRunRepository(None)

    with pytest.raises(ResearchRunStatusNotFoundError):
        await get_research_run(
            repository=repository,
            research_run_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )