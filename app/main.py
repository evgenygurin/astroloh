"""
Основной модуль FastAPI приложения для навыка "Астролог" Яндекс Алисы.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.yandex_dialogs import router as yandex_router
from app.core.config import settings

app = FastAPI(
    title="Astroloh - Навык Астролог для Яндекс Алисы",
    description="API для предоставления астрологических прогнозов и консультаций",
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


@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работы API."""
    return {"message": "Астролог навык для Яндекс Алисы работает!"}


@app.get("/health")
async def health_check():
    """Эндпоинт для проверки здоровья сервиса."""
    return {"status": "healthy"}