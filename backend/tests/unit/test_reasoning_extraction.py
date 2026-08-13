from app.infrastructure.llm.groq_client import (
    ReasoningExtraction,
    _normalize_source_indexes,
)


def test_reasoning_extraction_accepts_flat_structured_output():
    extraction = ReasoningExtraction(
        items=["Continuous monitoring is required."],
        supporting_source_indexes=[0],
        contradicting_source_indexes=[],
    )

    assert extraction.items == ["Continuous monitoring is required."]
    assert extraction.supporting_source_indexes == [0]
    assert extraction.contradicting_source_indexes == []


def test_normalize_source_indexes_handles_concatenated_groq_indexes():
    assert _normalize_source_indexes(["0123456789"], set(range(8))) == list(
        range(8)
    )
