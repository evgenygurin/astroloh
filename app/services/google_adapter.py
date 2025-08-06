"""
Google Assistant platform adapter for converting between Google Actions and universal formats.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app.models.google_models import (
    GoogleBasicCard,
    GoogleDialogflowResponse,
    GoogleFinalResponse,
    GoogleRequest,
    GoogleResponse,
    GoogleRichResponse,
    GoogleSimpleResponse,
    GoogleSuggestion,
)
from app.models.platform_models import (
    Button,
    MessageType,
    Platform,
    PlatformAdapter,
    UniversalRequest,
    UniversalResponse,
)

logger = logging.getLogger(__name__)


class GoogleAssistantAdapter(PlatformAdapter):
    """Google Assistant platform adapter."""
    
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate Google Actions request."""
        try:
            if not isinstance(request, dict):
                return False
            
            # Check for required Dialogflow fields
            if "queryResult" in request:
                # Dialogflow v2 format
                query_result = request.get("queryResult", {})
                return "queryText" in query_result and "intent" in query_result
            
            # Check for Google Actions format
            if "user" not in request:
                return False
                
            if "conversation" not in request:
                return False
                
            if "inputs" not in request:
                return False
                
            return True
        except Exception as e:
            logger.error(f"Google request validation error: {e}")
            return False
    
    def to_universal_request(self, google_data: Dict[str, Any]) -> UniversalRequest:
        """Convert Google Actions request to universal request format."""
        try:
            # Handle Dialogflow format
            if "queryResult" in google_data:
                return self._from_dialogflow_request(google_data)
            
            # Handle Google Actions format
            google_request = GoogleRequest(**google_data)
            
            # Extract user info
            user_id = google_request.user.user_id
            conversation_id = google_request.conversation.conversation_id
            
            # Extract text from inputs
            text = ""
            intent = ""
            for input_data in google_request.inputs:
                if input_data.raw_inputs:
                    for raw_input in input_data.raw_inputs:
                        if "query" in raw_input:
                            text = raw_input["query"]
                            break
                intent = input_data.intent
                if text:
                    break
            
            # Determine if new session
            is_new_session = google_request.conversation.type == "NEW"
            
            # Build user context
            user_context = {
                "google_user": {
                    "user_id": google_request.user.user_id,
                    "locale": google_request.user.locale,
                },
                "device": google_request.device.dict() if google_request.device else {},
                "surface_capabilities": [cap for cap in google_request.surface.capabilities] if google_request.surface else [],
                "conversation_token": google_request.conversation.conversation_token,
                "intent": intent,
            }
            
            return UniversalRequest(
                platform=Platform.GOOGLE_ASSISTANT,
                user_id=user_id,
                session_id=conversation_id,
                message_id=conversation_id,  # Use conversation_id as message_id
                text=text,
                message_type=MessageType.TEXT,
                is_new_session=is_new_session,
                user_context=user_context,
                original_request=google_data,
            )
            
        except Exception as e:
            logger.error(f"Error converting Google request: {e}")
            raise
    
    def _from_dialogflow_request(self, dialogflow_data: Dict[str, Any]) -> UniversalRequest:
        """Convert Dialogflow v2 request to universal format."""
        query_result = dialogflow_data.get("queryResult", {})
        session = dialogflow_data.get("session", "")
        
        # Extract session and user info
        session_parts = session.split("/")
        session_id = session_parts[-1] if session_parts else "unknown"
        user_id = session_id  # Use session as user_id for Dialogflow
        
        text = query_result.get("queryText", "")
        intent_name = query_result.get("intent", {}).get("displayName", "")
        
        user_context = {
            "dialogflow": {
                "intent_name": intent_name,
                "intent_detection_confidence": query_result.get("intentDetectionConfidence", 0.0),
                "language_code": query_result.get("languageCode", "en"),
                "parameters": query_result.get("parameters", {}),
            },
            "session_info": dialogflow_data.get("sessionInfo", {}),
        }
        
        return UniversalRequest(
            platform=Platform.GOOGLE_ASSISTANT,
            user_id=user_id,
            session_id=session_id,
            message_id=session_id,
            text=text,
            message_type=MessageType.TEXT,
            is_new_session=intent_name == "Default Welcome Intent",
            user_context=user_context,
            original_request=dialogflow_data,
        )
    
    def from_universal_response(self, universal_response: UniversalResponse) -> Dict[str, Any]:
        """Convert universal response to Google Actions format."""
        try:
            # Check if this is a Dialogflow response
            if (universal_response.platform_specific and 
                universal_response.platform_specific.get("use_dialogflow", False)):
                return self._to_dialogflow_response(universal_response)
            
            # Build Google Actions response
            items = []
            
            # Add simple response (text/speech)
            simple_response = GoogleSimpleResponse(
                text_to_speech=universal_response.tts or universal_response.text,
                display_text=universal_response.text,
            )
            items.append({"simpleResponse": simple_response.dict()})
            
            # Add basic card if image is provided
            if universal_response.image_url:
                basic_card = GoogleBasicCard(
                    title="Astroloh",
                    formatted_text=universal_response.image_caption or universal_response.text,
                    image={"url": universal_response.image_url},
                )
                items.append({"basicCard": basic_card.dict()})
            
            # Add suggestions (buttons)
            suggestions = []
            if universal_response.buttons:
                for button in universal_response.buttons[:8]:  # Google limit
                    if not button.url:  # Only text suggestions, not web links
                        suggestions.append(GoogleSuggestion(title=button.title))
            
            # Build rich response
            rich_response = GoogleRichResponse(
                items=items,
                suggestions=suggestions if suggestions else None,
            )
            
            # Build final response or expected input based on end_session
            if universal_response.end_session:
                # Final response (conversation ends)
                final_response = GoogleFinalResponse(rich_response=rich_response)
                google_response = GoogleResponse(
                    expect_user_response=False,
                    final_response=final_response,
                )
            else:
                # Expected input (conversation continues)
                google_response = GoogleResponse(
                    expect_user_response=True,
                    rich_response=rich_response,
                )
            
            # Add conversation token if provided
            if (universal_response.platform_specific and 
                "conversation_token" in universal_response.platform_specific):
                google_response.conversation_token = universal_response.platform_specific["conversation_token"]
            
            return google_response.dict(exclude_none=True)
            
        except Exception as e:
            logger.error(f"Error converting to Google response: {e}")
            raise
    
    def _to_dialogflow_response(self, universal_response: UniversalResponse) -> Dict[str, Any]:
        """Convert to Dialogflow v2 response format."""
        fulfillment_messages = []
        
        # Add text response
        fulfillment_messages.append({
            "text": {
                "text": [universal_response.text]
            }
        })
        
        # Add image card if provided
        if universal_response.image_url:
            fulfillment_messages.append({
                "card": {
                    "title": "Astroloh",
                    "subtitle": universal_response.image_caption or "Astrological insight",
                    "imageUri": universal_response.image_url,
                }
            })
        
        # Add quick replies (buttons)
        if universal_response.buttons:
            quick_replies = []
            for button in universal_response.buttons[:13]:  # Dialogflow limit
                if not button.url:  # Only text replies
                    quick_replies.append(button.title)
            
            if quick_replies:
                fulfillment_messages.append({
                    "quickReplies": {
                        "title": "Choose an option:",
                        "quickReplies": quick_replies
                    }
                })
        
        dialogflow_response = GoogleDialogflowResponse(
            fulfillment_text=universal_response.text,
            fulfillment_messages=fulfillment_messages,
            source="astroloh",
        )
        
        return dialogflow_response.dict(exclude_none=True)
    
    def _format_google_text(self, text: str) -> str:
        """Format text for Google Assistant speech synthesis."""
        # Replace emojis with descriptive text for better speech
        formatted = text
        
        # Common emoji replacements for speech
        replacements = {
            "⭐": "star",
            "💕": "love",
            "💗": "heart",
            "💛": "yellow heart",
            "🌟": "star",
            "🌙": "moon",
            "🔮": "crystal ball",
            "💼": "briefcase",
            "🏥": "hospital",
            "💰": "money",
            "🔢": "numbers",
            "🎨": "art palette",
            "⚡": "lightning",
        }
        
        for emoji, replacement in replacements.items():
            formatted = formatted.replace(emoji, replacement)
        
        # Clean up extra spaces
        formatted = " ".join(formatted.split())
        
        return formatted