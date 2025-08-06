"""
Основной модуль FastAPI приложения для навыка "Астролог" Яндекс Алисы.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.google_assistant import router as google_router
from app.api.security import router as security_router
from app.api.telegram_bot import router as telegram_router
from app.api.yandex_dialogs import router as yandex_router
from app.api.recommendations import router as recommendations_router
from app.core.config import settings
from app.core.database import close_database, init_database

app = FastAPI(
    title="Astroloh - Multi-Platform Astrological Assistant",
    description="Unified API for astrological forecasts across Yandex Alice, Telegram Bot, and Google Assistant",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(yandex_router, prefix="/api/v1")
app.include_router(telegram_router, prefix="/api/v1")
app.include_router(google_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str | list[str]]:
    """Корневой эндпоинт для проверки работы API."""
    return {
        "message": "Astroloh - Multi-Platform Astrological Assistant is running!",
        "platforms": ["Yandex Alice", "Telegram Bot", "Google Assistant"],
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Эндпоинт для проверки здоровья сервиса."""
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.on_event("startup")
async def startup_event() -> None:
    """Инициализация при запуске приложения."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        if settings.DATABASE_URL:
            await init_database()
            logger.info("Database initialized successfully")
        else:
            logger.warning("DATABASE_URL not configured, running without database")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Очистка при завершении приложения."""
    logger = logging.getLogger(__name__)

    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
