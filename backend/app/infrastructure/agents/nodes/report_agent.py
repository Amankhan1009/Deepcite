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

REPORT_MAX_SOURCES = 6
REPORT_MAX_EVIDENCE_ITEMS = 16
REPORT_MAX_FACT_CHECK_ITEMS = 10


async def report_agent(state: GraphState) -> dict:
    """Generate a cited report from the strongest available evidence."""

    verified_sources = (
        state.get("verified_sources") or state.get("sources") or []
    )
    all_evidence = state.get("evidence") or []

    raw_report_sources = select_report_sources(verified_sources)[
        :REPORT_MAX_SOURCES
    ]
    raw_report_evidence = filter_evidence_for_sources(
        evidence=all_evidence,
        selected_sources=raw_report_sources,
    )[:REPORT_MAX_EVIDENCE_ITEMS]

    # Map raw source indexes to contiguous 0-based sequential indexes (0..N-1)
    # so that the report generation prompt and citations always start at [Source 1]
    # with no missing numbers or offsets.
    raw_to_seq_source_index: dict[int, int] = {}
    url_to_seq_source_index: dict[str, int] = {}

    report_sources = []
    for seq_index, source in enumerate(raw_report_sources):
        copied = dict(source)
        raw_idx = source.get("source_index")
        if raw_idx is not None:
            raw_to_seq_source_index[raw_idx] = seq_index

        url = str(source.get("url") or "").strip().lower()
        if url:
            url_to_seq_source_index[url] = seq_index

        copied["source_index"] = seq_index
        report_sources.append(copied)

    report_evidence = []
    for item in raw_report_evidence:
        copied = dict(item)
        raw_idx = item.get("source_index")
        item_url = str(item.get("source_url") or "").strip().lower()

        seq_idx = raw_to_seq_source_index.get(raw_idx)
        if seq_idx is None and item_url:
            seq_idx = url_to_seq_source_index.get(item_url)
        if seq_idx is None:
            seq_idx = 0

        copied["source_index"] = seq_idx
        report_evidence.append(copied)

    reasoning_data = state.get("reasoning") or {}
    reasoning_items = reasoning_data.get("items") or []

    raw_supporting = reasoning_data.get("supporting_source_indexes", [])
    raw_contradicting = reasoning_data.get("contradicting_source_indexes", [])

    mapped_supporting = [
        raw_to_seq_source_index[idx]
        for idx in raw_supporting
        if idx in raw_to_seq_source_index
    ]
    mapped_contradicting = [
        raw_to_seq_source_index[idx]
        for idx in raw_contradicting
        if idx in raw_to_seq_source_index
    ]

    reasoning = [
        {
            "claim_index": index,
            "text": item,
            "supporting_source_indexes": mapped_supporting,
            "contradicting_source_indexes": mapped_contradicting,
        }
        for index, item in enumerate(reasoning_items)
    ]

    fact_checks_data = state.get("fact_checks") or {}
    all_fact_checks = fact_checks_data.get("items") or []

    report_fact_checks = filter_fact_checks_for_evidence(
        fact_checks=all_fact_checks,
        selected_evidence=raw_report_evidence,
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
