"""
API роутер для интеграции с Яндекс.Диалогами.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.yandex_models import YandexRequestModel, YandexResponseModel
from app.services.dialog_handler import dialog_handler
from app.utils.error_handler import error_handler
from app.core.database import get_database
from app.services.user_manager import UserManager


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/yandex", tags=["Yandex Dialogs"])


@router.post("/webhook", response_model=YandexResponseModel)
async def yandex_webhook(request: YandexRequestModel, db: AsyncSession = Depends(get_database)):
    """
    Основной webhook для обработки запросов от Яндекс.Диалогов.
    
    Принимает запросы от Яндекс.Диалогов, обрабатывает их через 
    систему распознавания интентов и возвращает соответствующие ответы.
    """
    try:
        # Логируем входящий запрос
        logger.info(f"Received request from user {request.session.user_id}")
        
        # Инициализируем менеджер пользователей с базой данных
        user_manager = UserManager(db)
        
        # Получаем или создаем пользователя
        user = await user_manager.get_or_create_user(request.session.user_id)
        
        # Обрабатываем запрос через основной обработчик диалогов с интеграцией БД
        response = await dialog_handler.handle_request(request, db_session=db, user=user)
        
        # Логируем успешный ответ
        logger.info(f"Successfully processed request for user {request.session.user_id}")
        
        return response
        
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        # Обрабатываем ошибку и возвращаем соответствующий ответ
        error_response = error_handler.handle_error(e, {
            "user_id": request.session.user_id,
            "session_id": request.session.session_id,
            "request_text": request.request.original_utterance[:100]  # Ограничиваем для безопасности
        })
        
        # Формируем полный ответ с ошибкой
        return YandexResponseModel(
            response=error_response,
            session=request.session,
            version=request.version
        )


@router.get("/health")
async def health_check():
    """
    Эндпоинт проверки здоровья сервиса Яндекс.Диалогов.
    """
    try:
        # Проверяем доступность основных компонентов
        active_sessions = dialog_handler.session_manager.get_active_sessions_count()
        
        return {
            "status": "healthy",
            "service": "yandex_dialogs",
            "active_sessions": active_sessions,
            "components": {
                "intent_recognizer": "ok",
                "session_manager": "ok", 
                "response_formatter": "ok",
                "error_handler": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.post("/cleanup-sessions")
async def cleanup_sessions():
    """
    Эндпоинт для принудительной очистки устаревших сессий.
    """
    try:
        cleaned_count = dialog_handler.session_manager.cleanup_expired_sessions()
        return {
            "status": "success",
            "cleaned_sessions": cleaned_count
        }
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")