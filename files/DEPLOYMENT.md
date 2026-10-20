# DEPLOYMENT.md — Production & Deployment Specification

Status: **Live in Production** (Milestone 32 Complete).

---

## 🌐 Production Environments

| Layer | Service / Host | Production URL |
| :--- | :--- | :--- |
| **Frontend** | Vercel (Edge & Node.js Runtime) | [https://deepcite.vercel.app](https://deepcite.vercel.app) |
| **Backend API** | Render (Web Service) | [https://deepcite-967b.onrender.com](https://deepcite-967b.onrender.com) |
| **API Documentation** | Swagger / OpenAPI | [https://deepcite-967b.onrender.com/docs](https://deepcite-967b.onrender.com/docs) |
| **Database** | Neon Serverless PostgreSQL | `aws-us-east-1` (Pooled + Direct connections) |
| **Search Engine** | Tavily MCP Server | Managed Tavily API with stdio / HTTP bridge |
| **Observability** | LangSmith | Multi-agent tracing & LLM monitoring |

---

## 🏗️ Architecture & Topology

```text
               ┌────────────────────────────────────────────────────────┐
               │              Frontend: Next.js on Vercel               │
               │             (https://deepcite.vercel.app)              │
               └────────────┬─────────────────────────────┬─────────────┘
                            │ HTTPS / REST API            │
                            ▼                             ▼
               ┌───────────────────────────┐ ┌──────────────────────────┐
               │    Production Backend     │ │     Preview Deploys      │
               │   (Render Web Service)    │ │   (PR Branch Previews)   │
               └────────────┬──────────────┘ └──────────────────────────┘
                            │
          ┌─────────────────┼──────────────────────────┬─────────────────┐
          ▼                 ▼                          ▼                 ▼
┌──────────────────┐ ┌─────────────────┐ ┌───────────────────┐ ┌────────────────┐
│  Neon PostgreSQL │ │   Groq Cloud    │ │ Tavily MCP Search │ │   LangSmith    │
│  (Database +     │ │ (Llama 3.3 70B  │ │ (Live Multi-query │ │  (Distributed  │
│   Checkpoints)   │ │  Fast Inference)│ │  Web Retrieval)   │ │ Agent Traces)  │
└──────────────────┘ └─────────────────┘ └───────────────────┘ └────────────────┘
```

---

## 🔒 Secrets & Environment Variables

Environment variables are configured in host secret managers (Render Environment, Vercel Project Settings) and are never committed to version control.

### Backend (`Render` & Local `.env`)

```ini
# Application Core
ENV=production
PROJECT_NAME="Deepcite API"
API_V1_STR=/api/v1
SECRET_KEY=<cryptographically_secure_random_key>
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>/<database>?ssl=require

# External APIs
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...
GEMINI_API_KEY=AIzaSy... # Fallback provider

# Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_PROJECT="deepcite-production"

# CORS Configuration
CORS_ORIGINS=["https://deepcite.vercel.app","http://localhost:3000"]
```

### Frontend (`Vercel` & Local `.env.local`)

```ini
NEXT_PUBLIC_API_URL=https://deepcite-967b.onrender.com
NEXT_PUBLIC_APP_ENV=production
```

---

## 🔄 CI/CD Pipelines

### 1. GitHub Actions (`.github/workflows/ci.yml`)
Runs on every push and pull request to `main`:
- **Backend Quality**: Python 3.12 syntax check with `Ruff`, unit test suite execution with `pytest`.
- **Frontend Quality**: TypeScript type checking with `tsc --noEmit`, ESLint validation, production bundle build.
- **Docker Verification**: Automated container build and test validation.

### 2. Vercel Continuous Deployment
- Connected to GitHub repository `Amankhan1009/Deepcite`.
- Every push to `main` initiates a production deployment.
- Pull requests receive automatic isolated preview deployments. CORS in FastAPI dynamically permits preview domains matching `https://.*\.vercel\.app`.

### 3. Render Backend Deployment
- Deployed as a Python web service running `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Runs database migrations via Alembic on startup.
- Manages checkpointer state tables automatically via LangGraph Postgres checkpointer integration.

---

## 🐳 Local Containerization (Docker Compose)

For local development parity with production:

```bash
# Clone the repository
git clone https://github.com/Amankhan1009/Deepcite.git
cd Deepcite

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Run complete stack via Docker Compose
docker compose up --build
```

- Frontend available at: `http://localhost:3000`
- Backend API available at: `http://localhost:8000`
- API Docs at: `http://localhost:8000/docs`
