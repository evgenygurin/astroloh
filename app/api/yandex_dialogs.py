"""
API роутер для интеграции с Яндекс.Диалогами.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional


router = APIRouter(prefix="/yandex", tags=["Yandex Dialogs"])


class YandexRequest(BaseModel):
    """Модель запроса от Яндекс.Диалогов."""
    meta: Dict[str, Any]
    request: Dict[str, Any]
    session: Dict[str, Any]
    version: str


class YandexResponse(BaseModel):
    """Модель ответа для Яндекс.Диалогов."""
    response: Dict[str, Any]
    session: Dict[str, Any]
    version: str


@router.post("/webhook", response_model=YandexResponse)
async def yandex_webhook(request: YandexRequest):
    """
    Основной webhook для обработки запросов от Яндекс.Диалогов.
    """
    # Базовая обработка запроса
    user_message = request.request.get("original_utterance", "").lower()
    session_data = request.session
    
    # Определение типа запроса
    if request.session.get("new", True):
        # Новая сессия - приветствие
        response_text = "Привет! Я астролог Алисы. Я могу составить гороскоп, рассказать о совместимости знаков или дать астрологический совет. Что вас интересует?"
    elif "гороскоп" in user_message:
        response_text = "Для составления гороскопа мне нужна ваша дата рождения. Назовите, пожалуйста, день, месяц и год."
    elif "совместимость" in user_message:
        response_text = "Для проверки совместимости назовите знаки зодиака партнеров."
    elif "совет" in user_message:
        response_text = "Вот астрологический совет дня: звезды советуют быть внимательным к деталям и слушать свою интуицию."
    else:
        response_text = "Я пока изучаю астрологию. Попробуйте спросить про гороскоп, совместимость знаков или астрологический совет."
    
    return YandexResponse(
        response={
            "text": response_text,
            "end_session": False
        },
        session=session_data,
        version=request.version
    )