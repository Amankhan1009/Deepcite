# AGENTS.md — Instructions for Working On This Repo

## Purpose
This file is the entry point for any AI assistant (or human) picking up this
project. **Assume zero memory of prior conversations.** This repo's docs are
the only source of truth.

## Before touching anything
Read, in this order:
1. `docs/CURRENT_STATE.md` — what exists right now
2. `docs/MILESTONES.md` — what's done, what's next
3. `docs/DECISIONS.md` — why things are the way they are (don't relitigate)
4. `docs/ARCHITECTURE.md` — system design (frozen unless explicitly approved)

Then continue from the next incomplete milestone in `docs/MILESTONES.md`.

## Project identity
Production-Grade AI Deep Research Platform. Multi-agent research system
(planning → parallel research → verification → reasoning → fact-checking →
report), with evaluation and observability as first-class features, not
afterthoughts. See `docs/PROJECT_OVERVIEW.md`.

## Ground rules
- **Architecture is frozen** once approved (see ARCHITECTURE.md). Do not
  redesign, swap frameworks, or rename folders/APIs/tables without explicit
  approval. Exceptions: security issues, deprecated dependencies, critical
  bugs. Otherwise log the idea under "Future Improvements" in DECISIONS.md.
- **Work milestone-by-milestone.** Never generate the whole project at once.
  Explain why/how/design before code. Generate only the current milestone.
  List files to create/modify and exact commands to run. Stop. Wait for
  terminal output before continuing.
- **Every agent has ONE responsibility.** No giant all-purpose agent nodes.
- **No business logic in API routes, LangGraph nodes, or MCP tool
  functions** — those are thin adapters over the Application/Domain layers
  (Clean Architecture — see ARCHITECTURE.md).
- **Testing is not optional and not deferred.** Every milestone that adds
  behavior adds tests for that behavior in the same milestone.
- **LangSmith tracing and evaluation are mandatory**, not add-ons, wherever
  an LLM call or agent graph runs.
- **Update docs every milestone** — CURRENT_STATE.md, CHANGELOG.md,
  MILESTONES.md, TODO.md always; AGENTS.md/DATABASE.md/API.md/
  ARCHITECTURE.md/DECISIONS.md/EVALUATION.md only when something in them
  actually changed.

## Definition of Done (per milestone)
- [ ] Feature works, verified against a real run (not just unit tests)
- [ ] Tests pass
- [ ] Docs updated (see above)
- [ ] LangSmith tracing verified (if the milestone touches an LLM/agent call)
- [ ] Evaluation updated (if the milestone touches research quality)
- [ ] Handoff summary produced (Completed Work / Files Created / Files
      Modified / Docs Updated / Tests Executed / Known Issues / Next
      Milestone / Ready To Continue)

## Tech stack (frozen — see DECISIONS.md for rationale)
Gemini API · LangGraph · MCP · FastAPI · SQLAlchemy Async · Alembic ·
Neon PostgreSQL · Pydantic · Next.js/React/TypeScript/Tailwind/shadcn/ui ·
Docker/Docker Compose/GitHub Actions · LangSmith · Ruff · Pytest
