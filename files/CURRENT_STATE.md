# CURRENT_STATE.md

Last updated: Milestone 30 — Docker Compose local development complete

## Status
Phase 2 (Agent mesh), Phase 3 (Quality layer), Phase 4 (Product layer), and
Milestones 28-30 in Phase 5 are complete. The backend scaffold, core database
models, JWT authentication, workspace CRUD, LangGraph skeleton, and Alembic
migration are in place, with the migration applied to Neon.

## What exists
- This documentation set.
- Backend scaffold with the core database layer.
- Database schema (users, workspaces, research_runs) migrated to Neon via
  Alembic.
- JWT auth (register/login/me), password hashing, and get_current_user
  dependency for protected routes.
- Workspace CRUD (create/list/get/delete, soft-deleted, scoped to owner).
- LangGraph skeleton (Supervisor routing, Postgres-backed checkpointing via
  psycopg, stub agent proving end-to-end wiring), and POST /research/start.
- Planning Agent (real, Groq structured output using
  `openai/gpt-oss-120b`) generates and persists research plans. The original
  Gemini client remains available as a fallback.
- Tavily MCP search client using stdio transport.
- Research Agent executes one planned sub-question and returns raw sources.
- SourceRepository persists Tavily results to the sources table.
- Real POST /research/start flow completes through Groq planning, Tavily
  search, source persistence, and research-run completion.
- Evidence Agent extracts structured claims from source content.
- EvidenceRepository persists evidence linked to research runs and sources.
- Real M8 research run verified 27 evidence rows persisted in Neon.
- Report Agent assembles evidence into a cited Markdown research report.
- Reports persist in Neon and are available through the research report API.
- Real M9 research run verified report generation and retrieval end to end.
- Parallel Research Agent fans out across planned sub-questions and merges
  source results before Evidence Agent execution.
- Real M10 research run verified parallel research and multi-source report
  generation end to end.
- Verification Agent calculates deterministic reliability scores for sources.
- Source reliability scores persist in the `sources` table.
- Real M11 research run verified 8 persisted sources with scores from 0.65 to
  0.90.
- Reasoning Agent synthesizes evidence and verified sources into structured
  conclusions with normalized source indexes.
- Groq structured-output client is active for planning, evidence, reasoning,
  and report generation; Gemini remains as a documented fallback.
- Real M12 research run completed end to end through the Groq provider and
  persisted successfully in Neon.
- Fact Checking Agent compares reasoning conclusions against extracted
  evidence and classifies claims as supported, contradicted, or uncertain.
- Fact-check results persist through the existing claims table with linked
  supporting and contradicting evidence IDs.
- The graph now executes reasoning → fact checking → report generation.
- Real M13 research run completed successfully through Groq, Tavily, Neon,
  reasoning, fact checking, and report generation.
- Human Approval gate pauses the graph after fact checking and before report
  generation using the persisted LangGraph checkpoint.
- Ownership-protected approval endpoint resumes the same research thread and
  completes report generation only after explicit approval.
- Real M14 run verified `awaiting_approval` → approval → `completed`, with the
  final report retrieved successfully from Neon.
- Crash recovery resumes paused or failed research runs from their latest
  LangGraph checkpoint using the same research-run thread.
- Resume persistence is idempotent and avoids duplicate plans, sources,
  evidence, claims, and reports after repeated recovery attempts.
- Real M15 run verified `paused` → checkpoint resume → `awaiting_approval` →
  approval → `completed`.
- Claim-level confidence scores are calculated deterministically from
  fact-check status and source reliability.
- Reports persist an overall confidence score calculated from claim scores.
- Citation rows link reports, claims, and sources through inline markers.
- Selective quantitative chart generation is verified through Groq,
  report-agent, PNG rendering, and report asset persistence.
- Real M16 smoke run verified research completion, report retrieval,
  confidence persistence, citation persistence, and duplicate-free citations.
- LangSmith tracing covers the root research graph, every graph node,
  supervisor routing, fan-out routing, Groq structured-generation calls, and
  Tavily MCP search calls.
- Real M17 smoke run verified a completed research flow and confirmed the
  expected LangSmith project and trace hierarchy.
- Evaluation Agent v1 runs after report generation and evaluates planning
  quality and search quality with a separate Groq judge prompt.
- Source reliability evaluation is calculated deterministically from the
  Verification Agent's persisted source scores.
- Evaluation failures are non-blocking for report delivery and are recorded
  in graph state for operational visibility.
- Evaluation rows are persisted idempotently per research run and dimension
  in the `evaluations` table, with JSONB rationale/details.
- Alembic migration for the evaluations table and JSONB details column is
  applied to Neon and `alembic check` reports no pending operations.
- Real M18 smoke run completed after approval, generated a report, and
  persisted planning quality `0.9000`, search quality `0.8500`, and source
  reliability `0.8500` evaluations for eight sources.
- M18 verification completed with Ruff passing, 60 tests passing, 3
  intentionally skipped integration tests, and successful checkpoint resume
  after the optional chart-identification failure.
- Evaluation Agent v2 calculates deterministic citation coverage from the
  generated report and reasoning claims.
- Groundedness and hallucination detection use a separate evaluation-specific
  Groq judge prompt comparing the report with evidence, reasoning, and
  fact-check results.
- Overall research quality is calculated deterministically from all available
  evaluation dimensions and persisted as the `overall` dimension.
- Real M19 smoke run completed after approval, generated a cited report, and
  persisted seven evaluation rows: planning quality `0.9000`, search quality
  `0.8700`, source reliability `0.8938`, citation coverage `1.0000`,
  groundedness `1.0000`, hallucination detection `1.0000`, and overall
  quality `0.9440`.
- M19 verification completed with Alembic clean, Ruff passing, 67 tests
  passing, 3 intentionally skipped integration tests, and LangSmith traces
  verified for the Evaluation Agent and structured-generation calls.
- M20 exposes ownership-protected per-run evaluation data through
  `GET /api/v1/research/{id}/evaluation`.
- M20 exposes ownership-scoped aggregate evaluation data through
  `GET /api/v1/evaluation/summary`, grouped by dimension with average scores
  and run counts.
- Aggregate API scores are normalized to four decimal places to match the
  persisted evaluation precision.
- Real M20 API smoke verification returned all seven per-run dimensions and
  all seven aggregate dimensions for the completed M19 research run.
- M20 verification completed with Alembic clean, Ruff passing, 70 tests
  passing, 3 intentionally skipped integration tests, and cross-user
  ownership tests passing.
- M21 adds ownership-protected per-run LangSmith trace summaries through
  `GET /api/v1/research/{id}/trace`.
- M21 adds aggregate observability metrics through
  `GET /api/v1/observability/summary`.
- LangSmith trace data is materialized idempotently in the `agent_traces`
  table, including token usage, latency, retry count, status, errors, and
  estimated cost.
- Real M21 smoke testing returned 12 trace rows, 89,170 total tokens,
  444,367 milliseconds of latency, zero retries, zero errors, and HTTP 200
  responses for both observability endpoints.
- M21 verification completed with Alembic clean, Ruff passing, 73 tests
  passing, and 3 intentionally skipped integration tests.
- M22 adds the Next.js App Router frontend scaffold under `frontend/` with
  TypeScript, Tailwind CSS, ESLint, and the initial shadcn-style design
  system.
- M22 adds landing, login, registration, and dashboard routes with a
  responsive layout and persisted light/dark theme toggle.
- M22 frontend verification completed with `npm run lint`,
  `npm run build`, a running Next.js development server, and manual browser
  verification of all four routes.
- M23 connects the Next.js frontend to the backend API through a shared
  authenticated fetch client and browser-stored JWT access token.
- M23 login and registration submit to the real backend auth endpoints and
  redirect authenticated users to the dashboard.
- M23 dashboard loads and creates ownership-scoped workspaces, submits
  research questions, and displays the current research-run status.
- M23 adds an ownership-protected `GET /api/v1/research/{id}` status endpoint
  for frontend status verification.
- M23 adds local-development CORS configuration for the frontend origins
  `http://localhost:3000` and `http://127.0.0.1:3000`.
- Real M23 smoke testing completed registration, workspace creation,
  research submission, approval through the authenticated browser session,
  and status verification with `status: completed`.
- M23 verification completed with Ruff passing, 76 backend tests passing,
  3 intentionally skipped integration tests, frontend lint passing, and a
  successful Next.js production build.
- M24 adds the dynamic frontend report-review route at
  `/research/[id]`.
- M24 enriches report responses with citation details, claim confidence,
  fact-check status, source URLs, and source reliability scores.
- M24 adds the `report_feedback` table and ownership-protected feedback API
  for report decisions, comments, and ratings.
- M24 reuses the existing approval endpoint from the report-review page to
  resume runs paused at `awaiting_approval`.
- Real M24 browser verification completed approval, report rendering,
  confidence and citation display, and feedback submission with HTTP 201.
- M24 verification completed with Alembic clean, Ruff passing, 79 backend
  tests passing, 3 intentionally skipped integration tests, and frontend
  lint/build passing without warnings.
- M25 adds the frontend `/analytics` route for aggregate evaluation and
  observability dashboards.
- M25 displays evaluation dimensions, average scores, run counts, token
  usage, latency, retries, errors, and estimated cost.
- M25 supports per-run evaluation and trace inspection using the existing
  ownership-protected backend endpoints.
- Real M25 browser verification displayed two research runs, 12 agent
  traces, 69,240 total tokens, 295.87 seconds of latency, zero retries, and
  zero errors.
- M25 verification completed with frontend lint passing without warnings,
  a successful Next.js production build, and manual verification of
  aggregate and per-run analytics.
- M26 adds ownership-protected report export through
  `GET /api/v1/reports/{id}/export?format=markdown|pdf|docx`.
- M26 exports the persisted Markdown report to Markdown, PDF, and DOCX
  formats, including safe local report assets and a References section with
  source titles and URLs from persisted citation records.
- M26 PDF rendering normalizes unsupported Unicode punctuation and avoids
  duplicate executive summaries in exported documents.
- M26 verification completed with Ruff passing, 85 backend tests passing,
  3 intentionally skipped integration tests, focused export tests passing,
  and manual Markdown/PDF/DOCX download verification.
- M27 adds persisted user settings through the `user_settings` table and
  ownership-protected `GET/PATCH /api/v1/settings` endpoints.
- M27 adds ownership-scoped research history through
  `GET /api/v1/workspaces/{workspace_id}/research`.
- M27 adds frontend `/history` and `/settings` routes.
- M27 replaces manual research-run UUID entry in `/analytics` with a
  selectable list populated from the user's research history.
- M27 verification completed with the user-settings migration applied,
  Alembic clean, Ruff passing, 89 backend tests passing, 3 intentionally
  skipped integration tests, frontend lint/build passing, and manual browser
  verification of dashboard, history, settings, analytics, and report routes.
- M28 adds visible Resume actions for paused and failed research runs from
  both the research history page and the research detail page.
- M28 reuses the existing ownership-protected
  `POST /api/v1/research/{id}/resume` checkpoint-resume endpoint and updates
  the frontend status after the resume response.
- M28 preserves the existing approval workflow when a resumed run reaches
  `awaiting_approval`.
- Real M28 browser verification completed resume, approval, report retrieval,
  and Markdown/PDF export successfully.
- M28 verification completed with 89 backend tests passing, 3 intentionally
  skipped integration tests, frontend lint passing, and a successful Next.js
  production build.
- M29 improves Groq report generation by requesting deeper evidence-grounded
  reports targeting 1,450-1,500 total words while keeping bounded report inputs
  and a conservative 3,200 completion-token cap for Groq's 8,000 TPM limit.
- M29 report-quality evaluation tracks executive summary presence, required
  report sections, word count against a 1,500-word target, and inline citation
  marker count.
- M29 clarifies frontend report-quality wording by distinguishing inline
  citation markers from persisted evidence links.
- M29 verification completed with focused Groq report-payload and report-quality
  backend tests passing, plus frontend lint passing.
- M30 adds Docker Compose local development for PostgreSQL, backend, and
  frontend services.
- M30 backend container runs Alembic migrations, initializes LangGraph
  checkpointer tables, serves FastAPI on port 8000, and includes Node/npm/npx
  for the Tavily MCP stdio server.
- M30 frontend container serves the Next.js app on port 3000 and points browser
  API calls at the local Docker backend.
- M30 local smoke verification completed registration/login, workspace access,
  research start, Tavily-backed research, report generation, and report review
  through the Docker stack.

## What doesn't exist yet
- True streamed/SSE progress updates; the current M23 UI shows an in-flight
  loading state and the final status returned by the synchronous backend
  request. A durable live-progress transport remains a later enhancement.
- Fetch/scrape MCP integration
- Original topic-related illustration generation; report exports only include
  already-persisted safe local assets. New illustration generation remains a
  future enhancement and must use newly generated visuals rather than copied
  source-page images.
- Optional report expansion pass for generated reports that still land below
  the target word-count range.

## Next milestone
Milestone 31 — GitHub Actions CI: lint (Ruff), test (Pytest), build.
