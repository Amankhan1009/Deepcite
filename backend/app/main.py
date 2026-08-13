from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.presentation.api.v1 import (
    auth,
    evaluation,
    health,
    observability,
    reports,
    research,
    workspaces,
)
from app.presentation.api.v1 import (
    settings as settings_router,
)

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")
app.include_router(observability.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")
