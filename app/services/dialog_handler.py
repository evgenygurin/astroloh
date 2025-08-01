"""
Основной обработчик диалогов для навыка Яндекс.Диалогов.
"""
from typing import Dict, Any

from app.models.yandex_models import (
    YandexRequestModel, 
    YandexResponseModel, 
    YandexIntent,
    YandexZodiacSign,
    ProcessedRequest,
    UserContext
)
from app.services.intent_recognition import IntentRecognizer
from app.services.session_manager import SessionManager
from app.services.response_formatter import ResponseFormatter
from app.utils.error_handler import ErrorHandler, handle_skill_errors
from app.utils.validators import (
    DateValidator, 
    TimeValidator, 
    ZodiacValidator,
    YandexRequestValidator
)


class DialogHandler:
    """Основной класс обработки диалогов."""
    
    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.session_manager = SessionManager()
        self.response_formatter = ResponseFormatter()
        self.error_handler = ErrorHandler()
        self.date_validator = DateValidator()
        self.time_validator = TimeValidator()
        self.zodiac_validator = ZodiacValidator()
        self.request_validator = YandexRequestValidator()

    @handle_skill_errors()
    async def handle_request(self, request: YandexRequestModel) -> YandexResponseModel:
        """Обрабатывает запрос от Яндекс.Диалогов."""
        
        # Валидация запроса
        self.request_validator.validate_request_structure(request.dict())
        
        # Получение контекста пользователя
        user_context = self.session_manager.get_user_context(request.session)
        
        # Санитизация пользовательского ввода
        clean_input = self.request_validator.sanitize_user_input(
            request.request.original_utterance
        )
        
        # Распознавание интента
        processed_request = self.intent_recognizer.recognize_intent(
            clean_input, user_context
        )
        
        # Обработка интента
        response = await self._process_intent(processed_request, request.session)
        
        # Логирование
        self.error_handler.log_request_processing(
            user_id=request.session.user_id,
            session_id=request.session.session_id,
            intent=processed_request.intent.value,
            success=True
        )
        
        # Формирование полного ответа
        return YandexResponseModel(
            response=response,
            session=request.session,
            version=request.version
        )

    async def _process_intent(
        self, 
        processed_request: ProcessedRequest, 
        session
    ) -> Any:
        """Обрабатывает конкретный интент."""
        
        intent = processed_request.intent
        entities = processed_request.entities
        user_context = processed_request.user_context
        
        if intent == YandexIntent.GREET or self.session_manager.is_new_session(session):
            return await self._handle_greet(user_context, session)
        
        elif intent == YandexIntent.HOROSCOPE:
            return await self._handle_horoscope(entities, user_context, session)
        
        elif intent == YandexIntent.COMPATIBILITY:
            return await self._handle_compatibility(entities, user_context, session)
        
        elif intent == YandexIntent.NATAL_CHART:
            return await self._handle_natal_chart(entities, user_context, session)
        
        elif intent == YandexIntent.LUNAR_CALENDAR:
            return await self._handle_lunar_calendar(user_context, session)
        
        elif intent == YandexIntent.ADVICE:
            return await self._handle_advice(user_context, session)
        
        elif intent == YandexIntent.HELP:
            return await self._handle_help(user_context, session)
        
        else:
            return await self._handle_unknown(user_context, session)

    async def _handle_greet(self, user_context: UserContext, session) -> Any:
        """Обрабатывает приветствие."""
        is_returning = not self.session_manager.is_new_session(session)
        
        # Очищаем контекст для новой сессии
        if not is_returning:
            user_context = UserContext()
            self.session_manager.update_user_context(session, user_context)
        
        return self.response_formatter.format_welcome_response(is_returning)

    async def _handle_horoscope(
        self, 
        entities: Dict[str, Any], 
        user_context: UserContext, 
        session
    ) -> Any:
        """Обрабатывает запрос гороскопа."""
        
        # Проверяем, есть ли дата рождения в entities или в контексте
        birth_date = None
        
        if entities.get("birth_date"):
            birth_date_str = entities["birth_date"]
            birth_date = self.date_validator.parse_date_string(birth_date_str)
            
            if birth_date:
                self.date_validator.validate_birth_date(birth_date)
                user_context.birth_date = birth_date.isoformat()
                zodiac_sign = self.date_validator.get_zodiac_sign_by_date(birth_date)
                user_context.zodiac_sign = zodiac_sign
                self.session_manager.clear_awaiting_data(session, user_context)
                
                return self.response_formatter.format_horoscope_response(zodiac_sign)
        
        elif entities.get("dates"):
            birth_date_str = entities["dates"][0]
            birth_date = self.date_validator.parse_date_string(birth_date_str)
            
            if birth_date:
                self.date_validator.validate_birth_date(birth_date)
                user_context.birth_date = birth_date.isoformat()
                zodiac_sign = self.date_validator.get_zodiac_sign_by_date(birth_date)
                user_context.zodiac_sign = zodiac_sign
                self.session_manager.clear_awaiting_data(session, user_context)
                
                return self.response_formatter.format_horoscope_response(zodiac_sign)
        
        elif user_context.birth_date:
            # Используем сохраненную дату рождения
            from datetime import date
            birth_date = date.fromisoformat(user_context.birth_date)
            zodiac_sign = self.date_validator.get_zodiac_sign_by_date(birth_date)
            
            return self.response_formatter.format_horoscope_response(zodiac_sign)
        
        # Если даты нет, запрашиваем её
        self.session_manager.set_awaiting_data(
            session, user_context, "birth_date", YandexIntent.HOROSCOPE
        )
        
        return self.response_formatter.format_horoscope_request_response()

    async def _handle_compatibility(
        self, 
        entities: Dict[str, Any], 
        user_context: UserContext, 
        session
    ) -> Any:
        """Обрабатывает запрос совместимости."""
        
        zodiac_signs = entities.get("zodiac_signs", [])
        
        # Если есть оба знака
        if len(zodiac_signs) >= 2:
            sign1, sign2 = zodiac_signs[0], zodiac_signs[1]
            user_context.zodiac_sign = sign1
            user_context.partner_sign = sign2
            self.session_manager.clear_awaiting_data(session, user_context)
            
            return self.response_formatter.format_compatibility_response(sign1, sign2)
        
        # Если есть один знак
        elif len(zodiac_signs) == 1:
            if not user_context.zodiac_sign:
                user_context.zodiac_sign = zodiac_signs[0]
                self.session_manager.set_awaiting_data(
                    session, user_context, "partner_sign", YandexIntent.COMPATIBILITY
                )
                return self.response_formatter.format_compatibility_request_response(2)
            else:
                user_context.partner_sign = zodiac_signs[0]
                self.session_manager.clear_awaiting_data(session, user_context)
                
                return self.response_formatter.format_compatibility_response(
                    user_context.zodiac_sign, user_context.partner_sign
                )
        
        # Если знаков нет, запрашиваем первый
        if not user_context.zodiac_sign:
            self.session_manager.set_awaiting_data(
                session, user_context, "zodiac_sign", YandexIntent.COMPATIBILITY
            )
            return self.response_formatter.format_compatibility_request_response(1)
        
        # Если есть первый знак, запрашиваем второй
        elif not user_context.partner_sign:
            self.session_manager.set_awaiting_data(
                session, user_context, "partner_sign", YandexIntent.COMPATIBILITY
            )
            return self.response_formatter.format_compatibility_request_response(2)
        
        # Если оба знака есть в контексте
        else:
            self.session_manager.clear_awaiting_data(session, user_context)
            return self.response_formatter.format_compatibility_response(
                user_context.zodiac_sign, user_context.partner_sign
            )

    async def _handle_natal_chart(
        self, 
        entities: Dict[str, Any], 
        user_context: UserContext, 
        session
    ) -> Any:
        """Обрабатывает запрос натальной карты."""
        # Пока что возвращаем заглушку
        return self.response_formatter.format_error_response("general")

    async def _handle_lunar_calendar(self, user_context: UserContext, session) -> Any:
        """Обрабатывает запрос лунного календаря."""
        # Пока что возвращаем заглушку  
        return self.response_formatter.format_error_response("general")

    async def _handle_advice(self, user_context: UserContext, session) -> Any:
        """Обрабатывает запрос астрологического совета."""
        self.session_manager.clear_awaiting_data(session, user_context)
        return self.response_formatter.format_advice_response()

    async def _handle_help(self, user_context: UserContext, session) -> Any:
        """Обрабатывает запрос справки."""
        self.session_manager.clear_awaiting_data(session, user_context)
        return self.response_formatter.format_help_response()

    async def _handle_unknown(self, user_context: UserContext, session) -> Any:
        """Обрабатывает неизвестный интент."""
        return self.response_formatter.format_error_response("general")


# Глобальный экземпляр обработчика диалогов
dialog_handler = DialogHandler()