from fastapi import APIRouter

from app.infrastructure.db.session import check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    db_ok = await check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }
