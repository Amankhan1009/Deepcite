from app.core.config import get_settings
from app.infrastructure.observability.tracing import (
    process_llm_inputs,
    traceable_span,
    tracing_enabled,
)


async def test_traced_async_function_preserves_result(monkeypatch):
    settings = get_settings()

    monkeypatch.setattr(settings, "langsmith_tracing", False)
    monkeypatch.setattr(settings, "langsmith_api_key", "")

    @traceable_span(
        name="test.observability_function",
        run_type="chain",
    )
    async def traced_function(value: str) -> dict[str, str]:
        return {"value": value}

    result = await traced_function("ok")

    assert result == {"value": "ok"}
    assert tracing_enabled() is False


def test_process_llm_inputs_removes_client_object():
    class FakeSchema:
        __name__ = "FakeSchema"

    result = process_llm_inputs(
        {
            "client": object(),
            "contents": "Test prompt",
            "response_schema": FakeSchema,
        }
    )

    assert result == {
        "prompt": "Test prompt",
        "response_schema": "FakeSchema",
    }