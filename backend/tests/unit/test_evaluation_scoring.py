from app.domain.services.evaluation_scoring import (
    average_source_reliability,
    calculate_citation_coverage,
    calculate_overall_research_quality,
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