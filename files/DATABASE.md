# DATABASE.md

Engine: Neon PostgreSQL. ORM: SQLAlchemy 2.0 async. Migrations: Alembic.
Conventions: UUID primary keys, `created_at`/`updated_at` timestamps on
every table, soft delete only where it's clearly useful (workspaces,
research_runs — not on append-only tables like evaluations/traces).

## Core tables (v1 — Phase 1-3 scope)

**users**
id, email (unique), hashed_password, role (enum: user/admin — field exists
now, enforcement logic deferred), created_at, updated_at

**workspaces**
id, user_id (FK), name, description, created_at, updated_at, deleted_at

**research_runs**
id, workspace_id (FK), user_id (FK), question (text), status (enum:
planning/researching/verifying/reasoning/fact_checking/awaiting_approval/
generating_report/completed/failed/paused), langgraph_checkpoint_id
(pointer into LangGraph's checkpoint store), started_at, completed_at,
created_at, updated_at, deleted_at

**research_plans**
id, research_run_id (FK), sub_questions (jsonb), strategy (jsonb),
created_at

**sources**
id, research_run_id (FK), url, title, fetched_at, reliability_score
(nullable — filled by Verification Agent), raw_content_ref, created_at

**evidence**
id, research_run_id (FK), source_id (FK), claim_text, extracted_at,
created_at

**claims**
id, research_run_id (FK), text, supporting_evidence_ids (jsonb array of
evidence.id), contradicting_evidence_ids (jsonb), fact_check_status
(enum: unverified/supported/contradicted/uncertain), confidence_score,
created_at

**reports**
id, research_run_id (FK, unique), content_markdown, executive_summary,
overall_confidence_score, created_at, updated_at

**report_assets**
id, report_id (FK), asset_type (chart now; original illustration deferred to
M26), file_path or storage reference, caption, created_at

**citations**
id, report_id (FK), claim_id (FK), source_id (FK), inline_marker,
created_at. Citation persistence deduplicates each report/claim/source
relationship.

**report_feedback**
id, report_id (FK), user_id (FK), decision (enum: approved/rejected),
comment (text, nullable), rating (int, nullable), created_at

**evaluations**
id, research_run_id (FK), dimension (enum: planning_quality/
search_quality/source_reliability/citation_coverage/groundedness/
report_quality/hallucination_detection/confidence_score/overall), score
(numeric), details (jsonb), created_at

**agent_traces**
id, research_run_id (FK), agent_name, langsmith_run_id, tool_calls (jsonb),
token_usage (jsonb), latency_ms, status, error (nullable), created_at

Indexes: FK columns everywhere they're queried by (workspace_id,
research_run_id, user_id), plus `research_runs.status` and
`evaluations.dimension` for dashboard queries.

## Phase 4 additions
- `report_feedback` is an append-only feedback-event table. Each submission
  records the authenticated user, report, optional decision, optional
  comment, and optional 1–5 rating.
- Report feedback is ownership-protected through the report's research run;
  users cannot submit feedback for another user's report.
- The M24 Alembic migration is `a7b8c9d0e1f2_add_report_feedback.py`.

## Notes
- `research_runs.langgraph_checkpoint_id` is the bridge between the
  relational DB and LangGraph's own checkpoint storage — enables Resume
  and Human Approval without duplicating graph state in our own tables.
- Schema will grow in Phase 4 (exports don't need new tables — reports
  are rendered on demand) — no changes anticipated there.
- Never manually edit production schema; all changes go through Alembic
  migrations, reviewed in DECISIONS.md if they're non-trivial.
