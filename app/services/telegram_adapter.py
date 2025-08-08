"""
Telegram platform adapter for converting between Telegram and universal formats.
"""

import logging
from typing import Any, Dict

from app.models.platform_models import (
    MessageType,
    Platform,
    PlatformAdapter,
    UniversalRequest,
    UniversalResponse,
)
from app.models.telegram_models import (
    TelegramInlineKeyboard,
    TelegramInlineKeyboardMarkup,
    TelegramSendMessage,
    TelegramSendPhoto,
    TelegramUpdate,
)

logger = logging.getLogger(__name__)


class TelegramAdapter(PlatformAdapter):
    """Telegram platform adapter."""

    def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate Telegram webhook request."""
        try:
            if not isinstance(request, dict):
                return False

            if "update_id" not in request:
                return False

            # Must have either message or callback_query
            if "message" not in request and "callback_query" not in request:
                return False

            return True
        except Exception as e:
            logger.error(f"Telegram request validation error: {e}")
            return False

    def to_universal_request(
        self, telegram_data: Dict[str, Any]
    ) -> UniversalRequest:
        """Convert Telegram update to universal request format."""
        try:
            update = TelegramUpdate(**telegram_data)

            if update.message:
                # Handle regular message
                message = update.message
                text = message.text or ""
                user_id = str(message.user.id)
                chat_id = str(message.chat.id)
                message_id = str(message.message_id)

                # Determine message type
                message_type = MessageType.TEXT
                if message.photo:
                    message_type = MessageType.IMAGE
                elif message.document:
                    message_type = MessageType.DOCUMENT
                elif message.location:
                    message_type = MessageType.LOCATION

                # Build user context
                user_context = {
                    "telegram_user": {
                        "id": message.user.id,
                        "first_name": message.user.first_name,
                        "last_name": message.user.last_name,
                        "username": message.user.username,
                        "language_code": message.user.language_code,
                    },
                    "chat": {
                        "id": message.chat.id,
                        "type": message.chat.type,
                        "title": message.chat.title,
                    },
                }

                return UniversalRequest(
                    platform=Platform.TELEGRAM,
                    user_id=user_id,
                    session_id=chat_id,  # Use chat_id as session_id for Telegram
                    message_id=message_id,
                    text=text,
                    message_type=message_type,
                    is_new_session=True,  # Always treat as new for now
                    user_context=user_context,
                    original_request=telegram_data,
                )

            elif update.callback_query:
                # Handle callback query (inline button press)
                callback = update.callback_query
                text = callback.data or ""
                user_id = str(callback.user.id)
                chat_id = str(
                    callback.message.chat.id
                    if callback.message
                    else callback.user.id
                )
                message_id = str(
                    callback.message.message_id
                    if callback.message
                    else callback.id
                )

                user_context = {
                    "telegram_user": {
                        "id": callback.user.id,
                        "first_name": callback.user.first_name,
                        "last_name": callback.user.last_name,
                        "username": callback.user.username,
                        "language_code": callback.user.language_code,
                    },
                    "callback_query": {
                        "id": callback.id,
                        "data": callback.data,
                    },
                }

                return UniversalRequest(
                    platform=Platform.TELEGRAM,
                    user_id=user_id,
                    session_id=chat_id,
                    message_id=message_id,
                    text=text,
                    message_type=MessageType.TEXT,
                    is_new_session=False,
                    user_context=user_context,
                    original_request=telegram_data,
                )

            raise ValueError(
                "No valid message or callback_query in Telegram update"
            )

        except Exception as e:
            logger.error(f"Error converting Telegram request: {e}")
            raise

    def from_universal_response(
        self, universal_response: UniversalResponse
    ) -> Dict[str, Any]:
        """Convert universal response to Telegram format."""
        try:
            chat_id = None
            callback_query_id = None

            # Extract chat_id from platform_specific data
            if universal_response.platform_specific:
                chat_id = universal_response.platform_specific.get("chat_id")
                callback_query_id = universal_response.platform_specific.get(
                    "callback_query_id"
                )

            if not chat_id:
                raise ValueError("chat_id is required for Telegram response")

            # Prepare response
            response_data = {}

            # Handle callback query response if present
            if callback_query_id:
                response_data["answer_callback_query"] = {
                    "callback_query_id": callback_query_id,
                    "text": "✅",
                    "show_alert": False,
                }

            # Prepare inline keyboard if buttons are present
            reply_markup = None
            if universal_response.buttons:
                keyboard_rows = []
                for button in universal_response.buttons:
                    keyboard_button = TelegramInlineKeyboard(
                        text=button.title,
                        callback_data=str(button.payload)
                        if button.payload
                        else button.title,
                        url=button.url,
                    )
                    keyboard_rows.append([keyboard_button])

                reply_markup = TelegramInlineKeyboardMarkup(
                    inline_keyboard=keyboard_rows
                )

            # Send photo if image_url is provided
            if universal_response.image_url:
                send_photo = TelegramSendPhoto(
                    chat_id=int(chat_id),
                    photo=universal_response.image_url,
                    caption=universal_response.image_caption
                    or universal_response.text,
                    reply_markup=reply_markup,
                )
                response_data["send_photo"] = send_photo.dict()
            else:
                # Send text message
                send_message = TelegramSendMessage(
                    chat_id=int(chat_id),
                    text=self._format_telegram_text(universal_response.text),
                    reply_markup=reply_markup,
                )
                response_data["send_message"] = send_message.dict()

            return response_data

        except Exception as e:
            logger.error(f"Error converting to Telegram response: {e}")
            raise

    def _format_telegram_text(self, text: str) -> str:
        """Format text for Telegram HTML parsing."""
        # Remove emoji-style formatting and replace with Telegram HTML
        formatted = text

        # Replace common formatting
        formatted = formatted.replace("⭐", "⭐")  # Keep stars as is
        formatted = formatted.replace("💕", "💕")  # Keep hearts as is

        # Ensure text is not too long (Telegram limit is 4096 chars)
        if len(formatted) > 4090:
            formatted = formatted[:4087] + "..."

        return formatted
