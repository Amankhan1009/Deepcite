"""
Live End-to-End Deepcite Research Pipeline Run.
Calls the live Groq LLM across the entire pipeline:
Planning -> Evidence Extraction -> Reasoning -> Fact-Checking -> Report Generation -> Evaluation.
"""
import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


async def main():
    settings = get_settings()
    if not settings.groq_api_key:
        print("ERROR: GROQ_API_KEY is not set in backend/.env")
        sys.exit(1)

    question = (
        "How do retrieval-augmented generation (RAG) architectures "
        "mitigate hallucinations in production LLM applications?"
    )

    print("\n" + "=" * 70)
    print(f"RESEARCH QUESTION:\n{question}")
    print("=" * 70)

    print("\n[1/5] Planning Agent: Calling Groq LLM...")
    plan = await generate_research_plan(question)
    print(f"Strategy: {plan.strategy}")
    for idx, sq in enumerate(plan.sub_questions):
        print(f"  Sub-question {idx + 1}: {sq}")

    sources = [
        {
            "source_index": 0,
            "title": "Stanford AI Lab: Survey on Hallucination Mitigation via RAG",
            "url": "https://ai.stanford.edu/blog/rag-hallucinations-2024",
            "reliability_score": 0.88,
            "content": (
                "Retrieval-augmented generation (RAG) reduces factual hallucination rates from 14.2% to 2.8% "
                "across medical and legal benchmark questions by grounding completions in verified vector embeddings. "
                "However, retrieval noise and poorly ranked context can reintroduce conflicting information."
            ),
        },
        {
            "source_index": 1,
            "title": "MIT Technology Review: Enterprise Knowledge Retrieval Systems",
            "url": "https://technologyreview.com/enterprise-rag-evaluation",
            "reliability_score": 0.82,
            "content": (
                "Hybrid search combining dense semantic vectors with BM25 lexical keyword ranking improves context recall "
                "to 91% compared to 74% for pure vector search alone in high-throughput enterprise pipelines."
            ),
        },
        {
            "source_index": 2,
            "title": "ArXiv: Chunking Strategies and Context Window Bottlenecks",
            "url": "https://arxiv.org/abs/2403.99999",
            "reliability_score": 0.90,
            "content": (
                "Hierarchical sentence window chunking preserves 34% more semantic context than fixed 500-token chunks. "
                "Context compression filters out 40% of irrelevant tokens before generation, reducing token costs."
            ),
        },
        {
            "source_index": 3,
            "title": "ACM Computing Surveys: Verification Layers in Modern RAG",
            "url": "https://acm.org/surveys/rag-verification-layers",
            "reliability_score": 0.85,
            "content": (
                "Post-generation claim-level verification agents detect remaining hallucinated assertions with 89% precision, "
                "providing an essential secondary safety layer prior to returning responses to end users."
            ),
        },
    ]

    print("\n[2/5] Evidence Agent: Calling Groq LLM across 4 diverse sources...")
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

    print(f"Extracted {len(all_evidence)} factual claims:")
    for ev in all_evidence:
        print(f"  - [Source {ev['source_index'] + 1}] {ev['claim_text']}")

    print("\n[3/5] Reasoning Agent: Calling Groq LLM to synthesize conclusions...")
    reasoning_result = await generate_reasoning(
        question=question,
        sources=sources,
        evidence=all_evidence,
    )
    reasoning_items = [
        {"claim_index": idx, "claim_text": text}
        for idx, text in enumerate(reasoning_result.items)
    ]
    print(f"Synthesized {len(reasoning_items)} conclusions:")
    for item in reasoning_items:
        print(f"  {item['claim_index'] + 1}. {item['claim_text']}")

    print("\n[4/5] Fact Checking Agent: Calling Groq LLM to verify claims against evidence...")
    fact_check_result = await generate_fact_checks(
        question=question,
        reasoning=reasoning_items,
        evidence=all_evidence,
    )
    fact_check_items = [item.model_dump() for item in fact_check_result.items]
    for fc in fact_check_items:
        print(f"  Claim {fc['claim_index'] + 1}: status = {fc['status']}")
        print(f"    Explanation: {fc['explanation']}")

    claim_support = calculate_claim_support(fact_check_items)
    print(f"\nEmpirical Claim Support Score: {claim_support['score']}")
    print(f"  Breakdown: {claim_support['supported_count']} supported, {claim_support['partially_supported_count']} partially supported, {claim_support['unsupported_count']} unsupported")

    selected_sources = select_report_sources(sources)
    print(f"\nReport Source Selection: {len(selected_sources)} of {len(sources)} sources selected (threshold = 0.50):")
    for s in selected_sources:
        print(f"  - [Source {s['source_index'] + 1}] {s['title']}")

    filtered_evidence = filter_evidence_for_sources(all_evidence, selected_sources)
    filtered_fc = filter_fact_checks_for_evidence(
        fact_checks=fact_check_items,
        selected_evidence=filtered_evidence,
        all_evidence=all_evidence,
    )

    print("\n[5/5] Report Agent: Calling Groq LLM to generate full research report...")
    report = await generate_report(
        question=question,
        sources=selected_sources,
        evidence=filtered_evidence,
        reasoning=reasoning_items,
        fact_checks=filtered_fc,
    )
    words = len(report.content_markdown.split())
    print(f"\nReport Generated successfully ({words} words)!")
    print("\n--- EXECUTIVE SUMMARY ---")
    print(report.executive_summary)

    completeness = calculate_report_quality(
        report_markdown=report.content_markdown,
        executive_summary=report.executive_summary,
    )
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS:")
    print(f"  Report Completeness: {completeness['score']}")
    print(f"    Words: {completeness['word_count']} / 1500")
    print(f"    Sections: {completeness['present_section_count']} / 7 present ({', '.join(completeness['present_sections'])})")
    print(f"    Citation markers: {completeness['citation_count']}")
    print(f"  Claim Support: {claim_support['score']}")
    print("=" * 70)
    print("\nCOMPLETE RESEARCH RUN VIA LIVE GROQ LLM FINISHED.")


if __name__ == "__main__":
    asyncio.run(main())

