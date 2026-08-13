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
| 🤖 Multi-Agent Research | Specialized agents for planning, research, evidence, reasoning, verification, and fact-checking |
| 🔎 Evidence Gathering | Research results are converted into structured evidence |
| 🛡️ Source Verification | Sources are checked and reliability is incorporated into the workflow |
| 🧩 Claim Reasoning | Evidence is synthesized into supported claims and conclusions |
| 👤 Human Approval | Research can pause for human review before report generation |
| 🔄 Resume-Safe Workflow | Approved or interrupted workflows can resume through LangGraph state/checkpointing |
| 📚 Citation Grounding | Reports contain inline source references and persisted citation metadata |
| 📊 Confidence Scoring | Research outputs carry project-specific confidence information |
| 📝 Report Generation | Structured Markdown reports with executive summary and analytical sections |
| 🧪 Report Evaluation | Generated reports are evaluated for quality and groundedness |
| 📤 Export | Reports can be exported as Markdown, PDF, and DOCX |
| 📈 Observability | Research and agent activity can be inspected through observability features |
| 🐳 Containerized Development | Backend, frontend, and PostgreSQL can run through Docker Compose |
| ⚙️ CI | GitHub Actions validates backend and frontend changes |

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
│   ├── MILESTONES.md
│   ├── PROJECT_OVERVIEW.md
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

| Document | Purpose |
|---|---|
| `files/ARCHITECTURE.md` | System architecture |
| `files/API.md` | API documentation |
| `files/DATABASE.md` | Database design |
| `files/DECISIONS.md` | Architecture decisions |
| `files/EVALUATION.md` | Evaluation design |
| `files/MILESTONES.md` | Development roadmap |
| `files/CURRENT_STATE.md` | Current implementation state |
| `files/TODO.md` | Remaining work |
| `files/DEPLOYMENT.md` | Deployment information |

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
