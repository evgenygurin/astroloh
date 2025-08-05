#!/usr/bin/env python3
"""Debug script to check complete dialog flow."""

import asyncio
from unittest.mock import patch, MagicMock

from app.services.dialog_handler import DialogHandler
from app.services.dialog_flow_manager import DialogState
from app.models.yandex_models import (
    YandexRequestData,
    YandexRequestModel,
    YandexRequestMeta,
    YandexSession,
    YandexRequestType,
    UserContext,
    YandexResponse,
)

def create_mock_request(command: str, user_id: str = "test_user", session_id: str = "test_session") -> YandexRequestModel:
    """Create mock Yandex request."""
    return YandexRequestModel(
        meta=YandexRequestMeta(
            locale="ru-RU",
            timezone="UTC",
            client_id="test"
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

async def test_horoscope_flow():
    dialog_handler = DialogHandler()
    request = create_mock_request("мой гороскоп")
    
    # Mock all dependencies
    with patch.object(dialog_handler.session_manager, 'get_user_context') as mock_get_context, \
         patch.object(dialog_handler.session_manager, 'set_awaiting_data') as mock_set_awaiting, \
         patch.object(dialog_handler.conversation_manager, 'process_conversation') as mock_conversation, \
         patch.object(dialog_handler.response_formatter, 'format_horoscope_request_response') as mock_format:
        
        # Setup mocks with real UserContext
        user_context = UserContext(
            user_id="test_user", 
            birth_date=None, 
            zodiac_sign=None
        )
        mock_get_context.return_value = user_context
        mock_conversation.return_value = (DialogState.INITIAL, {})
        mock_format.return_value = YandexResponse(
            text="Для составления персонального гороскопа мне нужна ваша дата рождения."
        )
        
        print("About to call handle_request...")
        response = await dialog_handler.handle_request(request)
        
        print(f"Response: {response}")
        print(f"mock_get_context.called: {mock_get_context.called}")
        print(f"mock_conversation.called: {mock_conversation.called}")
        print(f"mock_set_awaiting.called: {mock_set_awaiting.called}")
        print(f"mock_format.called: {mock_format.called}")
        
        if mock_set_awaiting.call_args:
            print(f"set_awaiting_data call args: {mock_set_awaiting.call_args}")

if __name__ == "__main__":
    asyncio.run(test_horoscope_flow())