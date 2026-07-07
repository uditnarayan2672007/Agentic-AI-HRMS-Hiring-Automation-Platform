"""
HRMS Backend — Application Settings
Loaded from environment variables / .env file
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    APP_NAME: str = "Elite Coders HRMS API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/hrms_db"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:password@localhost:5432/hrms_db"

    # ── OpenAI ─────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = "sk-placeholder"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"

    # ── Storage ────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    GENERATED_DOCS_DIR: str = "./generated_docs"

    # ── Payroll ────────────────────────────────────────────────────────────
    DEFAULT_TAX_RATE: float = 0.20
    DEFAULT_WORKING_DAYS: int = 22

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
