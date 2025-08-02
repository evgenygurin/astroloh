"""
End-to-end workflow scenario tests.
"""
import pytest
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.dialog_handler import DialogHandler
from app.services.conversation_manager import ConversationManager
from app.services.dialog_flow_manager import DialogFlowManager, DialogState
from app.models.yandex_models import (
    YandexRequest, YandexSession, YandexUser, YandexRequestData, YandexIntent
)


class TestWorkflowScenarios:
    """End-to-end workflow scenario tests."""
    
    def setup_method(self):
        """Setup before each test."""
        self.dialog_handler = DialogHandler()
        self.conversation_manager = ConversationManager()
        self.dialog_flow_manager = DialogFlowManager()
    
    def create_mock_request(self, command: str, user_id: str = "test_user", 
                          session_id: str = "test_session") -> YandexRequest:
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
                session_id=session_id,
                skill_id="test_skill",
                user_id=user_id,
                user=YandexUser(user_id=user_id),
                application=MagicMock(),
                new=False
            ),
            version="1.0"
        )
    
    @pytest.mark.asyncio
    async def test_complete_horoscope_workflow(self):
        """Test complete horoscope request workflow."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            horoscope_generator=AsyncMock()
        ) as mocks:
            
            # Setup mocks
            mock_context = MagicMock()
            mock_context.personalization_level = 50
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Step 1: User greeting
            greeting_request = self.create_mock_request("привет")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.GREETING, {}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.GREETING
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['response_formatter'].format_greeting_response.return_value = MagicMock()
            
            greeting_response = await self.dialog_handler.handle_request(greeting_request, mock_db)
            assert greeting_response is not None
            
            # Step 2: User requests horoscope
            horoscope_request = self.create_mock_request("мой гороскоп на сегодня")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PERSONAL_HOROSCOPE, {"period": "today"}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_HOROSCOPE
            
            mock_horoscope = {
                "prediction": "Отличный день для новых начинаний!",
                "lucky_numbers": [7, 14, 21],
                "lucky_color": "синий"
            }
            mocks['horoscope_generator'].generate_personal_horoscope.return_value = mock_horoscope
            mocks['response_formatter'].format_horoscope_response.return_value = MagicMock()
            
            horoscope_response = await self.dialog_handler.handle_request(horoscope_request, mock_db)
            assert horoscope_response is not None
            
            # Verify workflow
            assert mocks['horoscope_generator'].generate_personal_horoscope.called
            assert mocks['response_formatter'].format_horoscope_response.called
    
    @pytest.mark.asyncio
    async def test_natal_chart_data_collection_workflow(self):
        """Test natal chart data collection workflow."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            natal_chart=AsyncMock(),
            user_manager=AsyncMock()
        ) as mocks:
            
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Step 1: User requests natal chart
            request1 = self.create_mock_request("составь мою натальную карту")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.NATAL_CHART, {}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.COLLECTING_BIRTH_DATA
            mocks['response_formatter'].format_clarification_response.return_value = MagicMock()
            
            response1 = await self.dialog_handler.handle_request(request1, mock_db)
            assert response1 is not None
            
            # Step 2: User provides birth date
            request2 = self.create_mock_request("15 мая 1990 года")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PROVIDE_DATA, {"birth_date": "1990-05-15"}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.COLLECTING_BIRTH_DATA
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.COLLECTING_BIRTH_TIME
            
            response2 = await self.dialog_handler.handle_request(request2, mock_db)
            assert response2 is not None
            
            # Step 3: User provides birth time
            request3 = self.create_mock_request("в 14:30")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PROVIDE_DATA, {"birth_time": "14:30"}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.COLLECTING_BIRTH_TIME
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.COLLECTING_BIRTH_LOCATION
            
            response3 = await self.dialog_handler.handle_request(request3, mock_db)
            assert response3 is not None
            
            # Step 4: User provides birth location
            request4 = self.create_mock_request("в Москве")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PROVIDE_DATA, {"birth_location": "Moscow"}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.COLLECTING_BIRTH_LOCATION
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_NATAL_CHART
            
            mock_natal_chart = {
                "planets": {"sun": {"sign": "taurus", "house": 2}},
                "interpretation": {"personality": "Стабильная и целеустремленная личность"}
            }
            mocks['natal_chart'].calculate_natal_chart.return_value = mock_natal_chart
            mocks['response_formatter'].format_natal_chart_response.return_value = MagicMock()
            
            response4 = await self.dialog_handler.handle_request(request4, mock_db)
            assert response4 is not None
            
            # Verify complete workflow
            assert mocks['natal_chart'].calculate_natal_chart.called
            assert mocks['user_manager'].store_birth_data.called
    
    @pytest.mark.asyncio
    async def test_compatibility_analysis_workflow(self):
        """Test compatibility analysis workflow."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            astrology_calculator=AsyncMock()
        ) as mocks:
            
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Step 1: User asks about compatibility
            request1 = self.create_mock_request("совместимость льва и весов")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.COMPATIBILITY, {"sign1": "leo", "sign2": "libra"}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_COMPATIBILITY
            
            mock_compatibility = {
                "score": 85,
                "description": "Отличная совместимость!",
                "strengths": ["понимание", "гармония"],
                "challenges": ["разные темпераменты"]
            }
            mocks['astrology_calculator'].calculate_compatibility.return_value = mock_compatibility
            mocks['response_formatter'].format_compatibility_response.return_value = MagicMock()
            
            response1 = await self.dialog_handler.handle_request(request1, mock_db)
            assert response1 is not None
            
            # Step 2: User asks for more details
            request2 = self.create_mock_request("расскажи подробнее")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.MORE_INFO, {}, 0.8
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.PROVIDING_COMPATIBILITY
            mocks['response_formatter'].format_detailed_compatibility_response.return_value = MagicMock()
            
            response2 = await self.dialog_handler.handle_request(request2, mock_db)
            assert response2 is not None
            
            # Verify workflow
            assert mocks['astrology_calculator'].calculate_compatibility.called
            assert mocks['response_formatter'].format_compatibility_response.called
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error recovery workflow."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            error_recovery=AsyncMock()
        ) as mocks:
            
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Step 1: User provides invalid input
            request1 = self.create_mock_request("гороскоп на 32 января")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PERSONAL_HOROSCOPE, {"date": "invalid"}, 0.7
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            
            # Simulate validation error
            mocks['dialog_flow_manager'].process_intent.side_effect = ValueError("Invalid date")
            mocks['error_recovery'].handle_error.return_value = MagicMock()
            
            response1 = await self.dialog_handler.handle_request(request1, mock_db)
            assert response1 is not None
            
            # Step 2: User provides corrected input
            request2 = self.create_mock_request("гороскоп на сегодня")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PERSONAL_HOROSCOPE, {"period": "today"}, 0.9
            )
            mocks['dialog_flow_manager'].process_intent.side_effect = None  # Reset error
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_HOROSCOPE
            mocks['response_formatter'].format_horoscope_response.return_value = MagicMock()
            
            response2 = await self.dialog_handler.handle_request(request2, mock_db)
            assert response2 is not None
            
            # Verify error recovery was used
            assert mocks['error_recovery'].handle_error.called
    
    @pytest.mark.asyncio
    async def test_multi_user_session_workflow(self):
        """Test handling multiple users in parallel sessions."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            horoscope_generator=AsyncMock()
        ) as mocks:
            
            # Setup different contexts for different users
            def get_context_side_effect(user_id, db):
                mock_context = MagicMock()
                if user_id == "user1":
                    mock_context.personalization_level = 20
                    mock_context.preferences = {"zodiac_sign": "leo"}
                else:
                    mock_context.personalization_level = 80
                    mock_context.preferences = {"zodiac_sign": "virgo", "theme": "love"}
                return mock_context
            
            mocks['conversation_manager'].get_conversation_context.side_effect = get_context_side_effect
            
            # User 1 requests horoscope
            request1 = self.create_mock_request("мой гороскоп", user_id="user1", session_id="session1")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.PERSONAL_HOROSCOPE, {"period": "today"}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.PROVIDING_HOROSCOPE
            mocks['horoscope_generator'].generate_personal_horoscope.return_value = {
                "prediction": "Horoscope for Leo"
            }
            mocks['response_formatter'].format_horoscope_response.return_value = MagicMock()
            
            response1 = await self.dialog_handler.handle_request(request1, mock_db)
            assert response1 is not None
            
            # User 2 requests horoscope (different session)
            request2 = self.create_mock_request("мой гороскоп", user_id="user2", session_id="session2")
            
            response2 = await self.dialog_handler.handle_request(request2, mock_db)
            assert response2 is not None
            
            # Verify both users were handled with their own contexts
            assert mocks['conversation_manager'].get_conversation_context.call_count == 2
            assert mocks['horoscope_generator'].generate_personal_horoscope.call_count == 2
    
    @pytest.mark.asyncio
    async def test_conversation_state_persistence_workflow(self):
        """Test conversation state persistence across multiple interactions."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock()
        ) as mocks:
            
            mock_context = MagicMock()
            mock_context.conversation_count = 5
            mock_context.preferences = {"favorite_topic": "love"}
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # Track dialog state changes
            dialog_states = []
            
            def track_state_change(intent, entities, context):
                new_state = DialogState.PROVIDING_HOROSCOPE  # Simplified
                dialog_states.append(new_state)
                return new_state
            
            mocks['dialog_flow_manager'].process_intent.side_effect = track_state_change
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            
            # Multiple interactions
            interactions = [
                ("привет", YandexIntent.GREETING),
                ("мой гороскоп", YandexIntent.PERSONAL_HOROSCOPE),
                ("спасибо", YandexIntent.THANKS),
                ("до свидания", YandexIntent.GOODBYE)
            ]
            
            for command, expected_intent in interactions:
                request = self.create_mock_request(command)
                mocks['intent_recognition'].recognize_intent.return_value = (
                    expected_intent, {}, 0.9
                )
                mocks['response_formatter'].format_greeting_response.return_value = MagicMock()
                mocks['response_formatter'].format_horoscope_response.return_value = MagicMock()
                mocks['response_formatter'].format_thanks_response.return_value = MagicMock()
                mocks['response_formatter'].format_goodbye_response.return_value = MagicMock()
                
                response = await self.dialog_handler.handle_request(request, mock_db)
                assert response is not None
            
            # Verify conversation state was maintained
            assert len(dialog_states) == len(interactions)
            assert mocks['conversation_manager'].update_conversation_context.call_count == len(interactions)
    
    @pytest.mark.asyncio
    async def test_personalization_improvement_workflow(self):
        """Test that personalization improves over multiple interactions."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock()
        ) as mocks:
            
            # Simulate increasing personalization levels
            personalization_levels = [10, 25, 50, 75]
            call_count = 0
            
            def get_context_with_increasing_personalization(user_id, db):
                nonlocal call_count
                mock_context = MagicMock()
                mock_context.personalization_level = personalization_levels[min(call_count, 3)]
                mock_context.conversation_count = call_count + 1
                call_count += 1
                return mock_context
            
            mocks['conversation_manager'].get_conversation_context.side_effect = \
                get_context_with_increasing_personalization
            
            # Multiple interactions
            for i in range(4):
                request = self.create_mock_request(f"тест {i}")
                mocks['intent_recognition'].recognize_intent.return_value = (
                    YandexIntent.GREETING, {}, 0.9
                )
                mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
                mocks['dialog_flow_manager'].process_intent.return_value = DialogState.GREETING
                mocks['response_formatter'].format_greeting_response.return_value = MagicMock()
                
                response = await self.dialog_handler.handle_request(request, mock_db)
                assert response is not None
            
            # Verify personalization increased
            assert call_count == 4
            assert mocks['conversation_manager'].get_conversation_context.call_count == 4
    
    @pytest.mark.asyncio
    async def test_data_privacy_workflow(self):
        """Test data privacy and GDPR compliance workflow."""
        mock_db = AsyncMock()
        
        with patch.multiple(
            self.dialog_handler,
            intent_recognition=AsyncMock(),
            conversation_manager=AsyncMock(),
            response_formatter=AsyncMock(),
            dialog_flow_manager=AsyncMock(),
            user_manager=AsyncMock(),
            gdpr_compliance=AsyncMock()
        ) as mocks:
            
            mock_context = MagicMock()
            mocks['conversation_manager'].get_conversation_context.return_value = mock_context
            
            # User requests data deletion
            request = self.create_mock_request("удали мои данные")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.DELETE_DATA, {}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.CONFIRMING_DATA_DELETION
            mocks['response_formatter'].format_data_deletion_confirmation.return_value = MagicMock()
            
            response1 = await self.dialog_handler.handle_request(request, mock_db)
            assert response1 is not None
            
            # User confirms deletion
            confirmation_request = self.create_mock_request("да, удали")
            mocks['intent_recognition'].recognize_intent.return_value = (
                YandexIntent.CONFIRM, {}, 0.9
            )
            mocks['dialog_flow_manager'].get_current_state.return_value = DialogState.CONFIRMING_DATA_DELETION
            mocks['dialog_flow_manager'].process_intent.return_value = DialogState.WAITING_FOR_REQUEST
            mocks['gdpr_compliance'].process_deletion_request.return_value = True
            mocks['response_formatter'].format_data_deletion_success.return_value = MagicMock()
            
            response2 = await self.dialog_handler.handle_request(confirmation_request, mock_db)
            assert response2 is not None
            
            # Verify GDPR compliance was handled
            assert mocks['gdpr_compliance'].process_deletion_request.called