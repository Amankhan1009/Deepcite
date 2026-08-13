import logging

from app.domain.services.evaluation_scoring import (
    average_source_reliability,
    calculate_citation_coverage,
    calculate_overall_research_quality,
    calculate_report_quality,
)
from app.infrastructure.llm.groq_client import (
    generate_evaluation,
    generate_quality_evaluation,
)

logger = logging.getLogger(__name__)


async def evaluate_research(
    *,
    question: str,
    plan: dict,
    sources: list[dict],
    report: dict,
    evidence: list[dict],
    reasoning: list[dict],
    fact_checks: list[dict],
) -> list[dict]:
    """
    Evaluate a completed run without discarding available scores on failure.

    Deterministic evaluation dimensions remain available when either optional
    LLM-judge call fails.
    """

    evaluations: list[dict] = []

    try:
        llm_evaluation = await generate_evaluation(
            question=question,
            plan=plan,
            sources=sources,
        )
    except Exception:
        logger.exception(
            "Planning and search quality evaluation failed",
        )
    else:
        evaluations.extend(
            [
                {
                    "dimension": "planning_quality",
                    "score": llm_evaluation.planning_quality_score,
                    "details": {
                        "rationale": (
                            llm_evaluation.planning_quality_rationale
                        ),
                    },
                },
                {
                    "dimension": "search_quality",
                    "score": llm_evaluation.search_quality_score,
                    "details": {
                        "rationale": (
                            llm_evaluation.search_quality_rationale
                        ),
                    },
                },
            ]
        )

    reliability_score = average_source_reliability(sources)

    if reliability_score is not None:
        evaluations.append(
            {
                "dimension": "source_reliability",
                "score": reliability_score,
                "details": {
                    "source_count": len(sources),
                    "method": "mean of Verification Agent scores",
                },
            }
        )

    report_markdown = report.get("content_markdown", "")
    executive_summary = report.get("executive_summary")

    citation_coverage = calculate_citation_coverage(
        report_markdown=report_markdown,
        reasoning_items=reasoning,
    )

    if citation_coverage is not None:
        evaluations.append(
            {
                "dimension": "citation_coverage",
                "score": citation_coverage,
                "details": {
                    "claim_count": len(reasoning),
                    "method": (
                        "cited factual report blocks capped by reasoning "
                        "claim count"
                    ),
                },
            }
        )

    report_quality = calculate_report_quality(
        report_markdown=report_markdown,
        executive_summary=executive_summary,
    )

    evaluations.append(
        {
            "dimension": "report_quality",
            "score": report_quality["score"],
            "details": report_quality,
        }
    )

    try:
        quality_evaluation = await generate_quality_evaluation(
            question=question,
            report_markdown=report_markdown,
            evidence=evidence,
            reasoning=reasoning,
            fact_checks=fact_checks,
        )
    except Exception:
        logger.exception(
            "Groundedness and hallucination evaluation failed",
        )
    else:
        evaluations.extend(
            [
                {
                    "dimension": "groundedness",
                    "score": quality_evaluation.groundedness_score,
                    "details": {
                        "rationale": (
                            quality_evaluation.groundedness_rationale
                        ),
                    },
                },
                {
                    "dimension": "hallucination_detection",
                    "score": (
                        quality_evaluation.hallucination_detection_score
                    ),
                    "details": {
                        "rationale": (
                            quality_evaluation
                            .hallucination_detection_rationale
                        ),
                        "unsupported_statements": (
                            quality_evaluation.unsupported_statements
                        ),
                    },
                },
            ]
        )

    overall_score = calculate_overall_research_quality(evaluations)

    if overall_score is not None:
        evaluations.append(
            {
                "dimension": "overall",
                "score": overall_score,
                "details": {
                    "method": "mean of all available evaluation dimensions",
                    "dimensions": [
                        item["dimension"]
                        for item in evaluations
                    ],
                },
            }
        )

    return evaluations