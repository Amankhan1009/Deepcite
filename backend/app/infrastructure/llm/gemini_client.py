import asyncio
import json
import random

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.core.config import get_settings
from app.infrastructure.observability.tracing import (
    process_llm_inputs,
    traceable_span,
)

settings = get_settings()

GEMINI_MODEL = "gemini-3.5-flash"
MAX_ATTEMPTS = 4
INITIAL_RETRY_DELAY_SECONDS = 1.0
MAX_RETRY_DELAY_SECONDS = 8.0


class ResearchPlan(BaseModel):
    sub_questions: list[str]
    strategy: str


class EvidenceExtraction(BaseModel):
    items: list[str]


class ReasoningExtraction(BaseModel):
    items: list[str]
    supporting_source_indexes: list[int]
    contradicting_source_indexes: list[int]


class ReportGeneration(BaseModel):
    content_markdown: str
    executive_summary: str


def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _is_retryable_error(error: errors.APIError) -> bool:
    """Return True only for transient Gemini API failures."""

    if isinstance(error, errors.ServerError):
        return True

    return isinstance(error, errors.ClientError) and error.code in {
        408,
        429,
    }

@traceable_span(
    name="llm.gemini.structured_generation",
    run_type="llm",
    process_inputs=process_llm_inputs,
)

async def _generate_content_with_retry(
    client: genai.Client,
    contents: str,
    response_schema: type[BaseModel],
) -> types.GenerateContentResponse:
    for attempt in range(MAX_ATTEMPTS):
        try:
            return await client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )

        except errors.APIError as error:
            is_last_attempt = attempt == MAX_ATTEMPTS - 1

            if is_last_attempt or not _is_retryable_error(error):
                raise

            exponential_delay = min(
                INITIAL_RETRY_DELAY_SECONDS * (2**attempt),
                MAX_RETRY_DELAY_SECONDS,
            )
            jitter = random.uniform(0, 0.5)

            await asyncio.sleep(exponential_delay + jitter)

    raise RuntimeError("Gemini retry loop exited unexpectedly")


async def generate_research_plan(question: str) -> ResearchPlan:
    """Generate a structured research plan."""

    client = _get_client()

    response = await _generate_content_with_retry(
        client=client,
        contents=(
            "Break this research question into 3-5 focused sub-questions "
            "and a one-sentence research strategy: "
            f"'{question}'"
        ),
        response_schema=ResearchPlan,
    )

    return ResearchPlan.model_validate_json(response.text)


async def generate_evidence(
    source_title: str | None,
    source_content: str,
) -> EvidenceExtraction:
    """Extract directly supported factual claims from one source."""

    client = _get_client()
    title = source_title or "Untitled source"

    response = await _generate_content_with_retry(
        client=client,
        contents=(
            "Extract only directly supported factual claims from the source "
            "below. Do not infer, speculate, or add outside knowledge. "
            "Return concise claims that can be cited in a research report.\n\n"
            f"Source title: {title}\n\n"
            f"Source content:\n{source_content}"
        ),
        response_schema=EvidenceExtraction,
    )

    return EvidenceExtraction.model_validate_json(response.text)


async def generate_reasoning(
    question: str,
    sources: list[dict],
    evidence: list[dict],
) -> ReasoningExtraction:
    """Synthesize evidence into structured research conclusions."""

    client = _get_client()

    source_lines = [
        {
            "source_index": source.get("source_index", 0),
            "title": source.get("title") or "Untitled source",
            "url": source.get("url", ""),
            "reliability_score": source.get("reliability_score"),
        }
        for source in sources
    ]

    evidence_lines = [
        {
            "source_index": item.get("source_index", 0),
            "claim_text": item["claim_text"],
        }
        for item in evidence
    ]

    prompt = (
        "Synthesize the supplied evidence into concise research conclusions.\n"
        "Use only the supplied evidence. Do not add outside knowledge.\n"
        "Each conclusion must be directly supported by the evidence.\n"
        "Return source indexes that support the conclusions and source indexes "
        "that contradict them.\n"
        "If there are no contradictions, return an empty contradiction list.\n\n"
        f"Research question:\n{question}\n\n"
        "Sources:\n"
        f"{json.dumps(source_lines, ensure_ascii=False, indent=2)}\n\n"
        "Evidence:\n"
        f"{json.dumps(evidence_lines, ensure_ascii=False, indent=2)}"
    )

    response = await _generate_content_with_retry(
        client=client,
        contents=prompt,
        response_schema=ReasoningExtraction,
    )

    return ReasoningExtraction.model_validate_json(response.text)


async def generate_report(
    question: str,
    sources: list[dict],
    evidence: list[dict],
    reasoning: list[dict] | None = None,
) -> ReportGeneration:
    """Generate a structured, evidence-grounded research report."""

    client = _get_client()

    source_lines = []

    for source in sources:
        source_index = source.get("source_index", 0) + 1
        reliability_score = float(
            source.get("reliability_score") or 0.0,
        )

        source_lines.append(
            f"[Source {source_index}] "
            f"{source.get('title') or 'Untitled source'} — "
            f"{source.get('url', '')} — "
            f"reliability score: {reliability_score:.2f}"
        )

    evidence_lines = []

    for item in evidence:
        source_index = item.get("source_index", 0) + 1
        evidence_lines.append(
            f"[Source {source_index}] {item['claim_text']}"
        )

    reasoning_lines = reasoning or []

    prompt = (
        "Write a detailed, evidence-grounded Markdown research report.\n"
        "The report should normally be between 1200 and 1800 words when "
        "the evidence supports that length.\n"
        "Do not add filler or unsupported outside knowledge.\n"
        "Treat source reliability scores as a ranking signal, not proof.\n"
        "Prefer the strongest available sources for important claims.\n"
        "Do not make precise numerical, benchmark, product, or vendor "
        "recommendations unless the supplied evidence directly supports "
        "them.\n"
        "A citation may support only the factual statement immediately "
        "before it; do not use one citation to support a large paragraph "
        "containing multiple unrelated claims.\n"
        "When evidence is weak, conflicting, or incomplete, state that "
        "limitation instead of guessing.\n"
        "Use only the supplied evidence and reasoning conclusions.\n"
        "Every factual statement must include an inline citation such as "
        "[Source 1].\n\n"
        "Return two fields:\n"
        "1. executive_summary: a focused 120-180 word summary without a "
        "heading.\n"
        "2. content_markdown: the complete report body.\n\n"
        "The content_markdown must contain these headings exactly once:\n"
        "# <descriptive report title>\n"
        "## Methodology\n"
        "## Findings\n"
        "## Analysis and Synthesis\n"
        "## Limitations and Risks\n"
        "## Recommendations\n"
        "## Conclusion\n\n"
        "Do not include an Executive Summary heading inside "
        "content_markdown.\n"
        "Do not include a References section or source URLs; references "
        "are assembled by the application.\n\n"
        f"Research question:\n{question}\n\n"
        "Available sources:\n"
        f"{json.dumps(source_lines, ensure_ascii=False, indent=2)}\n\n"
        "Extracted evidence:\n"
        f"{json.dumps(evidence_lines, ensure_ascii=False, indent=2)}\n\n"
        "Reasoning conclusions:\n"
        f"{json.dumps(reasoning_lines, ensure_ascii=False, indent=2)}"
    )

    response = await _generate_content_with_retry(
        client=client,
        contents=prompt,
        response_schema=ReportGeneration,
    )

    return ReportGeneration.model_validate_json(response.text)