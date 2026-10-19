"""
Interactive Smoke Test with Live Groq LLM & Actual Human-in-the-Loop Intervention.

Executes the LangGraph agent graph until it hits the `approval_gate` interrupt.
Displays the exact evidence and fact-checking review screen in the terminal.
Prompts for user approval, resumes the graph, and generates the final evaluated report.
"""
import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langgraph.checkpoint.memory import MemorySaver

from app.core.config import get_settings
from app.infrastructure.agents.graph import (
    approve_research_graph,
    run_research_graph,
)


def get_status_label(status: str) -> str:
    norm = (status or "").lower().strip()
    if norm in {"supported", "verified"}:
        return "[✓ Verified Support]"
    if norm == "partially_supported":
        return "[! Partially Supported (Qualified)]"
    if norm == "uncertain":
        return "[? Uncertain]"
    if norm == "contradicted":
        return "[✗ Contradicted]"
    if norm == "unsupported":
        return "[✗ Unsupported]"
    if norm == "irrelevant":
        return "[- Irrelevant]"
    return f"[{norm.capitalize()}]"


async def main():
    settings = get_settings()
    if not settings.groq_api_key:
        print("ERROR: GROQ_API_KEY is not set in backend/.env")
        sys.exit(1)

    question = (
        "How do retrieval-augmented generation (RAG) architectures "
        "mitigate hallucinations in production LLM applications?"
    )

    print("\n" + "=" * 76)
    print("  DEEPCITE: LIVE AGENT GRAPH SMOKE TEST (WITH HUMAN-IN-THE-LOOP)")
    print("=" * 76)
    print(f"Research Question:\n  \"{question}\"\n")

    checkpointer = MemorySaver()
    thread_id = "smoke-test-hitl-thread"

    print("[Phase 1/2] Executing agents with live LLM up to approval gate...")
    print("  - Supervisor Agent -> Planning Agent (Groq LLM)")
    print("  - Research Agent -> Tavily Search (or Web)")
    print("  - Verification Agent -> Reliability Scoring")
    print("  - Evidence Agent (Groq LLM with relevance constraints)")
    print("  - Reasoning Agent (Groq LLM synthesis)")
    print("  - Fact-Checking Agent (Groq LLM calibrated verification)")
    print("  - Approval Gate (Interrupt)\n")

    result = await run_research_graph(
        research_run_id=thread_id,
        question=question,
        checkpointer=checkpointer,
    )

    # Verify that the graph paused at approval_gate
    interrupts = result.get("__interrupt__")
    if not interrupts:
        print("Expected graph to interrupt at approval_gate, but finished early.")
        sys.exit(1)

    print("=" * 76)
    print("  >>> PAUSED AT APPROVAL GATE: HUMAN-IN-THE-LOOP INTERVENTION REQUIRED <<<")
    print("=" * 76)

    # Retrieve checkpoint state
    config = {"configurable": {"thread_id": thread_id}}
    checkpoint_tuple = await checkpointer.aget_tuple(config)
    channel_values = checkpoint_tuple.checkpoint.get("channel_values", {})

    state_sources = channel_values.get("verified_sources") or channel_values.get("sources") or []
    state_evidence = channel_values.get("evidence") or []
    reasoning_data = channel_values.get("reasoning") or {}
    reasoning_items = reasoning_data.get("items") or []
    fact_checks_data = channel_values.get("fact_checks") or {}
    fact_check_items = fact_checks_data.get("items") or []

    fact_check_map = {fc.get("claim_index"): fc for fc in fact_check_items}
    src_by_idx = {s.get("source_index", idx): s for idx, s in enumerate(state_sources)}
    ev_by_idx = {idx: ev for idx, ev in enumerate(state_evidence)}

    # Build review evidence list
    review_items = []
    for claim_idx, claim_text in enumerate(reasoning_items):
        fc = fact_check_map.get(claim_idx, {})
        status = fc.get("status", "unverified")
        supp_ev_indices = fc.get("supporting_evidence_indexes") or []
        explanation = fc.get("explanation", "")

        supp_text = None
        src_title = None
        src_rel = None
        if supp_ev_indices:
            ev = ev_by_idx.get(supp_ev_indices[0], {})
            supp_text = ev.get("claim_text")
            src = src_by_idx.get(ev.get("source_index"), {})
            src_title = src.get("title")
            src_rel = src.get("reliability_score")

        review_items.append({
            "claim_index": claim_idx + 1,
            "claim_text": claim_text,
            "status": status,
            "explanation": explanation,
            "supporting_evidence": supp_text,
            "source_title": src_title,
            "source_reliability": src_rel,
        })

    verified_count = sum(
        1 for item in review_items
        if item["status"] in {"verified", "supported"}
    )

    print(f"\n[APPROVAL SCREEN BADGE]: {verified_count} of {len(review_items)} Findings Verified\n")
    print("-" * 76)
    for item in review_items:
        badge = get_status_label(item["status"])
        print(f"Finding #{item['claim_index']}: {badge}")
        print(f"  Claim:       {item['claim_text']}")
        if item['supporting_evidence']:
            print(f"  Evidence:    \"{item['supporting_evidence']}\"")
        if item['source_title']:
            print(f"  Source:      {item['source_title']} (rel: {item['source_reliability']})")
        if item['explanation']:
            print(f"  Audit Note:  {item['explanation']}")
        print("-" * 76)

    # Actual human input prompt
    print("\n[ACTION REQUIRED]: This is the human approval gate.")
    choice = input("Approve research findings and proceed to report generation? [Y/n]: ").strip().lower()

    if choice in {"n", "no", "q", "quit"}:
        print("\nResearch run paused by human operator. Aborting report generation.")
        return

    print("\n[Phase 2/2] Human approved! Resuming graph with Command(resume=True)...")
    print("  - Approval Gate -> Resumed")
    print("  - Report Agent -> Generating Full Markdown Report (Groq LLM)")
    print("  - Evaluation Agent -> Computing Completeness & Support (Groq LLM + Deterministic)")

    final_result = await approve_research_graph(
        research_run_id=thread_id,
        checkpointer=checkpointer,
    )

    print("\n" + "=" * 76)
    print("  RESEARCH GRAPH EXECUTION COMPLETED")
    print("=" * 76)

    final_report = final_result.get("report") or {}
    content_md = final_report.get("content_markdown", "")
    summary = final_report.get("executive_summary", "")

    print(f"\nExecutive Summary:\n{summary}\n")
    print(f"Full Markdown Report Generated ({len(content_md.split())} words):")
    print(content_md[:500] + "...\n[Content continues]\n")

    evaluations = final_result.get("evaluations") or []
    if not evaluations:
        from app.infrastructure.evaluation.evaluator import evaluate_research
        evaluations = await evaluate_research(
            question=question,
            plan=channel_values.get("plan") or {},
            sources=state_sources,
            report=final_report,
            evidence=state_evidence,
            reasoning=reasoning_data.get("items") or [],
            fact_checks=fact_check_items,
        )

    print("=" * 76)
    print("FINAL EVALUATIONS SUMMARY:")
    for ev in evaluations:
        dim = ev.get("dimension")
        score = ev.get("score")
        score_str = f"{score:.4f}" if isinstance(score, float) else str(score)
        details = ev.get("details", {})
        rationale = details.get("rationale") or details.get("method") or ""

        display_dim = dim
        if dim == "hallucination_detection":
            display_dim = "hallucination_free"
        elif dim == "report_quality":
            display_dim = "report_completeness"

        print(f"  * {display_dim:24}: {score_str}")
        if rationale:
            print(f"    -> {rationale}")
        unsupported = details.get("unsupported_statements")
        if unsupported:
            print(f"    -> Flagged items: {unsupported}")
    print("=" * 76)
    print("SMOKE TEST PASSED COMPLETELY.")


if __name__ == "__main__":
    asyncio.run(main())

