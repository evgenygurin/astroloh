"""
Multi-platform response formatter that extends the existing ResponseFormatter
to support multiple platforms while maintaining unified business logic.
"""

import logging
from typing import Any, Dict, Optional

from app.models.platform_models import Button, Platform, UniversalResponse
from app.services.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)


class MultiPlatformFormatter(ResponseFormatter):
    """
    Extended response formatter that supports multiple platforms.

    This class extends the existing ResponseFormatter to provide
    platform-agnostic response generation while preserving all
    existing Yandex Alice functionality.
    """

    def __init__(self):
        super().__init__()

        # Platform-specific limits and features
        self.platform_limits = {
            Platform.YANDEX: {
                "max_buttons": 5,
                "max_text_length": 1024,
                "supports_tts": True,
                "supports_images": False,
                "supports_markup": False,
            },
            Platform.TELEGRAM: {
                "max_buttons": 10,
                "max_text_length": 4096,
                "supports_tts": False,
                "supports_images": True,
                "supports_markup": True,
            },
            Platform.GOOGLE_ASSISTANT: {
                "max_buttons": 8,
                "max_text_length": 640,  # For speech
                "supports_tts": True,
                "supports_images": True,
                "supports_markup": False,
            },
        }

    def format_universal_welcome_response(
        self, platform: Platform, is_returning_user: bool = False
    ) -> UniversalResponse:
        """Format welcome response for any platform."""
        # Use existing logic
        yandex_response = self.format_welcome_response(is_returning_user)

        # Convert to universal format
        universal_response = self._yandex_to_universal(
            yandex_response, platform
        )

        # Apply platform-specific optimizations
        return self._optimize_for_platform(universal_response, platform)

    def format_universal_horoscope_response(
        self,
        platform: Platform,
        horoscope_data: Optional[Dict[str, Any]] = None,
        zodiac_sign: Optional[Any] = None,
        period: str = "день",
    ) -> UniversalResponse:
        """Format horoscope response for any platform."""
        # Use existing logic
        yandex_response = self.format_horoscope_response(
            zodiac_sign, horoscope_data, period
        )

        # Convert to universal format
        universal_response = self._yandex_to_universal(
            yandex_response, platform
        )

        # Apply platform-specific optimizations
        return self._optimize_for_platform(universal_response, platform)

    def format_universal_compatibility_response(
        self,
        platform: Platform,
        compatibility_data: Optional[Dict[str, Any]] = None,
        sign1: Optional[Any] = None,
        sign2: Optional[Any] = None,
    ) -> UniversalResponse:
        """Format compatibility response for any platform."""
        # Use existing logic
        yandex_response = self.format_compatibility_response(
            sign1, sign2, compatibility_data
        )

        # Convert to universal format
        universal_response = self._yandex_to_universal(
            yandex_response, platform
        )

        # Apply platform-specific optimizations
        return self._optimize_for_platform(universal_response, platform)

    def format_universal_advice_response(
        self, platform: Platform
    ) -> UniversalResponse:
        """Format advice response for any platform."""
        # Use existing logic
        yandex_response = self.format_advice_response()

        # Convert to universal format
        universal_response = self._yandex_to_universal(
            yandex_response, platform
        )

        # Apply platform-specific optimizations
        return self._optimize_for_platform(universal_response, platform)

    def format_universal_help_response(
        self, platform: Platform
    ) -> UniversalResponse:
        """Format help response for any platform."""
        # Use existing logic
        yandex_response = self.format_help_response()

        # Convert to universal format
        universal_response = self._yandex_to_universal(
            yandex_response, platform
        )

        # Apply platform-specific optimizations
        return self._optimize_for_platform(universal_response, platform)

    def format_universal_error_response(
        self, platform: Platform, error_type: str = "general"
    ) -> UniversalResponse:
        """Format error response for any platform."""
        # Use existing logic
        yandex_response = self.format_error_response(error_type)

        # Convert to universal format
        universal_response = self._yandex_to_universal(
            yandex_response, platform
        )

        # Apply platform-specific optimizations
        return self._optimize_for_platform(universal_response, platform)

    def _yandex_to_universal(
        self, yandex_response: Any, target_platform: Platform
    ) -> UniversalResponse:
        """Convert Yandex response to universal format."""
        # Extract buttons
        buttons = []
        if hasattr(yandex_response, "buttons") and yandex_response.buttons:
            for yandex_button in yandex_response.buttons:
                button = Button(
                    title=yandex_button.title,
                    payload=yandex_button.payload,
                    url=yandex_button.url,
                )
                buttons.append(button)

        # Create universal response
        universal_response = UniversalResponse(
            text=yandex_response.text,
            tts=yandex_response.tts
            if hasattr(yandex_response, "tts")
            else None,
            buttons=buttons if buttons else None,
            end_session=yandex_response.end_session
            if hasattr(yandex_response, "end_session")
            else False,
            should_listen=not yandex_response.end_session
            if hasattr(yandex_response, "end_session")
            else True,
        )

        return universal_response

    def _optimize_for_platform(
        self, response: UniversalResponse, platform: Platform
    ) -> UniversalResponse:
        """Apply platform-specific optimizations."""
        platform_config = self.platform_limits.get(platform, {})

        # Optimize text length
        max_length = platform_config.get("max_text_length", 1024)
        if len(response.text) > max_length:
            response.text = response.text[: max_length - 3] + "..."

        # Optimize buttons
        max_buttons = platform_config.get("max_buttons", 5)
        if response.buttons and len(response.buttons) > max_buttons:
            response.buttons = response.buttons[:max_buttons]

        # Platform-specific text formatting
        if platform == Platform.TELEGRAM:
            response.text = self._format_for_telegram(response.text)
        elif platform == Platform.GOOGLE_ASSISTANT:
            response.text = self._format_for_google(response.text)
            # Ensure TTS is present for Google
            if not response.tts:
                response.tts = self._create_tts_for_google(response.text)

        # Remove TTS for platforms that don't support it
        if not platform_config.get("supports_tts", True):
            response.tts = None

        return response

    def _format_for_telegram(self, text: str) -> str:
        """Format text for Telegram with HTML support."""
        # Keep emojis but ensure proper formatting
        formatted = text

        # Convert some formatting to HTML if needed
        # For now, keep as plain text with emojis

        return formatted

    def _format_for_google(self, text: str) -> str:
        """Format text for Google Assistant display."""
        # Remove excessive emojis for better display
        formatted = text

        # Replace multiple line breaks
        formatted = formatted.replace("\n\n", "\n")
        formatted = formatted.replace("\n", " ")

        # Clean up spaces
        formatted = " ".join(formatted.split())

        return formatted

    def _create_tts_for_google(self, text: str) -> str:
        """Create TTS-optimized text for Google Assistant."""
        import re

        # Remove emojis for speech
        tts = re.sub(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]",
            "",
            text,
        )

        # Add natural speech pauses
        tts = tts.replace(".", ". ")
        tts = tts.replace("!", "! ")
        tts = tts.replace("?", "? ")
        tts = tts.replace(":", ": ")

        # Handle line breaks
        tts = tts.replace("\n\n", ". ")
        tts = tts.replace("\n", ", ")

        # Clean up spaces
        tts = re.sub(r"\s+", " ", tts).strip()

        return tts
