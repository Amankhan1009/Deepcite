# Deepcite Backend Service

FastAPI-powered backend orchestrating the evidence-grounded multi-agent research pipeline using LangGraph, PostgreSQL (Neon), Groq, and Tavily MCP.

For complete architectural and engineering documentation, see [`files/README.md`](../files/README.md).

---

## 🚀 Quickstart

### 1. Environment & Dependencies

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` to configure your API keys (`DATABASE_URL`, `GROQ_API_KEY`, `TAVILY_API_KEY`, `SECRET_KEY`).

### 2. Database Migrations

```bash
alembic upgrade head
```

### 3. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

- API Base URL: `http://localhost:8000/api/v1`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

---

## 🧪 Testing

```bash
# Run unit and agent tests
PYTHONPATH=. pytest tests/unit/ tests/agent/
```

---

## 🐳 Docker

```bash
docker build -t deepcite-backend .
docker run -p 8000:8000 --env-file .env deepcite-backend
```
