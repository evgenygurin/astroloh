"""
Multi-platform configuration settings.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseSettings):
    """Telegram Bot configuration settings."""

    BOT_TOKEN: Optional[str] = Field(default=None)
    WEBHOOK_URL: Optional[str] = Field(default=None)
    WEBHOOK_SECRET: Optional[str] = Field(default=None)

    # Bot configuration
    PARSE_MODE: str = Field(default="HTML")
    DISABLE_WEB_PAGE_PREVIEW: bool = Field(default=True)

    # Rate limiting
    MAX_MESSAGES_PER_MINUTE: int = Field(default=30)

    # Media settings
    MAX_PHOTO_SIZE_MB: int = Field(default=10)
    ENABLE_INLINE_QUERIES: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_prefix="TELEGRAM_", case_sensitive=True
    )


class GoogleAssistantSettings(BaseSettings):
    """Google Assistant configuration settings."""

    # Google Cloud Project settings
    PROJECT_ID: Optional[str] = Field(default=None)
    CREDENTIALS_PATH: Optional[str] = Field(default=None)

    # Dialogflow settings
    DIALOGFLOW_LANGUAGE_CODE: str = Field(default="ru")
    DIALOGFLOW_SESSION_TIMEOUT: int = Field(default=300)

    # Google Actions settings
    ACTIONS_CONSOLE_PROJECT_ID: Optional[str] = Field(default=None)

    # Response configuration
    DEFAULT_LOCALE: str = Field(default="ru-RU")
    ENABLE_ACCOUNT_LINKING: bool = Field(default=False)

    # Rich response settings
    ENABLE_BASIC_CARDS: bool = Field(default=True)
    ENABLE_SUGGESTIONS: bool = Field(default=True)
    MAX_SUGGESTIONS: int = Field(default=8)

    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_", case_sensitive=True
    )


class MultiPlatformSettings(BaseSettings):
    """Multi-platform integration settings."""

    # Platform enablement
    ENABLE_TELEGRAM: bool = Field(default=True)
    ENABLE_GOOGLE_ASSISTANT: bool = Field(default=True)
    ENABLE_YANDEX_ALICE: bool = Field(default=True)

    # Analytics and monitoring
    ENABLE_CROSS_PLATFORM_ANALYTICS: bool = Field(default=True)
    ANALYTICS_PROVIDER: str = Field(default="internal")

    # User data synchronization
    ENABLE_USER_SYNC: bool = Field(default=False)
    USER_SYNC_STRATEGY: str = Field(
        default="opt_in"
    )  # opt_in, opt_out, automatic

    # Content adaptation
    ADAPTIVE_RESPONSES: bool = Field(default=True)
    PLATFORM_SPECIFIC_CONTENT: bool = Field(default=True)

    # Rate limiting and security
    GLOBAL_RATE_LIMIT: int = Field(default=100)  # requests per minute
    ENABLE_WEBHOOK_VERIFICATION: bool = Field(default=True)

    # Telegram settings
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)

    # Google Assistant settings
    google: GoogleAssistantSettings = Field(
        default_factory=GoogleAssistantSettings
    )

    model_config = SettingsConfigDict(
        env_prefix="MULTIPLATFORM_", case_sensitive=True
    )


# Global settings instance
multi_platform_settings = MultiPlatformSettings()
