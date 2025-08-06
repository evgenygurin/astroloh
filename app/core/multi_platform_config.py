"""
Multi-platform configuration settings.
"""
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class TelegramSettings(BaseSettings):
    """Telegram Bot configuration settings."""
    
    BOT_TOKEN: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_URL")
    WEBHOOK_SECRET: Optional[str] = Field(default=None, env="TELEGRAM_WEBHOOK_SECRET")
    
    # Bot configuration
    PARSE_MODE: str = Field(default="HTML", env="TELEGRAM_PARSE_MODE")
    DISABLE_WEB_PAGE_PREVIEW: bool = Field(default=True, env="TELEGRAM_DISABLE_PREVIEW")
    
    # Rate limiting
    MAX_MESSAGES_PER_MINUTE: int = Field(default=30, env="TELEGRAM_RATE_LIMIT")
    
    # Media settings
    MAX_PHOTO_SIZE_MB: int = Field(default=10, env="TELEGRAM_MAX_PHOTO_SIZE")
    ENABLE_INLINE_QUERIES: bool = Field(default=False, env="TELEGRAM_INLINE_QUERIES")
    
    class Config:
        env_prefix = "TELEGRAM_"
        case_sensitive = True


class GoogleAssistantSettings(BaseSettings):
    """Google Assistant configuration settings."""
    
    # Google Cloud Project settings
    PROJECT_ID: Optional[str] = Field(default=None, env="GOOGLE_PROJECT_ID")
    CREDENTIALS_PATH: Optional[str] = Field(default=None, env="GOOGLE_CREDENTIALS_PATH")
    
    # Dialogflow settings
    DIALOGFLOW_LANGUAGE_CODE: str = Field(default="ru", env="DIALOGFLOW_LANGUAGE_CODE")
    DIALOGFLOW_SESSION_TIMEOUT: int = Field(default=300, env="DIALOGFLOW_SESSION_TIMEOUT")
    
    # Google Actions settings
    ACTIONS_CONSOLE_PROJECT_ID: Optional[str] = Field(default=None, env="GOOGLE_ACTIONS_PROJECT_ID")
    
    # Response configuration
    DEFAULT_LOCALE: str = Field(default="ru-RU", env="GOOGLE_DEFAULT_LOCALE")
    ENABLE_ACCOUNT_LINKING: bool = Field(default=False, env="GOOGLE_ACCOUNT_LINKING")
    
    # Rich response settings
    ENABLE_BASIC_CARDS: bool = Field(default=True, env="GOOGLE_BASIC_CARDS")
    ENABLE_SUGGESTIONS: bool = Field(default=True, env="GOOGLE_SUGGESTIONS")
    MAX_SUGGESTIONS: int = Field(default=8, env="GOOGLE_MAX_SUGGESTIONS")
    
    class Config:
        env_prefix = "GOOGLE_"
        case_sensitive = True


class MultiPlatformSettings(BaseSettings):
    """Multi-platform integration settings."""
    
    # Platform enablement
    ENABLE_TELEGRAM: bool = Field(default=True, env="ENABLE_TELEGRAM")
    ENABLE_GOOGLE_ASSISTANT: bool = Field(default=True, env="ENABLE_GOOGLE_ASSISTANT")
    ENABLE_YANDEX_ALICE: bool = Field(default=True, env="ENABLE_YANDEX_ALICE")
    
    # Analytics and monitoring
    ENABLE_CROSS_PLATFORM_ANALYTICS: bool = Field(default=True, env="ENABLE_CROSS_PLATFORM_ANALYTICS")
    ANALYTICS_PROVIDER: str = Field(default="internal", env="ANALYTICS_PROVIDER")
    
    # User data synchronization
    ENABLE_USER_SYNC: bool = Field(default=False, env="ENABLE_USER_SYNC")
    USER_SYNC_STRATEGY: str = Field(default="opt_in", env="USER_SYNC_STRATEGY")  # opt_in, opt_out, automatic
    
    # Content adaptation
    ADAPTIVE_RESPONSES: bool = Field(default=True, env="ADAPTIVE_RESPONSES")
    PLATFORM_SPECIFIC_CONTENT: bool = Field(default=True, env="PLATFORM_SPECIFIC_CONTENT")
    
    # Rate limiting and security
    GLOBAL_RATE_LIMIT: int = Field(default=100, env="GLOBAL_RATE_LIMIT")  # requests per minute
    ENABLE_WEBHOOK_VERIFICATION: bool = Field(default=True, env="ENABLE_WEBHOOK_VERIFICATION")
    
    # Telegram settings
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    
    # Google Assistant settings
    google: GoogleAssistantSettings = Field(default_factory=GoogleAssistantSettings)
    
    class Config:
        env_prefix = "MULTIPLATFORM_"
        case_sensitive = True


# Global settings instance
multi_platform_settings = MultiPlatformSettings()