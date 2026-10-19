import uuid
from unittest.mock import AsyncMock

from app.infrastructure.agents.nodes.evidence_agent import evidence_agent
from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import EvidenceExtraction


async def test_evidence_agent_extracts_claims_from_source(monkeypatch):
    mock_extraction = EvidenceExtraction(
        items=[
            (
                "Production AI systems require monitoring for model quality, "
                "latency, cost, and operational failures."
            ),
            (
                "Production AI systems should validate outputs before presenting "
                "them to users."
            ),
        ]
    )

    mock_generate = AsyncMock(return_value=mock_extraction)
    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.evidence_agent.generate_evidence",
        mock_generate,
    )

    state: GraphState = {
        "research_run_id": str(uuid.uuid4()),
        "question": "What are the main risks of production AI systems?",
        "plan": None,
        "sources": [
            {
                "source_index": 0,
                "url": "https://example.com/ai-risks",
                "title": "Production AI risks",
                "content": "Example source content.",
                "sub_question": "What are operational failure modes?",
            }
        ],
        "evidence": None,
    }

    result = await evidence_agent(state)

    assert result["evidence"]
    assert len(result["evidence"]) == 2
    assert result["evidence"][0]["source_index"] == 0
    assert result["evidence"][0]["claim_text"]

    mock_generate.assert_called_once_with(
        source_title="Production AI risks",
        source_content="Example source content.",
        research_question="What are the main risks of production AI systems?",
        sub_question="What are operational failure modes?",
    )
