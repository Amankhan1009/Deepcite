from langgraph.types import interrupt

from app.infrastructure.agents.state import GraphState


async def approval_gate(state: GraphState) -> dict:
    """Pause the graph until a human approves report generation."""

    decision = interrupt(
        {
            "type": "human_approval_required",
            "research_run_id": state["research_run_id"],
            "message": (
                "Review the fact-checked research findings before generating "
                "the final report."
            ),
        }
    )

    if decision is not True:
        raise ValueError("Research run approval must be explicitly true")

    return {}