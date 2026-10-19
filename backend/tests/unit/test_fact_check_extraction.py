import pytest
from pydantic import ValidationError

from app.infrastructure.llm.groq_client import (
    FactCheckExtraction,
    FactCheckItem,
    _FactCheckExtractionWire,
    _FactCheckItemWire,
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


def test_fact_check_extraction_accepts_partially_supported_claim():
    extraction = FactCheckExtraction(
        items=[
            FactCheckItem(
                claim_index=1,
                status="partially_supported",
                supporting_evidence_indexes=[0, 1],
                contradicting_evidence_indexes=[],
                explanation="Evidence supports the claim only for specific cohorts.",
            )
        ]
    )

    assert extraction.items[0].status == "partially_supported"
    assert extraction.items[0].supporting_evidence_indexes == [0, 1]


def test_fact_check_extraction_accepts_unsupported_and_irrelevant_claims():
    extraction = FactCheckExtraction(
        items=[
            FactCheckItem(
                claim_index=2,
                status="unsupported",
                supporting_evidence_indexes=[],
                contradicting_evidence_indexes=[],
                explanation="The evidence mentions the topic but provides no data.",
            ),
            FactCheckItem(
                claim_index=3,
                status="irrelevant",
                supporting_evidence_indexes=[],
                contradicting_evidence_indexes=[],
                explanation="The snippet does not meaningfully relate to the question.",
            ),
        ]
    )

    assert extraction.items[0].status == "unsupported"
    assert extraction.items[1].status == "irrelevant"


def test_fact_check_extraction_accepts_uncertain_and_contradicted():
    extraction = FactCheckExtraction(
        items=[
            FactCheckItem(
                claim_index=0,
                status="uncertain",
                supporting_evidence_indexes=[],
                contradicting_evidence_indexes=[],
                explanation="Evidence findings are ambiguous.",
            ),
            FactCheckItem(
                claim_index=1,
                status="contradicted",
                supporting_evidence_indexes=[],
                contradicting_evidence_indexes=[2],
                explanation="Evidence directly refutes the claim.",
            ),
        ]
    )

    assert extraction.items[0].status == "uncertain"
    assert extraction.items[1].status == "contradicted"


def test_fact_check_extraction_rejects_invalid_status():
    with pytest.raises(ValidationError):
        FactCheckItem(
            claim_index=0,
            status="invalid_status_label",
            supporting_evidence_indexes=[],
            contradicting_evidence_indexes=[],
            explanation="Invalid status.",
        )


def test_wire_model_deserialization():
    wire = _FactCheckExtractionWire(
        items=[
            _FactCheckItemWire(
                claim_index="0",
                status="partially_supported",
                supporting_evidence_indexes=["1"],
                contradicting_evidence_indexes=[],
                explanation="Wire test",
            )
        ]
    )

    assert wire.items[0].status == "partially_supported"
    assert wire.items[0].claim_index == "0"
    