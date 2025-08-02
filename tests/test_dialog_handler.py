"""
Tests for dialog handler functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.dialog_handler import DialogHandler
from app.models.yandex_models import (
    YandexRequestModel, YandexSession, YandexRequestData, YandexRequestMeta,
    YandexResponse, YandexIntent
)
from app.services.dialog_flow_manager import DialogState


class TestDialogHandler:
    """Tests for dialog handler."""
    
    def setup_method(self):
        """Setup before each test."""
        self.dialog_handler = DialogHandler()
    
    def create_mock_request(self, command: str = "привет", user_id: str = "test_user") -> YandexRequestModel:
        """Create mock Yandex request."""
        return YandexRequestModel(
            meta=YandexRequestMeta(
                locale="ru-RU",
                timezone="Europe/Moscow",
                client_id="test_client",
                interfaces={}
            ),
            request=YandexRequestData(
                command=command,
                original_utterance=command,
                type="SimpleUtterance",
                markup={},
                payload={}
            ),
            session=YandexSession(
                message_id=1,
                session_id="test_session",
                skill_id="test_skill",
                user_id=user_id,
                user={"user_id": user_id},
                application={},
                new=False
            ),
            version="1.0"
        )
    
    @pytest.mark.asyncio
    async def test_handle_request_greeting(self):
        """Test handling greeting request."""
        request = self.create_mock_request("привет")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognizer=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            from app.models.yandex_models import ProcessedRequest, UserContext
            mock_processed_request = ProcessedRequest(
                intent=YandexIntent.GREET,
                entities={},
                confidence=0.9,
                raw_text="привет",
                user_context=UserContext()
            )
            self.dialog_handler.intent_recognizer.recognize_intent.return_value = mock_processed_request
            
            # Mock conversation processing  
            self.dialog_handler.conversation_manager.process_conversation.return_value = (
                DialogState.INITIAL, {}
            )
            
            # Mock dialog flow
            self.dialog_handler.dialog_flow_manager.get_current_state.return_value = DialogState.INITIAL
            self.dialog_handler.dialog_flow_manager.process_intent.return_value = DialogState.INITIAL
            
            # Mock contextual response generation
            mock_response = YandexResponse(
                text="Привет! Я астролог Алиса."
            )
            self.dialog_handler._generate_contextual_response = AsyncMock(return_value=mock_response)
            
            result = await self.dialog_handler.handle_request(request)
            
            assert isinstance(result, YandexResponse)
            self.dialog_handler.intent_recognizer.recognize_intent.assert_called_once()
            self.dialog_handler.conversation_manager.process_conversation.assert_called_once()
            self.dialog_handler._generate_contextual_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request_horoscope(self):
        """Test handling horoscope request."""
        request = self.create_mock_request("мой гороскоп на сегодня")
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognizer=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            horoscope_generator=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            from app.models.yandex_models import ProcessedRequest, UserContext
            mock_processed_request = ProcessedRequest(
                intent=YandexIntent.HOROSCOPE,
                entities={"period": "today"},
                confidence=0.9,
                raw_text="мой гороскоп на сегодня",
                user_context=UserContext()
            )
            self.dialog_handler.intent_recognizer.recognize_intent.return_value = mock_processed_request
            
            # Mock conversation processing  
            self.dialog_handler.conversation_manager.process_conversation.return_value = (
                DialogState.PROVIDING_HOROSCOPE, {}
            )
            
            # Mock contextual response generation
            mock_response = YandexResponse(
                text="Отличный день для новых начинаний!"
            )
            self.dialog_handler._generate_contextual_response = AsyncMock(return_value=mock_response)
            
            result = await self.dialog_handler.handle_request(request)
            
            assert isinstance(result, YandexResponse)
            self.dialog_handler.intent_recognizer.recognize_intent.assert_called_once()
            self.dialog_handler.conversation_manager.process_conversation.assert_called_once()
            self.dialog_handler._generate_contextual_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request_compatibility(self):
        """Test handling compatibility request."""
        request = self.create_mock_request("совместимость льва и весов")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognizer=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            astro_calculator=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            from app.models.yandex_models import ProcessedRequest, UserContext
            mock_processed_request = ProcessedRequest(
                intent=YandexIntent.COMPATIBILITY,
                entities={"sign1": "leo", "sign2": "libra"},
                confidence=0.9,
                raw_text="совместимость льва и весов",
                user_context=UserContext()
            )
            self.dialog_handler.intent_recognizer.recognize_intent.return_value = mock_processed_request
            
            # Mock conversation processing  
            self.dialog_handler.conversation_manager.process_conversation.return_value = (
                DialogState.EXPLORING_COMPATIBILITY, {}
            )
            
            # Mock dialog flow
            self.dialog_handler.dialog_flow_manager.get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            self.dialog_handler.dialog_flow_manager.process_intent.return_value = DialogState.PROVIDING_COMPATIBILITY
            
            # Mock compatibility calculation
            mock_compatibility = {
                "score": 85,
                "description": "Отличная совместимость!",
                "strengths": ["понимание", "гармония"],
                "challenges": ["разные темпераменты"]
            }
            self.dialog_handler.astro_calculator.calculate_compatibility.return_value = mock_compatibility
            
            # Mock response formatting
            mock_response = YandexResponse(
                text="Mock response"
            )
            self.dialog_handler._generate_contextual_response = AsyncMock(return_value=mock_response)
            
            result = await self.dialog_handler.handle_request(request)
            
            assert isinstance(result, YandexResponse)
            self.dialog_handler.intent_recognizer.recognize_intent.assert_called_once()
            self.dialog_handler.conversation_manager.process_conversation.assert_called_once()
            self.dialog_handler._generate_contextual_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request_error_handling(self):
        """Test error handling in request processing."""
        request = self.create_mock_request("test command")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognizer=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            error_recovery_manager=AsyncMock()
            ) as mocks:
            
            # Mock intent recognition to raise an error
            self.dialog_handler.intent_recognizer.recognize_intent.side_effect = Exception("Test error")
            
            # Mock error recovery
            mock_error_response = YandexResponse(
                text="Произошла ошибка, попробуйте еще раз"
            )
            self.dialog_handler.error_recovery_manager.handle_error.return_value = (None, mock_error_response)
            
            result = await self.dialog_handler.handle_request(request)
            
            assert isinstance(result, YandexResponse)
            self.dialog_handler.intent_recognizer.recognize_intent.assert_called_once()
            self.dialog_handler.conversation_manager.process_conversation.assert_called_once()
            self.dialog_handler._generate_contextual_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_natal_chart_request(self):
        """Test handling natal chart request."""
        request = self.create_mock_request("составь мою натальную карту")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognizer=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            natal_chart_calculator=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            from app.models.yandex_models import ProcessedRequest, UserContext
            mock_processed_request = ProcessedRequest(
                intent=YandexIntent.NATAL_CHART,
                entities={},
                confidence=0.9,
                raw_text="составь мою натальную карту",
                user_context=UserContext()
            )
            self.dialog_handler.intent_recognizer.recognize_intent.return_value = mock_processed_request
            
            # Mock conversation processing  
            self.dialog_handler.conversation_manager.process_conversation.return_value = (
                DialogState.EXPLORING_COMPATIBILITY, {}
            )
            
            # Mock dialog flow
            self.dialog_handler.dialog_flow_manager.get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            self.dialog_handler.dialog_flow_manager.process_intent.return_value = DialogState.COLLECTING_BIRTH_DATA
            
            # Mock response formatting
            mock_response = YandexResponse(
                text="Mock response"
            )
            self.dialog_handler.response_formatter.format_clarification_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request)
            
            assert isinstance(result, YandexResponse)
            self.dialog_handler.response_formatter.format_clarification_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_lunar_calendar_request(self):
        """Test handling lunar calendar request."""
        request = self.create_mock_request("лунный календарь на сегодня")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognizer=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            lunar_calendar=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            from app.models.yandex_models import ProcessedRequest, UserContext
            mock_processed_request = ProcessedRequest(
                intent=YandexIntent.LUNAR_CALENDAR,
                entities={"date": "today"},
                confidence=0.9,
                raw_text="лунный календарь на сегодня",
                user_context=UserContext()
            )
            self.dialog_handler.intent_recognizer.recognize_intent.return_value = mock_processed_request
            
            # Mock conversation processing  
            self.dialog_handler.conversation_manager.process_conversation.return_value = (
                DialogState.EXPLORING_COMPATIBILITY, {}
            )
            
            # Mock dialog flow
            self.dialog_handler.dialog_flow_manager.get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            self.dialog_handler.dialog_flow_manager.process_intent.return_value = DialogState.PROVIDING_LUNAR_INFO
            
            # Mock lunar calendar data
            mock_lunar_data = {
                "lunar_day": 15,
                "phase": "Full Moon",
                "recommendations": ["Время для завершения дел"],
                "energy_level": 90
            }
            self.dialog_handler.lunar_calendar.get_lunar_day_info.return_value = mock_lunar_data
            
            # Mock response formatting
            mock_response = YandexResponse(
                text="Mock response"
            )
            self.dialog_handler.response_formatter.format_lunar_calendar_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request)
            
            assert isinstance(result, YandexResponse)
            self.dialog_handler.lunar_calendar.get_lunar_day_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_help_request(self):
        """Test handling help request."""
        request = self.create_mock_request("помощь")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognizer=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            from app.models.yandex_models import ProcessedRequest, UserContext
            mock_processed_request = ProcessedRequest(
                intent=YandexIntent.HELP,
                entities={},
                confidence=0.9,
                raw_text="помощь",
                user_context=UserContext()
            )
            self.dialog_handler.intent_recognizer.recognize_intent.return_value = mock_processed_request
            
            # Mock conversation processing  
            self.dialog_handler.conversation_manager.process_conversation.return_value = (
                DialogState.EXPLORING_COMPATIBILITY, {}
            )
            
            # Mock dialog flow
            self.dialog_handler.dialog_flow_manager.get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            
            # Mock response formatting
            mock_response = YandexResponse(
                text="Mock response"
            )
            self.dialog_handler._generate_contextual_response = AsyncMock(return_value=mock_response)
            
            result = await self.dialog_handler.handle_request(request)
            
            assert isinstance(result, YandexResponse)
            self.dialog_handler.intent_recognizer.recognize_intent.assert_called_once()
            self.dialog_handler.conversation_manager.process_conversation.assert_called_once()
            self.dialog_handler._generate_contextual_response.assert_called_once()
    
    def test_log_interaction(self):
        """Test interaction logging."""
        request = self.create_mock_request("test command")
        response = YandexResponse(
            text="test response"
        )
        
        # Should not raise any exceptions
        self.dialog_handler.log_interaction(request, response, "test_intent", 0.9)
        assert True  # If we get here, logging worked
    
    def test_extract_user_context(self):
        """Test user context extraction."""
        request = self.create_mock_request("привет")
        
        context = self.dialog_handler.extract_user_context(request)
        
        assert "user_id" in context
        assert "session_id" in context
        assert context["user_id"] == "test_user"
        assert context["session_id"] == "test_session"