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


def test_partially_supported_retains_intermediate_confidence():
    score = calculate_claim_confidence(
        status="partially_supported",
        supporting_source_reliabilities=[0.9],
        contradicting_source_reliabilities=[],
    )

    # (0.60 base + 0.90 reliability) / 2 = 0.75
    assert score == 0.75


def test_partially_supported_without_sources():
    score = calculate_claim_confidence(
        status="partially_supported",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[],
    )

    assert score == 0.6


def test_unsupported_claim_has_low_confidence():
    score = calculate_claim_confidence(
        status="unsupported",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[],
    )

    assert score == 0.3


def test_irrelevant_claim_is_zero_even_with_high_reliability_sources():
    score = calculate_claim_confidence(
        status="irrelevant",
        supporting_source_reliabilities=[1.0, 0.95],
        contradicting_source_reliabilities=[],
    )

    assert score == 0.0


def test_uncertain_claim_preserves_legacy_base_score():
    score = calculate_claim_confidence(
        status="uncertain",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[],
    )

    assert score == 0.5


def test_status_normalization_handles_case_and_whitespace():
    score_upper = calculate_claim_confidence(
        status="  PARTIALLY_SUPPORTED  ",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[],
    )
    assert score_upper == 0.6

    score_mixed = calculate_claim_confidence(
        status="Contradicted",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[],
    )
    assert score_mixed == 0.2


def test_unknown_and_empty_status_uses_fallback():
    score_unknown = calculate_claim_confidence(
        status="unrecognized_custom_status",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[],
    )
    assert score_unknown == 0.4

    score_empty = calculate_claim_confidence(
        status="",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[],
    )
    assert score_empty == 0.4


def test_contradiction_penalty_is_capped_at_forty_percent():
    # Base 0.80, support 0.80 -> 0.80. Three 1.0 contradictions -> penalty capped at 0.40 -> 0.40.
    score = calculate_claim_confidence(
        status="supported",
        supporting_source_reliabilities=[0.8],
        contradicting_source_reliabilities=[1.0, 1.0, 1.0],
    )

    assert score == 0.4


def test_floor_bounding_at_zero():
    # Base 0.20 - penalty 0.40 = -0.20 -> clamped to 0.0
    score = calculate_claim_confidence(
        status="contradicted",
        supporting_source_reliabilities=[],
        contradicting_source_reliabilities=[1.0, 1.0],
    )

    assert score == 0.0