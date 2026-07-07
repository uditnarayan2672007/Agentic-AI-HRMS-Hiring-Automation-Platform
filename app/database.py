"""
Database Engine & Session Factory
- Async SQLAlchemy engine (asyncpg driver)
- Sync engine for Alembic migrations only
- pgvector extension registered automatically
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from loguru import logger

from app.config import settings


# ── Async Engine ──────────────────────────────────────────────────────────────
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ── Base Model ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Startup ───────────────────────────────────────────────────────────────────
async def init_db():
    """Create all tables and ensure pgvector extension exists."""
    async with async_engine.begin() as conn:
        # Enable pgvector
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all ORM-mapped tables
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database initialized — pgvector extension enabled")
