import re
from collections.abc import Iterable


def clamp_evaluation_score(score: float) -> float:
    """Keep evaluation scores inside the inclusive 0-1 range."""

    return round(
        max(0.0, min(1.0, float(score))),
        4,
    )


def average_source_reliability(
    sources: Iterable[dict],
) -> float | None:
    """Calculate the mean reliability score for verified sources."""

    scores = [
        float(source["reliability_score"])
        for source in sources
        if source.get("reliability_score") is not None
    ]

    if not scores:
        return None

    return clamp_evaluation_score(sum(scores) / len(scores))


def calculate_citation_coverage(
    report_markdown: str,
    reasoning_items: Iterable[dict],
) -> float | None:
    """
    Estimate citation coverage for reasoning claims.

    Each factual report line containing a source marker is counted as cited.
    The result is capped by the number of reasoning claims.
    """

    claims = list(reasoning_items)

    if not claims:
        return None

    factual_lines = []

    for line in report_markdown.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        if stripped.startswith("---"):
            continue

        if stripped.startswith("*All statements"):
            continue

        factual_lines.append(stripped)

    cited_lines = [
        line
        for line in factual_lines
        if re.search(r"\[Source\s+\d+\]", line)
    ]

    covered_claims = min(len(cited_lines), len(claims))

    return clamp_evaluation_score(
        covered_claims / len(claims),
    )


def calculate_overall_research_quality(
    evaluations: Iterable[dict],
) -> float | None:
    """Calculate the mean across available evaluation dimensions."""

    scores = [
        float(item["score"])
        for item in evaluations
        if item.get("dimension") != "overall"
        and item.get("score") is not None
    ]

    if not scores:
        return None

    return clamp_evaluation_score(sum(scores) / len(scores))


def calculate_report_quality(
    report_markdown: str,
    executive_summary: str | None = None,
) -> dict:
    """
    Calculate deterministic report-quality metrics.

    The executive summary is persisted separately from the Markdown body, so
    it is evaluated as its own required section rather than as a Markdown
    heading.
    """

    required_sections = {
        "executive_summary": {
            "executive summary",
        },
        "methodology": {
            "methodology",
            "research methodology",
        },
        "findings": {
            "findings",
            "key findings",
        },
        "analysis": {
            "analysis and synthesis",
            "analysis",
            "synthesis",
            "comparison",
        },
        "limitations": {
            "limitations and risks",
            "limitations",
            "risks",
        },
        "recommendations": {
            "recommendations",
            "recommendation",
        },
        "conclusion": {
            "conclusion",
        },
    }

    normalized_summary = (executive_summary or "").strip()
    heading_names = {
        heading.strip().lower()
        for heading in re.findall(
            r"(?im)^#{1,3}\s+(.+?)\s*$",
            report_markdown,
        )
    }

    full_report_text = "\n\n".join(
        part
        for part in (normalized_summary, report_markdown)
        if part
    )

    words = re.findall(
        r"\b[a-zA-Z0-9][a-zA-Z0-9'-]*\b",
        full_report_text,
    )
    word_count = len(words)

    present_sections = []
    missing_sections = []

    for section_name, aliases in required_sections.items():
        is_present = (
            bool(normalized_summary)
            if section_name == "executive_summary"
            else bool(heading_names.intersection(aliases))
        )

        if is_present:
            present_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    section_score = len(present_sections) / len(required_sections)

    target_word_count = 1500
    word_score = min(word_count / target_word_count, 1.0)

    citation_count = len(
        re.findall(
            r"\[Source\s+\d+\]",
            full_report_text,
            flags=re.IGNORECASE,
        )
    )

    citation_target = 6
    citation_score = min(citation_count / citation_target, 1.0)

    quality_score = clamp_evaluation_score(
        (word_score * 0.45)
        + (section_score * 0.40)
        + (citation_score * 0.15)
    )

    return {
        "score": quality_score,
        "word_count": word_count,
        "target_word_count": target_word_count,
        "citation_count": citation_count,
        "required_section_count": len(required_sections),
        "present_section_count": len(present_sections),
        "present_sections": present_sections,
        "missing_sections": missing_sections,
        "executive_summary_present": bool(normalized_summary),
        "method": (
            "weighted deterministic score: "
            "45% word count, 40% section coverage, "
            "15% citation presence"
        ),
    }
