"""
Tests for Google Assistant integration.
"""
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.google_adapter import GoogleAssistantAdapter


class TestGoogleAssistantWebhook:
    """Test Google Assistant webhook endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    @patch('app.api.google_assistant.multi_platform_handler')
    @patch('app.api.google_assistant.UserManager')
    def test_google_actions_webhook(self, mock_user_manager, mock_handler):
        """Test Google Actions webhook request."""
        # Mock user manager
        mock_user_manager_instance = AsyncMock()
        mock_user_manager.return_value = mock_user_manager_instance
        
        # Mock handler response
        from app.models.platform_models import UniversalResponse, Button
        mock_response = UniversalResponse(
            text="Добро пожаловать в мир астрологии! Я помогу вам с гороскопами.",
            tts="Добро пожаловать в мир астрологии! Я помогу вам с гороскопами.",
            buttons=[
                Button(title="Мой гороскоп", payload={"action": "horoscope"}),
                Button(title="Совместимость", payload={"action": "compatibility"})
            ],
            end_session=False
        )
        mock_handler.handle_request = AsyncMock(return_value=mock_response)
        
        # Test Google Actions request
        google_request = {
            "user": {
                "userId": "google_user_123",
                "locale": "ru-RU"
            },
            "conversation": {
                "conversationId": "conv_456",
                "type": "NEW"
            },
            "inputs": [
                {
                    "intent": "actions.intent.MAIN",
                    "rawInputs": [
                        {"query": "Talk to Astrologer"}
                    ]
                }
            ],
            "device": {},
            "surface": {
                "capabilities": [
                    {"name": "actions.capability.SCREEN_OUTPUT"},
                    {"name": "actions.capability.AUDIO_OUTPUT"}
                ]
            }
        }
        
        response = self.client.post("/api/v1/google/webhook", json=google_request)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Should have Google Actions response format
        assert "expect_user_response" in response_data
        assert "rich_response" in response_data
        assert response_data["expect_user_response"]
        
        # Verify handler was called
        mock_handler.handle_request.assert_called_once()
    
    @patch('app.api.google_assistant.multi_platform_handler')
    @patch('app.api.google_assistant.UserManager')
    def test_dialogflow_webhook(self, mock_user_manager, mock_handler):
        """Test Dialogflow v2 webhook request."""
        # Mock user manager
        mock_user_manager_instance = AsyncMock()
        mock_user_manager.return_value = mock_user_manager_instance
        
        # Mock handler response
        from app.models.platform_models import UniversalResponse
        mock_response = UniversalResponse(
            text="Для составления гороскопа назовите ваш знак зодиака.",
            end_session=False
        )
        mock_handler.handle_request = AsyncMock(return_value=mock_response)
        
        # Test Dialogflow request
        dialogflow_request = {
            "queryResult": {
                "queryText": "Расскажи гороскоп",
                "intent": {
                    "name": "projects/test/agent/intents/horoscope",
                    "displayName": "Horoscope Intent"
                },
                "intentDetectionConfidence": 0.95,
                "languageCode": "ru"
            },
            "session": "projects/test/agent/sessions/session_789"
        }
        
        response = self.client.post("/api/v1/google/webhook", json=dialogflow_request)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Should have Dialogflow response format
        assert "fulfillmentText" in response_data
        assert "гороскопа" in response_data["fulfillmentText"]
        
        # Verify handler was called
        mock_handler.handle_request.assert_called_once()
    
    def test_google_webhook_invalid_request(self):
        """Test Google webhook with invalid request."""
        invalid_request = {"invalid": "data"}
        
        response = self.client.post("/api/v1/google/webhook", json=invalid_request)
        
        assert response.status_code == 400
        assert "Invalid Google Assistant request" in response.json()["detail"]
    
    def test_google_health_check(self):
        """Test Google Assistant health check endpoint."""
        response = self.client.get("/api/v1/google/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "google_assistant"
        assert data["platform"] == "google_assistant"
        assert "supported_formats" in data
        assert "google_actions" in data["supported_formats"]
        assert "dialogflow_v2" in data["supported_formats"]


class TestGoogleAssistantAdapter:
    """Test Google Assistant adapter functionality."""
    
    def setup_method(self):
        """Set up test adapter."""
        self.adapter = GoogleAssistantAdapter()
    
    def test_validate_google_actions_request(self):
        """Test Google Actions request validation."""
        valid_request = {
            "user": {"userId": "test_user"},
            "conversation": {"conversationId": "test_conv", "type": "NEW"},
            "inputs": [{"intent": "actions.intent.MAIN"}]
        }
        
        assert self.adapter.validate_request(valid_request)
    
    def test_validate_dialogflow_request(self):
        """Test Dialogflow request validation."""
        valid_request = {
            "queryResult": {
                "queryText": "Hello",
                "intent": {"displayName": "Default Welcome Intent"}
            }
        }
        
        assert self.adapter.validate_request(valid_request)
    
    def test_convert_google_actions_to_universal(self):
        """Test converting Google Actions request to universal format."""
        google_request = {
            "user": {
                "userId": "google_user_123",
                "locale": "ru-RU"
            },
            "conversation": {
                "conversationId": "conv_456",
                "type": "ACTIVE",
                "conversationToken": "token_789"
            },
            "inputs": [
                {
                    "intent": "horoscope.get",
                    "rawInputs": [
                        {"query": "Расскажи гороскоп на завтра"}
                    ]
                }
            ],
            "device": {
                "location": {"country": "RU"}
            },
            "surface": {
                "capabilities": [
                    {"name": "actions.capability.SCREEN_OUTPUT"}
                ]
            }
        }
        
        universal_request = self.adapter.to_universal_request(google_request)
        
        assert universal_request.platform.value == "google_assistant"
        assert universal_request.user_id == "google_user_123"
        assert universal_request.session_id == "conv_456"
        assert universal_request.text == "Расскажи гороскоп на завтра"
        assert not universal_request.is_new_session
        
        # Check user context
        assert "google_user" in universal_request.user_context
        assert universal_request.user_context["google_user"]["locale"] == "ru-RU"
        assert universal_request.user_context["conversation_token"] == "token_789"
        assert universal_request.user_context["intent"] == "horoscope.get"
    
    def test_convert_dialogflow_to_universal(self):
        """Test converting Dialogflow request to universal format."""
        dialogflow_request = {
            "queryResult": {
                "queryText": "Какая совместимость у Льва и Рыб?",
                "intent": {
                    "name": "projects/test/agent/intents/compatibility",
                    "displayName": "Compatibility Intent"
                },
                "intentDetectionConfidence": 0.89,
                "languageCode": "ru",
                "parameters": {
                    "sign1": "Лев",
                    "sign2": "Рыбы"
                }
            },
            "session": "projects/test/agent/sessions/session_abc123"
        }
        
        universal_request = self.adapter.to_universal_request(dialogflow_request)
        
        assert universal_request.platform.value == "google_assistant"
        assert universal_request.user_id == "session_abc123"
        assert universal_request.text == "Какая совместимость у Льва и Рыб?"
        assert not universal_request.is_new_session
        
        # Check Dialogflow-specific context
        assert "dialogflow" in universal_request.user_context
        assert universal_request.user_context["dialogflow"]["intent_name"] == "Compatibility Intent"
        assert universal_request.user_context["dialogflow"]["parameters"]["sign1"] == "Лев"
    
    def test_convert_universal_response_to_google_actions(self):
        """Test converting universal response to Google Actions format."""
        from app.models.platform_models import UniversalResponse, Button
        
        universal_response = UniversalResponse(
            text="Совместимость Льва и Рыб составляет 75%. Это хорошая пара!",
            tts="Совместимость Льва и Рыб составляет семьдесят пять процентов. Это хорошая пара!",
            buttons=[
                Button(title="Другая пара", payload={"action": "new_compatibility"}),
                Button(title="Мой гороскоп", payload={"action": "horoscope"}),
                Button(title="Главное меню", payload={"action": "main_menu"})
            ],
            end_session=False
        )
        
        google_response = self.adapter.from_universal_response(universal_response)
        
        assert "expect_user_response" in google_response
        assert google_response["expect_user_response"]
        
        assert "rich_response" in google_response
        rich_response = google_response["rich_response"]
        
        # Check simple response
        assert "items" in rich_response
        assert len(rich_response["items"]) == 1
        simple_response = rich_response["items"][0]["simpleResponse"]
        assert "совместимость" in simple_response["display_text"].lower()
        
        # Check suggestions
        assert "suggestions" in rich_response
        assert len(rich_response["suggestions"]) == 3
        assert rich_response["suggestions"][0]["title"] == "Другая пара"
    
    def test_convert_universal_response_to_dialogflow(self):
        """Test converting universal response to Dialogflow format."""
        from app.models.platform_models import UniversalResponse, Button
        
        universal_response = UniversalResponse(
            text="Астрологический совет: доверьтесь интуиции в принятии решений.",
            buttons=[
                Button(title="Новый совет", payload={"action": "new_advice"}),
                Button(title="Гороскоп", payload={"action": "horoscope"})
            ],
            end_session=False,
            platform_specific={
                "use_dialogflow": True
            }
        )
        
        dialogflow_response = self.adapter.from_universal_response(universal_response)
        
        assert "fulfillmentText" in dialogflow_response
        assert "совет" in dialogflow_response["fulfillmentText"].lower()
        
        assert "fulfillmentMessages" in dialogflow_response
        messages = dialogflow_response["fulfillmentMessages"]
        
        # Should have text response
        text_message = next((m for m in messages if "text" in m), None)
        assert text_message is not None
        assert "интуиции" in text_message["text"]["text"][0]
        
        # Should have quick replies
        quick_replies_message = next((m for m in messages if "quickReplies" in m), None)
        assert quick_replies_message is not None
        assert len(quick_replies_message["quickReplies"]["quickReplies"]) == 2
        assert "Новый совет" in quick_replies_message["quickReplies"]["quickReplies"]
    
    def test_format_google_text_for_speech(self):
        """Test formatting text for Google Assistant speech synthesis."""
        text_with_emojis = "Ваш гороскоп ⭐: сегодня вас ждёт успех 💕 в любви!"
        formatted = self.adapter._format_google_text(text_with_emojis)
        
        # Should remove emojis and clean up for speech
        assert "⭐" not in formatted
        assert "💕" not in formatted
        assert "гороскоп" in formatted
        assert "star" in formatted  # ⭐ should be replaced with "star"
        assert "love" in formatted  # 💕 should be replaced with "love"
        assert "успех" in formatted
        assert "любви" in formatted
    
    def test_final_response_on_end_session(self):
        """Test that final response is used when end_session is True."""
        from app.models.platform_models import UniversalResponse
        
        universal_response = UniversalResponse(
            text="До свидания! Пусть звёзды ведут вас к счастью!",
            tts="До свидания! Пусть звёзды ведут вас к счастью!",
            end_session=True
        )
        
        google_response = self.adapter.from_universal_response(universal_response)
        
        assert "expect_user_response" in google_response
        assert not google_response["expect_user_response"]
        
        assert "final_response" in google_response
        assert "rich_response" in google_response["final_response"]