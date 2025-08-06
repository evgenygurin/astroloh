"""
Yandex Alice platform adapter for converting between Yandex format and universal formats.
"""
import logging
from typing import Any

from app.models.platform_models import (
    MessageType,
    Platform,
    PlatformAdapter,
    UniversalRequest,
    UniversalResponse,
)
from app.models.yandex_models import YandexRequestModel, YandexResponseModel

logger = logging.getLogger(__name__)


class YandexAdapter(PlatformAdapter):
    """Yandex Alice platform adapter."""
    
    def validate_request(self, request: Any) -> bool:
        """Validate Yandex Alice request."""
        try:
            if isinstance(request, dict):
                return ("session" in request and 
                        "request" in request and 
                        "version" in request)
            
            if hasattr(request, 'session') and hasattr(request, 'request'):
                return True
                
            return False
        except Exception as e:
            logger.error(f"Yandex request validation error: {e}")
            return False
    
    def to_universal_request(self, yandex_request: YandexRequestModel) -> UniversalRequest:
        """Convert Yandex Alice request to universal request format."""
        try:
            # Extract basic info
            user_id = yandex_request.session.user_id
            session_id = yandex_request.session.session_id
            message_id = f"{session_id}_{yandex_request.session.message_id}"
            text = yandex_request.request.original_utterance
            is_new_session = yandex_request.session.new
            
            # Build user context
            user_context = {
                "yandex_user": {
                    "user_id": yandex_request.session.user_id,
                    "application_id": yandex_request.session.application.application_id,
                },
                "application": yandex_request.session.application.dict(),
                "interfaces": yandex_request.session.interfaces.dict() if yandex_request.session.interfaces else {},
                "nlu": yandex_request.request.nlu.dict() if yandex_request.request.nlu else {},
                "command": yandex_request.request.command,
                "type": yandex_request.request.type,
            }
            
            # Add markup info if present
            if yandex_request.request.markup:
                user_context["markup"] = yandex_request.request.markup.dict()
            
            return UniversalRequest(
                platform=Platform.YANDEX,
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                text=text,
                message_type=MessageType.TEXT,
                is_new_session=is_new_session,
                user_context=user_context,
                original_request=yandex_request.dict(),
            )
            
        except Exception as e:
            logger.error(f"Error converting Yandex request: {e}")
            raise
    
    def from_universal_response(self, universal_response: UniversalResponse) -> YandexResponseModel:
        """Convert universal response to Yandex Alice format."""
        try:
            from app.models.yandex_models import YandexButton, YandexResponse
            
            # Convert buttons
            yandex_buttons = []
            if universal_response.buttons:
                for button in universal_response.buttons[:5]:  # Yandex limit
                    yandex_button = YandexButton(
                        title=button.title,
                        payload=button.payload or {"action": button.title.lower().replace(" ", "_")},
                        url=button.url,
                    )
                    yandex_buttons.append(yandex_button)
            
            # Create Yandex response
            yandex_response = YandexResponse(
                text=universal_response.text,
                tts=universal_response.tts or self._add_tts_pauses(universal_response.text),
                buttons=yandex_buttons if yandex_buttons else None,
                end_session=universal_response.end_session,
            )
            
            # Get session info from platform_specific data
            session_data = None
            version = "1.0"
            
            if universal_response.platform_specific:
                session_data = universal_response.platform_specific.get("session")
                version = universal_response.platform_specific.get("version", "1.0")
            
            if not session_data:
                # Create minimal session data
                from app.models.yandex_models import YandexSession, YandexApplication
                session_data = YandexSession(
                    session_id="unknown",
                    message_id=0,
                    user_id="unknown",
                    new=False,
                    application=YandexApplication(application_id="unknown"),
                )
            
            return YandexResponseModel(
                response=yandex_response,
                session=session_data,
                version=version,
            )
            
        except Exception as e:
            logger.error(f"Error converting to Yandex response: {e}")
            raise
    
    def _add_tts_pauses(self, text: str) -> str:
        """Add TTS pauses for Yandex Alice."""
        import re
        
        # Remove emojis for TTS
        tts = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]', '', text)
        
        # Add pauses
        tts = tts.replace(".", ". - ")
        tts = tts.replace("!", "! - ")
        tts = tts.replace("?", "? - ")
        tts = tts.replace(":", ": ")
        tts = tts.replace(";", "; ")
        
        # Handle line breaks
        tts = tts.replace("\n\n", ". ")
        tts = tts.replace("\n", ", ")
        
        # Clean up spaces
        tts = re.sub(r'\s+', ' ', tts).strip()
        
        return tts