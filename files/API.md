# API.md

Base: `/api/v1`. Auth: JWT bearer token on all routes except
register/login. All request/response bodies are Pydantic-validated.

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

## Workspaces
- `POST /workspaces`
- `GET /workspaces`
- `GET /workspaces/{id}`
- `DELETE /workspaces/{id}` (soft delete)

## Research
- `POST /research/start` — start a research run (workspace ID and question in)
- `GET /research/{id}` — ownership-protected status and creation timestamp
- `GET /research/{id}/stream` — SSE/WebSocket for live progress (Phase 4)
- `POST /research/{id}/approve` — resume a paused-for-approval run
- `POST /research/{id}/pause` — explicit user-triggered pause (if in scope)
- `POST /research/{id}/resume` — resume after crash/interruption
- `GET /workspaces/{id}/research` — history list

## Reports
- `GET /research/{id}/report` — ownership-protected report content,
  confidence, and citation details
- `POST /reports/{id}/feedback` — ownership-protected approve/reject/comment/
  rate feedback; at least one feedback value is required
- `GET /reports/{id}/export?format=markdown|pdf|docx`
  — ownership-protected downloadable report export. Supported formats are
  Markdown (`text/markdown`), PDF (`application/pdf`), and DOCX
  (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
  Exported documents include persisted citation references and safe local
  report assets when available.

Report feedback request fields:

```json
{
  "decision": "approved|rejected|null",
  "comment": "optional text up to 2000 characters",
  "rating": "optional integer from 1 to 5"
}
```

Research approval remains a separate action:
`POST /research/{id}/approve` resumes a run paused at `awaiting_approval`.

## Evaluation
- `GET /research/{id}/evaluation` — ownership-protected per-run scores
  including dimension, score, details, and creation time
- `GET /evaluation/summary` — aggregate scores grouped by dimension for the
  authenticated user's completed research runs, including average score and
  run count

## Observability
- `GET /research/{id}/trace` — ownership-protected per-run agent/tool/LLM
  trace summary, including token usage, latency, retries, errors, status,
  and estimated cost
- `GET /observability/summary` — ownership-scoped aggregate token usage,
  latency, retries, errors, and estimated cost for completed research runs

Trace records are materialized in the `agent_traces` table from LangSmith
data. Repeating a trace request is idempotent and does not create duplicate
LangSmith trace rows.

## Settings
- `GET /settings`, `PATCH /settings`

Full request/response schemas will be added here as each endpoint is
built (Phase 1 onward) rather than speculatively defined now.

M23 frontend integration uses the synchronous `POST /research/start` response
and `GET /research/{id}` for status verification. The stream endpoint remains
planned and is not implemented yet.

M24 frontend integration uses `GET /research/{id}/report` for the report page,
the existing approval endpoint for human approval, and
`POST /reports/{id}/feedback` for persisted report feedback.

M25 frontend integration uses the existing evaluation and observability
endpoints for aggregate and per-run dashboards. The current UI requires a
research-run UUID for per-run inspection; a selectable history-based flow is
deferred to M27.
