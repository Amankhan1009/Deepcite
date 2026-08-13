#!/bin/sh
set -e

alembic upgrade head

python -c "import asyncio; from app.infrastructure.agents.checkpointer import setup_checkpointer_tables; asyncio.run(setup_checkpointer_tables())"

uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"