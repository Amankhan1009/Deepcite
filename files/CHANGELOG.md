# CHANGELOG.md

## Milestone 27 — Settings, research history, and run selection

Completed the M27 product workflow improvements.

- Added persisted user settings with ownership-protected `GET/PATCH
  /api/v1/settings` endpoints.
- Added the `user_settings` table and Alembic migrations, including the
  follow-up migration that keeps the schema aligned with the ORM metadata.
- Added ownership-scoped research history through
  `GET /api/v1/workspaces/{workspace_id}/research`.
- Added frontend `/history` and `/settings` routes.
- Added dashboard navigation for History and Settings.
- Replaced manual research-run UUID entry in Analytics with a selectable
  research-history dropdown.
- Verified 89 backend tests passed, 3 integration tests were intentionally
  skipped, Ruff passed, and frontend lint/build passed successfully.
- Follow-up: expose the existing paused-run resume capability through a
  visible frontend Resume button.

## Roadmap update after Milestone 27

- Promoted the visible paused-run Resume workflow to Milestone 28 so the
  user-facing recovery experience is completed before containerization.
- Promoted deeper report generation and report-quality evaluation to M29 so
  report behavior is finalized before containerization.
- Shifted Docker Compose to M30, GitHub Actions CI to M31, and production
  deployment/hardening to M32.

## Milestone 28 — Frontend resume workflow

Completed the user-facing recovery workflow for interrupted research runs.

- Added Resume actions for `paused` and `failed` runs in research history.
- Added Resume action to the research detail page.
- Reused the existing ownership-protected checkpoint-resume endpoint.
- Added loading and status transitions after a resume request.
- Preserved the approval button when a resumed run reaches
  `awaiting_approval`.
- Verified a real browser flow through resume, approval, report retrieval,
  and Markdown/PDF export.
- Verified 89 backend tests passed, 3 integration tests were intentionally
  skipped, frontend lint passed, and the Next.js production build passed.

## Milestone 26 — Report export

Added production-oriented report export for the existing persisted report.

- Added Markdown, PDF, and DOCX export through the ownership-protected
  `GET /api/v1/reports/{id}/export?format=markdown|pdf|docx` endpoint.
- Included persisted report assets in export output when they resolve safely
  inside the backend asset root.
- Added References sections containing persisted source titles and URLs,
  deduplicated by source.
- Normalized unsupported Unicode punctuation during PDF rendering to prevent
  black-square glyphs.
- Prevented duplicate executive summaries in exported documents.
- Verified focused export tests, Ruff, 85 backend tests, and 3 intentionally
  skipped integration tests.
- Known limitation: report depth depends on the Report Agent output and is
  not artificially expanded by the export layer. Deeper report-generation
  requirements remain future work.

## Phase 0 — Planning
- Reviewed master project specification.
- Identified risks: overall scope size, Gemini structured-output/tool-call
  parity unverified, checkpointing implications of resume/approval
  features, MCP boundary needs defining, RBAC scope for v1 needs
  clarification.
- Drafted ARCHITECTURE.md (Clean Architecture layering, agent
  architecture, MCP boundary, frontend/deployment/observability
  architecture) — pending approval.
- Drafted 30-milestone roadmap across 5 phases (MILESTONES.md).
- Created initial documentation set (this file, AGENTS.md,
  PROJECT_OVERVIEW.md, CURRENT_STATE.md, DECISIONS.md, DATABASE.md,
  API.md, EVALUATION.md, TODO.md, DEPLOYMENT.md).

## Milestone 23 — Backend-connected workspace and research UI

Connected the Next.js frontend to the existing authenticated research API.

- Added shared frontend API and authentication helpers using the existing JWT
  bearer-token contract.
- Connected registration and login forms to the backend and added dashboard
  authentication handling.
- Added workspace listing and creation from the dashboard.
- Added research-question submission and current run-status display.
- Added ownership-protected `GET /api/v1/research/{id}` status retrieval.
- Added local-development CORS support for the frontend dev origins.
- Verified a real browser flow from registration through workspace creation,
  research submission, approval, and `completed` status retrieval.
- Verified 76 backend tests passed, 3 integration tests were intentionally
  skipped, Ruff passed, and frontend lint/build passed.
- Deferred historical run/report browsing and true streamed progress to later
  product milestones.

## Milestone 24 — Report review and feedback UI

Added the authenticated report-review product surface.

- Added the dynamic `/research/[id]` frontend route.
- Added report rendering with executive summary, Markdown content, overall
  confidence, citation claims, source links, and reliability scores.
- Reused the existing approval endpoint to resume `awaiting_approval` runs
  directly from the frontend.
- Added the `report_feedback` table, Alembic migration, repository, use case,
  schema, and ownership-protected feedback endpoint.
- Added report feedback controls for approve, reject, comment, and rating.
- Verified real browser approval and feedback submission; feedback returned
  HTTP 201 Created.
- Verified Alembic clean, Ruff clean, 79 backend tests passed, 3 intentionally
  skipped integration tests, and frontend lint/build passed without warnings.
- Historical research listing remains deferred to M27.

## Milestone 25 — Evaluation and observability dashboards

Added the frontend quality and operations dashboard at `/analytics`.

- Added aggregate evaluation dimensions with average scores and run counts.
- Added aggregate observability metrics for runs, traces, tokens, latency,
  retries, errors, and estimated cost.
- Added per-run evaluation and LangSmith trace inspection using an owned
  research-run UUID.
- Added dashboard navigation to the analytics route.
- Verified a real traced run with 12 traces, 69,240 total tokens, 295.87
  seconds of latency, zero retries, and zero errors.
- Verified frontend lint and production build successfully.
- Known usability limitation: research-run UUID entry is manual until the
  persistent history and run selector work planned for M27.

## Milestone 2 — Core DB models (users, workspaces, research_runs) + Alembic
migrations applied to Neon. Ruff config updated to exclude alembic/
(generated/boilerplate files shouldn't be hand-linted).

- Completed: Base, User, Workspace, ResearchRun models; Alembic wired to the
  async engine; migration generated and applied to Neon.
- Verified: tables exist in Neon, existing test still passes, ruff clean.
- Known issues: none.

## Milestone 7 — Research Agent: Tavily MCP search and source persistence

Implemented the Research Agent for one planned sub-question using the official
Tavily MCP server over stdio transport. Search results are parsed into
provider-neutral records and persisted through SourceRepository into Neon.

- Completed: Tavily MCP client, MCP registry, Research Agent node,
  SourceRepository integration, graph wiring, and source persistence.
- Verified: real `/research/start` completed successfully through Gemini
  planning, Tavily search, source persistence, and research-run completion.
- Verified: all 10 tests pass and Ruff is clean.
- Fixed: added bounded exponential backoff for transient Gemini 503/429/5xx
  failures.
- Known gap: `/research/start` workspace ownership enforcement remains a
  follow-up item; report retrieval itself is ownership-scoped.
- Known warnings: dependency deprecation warnings from passlib and the
  google-genai/Pydantic integration.

## Milestone 8 — Evidence Agent: structured evidence extraction and persistence

Implemented the Evidence Agent using Gemini structured output to extract
directly supported factual claims from persisted source content. Evidence is
linked to both the originating research run and source, then persisted in the
Neon `evidence` table.

- Completed: Evidence model, Alembic migration, EvidenceRepository, Gemini
  evidence extraction schema, Evidence Agent node, graph wiring, and evidence
  persistence in `start_research_run`.
- Fixed: flattened the evidence structured-output schema to avoid unsupported
  nested `$defs`/`$ref` handling in `google-genai==0.3.0`.
- Verified: real `/research/start` completed successfully and persisted 27
  evidence rows in Neon for the M8 run.
- Verified: 14 tests pass and Ruff is clean.
- Known warnings: dependency deprecation warning from passlib.

## Milestone 11 — Verification Agent: deterministic source reliability
scoring

Implemented the Verification Agent as a deterministic domain-service-backed
step between parallel research and evidence extraction. Each source receives
a transparent reliability score based on URL security, hostname presence,
title completeness, content length, and domain suffix.

- Completed: source reliability scoring service, Verification Agent node,
  verified-source graph state, source persistence of reliability scores, and
  unit/agent/database tests.
- Usage protection: verification uses no Gemini calls.
- Verified: one real M11 research run completed and persisted 8 source scores
  ranging from 0.65 to 0.90 in Neon.
- Verified: 25 tests pass and Ruff is clean.
- Known warnings: dependency deprecation warning from passlib.

## Milestone 12 — Reasoning Agent and Gemini-to-Groq provider migration

Implemented the Reasoning Agent to synthesize extracted evidence and verified
source metadata into structured conclusions with supporting and contradicting
source indexes. Migrated active LLM calls to Groq's
`openai/gpt-oss-120b` while preserving the existing client function
signatures and Pydantic return types.

- Completed: reasoning extraction, source-index normalization, Groq client,
  opt-in live Groq integration test, and full graph wiring.
- Fixed: Groq could emit concatenated string citation indexes such as
  `"0123456789"`; the client now normalizes them into valid integer indexes
  and rejects indexes that are not present in the source set.
- Verified: Ruff clean, 29 automated tests passed with one intentionally skipped
  live integration test, the live Groq integration test passed, and a real
  `/research/start` run completed successfully through Neon.
- Provider decision: Groq is active because Gemini's free-tier quota was not
  dependable for development. `gemini_client.py` and its spike remain as a
  documented fallback.
- Known warning: dependency deprecation warning from passlib.

## Milestone 10 — Parallel Research Agent: fan-out and fan-in

Implemented LangGraph fan-out/fan-in across all planned research
sub-questions. Each sub-question runs through an independent Research Agent
worker, and source results are merged before Evidence Agent execution.

- Completed: parallel research task state, LangGraph `Send` fan-out, source
  reducer for fan-in, globally unique source indexes, and mocked parallel
  research tests.
- Fixed: updated LangGraph `Send` imports to the non-deprecated
  `langgraph.types` location.
- Usage protection: automated tests mock Tavily and Gemini-dependent nodes;
  real search results were limited to two per sub-question for verification.
- Verified: one real M10 research run completed and produced a cited report
  using sources from multiple planned research paths.
- Verified: 21 tests pass and Ruff is clean.
- Known warnings: dependency deprecation warning from passlib.

## Milestone 9 — Report Agent: minimal cited Markdown report

Implemented the Report Agent using Gemini structured output to assemble
persisted evidence into a concise Markdown report with inline source
citations. Reports are persisted in the Neon `reports` table and exposed
through the research report endpoint with ownership enforcement.

- Completed: Report model, Alembic migration, ReportRepository, report
  generation schema, Report Agent node, graph wiring, report persistence, and
  `GET /api/v1/research/{id}/report`.
- Verified: one real end-to-end research run completed through planning,
  Tavily search, evidence extraction, report generation, persistence, and API
  retrieval.
- Verified: 19 tests pass and Ruff is clean.
- Known gap: `/research/start` workspace ownership enforcement remains a
  follow-up item; the new report endpoint is ownership-scoped.
- Known warnings: dependency deprecation warning from passlib.

## Milestone 5 — LangGraph skeleton: GraphState, Supervisor node, stub
agent, Postgres checkpointer (via psycopg, separate driver from the
SQLAlchemy/asyncpg app DB — see ARCHITECTURE.md). POST /research/start
creates a research_runs row and executes the graph end to end, verified
against real Neon. Fixed along the way: psycopg needs sslmode=require,
not asyncpg's ssl=require, in its connection string; AsyncIterator ->
AsyncGenerator return-type annotation for @asynccontextmanager.

- Completed: GraphState, Supervisor node, stub agent, graph builder, Postgres
  checkpointer setup, start_research_run use case, and POST /research/start.
- Files created: 8 app files + test_graph.py; edited main.py and
  requirements.txt.
- Verified: real research run against Neon returns status: completed;
  LangGraph checkpoint tables were created and used; all 7 tests pass; Ruff
  clean.
- Known gap: /research/start does not yet check workspace ownership; this
  remains a follow-up item.
- Bugs fixed: psycopg vs asyncpg SSL parameter naming; asynccontextmanager
  return-type annotation.

## Milestone 6 — Planning Agent (real): Gemini structured output
(gemini-3.5-flash, async client) generates sub-questions + strategy from
a research question; persisted to new research_plans table. Fixed a
significant bug found during verification: alembic autogenerate doesn't
know about LangGraph's self-managed checkpoint tables and generated DROP
statements for them, which then executed and deleted the checkpointer's
schema. Fixed by excluding checkpoint* tables from autogenerate via
include_object in alembic/env.py, and recreated the tables via
setup_checkpointer_tables().

- Completed: ResearchPlan model + migration, gemini_client.py (async
  structured output), planning_agent node (replaces stub),
  ResearchPlanRepository, and plan persistence in start_research_run.
- Files created/modified: 9 files total; deleted stub_agent.py and
  test_graph.py.
- Verified: real Gemini call produces a valid plan persisted correctly to
  Neon; all 7 tests pass; Ruff clean.
- Significant bug fixed: Alembic autogenerate silently dropping LangGraph's
  checkpoint tables; permanently guarded via include_object.

## Milestone 3 — JWT auth (register/login/me), password hashing (bcrypt),
UserRepository, register/login use cases, get_current_user dependency for
protecting future routes. Fixed: DB engine switched to NullPool (pooled
asyncpg connections were binding to whichever event loop created them,
breaking across loop boundaries — surfaced first in tests, would have hit
production too under enough concurrency). Ruff config: ignore B008
(FastAPI's Depends()-as-default is intentional, not a bug).

- Completed: security.py (hashing + JWT), UserRepository, register_user/login_user
  use cases, get_current_user dependency, /auth/register, /auth/login, and
  /auth/me endpoints.
- Files created: 8 app files + test_auth.py, plus edits to main.py, config.py,
  .env.example, requirements.txt, pyproject.toml, and session.py.
- Verified: register → token → /me works end to end against real Neon; all 3
  tests pass; Ruff clean.
- Known issues: none.
- Bugs fixed: email-validator missing dependency; NullPool architecture
  decision documented in DECISIONS.md.

## Milestone 4 — Workspace CRUD (create/list/get/delete), ownership checks
in the use-case layer (404 for both not-found and not-owned, to avoid
leaking existence of other users' workspaces). Fixed two latent bugs
surfaced by this milestone's DB writes: (1) Workspace.deleted_at and all
three ResearchRun timestamp columns were missing DateTime(timezone=True),
same class of bug as the DevOps Copilot project — fixed via migration;
(2) Neon's pooled (-pooler) connection string breaks prepared-statement
caching under schema changes — switched to the direct connection string.
Phase 1 (Foundation) complete.

- Completed: WorkspaceRepository, four use cases (create/list/get/delete),
  ownership-scoped routes, and full CRUD tests.
- Files created: 7 app files + test_workspaces.py; edited main.py.
- Bugs found and fixed: naive timestamp columns on Workspace/ResearchRun;
  Neon pooled-endpoint prepared-statement caching issue.
- Verified: all 6 tests pass, Ruff clean, and manual curl flow works against
  real Neon.
- Known issues: none.

## Milestone 13 — Fact Checking Agent

Implemented the Fact Checking Agent between reasoning and report generation.
Each reasoning conclusion is checked against extracted evidence and classified
as supported, contradicted, or uncertain.

- Completed: Fact Checking Agent, Groq structured-output extraction,
  contradiction detection, claim status persistence, and graph wiring.
- Updated: claims now persist fact-check status plus supporting and
  contradicting evidence IDs.
- Verified: Ruff clean, 32 tests passed, and a real `/research/start` run
  completed successfully through the full reasoning → fact checking → report
  pipeline.
- Known warning: dependency deprecation warning from passlib.

## Milestone 14 — Human Approval and checkpoint-based report approval

Added a human-in-the-loop approval gate after fact checking and before final
report generation. Research artifacts are persisted while the graph is paused,
and approval resumes the same LangGraph checkpoint before persisting the final
report.

- Completed: approval gate, ownership-scoped research-run repository,
  approval use case, resumable graph invocation, approval API endpoint, and
  shared artifact/report persistence.
- Verified: Ruff clean, 35 tests passed, and a real run transitioned from
  `awaiting_approval` to `completed` after approval; the final report was
  retrieved successfully.
- Known warning: dependency deprecation warning from passlib.

## Milestone 15 — Research Resume and crash recovery

Added checkpoint-based resume for paused or failed research runs. A resumable
run now continues from its latest LangGraph checkpoint instead of restarting
planning, research, evidence, reasoning, and fact checking from the beginning.

- Completed: resume use case, ownership-scoped resume endpoint,
  crash-recovery graph invocation, idempotent artifact persistence, and resume
  tests.
- Verified: Ruff clean, 39 tests passed, and a real run transitioned from
  `paused` to checkpoint resume, back to `awaiting_approval`, and finally to
  `completed` after approval.
- Known warning: dependency deprecation warning from passlib.

## Milestone 16 — Citation management, confidence scoring, and selective charts

Implemented deterministic claim-level confidence scoring, report-level
confidence aggregation, citation persistence linking reports to claims and
sources, and selective quantitative chart generation with PNG asset
persistence.

- Completed: confidence scoring domain service, claim confidence persistence,
  citation model/repository, Alembic migration, citation persistence, chart
  rendering, chart asset persistence, and positive chart-path tests.
- Verified: Alembic upgrade and `alembic check` pass; Ruff passes; 50 tests
  pass with 3 intentionally skipped integration tests; live Groq chart
  identification passes; and the real smoke run completed through approval,
  report retrieval, confidence persistence, and duplicate-free citation
  persistence.
- Known warning: dependency deprecation warning from passlib.

## Milestone 17 — LangSmith tracing

Added LangSmith tracing across the research execution path.

- Completed: root research-graph tracing, traced LangGraph node execution,
  supervisor and fan-out routing spans, Groq structured-generation spans,
  Gemini fallback tracing, and Tavily MCP/tool tracing.
- Added explicit LangSmith configuration for API key, project, endpoint, and
  opt-in tracing.
- Verified: Ruff clean, observability tests pass, full test suite passes, a
  real research run completed successfully, and the LangSmith project shows
  the expected graph, agent, LLM, and MCP trace hierarchy.
- Known warning: dependency deprecation warning from passlib.

## Milestone 18 — Evaluation Agent v1

Added automatic per-run evaluation for planning quality, search quality, and
source reliability.

- Completed: evaluation scoring service, Evaluation Agent, separate Groq
  evaluation prompt, evaluation model/repository, graph wiring after Report
  Agent, idempotent evaluation persistence, JSONB migration, and focused
  unit/agent/database/application tests.
- Resilience: evaluation failures are non-blocking for report delivery, and
  optional chart-identification failures degrade to no chart instead of
  aborting the research run.
- Verified: Ruff passes; 60 tests pass with 3 intentionally skipped
  integration tests; the real M18 smoke run completed after approval; the
  report was retrieved successfully; and Neon contains three evaluations for
  the run: planning quality `0.9000`, search quality `0.8500`, and source
  reliability `0.8500` across eight sources.
- Verified: checkpoint resume recovered the original run after the initial
  chart-identification failure.
- Known warning: dependency deprecation warning from passlib.

## Milestone 19 — Evaluation Agent v2

Expanded automatic research evaluation with report-quality dimensions.

- Completed: deterministic citation coverage, groundedness evaluation,
  hallucination detection, overall research-quality aggregation, separate
  Groq quality-judge structured output, and persisted evaluation details.
- Resilience: evaluation remains non-blocking for report delivery, and all
  M19 dimensions use the existing idempotent evaluation persistence path.
- Verified: Alembic reports no pending operations; Ruff passes; 67 tests pass
  with 3 intentionally skipped integration tests; and the real M19 smoke run
  completed after approval with seven persisted dimensions.
- Verified scores: planning quality `0.9000`, search quality `0.8700`, source
  reliability `0.8938`, citation coverage `1.0000`, groundedness `1.0000`,
  hallucination detection `1.0000`, and overall quality `0.9440`.
- Verified: LangSmith contains the M19 Evaluation Agent and Groq structured
  generation traces.
- Known warning: dependency deprecation warning from passlib.

## Milestone 20 — Evaluation Dashboard API

Added authenticated API access to persisted evaluation data.

- Completed: ownership-filtered per-run evaluation query, aggregate
  dimension summary query, application use cases, Pydantic response schemas,
  evaluation API router, and API integration tests.
- Added endpoints:
  - `GET /api/v1/research/{id}/evaluation`
  - `GET /api/v1/evaluation/summary`
- Security: users can access only evaluations belonging to their own
  research runs; unauthorized cross-user access returns `404`.
- Compatibility: aggregate scores are cast to `Numeric(5,4)` so API output
  matches persisted score precision.
- Verified: Alembic reports no new operations; Ruff passes; 70 tests pass
  with 3 intentionally skipped integration tests; and the live API smoke
  test returned all seven per-run and aggregate evaluation dimensions.
- Known warning: dependency deprecation warning from passlib.

## Milestone 21 — Observability Dashboard API

Added authenticated observability APIs backed by LangSmith trace data and the
`agent_traces` table.

- Added per-run trace summary endpoint:
  `GET /api/v1/research/{id}/trace`.
- Added aggregate observability endpoint:
  `GET /api/v1/observability/summary`.
- Added token usage, latency, retry, error, status, and estimated-cost
  aggregation.
- Added idempotent LangSmith trace materialization and ownership filtering.
- Added the `agent_traces` table and Alembic migrations.
- Verified: Alembic clean, Ruff clean, 73 tests passed, 3 intentionally
  skipped integration tests, and live API smoke tests returned HTTP 200 for
  both endpoints and HTTP 404 for unauthorized/nonexistent runs.
- Known warning: dependency deprecation warning from passlib.

## Milestone 22 — Next.js frontend scaffold

Added the initial frontend product shell under `frontend/`.

- Added Next.js App Router with TypeScript and Tailwind CSS.
- Added ESLint and the initial shadcn-style design system utilities.
- Added landing, login, registration, and dashboard routes.
- Added responsive layout and persisted light/dark theme switching.
- Kept authentication and research forms presentation-only until M23.
- Verified: `npm run lint` passes, `npm run build` passes, the development
  server starts successfully, and all four routes were manually verified in
  the browser.
