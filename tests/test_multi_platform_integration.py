"""
Tests for multi-platform integration functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.platform_models import Platform, UniversalRequest, UniversalResponse
from app.services.google_adapter import GoogleAssistantAdapter
from app.services.multi_platform_handler import multi_platform_handler
from app.services.telegram_adapter import TelegramAdapter
from app.services.yandex_adapter import YandexAdapter


class TestPlatformAdapters:
    """Test platform adapters for converting between formats."""
    
    def test_telegram_adapter_validation(self):
        """Test Telegram adapter request validation."""
        adapter = TelegramAdapter()
        
        # Valid request
        valid_request = {
            "update_id": 123,
            "message": {
                "message_id": 456,
                "from": {"id": 789, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567890,
                "text": "Hello"
            }
        }
        assert adapter.validate_request(valid_request) == True
        
        # Invalid request - missing update_id
        invalid_request = {
            "message": {
                "message_id": 456,
                "from": {"id": 789, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567890,
                "text": "Hello"
            }
        }
        assert adapter.validate_request(invalid_request) == False
        
        # Invalid request - no message or callback_query
        invalid_request2 = {"update_id": 123}
        assert adapter.validate_request(invalid_request2) == False
    
    def test_telegram_adapter_conversion(self):
        """Test Telegram adapter conversion to universal format."""
        adapter = TelegramAdapter()
        
        telegram_data = {
            "update_id": 123,
            "message": {
                "message_id": 456,
                "from": {
                    "id": 789,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {"id": 789, "type": "private"},
                "date": 1234567890,
                "text": "Привет"
            }
        }
        
        universal_request = adapter.to_universal_request(telegram_data)
        
        assert universal_request.platform == Platform.TELEGRAM
        assert universal_request.user_id == "789"
        assert universal_request.session_id == "789"
        assert universal_request.text == "Привет"
        assert universal_request.user_context["telegram_user"]["first_name"] == "Test"
    
    def test_google_adapter_validation(self):
        """Test Google Assistant adapter request validation."""
        adapter = GoogleAssistantAdapter()
        
        # Valid Dialogflow request
        valid_dialogflow_request = {
            "queryResult": {
                "queryText": "Hello",
                "intent": {
                    "name": "projects/test/agent/intents/123",
                    "displayName": "Default Welcome Intent"
                }
            },
            "session": "projects/test/agent/sessions/456"
        }
        assert adapter.validate_request(valid_dialogflow_request) == True
        
        # Valid Google Actions request
        valid_actions_request = {
            "user": {"userId": "test123"},
            "conversation": {"conversationId": "conv456", "type": "NEW"},
            "inputs": [{"intent": "actions.intent.MAIN"}]
        }
        assert adapter.validate_request(valid_actions_request) == True
        
        # Invalid request
        invalid_request = {"invalid": "data"}
        assert adapter.validate_request(invalid_request) == False
    
    def test_yandex_adapter_validation(self):
        """Test Yandex adapter request validation."""
        from app.models.yandex_models import (
            YandexApplication,
            YandexRequest,
            YandexRequestModel,
            YandexSession
        )
        
        adapter = YandexAdapter()
        
        # Create valid Yandex request
        application = YandexApplication(application_id="test")
        session = YandexSession(
            session_id="session123",
            message_id=1,
            user_id="user456",
            new=True,
            application=application
        )
        request = YandexRequest(
            command="привет",
            original_utterance="Привет",
            type="SimpleUtterance"
        )
        
        yandex_request = YandexRequestModel(
            meta={"locale": "ru-RU", "timezone": "UTC", "client_id": "test"},
            session=session,
            request=request,
            version="1.0"
        )
        
        assert adapter.validate_request(yandex_request) == True
        assert adapter.validate_request({"invalid": "data"}) == False


class TestMultiPlatformHandler:
    """Test the unified multi-platform handler."""
    
    @pytest.mark.asyncio
    async def test_handle_telegram_request(self):
        """Test handling Telegram requests through multi-platform handler."""
        # Create mock universal request
        universal_request = UniversalRequest(
            platform=Platform.TELEGRAM,
            user_id="123",
            session_id="session123",
            message_id="msg456",
            text="гороскоп",
            is_new_session=True,
            original_request={
                "update_id": 789,
                "message": {
                    "message_id": 456,
                    "from": {"id": 123, "first_name": "Test"},
                    "chat": {"id": 123, "type": "private"},
                    "text": "гороскоп"
                }
            }
        )
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Mock dialog handler
        with patch('app.services.multi_platform_handler.dialog_handler') as mock_dialog_handler:
            from app.models.yandex_models import YandexButton, YandexResponse, YandexResponseModel, YandexSession, YandexApplication
            
            # Mock Yandex response
            mock_yandex_response = YandexResponseModel(
                response=YandexResponse(
                    text="Для составления гороскопа назовите ваш знак зодиака.",
                    tts="Для составления гороскопа назовите ваш знак зодиака.",
                    buttons=[
                        YandexButton(title="Овен", payload={"sign": "овен"}),
                        YandexButton(title="Телец", payload={"sign": "телец"})
                    ],
                    end_session=False
                ),
                session=YandexSession(
                    session_id="session123",
                    message_id=1,
                    user_id="123",
                    new=True,
                    application=YandexApplication(application_id="test")
                ),
                version="1.0"
            )
            
            mock_dialog_handler.handle_request.return_value = mock_yandex_response
            
            # Test the handler
            response = await multi_platform_handler.handle_request(universal_request, mock_db)
            
            assert isinstance(response, UniversalResponse)
            assert "гороскопа" in response.text
            assert response.buttons is not None
            assert len(response.buttons) == 2
            assert response.buttons[0].title == "Овен"
    
    @pytest.mark.asyncio
    async def test_handle_google_request(self):
        """Test handling Google Assistant requests through multi-platform handler."""
        # Create mock universal request
        universal_request = UniversalRequest(
            platform=Platform.GOOGLE_ASSISTANT,
            user_id="google123",
            session_id="conv456",
            message_id="conv456",
            text="астрологический совет",
            is_new_session=False,
            original_request={
                "user": {"userId": "google123"},
                "conversation": {"conversationId": "conv456", "type": "ACTIVE"},
                "inputs": [{"intent": "horoscope.advice"}]
            }
        )
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Mock dialog handler
        with patch('app.services.multi_platform_handler.dialog_handler') as mock_dialog_handler:
            from app.models.yandex_models import YandexButton, YandexResponse, YandexResponseModel, YandexSession, YandexApplication
            
            # Mock Yandex response
            mock_yandex_response = YandexResponseModel(
                response=YandexResponse(
                    text="Астрологический совет дня: Сегодня звёзды советуют прислушаться к своей интуиции.",
                    tts="Астрологический совет дня: Сегодня звёзды советуют прислушаться к своей интуиции.",
                    buttons=[
                        YandexButton(title="Новый совет", payload={"action": "new_advice"}),
                        YandexButton(title="Гороскоп", payload={"action": "horoscope"})
                    ],
                    end_session=False
                ),
                session=YandexSession(
                    session_id="conv456",
                    message_id=1,
                    user_id="google123",
                    new=False,
                    application=YandexApplication(application_id="test")
                ),
                version="1.0"
            )
            
            mock_dialog_handler.handle_request.return_value = mock_yandex_response
            
            # Test the handler
            response = await multi_platform_handler.handle_request(universal_request, mock_db)
            
            assert isinstance(response, UniversalResponse)
            assert "совет" in response.text.lower()
            assert response.tts is not None
            assert response.buttons is not None
            assert len(response.buttons) == 2


class TestResponseConversion:
    """Test response conversion between formats."""
    
    def test_telegram_response_conversion(self):
        """Test converting universal response to Telegram format."""
        adapter = TelegramAdapter()
        
        universal_response = UniversalResponse(
            text="Ваш гороскоп на сегодня: отличный день для новых начинаний! ⭐",
            buttons=[
                {"title": "Завтра", "payload": {"period": "tomorrow"}},
                {"title": "Совместимость", "payload": {"action": "compatibility"}}
            ],
            end_session=False,
            platform_specific={
                "chat_id": "123456"
            }
        )
        
        telegram_response = adapter.from_universal_response(universal_response)
        
        assert "send_message" in telegram_response
        assert telegram_response["send_message"]["chat_id"] == 123456
        assert "гороскоп" in telegram_response["send_message"]["text"]
        assert "reply_markup" in telegram_response["send_message"]
        assert len(telegram_response["send_message"]["reply_markup"]["inline_keyboard"]) == 2
    
    def test_google_response_conversion(self):
        """Test converting universal response to Google format."""
        adapter = GoogleAssistantAdapter()
        
        universal_response = UniversalResponse(
            text="Ваш гороскоп: звёзды благоволят вам сегодня!",
            tts="Ваш гороскоп: звёзды благоволят вам сегодня!",
            buttons=[
                {"title": "Завтра", "payload": {"period": "tomorrow"}},
                {"title": "Совет дня", "payload": {"action": "advice"}}
            ],
            end_session=False
        )
        
        google_response = adapter.from_universal_response(universal_response)
        
        assert "expect_user_response" in google_response
        assert google_response["expect_user_response"] == True
        assert "rich_response" in google_response
        assert "items" in google_response["rich_response"]
        assert "suggestions" in google_response["rich_response"]
        assert len(google_response["rich_response"]["suggestions"]) == 2
    
    def test_yandex_response_conversion(self):
        """Test converting universal response to Yandex format."""
        from app.models.yandex_models import YandexApplication, YandexSession
        
        adapter = YandexAdapter()
        
        universal_response = UniversalResponse(
            text="Добро пожаловать в мир астрологии!",
            tts="Добро пожаловать в мир астрологии!",
            buttons=[
                {"title": "Гороскоп", "payload": {"action": "horoscope"}},
                {"title": "Помощь", "payload": {"action": "help"}}
            ],
            end_session=False,
            platform_specific={
                "session": YandexSession(
                    session_id="test123",
                    message_id=1,
                    user_id="user456",
                    new=True,
                    application=YandexApplication(application_id="test")
                ),
                "version": "1.0"
            }
        )
        
        yandex_response = adapter.from_universal_response(universal_response)
        
        assert hasattr(yandex_response, 'response')
        assert yandex_response.response.text == "Добро пожаловать в мир астрологии!"
        assert yandex_response.response.tts == "Добро пожаловать в мир астрологии!"
        assert len(yandex_response.response.buttons) == 2
        assert yandex_response.response.end_session == False