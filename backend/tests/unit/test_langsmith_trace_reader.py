import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.infrastructure.observability.langsmith_trace_reader import (
    LangSmithTraceReader,
)


class FakeLangSmithClient:
    def __init__(self, root_run, child_run):
        self.root_run = root_run
        self.child_run = child_run

    def list_runs(self, **kwargs):
        if kwargs.get("is_root"):
            return iter([self.root_run])

        return iter([self.root_run, self.child_run])


class FakeRunsResource:
    def __init__(self, root_run, child_run):
        self.root_run = root_run
        self.child_run = child_run
        self.last_query_kwargs = None

    def query_v2(self, **kwargs):
        self.last_query_kwargs = kwargs
        if kwargs.get("is_root"):
            return iter([self.root_run])
        return iter([self.root_run, self.child_run])


class FakeLangSmithV2Client:
    def __init__(self, root_run, child_run):
        self.project_id = uuid.uuid4()
        self.runs = FakeRunsResource(root_run, child_run)

    def read_project(self, project_name):
        return SimpleNamespace(id=self.project_id)


def test_reader_normalizes_trace_runs():
    research_run_id = uuid.uuid4()
    root_id = uuid.uuid4()
    child_id = uuid.uuid4()

    start_time = datetime(
        2026,
        8,
        9,
        10,
        0,
        tzinfo=UTC,
    )
    end_time = datetime(
        2026,
        8,
        9,
        10,
        0,
        1,
        500000,
        tzinfo=UTC,
    )

    root_run = SimpleNamespace(
        id=root_id,
        name="research_graph",
        run_type="chain",
        inputs={"research_run_id": str(research_run_id)},
        extra={"metadata": {}},
        start_time=start_time,
        end_time=end_time,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        total_cost="0.0123",
        status="success",
        error=None,
    )

    child_run = SimpleNamespace(
        id=child_id,
        name="agent.planning_agent",
        run_type="chain",
        inputs={},
        extra={
            "metadata": {
                "retry_count": 2,
            }
        },
        start_time=start_time,
        end_time=end_time,
        prompt_tokens=20,
        completion_tokens=10,
        total_tokens=30,
        total_cost="0.0010",
        status="success",
        error=None,
    )

    reader = LangSmithTraceReader(
        client=FakeLangSmithClient(root_run, child_run),
    )

    rows = reader.read_for_research_run(research_run_id)

    assert len(rows) == 2
    assert rows[0]["langsmith_run_id"] == root_id
    assert rows[0]["agent_name"] == "research_graph"
    assert rows[0]["token_usage"]["total_tokens"] == 150
    assert rows[0]["latency_ms"] == 1500

    assert rows[1]["langsmith_run_id"] == child_id
    assert rows[1]["token_usage"]["retry_count"] == 2


def test_reader_returns_no_rows_for_unknown_research_run():
    research_run_id = uuid.uuid4()
    other_run_id = uuid.uuid4()

    root_run = SimpleNamespace(
        id=uuid.uuid4(),
        name="research_graph",
        run_type="chain",
        inputs={"research_run_id": str(other_run_id)},
        extra={"metadata": {}},
        start_time=None,
        end_time=None,
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
        total_cost=None,
        status="success",
        error=None,
    )

    reader = LangSmithTraceReader(
        client=FakeLangSmithClient(root_run, root_run),
    )

    rows = reader.read_for_research_run(research_run_id)

    assert rows == []


def test_reader_uses_smithdb_query_v2_when_available():
    research_run_id = uuid.uuid4()
    root_id = uuid.uuid4()
    child_id = uuid.uuid4()

    root_run = SimpleNamespace(
        id=root_id,
        name="research_graph",
        run_type="chain",
        inputs={"research_run_id": str(research_run_id)},
        extra={"metadata": {}},
        start_time=None,
        end_time=None,
        prompt_tokens=50,
        completion_tokens=25,
        total_tokens=75,
        total_cost=None,
        status="success",
        error=None,
    )
    child_run = SimpleNamespace(
        id=child_id,
        name="agent.planning_agent",
        run_type="chain",
        inputs={},
        extra={"metadata": {}},
        start_time=None,
        end_time=None,
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        total_cost=None,
        status="success",
        error=None,
    )

    client = FakeLangSmithV2Client(root_run, child_run)
    reader = LangSmithTraceReader(client=client)

    rows = reader.read_for_research_run(research_run_id)

    assert len(rows) == 2
    assert rows[0]["langsmith_run_id"] == root_id
    assert rows[0]["agent_name"] == "research_graph"
    assert rows[1]["langsmith_run_id"] == child_id
    # Assert query_v2 parameters were populated correctly
    assert client.runs.last_query_kwargs is not None
    assert "project_ids" in client.runs.last_query_kwargs
    assert client.runs.last_query_kwargs["project_ids"] == [str(client.project_id)]
    assert "selects" in client.runs.last_query_kwargs
    assert client.runs.last_query_kwargs["trace_id"] == str(root_id)
