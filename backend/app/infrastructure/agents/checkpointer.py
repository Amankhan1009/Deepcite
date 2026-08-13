from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import get_settings

settings = get_settings()

# LangGraph's checkpointer uses psycopg (v3), not asyncpg — a separate
# driver from the rest of the app (session.py uses asyncpg via SQLAlchemy).
# Deliberate, not accidental: the checkpointer manages its own schema
# (checkpoints, checkpoint_writes, etc.) and transaction boundaries that
# have nothing to do with our ORM models — mixing the two would couple
# two independent systems for no benefit.
#
# Uses the DIRECT (non-pooled) Neon connection string, same reasoning as
# session.py — see DECISIONS.md.
def _build_checkpointer_db_url(database_url: str) -> str:
    url = database_url.replace(
        "postgresql+asyncpg://",
        "postgresql://",
    ).replace(
        "ssl=require",
        "sslmode=require",
    )

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}connect_timeout=30"


_CHECKPOINTER_DB_URL = _build_checkpointer_db_url(settings.database_url)

@asynccontextmanager
async def get_checkpointer() -> AsyncGenerator[AsyncPostgresSaver]:
    """Yields a ready-to-use Postgres checkpointer. Callers must use this
    as an async context manager — the underlying connection is closed
    when the block exits."""
    async with AsyncPostgresSaver.from_conn_string(_CHECKPOINTER_DB_URL) as checkpointer:
        yield checkpointer


async def setup_checkpointer_tables() -> None:
    """Creates the checkpointer's own tables if they don't exist yet.
    Run once (see the command in this milestone's verification steps) —
    idempotent, safe to run again."""
    async with get_checkpointer() as checkpointer:
        await checkpointer.setup()
