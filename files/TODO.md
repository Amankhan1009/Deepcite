# TODO.md

## Phase 1 complete
Authentication, database, workspace CRUD, and the technology-stack spike
are complete and verified.

## Phase 2 complete
Milestones 5, 6, and 7 are complete and verified against real Neon and live
external services.

Milestones 8 through 16 are complete and verified with live external
services, including parallel Tavily research, deterministic source
verification, evidence persistence, reasoning, cited report generation,
confidence scoring, citation persistence, selective chart generation, and
report retrieval from Neon. Groq is now the active LLM provider; Gemini is
retained as a fallback.

## Phase 3 started
Milestone 17 is complete and verified with a real LangSmith-traced research
run. The root graph, LangGraph nodes, Groq calls, and Tavily MCP calls are
visible in the configured LangSmith project.

Milestone 18 is complete and verified with deterministic tests, a real
approved research run, persisted evaluation rows, and checkpoint recovery
after an optional chart-generation failure.

Milestone 19 is complete and verified with citation coverage, groundedness,
hallucination detection, overall quality scoring, a real approved smoke run,
persisted evaluation rows, and LangSmith trace verification.

Milestone 20 is complete and verified with ownership-protected per-run and
aggregate evaluation APIs, real API smoke testing, four-decimal score
serialization, and cross-user access tests.

Milestone 21 is complete and verified with the ownership-protected trace API,
aggregate observability API, LangSmith trace materialization, token and
latency aggregation, retry and error reporting, Alembic validation, Ruff,
73 passing tests, and 3 intentionally skipped integration tests.

Milestone 22 is complete and verified with the Next.js App Router scaffold,
TypeScript, Tailwind CSS, ESLint, landing/login/registration/dashboard routes,
responsive layout, persisted dark mode, and successful frontend lint/build
checks.

Milestone 23 is complete and verified with backend-connected registration and
login, JWT persistence, workspace listing and creation, research submission,
ownership-protected research status retrieval, local-development CORS, a real
approved browser smoke run, 76 passing backend tests, and successful frontend
lint/build checks.

Milestone 24 is complete and verified with the dynamic report-review page,
report citations and confidence display, the existing approval workflow,
persisted ownership-protected report feedback, Alembic validation, Ruff,
79 passing backend tests, 3 intentionally skipped integration tests, and
successful frontend lint/build checks.

Milestone 25 is complete and verified with the frontend evaluation and
observability dashboard, aggregate evaluation dimensions, aggregate runtime
metrics, per-run evaluation and trace inspection, a real traced research run,
frontend lint/build checks, 12 displayed traces, and zero retries/errors.

Milestone 26 is complete and verified with ownership-protected Markdown, PDF,
and DOCX report exports, persisted report-asset inclusion, exported citation
references with source titles and URLs, Unicode-safe PDF rendering, focused
export tests, 85 passing backend tests, and 3 intentionally skipped
integration tests.

Milestone 27 is complete and verified with persisted user settings, the
ownership-scoped research history API, frontend history and settings routes,
the Analytics research-run selector, 89 passing backend tests, 3
intentionally skipped integration tests, and successful frontend lint/build
checks.

Milestone 29 is complete and verified with deeper Groq report-generation
instructions, report-quality scoring against a 1,500-word target, citation
marker display clarification, focused backend tests, and frontend lint.

Milestone 30 is complete and verified with Docker Compose local development for
PostgreSQL, the FastAPI backend, and the Next.js frontend. The backend container
runs Alembic migrations, initializes LangGraph checkpointer tables, supports
Tavily MCP via npx, and completed an end-to-end Docker research smoke run.

Milestone 31 is complete and verified with GitHub Actions backend lint/tests,
frontend lint/build, Docker image builds, and Docker Hub publishing after tests
pass.

## Next milestone
- [x] Complete Milestone 27 — Settings page, research history list/detail views
- [x] Complete Milestone 28 — Frontend resume workflow for paused/interrupted
      research runs
- [x] Complete Milestone 29 — Deeper report generation and report-quality
      evaluation
- [x] Complete Milestone 30 — Docker Compose for local development
- [x] Complete Milestone 31 — GitHub Actions CI: lint, test, build, Docker
      image publish
- [ ] Start Milestone 32 — Production deployment, secrets management, final
      security pass, portfolio README

## Future report-quality work
- [ ] Add an optional controlled expansion pass when a generated report still
      lands below the target word-count range.
