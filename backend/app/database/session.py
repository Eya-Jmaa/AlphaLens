"""Async SQLAlchemy engine/session management.

Persistence is optional: if DATABASE_URL is unset or the database is
unreachable, `get_session_factory()` returns None and every repository
function degrades gracefully (logs a warning, returns None/empty) instead of
crashing the app. The core analysis workflow never depends on this.
"""
import logging
from typing import AsyncIterator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings

logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def _normalize_url(url: str) -> str:
    """Accept a plain postgresql:// URL and upgrade it to the asyncpg driver scheme."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def is_configured() -> bool:
    return bool(settings.DATABASE_URL)


def get_engine() -> Optional[AsyncEngine]:
    global _engine
    if _engine is None and is_configured():
        _engine = create_async_engine(_normalize_url(settings.DATABASE_URL), pool_pre_ping=True)
    return _engine


def get_session_factory() -> Optional[async_sessionmaker]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        if engine is not None:
            _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def get_db() -> AsyncIterator[Optional[AsyncSession]]:
    """FastAPI dependency yielding a session, or None if no database is configured."""
    factory = get_session_factory()
    if factory is None:
        yield None
        return
    async with factory() as session:
        yield session


async def check_connection() -> bool:
    """Best-effort connectivity check for health checks / graceful degradation."""
    engine = get_engine()
    if engine is None:
        return False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connectivity check failed: {e}")
        return False
