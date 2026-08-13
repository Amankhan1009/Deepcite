from pathlib import Path

from app.domain.services.report_source_selection import (
    filter_evidence_for_sources,
    filter_fact_checks_for_evidence,
    select_report_sources,
)
from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import (
    generate_report,
    identify_chartable_data,
)
from app.infrastructure.visualization.chart_generator import render_chart

REPORT_MAX_SOURCES = 3
REPORT_MAX_EVIDENCE_ITEMS = 8
REPORT_MAX_FACT_CHECK_ITEMS = 6


async def report_agent(state: GraphState) -> dict:
    """Generate a cited report from the strongest available evidence."""

    verified_sources = (
        state.get("verified_sources") or state.get("sources") or []
    )
    all_evidence = state.get("evidence") or []

    report_sources = select_report_sources(verified_sources)[
        :REPORT_MAX_SOURCES
    ]
    report_evidence = filter_evidence_for_sources(
        evidence=all_evidence,
        selected_sources=report_sources,
    )[:REPORT_MAX_EVIDENCE_ITEMS]

    reasoning_data = state.get("reasoning") or {}
    reasoning_items = reasoning_data.get("items") or []

    reasoning = [
        {
            "claim_index": index,
            "text": item,
            "supporting_source_indexes": reasoning_data.get(
                "supporting_source_indexes",
                [],
            ),
            "contradicting_source_indexes": reasoning_data.get(
                "contradicting_source_indexes",
                [],
            ),
        }
        for index, item in enumerate(reasoning_items)
    ]

    fact_checks_data = state.get("fact_checks") or {}
    all_fact_checks = fact_checks_data.get("items") or []

    report_fact_checks = filter_fact_checks_for_evidence(
        fact_checks=all_fact_checks,
        selected_evidence=report_evidence,
        all_evidence=all_evidence,
    )[:REPORT_MAX_FACT_CHECK_ITEMS]

    report = await generate_report(
        question=state["question"],
        sources=report_sources,
        evidence=report_evidence,
        reasoning=reasoning,
        fact_checks=report_fact_checks,
    )

    chart_input = [
        {
            "claim_index": item["claim_index"],
            "claim_text": item["text"],
            "supporting_source_indexes": item[
                "supporting_source_indexes"
            ],
            "contradicting_source_indexes": item[
                "contradicting_source_indexes"
            ],
        }
        for item in reasoning
    ]

    chart_input.extend(
        {
            "claim_index": item.get("claim_index"),
            "status": item.get("status"),
            "explanation": item.get("explanation"),
            "supporting_evidence_indexes": item.get(
                "supporting_evidence_indexes",
                [],
            ),
            "contradicting_evidence_indexes": item.get(
                "contradicting_evidence_indexes",
                [],
            ),
        }
        for item in report_fact_checks
    )

    chart_spec = await identify_chartable_data(chart_input)

    if chart_spec is None:
        return {
            "report": report.model_dump(),
            "chart_asset": None,
        }

    output_path = (
        Path("generated_assets")
        / f"{state['research_run_id']}.png"
    )

    rendered_path = render_chart(
        spec=chart_spec,
        output_path=output_path,
    )

    chart_asset = {
        "asset_type": "chart",
        "file_path": str(rendered_path),
        "caption": chart_spec.title,
    }

    return {
        "report": report.model_dump(),
        "chart_asset": chart_asset,
    }
