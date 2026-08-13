from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import generate_evidence


async def evidence_agent(state: GraphState) -> dict:
    """Extract structured evidence from verified research sources."""

    sources = state.get("verified_sources") or state.get("sources") or []
    extracted_evidence: list[dict] = []

    for source in sources:
        content = source.get("content", "").strip()

        if not content:
            continue

        extraction = await generate_evidence(
            source_title=source.get("title"),
            source_content=content,
        )

        for claim_text in extraction.items:
            cleaned_claim = claim_text.strip()

            if not cleaned_claim:
                continue

            extracted_evidence.append(
                {
                    "source_index": source["source_index"],
                    "claim_text": cleaned_claim,
                }
            )

    return {"evidence": extracted_evidence}
