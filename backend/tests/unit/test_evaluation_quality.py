from app.infrastructure.llm.groq_client import (
    QualityEvaluationExtraction,
    build_quality_evaluation_payload,
)


def test_quality_evaluation_scores_are_structured():
    evaluation = QualityEvaluationExtraction(
        groundedness_score=0.9,
        groundedness_rationale="Claims are supported by the evidence.",
        hallucination_detection_score=0.95,
        hallucination_detection_rationale=(
            "No unsupported factual statements were found."
        ),
        unsupported_statements=[],
    )

    assert evaluation.groundedness_score == 0.9
    assert evaluation.hallucination_detection_score == 0.95
    assert evaluation.unsupported_statements == []


def test_quality_evaluation_payload_is_bounded():
    payload = build_quality_evaluation_payload(
        question="q" * 2_000,
        report_markdown="r" * 10_000,
        evidence=[
            {
                "claim_text": "e" * 1_000,
                "source_index": index,
            }
            for index in range(15)
        ],
        reasoning=[
            {
                "claim_text": "r" * 1_000,
                "supporting_source_indexes": [0],
            }
            for _ in range(12)
        ],
        fact_checks=[
            {
                "claim_index": index,
                "status": "supported",
                "explanation": "f" * 1_000,
                "supporting_evidence_indexes": [index],
                "contradicting_evidence_indexes": [],
            }
            for index in range(12)
        ],
    )

    assert len(payload["question"]) <= 1_000
    assert len(payload["report_markdown"]) <= 6_001
    assert len(payload["evidence"]) == 10
    assert len(payload["reasoning"]) == 8
    assert len(payload["fact_checks"]) == 8
    assert all(
        len(item["claim_text"]) <= 351
        for item in payload["evidence"]
    )
    assert all(
        len(item["claim_text"]) <= 351
        for item in payload["reasoning"]
    )
    assert all(
        len(item["explanation"]) <= 351
        for item in payload["fact_checks"]
    )