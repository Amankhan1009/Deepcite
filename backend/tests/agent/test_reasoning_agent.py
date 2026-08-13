import uuid
from unittest.mock import AsyncMock

from app.infrastructure.agents.nodes.reasoning_agent import reasoning_agent
from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import ReasoningExtraction


async def test_reasoning_agent_generates_conclusions(monkeypatch):
    mock_reasoning = ReasoningExtraction(
        items=[
            "Production AI systems require continuous monitoring.",
            "Prompt injection is a significant security risk.",
        ],
        supporting_source_indexes=[0, 1],
        contradicting_source_indexes=[],
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.reasoning_agent.generate_reasoning",
        AsyncMock(return_value=mock_reasoning),
    )

    state: GraphState = {
        "research_run_id": str(uuid.uuid4()),
        "question": "What are the main risks of production AI systems?",
        "plan": None,
        "sources": [],
        "verified_sources": [
            {
                "source_index": 0,
                "url": "https://example.com/one",
                "title": "AI monitoring",
                "content": "Monitoring content.",
                "reliability_score": 0.9,
            },
            {
                "source_index": 1,
                "url": "https://example.com/two",
                "title": "AI security",
                "content": "Security content.",
                "reliability_score": 0.8,
            },
        ],
        "evidence": [
            {
                "source_index": 0,
                "claim_text": "Production AI systems require monitoring.",
            },
            {
                "source_index": 1,
                "claim_text": "Prompt injection is a security risk.",
            },
        ],
        "reasoning": None,
        "report": None,
    }

    result = await reasoning_agent(state)

    assert len(result["reasoning"]["items"]) == 2
    assert result["reasoning"]["supporting_source_indexes"] == [0, 1]
    assert result["reasoning"]["contradicting_source_indexes"] == []
