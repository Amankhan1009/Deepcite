from unittest.mock import AsyncMock

from app.infrastructure.agents.nodes.research_agent import research_agent
from app.infrastructure.agents.state import ResearchTask
from app.infrastructure.mcp.tavily_client import SearchResult


async def test_research_agent_searches_one_subquestion(monkeypatch):
    fake_search = AsyncMock(
        return_value=[
            SearchResult(
                url="https://example.com/security",
                title="AI Security Research",
                content="AI systems require strong security controls.",
            ),
            SearchResult(
                url="https://example.com/governance",
                title="AI Governance Research",
                content="AI systems require monitoring and governance.",
            ),
        ]
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.research_agent.get_search_client",
        lambda: fake_search,
    )

    state: ResearchTask = {
        "sub_question": "What are the security risks of production AI systems?",
        "sub_question_index": 1,
    }

    result = await research_agent(state)

    fake_search.assert_awaited_once_with(
        "What are the security risks of production AI systems?",
        2,
    )

    assert len(result["sources"]) == 2
    assert result["sources"][0]["source_index"] == 2
    assert result["sources"][1]["source_index"] == 3
    assert result["sources"][0]["sub_question_index"] == 1