"""
Обработчик ошибок для навыка Яндекс.Диалогов.
"""
import logging
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import HTTPException
from pydantic import ValidationError

from app.models.yandex_models import YandexResponse
from app.services.response_formatter import ResponseFormatter


logger = logging.getLogger(__name__)


class SkillError(Exception):
    """Базовое исключение навыка."""
    def __init__(self, message: str, error_type: str = "general"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)


class ValidationSkillError(SkillError):
    """Ошибка валидации данных."""
    def __init__(self, message: str, field: str):
        self.field = field
        super().__init__(message, "validation")


class ProcessingSkillError(SkillError):
    """Ошибка обработки запроса."""
    def __init__(self, message: str):
        super().__init__(message, "processing")


class DataSkillError(SkillError):
    """Ошибка данных."""
    def __init__(self, message: str):
        super().__init__(message, "data")


class ErrorHandler:
    """Класс для обработки ошибок навыка."""
    
    def __init__(self):
        self.response_formatter = ResponseFormatter()
        self.error_mappings = {
            "validation": "invalid_data",
            "processing": "general", 
            "data": "no_data",
            "date_parsing": "invalid_date",
            "zodiac_parsing": "invalid_sign"
        }

    def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> YandexResponse:
        """Обрабатывает ошибку и возвращает соответствующий ответ."""
        
        if isinstance(error, SkillError):
            return self._handle_skill_error(error, context)
        elif isinstance(error, ValidationError):
            return self._handle_validation_error(error, context)
        elif isinstance(error, HTTPException):
            return self._handle_http_error(error, context)
        else:
            return self._handle_unknown_error(error, context)

    def _handle_skill_error(
        self, 
        error: SkillError, 
        context: Optional[Dict[str, Any]] = None
    ) -> YandexResponse:
        """Обрабатывает ошибки навыка."""
        logger.warning(f"Skill error: {error.message}", extra={"context": context})
        
        error_type = self.error_mappings.get(error.error_type, "general")
        return self.response_formatter.format_error_response(error_type)

    def _handle_validation_error(
        self, 
        error: ValidationError, 
        context: Optional[Dict[str, Any]] = None
    ) -> YandexResponse:
        """Обрабатывает ошибки валидации Pydantic."""
        logger.warning(f"Validation error: {error}", extra={"context": context})
        
        return self.response_formatter.format_error_response("invalid_data")

    def _handle_http_error(
        self, 
        error: HTTPException, 
        context: Optional[Dict[str, Any]] = None
    ) -> YandexResponse:
        """Обрабатывает HTTP ошибки."""
        logger.error(f"HTTP error: {error.detail}", extra={"context": context})
        
        return self.response_formatter.format_error_response("general")

    def _handle_unknown_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> YandexResponse:
        """Обрабатывает неизвестные ошибки."""
        logger.error(f"Unknown error: {str(error)}", extra={"context": context}, exc_info=True)
        
        return self.response_formatter.format_error_response("general")

    def log_request_processing(
        self, 
        user_id: str, 
        session_id: str, 
        intent: str, 
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Логирует обработку запроса."""
        log_data = {
            "user_id": user_id,
            "session_id": session_id,
            "intent": intent,
            "success": success
        }
        
        if success:
            logger.info("Request processed successfully", extra=log_data)
        else:
            log_data["error"] = error
            logger.error("Request processing failed", extra=log_data)


def handle_skill_errors(error_handler: Optional[ErrorHandler] = None):
    """Декоратор для обработки ошибок в хендлерах навыка."""
    if error_handler is None:
        error_handler = ErrorHandler()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:500],  # Ограничиваем размер для безопасности
                    "kwargs": str(kwargs)[:500]
                }
                return error_handler.handle_error(e, context)
        return wrapper
    return decorator


# Глобальный экземпляр обработчика ошибок
error_handler = ErrorHandler()