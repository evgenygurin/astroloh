"""
API роутер для интеграции с Яндекс.Диалогами.
"""

import logging
import json
import uuid
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.models.yandex_models import YandexRequestModel, YandexResponseModel
from app.services.dialog_handler import dialog_handler
from app.services.user_manager import UserManager
from app.utils.error_handler import error_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/yandex", tags=["Yandex Dialogs"])


@router.post("/webhook", response_model=YandexResponseModel)
async def yandex_webhook(
    request: YandexRequestModel, db: AsyncSession = Depends(get_database)
) -> YandexResponseModel:
    """
    Основной webhook для обработки запросов от Яндекс.Диалогов.

    Принимает запросы от Яндекс.Диалогов, обрабатывает их через
    систему распознавания интентов и возвращает соответствующие ответы.
    """
    # Создаем уникальный correlation ID для отслеживания запроса
    correlation_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Формируем контекст логирования
    log_context = {
        "correlation_id": correlation_id,
        "user_id": request.session.user_id,
        "session_id": request.session.session_id,
        "timestamp": start_time.isoformat()
    }
    
    logger.info(
        "WEBHOOK_REQUEST_START",
        extra={
            **log_context,
            "request_data": {
                "new_session": request.session.new,
                "application_id": getattr(request.session.application, 'application_id', 'unknown') if hasattr(request.session, 'application') else 'unknown',
                "user_utterance": request.request.original_utterance[:200] if request.request.original_utterance else '',
                "command": getattr(request.request, 'command', '') if hasattr(request.request, 'command') else '',
                "type": getattr(request.request, 'type', 'SimpleUtterance') if hasattr(request.request, 'type') else 'SimpleUtterance',
                "has_markup": bool(getattr(request.request, 'markup', None)),
                "has_payload": bool(getattr(request.request, 'payload', None)),
                "has_interfaces": bool(getattr(request.meta, 'interfaces', None)) if hasattr(request, 'meta') else False,
                "locale": getattr(request.meta, 'locale', 'ru-RU') if hasattr(request, 'meta') else 'ru-RU',
                "timezone": getattr(request.meta, 'timezone', 'UTC') if hasattr(request, 'meta') else 'UTC',
                "client_id": getattr(request.meta, 'client_id', 'unknown') if hasattr(request, 'meta') else 'unknown'
            }
        }
    )
    
    try:
        logger.info("USER_MANAGER_INIT", extra={**log_context, "step": "initializing_user_manager"})
        
        # Инициализируем менеджер пользователей с базой данных
        user_manager = UserManager(db)

        logger.info("USER_LOOKUP_START", extra={**log_context, "step": "user_lookup"})
        
        # Получаем или создаем пользователя
        user = await user_manager.get_or_create_user(request.session.user_id)
        
        logger.info(
            "USER_LOOKUP_COMPLETE", 
            extra={
                **log_context, 
                "step": "user_lookup_complete",
                "user_exists": user is not None,
                "user_created": hasattr(user, '_sa_instance_state') and hasattr(user._sa_instance_state, 'pending') and user._sa_instance_state.pending if user is not None else False
            }
        )

        logger.info("DIALOG_HANDLER_START", extra={**log_context, "step": "dialog_processing"})
        
        # Обрабатываем запрос через основной обработчик диалогов
        dialog_response = await dialog_handler.handle_request(request)
        
        # Вычисляем время выполнения
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            "WEBHOOK_REQUEST_SUCCESS",
            extra={
                **log_context,
                "processing_time_seconds": processing_time,
                "response_data": {
                    "text": dialog_response.response.text[:150] if hasattr(dialog_response, 'response') and hasattr(dialog_response.response, 'text') else '',
                    "tts": dialog_response.response.tts[:100] if hasattr(dialog_response, 'response') and hasattr(dialog_response.response, 'tts') and dialog_response.response.tts else None,
                    "has_buttons": bool(getattr(dialog_response.response, 'buttons', None)) if hasattr(dialog_response, 'response') else False,
                    "has_card": bool(getattr(dialog_response.response, 'card', None)) if hasattr(dialog_response, 'response') else False,
                    "end_session": getattr(dialog_response.response, 'end_session', False) if hasattr(dialog_response, 'response') else False
                },
                "session_state": {
                    "message_id": dialog_response.session.message_id,
                    "session_id": dialog_response.session.session_id
                }
            }
        )

        # Возвращаем ответ напрямую (уже содержит все необходимые поля)
        return dialog_response

    except Exception as e:
        # Вычисляем время до ошибки
        error_time = (datetime.now() - start_time).total_seconds()
        
        # Детальное логирование ошибки
        logger.error(
            "WEBHOOK_REQUEST_ERROR",
            extra={
                **log_context,
                "processing_time_seconds": error_time,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "step": "error_handling"
            },
            exc_info=True
        )

        # Обрабатываем ошибку и возвращаем соответствующий ответ
        error_response = error_handler.handle_error(
            e,
            {
                "user_id": request.session.user_id,
                "session_id": request.session.session_id,
                "request_text": request.request.original_utterance[:100] if request.request.original_utterance else "",
                "correlation_id": correlation_id
            },
        )

        logger.info(
            "ERROR_RESPONSE_GENERATED",
            extra={
                **log_context,
                "error_response_generated": True,
                "processing_time_seconds": error_time
            }
        )

        # Формируем полный ответ с ошибкой
        return YandexResponseModel(
            response=error_response,
            session=request.session,
            version=request.version,
        )


@router.get("/health")
async def health_check() -> dict[str, Any]:
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
                "error_handler": "ok",
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.post("/cleanup-sessions")
async def cleanup_sessions() -> dict[str, Any]:
    """
    Эндпоинт для принудительной очистки устаревших сессий.
    """
    try:
        cleaned_count = dialog_handler.session_manager.cleanup_expired_sessions()
        return {"status": "success", "cleaned_sessions": cleaned_count}
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")
