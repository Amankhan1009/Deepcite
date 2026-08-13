from app.domain.services.source_reliability import (
    score_source_reliability,
    source_authority_tier,
)
from app.infrastructure.agents.state import GraphState


async def verification_agent(state: GraphState) -> dict:
    """Score and classify every collected source deterministically."""

    sources = state.get("sources") or []
    verified_sources: list[dict] = []

    for source in sources:
        verified_source = dict(source)
        verified_source["reliability_score"] = score_source_reliability(
            url=source.get("url", ""),
            title=source.get("title"),
            content=source.get("content"),
        )
        verified_source["authority_tier"] = source_authority_tier(
            source.get("url", ""),
        )
        verified_sources.append(verified_source)

    return {"verified_sources": verified_sources}