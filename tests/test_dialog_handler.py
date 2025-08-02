"""
Tests for dialog handler functionality.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.dialog_handler import DialogHandler
from app.models.yandex_models import (
    YandexRequest, YandexSession, YandexUser, YandexRequestData, 
    YandexResponse, YandexIntent
)
from app.services.dialog_flow_manager import DialogState


class TestDialogHandler:
    """Tests for dialog handler."""
    
    def setup_method(self):
        """Setup before each test."""
        self.dialog_handler = DialogHandler()
    
    def create_mock_request(self, command: str = "привет", user_id: str = "test_user") -> YandexRequest:
        """Create mock Yandex request."""
        return YandexRequest(
            meta=MagicMock(),
            request=YandexRequestData(
                command=command,
                original_utterance=command,
                type="SimpleUtterance",
                markup=MagicMock(),
                payload={}
            ),
            session=YandexSession(
                message_id=1,
                session_id="test_session",
                skill_id="test_skill",
                user_id=user_id,
                user=YandexUser(user_id=user_id),
                application=MagicMock(),
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
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.GREETING, {}, 0.9
            )
            
            # Mock conversation context
            mock_context = MagicMock()
            mock_context.personalization_level = 50
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Mock dialog flow
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.GREETING
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.WAITING_FOR_REQUEST
            
            # Mock response formatting
            mock_response = YandexResponse(
                response=MagicMock(),
                session=MagicMock(),
                version="1.0"
            )
            mocks['response_formatter'].format_greeting_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request, mock_db)
            
            assert isinstance(result, YandexResponse)
            mocks['intent_recognition'].recognize_intent.assert_called_once()
            mocks['conversation_manager'].get_conversation_context.assert_called_once()
            mocks['response_formatter'].format_greeting_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request_horoscope(self):
        """Test handling horoscope request."""
        request = self.create_mock_request("мой гороскоп на сегодня")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            horoscope_generator=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PERSONAL_HOROSCOPE, {"period": "today"}, 0.9
            )
            
            # Mock conversation context
            mock_context = MagicMock()
            mock_context.personalization_level = 70
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Mock dialog flow
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_HOROSCOPE
            
            # Mock horoscope generation
            mock_horoscope = {
                "prediction": "Отличный день для новых начинаний!",
                "lucky_numbers": [7, 14, 21],
                "lucky_color": "синий"
            }
            mocks['horoscope_generator'].generate_personal_horoscope.return_value = mock_horoscope
            
            # Mock response formatting
            mock_response = YandexResponse(
                response=MagicMock(),
                session=MagicMock(),
                version="1.0"
            )
            mocks['response_formatter'].format_horoscope_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request, mock_db)
            
            assert isinstance(result, YandexResponse)
            mocks['horoscope_generator'].generate_personal_horoscope.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request_compatibility(self):
        """Test handling compatibility request."""
        request = self.create_mock_request("совместимость льва и весов")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            astrology_calculator=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.COMPATIBILITY, {"sign1": "leo", "sign2": "libra"}, 0.9
            )
            
            # Mock conversation context
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Mock dialog flow
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_COMPATIBILITY
            
            # Mock compatibility calculation
            mock_compatibility = {
                "score": 85,
                "description": "Отличная совместимость!",
                "strengths": ["понимание", "гармония"],
                "challenges": ["разные темпераменты"]
            }
            mocks['astrology_calculator'].calculate_compatibility.return_value = mock_compatibility
            
            # Mock response formatting
            mock_response = YandexResponse(
                response=MagicMock(),
                session=MagicMock(),
                version="1.0"
            )
            mocks['response_formatter'].format_compatibility_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request, mock_db)
            
            assert isinstance(result, YandexResponse)
            mocks['astrology_calculator'].calculate_compatibility.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_request_error_handling(self):
        """Test error handling in request processing."""
        request = self.create_mock_request("test command")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            error_recovery=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition to raise an error
            mocks['intent_recognition'].recognize_intent.side_effect = Exception("Test error")
            
            # Mock error recovery
            mock_error_response = YandexResponse(
                response=MagicMock(),
                session=MagicMock(),
                version="1.0"
            )
            mocks['error_recovery'].handle_error.return_value = mock_error_response
            
            result = await self.dialog_handler.handle_request(request, mock_db)
            
            assert isinstance(result, YandexResponse)
            mocks['error_recovery'].handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_natal_chart_request(self):
        """Test handling natal chart request."""
        request = self.create_mock_request("составь мою натальную карту")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            natal_chart=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.NATAL_CHART, {}, 0.9
            )
            
            # Mock conversation context
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Mock dialog flow
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.COLLECTING_BIRTH_DATA
            
            # Mock response formatting
            mock_response = YandexResponse(
                response=MagicMock(),
                session=MagicMock(),
                version="1.0"
            )
            mocks['response_formatter'].format_clarification_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request, mock_db)
            
            assert isinstance(result, YandexResponse)
            mocks['response_formatter'].format_clarification_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_lunar_calendar_request(self):
        """Test handling lunar calendar request."""
        request = self.create_mock_request("лунный календарь на сегодня")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            lunar_calendar=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.LUNAR_CALENDAR, {"date": "today"}, 0.9
            )
            
            # Mock conversation context
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Mock dialog flow
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_LUNAR_INFO
            
            # Mock lunar calendar data
            mock_lunar_data = {
                "lunar_day": 15,
                "phase": "Full Moon",
                "recommendations": ["Время для завершения дел"],
                "energy_level": 90
            }
            mocks['lunar_calendar'].get_lunar_day_info.return_value = mock_lunar_data
            
            # Mock response formatting
            mock_response = YandexResponse(
                response=MagicMock(),
                session=MagicMock(),
                version="1.0"
            )
            mocks['response_formatter'].format_lunar_calendar_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request, mock_db)
            
            assert isinstance(result, YandexResponse)
            mocks['lunar_calendar'].get_lunar_day_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_help_request(self):
        """Test handling help request."""
        request = self.create_mock_request("помощь")
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock()
        ) as mocks:
            
            # Mock intent recognition
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.HELP, {}, 0.9
            )
            
            # Mock conversation context
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Mock dialog flow
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            
            # Mock response formatting
            mock_response = YandexResponse(
                response=MagicMock(),
                session=MagicMock(),
                version="1.0"
            )
            mocks['response_formatter'].format_help_response.return_value = mock_response
            
            result = await self.dialog_handler.handle_request(request, mock_db)
            
            assert isinstance(result, YandexResponse)
            mocks['response_formatter'].format_help_response.assert_called_once()
    
    def test_log_interaction(self):
        """Test interaction logging."""
        request = self.create_mock_request("test command")
        response = YandexResponse(
            response=MagicMock(),
            session=MagicMock(),
            version="1.0"
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