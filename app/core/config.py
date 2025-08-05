"""
Конфигурация приложения.
"""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    # Основные настройки
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # База данных
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # Яндекс Диалоги
    YANDEX_SKILL_ID: Optional[str] = os.getenv("YANDEX_SKILL_ID")
    YANDEX_OAUTH_TOKEN: Optional[str] = os.getenv("YANDEX_OAUTH_TOKEN")
    
    # Yandex GPT API
    YANDEX_API_KEY: Optional[str] = os.getenv("YANDEX_API_KEY")
    YANDEX_FOLDER_ID: Optional[str] = os.getenv("YANDEX_FOLDER_ID")
    YANDEX_CATALOG_ID: Optional[str] = os.getenv("YANDEX_CATALOG_ID")

    # Секретные ключи
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")

    # Астрологические вычисления
    SWISS_EPHEMERIS_PATH: str = os.getenv(
        "SWISS_EPHEMERIS_PATH", "/app/swisseph"
    )
    
    # AI настройки
    ENABLE_AI_GENERATION: bool = os.getenv("ENABLE_AI_GENERATION", "true").lower() == "true"
    AI_FALLBACK_ENABLED: bool = os.getenv("AI_FALLBACK_ENABLED", "true").lower() == "true"
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "800"))

    # Дополнительные настройки безопасности
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    class Config:
        env_file = ".env"


settings = Settings()
