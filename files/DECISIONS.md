# DECISIONS.md

## Decided
- **Tech stack is frozen** as specified: Gemini, LangGraph, MCP, FastAPI,
  SQLAlchemy Async, Alembic, Neon Postgres, Pydantic, Next.js/React/
  TypeScript/Tailwind/shadcn/ui, Docker/Compose/GitHub Actions, LangSmith,
  Ruff, Pytest.
- **Clean Architecture** with presentation/application/domain/
  infrastructure layers; LangGraph nodes and MCP tools are thin adapters
  with no business logic.
- **Single-responsibility agents**, Supervisor-coordinated.
- **Evaluation and observability are built from v1**, not deferred.
- **Sequencing:** build a narrow but fully end-to-end research run first
  (Phase 1) before adding parallelism, the full agent mesh, evaluation UI,
  and frontend — to avoid the project stalling under its own scope.
- **v1 is single-LLM-provider (Gemini) and single-tenant-per-user** — no
  provider abstraction, no org/admin layer yet. Logged as Future
  Improvements below.
- **Gemini SDK: decided — direct `google-genai` SDK.** Milestone 1 spike
  confirmed clean structured-output parsing (Pydantic schema round-trip)
  and correct tool/function-calling behavior on `gemini-3.5-flash`. No
  LangChain wrapper needed.
- **LLM provider: Groq with `openai/gpt-oss-120b` is now the active
  provider.** This supersedes the original decision: “Gemini SDK: decided —
  direct `google-genai` SDK.” Gemini's free tier repeatedly exhausted its
  quota during development and required billing for dependable usage, while
  Groq provides a genuinely free tier without requiring a card. The Gemini
  client and spike remain in the repository as an explicit fallback.
- **DB connection pooling: NullPool, not SQLAlchemy's default pool.** Neon
  is serverless Postgres and recommends short-lived connections; its own
  pooler handles reuse server-side. This also sidesteps pooled asyncpg
  connections binding to a single event loop, which caused cross-test
  failures in M3 and would have been a latent production bug.
- **Neon connection string: use the direct endpoint, not the `-pooler`
  endpoint.** Neon's pooled connection string breaks asyncpg prepared-
  statement caching during schema changes, so the direct connection string
  is used with SQLAlchemy's `NullPool`.
- **LangGraph checkpointer uses psycopg (v3), the app DB uses asyncpg — two
  Postgres drivers, deliberately.** The checkpointer owns its own schema and
  transaction boundaries independent of our SQLAlchemy models; coupling them
  would tie two unrelated systems together for no benefit. Both connect to
  Neon's direct (non-pooled) endpoint.
- **Alembic must never autogenerate migrations for LangGraph's `checkpoint*`
  tables.** They are created and managed exclusively by
  `AsyncPostgresSaver.setup()`, not by our SQLAlchemy models. They are
  excluded via `include_object` in `alembic/env.py`; this must remain in
  place for every future migration or autogenerate may propose dropping the
  checkpointer schema.
- **MCP search provider (v1 minimum): Tavily**, wrapped as an MCP server
  rather than called via raw SDK, to keep the Research Agent decoupled
  from the concrete provider per ARCHITECTURE.md §4 (new MCP servers
  register in infrastructure/mcp/registry.py without touching agent code).
  Fetch/scrape MCP server is deferred — M7 ships search only, per the
  "minimum viable pair" note in DECISIONS.md; fetch can be added later
  without changing the Research Agent's interface.
- **Report visualization: selective generated charts only.** The Report Agent
  may request a chart only when structured reasoning/fact-checking output
  contains genuinely chartable quantitative data; reports without such data
  receive zero charts. Gemini decides what is chartable, while a pure
  infrastructure renderer handles PNG creation. Local asset storage is
  development-only; production object storage is deferred.
- **Original topic illustrations are deferred to M26.** If visual generation
  is added, it will create new topic-relevant images only when they improve a
  report, store them as report assets, and never copy images from source pages.

## Open — remaining project decisions
1. **Hosting for production backend/frontend** — no provider chosen yet
   (previous project used Render + Streamlit Cloud; this one needs a
   Next.js-capable host, e.g. Vercel for frontend + Render/Fly.io for
   backend — your call).
2. **Checkpointing mechanism** — proposal is LangGraph's built-in Postgres
   checkpointer (least custom code, fits Neon). Confirm or override.

## Future Improvements (explicitly deferred, not forgotten)
- Multi-LLM-provider abstraction (Gemini + others)
- Full RBAC / multi-tenant admin dashboard
- Real-time collaborative report editing
- Additional MCP servers beyond the v1 minimum
