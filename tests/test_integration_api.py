"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.yandex_models import YandexRequest, YandexSession, YandexUser


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    def setup_method(self):
        """Setup before each test."""
        self.client = TestClient(app)
    
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
                "client_id": "test_client"
            },
            "session": {
                "message_id": 1,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {
                    "user_id": "test_user_456"
                },
                "application": {
                    "application_id": "test_app"
                },
                "new": True
            },
            "request": {
                "command": "привет",
                "original_utterance": "привет",
                "type": "SimpleUtterance",
                "markup": {
                    "dangerous_context": False
                },
                "payload": {}
            },
            "version": "1.0"
        }
        
        with patch('app.core.database.get_database') as mock_db:
            mock_db.return_value = AsyncMock()
            
            response = self.client.post(
                "/api/v1/yandex/webhook",
                json=request_data,
                headers={"Content-Type": "application/json"}
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
                "client_id": "test_client"
            },
            "session": {
                "message_id": 2,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {
                    "user_id": "test_user_456"
                },
                "application": {
                    "application_id": "test_app"
                },
                "new": False
            },
            "request": {
                "command": "мой гороскоп на сегодня",
                "original_utterance": "мой гороскоп на сегодня",
                "type": "SimpleUtterance",
                "markup": {
                    "dangerous_context": False
                },
                "payload": {}
            },
            "version": "1.0"
        }
        
        with patch('app.core.database.get_database') as mock_db:
            mock_db.return_value = AsyncMock()
            
            response = self.client.post(
                "/api/v1/yandex/webhook",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        response_data = data["response"]
        assert "text" in response_data
        
        # Should contain horoscope-related content
        text = response_data["text"].lower()
        assert any(word in text for word in ["гороскоп", "прогноз", "звёзды", "астрологи"])
    
    def test_yandex_webhook_compatibility_request(self):
        """Test Yandex webhook with compatibility request."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client"
            },
            "session": {
                "message_id": 3,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {
                    "user_id": "test_user_456"
                },
                "application": {
                    "application_id": "test_app"
                },
                "new": False
            },
            "request": {
                "command": "совместимость льва и весов",
                "original_utterance": "совместимость льва и весов",
                "type": "SimpleUtterance",
                "markup": {
                    "dangerous_context": False
                },
                "payload": {}
            },
            "version": "1.0"
        }
        
        with patch('app.core.database.get_database') as mock_db:
            mock_db.return_value = AsyncMock()
            
            response = self.client.post(
                "/api/v1/yandex/webhook",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        response_data = data["response"]
        assert "text" in response_data
        
        # Should contain compatibility-related content
        text = response_data["text"].lower()
        assert any(word in text for word in ["совместимость", "отношения", "пара", "лев", "весы"])
    
    def test_yandex_webhook_help_request(self):
        """Test Yandex webhook with help request."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client"
            },
            "session": {
                "message_id": 4,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {
                    "user_id": "test_user_456"
                },
                "application": {
                    "application_id": "test_app"
                },
                "new": False
            },
            "request": {
                "command": "помощь",
                "original_utterance": "помощь",
                "type": "SimpleUtterance",
                "markup": {
                    "dangerous_context": False
                },
                "payload": {}
            },
            "version": "1.0"
        }
        
        with patch('app.core.database.get_database') as mock_db:
            mock_db.return_value = AsyncMock()
            
            response = self.client.post(
                "/api/v1/yandex/webhook",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        response_data = data["response"]
        assert "text" in response_data
        
        # Should contain help information
        text = response_data["text"].lower()
        assert any(word in text for word in ["помощь", "команды", "возможности", "умею"])
    
    def test_yandex_webhook_invalid_request(self):
        """Test Yandex webhook with invalid request data."""
        invalid_request = {
            "invalid": "data"
        }
        
        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=invalid_request,
            headers={"Content-Type": "application/json"}
        )
        
        # Should handle invalid data gracefully
        assert response.status_code in [400, 422, 500]
    
    def test_yandex_webhook_empty_command(self):
        """Test Yandex webhook with empty command."""
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client"
            },
            "session": {
                "message_id": 5,
                "session_id": "test_session_123",
                "skill_id": "test_skill",
                "user_id": "test_user_456",
                "user": {
                    "user_id": "test_user_456"
                },
                "application": {
                    "application_id": "test_app"
                },
                "new": False
            },
            "request": {
                "command": "",
                "original_utterance": "",
                "type": "SimpleUtterance",
                "markup": {
                    "dangerous_context": False
                },
                "payload": {}
            },
            "version": "1.0"
        }
        
        with patch('app.core.database.get_database') as mock_db:
            mock_db.return_value = AsyncMock()
            
            response = self.client.post(
                "/api/v1/yandex/webhook",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should handle empty commands gracefully
        assert "response" in data
        assert "text" in data["response"]
    
    def test_security_endpoint_data_export(self):
        """Test security endpoint for data export."""
        with patch('app.core.database.get_database') as mock_db:
            mock_db.return_value = AsyncMock()
            
            response = self.client.post(
                "/api/v1/security/export-data",
                json={"user_id": "test_user", "verification_token": "test_token"}
            )
        
        # Should return 200 or appropriate response
        assert response.status_code in [200, 202, 400, 401, 404]
    
    def test_security_endpoint_data_deletion(self):
        """Test security endpoint for data deletion."""
        with patch('app.core.database.get_database') as mock_db:
            mock_db.return_value = AsyncMock()
            
            response = self.client.post(
                "/api/v1/security/delete-data",
                json={"user_id": "test_user", "verification_token": "test_token"}
            )
        
        # Should return 200 or appropriate response
        assert response.status_code in [200, 202, 400, 401, 404]
    
    def test_yandex_webhook_concurrent_requests(self):
        """Test handling concurrent requests to Yandex webhook."""
        import threading
        import time
        
        request_data = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "test_client"
            },
            "session": {
                "message_id": 6,
                "session_id": "test_session_concurrent",
                "skill_id": "test_skill",
                "user_id": "test_user_concurrent",
                "user": {
                    "user_id": "test_user_concurrent"
                },
                "application": {
                    "application_id": "test_app"
                },
                "new": False
            },
            "request": {
                "command": "привет",
                "original_utterance": "привет",
                "type": "SimpleUtterance",
                "markup": {
                    "dangerous_context": False
                },
                "payload": {}
            },
            "version": "1.0"
        }
        
        responses = []
        
        def make_request():
            with patch('app.core.database.get_database') as mock_db:
                mock_db.return_value = AsyncMock()
                
                response = self.client.post(
                    "/api/v1/yandex/webhook",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
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
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]
        
        # Test with missing required fields
        incomplete_request = {
            "session": {
                "session_id": "test_session"
            }
        }
        
        response = self.client.post(
            "/api/v1/yandex/webhook",
            json=incomplete_request,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]