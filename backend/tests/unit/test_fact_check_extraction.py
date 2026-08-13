from app.infrastructure.llm.groq_client import (
    FactCheckExtraction,
    FactCheckItem,
)


def test_fact_check_extraction_accepts_supported_claim():
    extraction = FactCheckExtraction(
        items=[
            FactCheckItem(
                claim_index=0,
                status="supported",
                supporting_evidence_indexes=[0],
                contradicting_evidence_indexes=[],
                explanation="The evidence directly supports the claim.",
            )
        ]
    )

    assert len(extraction.items) == 1
    assert extraction.items[0].claim_index == 0
    assert extraction.items[0].status == "supported"
    assert extraction.items[0].supporting_evidence_indexes == [0]
    assert extraction.items[0].contradicting_evidence_indexes == []