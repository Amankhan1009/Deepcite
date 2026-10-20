# Deepcite Engineering Documentation

Welcome to the internal engineering documentation and architecture specifications for Deepcite.

Deepcite is an evidence-grounded multi-agent research platform designed to transform complex research questions into structured, cited, and confidence-scored reports through a verifiable LangGraph pipeline.

---

## 📑 Documentation Index

| Document | Purpose |
| :--- | :--- |
| [Architecture](ARCHITECTURE.md) | Clean Architecture layering, domain boundaries, state machine, and LangGraph topology |
| [API Reference](API.md) | Complete OpenAPI/FastAPI endpoint specification, request/response models, and auth contracts |
| [Agents & Workflow](AGENTS.md) | Agent mesh specifications, prompts, node responsibilities, and developer guidelines |
| [Deployment & Infrastructure](DEPLOYMENT.md) | Production setup on Render, Vercel, Neon PostgreSQL, and Tavily MCP |
| [Database Schema](DATABASE.md) | Relational data model, checkpointing tables, migrations, and relationship diagrams |
| [Evaluation & Quality](EVALUATION.md) | Evaluation dimensions, deterministic citation scoring, and LLM-as-a-judge metrics |
| [Architecture Decisions](DECISIONS.md) | Architecture Decision Records (ADRs) detailing why specific technical choices were made |
| [Current State](CURRENT_STATE.md) | Snapshot of implemented features, live capabilities, and verified milestones |
| [Project Overview](PROJECT_OVERVIEW.md) | High-level product vision, user personas, problem statement, and scope boundaries |
| [Changelog](CHANGELOG.md) | Chronological release and milestone history from Phase 0 to Milestone 32 |
| [Roadmap & Milestones](MILESTONES.md) | Five-phase engineering roadmap and milestone breakdown |
| [Task Backlog](TODO.md) | Completed deliverables and future backlog items |

---

## 🚀 Live Environments

- **Web Application**: [https://deepcite.vercel.app](https://deepcite.vercel.app)
- **Backend API**: [https://deepcite-967b.onrender.com](https://deepcite-967b.onrender.com)
- **Interactive API Docs (Swagger UI)**: [https://deepcite-967b.onrender.com/docs](https://deepcite-967b.onrender.com/docs)
- **Database**: Serverless PostgreSQL via Neon
- **Observability**: Traces and latency telemetry via LangSmith

---

## 🛠️ Key Architectural Invariants

1. **Evidence Before Generation**: LLMs never produce ungrounded assertions; every factual claim must trace back to extracted evidence and verified sources.
2. **Deterministic Quality Controls**: Source reliability, fact-check classification, and citation coverage are calculated using deterministic mathematical rules, not subjective LLM vibes.
3. **Resumable State**: Every graph step is checkpointed in PostgreSQL. Runs can be paused for human approval or resumed seamlessly after failures.
4. **Clean Architecture Boundaries**: External frameworks (FastAPI, Next.js, LangGraph, Tavily MCP) are isolated adapters around the core domain and application services.
