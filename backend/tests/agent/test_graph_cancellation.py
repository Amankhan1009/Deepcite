from unittest.mock import AsyncMock

import pytest

from app.infrastructure.agents.graph import (
    ResearchRunCancelledError,
    _node_with_cancellation_guard,
)


async def test_guarded_node_raises_when_run_is_cancelled(monkeypatch):
    node_mock = AsyncMock(return_value={"ok": True})

    monkeypatch.setattr(
        "app.infrastructure.agents.graph._research_run_is_cancelled",
        AsyncMock(return_value=True),
    )

    guarded = _node_with_cancellation_guard("test_node", node_mock)

    with pytest.raises(ResearchRunCancelledError):
        await guarded({"research_run_id": "test-run-id"})

    node_mock.assert_not_called()


async def test_guarded_node_runs_when_not_cancelled(monkeypatch):
    node_mock = AsyncMock(return_value={"ok": True})

    monkeypatch.setattr(
        "app.infrastructure.agents.graph._research_run_is_cancelled",
        AsyncMock(return_value=False),
    )

    guarded = _node_with_cancellation_guard("test_node", node_mock)
    result = await guarded({"research_run_id": "test-run-id"})

    assert result == {"ok": True}
    node_mock.assert_called_once()
