from app.domain.services.confidence_scoring import (
    calculate_claim_confidence,
    calculate_overall_confidence,
)


def test_supported_claim_has_high_confidence():
    score = calculate_claim_confidence(
        status="supported",
        supporting_source_reliabilities=[0.9],
        contradicting_source_reliabilities=[],
    )

    assert score == 0.85


def test_contradicting_evidence_reduces_confidence():
    score = calculate_claim_confidence(
        status="supported",
        supporting_source_reliabilities=[0.9],
        contradicting_source_reliabilities=[0.9],
    )

    assert score == 0.67


def test_confidence_score_is_bounded():
    score = calculate_claim_confidence(
        status="contradicted",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[1.0, 1.0, 1.0],
    )

    assert 0.0 <= score <= 1.0


def test_overall_confidence_is_mean():
    score = calculate_overall_confidence([0.8, 0.6, 1.0])

    assert score == 0.8


def test_overall_confidence_is_none_without_scores():
    assert calculate_overall_confidence([]) is None