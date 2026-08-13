# Deepcite — Technology Stack Report

**Project:** Deepcite — Production-Grade AI Deep Research Platform
**Purpose of this document:** a complete record of every tool/technology
used in the project, why it was chosen, and how it's actually applied —
for portfolio reference, interview prep, and onboarding anyone new to
the codebase.

---

## 1. Backend Framework & Core Runtime

| Tool | Role |
|---|---|
| **Python 3.12** | Primary language |
| **FastAPI** | Web framework / API layer |
| **Uvicorn** | ASGI server that runs the FastAPI app |
| **Pydantic** | Data validation, request/response schemas, settings |

**Why Python:** the entire AI/agent ecosystem this project depends on —
LangGraph, the LLM SDKs, MCP — is Python-native. There's no serious
alternative for this category of project today.

**Why FastAPI:** it's async-native, which matters directly here because
every database call and every LLM call in this system is non-blocking
(`await`-based). FastAPI also validates incoming requests automatically
via Pydantic and generates interactive API docs from the code itself,
with no separate documentation step required.

**Uvicorn vs. FastAPI, in plain terms:** FastAPI defines *what* happens
when a request arrives; Uvicorn is the actual running process that
listens on a network port and hands requests to FastAPI.

**Pydantic, in plain terms:** a strict gatekeeper. Every request body
(`RegisterRequest`, `CreateWorkspaceRequest`, `StartResearchRequest`) is
validated against a defined shape before any application code touches
it — malformed input is rejected automatically. The same library also
validates environment configuration (`Settings` in `config.py`).

---

## 2. Database Layer

| Tool | Role |
|---|---|
| **Neon (Postgres)** | Hosted, serverless database |
| **SQLAlchemy (async) + asyncpg** | ORM and database driver |
| **Alembic** | Schema migration tool |

**Why Neon:** standard Postgres underneath (mature, reliable, supports
JSONB — used for `sub_questions`, evidence payloads) but serverless and
fully managed, so there's no server to provision or patch. A good fit
for a project that needs production-grade data behavior without
production-grade ops overhead.

**Why SQLAlchemy (async) + asyncpg:** SQLAlchemy lets database tables be
defined and queried as Python classes (`User`, `Workspace`,
`ResearchRun`, ...) instead of raw SQL strings. `asyncpg` is the
low-level driver actually speaking Postgres's wire protocol underneath
it. The async variant is required because FastAPI is async — a
synchronous DB call would stall the entire server on every query.

**Why Alembic:** it's version control for the database schema. Every
model change (a new column, a new table) becomes a generated,
reviewable, reversible migration script — the same discipline Git
applies to code, applied to schema.

**A configuration decision worth noting — `NullPool`:** the app is
configured so no database connections are held open between requests;
each request opens a fresh one. This wasn't a default left unconfigured
— it fixed a real bug (pooled connections binding to whichever event
loop created them, which broke across test runs) and separately matches
Neon's own guidance for serverless Postgres, which favors short-lived
connections over long-held pools.

---

## 3. Authentication & Security

| Tool | Role |
|---|---|
| **python-jose** | JWT (JSON Web Token) creation and verification |
| **passlib + bcrypt** | Password hashing |

**How it's used:** on register/login, `passlib`/`bcrypt` hash the
password before it's stored — the database never holds a plaintext
password, only a one-way hash. `python-jose` issues a signed JWT on
successful login, which the client sends back on every subsequent
request; `python-jose` verifies it to identify the current user.

---

## 4. Agent Orchestration

| Tool | Role |
|---|---|
| **LangGraph** | Multi-agent graph orchestration |
| **langgraph-checkpoint-postgres (via psycopg v3)** | Persistent, resumable agent state |

**Why LangGraph:** it's the core of the project's "agentic" behavior.
Rather than calling an LLM in an ad hoc loop, the research pipeline is
modeled as a graph of nodes (Supervisor → Planning → Research →
Evidence → ...), each reading and writing a shared state object, with
the graph itself handling routing between them.

**Why checkpointing matters here specifically:** it's what makes pausing
and resuming a research run possible — a first-class feature of this
project (human approval gates, crash recovery), not an afterthought.
Every step of the graph's state is persisted to Postgres as it runs,
keyed by a `thread_id` set to the research run's own ID. In plain terms:
it's autosave for a multi-step AI process — if a run is interrupted, or
needs a human decision before continuing, it resumes exactly where it
left off instead of restarting.

**Why a second, separate Postgres driver (`psycopg` v3) instead of
reusing `asyncpg`:** LangGraph's checkpointer manages its own schema and
transaction boundaries independently of the app's SQLAlchemy models.
Keeping the two systems on separate drivers/connections is a deliberate
architectural boundary, not duplication — it prevents two unrelated
systems from being coupled through a shared transaction.

---

## 5. LLM Providers

| Tool | Role |
|---|---|
| **Google Gemini (`google-genai` SDK)** | Original LLM provider (Planning Agent) |
| **Groq (`openai/gpt-oss-120b`)** | Current/migrated LLM provider |

**Why Gemini was chosen initially:** a spike (Milestone 1) verified it
could reliably return structured output (data conforming to a defined
Pydantic schema, not free-form text) and perform tool/function calling —
both required by the agent pipeline.

**Why the project migrated to Groq:** Gemini's free tier now requires
billing to be enabled even for light development use — in practice this
showed up as a hard cap of roughly 20 requests/day before hitting 429
quota errors, which made iterative development and testing impractical
without attaching billing. Groq offers a genuinely free tier (no card
required) with workable rate limits (30 requests/minute, roughly 1,000+
requests/day depending on model), running on custom inference hardware
(LPUs) that is also notably fast.

**Why `openai/gpt-oss-120b` specifically:** it's an open-weight
*reasoning* model (as opposed to a general-purpose chat model), which
better matches what the pipeline's agents actually need — multi-step
planning, evidence reasoning, and fact-checking all benefit more from a
model built for structured reasoning than one optimized for
conversational speed.

**In plain terms:** these are the system's "brains." Any time an agent
needs to think — break a question into sub-questions, extract facts from
a source, judge whether a claim is supported — that's a structured
request sent to one of these APIs.

---

## 6. External Tools & Search

| Tool | Role |
|---|---|
| **Tavily** | Web search provider |
| **MCP (Model Context Protocol)** | Standardized tool-calling interface |

**How it's used:** the Research Agent needs to search the web for each
sub-question in a research plan. Rather than calling Tavily's REST API
directly, the project integrates it via MCP — a real MCP client (the
official `mcp` Python SDK) communicates with the `tavily-mcp` server
over a subprocess (spawned via `npx`, using stdio transport).

**Why MCP instead of a direct API integration:** it mirrors the same
tool-integration pattern used in real production agent systems — a
standardized protocol between an agent and its tools, rather than a
bespoke one-off wrapper. It also means swapping search providers later
would only require changing the MCP server, not the agent's own code.

---

## 7. Testing & Code Quality

| Tool | Role |
|---|---|
| **pytest + pytest-asyncio** | Test runner |
| **httpx** | In-process API testing |
| **Ruff** | Linting |

**Why pytest-asyncio specifically:** nearly everything in this
application — routes, database calls, agent nodes — is defined with
`async def`. Plain pytest has no native way to run and await those
without this plugin.

**Why httpx for testing:** it lets tests send requests directly into the
FastAPI app in-process (via `ASGITransport`), without needing to start
an actual running server — faster and more self-contained.

**Why Ruff:** a linter and formatter that checks code style and flags
likely bugs (unused imports, etc.) on every milestone's verification
pass. It replaces the role of multiple older tools (flake8, black) in a
single, significantly faster tool (implemented in Rust).

---

## 8. Observability

| Tool | Role |
|---|---|
| **LangSmith** | Tracing and monitoring for LLM/agent calls |

**Why it's part of this project specifically:** observability was
scoped as a first-class feature from the project's initial planning
phase, not an afterthought — every LLM call, every LangGraph node
execution, and every tool call is traced, with latency, token usage, and
full input/output visible per run.

**In plain terms:** it's a flight recorder for the agents. When
something goes wrong several steps into a research run, instead of
guessing, the exact sequence of what each agent said and did is
visible and inspectable.

---

## 9. Development Tooling

| Tool | Role |
|---|---|
| **Git / GitHub** | Version control, remote repository |
| **Codex (VS Code extension)** | AI coding assistant used to implement planned changes |

---

## Summary — Request Flow Through the Stack

1. A request hits **FastAPI**, served by **Uvicorn**
2. **Pydantic** validates the request shape
3. **python-jose** verifies the user's JWT (if the route is protected)
4. The request triggers a **LangGraph** run
5. Each graph node calls out to **Groq** (reasoning) and/or **Tavily via
   MCP** (search) as needed
6. **LangGraph's checkpointer** (via `psycopg`) persists graph state to
   **Neon** after each step
7. The use case layer persists final results via **SQLAlchemy/asyncpg**
   to **Neon**
8. Every LLM/agent/tool call along the way is traced in **LangSmith**
9. **pytest**, **httpx**, and **Ruff** verify correctness and code
   quality at every milestone
