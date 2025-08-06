"""
Tests for Yandex Dialogs API endpoints.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app
from app.models.yandex_models import YandexSession, YandexResponseModel, YandexResponse


class TestYandexDialogsAPI:
    """Test Yandex Dialogs API endpoints."""

    def setup_method(self):
        """Setup before each test."""
        self.client = TestClient(app)

    def test_yandex_health_endpoint(self):
        """Test Yandex dialogs health check endpoint."""
        with patch("app.api.yandex_dialogs.dialog_handler") as mock_handler:
            mock_session_manager = MagicMock()
            mock_session_manager.get_active_sessions_count.return_value = 5
            mock_handler.session_manager = mock_session_manager

            response = self.client.get("/api/v1/yandex/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "yandex_dialogs"
            assert data["active_sessions"] == 5
            assert "components" in data

    def test_yandex_health_endpoint_error(self):
        """Test Yandex dialogs health check when service fails."""
        with patch("app.api.yandex_dialogs.dialog_handler") as mock_handler:
            mock_handler.session_manager.get_active_sessions_count.side_effect = (
                Exception("Service error")
            )

            response = self.client.get("/api/v1/yandex/health")

            assert response.status_code == 503

    def test_cleanup_sessions_endpoint(self):
        """Test cleanup sessions endpoint."""
        with patch("app.api.yandex_dialogs.dialog_handler") as mock_handler:
            mock_session_manager = MagicMock()
            mock_session_manager.cleanup_expired_sessions.return_value = 3
            mock_handler.session_manager = mock_session_manager

            response = self.client.post("/api/v1/yandex/cleanup-sessions")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["cleaned_sessions"] == 3

    def test_cleanup_sessions_endpoint_error(self):
        """Test cleanup sessions endpoint when cleanup fails."""
        with patch("app.api.yandex_dialogs.dialog_handler") as mock_handler:
            mock_handler.session_manager.cleanup_expired_sessions.side_effect = (
                Exception("Cleanup failed")
            )

            response = self.client.post("/api/v1/yandex/cleanup-sessions")

            assert response.status_code == 500

    @patch("app.api.yandex_dialogs.get_database")
    @patch("app.api.yandex_dialogs.UserManager")
    @patch("app.api.yandex_dialogs.dialog_handler")
    def test_yandex_webhook_success(
        self, mock_handler, mock_user_manager_class, mock_get_db
    ):
        """Test successful webhook request processing."""
        # Setup mocks
        mock_db = MagicMock()

        async def mock_get_database():
            yield mock_db

        mock_get_db.side_effect = mock_get_database

        mock_user_manager = AsyncMock()
        mock_user_manager_class.return_value = mock_user_manager

        mock_response = YandexResponseModel(
            response=YandexResponse(text="Test response", end_session=False),
            session=YandexSession(
                message_id=1,
                session_id="test_session",
                skill_id="test_skill",
                user_id="test_user",
            ),
            version="1.0",
        )
        mock_handler.handle_request = AsyncMock(return_value=mock_response)

        # Create test request
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "ru.yandex.searchplugin/7.16",
            },
            "session": {
                "message_id": 1,
                "session_id": "test_session",
                "skill_id": "test_skill",
                "user_id": "test_user",
                "new": True,
            },
            "request": {
                "command": "привет",
                "original_utterance": "Привет",
                "nlu": {"tokens": ["привет"], "entities": [], "intents": {}},
                "markup": {"dangerous_context": False},
                "type": "SimpleUtterance",
            },
            "version": "1.0",
        }

        response = self.client.post("/api/v1/yandex/webhook", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session" in data

    @patch("app.api.yandex_dialogs.get_database")
    @patch("app.api.yandex_dialogs.UserManager")
    @patch("app.api.yandex_dialogs.dialog_handler")
    def test_yandex_webhook_error_handling(
        self, mock_handler, mock_user_manager_class, mock_get_db
    ):
        """Test webhook error handling."""
        # Setup mocks to raise an exception
        mock_db = MagicMock()

        async def mock_get_database():
            yield mock_db

        mock_get_db.side_effect = mock_get_database

        mock_user_manager = AsyncMock()
        mock_user_manager_class.return_value = mock_user_manager

        mock_handler.handle_request = AsyncMock(
            side_effect=Exception("Processing error")
        )

        with patch("app.api.yandex_dialogs.error_handler") as mock_error_handler:
            mock_error_response = YandexResponse(
                text="Извините, произошла ошибка. Попробуйте еще раз.",
                end_session=False,
            )
            mock_error_handler.handle_error.return_value = mock_error_response

            request_data = {
                "meta": {
                    "locale": "ru-RU",
                    "timezone": "UTC",
                    "client_id": "ru.yandex.searchplugin/7.16",
                },
                "session": {
                    "message_id": 1,
                    "session_id": "test_session",
                    "skill_id": "test_skill",
                    "user_id": "test_user",
                    "new": True,
                },
                "request": {
                    "command": "привет",
                    "original_utterance": "Привет",
                    "nlu": {"tokens": ["привет"], "entities": [], "intents": {}},
                    "markup": {"dangerous_context": False},
                    "type": "SimpleUtterance",
                },
                "version": "1.0",
            }

            response = self.client.post("/api/v1/yandex/webhook", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            mock_error_handler.handle_error.assert_called_once()

    def test_yandex_webhook_invalid_request(self):
        """Test webhook with invalid request data."""
        # Send invalid JSON
        response = self.client.post("/api/v1/yandex/webhook", json={})

        # Should return validation error
        assert response.status_code == 422
