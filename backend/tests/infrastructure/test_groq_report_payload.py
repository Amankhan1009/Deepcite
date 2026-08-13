from app.infrastructure.llm.groq_client import (
    REPORT_MAX_EVIDENCE_CLAIM_CHARS,
    REPORT_MAX_EVIDENCE_ITEMS,
    REPORT_MAX_FACT_CHECK_EXPLANATION_CHARS,
    REPORT_MAX_FACT_CHECK_ITEMS,
    REPORT_MAX_QUESTION_CHARS,
    REPORT_MAX_REASONING_ITEM_CHARS,
    REPORT_MAX_REASONING_ITEMS,
    REPORT_MAX_SOURCE_TITLE_CHARS,
    REPORT_MAX_SOURCES,
    build_report_generation_payload,
)


def test_build_report_generation_payload_bounds_report_inputs():
    payload = build_report_generation_payload(
        question="Q" * (REPORT_MAX_QUESTION_CHARS + 25),
        sources=[
            {
                "source_index": index,
                "title": "T" * (REPORT_MAX_SOURCE_TITLE_CHARS + 25),
                "reliability_score": 0.9,
            }
            for index in range(REPORT_MAX_SOURCES + 2)
        ],
        evidence=[
            {
                "source_index": 0,
                "claim_text": "E" * (REPORT_MAX_EVIDENCE_CLAIM_CHARS + 25),
            }
            for _ in range(REPORT_MAX_EVIDENCE_ITEMS + 2)
        ],
        reasoning=[
            {
                "claim_index": index,
                "text": "R" * (REPORT_MAX_REASONING_ITEM_CHARS + 25),
                "supporting_source_indexes": [0],
                "contradicting_source_indexes": [],
            }
            for index in range(REPORT_MAX_REASONING_ITEMS + 2)
        ],
        fact_checks=[
            {
                "claim_index": index,
                "status": "supported",
                "explanation": "F"
                * (REPORT_MAX_FACT_CHECK_EXPLANATION_CHARS + 25),
                "supporting_evidence_indexes": [0],
                "contradicting_evidence_indexes": [],
            }
            for index in range(REPORT_MAX_FACT_CHECK_ITEMS + 2)
        ],
    )

    assert len(payload["question"]) == REPORT_MAX_QUESTION_CHARS
    assert len(payload["sources"]) == REPORT_MAX_SOURCES
    assert len(payload["evidence"]) == REPORT_MAX_EVIDENCE_ITEMS
    assert len(payload["reasoning"]) == REPORT_MAX_REASONING_ITEMS
    assert len(payload["fact_checks"]) == REPORT_MAX_FACT_CHECK_ITEMS

    assert "T" * (REPORT_MAX_SOURCE_TITLE_CHARS + 1) not in payload["sources"][0]
    assert (
        "E" * (REPORT_MAX_EVIDENCE_CLAIM_CHARS + 1)
        not in payload["evidence"][0]
    )
    assert (
        len(payload["reasoning"][0]["text"])
        == REPORT_MAX_REASONING_ITEM_CHARS
    )
    assert (
        len(payload["fact_checks"][0]["explanation"])
        == REPORT_MAX_FACT_CHECK_EXPLANATION_CHARS
    )
    assert payload["truncation"] == {
        "sources_sent": REPORT_MAX_SOURCES,
        "sources_available": REPORT_MAX_SOURCES + 2,
        "evidence_items_sent": REPORT_MAX_EVIDENCE_ITEMS,
        "evidence_items_available": REPORT_MAX_EVIDENCE_ITEMS + 2,
        "reasoning_items_sent": REPORT_MAX_REASONING_ITEMS,
        "reasoning_items_available": REPORT_MAX_REASONING_ITEMS + 2,
        "fact_check_items_sent": REPORT_MAX_FACT_CHECK_ITEMS,
        "fact_check_items_available": REPORT_MAX_FACT_CHECK_ITEMS + 2,
    }
