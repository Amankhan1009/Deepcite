from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import generate_reasoning


async def reasoning_agent(state: GraphState) -> dict:
    """Synthesize verified evidence into structured conclusions."""

    sources = state.get("verified_sources") or state.get("sources") or []

    reasoning = await generate_reasoning(
        question=state["question"],
        sources=sources,
        evidence=state.get("evidence") or [],
    )

    return {"reasoning": reasoning.model_dump()}
