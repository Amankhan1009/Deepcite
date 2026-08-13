# EVALUATION.md

Evaluation is a first-class feature, run automatically at the end of every
research run (async, non-blocking to report delivery).

## Dimensions (v1)
- **Planning quality** — does the plan's sub-questions actually cover the
  original question? (LLM-judge against the original question + plan)
- **Search quality** — did research queries return relevant sources?
- **Source reliability** — aggregate of Verification Agent's per-source
  scores
- **Citation coverage** — % of claims in the report that have a citation
- **Groundedness** — % of report statements traceable to evidence
  (LLM-judge comparing report text to evidence store)
- **Hallucination detection** — flags statements with no supporting
  evidence at all
- **Report quality** — LLM-judge rubric: clarity, structure, completeness
- **Confidence score** — the report's own stated confidence vs. an
  independent evaluator's estimate (delta = calibration signal)
- **Overall research quality** — weighted rollup of the above

## Storage
Each dimension is one row in `evaluations` (see DATABASE.md), so scores
are queryable per-run and aggregable over time — this is what powers the
Evaluation Dashboard (trend lines, not just single-run snapshots).

## Implementation approach
Evaluation Agent runs as the final LangGraph node after Report Agent.
LLM-judge evaluations use a separate, evaluation-specific prompt (never
reuse the generation prompt as its own judge without adjustment) and are
themselves traced in LangSmith like any other agent step, so evaluation
cost/latency is visible too.

## M18 implementation status
Planning quality and search quality are scored by the independent evaluation
judge. Source reliability is calculated as the mean of the Verification
Agent's per-source reliability scores. Each available dimension is persisted
as one idempotent row per research run in the `evaluations` table.

Evaluation execution is non-blocking: a failed evaluation does not prevent a
completed report from being delivered.

## M19 implementation status
Citation coverage is calculated deterministically from factual report lines
containing source markers, capped by the number of reasoning claims.

Groundedness and hallucination detection are evaluated by a separate Groq
quality-judge prompt that compares the report with evidence, reasoning, and
fact-check results. Hallucination detection is represented as a bounded score
where `1.0` means no materially unsupported statements were found; the
details JSONB field stores unsupported statements identified by the judge.

Overall research quality is the deterministic mean of all available
evaluation dimensions, excluding the overall dimension itself. M19 is
verified with seven persisted dimensions and LangSmith traces for the
Evaluation Agent and structured-generation calls.

## Deferred to later milestones
Human-labeled eval sets / regression testing against a golden dataset —
valuable but not v1-blocking; noted under Future Improvements in
DECISIONS.md once the automatic evaluators are working. Evaluation aggregate
and per-run API access is deferred to M20.
