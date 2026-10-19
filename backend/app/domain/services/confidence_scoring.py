from collections.abc import Iterable


def calculate_claim_confidence(
    *,
    status: str,
    supporting_source_reliabilities: Iterable[float],
    contradicting_source_reliabilities: Iterable[float],
) -> float:
    """Calculate a bounded heuristic confidence score for one claim."""

    normalized_status = str(status or "").strip().lower()

    # Irrelevant claims receive zero confidence and cannot be inflated by supporting sources.
    if normalized_status == "irrelevant":
        return 0.0

    if normalized_status == "supported":
        base_score = 0.80
    elif normalized_status == "partially_supported":
        base_score = 0.60
    elif normalized_status == "uncertain":
        base_score = 0.50
    elif normalized_status == "unsupported":
        base_score = 0.30
    elif normalized_status == "contradicted":
        base_score = 0.20
    else:
        # Fallback for unverified or unrecognized statuses
        base_score = 0.40

    supporting = list(supporting_source_reliabilities)
    contradicting = list(contradicting_source_reliabilities)

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

    values = [score for score in scores if score is not None]

    if not values:
        return None

    return round(sum(values) / len(values), 4)