import asyncio
import json
import logging
import random
import re
from copy import deepcopy
from typing import Literal

from groq import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    InternalServerError,
    RateLimitError,
)
from groq.types.chat import ChatCompletion
from pydantic import BaseModel

from app.core.config import get_settings
from app.infrastructure.llm.gemini_client import (
    EvidenceExtraction,
    ReasoningExtraction,
    ReportGeneration,
    ResearchPlan,
)
from app.infrastructure.observability.tracing import (
    process_llm_inputs,
    traceable_span,
)

settings = get_settings()
logger = logging.getLogger(__name__)

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_STRUCTURED_OUTPUT_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
}
GROQ_TEMPERATURE = 0.0
MAX_ATTEMPTS = 4
INITIAL_RETRY_DELAY_SECONDS = 1.0
MAX_RETRY_DELAY_SECONDS = 8.0
QUALITY_EVALUATION_MAX_QUESTION_CHARS = 1_000
QUALITY_EVALUATION_MAX_REPORT_CHARS = 6_000
QUALITY_EVALUATION_MAX_EVIDENCE_ITEMS = 10
QUALITY_EVALUATION_MAX_EVIDENCE_CLAIM_CHARS = 350
QUALITY_EVALUATION_MAX_REASONING_ITEMS = 8
QUALITY_EVALUATION_MAX_REASONING_ITEM_CHARS = 350
QUALITY_EVALUATION_MAX_FACT_CHECK_ITEMS = 8
QUALITY_EVALUATION_MAX_FACT_CHECK_EXPLANATION_CHARS = 350
REPORT_MAX_COMPLETION_TOKENS = 3200
REPORT_MAX_QUESTION_CHARS = 1_000
REPORT_MAX_SOURCES = 3
REPORT_MAX_SOURCE_TITLE_CHARS = 180
REPORT_MAX_EVIDENCE_ITEMS = 8
REPORT_MAX_EVIDENCE_CLAIM_CHARS = 450
REPORT_MAX_REASONING_ITEMS = 8
REPORT_MAX_REASONING_ITEM_CHARS = 450
REPORT_MAX_FACT_CHECK_ITEMS = 6
REPORT_MAX_FACT_CHECK_EXPLANATION_CHARS = 350
EVIDENCE_MAX_COMPLETION_TOKENS = 1_200
EVIDENCE_MAX_SOURCE_CHARS = 2_000
EVIDENCE_MAX_ITEMS = 5
EVIDENCE_MAX_CLAIM_CHARS = 220
GROQ_CONCURRENCY = 1
_groq_semaphore = asyncio.Semaphore(GROQ_CONCURRENCY)


class _ReasoningExtractionWire(BaseModel):
    """Tolerant wire model for Groq's citation-index generation."""

    items: list[str]
    supporting_source_indexes: list[str]
    contradicting_source_indexes: list[str]


class FactCheckItem(BaseModel):
    """Fact-check result for one reasoning conclusion."""

    claim_index: int
    status: Literal["supported", "contradicted", "uncertain"]
    supporting_evidence_indexes: list[int]
    contradicting_evidence_indexes: list[int]
    explanation: str


class FactCheckExtraction(BaseModel):
    """Structured fact-check results for all reasoning conclusions."""

    items: list[FactCheckItem]


class _FactCheckItemWire(BaseModel):
    """Tolerant wire representation used for Groq output."""

    claim_index: str
    status: Literal["supported", "contradicted", "uncertain"]
    supporting_evidence_indexes: list[str]
    contradicting_evidence_indexes: list[str]
    explanation: str


class _FactCheckExtractionWire(BaseModel):
    """Groq wire response for fact checking."""

    items: list[_FactCheckItemWire]


class ChartSpec(BaseModel):
    """Validated specification for one evidence-based chart."""

    chart_type: Literal["bar", "line", "table"]
    title: str
    labels: list[str]
    values: list[float]
    source_claim_ids: list[int]


class ChartDecision(BaseModel):
    """Groq decision about whether a report contains chartable data."""

    chartable: bool
    spec: ChartSpec | None


class EvaluationExtraction(BaseModel):
    """Structured evaluation scores from the evaluation judge."""

    planning_quality_score: float
    planning_quality_rationale: str
    search_quality_score: float
    search_quality_rationale: str


class QualityEvaluationExtraction(BaseModel):
    """Structured groundedness and hallucination evaluation."""

    groundedness_score: float
    groundedness_rationale: str
    hallucination_detection_score: float
    hallucination_detection_rationale: str
    unsupported_statements: list[str]

def _get_client() -> AsyncGroq:
    return AsyncGroq(api_key=settings.groq_api_key)


def _strict_json_schema(response_schema: type[BaseModel]) -> dict:
    """Build the strict JSON Schema required by Groq structured output."""

    schema = deepcopy(response_schema.model_json_schema())

    def mark_objects_strict(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object":
                value["additionalProperties"] = False

            for nested_value in value.values():
                mark_objects_strict(nested_value)

        elif isinstance(value, list):
            for nested_value in value:
                mark_objects_strict(nested_value)

    mark_objects_strict(schema)
    return schema


def _supports_structured_output(model_name: str) -> bool:
    return model_name in GROQ_STRUCTURED_OUTPUT_MODELS


def _response_format(response_schema: type[BaseModel]) -> dict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": response_schema.__name__.lower(),
            "strict": True,
            "schema": _strict_json_schema(response_schema),
        },
    }


def _is_retryable_error(error: APIError) -> bool:
    """Return True only for transient Groq API failures."""

    if isinstance(
        error,
        APIConnectionError
        | APITimeoutError
        | InternalServerError
        | RateLimitError,
    ):
        return True

    return isinstance(error, APIStatusError) and error.status_code in {
        408,
        429,
        500,
        502,
        503,
        504,
    }


def _get_retry_delay(error: APIError, attempt: int) -> float:
    """Calculate a retry delay, respecting Groq's requested wait time."""
    error_text = str(error)

    match = re.search(
        r"try again in ([0-9]+(?:\.[0-9]+)?)s",
        error_text,
        re.IGNORECASE,
    )

    if match:
        return float(match.group(1)) + random.uniform(0.25, 0.75)

    exponential_delay = min(
        INITIAL_RETRY_DELAY_SECONDS * (2**attempt),
        MAX_RETRY_DELAY_SECONDS,
    )

    return exponential_delay + random.uniform(0.25, 0.75)


@traceable_span(
    name="llm.groq.structured_generation",
    run_type="llm",
    process_inputs=process_llm_inputs,
)
@traceable_span(
    name="llm.groq.structured_generation",
    run_type="llm",
    process_inputs=process_llm_inputs,
)
async def _generate_content_with_retry(
    client: AsyncGroq,
    contents: str,
    response_schema: type[BaseModel],
    *,
    max_completion_tokens: int | None = None,
) -> ChatCompletion:
    async with _groq_semaphore:
        for attempt in range(MAX_ATTEMPTS):
            try:
                request_kwargs = {
                    "model": GROQ_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": contents,
                        }
                    ],
                    "temperature": GROQ_TEMPERATURE,
                }

                if _supports_structured_output(GROQ_MODEL):
                    request_kwargs["response_format"] = _response_format(
                        response_schema,
                    )

                if max_completion_tokens is not None:
                    request_kwargs["max_completion_tokens"] = max_completion_tokens

                return await client.chat.completions.create(**request_kwargs)

            except APIError as error:
                is_last_attempt = attempt == MAX_ATTEMPTS - 1

                if is_last_attempt or not _is_retryable_error(error):
                    raise

                delay = _get_retry_delay(error, attempt)

                logger.warning(
                    "Groq request failed with %s. "
                    "Retrying in %.2fs (attempt %d/%d).",
                    type(error).__name__,
                    delay,
                    attempt + 1,
                    MAX_ATTEMPTS,
                )

                await asyncio.sleep(delay)

    raise RuntimeError("Groq retry loop exited unexpectedly")

def _response_text(response: ChatCompletion) -> str:
    content = response.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty response")

    return content


def _normalize_source_indexes(
    values: list[str],
    valid_indexes: set[int],
) -> list[int]:
    """Normalize Groq's string citation indexes into valid integer indexes."""

    normalized: list[int] = []

    for value in values:
        digits = re.findall(r"\d+", value)

        for token in digits:
            candidate = int(token)

            if candidate in valid_indexes:
                candidates = [candidate]
            elif value.isdigit() and len(value) > 1:
                candidates = [int(character) for character in value]
            else:
                candidates = []

            for index in candidates:
                if index in valid_indexes and index not in normalized:
                    normalized.append(index)

    return normalized


def _repair_chart_values(
    spec: ChartSpec,
    reasoning_output: list[dict],
) -> ChartSpec:
    """Repair concatenated numeric values emitted by the LLM when safe."""

    if len(spec.labels) == len(spec.values):
        return spec

    claim_text = " ".join(
        str(item.get("claim_text", ""))
        for item in reasoning_output
    )

    extracted_values = [
        float(value)
        for value in re.findall(
            r"(?<![\w.])\d+(?:\.\d+)?",
            claim_text,
        )
    ]

    if len(extracted_values) != len(spec.labels):
        return spec

    return spec.model_copy(
        update={
            "values": extracted_values,
        }
    )


async def generate_research_plan(question: str) -> ResearchPlan:
    """Generate a structured research plan."""

    client = _get_client()

    response = await _generate_content_with_retry(
        client=client,
        contents=(
            "Create exactly 3 sub-questions and a one-sentence strategy for "
            "this research question. Keep the output concise and directly "
            f"actionable: '{question}'"
        ),
        response_schema=ResearchPlan,
        max_completion_tokens=800,
    )

    return ResearchPlan.model_validate_json(_response_text(response))


def _truncate_source_for_evidence(source_content: str) -> str:
    """Bound evidence input size to avoid oversized Groq JSON-generation requests."""
    trimmed = source_content.strip()

    if len(trimmed) <= EVIDENCE_MAX_SOURCE_CHARS:
        return trimmed

    truncated = trimmed[:EVIDENCE_MAX_SOURCE_CHARS].rsplit(" ", 1)[0]
    return f"{truncated} ..."


async def generate_evidence(
    source_title: str | None,
    source_content: str,
) -> EvidenceExtraction:
    """Extract directly supported factual claims from one source."""

    client = _get_client()
    title = source_title or "Untitled source"
    bounded_source_content = _truncate_source_for_evidence(source_content)

    response = await _generate_content_with_retry(
        client=client,
        contents=(
            "Extract up to "
            f"{EVIDENCE_MAX_ITEMS} directly supported factual claims from the source "
            "below. Do not infer, speculate, or add outside knowledge. "
            "Return concise, citation-ready claims. Each claim must be short "
            f"({EVIDENCE_MAX_CLAIM_CHARS} characters or fewer). "
            "Do not repeat claims.\n\n"
            f"Source title: {title}\n\n"
            f"Source content:\n{bounded_source_content}"
        ),
        response_schema=EvidenceExtraction,
        max_completion_tokens=EVIDENCE_MAX_COMPLETION_TOKENS,
    )

    return EvidenceExtraction.model_validate_json(_response_text(response))


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
        "that contradict them. Represent each index as a string containing one "
        "integer, such as [\"0\", \"2\"]. Never concatenate multiple indexes "
        "into one string.\n"
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
        response_schema=_ReasoningExtractionWire,
    )

    wire_result = _ReasoningExtractionWire.model_validate_json(
        _response_text(response)
    )

    valid_indexes = {
        source.get("source_index", 0)
        for source in sources
        if isinstance(source.get("source_index", 0), int)
    }

    return ReasoningExtraction(
        items=wire_result.items,
        supporting_source_indexes=_normalize_source_indexes(
            wire_result.supporting_source_indexes,
            valid_indexes,
        ),
        contradicting_source_indexes=_normalize_source_indexes(
            wire_result.contradicting_source_indexes,
            valid_indexes,
        ),
    )


async def generate_fact_checks(
    question: str,
    reasoning: list[dict],
    evidence: list[dict],
) -> FactCheckExtraction:
    """Cross-check reasoning conclusions against extracted evidence."""

    client = _get_client()

    reasoning_lines = [
        {
            "claim_index": index,
            "claim_text": item.get("claim_text")
            or item.get("text")
            or "",
        }
        for index, item in enumerate(reasoning)
    ]

    evidence_lines = [
        {
            "evidence_index": index,
            "source_index": item.get("source_index", 0),
            "claim_text": item.get("claim_text", ""),
        }
        for index, item in enumerate(evidence)
    ]

    prompt = (
        "Fact-check each reasoning conclusion against the supplied evidence.\n"
        "Use only the supplied evidence. Do not add outside knowledge.\n"
        "Return exactly one fact-check result for each reasoning conclusion.\n"
        "Use status supported when the evidence supports the conclusion.\n"
        "Use status contradicted when the evidence conflicts with it.\n"
        "Use status uncertain when the evidence is insufficient.\n"
        "Represent claim_index and evidence indexes as strings containing "
        "one integer, such as [\"0\", \"2\"].\n"
        "Never concatenate multiple indexes into one string.\n"
        "The evidence indexes refer to the evidence_index field, not the "
        "source_index field.\n\n"
        f"Research question:\n{question}\n\n"
        "Reasoning conclusions:\n"
        f"{json.dumps(reasoning_lines, ensure_ascii=False, indent=2)}\n\n"
        "Evidence:\n"
        f"{json.dumps(evidence_lines, ensure_ascii=False, indent=2)}"
    )

    response = await _generate_content_with_retry(
        client=client,
        contents=prompt,
        response_schema=_FactCheckExtractionWire,
    )

    wire_result = _FactCheckExtractionWire.model_validate_json(
        _response_text(response)
    )

    valid_claim_indexes = set(range(len(reasoning)))
    valid_evidence_indexes = set(range(len(evidence)))
    fact_check_items: list[FactCheckItem] = []

    for position, item in enumerate(wire_result.items):
        claim_indexes = _normalize_source_indexes(
            [item.claim_index],
            valid_claim_indexes,
        )

        claim_index = claim_indexes[0] if claim_indexes else position

        if claim_index not in valid_claim_indexes:
            continue

        fact_check_items.append(
            FactCheckItem(
                claim_index=claim_index,
                status=item.status,
                supporting_evidence_indexes=_normalize_source_indexes(
                    item.supporting_evidence_indexes,
                    valid_evidence_indexes,
                ),
                contradicting_evidence_indexes=_normalize_source_indexes(
                    item.contradicting_evidence_indexes,
                    valid_evidence_indexes,
                ),
                explanation=item.explanation,
            )
        )

    return FactCheckExtraction(items=fact_check_items)


async def identify_chartable_data(
    reasoning_output: list[dict],
) -> ChartSpec | None:
    """Identify genuinely chartable quantitative findings."""

    client = _get_client()

    prompt = (
        "Inspect the supplied reasoning and fact-checking output.\n"
        "Decide whether it contains genuinely chartable quantitative data.\n"
        "Chartable data includes numeric comparisons, trends over time, "
        "ranked lists with measurable values, or other meaningful statistics.\n"
        "Do not create a chart for qualitative claims without numeric data.\n"
        "Do not create decorative or speculative charts.\n"
        "If no meaningful chart exists, return chartable=false and spec=null.\n"
        "If chartable, return exactly one small chart specification.\n"
        "Use chart_type bar for category comparisons, line for time trends, "
        "and table for compact numeric summaries.\n"
        "The labels and values arrays must have exactly the same length.\n"
        "Return one numeric value for every label.\n"
        "Never concatenate multiple numeric values into one value.\n"
        "source_claim_ids must contain the indexes of the claims supporting "
        "the chart.\n\n"
        "Reasoning and fact-checking output:\n"
        f"{json.dumps(reasoning_output, ensure_ascii=False, indent=2)}"
    )

    try:
        response = await _generate_content_with_retry(
            client=client,
            contents=prompt,
            response_schema=ChartDecision,
        )

        decision = ChartDecision.model_validate_json(
            _response_text(response)
        )

    except (APIError, ValueError) as exc:
        logger.warning(
            "Chart identification failed; continuing without chart: %s",
            exc,
        )
        return None

    if not decision.chartable:
        return None

    if decision.spec is None:
        return None

    repaired_spec = _repair_chart_values(
        spec=decision.spec,
        reasoning_output=reasoning_output,
    )

    if len(repaired_spec.labels) != len(repaired_spec.values):
        return None

    if not repaired_spec.labels:
        return None

    return repaired_spec


async def generate_evaluation(
    *,
    question: str,
    plan: dict,
    sources: list[dict],
) -> EvaluationExtraction:
    """Evaluate plan quality and search quality with a separate judge prompt."""

    client = _get_client()

    source_lines = [
        {
            "title": source.get("title") or "Untitled source",
            "url": source.get("url", ""),
            "content": source.get("content", "")[:2000],
            "reliability_score": source.get("reliability_score"),
        }
        for source in sources
    ]

    prompt = (
        "You are an independent research-quality evaluator.\n"
        "Do not generate research content.\n"
        "Evaluate only the supplied research plan and search results.\n"
        "Return scores from 0.0 to 1.0.\n"
        "planning_quality measures whether the sub-questions cover the "
        "original research question and form a coherent plan.\n"
        "search_quality measures whether the returned sources are relevant "
        "and useful for answering the original question.\n"
        "Use concise rationales grounded only in the supplied data.\n\n"
        f"Original question:\n{question}\n\n"
        "Research plan:\n"
        f"{json.dumps(plan, ensure_ascii=False, indent=2)}\n\n"
        "Sources:\n"
        f"{json.dumps(source_lines, ensure_ascii=False, indent=2)}"
    )

    response = await _generate_content_with_retry(
        client=client,
        contents=prompt,
        response_schema=EvaluationExtraction,
    )

    evaluation = EvaluationExtraction.model_validate_json(
        _response_text(response),
    )

    return EvaluationExtraction(
        planning_quality_score=max(
            0.0,
            min(1.0, evaluation.planning_quality_score),
        ),
        planning_quality_rationale=evaluation.planning_quality_rationale,
        search_quality_score=max(
            0.0,
            min(1.0, evaluation.search_quality_score),
        ),
        search_quality_rationale=evaluation.search_quality_rationale,
    )


def _truncate_quality_evaluation_text(value: object, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text

    if limit <= 1:
        return text[:limit]

    return text[: limit - 1].rstrip() + "…"


def _normalize_quality_reasoning_item(item: object) -> str:
    if isinstance(item, dict):
        return _truncate_quality_evaluation_text(
            item.get("claim_text", item.get("text", "")),
            QUALITY_EVALUATION_MAX_REASONING_ITEM_CHARS,
        )

    return _truncate_quality_evaluation_text(
        item,
        QUALITY_EVALUATION_MAX_REASONING_ITEM_CHARS,
    )


def _normalize_quality_reasoning_metadata(
    item: object,
    key: str,
) -> list[int]:
    if not isinstance(item, dict):
        return []

    raw_values = item.get(key, [])

    if isinstance(raw_values, list):
        normalized_values: list[int] = []

        for value in raw_values:
            if isinstance(value, int):
                normalized_values.append(value)
            elif isinstance(value, str) and value.isdigit():
                normalized_values.append(int(value))

        return normalized_values

    return []


def build_quality_evaluation_payload(
    *,
    question: str,
    report_markdown: str,
    evidence: list[dict],
    reasoning: list[dict],
    fact_checks: list[dict],
) -> dict:
    """
    Build a bounded evidence payload for groundedness evaluation.

    The quality judge needs representative, traceable input rather than every
    persisted artifact. Bounds keep the request below Groq's TPM limit.
    """

    evidence_lines = [
        {
            "evidence_index": index,
            "claim_text": _truncate_quality_evaluation_text(
                item.get("claim_text"),
                QUALITY_EVALUATION_MAX_EVIDENCE_CLAIM_CHARS,
            ),
            "source_index": item.get("source_index", 0),
        }
        for index, item in enumerate(
            evidence[:QUALITY_EVALUATION_MAX_EVIDENCE_ITEMS],
        )
    ]

    reasoning_lines = [
        {
            "claim_text": _normalize_quality_reasoning_item(item),
            "supporting_source_indexes": _normalize_quality_reasoning_metadata(
                item,
                "supporting_source_indexes",
            ),
            "contradicting_source_indexes": _normalize_quality_reasoning_metadata(
                item,
                "contradicting_source_indexes",
            ),
        }
        for item in reasoning[:QUALITY_EVALUATION_MAX_REASONING_ITEMS]
    ]

    fact_check_lines = [
        {
            "claim_index": item.get("claim_index"),
            "status": item.get("status"),
            "explanation": _truncate_quality_evaluation_text(
                item.get("explanation"),
                QUALITY_EVALUATION_MAX_FACT_CHECK_EXPLANATION_CHARS,
            ),
            "supporting_evidence_indexes": item.get(
                "supporting_evidence_indexes",
                [],
            ),
            "contradicting_evidence_indexes": item.get(
                "contradicting_evidence_indexes",
                [],
            ),
        }
        for item in fact_checks[
            :QUALITY_EVALUATION_MAX_FACT_CHECK_ITEMS
        ]
    ]

    return {
        "question": _truncate_quality_evaluation_text(
            question,
            QUALITY_EVALUATION_MAX_QUESTION_CHARS,
        ),
        "report_markdown": _truncate_quality_evaluation_text(
            report_markdown,
            QUALITY_EVALUATION_MAX_REPORT_CHARS,
        ),
        "evidence": evidence_lines,
        "reasoning": reasoning_lines,
        "fact_checks": fact_check_lines,
        "truncation": {
            "evidence_items_sent": len(evidence_lines),
            "evidence_items_available": len(evidence),
            "reasoning_items_sent": len(reasoning_lines),
            "reasoning_items_available": len(reasoning),
            "fact_check_items_sent": len(fact_check_lines),
            "fact_check_items_available": len(fact_checks),
        },
    }


async def generate_quality_evaluation(
    *,
    question: str,
    report_markdown: str,
    evidence: list[dict],
    reasoning: list[dict],
    fact_checks: list[dict],
) -> QualityEvaluationExtraction:
    """Evaluate report groundedness with a bounded evidence payload."""

    client = _get_client()

    payload = build_quality_evaluation_payload(
        question=question,
        report_markdown=report_markdown,
        evidence=evidence,
        reasoning=reasoning,
        fact_checks=fact_checks,
    )

    prompt = (
        "You are an independent research-quality evaluator.\n"
        "Evaluate only whether the supplied report is grounded in the "
        "supplied evidence.\n"
        "Do not add outside knowledge.\n"
        "Groundedness score must be between 0.0 and 1.0, where 1.0 means "
        "the report's factual statements are fully supported by the evidence.\n"
        "Hallucination detection score must be between 0.0 and 1.0, where "
        "1.0 means no unsupported factual statements were detected.\n"
        "List every materially unsupported factual statement. Return an empty "
        "list when no unsupported statement is found.\n"
        "Use concise rationales grounded only in the supplied report and "
        "evidence.\n"
        "The input may be a bounded representative subset. Do not infer "
        "support from evidence that was not supplied.\n\n"
        f"Research question:\n{payload['question']}\n\n"
        f"Report:\n{payload['report_markdown']}\n\n"
        "Reasoning conclusions:\n"
        f"{json.dumps(payload['reasoning'], ensure_ascii=False, indent=2)}\n\n"
        "Fact-check results:\n"
        f"{json.dumps(payload['fact_checks'], ensure_ascii=False, indent=2)}\n\n"
        "Evidence:\n"
        f"{json.dumps(payload['evidence'], ensure_ascii=False, indent=2)}"
    )

    response = await _generate_content_with_retry(
        client=client,
        contents=prompt,
        response_schema=QualityEvaluationExtraction,
    )

    evaluation = QualityEvaluationExtraction.model_validate_json(
        _response_text(response),
    )

    return QualityEvaluationExtraction(
        groundedness_score=max(
            0.0,
            min(1.0, evaluation.groundedness_score),
        ),
        groundedness_rationale=evaluation.groundedness_rationale,
        hallucination_detection_score=max(
            0.0,
            min(1.0, evaluation.hallucination_detection_score),
        ),
        hallucination_detection_rationale=(
            evaluation.hallucination_detection_rationale
        ),
        unsupported_statements=evaluation.unsupported_statements,
    )


def _truncate_report_text(value: object, limit: int) -> str:
    return _truncate_quality_evaluation_text(value, limit)


def _normalize_report_reasoning_item(item: object, index: int) -> dict:
    if isinstance(item, dict):
        return {
            "claim_index": item.get("claim_index", index),
            "text": _truncate_report_text(
                item.get("text", item.get("claim_text", "")),
                REPORT_MAX_REASONING_ITEM_CHARS,
            ),
            "supporting_source_indexes": item.get(
                "supporting_source_indexes",
                [],
            ),
            "contradicting_source_indexes": item.get(
                "contradicting_source_indexes",
                [],
            ),
        }

    return {
        "claim_index": index,
        "text": _truncate_report_text(item, REPORT_MAX_REASONING_ITEM_CHARS),
        "supporting_source_indexes": [],
        "contradicting_source_indexes": [],
    }


def build_report_generation_payload(
    *,
    question: str,
    sources: list[dict],
    evidence: list[dict],
    reasoning: list[dict] | None = None,
    fact_checks: list[dict] | None = None,
) -> dict:
    """
    Build a bounded report-generation payload.

    Groq on-demand tiers can reject requests where prompt tokens plus the
    reserved completion budget exceed TPM. Report generation needs the best
    representative evidence, not every intermediate artifact.
    """

    source_lines = []

    for source in sources[:REPORT_MAX_SOURCES]:
        source_index = source.get("source_index", 0) + 1
        reliability_score = float(
            source.get("reliability_score") or 0.0,
        )
        title = _truncate_report_text(
            source.get("title") or "Untitled source",
            REPORT_MAX_SOURCE_TITLE_CHARS,
        )

        source_lines.append(
            f"[Source {source_index}] {title} "
            f"(rel {reliability_score:.2f})"
        )

    evidence_lines = []

    for item in evidence[:REPORT_MAX_EVIDENCE_ITEMS]:
        source_index = item.get("source_index", 0) + 1
        claim_text = _truncate_report_text(
            item.get("claim_text"),
            REPORT_MAX_EVIDENCE_CLAIM_CHARS,
        )
        evidence_lines.append(f"[Source {source_index}] {claim_text}")

    reasoning_lines = [
        _normalize_report_reasoning_item(item, index)
        for index, item in enumerate(
            (reasoning or [])[:REPORT_MAX_REASONING_ITEMS],
        )
    ]

    fact_check_lines = [
        {
            "claim_index": item.get("claim_index"),
            "status": item.get("status"),
            "explanation": _truncate_report_text(
                item.get("explanation"),
                REPORT_MAX_FACT_CHECK_EXPLANATION_CHARS,
            ),
            "supporting_evidence_indexes": item.get(
                "supporting_evidence_indexes",
                [],
            ),
            "contradicting_evidence_indexes": item.get(
                "contradicting_evidence_indexes",
                [],
            ),
        }
        for item in (fact_checks or [])[:REPORT_MAX_FACT_CHECK_ITEMS]
    ]

    return {
        "question": _truncate_report_text(question, REPORT_MAX_QUESTION_CHARS),
        "sources": source_lines,
        "evidence": evidence_lines,
        "reasoning": reasoning_lines,
        "fact_checks": fact_check_lines,
        "truncation": {
            "sources_sent": len(source_lines),
            "sources_available": len(sources),
            "evidence_items_sent": len(evidence_lines),
            "evidence_items_available": len(evidence),
            "reasoning_items_sent": len(reasoning_lines),
            "reasoning_items_available": len(reasoning or []),
            "fact_check_items_sent": len(fact_check_lines),
            "fact_check_items_available": len(fact_checks or []),
        },
    }


async def generate_report(
    question: str,
    sources: list[dict],
    evidence: list[dict],
    reasoning: list[dict] | None = None,
    fact_checks: list[dict] | None = None,
) -> ReportGeneration:
    """Generate a structured, evidence-grounded research report."""

    client = _get_client()
    payload = build_report_generation_payload(
        question=question,
        sources=sources,
        evidence=evidence,
        reasoning=reasoning,
        fact_checks=fact_checks,
    )

    prompt = (
        "Write a deep, evidence-grounded Markdown research report.\n"
        "Aim for 1450-1500 total words across executive_summary and "
        "content_markdown. Use roughly 1200-1300 words in "
        "content_markdown.\n"
        "Use only the supplied sources, evidence, reasoning, and fact-checks.\n"
        "Do not add outside knowledge or filler.\n"
        "Cite each factual statement with [Source X].\n"
        "Return JSON with:\n"
        "- executive_summary: 120-180 words, no heading\n"
        "- content_markdown: report body with these headings once each:\n"
        "  # <title>\n"
        "  ## Methodology\n"
        "  ## Findings\n"
        "  ## Analysis and Synthesis\n"
        "  ## Limitations and Risks\n"
        "  ## Recommendations\n"
        "  ## Conclusion\n"
        "Do not include an Executive Summary heading or References section.\n\n"
        f"Research question:\n{payload['question']}\n\n"
        "Available sources:\n"
        f"{json.dumps(payload['sources'], ensure_ascii=False, separators=(',', ':'))}\n\n"
        "Extracted evidence:\n"
        f"{json.dumps(payload['evidence'], ensure_ascii=False, separators=(',', ':'))}\n\n"
        "Reasoning conclusions:\n"
        f"{json.dumps(payload['reasoning'], ensure_ascii=False, separators=(',', ':'))}\n\n"
        "Fact-check results:\n"
        f"{json.dumps(payload['fact_checks'], ensure_ascii=False, separators=(',', ':'))}"
    )

    response = await _generate_content_with_retry(
        client=client,
        contents=prompt,
        response_schema=ReportGeneration,
        max_completion_tokens=REPORT_MAX_COMPLETION_TOKENS,
    )

    return ReportGeneration.model_validate_json(_response_text(response))
