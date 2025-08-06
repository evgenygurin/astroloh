"""
Telegram-specific models and data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    """Telegram user model."""

    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    """Telegram chat model."""

    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramMessage(BaseModel):
    """Telegram message model."""

    message_id: int
    user: TelegramUser = Field(alias="from")
    chat: TelegramChat
    date: int
    text: Optional[str] = None
    photo: Optional[List[Dict[str, Any]]] = None
    document: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, float]] = None

    class Config:
        populate_by_name = True


class TelegramCallbackQuery(BaseModel):
    """Telegram callback query model."""

    id: str
    user: TelegramUser = Field(alias="from")
    message: Optional[TelegramMessage] = None
    inline_message_id: Optional[str] = None
    chat_instance: str
    data: Optional[str] = None

    class Config:
        populate_by_name = True


class TelegramUpdate(BaseModel):
    """Telegram update model."""

    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[TelegramCallbackQuery] = None


class TelegramInlineKeyboard(BaseModel):
    """Telegram inline keyboard model."""

    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None


class TelegramInlineKeyboardMarkup(BaseModel):
    """Telegram inline keyboard markup model."""

    inline_keyboard: List[List[TelegramInlineKeyboard]]


class TelegramSendMessage(BaseModel):
    """Telegram send message model."""

    chat_id: int
    text: str
    parse_mode: Optional[str] = "HTML"
    reply_markup: Optional[TelegramInlineKeyboardMarkup] = None
    disable_web_page_preview: Optional[bool] = True


class TelegramSendPhoto(BaseModel):
    """Telegram send photo model."""

    chat_id: int
    photo: str  # URL or file_id
    caption: Optional[str] = None
    parse_mode: Optional[str] = "HTML"
    reply_markup: Optional[TelegramInlineKeyboardMarkup] = None


class TelegramAnswerCallbackQuery(BaseModel):
    """Telegram answer callback query model."""

    callback_query_id: str
    text: Optional[str] = None
    show_alert: Optional[bool] = False
    url: Optional[str] = None
    cache_time: Optional[int] = 0
