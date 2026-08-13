from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# NullPool: no connections are held open between requests — each checkout
# opens a fresh asyncpg connection. Deliberate, not a default we forgot to
# change: (1) Neon is serverless Postgres and recommends short-lived
# connections over long-held pools, its own pooler handles reuse server-side;
# (2) SQLAlchemy's pooled connections are bound to the event loop they were
# created on, which breaks (RuntimeError: attached to a different loop) the
# moment anything — our own tests included — runs queries across more than
# one loop. NullPool sidesteps that whole class of bug entirely.
#
# statement_cache_size=0: Neon's pooled connection string runs PgBouncer in
# transaction-pooling mode, which doesn't guarantee the same physical
# connection across statements. asyncpg's default prepared-statement cache
# assumes it does — without this, you get intermittent
# InvalidCachedStatementError. Required whenever connecting through Neon's
# `-pooler` endpoint.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
        "timeout": 30.0,
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a request-scoped async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def check_db_connection() -> bool:
    """Used by the health endpoint. Returns True if a trivial query succeeds."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
