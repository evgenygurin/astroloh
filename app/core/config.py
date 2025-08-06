"""
Конфигурация приложения.
"""

import secrets
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    # Основные настройки
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # API настройки
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Astroloh"

    # База данных
    DATABASE_URL: Optional[str] = None

    # Яндекс Диалоги
    YANDEX_SKILL_ID: Optional[str] = None
    YANDEX_OAUTH_TOKEN: Optional[str] = None

    # Yandex GPT API
    YANDEX_API_KEY: Optional[str] = None
    YANDEX_FOLDER_ID: Optional[str] = None
    YANDEX_CATALOG_ID: Optional[str] = None
    YANDEX_GPT_API_KEY: Optional[str] = None
    YANDEX_GPT_FOLDER_ID: Optional[str] = None

    # Секретные ключи
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ENCRYPTION_KEY: str = ""

    # CORS настройки
    CORS_ORIGINS: List[str] = ["*"]

    # Астрологические вычисления
    SWISS_EPHEMERIS_PATH: str = "/app/swisseph"

    # AI настройки
    ENABLE_AI_GENERATION: bool = True
    AI_FALLBACK_ENABLED: bool = True
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 800

    # Дополнительные настройки безопасности
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Ngrok settings
    NGROK_AUTHTOKEN: Optional[str] = None
    NGROK_BACKEND_HOSTNAME: Optional[str] = None
    NGROK_FRONTEND_HOSTNAME: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, values):
        """Validate fields, handling invalid values gracefully."""
        if isinstance(values, dict) and "DEBUG" in values:
            debug_val = values["DEBUG"]
            if isinstance(debug_val, str):
                values["DEBUG"] = debug_val.lower() == "true"
            else:
                values["DEBUG"] = bool(debug_val)
        return values

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ENCRYPTION_KEY:
            self.ENCRYPTION_KEY = secrets.token_hex(32)

    class Config:
        env_file = ".env"


settings = Settings()
