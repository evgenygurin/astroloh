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
    
    # Секретные ключи
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")
    
    # Астрологические вычисления
    SWISS_EPHEMERIS_PATH: str = os.getenv("SWISS_EPHEMERIS_PATH", "/app/swisseph")
    
    class Config:
        env_file = ".env"


settings = Settings()