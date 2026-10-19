import os

import pytest

from app.core.config import get_settings
from app.domain.services.evaluation_scoring import (
    calculate_claim_support,
    calculate_report_quality,
)
from app.domain.services.report_source_selection import (
    filter_evidence_for_sources,
    filter_fact_checks_for_evidence,
    select_report_sources,
)
from app.infrastructure.llm.groq_client import (
    generate_evidence,
    generate_fact_checks,
    generate_reasoning,
    generate_report,
    generate_research_plan,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not get_settings().groq_api_key or os.getenv("RUN_GROQ_INTEGRATION") != "1",
        reason="Set GROQ_API_KEY and RUN_GROQ_INTEGRATION=1 to run the real Groq test",
    ),
]


@pytest.mark.asyncio
async def test_complete_end_to_end_research_pipeline_with_live_llm():
    """
    Execute the entire research pipeline from question to final evaluated report
    using live Groq LLM calls across all agents.
    """
    question = (
        "How do retrieval-augmented generation (RAG) architectures "
        "mitigate hallucinations in production LLM applications?"
    )

    print("\n" + "=" * 70)
    print("STEP 1: Calling Groq LLM -> Generating Structured Research Plan")
    print("=" * 70)
    plan = await generate_research_plan(question)
    assert plan.sub_questions
    assert len(plan.sub_questions) >= 3
    print(f"Strategy: {plan.strategy}")
    for idx, sq in enumerate(plan.sub_questions):
        print(f"  Sub-question {idx + 1}: {sq}")

    # 4 diverse authoritative sources
    sources = [
        {
            "source_index": 0,
            "title": "Stanford AI Lab: Survey on Hallucination Mitigation via RAG",
            "url": "https://ai.stanford.edu/blog/rag-hallucinations-2024",
            "reliability_score": 0.88,
            "content": (
                "Retrieval-augmented generation (RAG) reduces factual hallucination rates "
                "from 14.2% to 2.8% across medical and legal benchmark questions by grounding "
                "completions in verified vector embeddings. However, retrieval noise and poorly "
                "ranked context can reintroduce conflicting information."
            ),
        },
        {
            "source_index": 1,
            "title": "MIT Technology Review: Enterprise Knowledge Retrieval Systems",
            "url": "https://technologyreview.com/enterprise-rag-evaluation",
            "reliability_score": 0.82,
            "content": (
                "Hybrid search combining dense semantic vectors with BM25 lexical keyword ranking "
                "improves context recall to 91% compared to 74% for pure vector search alone in "
                "high-throughput enterprise pipelines."
            ),
        },
        {
            "source_index": 2,
            "title": "ArXiv: Chunking Strategies and Context Window Bottlenecks",
            "url": "https://arxiv.org/abs/2403.99999",
            "reliability_score": 0.90,
            "content": (
                "Hierarchical sentence window chunking preserves 34% more semantic context than "
                "fixed 500-token chunks. Context compression filters out 40% of irrelevant tokens "
                "before generation, reducing token costs."
            ),
        },
        {
            "source_index": 3,
            "title": "ACM Computing Surveys: Verification Layers in Modern RAG",
            "url": "https://acm.org/surveys/rag-verification-layers",
            "reliability_score": 0.85,
            "content": (
                "Post-generation claim-level verification agents detect remaining hallucinated "
                "assertions with 89% precision, providing an essential secondary safety layer "
                "prior to returning responses to end users."
            ),
        },
    ]

    print("\n" + "=" * 70)
    print("STEP 2: Calling Groq LLM -> Extracting Evidence across Sources")
    print("=" * 70)
    all_evidence = []
    ev_idx = 0
    for src in sources:
        extraction = await generate_evidence(
            source_title=src["title"],
            source_content=src["content"],
            research_question=question,
            sub_question=plan.sub_questions[0],
        )
        for claim in extraction.items:
            all_evidence.append(
                {
                    "evidence_index": ev_idx,
                    "source_index": src["source_index"],
                    "claim_text": claim,
                }
            )
            ev_idx += 1

    print(f"Extracted {len(all_evidence)} factual claims across {len(sources)} sources:")
    for ev in all_evidence[:4]:
        print(f"  - [Source {ev['source_index'] + 1}]: {ev['claim_text']}")

    assert len(all_evidence) > 0

    print("\n" + "=" * 70)
    print("STEP 3: Calling Groq LLM -> Synthesizing Reasoning Conclusions")
    print("=" * 70)
    reasoning_result = await generate_reasoning(
        question=question,
        sources=sources,
        evidence=all_evidence,
    )
    assert reasoning_result.items
    reasoning_items = [
        {"claim_index": idx, "claim_text": text}
        for idx, text in enumerate(reasoning_result.items)
    ]
    print(f"Synthesized {len(reasoning_items)} reasoning conclusions:")
    for item in reasoning_items:
        print(f"  {item['claim_index'] + 1}. {item['claim_text']}")

    print("\n" + "=" * 70)
    print("STEP 4: Calling Groq LLM -> Fact-Checking Claims against Evidence")
    print("=" * 70)
    fact_check_result = await generate_fact_checks(
        question=question,
        reasoning=reasoning_items,
        evidence=all_evidence,
    )
    assert fact_check_result.items
    fact_check_items = [item.model_dump() for item in fact_check_result.items]

    for fc in fact_check_items:
        print(f"  Claim {fc['claim_index'] + 1}: status = {fc['status']}")
        print(f"    Explanation: {fc['explanation']}")

    # Calculate claim support
    claim_support = calculate_claim_support(fact_check_items)
    print(f"\nEmpirical Claim Support Score: {claim_support['score']}")
    print(
        f"  Supported: {claim_support['supported_count']}, "
        f"Partially Supported: {claim_support['partially_supported_count']}, "
        f"Unsupported: {claim_support['unsupported_count']}"
    )

    # Select report sources (validating coverage fix)
    selected_sources = select_report_sources(sources)
    print(
        f"\nSelected {len(selected_sources)} of {len(sources)} sources for report "
        "(diversity threshold = 0.50):"
    )
    for s in selected_sources:
        print(f"  - [Source {s['source_index'] + 1}] {s['title']} (rel: {s['reliability_score']})")

    assert len(selected_sources) >= 3

    filtered_evidence = filter_evidence_for_sources(all_evidence, selected_sources)
    filtered_fc = filter_fact_checks_for_evidence(
        fact_checks=fact_check_items,
        selected_evidence=filtered_evidence,
        all_evidence=all_evidence,
    )

    print("\n" + "=" * 70)
    print("STEP 5: Calling Groq LLM -> Generating Full Markdown Report")
    print("=" * 70)
    report = await generate_report(
        question=question,
        sources=selected_sources,
        evidence=filtered_evidence,
        reasoning=reasoning_items,
        fact_checks=filtered_fc,
    )
    assert report.content_markdown
    words = len(report.content_markdown.split())
    print(f"Generated Report ({words} words):")
    print(f"Executive Summary:\n{report.executive_summary}\n")

    # Evaluate report completeness
    completeness = calculate_report_quality(
        report_markdown=report.content_markdown,
        executive_summary=report.executive_summary,
    )
    print("=" * 70)
    print("EVALUATION SCORES (NEW SEPARATED METRICS):")
    print(f"1. Report Completeness: {completeness['score']}")
    print(f"   Word count: {completeness['word_count']} / 1500")
    present_secs = ", ".join(completeness["present_sections"])
    print(f"   Sections: {completeness['present_section_count']} / 7 present ({present_secs})")
    print(f"   Citations: {completeness['citation_count']} markers")
    print(f"2. Claim Support: {claim_support['score']}")
    print(
        f"   Breakdown: {claim_support['supported_count']} supported, "
        f"{claim_support['partially_supported_count']} partially supported"
    )
    print("=" * 70)

    assert completeness["score"] > 0.0
    assert claim_support["score"] is not None

