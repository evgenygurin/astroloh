"""
Database initialization and dependency injection.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import DatabaseManager
from app.core.config import settings


# Global database manager instance
db_manager: DatabaseManager = None


async def init_database():
    """Initialize database connection."""
    global db_manager
    
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is not configured")
    
    db_manager = DatabaseManager(settings.DATABASE_URL)
    await db_manager.initialize()
    await db_manager.create_tables()


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for FastAPI.
    
    Yields:
        AsyncSession: Database session
    """
    if not db_manager:
        await init_database()
    
    async for session in db_manager.get_session():
        yield session


async def close_database():
    """Close database connections."""
    if db_manager:
        await db_manager.close()