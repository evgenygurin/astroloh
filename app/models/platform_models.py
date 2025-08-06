"""
Platform abstraction models for multi-platform integrations.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Platform(str, Enum):
    """Supported platforms."""
    YANDEX = "yandex"
    TELEGRAM = "telegram"
    GOOGLE_ASSISTANT = "google_assistant"


class MessageType(str, Enum):
    """Message types."""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"


class Button(BaseModel):
    """Universal button model."""
    title: str
    payload: Optional[Dict[str, Any]] = None
    url: Optional[str] = None


class UniversalRequest(BaseModel):
    """Universal request model for all platforms."""
    platform: Platform
    user_id: str
    session_id: str
    message_id: str
    text: str
    message_type: MessageType = MessageType.TEXT
    is_new_session: bool = False
    user_context: Optional[Dict[str, Any]] = None
    original_request: Optional[Dict[str, Any]] = None


class UniversalResponse(BaseModel):
    """Universal response model for all platforms."""
    text: str
    tts: Optional[str] = None
    buttons: Optional[List[Button]] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None
    end_session: bool = False
    should_listen: bool = True
    platform_specific: Optional[Dict[str, Any]] = None


class PlatformAdapter(ABC):
    """Abstract base class for platform adapters."""
    
    @abstractmethod
    def to_universal_request(self, platform_request: Any) -> UniversalRequest:
        """Convert platform-specific request to universal format."""
        pass
    
    @abstractmethod
    def from_universal_response(self, universal_response: UniversalResponse) -> Any:
        """Convert universal response to platform-specific format."""
        pass
    
    @abstractmethod
    def validate_request(self, request: Any) -> bool:
        """Validate platform-specific request."""
        pass