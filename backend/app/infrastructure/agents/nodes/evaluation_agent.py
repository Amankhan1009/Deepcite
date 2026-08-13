import logging

from app.infrastructure.agents.state import GraphState
from app.infrastructure.evaluation.evaluator import evaluate_research

logger = logging.getLogger(__name__)


async def evaluation_agent(state: GraphState) -> dict:
    """Evaluate the completed research run without blocking report delivery."""

    plan = state.get("plan") or {}
    sources = state.get("verified_sources") or state.get("sources") or []
    report = state.get("report") or {}

    reasoning_data = state.get("reasoning") or {}
    reasoning = reasoning_data.get("items") or []

    fact_checks_data = state.get("fact_checks") or {}
    fact_checks = fact_checks_data.get("items") or []

    try:
        evaluations = await evaluate_research(
            question=state["question"],
            plan=plan,
            sources=sources,
            report=report,
            evidence=state.get("evidence") or [],
            reasoning=reasoning,
            fact_checks=fact_checks,
        )

    except Exception:
        logger.exception(
            "Evaluation failed for research run %s",
            state["research_run_id"],
        )

        return {
            "evaluations": [],
            "evaluation_error": True,
        }

    return {
        "evaluations": evaluations,
        "evaluation_error": False,
    }