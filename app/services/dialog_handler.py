"""
Основной обработчик диалогов для навыка Яндекс.Диалогов с расширенной функциональностью.
Интегрирует продвинутое управление диалогами, персонализацию и безопасное хранение данных.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from app.core.logging_config import log_ai_operation, log_dialog_flow
from app.models.yandex_models import (
    ProcessedRequest,
    UserContext,
    YandexIntent,
    YandexRequestModel,
    YandexResponseModel,
)
from app.services.ai_horoscope_service import ai_horoscope_service
from app.services.astrology_calculator import AstrologyCalculator
from app.services.conversation_manager import ConversationManager
from app.services.dialog_flow_manager import DialogFlowManager, DialogState
from app.services.horoscope_generator import HoroscopeGenerator, HoroscopePeriod
from app.services.intent_recognition import IntentRecognizer
from app.services.lunar_calendar import LunarCalendar
from app.services.natal_chart import NatalChartCalculator
from app.services.response_formatter import ResponseFormatter
from app.services.session_manager import SessionManager
from app.services.transit_calculator import TransitCalculator
from app.utils.error_handler import ErrorHandler, handle_skill_errors
from app.utils.validators import (
    DateValidator,
    TimeValidator,
    YandexRequestValidator,
    ZodiacValidator,
)

logger = logging.getLogger(__name__)


class DialogHandler:
    """Основной класс обработки диалогов с расширенной функциональностью."""

    def __init__(self):
        # Основные компоненты
        self.intent_recognizer = IntentRecognizer()
        self.session_manager = SessionManager()
        self.response_formatter = ResponseFormatter()
        self.horoscope_generator = HoroscopeGenerator()
        self.natal_chart_calculator = NatalChartCalculator()
        self.lunar_calendar = LunarCalendar()
        self.astro_calculator = AstrologyCalculator()
        self.transit_calculator = TransitCalculator()

        # AI-powered сервисы
        self.ai_horoscope_service = ai_horoscope_service

        # Расширенная функциональность Stage 5
        self.dialog_flow_manager = DialogFlowManager()
        self.conversation_manager = ConversationManager()
        self.user_manager = (
            None  # Will be initialized when db_session is available
        )

        # Система восстановления после ошибок
        from app.services.error_recovery import ErrorRecoveryManager

        self.error_recovery_manager = ErrorRecoveryManager()

        # Утилиты
        self.error_handler = ErrorHandler()
        self.date_validator = DateValidator()
        self.time_validator = TimeValidator()
        self.zodiac_validator = ZodiacValidator()
        self.request_validator = YandexRequestValidator()

        # Логирование
        self.logger = logging.getLogger(__name__)

    def extract_user_context(
        self, request: YandexRequestModel
    ) -> Dict[str, Any]:
        """
        Извлекает пользовательский контекст из запроса.

        Args:
            request: Запрос от Яндекс.Диалогов

        Returns:
            Словарь с контекстом пользователя
        """
        return {
            "user_id": request.session.user_id or "test_user",
            "session_id": request.session.session_id,
            "message_id": request.session.message_id,
        }

    def log_interaction(
        self,
        request: YandexRequestModel,
        response,
        intent: str,
        confidence: float,
    ):
        """
        Логирует взаимодействие пользователя с навыком.

        Args:
            request: Запрос пользователя
            response: Ответ навыка
            intent: Распознанный интент
            confidence: Уверенность в распознавании
        """
        self.logger.info(
            f"User interaction: intent={intent}, confidence={confidence:.2f}, "
            f"user_id={request.session.user_id}, session_id={request.session.session_id}"
        )

    @handle_skill_errors()
    async def handle_request(
        self, request: YandexRequestModel
    ) -> YandexResponseModel:
        """Обрабатывает запрос от Яндекс.Диалогов с расширенной функциональностью."""

        # Создаем correlation ID для диалога (если не передан из webhook)
        dialog_correlation_id = str(uuid.uuid4())
        start_time = datetime.now()

        # Контекст логирования для диалога
        log_context = {
            "correlation_id": dialog_correlation_id,
            "user_id": request.session.user_id,
            "session_id": request.session.session_id,
            "message_id": request.session.message_id,
            "timestamp": start_time.isoformat(),
        }

        logger.info(
            "DIALOG_HANDLER_START",
            extra={
                **log_context,
                "request_type": getattr(
                    request.request, "type", "SimpleUtterance"
                ),
                "new_session": request.session.new,
                "original_utterance": request.request.original_utterance[:100]
                if request.request.original_utterance
                else "",
            },
        )

        try:
            # Валидация запроса
            logger.info(
                "REQUEST_VALIDATION_START",
                extra={**log_context, "step": "validation"},
            )
            self.request_validator.validate_request_structure(
                request.model_dump()
            )
            logger.info(
                "REQUEST_VALIDATION_SUCCESS",
                extra={**log_context, "step": "validation_complete"},
            )

            # Получение контекста пользователя
            logger.info(
                "USER_CONTEXT_RETRIEVAL_START",
                extra={**log_context, "step": "context_retrieval"},
            )
            user_context = self.session_manager.get_user_context(
                request.session
            )

            logger.info(
                "USER_CONTEXT_RETRIEVAL_SUCCESS",
                extra={
                    **log_context,
                    "step": "context_retrieval_complete",
                    "context_data": {
                        "awaiting_data": getattr(
                            user_context, "awaiting_data", None
                        ),
                        "conversation_step": getattr(
                            user_context, "conversation_step", 0
                        ),
                        "user_preferences": getattr(
                            user_context, "user_preferences", None
                        )
                        is not None,
                        "zodiac_sign": getattr(
                            user_context, "zodiac_sign", None
                        ),
                        "has_birth_date": getattr(
                            user_context, "birth_date", None
                        )
                        is not None,
                    },
                },
            )

            # Обработка в зависимости от типа запроса
            logger.info(
                "INPUT_PROCESSING_START",
                extra={**log_context, "step": "input_processing"},
            )
            if request.request.type == "ButtonPressed":
                # Обрабатываем нажатия кнопок
                clean_input = self._handle_button_press(request)
                logger.info(
                    "BUTTON_PRESS_PROCESSED",
                    extra={
                        **log_context,
                        "input_type": "button",
                        "clean_input": clean_input[:50],
                    },
                )
            else:
                # Санитизация пользовательского ввода для обычных запросов
                original_input = request.request.original_utterance or ""
                clean_input = self.request_validator.sanitize_user_input(
                    original_input
                )
                logger.info(
                    "TEXT_INPUT_PROCESSED",
                    extra={
                        **log_context,
                        "input_type": "text",
                        "original_length": len(original_input),
                        "clean_length": len(clean_input),
                        "sanitized": original_input != clean_input,
                        "clean_input": clean_input[:50],
                    },
                )

            # Распознавание интента с расширенными возможностями
            logger.info(
                "INTENT_RECOGNITION_START",
                extra={**log_context, "step": "intent_recognition"},
            )

            intent_start_time = datetime.now()
            processed_request = self.intent_recognizer.recognize_intent(
                clean_input, user_context
            )
            intent_processing_time = (
                datetime.now() - intent_start_time
            ).total_seconds()

            logger.info(
                f"Intent recognized: {processed_request.intent.value} (confidence: {processed_request.confidence:.2f}) for input: '{clean_input}'"
            )

            # Используем новую функцию логирования диалога
            log_dialog_flow(
                user_id=request.session.user_id or "anonymous",
                session_id=request.session.session_id,
                intent=processed_request.intent.value,
                confidence=processed_request.confidence,
                processing_time=intent_processing_time,
            )

            # Обработка в контексте разговора (Stage 5 enhancement)
            logger.info(
                "CONVERSATION_PROCESSING_START",
                extra={**log_context, "step": "conversation_processing"},
            )

            conversation_start_time = datetime.now()
            conversation_result = (
                await self.conversation_manager.process_conversation(
                    user_id=request.session.user_id,
                    session_id=request.session.session_id,
                    processed_request=processed_request,
                )
            )
            conversation_processing_time = (
                datetime.now() - conversation_start_time
            ).total_seconds()

            if (
                isinstance(conversation_result, tuple)
                and len(conversation_result) == 2
            ):
                dialog_state, response_context = conversation_result
            else:
                dialog_state = DialogState.INITIAL
                response_context = {}

            logger.info(
                "CONVERSATION_PROCESSING_SUCCESS",
                extra={
                    **log_context,
                    "step": "conversation_processing_complete",
                    "processing_time_seconds": conversation_processing_time,
                    "conversation_result": {
                        "dialog_state": dialog_state.value
                        if hasattr(dialog_state, "value")
                        else str(dialog_state),
                        "has_response_context": bool(response_context),
                        "response_context_keys": list(response_context.keys())
                        if response_context
                        else [],
                    },
                },
            )

            # Генерируем ответ с учетом состояния диалога и контекста
            logger.info(
                "RESPONSE_GENERATION_START",
                extra={**log_context, "step": "response_generation"},
            )

            response_start_time = datetime.now()
            response = await self._generate_contextual_response(
                dialog_state,
                response_context,
                processed_request,
                request.session,
            )
            response_generation_time = (
                datetime.now() - response_start_time
            ).total_seconds()

            logger.info(
                "RESPONSE_GENERATION_SUCCESS",
                extra={
                    **log_context,
                    "step": "response_generation_complete",
                    "processing_time_seconds": response_generation_time,
                    "response_preview": {
                        "text_length": len(response.text)
                        if hasattr(response, "text") and response.text
                        else 0,
                        "has_tts": bool(getattr(response, "tts", None)),
                        "has_buttons": bool(
                            getattr(response, "buttons", None)
                        ),
                        "has_card": bool(getattr(response, "card", None)),
                        "end_session": getattr(response, "end_session", False),
                    },
                },
            )

        except Exception as e:
            self.logger.error(
                f"Error in conversation processing: {str(e)}", exc_info=True
            )

            # Alice-совместимая обработка ошибок
            # Создаем dummy processed_request если он не был создан
            dummy_processed_request = None
            try:
                dummy_processed_request = processed_request
            except NameError:
                # processed_request не был создан из-за ошибки в валидации или распознавании интента
                from app.models.yandex_models import ProcessedRequest, YandexIntent

                dummy_processed_request = ProcessedRequest(
                    intent=YandexIntent.UNKNOWN,
                    confidence=0.0,
                    entities={},
                    user_input=request.request.original_utterance or "",
                    context_data={},
                )

            response = await self._handle_error_gracefully(
                e, request, dummy_processed_request
            )

            # Очищаем состояние сессии при критических ошибках
            user_context = self.session_manager.get_user_context(
                request.session
            )
            if self._is_critical_error(e):
                user_context.awaiting_data = None
                user_context.conversation_step = 0
                self.session_manager.update_user_context(
                    request.session, user_context
                )

        # Логирование обработки запроса
        try:
            final_processed_request = (
                processed_request
                if "processed_request" in locals()
                else dummy_processed_request
            )
            self.error_handler.log_request_processing(
                user_id=request.session.user_id,
                session_id=request.session.session_id,
                intent=final_processed_request.intent.value
                if final_processed_request
                else "unknown",
                success=True,
            )
        except Exception as log_error:
            logger.warning(f"Failed to log request processing: {log_error}")

        # Формирование полного ответа
        return YandexResponseModel(
            response=response, session=request.session, version=request.version
        )

    async def _generate_contextual_response(
        self,
        dialog_state: DialogState,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Генерирует контекстуальный ответ на основе состояния диалога."""

        # Выбираем метод обработки на основе состояния диалога
        if dialog_state == DialogState.COLLECTING_BIRTH_DATA:
            return await self._handle_birth_data_collection(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.COLLECTING_PARTNER_DATA:
            return await self._handle_partner_data_collection(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.PROVIDING_HOROSCOPE:
            return await self._handle_personalized_horoscope(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.EXPLORING_COMPATIBILITY:
            return await self._handle_compatibility_exploration(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.DISCUSSING_NATAL_CHART:
            return await self._handle_natal_discussion(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.LUNAR_GUIDANCE:
            return await self._handle_lunar_guidance(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.GIVING_ADVICE:
            return await self._handle_personalized_advice(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.CLARIFYING_REQUEST:
            return await self._handle_clarification(
                response_context, processed_request, session
            )
        elif dialog_state == DialogState.ERROR_RECOVERY:
            return await self._handle_error_recovery(
                response_context, processed_request, session
            )
        else:
            # Fallback к стандартной обработке
            return await self._process_intent(processed_request, session)

    async def _handle_birth_data_collection(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает сбор данных о рождении с персонализацией."""
        entities = processed_request.entities

        # Проверяем, какие данные уже есть в контексте потока
        flow_context = response_context.get("flow_context", {})
        missing_data = response_context.get("required_data", [])

        if "birth_date" in missing_data:
            # Формируем персонализированный запрос даты рождения
            personalization_level = response_context.get(
                "interaction_stats", {}
            ).get("personalization_level", 0)

            if personalization_level > 0.5:
                return self.response_formatter.format_personalized_birth_date_request(
                    user_returning=True,
                    suggestions=response_context.get(
                        "adaptive_suggestions", []
                    ),
                )
            else:
                return (
                    self.response_formatter.format_horoscope_request_response()
                )

        # Если данные получены, переходим к обработке
        if entities.get("dates") or flow_context.get("birth_date"):
            return await self._handle_horoscope(
                entities, processed_request.user_context, session
            )

        return self.response_formatter.format_horoscope_request_response()

    async def _handle_partner_data_collection(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает сбор данных о партнере с учетом контекста."""
        return await self._handle_compatibility(
            processed_request.entities, processed_request.user_context, session
        )

    async def _handle_personalized_horoscope(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает персонализированный гороскоп."""
        entities = processed_request.entities

        # Добавляем контекст персонализации
        if response_context.get("can_provide_service"):
            flow_context = response_context.get("flow_context", {})

            # Используем сохраненные данные пользователя
            if flow_context.get("birth_date"):
                entities["dates"] = [flow_context["birth_date"]]

            # Определяем предпочитаемый период
            preferred_periods = flow_context.get(
                "requested_periods", ["daily"]
            )
            # Note: Period preferences are analyzed but not currently used
            if "weekly" in preferred_periods:
                pass  # Weekly period preference noted
            elif "monthly" in preferred_periods:
                pass  # Monthly period preference noted

            # Генерируем персонализированный ответ
            result = await self._handle_horoscope(
                entities, processed_request.user_context, session
            )

            # Добавляем контекстные предложения
            if (
                hasattr(result, "buttons")
                and result.buttons is not None
                and response_context.get("contextual_suggestions")
            ):
                result.buttons.extend(
                    response_context["contextual_suggestions"][:2]
                )

            return result

        return await self._handle_horoscope(
            entities, processed_request.user_context, session
        )

    async def _handle_compatibility_exploration(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает исследование совместимости с расширенным контекстом."""
        return await self._handle_compatibility(
            processed_request.entities, processed_request.user_context, session
        )

    async def _handle_natal_discussion(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает обсуждение натальной карты."""
        return await self._handle_natal_chart(
            processed_request.entities, processed_request.user_context, session
        )

    async def _handle_lunar_guidance(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает лунное руководство с персонализацией."""
        return await self._handle_lunar_calendar(
            processed_request.user_context, session
        )

    async def _handle_personalized_advice(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает персонализированные советы."""
        # Анализируем предпочтения пользователя для более точных советов
        preferred_topics = response_context.get("preferred_topics", [])
        sentiment = processed_request.entities.get("sentiment", "neutral")

        return self.response_formatter.format_personalized_advice_response(
            preferred_topics=preferred_topics,
            sentiment=sentiment,
            suggestions=response_context.get("adaptive_suggestions", []),
        )

    async def _handle_clarification(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает запросы на уточнение."""
        return self.response_formatter.format_clarification_response(
            recent_context=processed_request.entities.get(
                "recent_context", []
            ),
            suggestions=response_context.get("suggestions", []),
        )

    async def _handle_error_recovery(
        self,
        response_context: Dict[str, Any],
        processed_request: ProcessedRequest,
        session,
    ) -> Any:
        """Обрабатывает восстановление после ошибок с персонализацией."""
        error_suggestions = response_context.get("error_suggestions", [])

        # Получаем персонализированные предложения для восстановления
        if (
            processed_request.user_context
            and processed_request.user_context.user_id
        ):
            recovery_suggestions = (
                self.error_recovery_manager.get_recovery_suggestions(
                    processed_request.user_context.user_id,
                    session.session_id
                    if hasattr(session, "session_id")
                    else "unknown",
                )
            )
            error_suggestions.extend(recovery_suggestions)

        # Убираем дубликаты и ограничиваем количество
        unique_suggestions = list(dict.fromkeys(error_suggestions))[:4]

        return self.response_formatter.format_error_recovery_response(
            unique_suggestions
        )

    async def _process_intent(
        self, processed_request: ProcessedRequest, session
    ) -> Any:
        """Обрабатывает конкретный интент."""

        intent = processed_request.intent
        entities = processed_request.entities
        user_context = processed_request.user_context

        if (
            intent == YandexIntent.GREET
            or self.session_manager.is_new_session(session)
        ):
            return await self._handle_greet(user_context, session)

        elif intent == YandexIntent.HOROSCOPE:
            return await self._handle_horoscope(
                entities, user_context, session
            )

        elif intent == YandexIntent.COMPATIBILITY:
            return await self._handle_compatibility(
                entities, user_context, session
            )

        elif intent == YandexIntent.NATAL_CHART:
            return await self._handle_natal_chart(
                entities, user_context, session
            )

        elif intent == YandexIntent.LUNAR_CALENDAR:
            return await self._handle_lunar_calendar(user_context, session)

        elif intent == YandexIntent.TRANSITS:
            return await self._handle_transits(entities, user_context, session)

        elif intent == YandexIntent.PROGRESSIONS:
            return await self._handle_progressions(
                entities, user_context, session
            )

        elif intent == YandexIntent.SOLAR_RETURN:
            return await self._handle_solar_return(
                entities, user_context, session
            )

        elif intent == YandexIntent.LUNAR_RETURN:
            return await self._handle_lunar_return(
                entities, user_context, session
            )

        elif intent == YandexIntent.ADVICE:
            return await self._handle_advice(user_context, session)

        elif intent == YandexIntent.HELP:
            return await self._handle_help(user_context, session)

        elif intent == YandexIntent.EXIT:
            return await self._handle_exit(user_context, session)

        else:
            return await self._handle_unknown(user_context, session)

    async def _handle_greet(self, user_context: UserContext, session) -> Any:
        """Обрабатывает приветствие."""
        logger.info("INTENT_GREET_START: Processing greeting")
        is_returning = not self.session_manager.is_new_session(session)
        logger.info(f"INTENT_GREET_USER_TYPE: returning={is_returning}")

        # Очищаем контекст для новой сессии
        if not is_returning:
            logger.info(
                "INTENT_GREET_NEW_USER: Clearing context for new session"
            )
            user_context = UserContext()
            self.session_manager.update_user_context(session, user_context)

        response = self.response_formatter.format_welcome_response(
            is_returning
        )
        logger.info("INTENT_GREET_SUCCESS: Generated welcome response")
        return response

    async def _handle_horoscope(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос гороскопа."""
        logger.info("INTENT_HOROSCOPE_START: Processing horoscope request")
        logger.info(f"INTENT_HOROSCOPE_ENTITIES: {list(entities.keys())}")
        logger.info(
            f"INTENT_HOROSCOPE_CONTEXT: birth_date={user_context.birth_date}, zodiac_sign={user_context.zodiac_sign}"
        )

        # Проверяем, есть ли дата рождения в entities или в контексте
        birth_date = None

        if entities.get("birth_date"):
            birth_date_str = entities["birth_date"]
            birth_date = self.date_validator.parse_date_string(birth_date_str)

            if birth_date:
                self.date_validator.validate_birth_date(birth_date)
                user_context.birth_date = birth_date.isoformat()
                zodiac_sign = self.date_validator.get_zodiac_sign_by_date(
                    birth_date
                )
                user_context.zodiac_sign = zodiac_sign
                self.session_manager.clear_awaiting_data(session, user_context)

                # Генерируем персональный гороскоп
                horoscope = (
                    self.horoscope_generator.generate_personalized_horoscope(
                        zodiac_sign=zodiac_sign,
                        birth_date=birth_date,
                        period=HoroscopePeriod.DAILY,
                    )
                )

                return self.response_formatter.format_horoscope_response(
                    zodiac_sign, horoscope
                )

        elif entities.get("dates"):
            # Проверяем контекст: это дата прогноза или дата рождения?
            date_str = entities["dates"][0]
            parsed_date = self.date_validator.parse_date_string(date_str)

            if parsed_date:
                # Определяем тип даты на основе контекста запроса
                from datetime import date

                current_date = date.today()

                # Если дата в будущем или сегодня, это дата прогноза
                if parsed_date >= current_date:
                    logger.info(
                        f"INTENT_HOROSCOPE_FORECAST_DATE: date={parsed_date.isoformat()}"
                    )

                    # Если у пользователя уже есть знак зодиака, используем его
                    if user_context.zodiac_sign:
                        zodiac_sign = user_context.zodiac_sign
                        logger.info(
                            f"INTENT_HOROSCOPE_USING_SAVED_SIGN: {zodiac_sign}"
                        )
                    elif entities.get("zodiac_signs"):
                        zodiac_sign = entities["zodiac_signs"][0]
                        logger.info(
                            f"INTENT_HOROSCOPE_USING_EXTRACTED_SIGN: {zodiac_sign}"
                        )
                    else:
                        # Запрашиваем знак зодиака
                        logger.info("INTENT_HOROSCOPE_REQUEST_ZODIAC_SIGN")
                        user_context.awaiting_data = "zodiac_sign"
                        self.session_manager.set_awaiting_data(
                            session, user_context, "zodiac_sign"
                        )
                        return self.response_formatter.format_clarification_response(
                            recent_context=[
                                "Для какого знака зодиака составить гороскоп?"
                            ],
                            suggestions=[
                                "Овен",
                                "Телец",
                                "Близнецы",
                                "Рак",
                                "Лев",
                                "Дева",
                            ],
                        )

                    # Генерируем гороскоп на указанную дату
                    logger.info(
                        f"Starting AI horoscope generation for {zodiac_sign} on {parsed_date.isoformat()}"
                    )
                    ai_start_time = datetime.now()
                    try:
                        horoscope = await self.ai_horoscope_service.generate_enhanced_horoscope(
                            zodiac_sign=zodiac_sign,
                            birth_date=None,  # Не передаем дату рождения для прогноза
                            period=HoroscopePeriod.DAILY,
                            forecast_date=parsed_date,  # Передаем дату прогноза
                        )
                        ai_duration = (
                            datetime.now() - ai_start_time
                        ).total_seconds()
                        ai_generated = (
                            horoscope.get("ai_generated", False)
                            if isinstance(horoscope, dict)
                            else False
                        )

                        log_ai_operation(
                            operation="horoscope",
                            zodiac_sign=zodiac_sign,
                            success=True,
                            duration=ai_duration,
                        )
                    except Exception as e:
                        ai_duration = (
                            datetime.now() - ai_start_time
                        ).total_seconds()
                        logger.error(f"AI_HOROSCOPE_ERROR: {e}")

                        log_ai_operation(
                            operation="horoscope",
                            zodiac_sign=zodiac_sign,
                            success=False,
                            duration=ai_duration,
                            error=str(e),
                        )

                        # Fallback к традиционному гороскопу
                        horoscope = self.horoscope_generator.generate_personalized_horoscope(
                            zodiac_sign=zodiac_sign,
                            birth_date=None,
                            period=HoroscopePeriod.DAILY,
                        )
                        ai_generated = False

                    logger.info(
                        f"AI horoscope generation completed - ai_generated={ai_generated}"
                    )
                    return self.response_formatter.format_horoscope_response(
                        zodiac_sign, horoscope
                    )

                # Если дата в прошлом, это дата рождения
                else:
                    logger.info(
                        f"INTENT_HOROSCOPE_BIRTH_DATE: date={parsed_date.isoformat()}"
                    )
                    self.date_validator.validate_birth_date(parsed_date)
                    user_context.birth_date = parsed_date.isoformat()
                    zodiac_sign = self.date_validator.get_zodiac_sign_by_date(
                        parsed_date
                    )
                    user_context.zodiac_sign = zodiac_sign
                    self.session_manager.clear_awaiting_data(
                        session, user_context
                    )

                    # Генерируем персональный гороскоп с AI
                    logger.info(
                        f"Starting AI horoscope generation for {zodiac_sign}"
                    )
                    ai_start_time = datetime.now()
                    try:
                        horoscope = await self.ai_horoscope_service.generate_enhanced_horoscope(
                            zodiac_sign=zodiac_sign,
                            birth_date=parsed_date,
                            period=HoroscopePeriod.DAILY,
                        )
                        ai_duration = (
                            datetime.now() - ai_start_time
                        ).total_seconds()
                        ai_generated = (
                            horoscope.get("ai_generated", False)
                            if isinstance(horoscope, dict)
                            else False
                        )

                        log_ai_operation(
                            operation="horoscope",
                            zodiac_sign=zodiac_sign,
                            success=True,
                            duration=ai_duration,
                        )
                    except Exception as e:
                        ai_duration = (
                            datetime.now() - ai_start_time
                        ).total_seconds()
                        logger.error(f"AI horoscope generation failed: {e}")

                        log_ai_operation(
                            operation="horoscope",
                            zodiac_sign=zodiac_sign,
                            success=False,
                            duration=ai_duration,
                            error=str(e),
                        )

                        # Fallback к традиционному гороскопу
                        horoscope = self.horoscope_generator.generate_personalized_horoscope(
                            zodiac_sign=zodiac_sign,
                            birth_date=parsed_date,
                            period=HoroscopePeriod.DAILY,
                        )
                        ai_generated = False

                    logger.info(
                        f"AI horoscope generation completed - ai_generated={ai_generated}"
                    )
                    return self.response_formatter.format_horoscope_response(
                        zodiac_sign, horoscope
                    )

        elif user_context.birth_date:
            # Используем сохраненную дату рождения
            from datetime import date

            birth_date = date.fromisoformat(user_context.birth_date)
            zodiac_sign = self.date_validator.get_zodiac_sign_by_date(
                birth_date
            )

            # Генерируем персональный гороскоп с AI
            try:
                horoscope = await self.ai_horoscope_service.generate_enhanced_horoscope(
                    zodiac_sign=zodiac_sign,
                    birth_date=birth_date,
                    period=HoroscopePeriod.DAILY,
                )
            except Exception as e:
                self.logger.error(f"AI horoscope generation failed: {e}")
                # Fallback к традиционному гороскопу
                horoscope = (
                    self.horoscope_generator.generate_personalized_horoscope(
                        zodiac_sign=zodiac_sign,
                        birth_date=birth_date,
                        period=HoroscopePeriod.DAILY,
                    )
                )

            return self.response_formatter.format_horoscope_response(
                zodiac_sign, horoscope
            )

        # Если даты нет, запрашиваем её
        self.session_manager.set_awaiting_data(
            session, user_context, "birth_date", YandexIntent.HOROSCOPE
        )

        return self.response_formatter.format_horoscope_request_response()

    async def _handle_compatibility(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос совместимости."""
        logger.info(
            "INTENT_COMPATIBILITY_START: Processing compatibility request"
        )
        zodiac_signs = entities.get("zodiac_signs", [])
        logger.info(
            f"INTENT_COMPATIBILITY_SIGNS: Found {len(zodiac_signs)} signs: {zodiac_signs}"
        )

        # Если есть оба знака
        if len(zodiac_signs) >= 2:
            sign1, sign2 = zodiac_signs[0], zodiac_signs[1]
            logger.info(f"INTENT_COMPATIBILITY_BOTH_SIGNS: {sign1} + {sign2}")
            user_context.zodiac_sign = sign1
            user_context.partner_sign = sign2
            self.session_manager.clear_awaiting_data(session, user_context)

            # Вычисляем совместимость с AI поддержкой
            logger.info(
                f"Starting AI compatibility analysis for {sign1} + {sign2}"
            )
            ai_start_time = datetime.now()
            try:
                compatibility = await self.ai_horoscope_service.generate_compatibility_analysis(
                    sign1, sign2, use_ai=True
                )
                ai_duration = (datetime.now() - ai_start_time).total_seconds()

                log_ai_operation(
                    operation="compatibility",
                    zodiac_sign=f"{sign1}+{sign2}",
                    success=True,
                    duration=ai_duration,
                )
            except Exception as e:
                ai_duration = (datetime.now() - ai_start_time).total_seconds()
                self.logger.error(f"AI compatibility analysis failed: {e}")

                log_ai_operation(
                    operation="compatibility",
                    zodiac_sign=f"{sign1}+{sign2}",
                    success=False,
                    duration=ai_duration,
                    error=str(e),
                )

                # Fallback к традиционному анализу
                compatibility = (
                    self.astro_calculator.calculate_compatibility_score(
                        sign1, sign2
                    )
                )

            return self.response_formatter.format_compatibility_response(
                sign1, sign2, compatibility
            )

        # Если есть один знак
        elif len(zodiac_signs) == 1:
            if not user_context.zodiac_sign:
                user_context.zodiac_sign = zodiac_signs[0]
                self.session_manager.set_awaiting_data(
                    session,
                    user_context,
                    "partner_sign",
                    YandexIntent.COMPATIBILITY,
                )
                return self.response_formatter.format_compatibility_request_response(
                    2
                )
            else:
                user_context.partner_sign = zodiac_signs[0]
                self.session_manager.clear_awaiting_data(session, user_context)

                # Вычисляем совместимость с AI поддержкой
                try:
                    compatibility = await self.ai_horoscope_service.generate_compatibility_analysis(
                        user_context.zodiac_sign,
                        user_context.partner_sign,
                        use_ai=True,
                    )
                except Exception as e:
                    self.logger.error(f"AI compatibility analysis failed: {e}")
                    # Fallback к традиционному анализу
                    compatibility = (
                        self.astro_calculator.calculate_compatibility_score(
                            user_context.zodiac_sign, user_context.partner_sign
                        )
                    )

                return self.response_formatter.format_compatibility_response(
                    user_context.zodiac_sign,
                    user_context.partner_sign,
                    compatibility,
                )

        # Если знаков нет, запрашиваем первый
        if not user_context.zodiac_sign:
            self.session_manager.set_awaiting_data(
                session,
                user_context,
                "zodiac_sign",
                YandexIntent.COMPATIBILITY,
            )
            return (
                self.response_formatter.format_compatibility_request_response(
                    1
                )
            )

        # Если есть первый знак, запрашиваем второй
        elif not user_context.partner_sign:
            self.session_manager.set_awaiting_data(
                session,
                user_context,
                "partner_sign",
                YandexIntent.COMPATIBILITY,
            )
            return (
                self.response_formatter.format_compatibility_request_response(
                    2
                )
            )

        # Если оба знака есть в контексте
        else:
            self.session_manager.clear_awaiting_data(session, user_context)

            # Вычисляем совместимость с AI поддержкой
            try:
                compatibility = await self.ai_horoscope_service.generate_compatibility_analysis(
                    user_context.zodiac_sign,
                    user_context.partner_sign,
                    use_ai=True,
                )
            except Exception as e:
                self.logger.error(f"AI compatibility analysis failed: {e}")
                # Fallback к традиционному анализу
                compatibility = (
                    self.astro_calculator.calculate_compatibility_score(
                        user_context.zodiac_sign, user_context.partner_sign
                    )
                )

            return self.response_formatter.format_compatibility_response(
                user_context.zodiac_sign,
                user_context.partner_sign,
                compatibility,
            )

    async def _handle_natal_chart(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос натальной карты."""
        logger.info("INTENT_NATAL_CHART_START: Processing natal chart request")
        logger.info(
            f"INTENT_NATAL_CHART_CONTEXT: birth_date={user_context.birth_date}"
        )

        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.NATAL_CHART
            )
            return (
                self.response_formatter.format_natal_chart_request_response()
            )

        try:
            # Парсим дату рождения
            from datetime import date

            birth_date = date.fromisoformat(user_context.birth_date)
            logger.info(
                f"INTENT_NATAL_CHART_CALCULATION_START: birth_date={birth_date}"
            )

            # Рассчитываем натальную карту
            natal_chart = self.natal_chart_calculator.calculate_natal_chart(
                birth_date
            )
            logger.info(
                f"INTENT_NATAL_CHART_SUCCESS: Calculated natal chart with {len(natal_chart.get('planets', {}))} planets"
            )

            return self.response_formatter.format_natal_chart_response(
                natal_chart
            )

        except Exception as e:
            logger.error(f"INTENT_NATAL_CHART_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("general")

    async def _handle_lunar_calendar(
        self, user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос лунного календаря."""
        logger.info(
            "INTENT_LUNAR_CALENDAR_START: Processing lunar calendar request"
        )

        try:
            from datetime import datetime

            # Получаем информацию о сегодняшнем лунном дне
            today = datetime.now()
            logger.info(
                f"INTENT_LUNAR_CALENDAR_CALCULATION: date={today.date()}"
            )
            lunar_info = self.lunar_calendar.get_lunar_day_info(today)
            logger.info(
                f"INTENT_LUNAR_CALENDAR_SUCCESS: Retrieved lunar info for day {lunar_info.get('lunar_day', 'unknown')}"
            )

            return self.response_formatter.format_lunar_calendar_response(
                lunar_info
            )

        except Exception as e:
            logger.error(
                f"INTENT_LUNAR_CALENDAR_ERROR: {str(e)}", exc_info=True
            )
            return self.response_formatter.format_error_response("general")

    async def _handle_advice(self, user_context: UserContext, session) -> Any:
        """Обрабатывает запрос астрологического совета с AI поддержкой."""
        logger.info("INTENT_ADVICE_START: Processing advice request")
        self.session_manager.clear_awaiting_data(session, user_context)

        # Пытаемся сгенерировать персонализированный совет с AI
        if user_context.zodiac_sign:
            logger.info(
                f"INTENT_ADVICE_PERSONALIZED: Using zodiac sign {user_context.zodiac_sign}"
            )
            try:
                advice = await self.ai_horoscope_service.generate_personalized_advice(
                    zodiac_sign=user_context.zodiac_sign,
                    user_context={"mood": "neutral"},
                    use_ai=True,
                )

                if advice and advice.get("ai_enhanced"):
                    return self.response_formatter.format_personalized_advice_response(
                        advice_text=advice["advice"],
                        zodiac_sign=user_context.zodiac_sign,
                    )
            except Exception as e:
                self.logger.error(f"AI advice generation failed: {e}")
                # Продолжаем к fallback

        # Fallback к обычному ответу
        return self.response_formatter.format_advice_response()

    async def _handle_help(self, user_context: UserContext, session) -> Any:
        """Обрабатывает запрос справки."""
        logger.info("INTENT_HELP_START: Processing help request")
        self.session_manager.clear_awaiting_data(session, user_context)
        logger.info("INTENT_HELP_SUCCESS: Generated help response")
        return self.response_formatter.format_help_response()

    async def _handle_exit(self, user_context: UserContext, session) -> Any:
        """Обрабатывает запрос на выход из навыка."""
        logger.info("INTENT_EXIT_START: Processing exit request")

        # Очищаем состояние сессии
        self.session_manager.clear_user_context(session)
        logger.info("INTENT_EXIT_SESSION_CLEARED: User session cleared")

        # Проверяем, хочет ли пользователь персонализированное прощание
        has_user_data = (
            user_context.zodiac_sign
            or user_context.birth_date
            or user_context.conversation_step > 2
        )
        logger.info(
            f"INTENT_EXIT_PERSONALIZATION: has_user_data={has_user_data}"
        )

        return self.response_formatter.format_goodbye_response(
            personalized=bool(has_user_data), user_context=user_context
        )

    async def _handle_unknown(self, user_context: UserContext, session) -> Any:
        """Обрабатывает неизвестный интент с помощью по контексту."""
        logger.info("INTENT_UNKNOWN_START: Processing unknown intent")
        logger.info(
            f"INTENT_UNKNOWN_CONTEXT: awaiting_data={user_context.awaiting_data}"
        )

        # Проверяем, можем ли помочь на основе текущего состояния
        if user_context.awaiting_data:
            logger.info(
                f"INTENT_UNKNOWN_AWAITING_DATA: Providing contextual help for {user_context.awaiting_data}"
            )
            # Пользователь может быть запутался в процессе ввода данных
            if user_context.awaiting_data == "birth_date":
                return self.response_formatter.format_personalized_birth_date_request(
                    user_returning=True,
                    suggestions=["Пример: 15 марта 1990", "Помощь"],
                )
            elif user_context.awaiting_data in ["zodiac_sign", "partner_sign"]:
                return self.response_formatter.format_compatibility_request_response(
                    1 if user_context.awaiting_data == "zodiac_sign" else 2
                )

        # Обычный ответ с помощью
        logger.info("INTENT_UNKNOWN_FALLBACK: Providing general clarification")
        return self.response_formatter.format_clarification_response(
            suggestions=["Мой гороскоп", "Совместимость", "Помощь"]
        )

    async def _handle_error_gracefully(
        self,
        error: Exception,
        request: YandexRequestModel,
        processed_request: ProcessedRequest,
    ) -> Any:
        """Обрабатывает ошибки без нарушения потока разговора Alice."""
        error_type = self._classify_error(error)

        # Пробуем систему восстановления сначала
        try:
            recovery_response = await self.error_recovery_manager.handle_error(
                error,
                request,
                {
                    "user_id": request.session.user_id,
                    "session_id": request.session.session_id,
                    "intent": processed_request.intent,
                    "error_type": error_type,
                },
            )
            if recovery_response:
                return recovery_response
        except Exception as recovery_error:
            self.logger.error(f"Error recovery failed: {str(recovery_error)}")

        # Fallback к стандартной обработке ошибок
        if error_type == "validation":
            return self.response_formatter.format_error_response(
                "invalid_date"
            )
        elif error_type == "timeout":
            return self.response_formatter.format_error_response("timeout")
        elif error_type == "data":
            return self.response_formatter.format_error_response("no_data")
        else:
            return self.response_formatter.format_error_response("general")

    def _classify_error(self, error: Exception) -> str:
        """Классифицирует тип ошибки для более точного ответа."""
        error_str = str(error).lower()

        if any(
            keyword in error_str
            for keyword in ["date", "datetime", "parse", "format"]
        ):
            return "validation"
        elif any(
            keyword in error_str
            for keyword in ["timeout", "connection", "network"]
        ):
            return "timeout"
        elif any(
            keyword in error_str
            for keyword in ["data", "missing", "required", "empty"]
        ):
            return "data"
        elif any(
            keyword in error_str
            for keyword in ["database", "sql", "connection"]
        ):
            return "database"
        else:
            return "general"

    def _is_critical_error(self, error: Exception) -> bool:
        """Определяет, является ли ошибка критической (требует сброса состояния)."""
        critical_errors = [
            "AttributeError",
            "TypeError",
            "KeyError",
            "ImportError",
            "MemoryError",
        ]
        return any(
            error_type in str(type(error)) for error_type in critical_errors
        )

    def _handle_button_press(self, request: YandexRequestModel) -> str:
        """Обрабатывает нажатие кнопки с учетом Alice совместимости."""
        # Проверяем payload кнопки
        if request.request.payload:
            action = request.request.payload.get("action")
            if action == "confirm_exit":
                return "выход"
            elif action == "cancel_exit":
                return "помощь"
            elif action:
                # Преобразуем action в текст
                return action.replace("_", " ")

        # Используем NLU токены если доступны
        if request.request.nlu and request.request.nlu.get("tokens"):
            return " ".join(request.request.nlu["tokens"])

        # По умолчанию показываем помощь
        return "помощь"

    async def _handle_transits(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос транзитов."""
        logger.info("INTENT_TRANSITS_START: Processing transits request")
        logger.info(
            f"INTENT_TRANSITS_CONTEXT: birth_date={user_context.birth_date}"
        )

        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.TRANSITS
            )
            return self.response_formatter.format_transit_request_response()

        try:
            from datetime import date

            birth_date = date.fromisoformat(user_context.birth_date)
            logger.info(
                f"INTENT_TRANSITS_CALCULATION_START: birth_date={birth_date}"
            )

            # Вычисляем натальную карту для транзитов
            natal_chart = self.natal_chart_calculator.calculate_natal_chart(
                birth_date
            )
            natal_planets = natal_chart["planets"]
            logger.info(
                f"INTENT_TRANSITS_NATAL_CHART: {len(natal_planets)} planets calculated"
            )

            # Вычисляем текущие транзиты
            transits = self.transit_calculator.calculate_current_transits(
                natal_planets
            )
            logger.info(
                f"INTENT_TRANSITS_SUCCESS: Calculated {len(transits)} transits"
            )

            return self.response_formatter.format_transits_response(transits)

        except Exception as e:
            logger.error(f"INTENT_TRANSITS_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("general")

    async def _handle_progressions(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос прогрессий."""
        logger.info(
            "INTENT_PROGRESSIONS_START: Processing progressions request"
        )
        logger.info(
            f"INTENT_PROGRESSIONS_CONTEXT: birth_date={user_context.birth_date}"
        )

        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.PROGRESSIONS
            )
            return (
                self.response_formatter.format_progressions_request_response()
            )

        try:
            from datetime import date

            birth_date = date.fromisoformat(user_context.birth_date)
            logger.info(
                f"INTENT_PROGRESSIONS_CALCULATION_START: birth_date={birth_date}"
            )

            # Вычисляем прогрессии
            progressions = self.natal_chart_calculator.calculate_progressions(
                birth_date
            )
            logger.info("INTENT_PROGRESSIONS_SUCCESS: Calculated progressions")

            return self.response_formatter.format_progressions_response(
                progressions
            )

        except Exception as e:
            logger.error(f"INTENT_PROGRESSIONS_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("general")

    async def _handle_solar_return(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос соляра."""
        logger.info(
            "INTENT_SOLAR_RETURN_START: Processing solar return request"
        )
        logger.info(
            f"INTENT_SOLAR_RETURN_CONTEXT: birth_date={user_context.birth_date}"
        )

        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.SOLAR_RETURN
            )
            return (
                self.response_formatter.format_solar_return_request_response()
            )

        try:
            from datetime import date

            birth_date = date.fromisoformat(user_context.birth_date)
            current_year = date.today().year
            logger.info(
                f"INTENT_SOLAR_RETURN_CALCULATION_START: birth_date={birth_date}, year={current_year}"
            )

            # Вычисляем соляр на текущий год
            solar_return = self.transit_calculator.calculate_solar_return(
                birth_date, current_year
            )
            logger.info(
                f"INTENT_SOLAR_RETURN_SUCCESS: Calculated solar return for {current_year}"
            )

            return self.response_formatter.format_solar_return_response(
                solar_return
            )

        except Exception as e:
            logger.error(f"INTENT_SOLAR_RETURN_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("general")

    async def _handle_lunar_return(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос лунара."""
        logger.info(
            "INTENT_LUNAR_RETURN_START: Processing lunar return request"
        )
        logger.info(
            f"INTENT_LUNAR_RETURN_CONTEXT: birth_date={user_context.birth_date}"
        )

        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.LUNAR_RETURN
            )
            return (
                self.response_formatter.format_lunar_return_request_response()
            )

        try:
            from datetime import date

            birth_date = date.fromisoformat(user_context.birth_date)
            current_date = date.today()
            logger.info(
                f"INTENT_LUNAR_RETURN_CALCULATION_START: birth_date={birth_date}, month={current_date.month}, year={current_date.year}"
            )

            # Вычисляем лунар на текущий месяц
            lunar_return = self.transit_calculator.calculate_lunar_return(
                birth_date, current_date.month, current_date.year
            )
            logger.info(
                f"INTENT_LUNAR_RETURN_SUCCESS: Calculated lunar return for {current_date.month}/{current_date.year}"
            )

            return self.response_formatter.format_lunar_return_response(
                lunar_return
            )

        except Exception as e:
            logger.error(f"INTENT_LUNAR_RETURN_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("general")

    # Enhanced transit and forecast handlers

    async def _handle_enhanced_transits(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает расширенные транзиты с Kerykeion интеграцией."""
        logger.info("INTENT_ENHANCED_TRANSITS_START: Processing enhanced transits request")
        
        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.TRANSITS
            )
            return self.response_formatter.format_transit_request_response()

        try:
            from datetime import date
            
            birth_date = date.fromisoformat(user_context.birth_date)
            logger.info(f"INTENT_ENHANCED_TRANSITS_DATE: {birth_date}")
            
            # Создаем расширенные данные натальной карты для транзитов
            natal_chart_data = await self._create_enhanced_natal_chart_data(user_context)
            
            # Получаем расширенные транзиты
            enhanced_transits = self.transit_calculator.get_enhanced_current_transits(
                natal_chart_data,
                include_minor_aspects=True
            )
            
            logger.info("INTENT_ENHANCED_TRANSITS_SUCCESS: Enhanced transits calculated")
            
            return self.response_formatter.format_enhanced_transits_response(enhanced_transits)
            
        except Exception as e:
            logger.error(f"INTENT_ENHANCED_TRANSITS_ERROR: {str(e)}", exc_info=True)
            # Fallback к обычным транзитам
            return await self._handle_transits(entities, user_context, session)

    async def _handle_period_forecast(
        self, entities: Dict[str, Any], user_context: UserContext, session, days: int = 7
    ) -> Any:
        """Обрабатывает прогноз на период."""
        logger.info(f"INTENT_PERIOD_FORECAST_START: {days} days forecast")
        
        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.TRANSITS
            )
            return self.response_formatter.format_birth_date_request_response()

        try:
            # Создаем данные натальной карты
            natal_chart_data = await self._create_enhanced_natal_chart_data(user_context)
            
            # Получаем прогноз на период
            period_forecast = self.transit_calculator.get_period_forecast(
                natal_chart_data, 
                days
            )
            
            logger.info(f"INTENT_PERIOD_FORECAST_SUCCESS: {days} days calculated")
            
            return self.response_formatter.format_period_forecast_response(period_forecast, days)
            
        except Exception as e:
            logger.error(f"INTENT_PERIOD_FORECAST_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("forecast")

    async def _handle_weekly_forecast(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает недельный прогноз."""
        logger.info("INTENT_WEEKLY_FORECAST_START")
        return await self._handle_period_forecast(entities, user_context, session, days=7)

    async def _handle_important_transits(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает важные транзиты."""
        logger.info("INTENT_IMPORTANT_TRANSITS_START")
        
        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.TRANSITS
            )
            return self.response_formatter.format_birth_date_request_response()

        try:
            # Создаем данные натальной карты
            natal_chart_data = await self._create_enhanced_natal_chart_data(user_context)
            
            # Получаем важные транзиты (90 дней вперед, 30 назад)
            important_transits = self.transit_calculator.get_important_transits(
                natal_chart_data,
                lookback_days=30,
                lookahead_days=90
            )
            
            logger.info("INTENT_IMPORTANT_TRANSITS_SUCCESS")
            
            return self.response_formatter.format_important_transits_response(important_transits)
            
        except Exception as e:
            logger.error(f"INTENT_IMPORTANT_TRANSITS_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("transits")

    async def _handle_comprehensive_analysis(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает комплексный астрологический анализ."""
        logger.info("INTENT_COMPREHENSIVE_ANALYSIS_START")
        
        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.TRANSITS
            )
            return self.response_formatter.format_birth_date_request_response()

        try:
            # Создаем данные натальной карты
            natal_chart_data = await self._create_enhanced_natal_chart_data(user_context)
            
            # Получаем комплексный анализ (30 дней)
            comprehensive_analysis = self.transit_calculator.get_comprehensive_transit_analysis(
                natal_chart_data,
                analysis_period_days=30
            )
            
            logger.info("INTENT_COMPREHENSIVE_ANALYSIS_SUCCESS")
            
            return self.response_formatter.format_comprehensive_analysis_response(comprehensive_analysis)
            
        except Exception as e:
            logger.error(f"INTENT_COMPREHENSIVE_ANALYSIS_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("analysis")

    async def _handle_enhanced_horoscope_with_transits(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает улучшенный гороскоп с транзитами."""
        logger.info("INTENT_ENHANCED_HOROSCOPE_TRANSITS_START")
        
        # Получаем знак зодиака
        zodiac_sign = entities.get("zodiac_sign")
        if not zodiac_sign:
            # Пытаемся получить из контекста пользователя
            if user_context.birth_date:
                try:
                    from datetime import date
                    birth_date = date.fromisoformat(user_context.birth_date)
                    zodiac_sign = self.astro_calc.get_zodiac_sign(birth_date)
                except Exception:
                    pass
        
        if not zodiac_sign:
            return self.response_formatter.format_zodiac_request_response()

        try:
            from app.models.yandex_models import YandexZodiacSign
            from app.services.horoscope_generator import HoroscopePeriod
            
            # Преобразуем знак зодиака
            try:
                sign_enum = YandexZodiacSign(zodiac_sign.lower())
            except ValueError:
                logger.warning(f"INTENT_ENHANCED_HOROSCOPE_TRANSITS_INVALID_SIGN: {zodiac_sign}")
                return self.response_formatter.format_error_response("zodiac")
            
            # Создаем данные натальной карты если доступны
            natal_chart_data = None
            if user_context.birth_date:
                try:
                    natal_chart_data = await self._create_enhanced_natal_chart_data(user_context)
                except Exception as e:
                    logger.warning(f"INTENT_ENHANCED_HOROSCOPE_TRANSITS_NATAL_ERROR: {e}")
            
            # Генерируем улучшенный гороскоп с транзитами
            enhanced_horoscope = self.horoscope_generator.generate_enhanced_horoscope(
                sign=sign_enum,
                period=HoroscopePeriod.DAILY,
                natal_chart_data=natal_chart_data,
                include_transits=True
            )
            
            logger.info("INTENT_ENHANCED_HOROSCOPE_TRANSITS_SUCCESS")
            
            return self.response_formatter.format_enhanced_horoscope_response(enhanced_horoscope)
            
        except Exception as e:
            logger.error(f"INTENT_ENHANCED_HOROSCOPE_TRANSITS_ERROR: {str(e)}", exc_info=True)
            # Fallback к обычному гороскопу
            return await self._handle_horoscope(entities, user_context, session)

    async def _handle_timing_question(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает вопросы о времени для действий ("когда лучше")."""
        logger.info("INTENT_TIMING_QUESTION_START")
        
        # Проверяем наличие данных рождения
        if not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "birth_date", YandexIntent.ADVICE
            )
            return self.response_formatter.format_birth_date_request_response()

        try:
            # Создаем данные натальной карты
            natal_chart_data = await self._create_enhanced_natal_chart_data(user_context)
            
            # Получаем прогноз на ближайшую неделю для тайминга
            period_forecast = self.transit_calculator.get_period_forecast(
                natal_chart_data, 
                days=7
            )
            
            # Анализируем лучшее время для действий
            timing_advice = self._extract_timing_advice_from_forecast(period_forecast, entities)
            
            logger.info("INTENT_TIMING_QUESTION_SUCCESS")
            
            return self.response_formatter.format_timing_advice_response(timing_advice)
            
        except Exception as e:
            logger.error(f"INTENT_TIMING_QUESTION_ERROR: {str(e)}", exc_info=True)
            return self.response_formatter.format_error_response("timing")

    # Helper methods for enhanced functionality

    async def _create_enhanced_natal_chart_data(self, user_context: UserContext) -> Dict[str, Any]:
        """Создает расширенные данные натальной карты для транзитов."""
        from datetime import date, datetime, time
        
        birth_date = date.fromisoformat(user_context.birth_date)
        
        # Используем время из контекста или полдень по умолчанию
        birth_time = time(12, 0)  # По умолчанию полдень
        if user_context.birth_time:
            try:
                birth_time = time.fromisoformat(user_context.birth_time)
            except Exception:
                pass
        
        birth_datetime = datetime.combine(birth_date, birth_time)
        
        # Координаты (по умолчанию Москва)
        coordinates = {
            "latitude": 55.7558, 
            "longitude": 37.6176
        }
        if user_context.birth_place:
            coordinates.update(user_context.birth_place)
        
        # Рассчитываем расширенную натальную карту
        enhanced_natal_chart = self.natal_chart_calculator.calculate_enhanced_natal_chart(
            name=user_context.user_id or "User",
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=coordinates,
            timezone_str="Europe/Moscow"
        )
        
        # Добавляем необходимые поля для транзитного анализа
        chart_data = {
            "birth_datetime": birth_datetime.isoformat(),
            "coordinates": coordinates,
            "planets": enhanced_natal_chart.get("planets", {}),
            "houses": enhanced_natal_chart.get("houses", {}),
            "aspects": enhanced_natal_chart.get("aspects", []),
        }
        
        return chart_data

    def _extract_timing_advice_from_forecast(
        self, 
        period_forecast: Dict[str, Any], 
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Извлекает советы по таймингу из прогноза."""
        
        daily_forecasts = period_forecast.get("daily_forecasts", [])
        important_dates = period_forecast.get("important_dates", [])
        
        # Анализируем, что спрашивает пользователь
        action_type = self._determine_action_type(entities)
        
        best_days = []
        avoid_days = []
        
        for day_data in daily_forecasts:
            energy_level = day_data.get("energy_level", "умеренная")
            recommendations = day_data.get("recommendations", [])
            
            # Определяем подходящие дни на основе энергии и рекомендаций
            if energy_level in ["высокая", "повышенная"]:
                if action_type in ["новые_дела", "активность", "общее"]:
                    best_days.append({
                        "date": day_data.get("date", ""),
                        "reason": f"Высокая энергия ({energy_level})",
                        "advice": "; ".join(recommendations[:2])
                    })
            elif energy_level in ["низкая", "пониженная"]:
                avoid_days.append({
                    "date": day_data.get("date", ""),
                    "reason": f"Низкая энергия ({energy_level})",
                    "advice": "Лучше отложить активные дела"
                })
        
        # Добавляем важные даты
        for date_info in important_dates[:2]:
            best_days.append({
                "date": date_info.get("date", ""),
                "reason": "Важное астрологическое влияние",
                "advice": date_info.get("significance", "")
            })
        
        return {
            "action_type": action_type,
            "best_days": best_days[:3],  # Топ-3 дня
            "avoid_days": avoid_days[:2],  # Топ-2 дня избегания
            "general_advice": period_forecast.get("general_advice", "Следуйте интуиции и естественным ритмам"),
            "period": period_forecast.get("period", "7 дней")
        }

    def _determine_action_type(self, entities: Dict[str, Any]) -> str:
        """Определяет тип действия из сущностей запроса."""
        # Анализируем сущности для определения типа действия
        # Возможные типы: новые_дела, отношения, работа, здоровье, общее
        
        return "общее"  # По умолчанию


# Глобальный экземпляр обработчика диалогов
dialog_handler = DialogHandler()
