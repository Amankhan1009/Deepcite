import operator
from typing import Annotated, TypedDict


class ResearchTask(TypedDict):
    """Input delivered to one parallel Research Agent worker."""

    sub_question: str
    sub_question_index: int


class GraphState(TypedDict):
    """Shared state passed between every node in the research graph."""

    research_run_id: str
    question: str
    plan: dict | None
    sources: Annotated[list[dict], operator.add]
    verified_sources: list[dict] | None
    evidence: list[dict] | None
    reasoning: dict | None
    fact_checks: dict | None
    chart_asset: dict | None
    report: dict | None
    evaluations: list[dict] | None
    evaluation_error: bool