import uuid
from unittest.mock import AsyncMock

from app.infrastructure.agents.nodes.planning_agent import planning_agent
from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import ResearchPlan


async def test_planning_agent_produces_a_plan(monkeypatch):
    mock_plan = ResearchPlan(
        sub_questions=[
            "What are the security risks of persistent agent memory?",
            "What are the privacy risks of persistent agent memory?",
            "How can persistent agent memory be governed safely?",
        ],
        strategy="Compare security, privacy, and governance research.",
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.planning_agent.generate_research_plan",
        AsyncMock(return_value=mock_plan),
    )

    state: GraphState = {
        "research_run_id": str(uuid.uuid4()),
        "question": "What are the risks of AI agents with persistent memory?",
        "plan": None,
        "sources": None,
        "evidence": None,
    }

    result = await planning_agent(state)

    assert result["plan"] is not None
    assert len(result["plan"]["sub_questions"]) == 3
    assert result["plan"]["strategy"]
