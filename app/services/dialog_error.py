"""
Централизованная система обработки ошибок для диалогов.
"""
from typing import Dict, Any, Optional
from app.services.error_recovery import ErrorType


class DialogError(Exception):
    """Базовый класс для ошибок диалогов."""
    
    def __init__(
        self, 
        error_type: ErrorType, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.error_type = error_type
        self.context = context or {}
        self.user_id = user_id
        self.session_id = session_id
        super().__init__(message)


class ValidationError(DialogError):
    """Ошибка валидации пользовательского ввода."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.VALIDATION_ERROR, message, **kwargs)


class DataMissingError(DialogError):
    """Ошибка отсутствия необходимых данных."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.DATA_MISSING, message, **kwargs)


class CalculationError(DialogError):
    """Ошибка в астрологических вычислениях."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.CALCULATION_ERROR, message, **kwargs)


class ExternalServiceError(DialogError):
    """Ошибка внешнего сервиса."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.EXTERNAL_SERVICE_ERROR, message, **kwargs)


class AmbiguousIntentError(DialogError):
    """Ошибка неоднозначного интента."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.INTENT_AMBIGUOUS, message, **kwargs)


class UserInputUnclearError(DialogError):
    """Ошибка неясного ввода пользователя."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.USER_INPUT_UNCLEAR, message, **kwargs)


class SystemOverloadError(DialogError):
    """Ошибка перегрузки системы."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.SYSTEM_OVERLOAD, message, **kwargs)


class PermissionDeniedError(DialogError):
    """Ошибка доступа."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorType.PERMISSION_DENIED, message, **kwargs)