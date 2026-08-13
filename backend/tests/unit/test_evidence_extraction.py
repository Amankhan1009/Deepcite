from app.infrastructure.llm.groq_client import EvidenceExtraction


def test_evidence_extraction_validates_structured_output():
    extraction = EvidenceExtraction.model_validate(
        {
            "items": [
                (
                    "Production AI systems require monitoring for model "
                    "quality and operational failures."
                )
            ]
        }
    )

    assert len(extraction.items) == 1
    assert extraction.items[0].startswith("Production AI systems")
