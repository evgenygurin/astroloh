"""
Database initialization and dependency injection.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import DatabaseManager

# Global database manager instance
db_manager: DatabaseManager = None

# For backward compatibility with tests
async_session_factory = None


async def init_database():
    """Initialize database connection."""
    global db_manager, async_session_factory

    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured")

    db_manager = DatabaseManager(settings.DATABASE_URL)
    await db_manager.initialize()
    await db_manager.create_tables()

    # Set for backward compatibility with tests
    async_session_factory = db_manager.async_session


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for FastAPI.

    Yields:
        AsyncSession: Database session
    """
    if not db_manager:
        await init_database()

    async with db_manager.async_session() as session:
        yield session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Alias for get_database for backward compatibility.

    Yields:
        AsyncSession: Database session
    """
    async for session in get_database():
        yield session


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.

    Yields:
        AsyncSession: Database session
    """
    if not db_manager:
        await init_database()

    async with db_manager.async_session() as session:
        yield session


async def close_database():
    """Close database connections."""
    if db_manager:
        try:
            await db_manager.close()
        except Exception:
            pass
