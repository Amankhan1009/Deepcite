import uuid

from app.infrastructure.agents.nodes.verification_agent import (
    verification_agent,
)
from app.infrastructure.agents.state import GraphState


async def test_verification_agent_scores_all_sources():
    state: GraphState = {
        "research_run_id": str(uuid.uuid4()),
        "question": "What are the risks of production AI systems?",
        "plan": None,
        "sources": [
            {
                "source_index": 0,
                "url": "https://example.gov/ai",
                "title": "AI Safety Report",
                "content": "A" * 1200,
            },
            {
                "source_index": 1,
                "url": "http://example.com",
                "title": None,
                "content": "Short content.",
            },
        ],
        "verified_sources": None,
        "evidence": None,
        "report": None,
    }

    result = await verification_agent(state)

    verified_sources = result["verified_sources"]

    assert len(verified_sources) == 2
    assert verified_sources[0]["source_index"] == 0
    assert verified_sources[0]["reliability_score"] == 1.0
    assert verified_sources[1]["source_index"] == 1
    assert 0.0 < verified_sources[1]["reliability_score"] < 0.5