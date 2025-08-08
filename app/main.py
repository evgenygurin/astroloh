"""
Основной модуль FastAPI приложения для навыка "Астролог" Яндекс Алисы.
"""

import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.google_assistant import router as google_router
from app.api.security import router as security_router
from app.api.telegram_bot import router as telegram_router
from app.api.yandex_dialogs import router as yandex_router
from app.api.recommendations import router as recommendations_router
from app.api.iot_api import router as iot_router
from app.api.auth import router as auth_router
from app.api.astrology import router as astrology_router
from app.api.lunar import router as lunar_router
from app.core.config import settings
from app.core.database import close_database, init_database


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления заголовков безопасности."""
    
    async def dispatch(self, request: Request, call_next):
        """Добавляет заголовки безопасности к каждому ответу."""
        response: Response = await call_next(request)
        
        # Content Security Policy (CSP)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # HTTP Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        return response


# Create limiter for rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Astroloh - Multi-Platform Astrological Assistant",
    description="Unified API for astrological forecasts across Yandex Alice, Telegram Bot, and Google Assistant",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Подключение роутеров
app.include_router(yandex_router, prefix="/api/v1")
app.include_router(telegram_router, prefix="/api/v1")
app.include_router(google_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(iot_router)
app.include_router(auth_router)
app.include_router(astrology_router)
app.include_router(lunar_router)


@app.get("/")
async def root() -> dict[str, str | list[str]]:
    """Корневой эндпоинт для проверки работы API."""
    return {
        "message": "Astroloh - Multi-Platform Astrological Assistant is running!",
        "platforms": ["Yandex Alice", "Telegram Bot", "Google Assistant", "IoT Smart Home"],
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
    # Настройка логирования с принудительным INFO уровнем
    logging.basicConfig(
        level=logging.INFO,  # Принудительно INFO для всех логов
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Переопределить существующую конфигурацию
    )
    logger = logging.getLogger(__name__)
    
    # Установить INFO уровень для всех логгеров приложения
    for logger_name in ['app', 'app.api', 'app.services', 'app.api.yandex_dialogs']:
        logging.getLogger(logger_name).setLevel(logging.INFO)
    
    logger.info("🚀 STARTUP: Logging configuration applied - INFO level enabled")

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
