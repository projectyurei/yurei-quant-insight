"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

# Create async engine with connection pooling
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session factory
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session with automatic cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_connection() -> bool:
    """Test database connectivity."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False
