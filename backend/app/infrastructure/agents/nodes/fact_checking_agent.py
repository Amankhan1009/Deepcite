from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import generate_fact_checks


async def fact_checking_agent(state: GraphState) -> dict:
    """Cross-check reasoning conclusions against extracted evidence."""

    reasoning_data = state.get("reasoning") or {}
    reasoning_items = reasoning_data.get("items") or []
    evidence = state.get("evidence") or []

    if not reasoning_items:
        return {"fact_checks": {"items": []}}

    reasoning = [
        {
            "claim_index": index,
            "claim_text": claim,
        }
        for index, claim in enumerate(reasoning_items)
    ]

    extraction = await generate_fact_checks(
        question=state["question"],
        reasoning=reasoning,
        evidence=evidence,
    )

    return {"fact_checks": extraction.model_dump()}