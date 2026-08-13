from collections.abc import Callable
from typing import Any

from langsmith import Client, traceable

from app.core.config import get_settings

settings = get_settings()


def tracing_enabled() -> bool:
    """Return whether LangSmith tracing is fully configured and enabled."""

    return bool(
        settings.langsmith_tracing
        and settings.langsmith_api_key
    )


def _get_client() -> Client | None:
    if not tracing_enabled():
        return None

    return Client(
        api_key=settings.langsmith_api_key,
        api_url=settings.langsmith_endpoint,
    )


def traceable_span(
    *,
    name: str,
    run_type: str = "chain",
    process_inputs: Callable[[dict[str, Any]], dict[str, Any]]
    | None = None,
    process_outputs: Callable[[Any], Any] | None = None,
) -> Callable:
    """Create a LangSmith decorator with safe application defaults."""

    return traceable(
        name=name,
        run_type=run_type,
        project_name=settings.langsmith_project,
        client=_get_client(),
        enabled=tracing_enabled(),
        process_inputs=process_inputs,
        process_outputs=process_outputs,
    )


def process_llm_inputs(
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Exclude SDK clients while preserving useful LLM trace inputs."""

    response_schema = inputs.get("response_schema")

    return {
        "prompt": inputs.get("contents", ""),
        "response_schema": getattr(
            response_schema,
            "__name__",
            str(response_schema),
        ),
    }