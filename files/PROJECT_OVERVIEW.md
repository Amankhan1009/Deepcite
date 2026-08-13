# PROJECT_OVERVIEW.md

## What this is
A production-grade AI Deep Research Platform: a multi-agent system that
takes a research question, plans a research strategy, executes parallel
research across sources, verifies and extracts evidence, reasons over it,
fact-checks claims, and produces a cited, confidence-scored report — with
every step traceable, evaluable, and resumable.

This is not a chatbot, a RAG demo, or a LangGraph tutorial. It's a platform:
multi-user, persistent, observable, evaluated, and deployable.

## Who it's for
Primary purpose: flagship portfolio project demonstrating AI Engineering,
Agentic AI (LangGraph), MCP, production backend engineering, modern
frontend development, DevOps, LLMOps, evaluation, observability, and system
design — targeting AI Engineer / GenAI Engineer / Agentic AI Engineer roles.

## What "done" looks like for v1.0
- A user can register, log in, and create a research workspace.
- They can submit a research question and watch it move through planning →
  parallel research → verification → reasoning → fact-checking → report,
  with live progress and the ability to pause and resume.
- The final report has inline citations, per-claim confidence scores, and
  can be exported as Markdown, PDF, or DOCX.
- Every agent run, tool call, and LLM call is traced in LangSmith.
- Every completed research run has evaluation scores across the defined
  quality dimensions (see EVALUATION.md), visible in a dashboard.
- The user can approve, reject, comment on, or rate any report.
- The whole thing runs via Docker Compose locally and is deployed
  (backend + frontend + DB) to real infrastructure with CI via GitHub
  Actions.

## Explicit non-goals for v1.0
- Full admin dashboard / multi-tenant org management (future).
- Multiple LLM provider support (Gemini only for v1; provider abstraction
  is a documented future improvement, not built now).
- Real-time collaborative editing of reports.

## Sequencing philosophy
Because the full feature list is large, v1.0 is built in phases that each
produce something demonstrable, rather than building all breadth first:
1. **Foundation** — auth, workspaces, DB, one agent, one straight-line
   research run, no UI polish.
2. **Agent mesh** — full multi-agent graph, parallelism, checkpointing/
   resume, human approval.
3. **Quality layer** — evaluation, observability dashboard, fact-checking,
   confidence scoring.
4. **Product layer** — full Next.js SaaS frontend, exports, dashboards.
5. **Ops layer** — Docker Compose, CI, deployment, hardening.

See MILESTONES.md for the concrete breakdown.
