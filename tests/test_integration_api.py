"""
Integration tests for API endpoints.
"""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.database import get_database
from app.main import app


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    def setup_method(self):
        """Setup before each test."""

        # Mock the database dependency
        async def mock_get_database():
            db = AsyncMock()

            # Create a proper mock result that returns None for scalar_one_or_none
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None

            db.execute = AsyncMock(return_value=mock_result)
            db.commit = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()
            db.add = AsyncMock()
            db.refresh = AsyncMock()
            yield db

        app.dependency_overrides[get_database] = mock_get_database
        self.client = TestClient(app)

    def teardown_method(self):
        """Cleanup after each test."""
        # Clear dependency overrides
        app.dependency_overrides.clear()

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Astroloh" in data["message"]

    def test_yandex_webhook_greeting(self):
        """Test Yandex webhook with greeting."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client",
            },
            "session": {
                "message_id": 1,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {"user_id": "test_user_456"},
                "application": {"application_id": "test_app"},
                "new": True,
            },
            "request": {
                "command": "привет",
                "original_utterance": "привет",
                "type": "SimpleUtterance",
                "markup": {"dangerous_context": False},
                "payload": {},
            },
            "version": "1.0",
        }

        async def mock_get_database():
            import uuid
            from datetime import datetime
            from unittest.mock import MagicMock

            # Create a mock user object
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.yandex_user_id = "test_user_123"
            mock_user.data_consent = True
            mock_user.last_accessed = datetime.utcnow()
            mock_user.zodiac_sign = "leo"
            mock_user.gender = "female"
            mock_user.encrypted_name = b"encrypted"

            # Create mock database session
            db = AsyncMock()

            # Mock the execute method to return proper results for different queries
            async def mock_execute_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                # For user queries, return the mock user
                mock_result.scalar_one_or_none.return_value = mock_user
                # For count queries, return a number
                mock_result.scalar.return_value = 1
                return mock_result

            db.execute.side_effect = mock_execute_side_effect
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()

            yield db

        # Clear existing dependency overrides and set specific mock
        app.dependency_overrides.clear()
        app.dependency_overrides[get_database] = mock_get_database

        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "session" in data
        assert "version" in data

        # Check response structure
        response_data = data["response"]
        assert "text" in response_data
        assert "end_session" in response_data
        assert isinstance(response_data["text"], str)
        assert len(response_data["text"]) > 0

    def test_yandex_webhook_horoscope_request(self):
        """Test Yandex webhook with horoscope request."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client",
            },
            "session": {
                "message_id": 2,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {"user_id": "test_user_456"},
                "application": {"application_id": "test_app"},
                "new": False,
            },
            "request": {
                "command": "мой гороскоп на сегодня",
                "original_utterance": "мой гороскоп на сегодня",
                "type": "SimpleUtterance",
                "markup": {"dangerous_context": False},
                "payload": {},
            },
            "version": "1.0",
        }

        async def mock_get_database():
            import uuid
            from datetime import datetime
            from unittest.mock import MagicMock

            # Create a mock user object
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.yandex_user_id = "test_user_123"
            mock_user.data_consent = True
            mock_user.last_accessed = datetime.utcnow()
            mock_user.zodiac_sign = "leo"
            mock_user.gender = "female"
            mock_user.encrypted_name = b"encrypted"

            # Create mock database session
            db = AsyncMock()

            # Mock the execute method to return proper results for different queries
            async def mock_execute_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                # For user queries, return the mock user
                mock_result.scalar_one_or_none.return_value = mock_user
                # For count queries, return a number
                mock_result.scalar.return_value = 1
                return mock_result

            db.execute.side_effect = mock_execute_side_effect
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()

            yield db

        # Clear existing dependency overrides and set specific mock
        app.dependency_overrides.clear()
        app.dependency_overrides[get_database] = mock_get_database

        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        response_data = data["response"]
        assert "text" in response_data

        # Should contain horoscope-related content
        text = response_data["text"].lower()
        assert any(
            word in text
            for word in ["гороскоп", "прогноз", "звёзды", "астрологи"]
        )

    def test_yandex_webhook_compatibility_request(self):
        """Test Yandex webhook with compatibility request."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client",
            },
            "session": {
                "message_id": 3,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {"user_id": "test_user_456"},
                "application": {"application_id": "test_app"},
                "new": False,
            },
            "request": {
                "command": "совместимость льва и весов",
                "original_utterance": "совместимость льва и весов",
                "type": "SimpleUtterance",
                "markup": {"dangerous_context": False},
                "payload": {},
            },
            "version": "1.0",
        }

        async def mock_get_database():
            import uuid
            from datetime import datetime
            from unittest.mock import MagicMock

            # Create a mock user object
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.yandex_user_id = "test_user_123"
            mock_user.data_consent = True
            mock_user.last_accessed = datetime.utcnow()
            mock_user.zodiac_sign = "leo"
            mock_user.gender = "female"
            mock_user.encrypted_name = b"encrypted"

            # Create mock database session
            db = AsyncMock()

            # Mock the execute method to return proper results for different queries
            async def mock_execute_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                # For user queries, return the mock user
                mock_result.scalar_one_or_none.return_value = mock_user
                # For count queries, return a number
                mock_result.scalar.return_value = 1
                return mock_result

            db.execute.side_effect = mock_execute_side_effect
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()

            yield db

        # Clear existing dependency overrides and set specific mock
        app.dependency_overrides.clear()
        app.dependency_overrides[get_database] = mock_get_database

        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        response_data = data["response"]
        assert "text" in response_data

        # Should contain compatibility-related content
        text = response_data["text"].lower()
        assert any(
            word in text
            for word in ["совместимость", "отношения", "пара", "лев", "весы"]
        )

    def test_yandex_webhook_help_request(self):
        """Test Yandex webhook with help request."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client",
            },
            "session": {
                "message_id": 4,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {"user_id": "test_user_456"},
                "application": {"application_id": "test_app"},
                "new": False,
            },
            "request": {
                "command": "помощь",
                "original_utterance": "помощь",
                "type": "SimpleUtterance",
                "markup": {"dangerous_context": False},
                "payload": {},
            },
            "version": "1.0",
        }

        async def mock_get_database():
            import uuid
            from datetime import datetime
            from unittest.mock import MagicMock

            # Create a mock user object
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.yandex_user_id = "test_user_123"
            mock_user.data_consent = True
            mock_user.last_accessed = datetime.utcnow()
            mock_user.zodiac_sign = "leo"
            mock_user.gender = "female"
            mock_user.encrypted_name = b"encrypted"

            # Create mock database session
            db = AsyncMock()

            # Mock the execute method to return proper results for different queries
            async def mock_execute_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                # For user queries, return the mock user
                mock_result.scalar_one_or_none.return_value = mock_user
                # For count queries, return a number
                mock_result.scalar.return_value = 1
                return mock_result

            db.execute.side_effect = mock_execute_side_effect
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()

            yield db

        # Clear existing dependency overrides and set specific mock
        app.dependency_overrides.clear()
        app.dependency_overrides[get_database] = mock_get_database

        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        response_data = data["response"]
        assert "text" in response_data

        # Should contain help information
        text = response_data["text"].lower()
        assert any(
            word in text
            for word in ["помощь", "команды", "возможности", "умею"]
        )

    def test_yandex_webhook_invalid_request(self):
        """Test Yandex webhook with invalid request data."""
        invalid_request = {"invalid": "data"}

        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=invalid_request,
            headers={"Content-Type": "application/json"},
        )

        # Should handle invalid data gracefully
        assert response.status_code in [400, 422, 500]

    def test_yandex_webhook_empty_command(self):
        """Test Yandex webhook with empty command."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client",
            },
            "session": {
                "message_id": 5,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {"user_id": "test_user_456"},
                "application": {"application_id": "test_app"},
                "new": False,
            },
            "request": {
                "command": "",
                "original_utterance": "",
                "type": "SimpleUtterance",
                "markup": {"dangerous_context": False},
                "payload": {},
            },
            "version": "1.0",
        }

        async def mock_get_database():
            import uuid
            from datetime import datetime
            from unittest.mock import MagicMock

            # Create a mock user object
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.yandex_user_id = "test_user_123"
            mock_user.data_consent = True
            mock_user.last_accessed = datetime.utcnow()
            mock_user.zodiac_sign = "leo"
            mock_user.gender = "female"
            mock_user.encrypted_name = b"encrypted"

            # Create mock database session
            db = AsyncMock()

            # Mock the execute method to return proper results for different queries
            async def mock_execute_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                # For user queries, return the mock user
                mock_result.scalar_one_or_none.return_value = mock_user
                # For count queries, return a number
                mock_result.scalar.return_value = 1
                return mock_result

            db.execute.side_effect = mock_execute_side_effect
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()

            yield db

        # Clear existing dependency overrides and set specific mock
        app.dependency_overrides.clear()
        app.dependency_overrides[get_database] = mock_get_database

        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle empty commands gracefully
        assert "response" in data
        assert "text" in data["response"]

    def test_security_endpoint_data_export(self):
        """Test security endpoint for data export."""

        async def mock_get_database():
            import uuid
            from datetime import datetime
            from unittest.mock import MagicMock

            # Create a mock user object
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.yandex_user_id = "test_user_123"
            mock_user.data_consent = True
            mock_user.last_accessed = datetime.utcnow()
            mock_user.zodiac_sign = "leo"
            mock_user.gender = "female"
            mock_user.encrypted_name = b"encrypted"

            # Create mock database session
            db = AsyncMock()

            # Mock the execute method to return proper results for different queries
            async def mock_execute_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                # For user queries, return the mock user
                mock_result.scalar_one_or_none.return_value = mock_user
                # For count queries, return a number
                mock_result.scalar.return_value = 1
                return mock_result

            db.execute.side_effect = mock_execute_side_effect
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()

            yield db

        with patch(
            "app.core.database.get_database", side_effect=mock_get_database
        ):
            response = self.client.post(
                "/api/v1/security/export-data",
                json={
                    "user_id": "test_user",
                    "verification_token": "test_token",
                },
            )

        # Should return 200 or appropriate response
        assert response.status_code in [200, 202, 400, 401, 404]

    def test_security_endpoint_data_deletion(self):
        """Test security endpoint for data deletion."""

        async def mock_get_database():
            import uuid
            from datetime import datetime
            from unittest.mock import MagicMock

            # Create a mock user object
            mock_user = MagicMock()
            mock_user.id = uuid.uuid4()
            mock_user.yandex_user_id = "test_user_123"
            mock_user.data_consent = True
            mock_user.last_accessed = datetime.utcnow()
            mock_user.zodiac_sign = "leo"
            mock_user.gender = "female"
            mock_user.encrypted_name = b"encrypted"

            # Create mock database session
            db = AsyncMock()

            # Mock the execute method to return proper results for different queries
            async def mock_execute_side_effect(*args, **kwargs):
                mock_result = MagicMock()
                # For user queries, return the mock user
                mock_result.scalar_one_or_none.return_value = mock_user
                # For count queries, return a number
                mock_result.scalar.return_value = 1
                return mock_result

            db.execute.side_effect = mock_execute_side_effect
            db.add = MagicMock()
            db.commit = AsyncMock()
            db.refresh = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()

            yield db

        with patch(
            "app.core.database.get_database", side_effect=mock_get_database
        ):
            response = self.client.post(
                "/api/v1/security/delete-data",
                json={
                    "user_id": "test_user",
                    "verification_token": "test_token",
                },
            )

        # Should return 200 or appropriate response
        assert response.status_code in [200, 202, 400, 401, 404]

    def test_yandex_webhook_concurrent_requests(self):
        """Test handling concurrent requests to Yandex webhook."""
        import threading

        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client",
            },
            "session": {
                "message_id": 6,
                "session_id": "test_session_concurrent",
                "skill_id": "test_skill",
                "user_id": "test_user_concurrent",
                "user": {"user_id": "test_user_concurrent"},
                "application": {"application_id": "test_app"},
                "new": False,
            },
            "request": {
                "command": "привет",
                "original_utterance": "привет",
                "type": "SimpleUtterance",
                "markup": {"dangerous_context": False},
                "payload": {},
            },
            "version": "1.0",
        }

        responses = []

        def make_request():
            async def mock_get_database():
                yield AsyncMock()

            with patch(
                "app.core.database.get_database", side_effect=mock_get_database
            ):
                response = self.client.post(
                    "/api/v1/yandex/webhook",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                )
                responses.append(response)

        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

        assert len(responses) == 3

    def test_api_error_handling(self):
        """Test API error handling."""
        # Test with malformed JSON
        response = self.client.post(
            "/api/v1/yandex/webhook",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code in [400, 422]

        # Test with missing required fields
        incomplete_request = {"session": {"session_id": "test_session"}}

        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=incomplete_request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code in [400, 422]

    def test_security_data_summary_endpoint(self):
        """Test security data summary endpoint."""
        async def mock_get_database():
            db = AsyncMock()
            db.execute = AsyncMock(return_value=AsyncMock())
            db.commit = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()
            yield db

        with patch("app.core.database.get_database", side_effect=mock_get_database):
            response = self.client.get("/api/v1/security/user/test_user/data-summary")
        
        # Should return some response (could be 200, 404, etc.)
        assert response.status_code in [200, 404, 400, 500]

    def test_security_consent_endpoint(self):
        """Test security consent endpoint."""
        async def mock_get_database():
            db = AsyncMock()
            db.execute = AsyncMock(return_value=AsyncMock())
            db.commit = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()
            yield db

        with patch("app.core.database.get_database", side_effect=mock_get_database):
            response = self.client.post(
                "/api/v1/security/user/test_user/consent",
                json={"consent": True, "retention_days": 365}
            )
        
        # Should return some response (could be 200, 404, etc.)
        assert response.status_code in [200, 404, 400, 422, 500]

    def test_security_export_endpoint(self):
        """Test security data export endpoint."""
        async def mock_get_database():
            db = AsyncMock()
            db.execute = AsyncMock(return_value=AsyncMock())
            db.commit = AsyncMock()
            db.rollback = AsyncMock()
            db.close = AsyncMock()
            yield db

        with patch("app.core.database.get_database", side_effect=mock_get_database):
            response = self.client.get("/api/v1/security/user/test_user/export")
        
        # Should return some response (could be 200, 404, etc.)
        assert response.status_code in [200, 404, 400, 500]
