from urllib.parse import urlparse

PRIMARY_SOURCE_DOMAINS = (
    "arxiv.org",
    "doi.org",
    "pubmed.ncbi.nlm.nih.gov",
    "nature.com",
    "science.org",
    "acm.org",
    "ieee.org",
    "who.int",
    "oecd.org",
    "worldbank.org",
)

REPUTABLE_SECONDARY_DOMAINS = (
    "apnews.com",
    "bbc.com",
    "ft.com",
    "reuters.com",
)

COMMUNITY_OR_CONTENT_PLATFORM_DOMAINS = (
    "linkedin.com",
    "medium.com",
    "quora.com",
    "reddit.com",
    "x.com",
    "youtube.com",
)

LOW_VALUE_REFERENCE_DOMAINS = (
    "dictionary.cambridge.org",
    "wiktionary.org",
    "merriam-webster.com",
    "dictionary.com",
    "thefreedictionary.com",
)


def _matches_domain(
    hostname: str,
    domains: tuple[str, ...],
) -> bool:
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in domains
    )


def source_authority_tier(url: str) -> str:
    """Classify a source by transparent, domain-based authority signals."""

    hostname = (urlparse(url).hostname or "").lower()

    if not hostname:
        return "unknown"

    if _matches_domain(hostname, LOW_VALUE_REFERENCE_DOMAINS):
        return "low_value_reference"

    if hostname.endswith((".gov", ".edu")):
        return "primary"

    if _matches_domain(hostname, PRIMARY_SOURCE_DOMAINS):
        return "primary"

    if _matches_domain(hostname, REPUTABLE_SECONDARY_DOMAINS):
        return "reputable_secondary"

    if _matches_domain(
        hostname,
        COMMUNITY_OR_CONTENT_PLATFORM_DOMAINS,
    ):
        return "community"

    if hostname.endswith(".org"):
        return "general"

    return "unknown"


def score_source_reliability(
    url: str,
    title: str | None,
    content: str | None,
) -> float:
    """
    Calculate a transparent deterministic source-reliability baseline.

    Authority signals carry more weight than presentation signals such as
    HTTPS, titles, and content length. A polished community post therefore
    cannot score as highly as a primary or academic source.
    """

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or ""
    normalized_content = (content or "").strip()

    if not hostname:
        return 0.0

    authority_tier = source_authority_tier(url)

    if authority_tier == "low_value_reference":
        return 0.10

    score = 0.0

    if parsed_url.scheme == "https":
        score += 0.10

    score += 0.10

    if title and title.strip():
        score += 0.10

    content_length = len(normalized_content)

    if content_length >= 1000:
        score += 0.15
    elif content_length >= 200:
        score += 0.05

    authority_scores = {
        "primary": 0.55,
        "reputable_secondary": 0.40,
        "general": 0.20,
        "community": 0.00,
        "unknown": 0.15,
        "low_value_reference": 0.00,
    }

    score += authority_scores[authority_tier]

    return round(min(score, 1.0), 2)