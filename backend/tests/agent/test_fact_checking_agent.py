import uuid
from unittest.mock import AsyncMock

from app.infrastructure.agents.nodes.fact_checking_agent import (
    fact_checking_agent,
)
from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import (
    FactCheckExtraction,
    FactCheckItem,
)


async def test_fact_checking_agent_classifies_claims(monkeypatch):
    mock_extraction = FactCheckExtraction(
        items=[
            FactCheckItem(
                claim_index=0,
                status="supported",
                supporting_evidence_indexes=[0],
                contradicting_evidence_indexes=[],
                explanation="The evidence directly supports the conclusion.",
            ),
            FactCheckItem(
                claim_index=1,
                status="contradicted",
                supporting_evidence_indexes=[],
                contradicting_evidence_indexes=[1],
                explanation="The evidence contradicts the conclusion.",
            ),
        ]
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.fact_checking_agent."
        "generate_fact_checks",
        AsyncMock(return_value=mock_extraction),
    )

    state: GraphState = {
        "research_run_id": str(uuid.uuid4()),
        "question": "What are the main risks of production AI systems?",
        "plan": None,
        "sources": [],
        "verified_sources": [],
        "evidence": [
            {
                "source_index": 0,
                "claim_text": "Production systems require monitoring.",
            },
            {
                "source_index": 1,
                "claim_text": "Prompt injection is a security risk.",
            },
        ],
        "reasoning": {
            "items": [
                "Production systems require monitoring.",
                "Prompt injection is not a security risk.",
            ],
            "supporting_source_indexes": [0],
            "contradicting_source_indexes": [1],
        },
        "fact_checks": None,
        "report": None,
    }

    result = await fact_checking_agent(state)

    assert len(result["fact_checks"]["items"]) == 2
    assert result["fact_checks"]["items"][0]["status"] == "supported"
    assert result["fact_checks"]["items"][1]["status"] == "contradicted"