# Deepcite

<div align="center">

### 🔎 Evidence-Grounded Multi-Agent Research

**Deepcite transforms a research question into a structured, cited, confidence-scored report — using a multi-agent workflow with verification, fact-checking, human approval, and report-quality evaluation.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-1C3C3C?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<br/>

[🌐 **Live Web Application**](https://deepcite.vercel.app) · [⚡ **API & Swagger Docs**](https://deepcite-967b.onrender.com/docs) · [📖 **Engineering Documentation**](files/README.md)

</div>

---

## ✨ Why Deepcite?

Most AI research tools stop at **"generate an answer."**

Deepcite is designed around a different principle:

> **Research should be traceable, verifiable, and reviewable — not just generated.**

Instead of sending a question directly to an LLM, Deepcite coordinates specialized agents that plan the research, gather evidence, verify sources, reason over claims, fact-check conclusions, and finally produce a citation-backed report.

The result is a research workflow where you can follow **how the answer was produced, what evidence supports it, and how confident the system is in its conclusions.**

---

## 🚀 What Deepcite Does

```text
                         ┌──────────────────┐
                         │  Research Query  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Planning Agent   │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Parallel Research Agents │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │ Evidence Agent   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Verification     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Reasoning Agent  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Fact Checking    │
                         └────────┬─────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │   Human Approval    │
                       └──────────┬───────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Report Agent    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Evaluation Agent │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Cited Research Report   │
                    │ + Confidence + Quality  │
                    └──────────────────────────┘
```

---

## 🧠 Core Features

| Capability | What it provides |
|---|---|
| 🤖 Multi-Agent Orchestration | Specialized agents for planning, parallel research, evidence extraction, reasoning, verification, and fact-checking |
| ⏱️ Real-Time Agent Stepper | Live tracking through every stage (`planning` → `researching` → `verifying` → `reasoning` → `fact_checking` → `awaiting_approval` → `generating_report`) |
| 📋 Instant Research Plan | Research strategy and targeted sub-questions are persisted ~5s into execution and cleanly docked beneath the active stepper |
| 🔎 Evidence Gathering | Unstructured search results from Tavily MCP are converted into structured, traceable evidence |
| 🛡️ Source Verification & Badges | Sources are deterministically scored with intuitive badges (`Academic / Peer-Reviewed`, `Verified Web Source`) |
| 🧩 Claim Reasoning & Fact-Checking | Claims are synthesized and cross-checked against supporting and contradicting evidence |
| 👤 Human-in-the-Loop Approval | Research pauses at a LangGraph checkpoint before report generation, allowing human inspection and approval |
| 🔄 Resume-Safe Workflows | Interrupted or paused runs resume effortlessly from their exact checkpoint without re-running prior steps |
| 📚 Sequential Citation Grounding | Every report statement is cited with clean `[Source 1]..[Source N]` markers without gaps or broken references |
| 📊 Deterministic Confidence | Factual claims carry mathematical confidence scores (e.g. `86%`) based on source reliability and verification |
| 📝 Structured Report Synthesis | In-depth analytical reports with executive summaries, findings, risk analyses, and recommendations |
| 🧪 Automated Evaluation | Completed reports are evaluated across planning quality, search quality, citation coverage, and groundedness |
| 📤 Multi-Format Export | Download reports as formatted Markdown (`.md`), PDF (`.pdf`), or Microsoft Word (`.docx`) |
| 📈 End-to-End Observability | Traces, latencies, and token expenditures monitored via LangSmith integration |
| 🐳 Docker & CI/CD | Fully containerized with Docker Compose and automated testing via GitHub Actions |

---

## 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                     │
│       Dashboard · Research · Reports · Evaluation            │
└──────────────────────────────┬───────────────────────────────┘
                               │ REST API
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                         FastAPI API                          │
│                Authentication · Research · Reports           │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                       Application Layer                      │
│             Use Cases · DTOs · Workflow Operations           │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                         Domain Layer                         │
│        Scoring · Source Selection · Reliability · Rules      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                     │
│ LangGraph · LLMs · MCP · PostgreSQL · Evaluation · Export   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy Async ORM
- Alembic
- PostgreSQL
- LangGraph
- Groq
- Tavily MCP
- LangSmith
- Pytest
- Ruff

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- ESLint

### Infrastructure

- Docker
- Docker Compose
- PostgreSQL 16
- GitHub Actions

---

## 📁 Project Structure

```text
Deepcite/
├── backend/
│   ├── app/
│   │   ├── application/
│   │   ├── core/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── presentation/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── package-lock.json
├── files/
│   ├── AGENTS.md
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── CURRENT_STATE.md
│   ├── DATABASE.md
│   ├── DECISIONS.md
│   ├── DEPLOYMENT.md
│   ├── EVALUATION.md
│   ├── FULL_WORKFLOW_EXPLAINED.md
│   ├── MILESTONES.md
│   ├── PROJECT_OVERVIEW.md
│   ├── README.md
│   └── TODO.md
├── scripts/
├── .github/workflows/ci.yml
├── docker-compose.yml
└── README.md
```

---

## ⚡ Quick Start

### Docker Compose

From the project root:

```bash
docker compose up --build
```

Then open:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
Health:   http://localhost:8000/api/v1/health
```

Stop:

```bash
docker compose down
```

To also remove the local PostgreSQL volume:

```bash
docker compose down -v
```

> ⚠️ `down -v` deletes the local PostgreSQL Docker volume and its stored database data.

### Hosted Backend

The backend is deployed on Render:

- Backend URL: [https://deepcite-967b.onrender.com/docs](https://deepcite-967b.onrender.com)

> ⚠️ Because this uses Render's free tier, the service may be asleep. If requests fail, wake it up by visiting the URL above and wait a minute for it to start.

---

## 💻 Local Development Without Docker

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

---

## 🔐 Environment Variables

Backend:

```text
backend/.env
```

Use `backend/.env.example` as the template.

```env
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
GEMINI_API_KEY=
GROQ_API_KEY=
JWT_SECRET=change-me-to-a-long-random-string
TAVILY_API_KEY=
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=deepcite
```

Frontend:

```text
frontend/.env.local
```

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

**Never commit real `.env` files or API keys.**

---

## 🧪 Testing

### Backend

```bash
cd backend
venv/bin/ruff check .
venv/bin/python -m pytest -q
```

Run a specific test:

```bash
venv/bin/python -m pytest tests/path/to/test_file.py -v
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

---

## 🔄 CI

GitHub Actions configuration:

```text
.github/workflows/ci.yml
```

The workflow validates:

```text
Backend
├── Ruff
└── Pytest + PostgreSQL

Frontend
├── ESLint
└── Production build
```

---

## 📊 Research Workflow

```text
User Question
      │
      ▼
Planning Agent
      │
      ▼
Parallel Research
      │
      ▼
Evidence Extraction
      │
      ▼
Source Verification
      │
      ▼
Reasoning
      │
      ▼
Fact Checking
      │
      ▼
Human Approval
      │
      ▼
Report Generation
      │
      ▼
Report Evaluation
      │
      ▼
┌─────────────────────────────────┐
│ Final Research Report           │
│                                 │
│ • Executive Summary             │
│ • Methodology                   │
│ • Findings                      │
│ • Analysis & Synthesis          │
│ • Limitations & Risks           │
│ • Recommendations               │
│ • Conclusion                    │
│ • Inline Citations              │
│ • Confidence / Quality Metrics  │
└─────────────────────────────────┘
```

---

## 👤 Human-in-the-Loop

Deepcite does not assume that an LLM should make every decision autonomously.

Research can pause at a human approval gate:

```text
Research Complete
       │
       ▼
┌────────────────────┐
│    Human Review    │
│                    │
│  Approve / Resume  │
└─────────┬──────────┘
          │
          ▼
   Report Generation
```

---

## 📈 Report Quality

Deepcite evaluates generated reports using deterministic, project-specific quality signals including:

- Executive summary presence
- Required report sections
- Word-count targets
- Inline citation markers
- Citation coverage
- Groundedness
- Fact-check outcomes
- Source reliability
- Overall report quality

The resulting quality score is an **internal project metric**, not a universal benchmark.

---

## 📦 Report Exports

Generated reports can be exported as:

- Markdown
- PDF
- DOCX

The same persisted report and citation information is used across the export pipeline.

---

## 🔍 Observability

Deepcite includes observability capabilities for inspecting research runs and agent execution:

- LangSmith tracing
- Research run state
- Agent traces
- Evaluation results
- Research history
- Observability APIs

---

## 🗺️ Roadmap

Development is organized milestone-by-milestone.

Completed work includes:

- Core backend architecture
- Authentication and workspaces
- LangGraph research orchestration
- Parallel research
- Evidence extraction
- Verification and fact checking
- Human approval/resume workflows
- Citation and confidence persistence
- Report generation
- Report evaluation
- Frontend dashboards
- Observability
- Report exports
- Containerization
- CI

Current and upcoming work is tracked in:

```text
files/MILESTONES.md
files/CURRENT_STATE.md
files/TODO.md
```

---

## 📚 Documentation

Comprehensive architectural and engineering specifications are organized in the [`files/`](files/README.md) directory:

| Document | Purpose |
|---|---|
| [📘 **Full Workflow & Architecture Guide**](files/FULL_WORKFLOW_EXPLAINED.md) | **Exhaustive end-to-end walkthrough of the 10-stage pipeline, data flow, and interview guide** |
| [📖 **Documentation Portal**](files/README.md) | Central entry point and index to all technical documentation |
| [🏛️ **System Architecture**](files/ARCHITECTURE.md) | Clean Architecture layering, domain boundaries, and LangGraph topology |
| [⚡ **API Reference**](files/API.md) | OpenAPI / FastAPI route specifications, request/response models, and auth |
| [🤖 **Agent Specifications**](files/AGENTS.md) | Agent mesh responsibilities, system prompts, and contributor ground rules |
| [🚀 **Deployment & Production**](files/DEPLOYMENT.md) | Live setup on Vercel, Render, Neon PostgreSQL, and Tavily MCP |
| [🗄️ **Database Design**](files/DATABASE.md) | Relational database schema, checkpointing models, and Alembic migrations |
| [⚖️ **Evaluation & Quality**](files/EVALUATION.md) | Evaluation dimensions, deterministic citation scoring, and LLM judge design |
| [💡 **Architecture Decisions**](files/DECISIONS.md) | Architecture Decision Records (ADRs) explaining key technical choices |
| [📌 **Current State**](files/CURRENT_STATE.md) | Verified capabilities, live production features, and active milestones |
| [🎯 **Project Overview**](files/PROJECT_OVERVIEW.md) | Product vision, target personas, problem definition, and scope boundaries |
| [📜 **Changelog**](files/CHANGELOG.md) | Release notes and milestone progress history from Phase 0 to Milestone 32 |
| [🗺️ **Roadmap & Milestones**](files/MILESTONES.md) | Five-phase roadmap tracking all 32 development milestones |
| [📝 **Task Backlog**](files/TODO.md) | Completed deliverables and future backlog items |

---

## 🎯 Engineering Principles

**Evidence over generation**  
LLM output should be grounded in collected evidence.

**Specialized agents over one giant prompt**  
Different research stages have different responsibilities.

**Human control where decisions matter**  
The workflow can pause for human review instead of blindly continuing.

**Traceability**  
Research artifacts, evidence, citations, confidence, and evaluation results remain inspectable.

**Deterministic quality signals**  
Important quality checks should not rely exclusively on an LLM's subjective judgment.

**Production-oriented engineering**  
The project emphasizes clear boundaries, persistence, testing, observability, reproducibility, and deployment readiness.

---

## 👨‍💻 Built With

**FastAPI · LangGraph · PostgreSQL · Groq · Tavily MCP · LangSmith · Next.js · TypeScript · Docker · GitHub Actions**

---

<div align="center">

### Deepcite

**Research → Evidence → Verification → Reasoning → Fact Check → Human Review → Report**

Built as a production-style exploration of multi-agent AI research systems.

</div>
