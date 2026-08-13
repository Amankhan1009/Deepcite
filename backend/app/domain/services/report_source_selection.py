from urllib.parse import urlparse, urlunparse

REPORT_SOURCE_RELIABILITY_THRESHOLD = 0.70
MINIMUM_REPORT_SOURCE_COUNT = 2
MAXIMUM_REPORT_SOURCE_COUNT = 5
MAXIMUM_REPORT_SOURCES_PER_DOMAIN = 2


def _normalized_source_url(source: dict) -> str:
    parsed_url = urlparse(str(source.get("url") or "").strip())

    if not parsed_url.netloc:
        return str(source.get("url") or "").strip().lower()

    return urlunparse(
        (
            parsed_url.scheme.lower(),
            parsed_url.netloc.lower(),
            parsed_url.path.rstrip("/"),
            "",
            parsed_url.query,
            "",
        )
    )


def _source_domain(source: dict) -> str:
    return (urlparse(str(source.get("url") or "")).hostname or "").lower()


def _deduplicate_sources(sources: list[dict]) -> list[dict]:
    deduplicated_sources = []
    seen_urls: set[str] = set()

    for source in sources:
        normalized_url = _normalized_source_url(source)

        if normalized_url and normalized_url in seen_urls:
            continue

        if normalized_url:
            seen_urls.add(normalized_url)

        deduplicated_sources.append(source)

    return deduplicated_sources


def _select_diverse_sources(
    sources: list[dict],
    *,
    maximum_source_count: int = MAXIMUM_REPORT_SOURCE_COUNT,
) -> list[dict]:
    selected_sources = []
    domain_counts: dict[str, int] = {}

    for source in sources:
        if len(selected_sources) >= maximum_source_count:
            break

        domain = _source_domain(source)
        domain_count = domain_counts.get(domain, 0)

        if domain and domain_count >= MAXIMUM_REPORT_SOURCES_PER_DOMAIN:
            continue

        selected_sources.append(source)

        if domain:
            domain_counts[domain] = domain_count + 1

    if len(selected_sources) >= MINIMUM_REPORT_SOURCE_COUNT:
        return selected_sources

    selected_source_indexes = {
        source.get("source_index")
        for source in selected_sources
    }

    for source in sources:
        if len(selected_sources) >= MINIMUM_REPORT_SOURCE_COUNT:
            break

        if source.get("source_index") in selected_source_indexes:
            continue

        selected_sources.append(source)
        selected_source_indexes.add(source.get("source_index"))

    return selected_sources


def select_report_sources(
    sources: list[dict],
) -> list[dict]:
    """
    Select the strongest verified sources for report generation.

    When fewer than two sources meet the quality threshold, use the two
    highest-scoring sources as a fallback so the report can still be produced.
    """

    ranked_sources = _deduplicate_sources(
        sorted(
            (dict(source) for source in sources),
            key=lambda source: float(
                source.get("reliability_score") or 0.0,
            ),
            reverse=True,
        )
    )

    strong_sources = [
        source
        for source in ranked_sources
        if float(source.get("reliability_score") or 0.0)
        >= REPORT_SOURCE_RELIABILITY_THRESHOLD
    ]

    if len(strong_sources) >= MINIMUM_REPORT_SOURCE_COUNT:
        return _select_diverse_sources(strong_sources)

    return _select_diverse_sources(
        ranked_sources,
        maximum_source_count=MINIMUM_REPORT_SOURCE_COUNT,
    )


def filter_evidence_for_sources(
    evidence: list[dict],
    selected_sources: list[dict],
) -> list[dict]:
    """Keep only evidence belonging to selected report sources."""

    selected_source_indexes = {
        source.get("source_index")
        for source in selected_sources
    }

    return [
        dict(item)
        for item in evidence
        if item.get("source_index") in selected_source_indexes
    ]


def filter_fact_checks_for_evidence(
    fact_checks: list[dict],
    selected_evidence: list[dict],
    all_evidence: list[dict],
) -> list[dict]:
    """
    Keep fact checks that are linked to evidence available to the report.

    Fact-check entries are copied so graph state is never mutated.
    """

    selected_evidence_indexes = {
        index
        for index, evidence_item in enumerate(all_evidence)
        if evidence_item in selected_evidence
    }

    filtered_fact_checks: list[dict] = []

    for fact_check in fact_checks:
        supporting_indexes = (
            fact_check.get("supporting_evidence_indexes") or []
        )
        contradicting_indexes = (
            fact_check.get("contradicting_evidence_indexes") or []
        )

        relevant_indexes = set(
            supporting_indexes + contradicting_indexes,
        )

        if relevant_indexes and not (
            relevant_indexes & selected_evidence_indexes
        ):
            continue

        filtered_fact_check = dict(fact_check)
        filtered_fact_check["supporting_evidence_indexes"] = [
            index
            for index in supporting_indexes
            if index in selected_evidence_indexes
        ]
        filtered_fact_check["contradicting_evidence_indexes"] = [
            index
            for index in contradicting_indexes
            if index in selected_evidence_indexes
        ]

        filtered_fact_checks.append(filtered_fact_check)

    return filtered_fact_checks
