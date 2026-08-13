import uuid
from unittest.mock import AsyncMock

from app.infrastructure.agents.nodes.report_agent import report_agent
from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import (
    ChartSpec,
    ReportGeneration,
)


async def test_report_agent_generates_report_without_chart(monkeypatch):
    mock_report = ReportGeneration(
        content_markdown=(
            "# Production AI Risks\n\n"
            "Production AI systems require monitoring [Source 1]."
        ),
        executive_summary=(
            "Production AI systems require monitoring [Source 1]."
        ),
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.report_agent.generate_report",
        AsyncMock(return_value=mock_report),
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.report_agent."
        "identify_chartable_data",
        AsyncMock(return_value=None),
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
            }
        ],
        "verified_sources": None,
        "evidence": [
            {
                "source_index": 0,
                "claim_text": (
                    "Production AI systems require monitoring."
                ),
            }
        ],
        "reasoning": {
            "items": [
                "Production AI systems require monitoring."
            ],
            "supporting_source_indexes": [0],
            "contradicting_source_indexes": [],
        },
        "fact_checks": {
            "items": [
                {
                    "claim_index": 0,
                    "status": "supported",
                    "explanation": "The evidence supports the claim.",
                    "supporting_evidence_indexes": [0],
                    "contradicting_evidence_indexes": [],
                }
            ]
        },
        "chart_asset": None,
        "report": None,
    }

    result = await report_agent(state)

    assert result["report"]["content_markdown"].startswith("#")
    assert "[Source 1]" in result["report"]["content_markdown"]
    assert result["report"]["executive_summary"]
    assert result["chart_asset"] is None

async def test_report_agent_generates_chart_asset(monkeypatch, tmp_path):
    mock_report = ReportGeneration(
        content_markdown=(
            "# Incident Comparison\n\n"
            "Security incidents affected 80% of systems [Source 1]."
        ),
        executive_summary=(
            "Security incidents affected 80% of systems [Source 1]."
        ),
    )

    chart_spec = ChartSpec(
        chart_type="bar",
        title="Security vs Reliability Incidents",
        labels=["Security incidents", "Reliability incidents"],
        values=[80.0, 45.0],
        source_claim_ids=[0],
    )

    rendered_path = tmp_path / "chart.png"

    def fake_render_chart(spec, output_path):
        assert spec == chart_spec
        rendered_path.write_bytes(b"\x89PNG\r\n\x1a\n")
        return rendered_path

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.report_agent.generate_report",
        AsyncMock(return_value=mock_report),
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.report_agent."
        "identify_chartable_data",
        AsyncMock(return_value=chart_spec),
    )

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.report_agent.render_chart",
        fake_render_chart,
    )

    state: GraphState = {
        "research_run_id": str(uuid.uuid4()),
        "question": "Compare security and reliability incidents.",
        "plan": None,
        "sources": [
            {
                "source_index": 0,
                "url": "https://example.com/incidents",
                "title": "Incident statistics",
                "content": "Security incidents affected 80% of systems.",
            }
        ],
        "verified_sources": None,
        "evidence": [
            {
                "source_index": 0,
                "claim_text": (
                    "Security incidents affected 80% of systems."
                ),
            }
        ],
        "reasoning": {
            "items": [
                "Security incidents affected 80% of systems."
            ],
            "supporting_source_indexes": [0],
            "contradicting_source_indexes": [],
        },
        "fact_checks": {
            "items": [
                {
                    "claim_index": 0,
                    "status": "supported",
                    "explanation": "The evidence supports the claim.",
                    "supporting_evidence_indexes": [0],
                    "contradicting_evidence_indexes": [],
                }
            ]
        },
        "chart_asset": None,
        "report": None,
    }

    result = await report_agent(state)

    assert result["chart_asset"] is not None
    assert result["chart_asset"]["asset_type"] == "chart"
    assert result["chart_asset"]["caption"] == chart_spec.title
    assert result["chart_asset"]["file_path"] == str(rendered_path)
    assert rendered_path.exists()
    assert rendered_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"