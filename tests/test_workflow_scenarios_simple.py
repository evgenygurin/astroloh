"""
Упрощенные end-to-end workflow тесты.
"""

from unittest.mock import patch

import pytest

from app.models.yandex_models import (
    UserContext,
    YandexRequestData,
    YandexRequestMeta,
    YandexRequestModel,
    YandexRequestType,
    YandexResponse,
    YandexSession,
)
from app.services.dialog_flow_manager import DialogState
from app.services.dialog_handler import DialogHandler


class TestSimpleWorkflowScenarios:
    """Упрощенные workflow тесты."""

    def setup_method(self):
        """Setup before each test."""
        self.dialog_handler = DialogHandler()

    def create_mock_request(
        self,
        command: str,
        user_id: str = "test_user",
        session_id: str = "test_session",
    ) -> YandexRequestModel:
        """Create mock Yandex request."""
        return YandexRequestModel(
            meta=YandexRequestMeta(
                locale="ru-RU", timezone="UTC", client_id="test"
            ),
            request=YandexRequestData(
                command=command,
                original_utterance=command,
                type=YandexRequestType.SIMPLE_UTTERANCE,
            ),
            session=YandexSession(
                message_id=1,
                session_id=session_id,
                skill_id="test_skill",
                user_id=user_id,
                new=False,
            ),
            version="1.0",
        )

    @pytest.mark.asyncio
    async def test_greeting_workflow(self):
        """Test simple greeting workflow."""
        request = self.create_mock_request("привет")

        # Mock the session manager to prevent database calls
        with (
            patch.object(
                self.dialog_handler.session_manager, "get_user_context"
            ) as mock_get_context,
            patch.object(
                self.dialog_handler.session_manager, "is_new_session"
            ) as mock_is_new,
            patch.object(
                self.dialog_handler.session_manager, "update_user_context"
            ) as mock_update,
            patch.object(
                self.dialog_handler.conversation_manager,
                "process_conversation",
            ) as mock_conversation,
        ):
            # Setup mocks with real UserContext
            user_context = UserContext(user_id="test_user")
            mock_get_context.return_value = user_context
            mock_is_new.return_value = True
            mock_update.return_value = None
            mock_conversation.return_value = (DialogState.INITIAL, {})

            response = await self.dialog_handler.handle_request(request)

            assert response is not None
            assert hasattr(response, "response")
            assert response.response.text is not None
            assert len(response.response.text) > 0

    @pytest.mark.asyncio
    async def test_horoscope_request_workflow(self):
        """Test horoscope request workflow."""
        request = self.create_mock_request("мой гороскоп")

        # Mock all dependencies
        with (
            patch.object(
                self.dialog_handler.session_manager, "get_user_context"
            ) as mock_get_context,
            patch.object(
                self.dialog_handler.session_manager, "set_awaiting_data"
            ) as mock_set_awaiting,
            patch.object(
                self.dialog_handler.session_manager, "is_new_session"
            ) as mock_is_new,
            patch.object(
                self.dialog_handler.conversation_manager,
                "process_conversation",
            ) as mock_conversation,
            patch.object(
                self.dialog_handler.response_formatter,
                "format_horoscope_request_response",
            ) as mock_format,
        ):
            # Setup mocks with real UserContext
            user_context = UserContext(
                user_id="test_user", birth_date=None, zodiac_sign=None
            )
            mock_get_context.return_value = user_context
            mock_is_new.return_value = False
            mock_conversation.return_value = (DialogState.INITIAL, {})
            mock_format.return_value = YandexResponse(
                text="Для составления персонального гороскопа мне нужна ваша дата рождения."
            )

            response = await self.dialog_handler.handle_request(request)

            assert response is not None
            assert mock_set_awaiting.called

    @pytest.mark.asyncio
    async def test_help_workflow(self):
        """Test help request workflow."""
        request = self.create_mock_request("помощь")

        with (
            patch.object(
                self.dialog_handler.session_manager, "get_user_context"
            ) as mock_get_context,
            patch.object(
                self.dialog_handler.session_manager, "is_new_session"
            ) as mock_is_new,
            patch.object(
                self.dialog_handler.conversation_manager,
                "process_conversation",
            ) as mock_conversation,
            patch.object(
                self.dialog_handler.response_formatter, "format_help_response"
            ) as mock_format,
        ):
            # Setup mocks with real UserContext
            user_context = UserContext(user_id="test_user")
            mock_get_context.return_value = user_context
            mock_is_new.return_value = False
            mock_conversation.return_value = (DialogState.INITIAL, {})
            mock_format.return_value = YandexResponse(
                text="Это навык астрологических прогнозов. Я могу составить ваш гороскоп, рассчитать совместимость или дать совет."
            )

            response = await self.dialog_handler.handle_request(request)

            assert response is not None
            assert mock_format.called
