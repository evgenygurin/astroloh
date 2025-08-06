"""
Multi-platform request handler that provides unified business logic for all platforms.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_models import Platform, UniversalRequest, UniversalResponse
from app.services.conversation_manager import ConversationManager
from app.services.dialog_handler import dialog_handler
from app.services.multi_platform_formatter import MultiPlatformFormatter
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class MultiPlatformHandler:
    """
    Unified handler for all platform requests.
    
    This class serves as the central orchestrator that:
    1. Receives universal requests from platform adapters
    2. Routes them through the existing business logic
    3. Returns universal responses for platform adapters to convert
    """
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.formatter = MultiPlatformFormatter()
        self.conversation_manager = ConversationManager()
    
    async def handle_request(
        self, 
        universal_request: UniversalRequest,
        db: AsyncSession
    ) -> UniversalResponse:
        """
        Process a universal request and return a universal response.
        
        Args:
            universal_request: The universal request object
            db: Database session
            
        Returns:
            UniversalResponse: The universal response object
        """
        try:
            logger.info(f"Processing {universal_request.platform} request for user {universal_request.user_id}")
            
            # Handle platform-specific logic
            if universal_request.platform == Platform.YANDEX:
                return await self._handle_yandex_request(universal_request, db)
            elif universal_request.platform == Platform.TELEGRAM:
                return await self._handle_telegram_request(universal_request, db)
            elif universal_request.platform == Platform.GOOGLE_ASSISTANT:
                return await self._handle_google_request(universal_request, db)
            else:
                logger.error(f"Unsupported platform: {universal_request.platform}")
                return self._create_error_response("Unsupported platform")
                
        except Exception as e:
            logger.error(f"Error in multi-platform handler: {str(e)}", exc_info=True)
            return self._create_error_response("Internal error occurred")
    
    async def _handle_yandex_request(
        self, 
        universal_request: UniversalRequest,
        db: AsyncSession
    ) -> UniversalResponse:
        """Handle Yandex Alice requests using existing logic."""
        try:
            # Convert universal request back to Yandex format for existing handler
            from app.models.yandex_models import YandexRequestModel
            
            # Reconstruct Yandex request from universal request
            original_yandex_data = universal_request.original_request
            if not original_yandex_data:
                raise ValueError("Missing original Yandex request data")
            
            yandex_request = YandexRequestModel(**original_yandex_data)
            
            # Use existing dialog handler
            yandex_response = await dialog_handler.handle_request(yandex_request)
            
            # Convert Yandex response to universal format
            universal_response = UniversalResponse(
                text=yandex_response.response.text,
                tts=yandex_response.response.tts,
                end_session=yandex_response.response.end_session,
                platform_specific={
                    "session": yandex_response.session.dict(),
                    "version": yandex_response.version,
                }
            )
            
            # Convert buttons
            if yandex_response.response.buttons:
                from app.models.platform_models import Button
                universal_buttons = []
                for btn in yandex_response.response.buttons:
                    universal_buttons.append(Button(
                        title=btn.title,
                        payload=btn.payload,
                        url=btn.url
                    ))
                universal_response.buttons = universal_buttons
            
            return universal_response
            
        except Exception as e:
            logger.error(f"Error handling Yandex request: {str(e)}")
            return self._create_error_response("Error processing Yandex request")
    
    async def _handle_telegram_request(
        self, 
        universal_request: UniversalRequest,
        db: AsyncSession
    ) -> UniversalResponse:
        """Handle Telegram Bot requests."""
        try:
            # For now, use the same dialog logic but adapt for Telegram
            # In the future, this could have Telegram-specific features
            
            # Create a mock Yandex request to reuse existing logic
            mock_yandex_request = self._create_mock_yandex_request(universal_request)
            
            # Process through existing dialog handler
            yandex_response = await dialog_handler.handle_request(mock_yandex_request)
            
            # Convert to universal format
            universal_response = UniversalResponse(
                text=yandex_response.response.text,
                tts=None,  # Telegram doesn't use TTS
                end_session=yandex_response.response.end_session,
            )
            
            # Convert buttons for Telegram
            if yandex_response.response.buttons:
                from app.models.platform_models import Button
                universal_buttons = []
                for btn in yandex_response.response.buttons:
                    universal_buttons.append(Button(
                        title=btn.title,
                        payload=btn.payload,
                        url=btn.url
                    ))
                universal_response.buttons = universal_buttons
            
            # Add Telegram-specific formatting
            universal_response.text = self._format_for_telegram(universal_response.text)
            
            return universal_response
            
        except Exception as e:
            logger.error(f"Error handling Telegram request: {str(e)}")
            return self._create_error_response("Error processing Telegram request")
    
    async def _handle_google_request(
        self, 
        universal_request: UniversalRequest,
        db: AsyncSession
    ) -> UniversalResponse:
        """Handle Google Assistant requests."""
        try:
            # Create a mock Yandex request to reuse existing logic
            mock_yandex_request = self._create_mock_yandex_request(universal_request)
            
            # Process through existing dialog handler
            yandex_response = await dialog_handler.handle_request(mock_yandex_request)
            
            # Convert to universal format
            universal_response = UniversalResponse(
                text=yandex_response.response.text,
                tts=yandex_response.response.tts or self._create_tts_for_google(yandex_response.response.text),
                end_session=yandex_response.response.end_session,
                should_listen=not yandex_response.response.end_session,
            )
            
            # Convert buttons for Google Assistant (suggestions)
            if yandex_response.response.buttons:
                from app.models.platform_models import Button
                universal_buttons = []
                for btn in yandex_response.response.buttons:
                    universal_buttons.append(Button(
                        title=btn.title,
                        payload=btn.payload,
                        url=btn.url
                    ))
                universal_response.buttons = universal_buttons
            
            # Format text for Google Assistant
            universal_response.text = self._format_for_google(universal_response.text)
            
            return universal_response
            
        except Exception as e:
            logger.error(f"Error handling Google request: {str(e)}")
            return self._create_error_response("Error processing Google request")
    
    def _create_mock_yandex_request(self, universal_request: UniversalRequest):
        """Create a mock Yandex request from universal request."""
        from app.models.yandex_models import (
            YandexApplication, 
            YandexRequest, 
            YandexRequestModel,
            YandexSession
        )
        
        # Create mock Yandex structures
        application = YandexApplication(application_id="multi_platform_mock")
        
        session = YandexSession(
            session_id=universal_request.session_id,
            message_id=0,
            user_id=universal_request.user_id,
            new=universal_request.is_new_session,
            application=application,
        )
        
        request = YandexRequest(
            command=universal_request.text,
            original_utterance=universal_request.text,
            type="SimpleUtterance",
        )
        
        return YandexRequestModel(
            meta={"locale": "ru-RU", "timezone": "UTC", "client_id": "multi_platform"},
            session=session,
            request=request,
            version="1.0",
        )
    
    def _format_for_telegram(self, text: str) -> str:
        """Format text specifically for Telegram."""
        # Keep emojis but ensure HTML-safe formatting
        formatted = text
        
        # Replace markdown-style formatting if any
        formatted = formatted.replace("**", "*")  # Bold
        formatted = formatted.replace("__", "_")  # Italic
        
        # Ensure text length is within Telegram limits
        if len(formatted) > 4090:
            formatted = formatted[:4087] + "..."
        
        return formatted
    
    def _format_for_google(self, text: str) -> str:
        """Format text specifically for Google Assistant."""
        # Remove excessive emojis and format for speech
        formatted = text
        
        # Replace common formatting for better speech
        formatted = formatted.replace("⭐", "")  # Remove stars
        formatted = formatted.replace("💕", "")  # Remove hearts
        formatted = formatted.replace("\n\n", ". ")  # Line breaks to pauses
        formatted = formatted.replace("\n", ", ")
        
        # Clean up extra spaces
        formatted = " ".join(formatted.split())
        
        return formatted
    
    def _create_tts_for_google(self, text: str) -> str:
        """Create TTS-optimized text for Google Assistant."""
        # Similar to _format_for_google but more aggressive emoji removal
        tts_text = self._format_for_google(text)
        
        # Add SSML pauses if needed
        tts_text = tts_text.replace(". ", ". <break time=\"0.5s\"/> ")
        tts_text = tts_text.replace("! ", "! <break time=\"0.5s\"/> ")
        tts_text = tts_text.replace("? ", "? <break time=\"0.5s\"/> ")
        
        return tts_text
    
    def _create_error_response(self, error_message: str) -> UniversalResponse:
        """Create a standardized error response."""
        return UniversalResponse(
            text=f"Извините, {error_message}. Попробуйте еще раз или скажите 'помощь'.",
            tts=f"Извините, {error_message}. Попробуйте еще раз или скажите помощь.",
            end_session=False,
        )


# Global instance
multi_platform_handler = MultiPlatformHandler()