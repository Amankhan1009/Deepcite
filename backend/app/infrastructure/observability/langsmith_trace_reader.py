from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from langsmith import Client

from app.core.config import get_settings
from app.infrastructure.observability.tracing import tracing_enabled


class ObservabilityUnavailableError(Exception):
    """Raised when LangSmith tracing is not configured."""


class LangSmithTraceReader:
    def __init__(self, client: Client | None = None):
        if not tracing_enabled() and client is None:
            raise ObservabilityUnavailableError(
                "LangSmith tracing is not configured",
            )

        settings = get_settings()

        self.client = client or Client(
            api_key=settings.langsmith_api_key,
            api_url=settings.langsmith_endpoint,
        )
        self.project_name = settings.langsmith_project

    def _contains_research_run_id(
        self,
        value: Any,
        research_run_id: str,
    ) -> bool:
        if isinstance(value, dict):
            return any(
                self._contains_research_run_id(
                    nested_value,
                    research_run_id,
                )
                for nested_value in value.values()
            )

        if isinstance(value, list):
            return any(
                self._contains_research_run_id(
                    nested_value,
                    research_run_id,
                )
                for nested_value in value
            )

        return value == research_run_id

    def _matches_research_run(
        self,
        run: Any,
        research_run_id: uuid.UUID,
    ) -> bool:
        target = str(research_run_id)

        inputs = getattr(run, "inputs", None) or {}
        extra = getattr(run, "extra", None) or {}
        metadata = extra.get("metadata", {})

        return (
            self._contains_research_run_id(inputs, target)
            or self._contains_research_run_id(metadata, target)
        )

    def _metadata(self, run: Any) -> dict[str, Any]:
        extra = getattr(run, "extra", None) or {}
        metadata = extra.get("metadata", {})

        return metadata if isinstance(metadata, dict) else {}

    def _latency_ms(self, run: Any) -> int | None:
        start_time = getattr(run, "start_time", None)
        end_time = getattr(run, "end_time", None)

        if not start_time or not end_time:
            return None

        latency = (end_time - start_time).total_seconds() * 1000
        return round(latency)

    def _token_usage(self, run: Any) -> dict[str, Any]:
        metadata = self._metadata(run)

        prompt_tokens = getattr(run, "prompt_tokens", None) or 0
        completion_tokens = getattr(run, "completion_tokens", None) or 0
        total_tokens = getattr(run, "total_tokens", None) or (
            prompt_tokens + completion_tokens
        )

        total_cost = getattr(run, "total_cost", None)
        if total_cost is None:
            total_cost = Decimal("0")

        retry_count = (
            metadata.get("retry_count")
            or metadata.get("retries")
            or metadata.get("ls_retry_count")
            or 0
        )

        return {
            "run_type": getattr(run, "run_type", "unknown"),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "total_cost": str(total_cost),
            "retry_count": int(retry_count),
        }

    def _normalize_run(self, run: Any) -> dict[str, Any]:
        error = getattr(run, "error", None)
        status = getattr(run, "status", None)

        if not status:
            status = "error" if error else "success"

        return {
            "langsmith_run_id": run.id,
            "agent_name": getattr(run, "name", "unknown"),
            "tool_calls": [],
            "token_usage": self._token_usage(run),
            "latency_ms": self._latency_ms(run),
            "status": status,
            "error": error,
        }

    def _find_root(
        self,
        research_run_id: uuid.UUID,
    ) -> Any | None:
        runs = self.client.list_runs(
            project_name=self.project_name,
            filter='eq(name, "research_graph")',
            is_root=True,
            limit=100,
        )

        for run in runs:
            if self._matches_research_run(run, research_run_id):
                return run

        return None

    def _read_runs(
        self,
        research_run_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        root = self._find_root(research_run_id)

        if root is None:
            return []

        runs = list(
            self.client.list_runs(
                project_name=self.project_name,
                trace_id=root.id,
                limit=100,
            )
        )

        if not any(run.id == root.id for run in runs):
            runs.insert(0, root)

        return [
            self._normalize_run(run)
            for run in runs
        ]

    def read_for_research_run(
        self,
        research_run_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        return self._read_runs(research_run_id)