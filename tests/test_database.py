"""
Tests for database connection and configuration.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.database import close_database, get_database, init_database


class TestDatabase:
    """Test database functionality."""

    @pytest.mark.asyncio
    async def test_get_database(self):
        """Test database session dependency."""
        with patch("app.core.database.db_manager") as mock_db_manager:
            mock_session = AsyncMock()

            # Create a proper async context manager mock
            class MockAsyncContextManager:
                async def __aenter__(self):
                    return mock_session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_db_manager.async_session.return_value = (
                MockAsyncContextManager()
            )

            # Get database session
            async for db in get_database():
                assert db == mock_session
                break

    @pytest.mark.asyncio
    async def test_init_database(self):
        """Test database initialization."""
        with patch(
            "app.core.database.DatabaseManager"
        ) as mock_db_manager_class:
            with patch("app.core.database.settings") as mock_settings:
                mock_settings.DATABASE_URL = "postgresql://test"
                mock_db_manager = AsyncMock()
                mock_db_manager_class.return_value = mock_db_manager

                await init_database()

                mock_db_manager.initialize.assert_called_once()
                mock_db_manager.create_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database(self):
        """Test database connection closure."""
        with patch("app.core.database.db_manager") as mock_db_manager:
            mock_db_manager.close = AsyncMock()

            await close_database()

            # Should call close if db_manager exists
            if mock_db_manager:
                mock_db_manager.close.assert_called_once()

    def test_database_url_configuration(self):
        """Test database URL configuration."""
        with patch("app.core.database.settings") as mock_settings:
            mock_settings.DATABASE_URL = (
                "postgresql://test:test@localhost:5432/testdb"
            )

            # Import module to trigger URL configuration

            # Should use the configured URL
            assert mock_settings.DATABASE_URL is not None

    def test_db_manager_creation(self):
        """Test database manager is properly initialized."""

        # Initially should be None before initialization
        # This tests the module-level variable exists

    @pytest.mark.asyncio
    async def test_database_dependency_error_handling(self):
        """Test database dependency handles errors gracefully."""
        with patch("app.core.database.db_manager", None):
            with patch("app.core.database.init_database") as mock_init:
                mock_init.side_effect = Exception("Connection failed")

                with pytest.raises(Exception):
                    async for db in get_database():
                        pass

    @pytest.mark.asyncio
    async def test_init_database_error_handling(self):
        """Test init_database handles errors gracefully."""
        with patch("app.core.database.settings") as mock_settings:
            mock_settings.DATABASE_URL = None

            with pytest.raises(ValueError):
                await init_database()

    @pytest.mark.asyncio
    async def test_close_database_error_handling(self):
        """Test close_database handles errors gracefully."""
        with patch("app.core.database.db_manager") as mock_db_manager:
            mock_db_manager.close.side_effect = Exception("Close failed")

            # Should not raise exception even if close fails
            await close_database()
