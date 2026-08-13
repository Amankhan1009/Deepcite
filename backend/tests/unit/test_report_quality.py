from app.domain.services.evaluation_scoring import (
    calculate_report_quality,
)


def test_report_quality_rewards_complete_deep_report():
    report = """
# AI Research Report

## Methodology

The report compares the supplied sources and verified claims.

## Findings

The evidence identifies several measurable findings [Source 1].
Additional findings are supported by independent sources [Source 2].

## Analysis and Synthesis

The sources agree on the main trend but differ on implementation trade-offs
[Source 3].

## Limitations and Risks

The available evidence has limitations and possible risks [Source 4].

## Recommendations

The evidence supports a practical recommendation [Source 5].

## Conclusion

The findings support a qualified conclusion [Source 6].
""" + (" evidence" * 1500)

    result = calculate_report_quality(
        report_markdown=report,
        executive_summary="A focused summary supported by evidence.",
    )

    assert result["score"] == 1.0
    assert result["word_count"] >= 1500
    assert result["missing_sections"] == []
    assert result["citation_count"] == 6
    assert result["executive_summary_present"] is True


def test_report_quality_penalizes_short_incomplete_report():
    result = calculate_report_quality(
        report_markdown="""
# Short Report

## Findings

A short finding without enough depth.
""",
        executive_summary=None,
    )

    assert result["score"] < 0.5
    assert result["word_count"] < 1500
    assert "executive_summary" in result["missing_sections"]
    assert "methodology" in result["missing_sections"]
    assert "conclusion" in result["missing_sections"]


def test_report_quality_counts_separate_executive_summary():
    result = calculate_report_quality(
        report_markdown="""
# Report

## Methodology

## FINDINGS

## Analysis and Synthesis

## Limitations and Risks

## Recommendations

## Conclusion
""",
        executive_summary="A separate persisted executive summary.",
    )

    assert result["present_section_count"] == 7
    assert result["missing_sections"] == []
    assert result["executive_summary_present"] is True
