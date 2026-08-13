from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env.
    Kept deliberately minimal for Milestone 1 — grows as later milestones
    need more (JWT secret in M3, MCP server URLs in M7, etc).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Deep Research Platform"
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000"
    database_url: str  # postgresql+asyncpg://user:pass@host/db?ssl=require
    gemini_api_key: str = ""  # required for scripts/gemini_spike.py, not app yet
    groq_api_key: str = ""
    jwt_secret: str = "dev-secret-change-in-production"
    tavily_api_key: str = ""  # required for M7 Research Agent (tavily-mcp server)
    
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "deepcite"
    langsmith_endpoint: str = "https://api.smith.langchain.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
