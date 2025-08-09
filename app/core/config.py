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

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: str = "logs/astroloh.log"
    LOG_MAX_SIZE: int = 10  # MB
    LOG_BACKUP_COUNT: int = 5
    
    # Production deployment settings
    ENABLE_DEPLOYMENT_MONITORING: bool = True
    ENABLE_FEATURE_FLAGS: bool = True
    ENABLE_ROLLBACK_AUTOMATION: bool = True
    REDIS_URL: Optional[str] = None  # For caching and feature flags
    
    # Deployment phase settings
    DEPLOYMENT_PHASE_1_PERCENTAGE: float = 5.0   # 5% rollout
    DEPLOYMENT_PHASE_2_PERCENTAGE: float = 20.0  # 20% rollout
    DEPLOYMENT_PHASE_3_PERCENTAGE: float = 50.0  # 50% rollout
    DEPLOYMENT_FULL_PERCENTAGE: float = 100.0    # Full rollout
    
    # Monitoring thresholds
    ALERT_RESPONSE_TIME_MS: int = 3000      # Max response time for Alice
    ALERT_ERROR_RATE_PERCENT: float = 5.0   # Max error rate
    ALERT_FALLBACK_RATE_PERCENT: float = 25.0  # Max fallback usage
    ALERT_USER_SATISFACTION_MIN: float = 7.0   # Min satisfaction score

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
