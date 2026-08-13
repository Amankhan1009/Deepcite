import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.infrastructure.db.models.agent_trace import AgentTrace
from app.presentation.api.v1.observability import _build_trace_response


def test_trace_response_aggregates_tokens_cost_latency_retries_and_errors():
    research_run_id = uuid.uuid4()

    first_trace = AgentTrace(
        id=uuid.uuid4(),
        research_run_id=research_run_id,
        agent_name="research_graph",
        langsmith_run_id=uuid.uuid4(),
        tool_calls=[],
        token_usage={
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "total_cost": "0.0123",
            "retry_count": 1,
        },
        latency_ms=1000,
        status="success",
        error=None,
        created_at=datetime.now(UTC),
    )

    second_trace = AgentTrace(
        id=uuid.uuid4(),
        research_run_id=research_run_id,
        agent_name="agent.planning_agent",
        langsmith_run_id=uuid.uuid4(),
        tool_calls=[],
        token_usage={
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30,
            "total_cost": "0.0010",
            "retry_count": 2,
        },
        latency_ms=500,
        status="error",
        error="provider timeout",
        created_at=datetime.now(UTC),
    )

    response = _build_trace_response(
        research_run_id,
        [first_trace, second_trace],
    )

    assert response.research_run_id == research_run_id
    assert response.trace_count == 2
    assert response.total_tokens == 180
    assert response.total_cost == Decimal("0.0133")
    assert response.total_latency_ms == 1500
    assert response.total_retries == 3
    assert response.total_errors == 1