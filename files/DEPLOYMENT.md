# DEPLOYMENT.md

Status: planned, not yet provisioned (Phase 5 / M28-30).

## Local dev
Docker Compose: `backend` (FastAPI), `frontend` (Next.js), plus Postgres
if not using Neon directly even locally (TBD — likely just point local
dev at a Neon dev branch to avoid schema drift between local Postgres and
Neon Postgres).

## CI (GitHub Actions)
On every push/PR: Ruff lint, Pytest (unit + integration + API + DB +
agent + MCP + evaluation suites), frontend build. On merge to main:
build + push Docker images, deploy.

## Production (provider TBD — see DECISIONS.md)
- Backend: containerized FastAPI, deployed to [pending decision]
- Frontend: Next.js, deployed to [pending decision — Vercel is the
  natural fit given the stack, but not yet confirmed]
- Database: Neon Postgres (production branch)
- Secrets: environment variables via host's secret manager, never
  committed; `.env.example` maintained in repo with no real values

## Rollout order
Backend + DB deploy first and are verified independently (health check +
smoke test of one real research run) before frontend deploy, matching
what worked well in the previous DevOps Copilot project.
