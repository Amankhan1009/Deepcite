from unittest.mock import AsyncMock

from langgraph.types import Command

from app.infrastructure.agents import graph


async def test_resume_research_graph_uses_existing_checkpoint(monkeypatch):
    invoke_mock = AsyncMock(
        return_value={
            "status": "resumed",
        }
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.graph._invoke_graph",
        invoke_mock,
    )

    result = await graph.resume_research_graph("resume-thread-id")

    assert result == {"status": "resumed"}
    invoke_mock.assert_awaited_once()

    call = invoke_mock.await_args
    assert call.kwargs["graph_input"] is None
    assert call.kwargs["research_run_id"] == "resume-thread-id"


async def test_approval_resume_uses_command(monkeypatch):
    invoke_mock = AsyncMock(
        return_value={
            "status": "approved",
        }
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.graph._invoke_graph",
        invoke_mock,
    )

    result = await graph.approve_research_graph("approval-thread-id")

    assert result == {"status": "approved"}

    call = invoke_mock.await_args
    assert isinstance(call.kwargs["graph_input"], Command)
    assert call.kwargs["graph_input"].resume is True