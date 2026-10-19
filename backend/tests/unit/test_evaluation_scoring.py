from app.domain.services.evaluation_scoring import (
    average_source_reliability,
    calculate_citation_coverage,
    calculate_claim_support,
    calculate_overall_research_quality,
    calculate_report_quality,
    clamp_evaluation_score,
)


def test_clamp_score_lower_bound():
    assert clamp_evaluation_score(-0.5) == 0.0


def test_clamp_score_upper_bound():
    assert clamp_evaluation_score(1.5) == 1.0


def test_average_source_reliability():
    score = average_source_reliability(
        [
            {"reliability_score": 0.8},
            {"reliability_score": 0.9},
        ]
    )

    assert score == 0.85


def test_average_source_reliability_returns_none_without_scores():
    assert average_source_reliability([{"reliability_score": None}]) is None


def test_citation_coverage_counts_cited_report_blocks():
    score = calculate_citation_coverage(
        report_markdown=(
            "# Report\n\n"
            "Supported finding [Source 1].\n\n"
            "Another supported finding [Source 2]."
        ),
        reasoning_items=[
            {"claim_text": "Finding one"},
            {"claim_text": "Finding two"},
        ],
    )

    assert score == 1.0


def test_citation_coverage_returns_zero_when_no_blocks_are_cited():
    score = calculate_citation_coverage(
        report_markdown=(
            "# Report\n\n"
            "Unsupported finding without a citation."
        ),
        reasoning_items=[
            {"claim_text": "Finding one"},
        ],
    )

    assert score == 0.0


def test_citation_coverage_returns_none_without_claims():
    assert (
        calculate_citation_coverage(
            report_markdown="# Empty",
            reasoning_items=[],
        )
        is None
    )


def test_overall_quality_ignores_existing_overall_dimension():
    score = calculate_overall_research_quality(
        [
            {"dimension": "planning_quality", "score": 0.9},
            {"dimension": "groundedness", "score": 0.8},
            {"dimension": "overall", "score": 0.1},
        ]
    )

    assert score == 0.85


def test_calculate_report_quality_identifies_completeness():
    markdown = """# Research Findings
## Methodology
We collected empirical papers.

## Key Findings
Finding 1 [Source 1].
Finding 2 [Source 2].

## Analysis
Comparative synthesis here.

## Limitations
Some boundaries exist.

## Recommendations
Future direction here.
"""
    result = calculate_report_quality(
        report_markdown=markdown,
        executive_summary="Summary of findings.",
    )
    assert result["metric_name"] == "report_completeness"
    assert result["executive_summary_present"] is True
    assert result["present_section_count"] == 6
    assert result["score"] > 0.0


def test_calculate_claim_support_weighted_breakdown():
    fact_checks = [
        {"status": "supported"},
        {"status": "partially_supported"},
        {"status": "unsupported"},
        {"status": "contradicted"},
    ]
    result = calculate_claim_support(fact_checks)
    assert result["score"] == 0.375
    assert result["total_claims"] == 4
    assert result["supported_count"] == 1
    assert result["partially_supported_count"] == 1
    assert result["unsupported_count"] == 1
    assert result["contradicted_count"] == 1


def test_calculate_claim_support_empty_returns_none():
    result = calculate_claim_support([])
    assert result["score"] is None
    assert result["total_claims"] == 0