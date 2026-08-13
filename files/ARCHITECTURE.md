# ARCHITECTURE.md

Status: **DRAFT — pending approval.** Once approved, this document is
frozen per the rules in AGENTS.md.

## 1. Clean Architecture layering

```
presentation/    FastAPI routers, request/response schemas, Next.js UI
application/     Use cases / services — orchestrates domain + infra,
                 no framework code here
domain/          Entities, value objects, domain services — pure Python,
                 no DB/HTTP/LLM imports
    infrastructure/  DB repositories (SQLAlchemy), LLM clients (Gemini),
                 MCP clients, LangGraph nodes, visualization, external APIs
```

Rule: LangGraph nodes and MCP tool functions are thin — they call an
application-layer use case and return its result. They never contain
business logic, DB queries, or prompt construction directly.

## 2. Backend service structure (proposed)

```
backend/
  app/
    presentation/
      api/v1/          # routers: auth, workspaces, research, reports,
                        # evaluation, observability
      schemas/         # Pydantic request/response models
    application/
      use_cases/       # e.g. start_research.py, resume_research.py,
                        # approve_report.py, export_report.py
      dto/
    domain/
      entities/         # ResearchRun, Evidence, Claim, Citation, Report
      value_objects/     # ConfidenceScore, Citation, SourceReliability
      services/          # domain-level scoring/validation logic
    infrastructure/
      db/
        models/          # SQLAlchemy ORM models
        repositories/    # concrete repo implementations
      llm/               # Gemini client wrapper, structured-output helpers
      mcp/                # MCP client(s), server configs
      agents/
        graph.py          # LangGraph graph assembly
        nodes/             # one file per agent node (thin adapters)
        state.py            # shared graph state schema
      observability/       # LangSmith wiring
      evaluation/            # evaluators, scoring pipelines
      export/                # Markdown/PDF/DOCX report renderers
    core/
      config.py               # env/settings
      security.py               # JWT, password hashing
      logging.py                  # safe/structured logging
  alembic/
  tests/
    unit/ integration/ api/ db/ agent/ mcp/ evaluation/
```

## 3. Agent architecture

Single-responsibility agents, coordinated by a Supervisor via LangGraph:

- **Supervisor** — routes between agents based on graph state; decides
  what runs next, in parallel or sequence; handles resume-from-checkpoint.
- **Planning Agent** — turns the research question into a structured
  research plan (sub-questions, search strategies).
- **Research Agent** — executes searches/tool calls per sub-question
  (parallelizable — one instance per sub-question).
- **Evidence Agent** — extracts structured evidence/claims from raw
  sources.
- **Verification Agent** — checks source reliability/credibility.
- **Reasoning Agent** — synthesizes evidence into conclusions.
- **Fact Checking Agent** — cross-checks claims against evidence,
  flags contradictions.
- **Report Agent** — assembles the final cited report.
- **Chart generation** — an infrastructure renderer produces PNG charts only
  when the Report Agent receives a validated chartable-data specification.
- **Original topic illustrations** — not included in M26. If added in a
  future milestone, they must be newly generated visuals stored as report
  assets; source-page images are not copied or embedded.
- **Evaluation Agent** — scores the completed run against the quality
  dimensions in EVALUATION.md (runs after Report Agent, not blocking
  report delivery to the user).

State is persisted via LangGraph checkpointing (Postgres-backed) so a run
can be paused for human approval and resumed later — this is the
architectural basis for "Human Approval" and "Research Resume" as
first-class features, not bolted on.

## 4. MCP architecture

MCP is used for tool integrations that are genuinely external/pluggable —
e.g. a web-search MCP server, a web-fetch/scrape MCP server. Tools that are
purely internal computation (e.g. confidence scoring math) are plain
LangGraph tools, not MCP servers — MCP is reserved for things a future
contributor might swap or add without touching agent code.

New MCP servers register in `infrastructure/mcp/registry.py` and become
available to the Research Agent without changing existing agent code.

Visualization is separate from agent decision-making: Gemini identifies
whether quantitative findings are genuinely chartable, while the renderer
only renders the supplied structured specification. Development PNGs may be
stored locally; production object storage is deferred.

## 5. Frontend architecture

Next.js App Router, TypeScript, Tailwind, and shadcn-style UI components.
The initial M22 scaffold provides the landing, authentication, and dashboard
surfaces. Key product surfaces are:
dashboard, workspace/research view (live progress + resume), report view
(citations, confidence, approve/reject/comment), evaluation dashboard,
observability dashboard, settings. Dark mode, responsive, loading/error
states throughout.

M22 kept authentication and research forms presentation-only. M23 adds the
thin frontend API client, JWT persistence, backend-connected authentication,
workspace operations, research submission, and ownership-protected status
retrieval. The backend remains the source of truth for authorization and
research-run state. M23 displays an in-flight loading state and the final
status from the synchronous research request; true streamed progress is
deferred until a durable SSE/WebSocket transport is implemented.

M24 adds the report-review route with citations, confidence, approval, and
feedback. M25 adds the `/analytics` route, which consumes the existing
evaluation and observability APIs for aggregate and per-run dashboards. Until
M27 implements persistent research history and run selection, per-run
analytics inspection requires a manually entered research-run UUID.

M26 adds a presentation-layer export endpoint backed by an application use
case and infrastructure renderers. Export rendering reuses persisted report,
citation, and report-asset data; it does not generate new research content.
PDF output normalizes unsupported Unicode punctuation, and asset paths are
validated to remain inside the backend asset root before embedding.

## 6. Deployment architecture

Docker Compose for local dev (backend + Postgres + frontend). Production:
containerized backend + frontend deployed to a hosting provider (decision
pending — see DECISIONS.md), Neon Postgres for the DB, GitHub Actions for
CI (lint, test, build, deploy on merge to main).

## 7. Observability architecture

LangSmith wraps every LLM call, every LangGraph node execution, every tool
call, and every MCP call. Traces are linked back to the research run ID so
the Observability Dashboard can show, per run: full agent trace, token
usage, latency, retries, errors, and estimated cost.

## Open decisions still needed before full freeze
- Hosting provider for backend/frontend in production
- Exact MCP servers to build/use for v1 (search + fetch minimum)
- Whether checkpointing uses LangGraph's native Postgres checkpointer or a
  custom implementation
