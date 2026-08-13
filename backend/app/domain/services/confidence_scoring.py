from collections.abc import Iterable


def calculate_claim_confidence(
    *,
    status: str,
    supporting_source_reliabilities: Iterable[float],
    contradicting_source_reliabilities: Iterable[float],
) -> float:
    """Calculate a bounded confidence score for one claim."""

    supporting = list(supporting_source_reliabilities)
    contradicting = list(contradicting_source_reliabilities)

    if status == "supported":
        base_score = 0.80
    elif status == "contradicted":
        base_score = 0.20
    elif status == "uncertain":
        base_score = 0.50
    else:
        base_score = 0.40

    if supporting:
        support_quality = sum(supporting) / len(supporting)
        base_score = (base_score + support_quality) / 2

    contradiction_penalty = min(
        0.40,
        sum(contradicting) * 0.20,
    )

    return round(
        max(0.0, min(1.0, base_score - contradiction_penalty)),
        4,
    )


def calculate_overall_confidence(
    scores: Iterable[float],
) -> float | None:
    """Calculate the mean confidence score for a report."""

    values = list(scores)

    if not values:
        return None

    return round(sum(values) / len(values), 4)