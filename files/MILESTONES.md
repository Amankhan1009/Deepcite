# MILESTONES.md

Legend: ☐ not started · ▶ in progress · ✓ done

## Phase 1 — Foundation (auth, DB, one straight-line research run)
✓ M1 — Repo scaffolding, Neon Postgres connection, health check, Gemini
       structured-output spike (confirm tool-calling/structured output
       parity before committing further)
✓ M2 — Core DB models (users, workspaces, research_runs) + Alembic
       migration
✓ M3 — JWT auth (register/login/me)
✓ M4 — Workspace CRUD (create/list/get/delete workspace)
✓ M5 — LangGraph skeleton: shared state schema, Postgres checkpointer
       wired up, Supervisor node, one stub agent, /research/start
       endpoint that runs it end to end
✓ M6 — Planning Agent (real): question → structured research plan
✓ M7 — Research Agent (real, single sub-question, one search tool via
       MCP): produces raw source results
✓ M8 — Evidence Agent: extracts structured claims/evidence from sources
✓ M9 — Report Agent (minimal): assembles a plain cited report from
       evidence — first fully end-to-end, if narrow, research run
 
## Phase 2 — Agent mesh (parallelism, verification, resume, approval)
✓ M10 — Parallel Research Agent: fan-out across all sub-questions from
        the plan, fan-in to Evidence Agent
✓ M11 — Verification Agent: source reliability scoring
✓ M12 — Reasoning Agent: synthesizes evidence + verification into
        conclusions
✓ M13 — Fact Checking Agent: cross-checks claims, flags contradictions
✓ M14 — Human Approval: graph pauses before final report, persists
        checkpoint, /research/{id}/approve resumes it
✓ M15 — Research Resume: resume any paused/interrupted run from its last
        checkpoint (crash recovery, not just approval gate)
✓ M16 — Citation management, confidence scoring, and selective chart
        generation wired into Report Agent output

## Phase 3 — Quality layer (evaluation + observability)
✓ M17 — LangSmith tracing wired through every node/tool/MCP/LLM call
        (retroactively verified across M1-M16 agents)
✓ M18 — Evaluation Agent v1: planning quality, search quality, source
        reliability scoring, persisted per run
✓ M19 — Evaluation Agent v2: citation coverage, groundedness,
        hallucination detection, overall research quality score
✓ M20 — Evaluation Dashboard API (aggregate + per-run evaluation data)
✓ M21 — Observability Dashboard API (per-run trace summary: token usage,
        latency, retries, errors, cost)

## Phase 4 — Product layer (frontend + exports)
✓ M22 — Next.js scaffold: auth pages, dashboard shell, dark mode, design
        system (shadcn/ui)
✓ M23 — Workspace + research submission UI, authenticated status view
✓ M24 — Report view: citations, confidence scores, approve/reject/
        comment/rate UI wired to backend
✓ M25 — Evaluation + Observability dashboards (frontend)
✓ M26 — Markdown/PDF/DOCX export with persisted report assets and citation
        references
✓ M27 — Settings page, research history list/detail views

## Phase 5 — Product completion and operations
✓ M28 — Frontend resume workflow for paused/interrupted research runs:
        Resume action from history and research detail, status refresh, and
        protection against invalid or completed-run resume attempts
✓ M29 — Deeper report generation and report-quality evaluation:
        methodology, evidence synthesis, contradictions, limitations, risks,
        recommendations, report-depth metrics, and deterministic evaluation
✓ M30 — Docker Compose (backend + Postgres + frontend) for local dev
✓ M31 — GitHub Actions CI: lint (Ruff), test (Pytest), build
☐ M32 — Production deployment (backend + frontend), secrets management,
        final security pass (RBAC field enforcement, input validation
        audit, safe-logging audit), portfolio README

Total: 32 milestones. Testing is added within each milestone's own scope,
not deferred to a separate milestone.
