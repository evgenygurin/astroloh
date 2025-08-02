"""
Система восстановления после ошибок и обработки сбоев для Stage 5.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import traceback

from app.models.yandex_models import (
    YandexIntent, 
    YandexZodiacSign, 
    ProcessedRequest, 
    UserContext,
    YandexResponse,
    YandexButton
)
from app.services.dialog_flow_manager import DialogState


class ErrorType(Enum):
    """Типы ошибок для классификации."""
    VALIDATION_ERROR = "validation_error"
    DATA_MISSING = "data_missing"
    CALCULATION_ERROR = "calculation_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    INTENT_AMBIGUOUS = "intent_ambiguous"
    USER_INPUT_UNCLEAR = "user_input_unclear"
    SYSTEM_OVERLOAD = "system_overload"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorContext:
    """Контекст ошибки для анализа и восстановления."""
    
    def __init__(
        self, 
        error_type: ErrorType, 
        severity: ErrorSeverity, 
        message: str,
        user_id: str = None,
        session_id: str = None,
        intent: YandexIntent = None,
        dialog_state: DialogState = None
    ):
        self.error_type = error_type
        self.severity = severity
        self.message = message
        self.user_id = user_id
        self.session_id = session_id
        self.intent = intent
        self.dialog_state = dialog_state
        self.timestamp = datetime.now()
        # Не сохраняем stack trace для безопасности
        self.stack_trace = None
        self.recovery_attempts = 0
        self.resolved = False


class ErrorRecoveryManager:
    """Менеджер восстановления после ошибок."""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        # Ограничение для предотвращения DoS
        from collections import defaultdict
        self.error_counts = defaultdict(list)
        self.max_errors_per_hour = 10
        self.max_history_size = 1000
        self.recovery_strategies: Dict[ErrorType, callable] = {
            ErrorType.VALIDATION_ERROR: self._handle_validation_error,
            ErrorType.DATA_MISSING: self._handle_missing_data,
            ErrorType.CALCULATION_ERROR: self._handle_calculation_error,
            ErrorType.EXTERNAL_SERVICE_ERROR: self._handle_service_error,
            ErrorType.INTENT_AMBIGUOUS: self._handle_ambiguous_intent,
            ErrorType.USER_INPUT_UNCLEAR: self._handle_unclear_input,
            ErrorType.SYSTEM_OVERLOAD: self._handle_system_overload,
            ErrorType.PERMISSION_DENIED: self._handle_permission_error,
            ErrorType.UNKNOWN_ERROR: self._handle_unknown_error,
        }
        
        self.fallback_responses = {
            ErrorSeverity.LOW: "Небольшая неточность, но я могу помочь. Попробуем по-другому?",
            ErrorSeverity.MEDIUM: "Возникла небольшая проблема. Давайте попробуем другой подход.",
            ErrorSeverity.HIGH: "Произошла ошибка, но я не сдаюсь! Попробуем что-то другое.",
            ErrorSeverity.CRITICAL: "Извините, произошла серьезная ошибка. Давайте начнем сначала."
        }
        
        self.logger = logging.getLogger(__name__)
    
    def handle_error(
        self, 
        error: Exception, 
        context: Dict[str, Any] = None
    ) -> Tuple[ErrorContext, YandexResponse]:
        """Обрабатывает ошибку и возвращает контекст ошибки и ответ для пользователя."""
        
        # Проверяем ограничения по частоте ошибок
        user_id = context.get("user_id") if context else "anonymous"
        if self._check_rate_limit(user_id):
            return self._create_rate_limit_response()
        
        # Классифицируем ошибку
        error_type, severity = self._classify_error(error, context)
        
        # Создаем контекст ошибки
        error_context = ErrorContext(
            error_type=error_type,
            severity=severity,
            message=str(error),
            user_id=context.get("user_id") if context else None,
            session_id=context.get("session_id") if context else None,
            intent=context.get("intent") if context else None,
            dialog_state=context.get("dialog_state") if context else None
        )
        
        # Сохраняем в истории с ограничением размера
        self.error_history.append(error_context)
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
        
        # Логируем ошибку
        self._log_error(error_context)
        
        # Применяем стратегию восстановления
        recovery_response = self._apply_recovery_strategy(error_context, context)
        
        return error_context, recovery_response
    
    def _classify_error(
        self, 
        error: Exception, 
        context: Dict[str, Any] = None
    ) -> Tuple[ErrorType, ErrorSeverity]:
        """Классифицирует ошибку по типу и серьезности."""
        
        error_message = str(error).lower()
        
        # Ошибки валидации
        if any(keyword in error_message for keyword in ["validation", "invalid", "format"]):
            return ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW
        
        # Отсутствующие данные
        if any(keyword in error_message for keyword in ["missing", "required", "not found"]):
            return ErrorType.DATA_MISSING, ErrorSeverity.MEDIUM
        
        # Ошибки вычислений
        if any(keyword in error_message for keyword in ["calculation", "math", "division"]):
            return ErrorType.CALCULATION_ERROR, ErrorSeverity.MEDIUM
        
        # Ошибки внешних сервисов
        if any(keyword in error_message for keyword in ["connection", "timeout", "service"]):
            return ErrorType.EXTERNAL_SERVICE_ERROR, ErrorSeverity.HIGH
        
        # Неоднозначные интенты
        if "ambiguous" in error_message or "unclear" in error_message:
            return ErrorType.INTENT_AMBIGUOUS, ErrorSeverity.LOW
        
        # Ошибки доступа
        if any(keyword in error_message for keyword in ["permission", "access", "denied"]):
            return ErrorType.PERMISSION_DENIED, ErrorSeverity.HIGH
        
        # Проверяем тип исключения
        if isinstance(error, ValueError):
            return ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW
        elif isinstance(error, KeyError):
            return ErrorType.DATA_MISSING, ErrorSeverity.MEDIUM
        elif isinstance(error, ConnectionError):
            return ErrorType.EXTERNAL_SERVICE_ERROR, ErrorSeverity.HIGH
        elif isinstance(error, MemoryError):
            return ErrorType.SYSTEM_OVERLOAD, ErrorSeverity.CRITICAL
        
        return ErrorType.UNKNOWN_ERROR, ErrorSeverity.MEDIUM
    
    def _apply_recovery_strategy(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Применяет стратегию восстановления."""
        
        strategy = self.recovery_strategies.get(
            error_context.error_type, 
            self._handle_unknown_error
        )
        
        try:
            return strategy(error_context, context)
        except Exception as recovery_error:
            self.logger.error(f"Recovery strategy failed: {recovery_error}")
            return self._create_fallback_response(error_context)
    
    def _handle_validation_error(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает ошибки валидации."""
        
        text = "Кажется, данные введены неверно. Давайте попробуем ещё раз!"
        
        buttons = [
            YandexButton(title="Пример формата", payload={"action": "format_example"}),
            YandexButton(title="Помощь", payload={"action": "help"}),
            YandexButton(title="Начать сначала", payload={"action": "restart"})
        ]
        
        # Добавляем специфичные предложения
        if error_context.intent == YandexIntent.HOROSCOPE:
            buttons.insert(0, YandexButton(
                title="Пример: 15 марта 1990", 
                payload={"action": "date_example"}
            ))
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _handle_missing_data(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает отсутствие данных."""
        
        text = "Для точного ответа нужно немного больше информации."
        
        buttons = []
        
        # Предлагаем варианты в зависимости от интента
        if error_context.intent == YandexIntent.HOROSCOPE:
            text += " Назовите вашу дату рождения."
            buttons = [
                YandexButton(title="Указать дату", payload={"action": "provide_date"}),
                YandexButton(title="Общий гороскоп", payload={"action": "general_horoscope"})
            ]
        elif error_context.intent == YandexIntent.COMPATIBILITY:
            text += " Назовите знаки зодиака для проверки совместимости."
            buttons = [
                YandexButton(title="Мой знак", payload={"action": "my_sign"}),
                YandexButton(title="Знак партнера", payload={"action": "partner_sign"})
            ]
        
        buttons.extend([
            YandexButton(title="Помощь", payload={"action": "help"}),
            YandexButton(title="Другой вопрос", payload={"action": "restart"})
        ])
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons[:4],  # Максимум 4 кнопки
            end_session=False
        )
    
    def _handle_calculation_error(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает ошибки вычислений."""
        
        text = "Произошла ошибка в астрологических вычислениях. Попробуем другой подход!"
        
        buttons = [
            YandexButton(title="Общий прогноз", payload={"action": "general_forecast"}),
            YandexButton(title="Другая дата", payload={"action": "different_date"}),
            YandexButton(title="Совет дня", payload={"action": "daily_advice"}),
            YandexButton(title="Помощь", payload={"action": "help"})
        ]
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _handle_service_error(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает ошибки внешних сервисов."""
        
        text = "Временные проблемы с подключением к астрологическим данным. Попробуем что-то другое!"
        
        buttons = [
            YandexButton(title="Повторить", payload={"action": "retry"}),
            YandexButton(title="Общий совет", payload={"action": "general_advice"}),
            YandexButton(title="Позже", payload={"action": "try_later"}),
            YandexButton(title="Помощь", payload={"action": "help"})
        ]
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _handle_ambiguous_intent(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает неоднозначные интенты."""
        
        text = "Не совсем поняла ваш запрос. Выберите, что вас интересует:"
        
        buttons = [
            YandexButton(title="Мой гороскоп", payload={"action": "horoscope"}),
            YandexButton(title="Совместимость", payload={"action": "compatibility"}),
            YandexButton(title="Лунный календарь", payload={"action": "lunar"}),
            YandexButton(title="Совет", payload={"action": "advice"})
        ]
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _handle_unclear_input(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает неясный ввод пользователя."""
        
        text = "Попробуйте переформулировать вопрос или выберите из предложенных вариантов:"
        
        buttons = [
            YandexButton(title="Что умеешь?", payload={"action": "capabilities"}),
            YandexButton(title="Примеры вопросов", payload={"action": "examples"}),
            YandexButton(title="Помощь", payload={"action": "help"}),
            YandexButton(title="Начать сначала", payload={"action": "restart"})
        ]
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _handle_system_overload(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает перегрузку системы."""
        
        text = "Система временно перегружена. Попробуйте немного позже или выберите более простой запрос."
        
        buttons = [
            YandexButton(title="Простой гороскоп", payload={"action": "simple_horoscope"}),
            YandexButton(title="Совет дня", payload={"action": "daily_advice"}),
            YandexButton(title="Позже", payload={"action": "try_later"}),
            YandexButton(title="Завершить", payload={"action": "end"})
        ]
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _handle_permission_error(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает ошибки доступа."""
        
        text = "Недостаточно прав для выполнения этого действия. Попробуйте что-то другое."
        
        buttons = [
            YandexButton(title="Общий гороскоп", payload={"action": "public_horoscope"}),
            YandexButton(title="Совет дня", payload={"action": "daily_advice"}),
            YandexButton(title="Помощь", payload={"action": "help"}),
            YandexButton(title="Главное меню", payload={"action": "main_menu"})
        ]
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _handle_unknown_error(
        self, 
        error_context: ErrorContext, 
        context: Dict[str, Any] = None
    ) -> YandexResponse:
        """Обрабатывает неизвестные ошибки."""
        
        return self._create_fallback_response(error_context)
    
    def _create_fallback_response(self, error_context: ErrorContext) -> YandexResponse:
        """Создает резервный ответ."""
        
        text = self.fallback_responses.get(
            error_context.severity, 
            "Произошла ошибка, но я готова помочь! Попробуем что-то другое?"
        )
        
        buttons = [
            YandexButton(title="Начать сначала", payload={"action": "restart"}),
            YandexButton(title="Помощь", payload={"action": "help"}),
            YandexButton(title="Завершить", payload={"action": "end"})
        ]
        
        return YandexResponse(
            text=text,
            tts=text,
            buttons=buttons,
            end_session=False
        )
    
    def _log_error(self, error_context: ErrorContext) -> None:
        """Логирует ошибку."""
        
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_context.severity, logging.ERROR)
        
        self.logger.log(
            log_level,
            f"Error in dialog: {error_context.error_type.value} - {error_context.message}",
            extra={
                "user_id": error_context.user_id,
                "session_id": error_context.session_id,
                "intent": error_context.intent.value if error_context.intent else None,
                "dialog_state": error_context.dialog_state.value if error_context.dialog_state else None,
                "severity": error_context.severity.value,
                "timestamp": error_context.timestamp.isoformat()
            }
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику ошибок."""
        
        if not self.error_history:
            return {"total_errors": 0}
        
        # Подсчитываем ошибки по типам
        error_types = {}
        severity_counts = {}
        recent_errors = 0
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for error in self.error_history:
            # По типам
            error_type = error.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # По серьезности
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Недавние ошибки
            if error.timestamp > cutoff_time:
                recent_errors += 1
        
        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "severity_counts": severity_counts,
            "recent_errors_24h": recent_errors,
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def cleanup_old_errors(self, days: int = 7) -> int:
        """Очищает старые ошибки из истории."""
        
        cutoff_time = datetime.now() - timedelta(days=days)
        initial_count = len(self.error_history)
        
        self.error_history = [
            error for error in self.error_history 
            if error.timestamp > cutoff_time
        ]
        
        cleaned_count = initial_count - len(self.error_history)
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old error records")
        
        return cleaned_count
    
    def get_recovery_suggestions(
        self, 
        user_id: str, 
        session_id: str
    ) -> List[str]:
        """Возвращает предложения для восстановления на основе истории ошибок пользователя."""
        
        user_errors = [
            error for error in self.error_history[-10:]  # Последние 10 ошибок
            if error.user_id == user_id
        ]
        
        if not user_errors:
            return [
                "Попробуйте простой вопрос",
                "Скажите 'помощь' для справки",
                "Начните с гороскопа"
            ]
        
        # Анализируем частые ошибки пользователя
        common_errors = {}
        for error in user_errors:
            error_type = error.error_type
            common_errors[error_type] = common_errors.get(error_type, 0) + 1
        
        suggestions = []
        
        # Предлагаем решения для частых ошибок
        if ErrorType.VALIDATION_ERROR in common_errors:
            suggestions.append("Проверьте формат даты: день.месяц.год")
        
        if ErrorType.DATA_MISSING in common_errors:
            suggestions.append("Укажите дату рождения для точного прогноза")
        
        if ErrorType.INTENT_AMBIGUOUS in common_errors:
            suggestions.append("Используйте простые фразы: 'мой гороскоп'")
        
        # Добавляем общие предложения
        suggestions.extend([
            "Попробуйте переформулировать вопрос",
            "Выберите из предложенных вариантов",
            "Скажите 'помощь' для инструкций"
        ])
        
        return suggestions[:4]  # Максимум 4 предложения
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Проверяет ограничения по частоте ошибок для пользователя."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Очищаем старые записи
        self.error_counts[user_id] = [
            timestamp for timestamp in self.error_counts[user_id]
            if timestamp > hour_ago
        ]
        
        # Проверяем лимит
        if len(self.error_counts[user_id]) >= self.max_errors_per_hour:
            return True
        
        # Добавляем текущую ошибку
        self.error_counts[user_id].append(now)
        return False
    
    def _create_rate_limit_response(self) -> Tuple[ErrorContext, YandexResponse]:
        """Создает ответ при превышении лимита ошибок."""
        error_context = ErrorContext(
            error_type=ErrorType.SYSTEM_OVERLOAD,
            severity=ErrorSeverity.HIGH,
            message="Rate limit exceeded for user"
        )
        
        response = YandexResponse(
            text="Слишком много ошибок. Попробуйте позже или обратитесь к администратору.",
            tts="Слишком много ошибок. Попробуйте позже.",
            buttons=[
                YandexButton(title="Позже", payload={"action": "try_later"}),
                YandexButton(title="Завершить", payload={"action": "end"})
            ],
            end_session=True
        )
        
        return error_context, response