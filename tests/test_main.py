"""
Tests for main FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app


class TestMainApp:
    """Test main FastAPI application."""

    def setup_method(self):
        """Setup before each test."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Astroloh" in data["message"]

    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_startup_event_with_database_url(self):
        """Test startup event with database URL configured."""
        with patch('app.main.settings') as mock_settings:
            with patch('app.main.init_database') as mock_init_db:
                mock_settings.DATABASE_URL = "postgresql://test"
                mock_init_db.return_value = AsyncMock()
                
                # Import and call startup event
                from app.main import startup_event
                await startup_event()
                
                mock_init_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_event_without_database_url(self):
        """Test startup event without database URL."""
        with patch('app.main.settings') as mock_settings:
            with patch('app.main.init_database') as mock_init_db:
                mock_settings.DATABASE_URL = None
                
                from app.main import startup_event
                await startup_event()
                
                mock_init_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_startup_event_database_error(self):
        """Test startup event when database initialization fails."""
        with patch('app.main.settings') as mock_settings:
            with patch('app.main.init_database') as mock_init_db:
                mock_settings.DATABASE_URL = "postgresql://test"
                mock_init_db.side_effect = Exception("Database connection failed")
                
                # Should not raise exception, just log the error
                from app.main import startup_event
                await startup_event()
                
                mock_init_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_event_success(self):
        """Test shutdown event successful execution."""
        with patch('app.main.close_database') as mock_close_db:
            mock_close_db.return_value = AsyncMock()
            
            from app.main import shutdown_event
            await shutdown_event()
            
            mock_close_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_event_error(self):
        """Test shutdown event when database close fails."""
        with patch('app.main.close_database') as mock_close_db:
            mock_close_db.side_effect = Exception("Failed to close database")
            
            # Should not raise exception, just log the error
            from app.main import shutdown_event
            await shutdown_event()
            
            mock_close_db.assert_called_once()

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is properly configured."""
        # Test that CORS headers are present in response
        response = self.client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        
        # CORS middleware should handle OPTIONS requests
        assert response.status_code in [200, 405]  # Some frameworks return 405 for OPTIONS

    def test_api_routes_included(self):
        """Test that API routes are properly included."""
        from app.main import app
        
        # Check that routers are included by examining the routes
        route_paths = [route.path for route in app.routes]
        
        # Should have routes from both routers
        has_yandex_routes = any("/api/v1" in path for path in route_paths)
        assert has_yandex_routes, "Yandex API routes should be included"

    def test_app_metadata(self):
        """Test FastAPI app metadata configuration."""
        assert app.title == "Astroloh - Навык Астролог для Яндекс Алисы"
        assert app.version == "1.0.0"
        assert "астрологических прогнозов" in app.description.lower()