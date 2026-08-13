from app.infrastructure.agents.nodes.evaluation_agent import evaluation_agent
from app.infrastructure.agents.state import GraphState


async def test_evaluation_agent_returns_evaluations(monkeypatch):
    async def fake_evaluate_research(
    *,
    question,
    plan,
    sources,
    report,
    evidence,
    reasoning,
    fact_checks,
    ):
        assert question == "What are AI risks?"
        assert plan["sub_questions"] == ["Risk one"]
        assert report["content_markdown"] == "# AI Risks"
        assert evidence == []
        assert reasoning == []
        assert fact_checks == []
        assert len(sources) == 1

        return [
            {
                "dimension": "planning_quality",
                "score": 0.9,
                "details": {"rationale": "The plan is focused."},
            },
            {
                "dimension": "search_quality",
                "score": 0.8,
                "details": {"rationale": "The source is relevant."},
            },
            {
                "dimension": "source_reliability",
                "score": 0.85,
                "details": {"source_count": 1},
            },
        ]

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.evaluation_agent."
        "evaluate_research",
        fake_evaluate_research,
    )

    state: GraphState = {
        "research_run_id": "evaluation-run",
        "question": "What are AI risks?",
        "plan": {
            "sub_questions": ["Risk one"],
            "strategy": "Compare evidence.",
        },
        "sources": [],
        "verified_sources": [
            {
                "source_index": 0,
                "url": "https://example.com",
                "title": "AI risks",
                "content": "Evidence",
                "reliability_score": 0.85,
            }
        ],
        "evidence": [],
        "reasoning": None,
        "fact_checks": None,
        "chart_asset": None,
        "report": {
            "content_markdown": "# AI Risks",
            "executive_summary": "AI risks summary",
        },
        "evaluations": None,
        "evaluation_error": False,
    }

    result = await evaluation_agent(state)

    assert result["evaluation_error"] is False
    assert len(result["evaluations"]) == 3
    assert result["evaluations"][0]["dimension"] == "planning_quality"


async def test_evaluation_agent_does_not_block_on_failure(monkeypatch):
    async def failing_evaluate_research(**kwargs):
        raise RuntimeError("judge unavailable")

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.evaluation_agent."
        "evaluate_research",
        failing_evaluate_research,
    )

    state: GraphState = {
        "research_run_id": "evaluation-failure-run",
        "question": "What are AI risks?",
        "plan": {},
        "sources": [],
        "verified_sources": [],
        "evidence": [],
        "reasoning": None,
        "fact_checks": None,
        "chart_asset": None,
        "report": None,
        "evaluations": None,
        "evaluation_error": False,
    }

    result = await evaluation_agent(state)

    assert result == {
        "evaluations": [],
        "evaluation_error": True,
    }