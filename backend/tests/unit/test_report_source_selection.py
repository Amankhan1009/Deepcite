from app.domain.services.report_source_selection import (
    filter_evidence_for_sources,
    filter_fact_checks_for_evidence,
    select_report_sources,
)


def test_select_report_sources_prefers_strong_sources():
    sources = [
        {
            "source_index": 0,
            "url": "https://docs.example.com/source-a",
            "reliability_score": 0.95,
        },
        {
            "source_index": 1,
            "url": "https://blog.example.com/source-b",
            "reliability_score": 0.45,
        },
        {
            "source_index": 2,
            "url": "https://docs.example.com/source-c",
            "reliability_score": 0.80,
        },
    ]

    selected = select_report_sources(sources)

    assert [source["source_index"] for source in selected] == [0, 2]


def test_select_report_sources_falls_back_to_best_two_sources():
    sources = [
        {
            "source_index": 0,
            "url": "https://docs.example.com/source-a",
            "reliability_score": 0.40,
        },
        {
            "source_index": 1,
            "url": "https://blog.example.com/source-b",
            "reliability_score": 0.60,
        },
        {
            "source_index": 2,
            "url": "https://docs.example.com/source-c",
            "reliability_score": 0.50,
        },
    ]

    selected = select_report_sources(sources)

    assert [source["source_index"] for source in selected] == [1, 2]


def test_select_report_sources_deduplicates_exact_source_urls():
    sources = [
        {
            "source_index": 0,
            "url": "https://docs.example.com/guide",
            "reliability_score": 0.95,
        },
        {
            "source_index": 1,
            "url": "https://docs.example.com/guide/",
            "reliability_score": 0.90,
        },
        {
            "source_index": 2,
            "url": "https://blog.example.com/analysis",
            "reliability_score": 0.80,
        },
    ]

    selected = select_report_sources(sources)

    assert [source["source_index"] for source in selected] == [0, 2]


def test_select_report_sources_limits_one_domain_when_alternatives_exist():
    sources = [
        {
            "source_index": 0,
            "url": "https://docs.example.com/a",
            "reliability_score": 0.95,
        },
        {
            "source_index": 1,
            "url": "https://docs.example.com/b",
            "reliability_score": 0.94,
        },
        {
            "source_index": 2,
            "url": "https://docs.example.com/c",
            "reliability_score": 0.93,
        },
        {
            "source_index": 3,
            "url": "https://research.example.org/a",
            "reliability_score": 0.82,
        },
    ]

    selected = select_report_sources(sources)

    assert [source["source_index"] for source in selected] == [0, 1, 3]


def test_filters_evidence_and_fact_checks_to_selected_sources():
    all_evidence = [
        {
            "source_index": 0,
            "claim_text": "Primary evidence.",
        },
        {
            "source_index": 1,
            "claim_text": "Low-quality evidence.",
        },
        {
            "source_index": 2,
            "claim_text": "Secondary evidence.",
        },
    ]

    selected_sources = [
        {
            "source_index": 0,
            "url": "https://docs.example.com/source-a",
            "reliability_score": 0.95,
        },
        {
            "source_index": 2,
            "url": "https://research.example.org/source-c",
            "reliability_score": 0.80,
        },
    ]

    selected_evidence = filter_evidence_for_sources(
        evidence=all_evidence,
        selected_sources=selected_sources,
    )

    fact_checks = [
        {
            "claim_index": 0,
            "status": "supported",
            "supporting_evidence_indexes": [0],
            "contradicting_evidence_indexes": [],
        },
        {
            "claim_index": 1,
            "status": "supported",
            "supporting_evidence_indexes": [1],
            "contradicting_evidence_indexes": [],
        },
        {
            "claim_index": 2,
            "status": "uncertain",
            "supporting_evidence_indexes": [2],
            "contradicting_evidence_indexes": [1],
        },
    ]

    selected_fact_checks = filter_fact_checks_for_evidence(
        fact_checks=fact_checks,
        selected_evidence=selected_evidence,
        all_evidence=all_evidence,
    )

    assert [
        item["claim_index"]
        for item in selected_fact_checks
    ] == [0, 2]

    assert selected_fact_checks[1][
        "contradicting_evidence_indexes"
    ] == []
