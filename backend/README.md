# Backend — Milestone 1

## Setup

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set DATABASE_URL to your Neon connection string
#   (postgresql+asyncpg://..., no sslmode param, use ?ssl=require)
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Then check:
```bash
curl http://127.0.0.1:8000/api/v1/health
```
Expect `{"status":"ok","database":"connected"}` once DATABASE_URL points
at a real reachable Neon database.

## Run tests

```bash
pytest
```

## Run the Gemini spike (separate from the app)

```bash
export GEMINI_API_KEY=your_key_here
python ../scripts/gemini_spike.py
```

Paste the output back — it decides the SDK question in DECISIONS.md.
