from app.domain.services.source_reliability import (
    score_source_reliability,
    source_authority_tier,
)


def test_authoritative_complete_source_gets_high_score():
    score = score_source_reliability(
        url="https://research.example.gov/ai-safety",
        title="Production AI Safety Research",
        content="A" * 1200,
    )

    assert score == 1.0


def test_source_with_missing_metadata_gets_lower_score():
    score = score_source_reliability(
        url="http://example.com",
        title=None,
        content="Short content.",
    )

    assert 0.0 < score < 0.5


def test_invalid_source_gets_zero_score():
    score = score_source_reliability(
        url="",
        title=None,
        content=None,
    )

    assert score == 0.0


def test_academic_source_is_classified_as_primary():
    assert (
        source_authority_tier(
            "https://arxiv.org/abs/2501.00001",
        )
        == "primary"
    )


def test_community_platform_cannot_receive_high_score():
    score = score_source_reliability(
        url="https://medium.com/example/research",
        title="A polished article",
        content="A" * 2000,
    )

    assert score < 0.65


def test_reputable_secondary_source_scores_above_threshold():
    score = score_source_reliability(
        url="https://www.reuters.com/technology/example",
        title="Technology report",
        content="A" * 1200,
    )

    assert score >= 0.65