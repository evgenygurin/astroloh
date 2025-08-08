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
from app.services.compatibility_analyzer import CompatibilityAnalyzer, CompatibilityType
from app.services.conversation_manager import ConversationManager
from app.services.dialog_flow_manager import DialogFlowManager, DialogState
from app.services.horoscope_generator import HoroscopeGenerator, HoroscopePeriod
from app.services.intent_recognition import IntentRecognizer
from app.services.lunar_calendar import LunarCalendar
from app.services.natal_chart import NatalChartCalculator
from app.services.response_formatter import ResponseFormatter
from app.services.session_manager import SessionManager
from app.services.synastry_service import PartnerData, SynastryService
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

        # Synastry and advanced compatibility services
        self.synastry_service = SynastryService(self.astro_calculator)
        self.compatibility_analyzer = CompatibilityAnalyzer(
            self.synastry_service
        )

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

        elif intent == YandexIntent.SYNASTRY:
            return await self._handle_synastry(entities, user_context, session)

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

        # Enhanced AI Consultation Intents
        elif intent == YandexIntent.AI_NATAL_INTERPRETATION:
            focus_area = entities.get("focus_area", entities.get("topic"))
            return await self._handle_ai_natal_chart_interpretation(
                user_context, session, focus_area
            )

        elif intent == YandexIntent.AI_CAREER_CONSULTATION:
            return await self._handle_ai_specialized_consultation(
                user_context, session, "карьера"
            )

        elif intent == YandexIntent.AI_LOVE_CONSULTATION:
            return await self._handle_ai_specialized_consultation(
                user_context, session, "любовь"
            )

        elif intent == YandexIntent.AI_HEALTH_CONSULTATION:
            return await self._handle_ai_specialized_consultation(
                user_context, session, "здоровье"
            )

        elif intent == YandexIntent.AI_FINANCIAL_CONSULTATION:
            return await self._handle_ai_specialized_consultation(
                user_context, session, "финансы"
            )

        elif intent == YandexIntent.AI_SPIRITUAL_CONSULTATION:
            return await self._handle_ai_specialized_consultation(
                user_context, session, "духовность"
            )

        elif intent == YandexIntent.AI_ENHANCED_COMPATIBILITY:
            partner_name = entities.get(
                "partner_name", entities.get("person_name")
            )
            return await self._handle_ai_enhanced_compatibility(
                user_context, session, partner_name
            )

        elif intent == YandexIntent.AI_TRANSIT_FORECAST:
            period_days = entities.get("period_days", 30)
            focus_area = entities.get("focus_area", entities.get("topic"))
            return await self._handle_ai_transit_forecast(
                user_context, session, period_days, focus_area
            )

        elif intent == YandexIntent.AI_SERVICE_STATUS:
            return await self._handle_ai_service_status(user_context, session)

        # NEW RUSSIAN LOCALIZATION HANDLERS - Issue #68
        elif intent == YandexIntent.SIGN_DESCRIPTION:
            return await self._handle_sign_description(
                entities, user_context, session
            )

        elif intent == YandexIntent.PLANET_IN_SIGN:
            return await self._handle_planet_in_sign(
                entities, user_context, session
            )

        elif intent == YandexIntent.HOUSE_CHARACTERISTICS:
            return await self._handle_house_characteristics(
                entities, user_context, session
            )

        elif intent == YandexIntent.ENHANCED_COMPATIBILITY:
            return await self._handle_enhanced_compatibility_analysis(
                entities, user_context, session
            )

        elif intent == YandexIntent.RETROGRADE_INFLUENCE:
            return await self._handle_retrograde_influence(
                entities, user_context, session
            )

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
        logger.info(
            "INTENT_ENHANCED_TRANSITS_START: Processing enhanced transits request"
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
            logger.info(f"INTENT_ENHANCED_TRANSITS_DATE: {birth_date}")

            # Создаем расширенные данные натальной карты для транзитов
            natal_chart_data = await self._create_enhanced_natal_chart_data(
                user_context
            )

            # Получаем расширенные транзиты
            enhanced_transits = (
                self.transit_calculator.get_enhanced_current_transits(
                    natal_chart_data, include_minor_aspects=True
                )
            )

            logger.info(
                "INTENT_ENHANCED_TRANSITS_SUCCESS: Enhanced transits calculated"
            )

            return self.response_formatter.format_enhanced_transits_response(
                enhanced_transits
            )

        except Exception as e:
            logger.error(
                f"INTENT_ENHANCED_TRANSITS_ERROR: {str(e)}", exc_info=True
            )
            # Fallback к обычным транзитам
            return await self._handle_transits(entities, user_context, session)

    async def _handle_period_forecast(
        self,
        entities: Dict[str, Any],
        user_context: UserContext,
        session,
        days: int = 7,
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
            natal_chart_data = await self._create_enhanced_natal_chart_data(
                user_context
            )

            # Получаем прогноз на период
            period_forecast = self.transit_calculator.get_period_forecast(
                natal_chart_data, days
            )

            logger.info(
                f"INTENT_PERIOD_FORECAST_SUCCESS: {days} days calculated"
            )

            return self.response_formatter.format_period_forecast_response(
                period_forecast, days
            )

        except Exception as e:
            logger.error(
                f"INTENT_PERIOD_FORECAST_ERROR: {str(e)}", exc_info=True
            )
            return self.response_formatter.format_error_response("forecast")

    async def _handle_weekly_forecast(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает недельный прогноз."""
        logger.info("INTENT_WEEKLY_FORECAST_START")
        return await self._handle_period_forecast(
            entities, user_context, session, days=7
        )

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
            natal_chart_data = await self._create_enhanced_natal_chart_data(
                user_context
            )

            # Получаем важные транзиты (90 дней вперед, 30 назад)
            important_transits = (
                self.transit_calculator.get_important_transits(
                    natal_chart_data, lookback_days=30, lookahead_days=90
                )
            )

            logger.info("INTENT_IMPORTANT_TRANSITS_SUCCESS")

            return self.response_formatter.format_important_transits_response(
                important_transits
            )

        except Exception as e:
            logger.error(
                f"INTENT_IMPORTANT_TRANSITS_ERROR: {str(e)}", exc_info=True
            )
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
            natal_chart_data = await self._create_enhanced_natal_chart_data(
                user_context
            )

            # Получаем комплексный анализ (30 дней)
            comprehensive_analysis = (
                self.transit_calculator.get_comprehensive_transit_analysis(
                    natal_chart_data, analysis_period_days=30
                )
            )

            logger.info("INTENT_COMPREHENSIVE_ANALYSIS_SUCCESS")

            return (
                self.response_formatter.format_comprehensive_analysis_response(
                    comprehensive_analysis
                )
            )

        except Exception as e:
            logger.error(
                f"INTENT_COMPREHENSIVE_ANALYSIS_ERROR: {str(e)}", exc_info=True
            )
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
                logger.warning(
                    f"INTENT_ENHANCED_HOROSCOPE_TRANSITS_INVALID_SIGN: {zodiac_sign}"
                )
                return self.response_formatter.format_error_response("zodiac")

            # Создаем данные натальной карты если доступны
            natal_chart_data = None
            if user_context.birth_date:
                try:
                    natal_chart_data = (
                        await self._create_enhanced_natal_chart_data(
                            user_context
                        )
                    )
                except Exception as e:
                    logger.warning(
                        f"INTENT_ENHANCED_HOROSCOPE_TRANSITS_NATAL_ERROR: {e}"
                    )

            # Генерируем улучшенный гороскоп с транзитами
            enhanced_horoscope = (
                self.horoscope_generator.generate_enhanced_horoscope(
                    sign=sign_enum,
                    period=HoroscopePeriod.DAILY,
                    natal_chart_data=natal_chart_data,
                    include_transits=True,
                )
            )

            logger.info("INTENT_ENHANCED_HOROSCOPE_TRANSITS_SUCCESS")

            return self.response_formatter.format_enhanced_horoscope_response(
                enhanced_horoscope
            )

        except Exception as e:
            logger.error(
                f"INTENT_ENHANCED_HOROSCOPE_TRANSITS_ERROR: {str(e)}",
                exc_info=True,
            )
            # Fallback к обычному гороскопу
            return await self._handle_horoscope(
                entities, user_context, session
            )

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
            natal_chart_data = await self._create_enhanced_natal_chart_data(
                user_context
            )

            # Получаем прогноз на ближайшую неделю для тайминга
            period_forecast = self.transit_calculator.get_period_forecast(
                natal_chart_data, days=7
            )

            # Анализируем лучшее время для действий
            timing_advice = self._extract_timing_advice_from_forecast(
                period_forecast, entities
            )

            logger.info("INTENT_TIMING_QUESTION_SUCCESS")

            return self.response_formatter.format_timing_advice_response(
                timing_advice
            )

        except Exception as e:
            logger.error(
                f"INTENT_TIMING_QUESTION_ERROR: {str(e)}", exc_info=True
            )
            return self.response_formatter.format_error_response("timing")

    # Helper methods for enhanced functionality

    async def _create_enhanced_natal_chart_data(
        self, user_context: UserContext
    ) -> Dict[str, Any]:
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
        coordinates = {"latitude": 55.7558, "longitude": 37.6176}
        if user_context.birth_place:
            coordinates.update(user_context.birth_place)

        # Рассчитываем расширенную натальную карту
        enhanced_natal_chart = (
            self.natal_chart_calculator.calculate_enhanced_natal_chart(
                name=user_context.user_id or "User",
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=coordinates,
                timezone_str="Europe/Moscow",
            )
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
        self, period_forecast: Dict[str, Any], entities: Dict[str, Any]
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
                    best_days.append(
                        {
                            "date": day_data.get("date", ""),
                            "reason": f"Высокая энергия ({energy_level})",
                            "advice": "; ".join(recommendations[:2]),
                        }
                    )
            elif energy_level in ["низкая", "пониженная"]:
                avoid_days.append(
                    {
                        "date": day_data.get("date", ""),
                        "reason": f"Низкая энергия ({energy_level})",
                        "advice": "Лучше отложить активные дела",
                    }
                )

        # Добавляем важные даты
        for date_info in important_dates[:2]:
            best_days.append(
                {
                    "date": date_info.get("date", ""),
                    "reason": "Важное астрологическое влияние",
                    "advice": date_info.get("significance", ""),
                }
            )

        return {
            "action_type": action_type,
            "best_days": best_days[:3],  # Топ-3 дня
            "avoid_days": avoid_days[:2],  # Топ-2 дня избегания
            "general_advice": period_forecast.get(
                "general_advice", "Следуйте интуиции и естественным ритмам"
            ),
            "period": period_forecast.get("period", "7 дней"),
        }

    def _determine_action_type(self, entities: Dict[str, Any]) -> str:
        """Определяет тип действия из сущностей запроса."""
        # Анализируем сущности для определения типа действия
        # Возможные типы: новые_дела, отношения, работа, здоровье, общее

        return "общее"  # По умолчанию

    async def _handle_synastry(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос синастрии и анализа отношений."""
        logger.info("INTENT_SYNASTRY_START: Processing synastry request")

        partner_names = entities.get("partner_names", [])
        zodiac_signs = entities.get("zodiac_signs", [])
        dates = entities.get("dates", [])

        logger.info(
            f"INTENT_SYNASTRY_ENTITIES: partner_names={partner_names}, "
            f"zodiac_signs=[{', '.join(sign.value for sign in zodiac_signs)}], "
            f"dates={dates}"
        )

        # Проверяем наличие данных пользователя
        if not user_context.zodiac_sign and not user_context.birth_date:
            self.session_manager.set_awaiting_data(
                session, user_context, "zodiac_sign", YandexIntent.SYNASTRY
            )
            return self.response_formatter.format_zodiac_request_response(
                "Для анализа отношений нужен ваш знак зодиака. Назовите его."
            )

        # Если есть имя партнера, но нет данных о партнере
        if partner_names and not user_context.partner_name:
            user_context.partner_name = partner_names[0]
            logger.info(
                f"INTENT_SYNASTRY_PARTNER_NAME_SET: {user_context.partner_name}"
            )

        # Проверяем наличие имени партнера
        if not user_context.partner_name:
            self.session_manager.set_awaiting_data(
                session, user_context, "partner_name", YandexIntent.SYNASTRY
            )
            return self.response_formatter.format_text_response(
                "Как зовут вашего партнера? Мне нужно имя для более персонального анализа отношений.",
                buttons=["Отмена"],
            )

        # Проверяем наличие знака партнера
        if not user_context.partner_sign:
            # Если в сообщении есть знак зодиака, используем его как знак партнера
            if zodiac_signs:
                user_context.partner_sign = zodiac_signs[0]
                logger.info(
                    f"INTENT_SYNASTRY_PARTNER_SIGN_SET: {user_context.partner_sign.value}"
                )
            else:
                self.session_manager.set_awaiting_data(
                    session,
                    user_context,
                    "partner_zodiac_sign",
                    YandexIntent.SYNASTRY,
                )
                return self.response_formatter.format_text_response(
                    f"Какой знак зодиака у {user_context.partner_name}?",
                    buttons=["Не знаю", "Отмена"],
                )

        # Опционально: дата рождения партнера для более точной синастрии
        if not user_context.partner_birth_date and dates:
            user_context.partner_birth_date = dates[0]
            logger.info(
                f"INTENT_SYNASTRY_PARTNER_BIRTH_DATE_SET: {user_context.partner_birth_date}"
            )

        # Все необходимые данные собраны, выполняем синастрию
        try:
            from datetime import datetime

            # Создаем объекты партнеров
            person1 = PartnerData(
                name="Вы",
                birth_date=datetime.fromisoformat(user_context.birth_date)
                if user_context.birth_date
                else datetime.now(),
                birth_time=datetime.fromisoformat(user_context.birth_time)
                if user_context.birth_time
                else None,
                birth_place=user_context.birth_place,
                zodiac_sign=user_context.zodiac_sign,
            )

            person2 = PartnerData(
                name=user_context.partner_name,
                birth_date=datetime.fromisoformat(
                    user_context.partner_birth_date
                )
                if user_context.partner_birth_date
                else datetime.now(),
                birth_time=None,  # Пока не собираем время партнера
                birth_place=None,  # Пока не собираем место партнера
                zodiac_sign=user_context.partner_sign,
            )

            logger.info(
                f"INTENT_SYNASTRY_CALCULATION_START: Analyzing {person1.name} ({person1.zodiac_sign.value}) "
                f"and {person2.name} ({person2.zodiac_sign.value})"
            )

            # Выполняем полный анализ совместимости
            compatibility_report = (
                await self.compatibility_analyzer.analyze_full_compatibility(
                    person1, person2, CompatibilityType.ROMANTIC
                )
            )

            logger.info(
                f"INTENT_SYNASTRY_SUCCESS: Generated compatibility report with {compatibility_report['overall_score']}% compatibility"
            )

            # Очищаем ожидание данных
            self.session_manager.clear_awaiting_data(session, user_context)

            # Формируем ответ
            return self.response_formatter.format_synastry_response(
                user_name="Вы",
                partner_name=user_context.partner_name,
                compatibility_report=compatibility_report,
            )

        except Exception as e:
            logger.error(f"INTENT_SYNASTRY_ERROR: {str(e)}", exc_info=True)

            # Fallback к простой совместимости по знакам
            if user_context.zodiac_sign and user_context.partner_sign:
                compatibility = (
                    self.astro_calculator.calculate_compatibility_score(
                        user_context.zodiac_sign, user_context.partner_sign
                    )
                )

                logger.info(
                    "INTENT_SYNASTRY_FALLBACK: Using basic zodiac compatibility"
                )

                return self.response_formatter.format_compatibility_response(
                    user_context.zodiac_sign,
                    user_context.partner_sign,
                    compatibility,
                    partner_name=user_context.partner_name,
                )

            return self.response_formatter.format_error_response("synastry")

    async def _handle_ai_natal_chart_interpretation(
        self, user_context: UserContext, session, focus_area: str = None
    ) -> Any:
        """
        Обрабатывает запрос интерпретации натальной карты с помощью AI.

        Args:
            user_context: Контекст пользователя
            session: Сессия
            focus_area: Область фокусировки (карьера, любовь, здоровье)

        Returns:
            Ответ с AI интерпретацией натальной карты
        """
        logger.info(
            f"AI_NATAL_INTERPRETATION_REQUEST_START: focus={focus_area}"
        )

        try:
            # Проверяем наличие полных данных рождения
            if not all(
                [
                    user_context.birth_date,
                    user_context.birth_time,
                    user_context.birth_place,
                ]
            ):
                logger.info(
                    "AI_NATAL_INTERPRETATION_INSUFFICIENT_DATA: Requesting birth data"
                )

                # Устанавливаем состояние ожидания данных
                user_context.awaiting_data = "birth_data_for_ai_natal"
                user_context.consultation_focus = focus_area
                self.session_manager.update_user_context(session, user_context)

                return self.response_formatter.format_text_response(
                    text="Для создания детальной интерпретации натальной карты мне нужны ваши точные данные рождения. Пожалуйста, укажите дату, время и место рождения.",
                    buttons=["Отмена"],
                )

            # Генерируем AI интерпретацию
            interpretation = await self.ai_horoscope_service.generate_natal_chart_interpretation(
                name=user_context.name or "Пользователь",
                birth_date=user_context.birth_date,
                birth_time=user_context.birth_time,
                birth_place={
                    "latitude": user_context.birth_place.get(
                        "latitude", 55.7558
                    ),
                    "longitude": user_context.birth_place.get(
                        "longitude", 37.6176
                    ),
                },
                timezone_str="Europe/Moscow",
                focus_area=focus_area,
            )

            if interpretation.get("ai_interpretation"):
                logger.info(
                    "AI_NATAL_INTERPRETATION_SUCCESS: Generated AI interpretation"
                )

                response_text = interpretation["ai_interpretation"]

                # Добавляем информацию об источнике данных
                if interpretation.get("data_source") == "kerykeion_enhanced":
                    response_text += "\n\nЭта интерпретация основана на профессиональных астрологических расчетах."

                return self.response_formatter.format_text_response(
                    text=response_text,
                    buttons=["Ещё вопрос", "Карьера", "Любовь", "Здоровье"],
                )
            else:
                logger.warning(
                    "AI_NATAL_INTERPRETATION_NO_RESULT: No interpretation generated"
                )
                return self.response_formatter.format_error_response(
                    "natal_ai"
                )

        except Exception as e:
            logger.error(f"AI_NATAL_INTERPRETATION_ERROR: {e}")
            return self.response_formatter.format_error_response("natal_ai")

    async def _handle_ai_specialized_consultation(
        self, user_context: UserContext, session, consultation_type: str
    ) -> Any:
        """
        Обрабатывает специализированную AI консультацию.

        Args:
            user_context: Контекст пользователя
            session: Сессия
            consultation_type: Тип консультации (карьера, любовь, здоровье, финансы, духовность)

        Returns:
            Ответ с специализированной консультацией
        """
        logger.info(
            f"AI_SPECIALIZED_CONSULTATION_START: type={consultation_type}"
        )

        try:
            if not user_context.zodiac_sign:
                logger.info(
                    "AI_SPECIALIZED_CONSULTATION_NO_SIGN: Requesting zodiac sign"
                )

                user_context.awaiting_data = (
                    f"zodiac_for_ai_{consultation_type}"
                )
                self.session_manager.update_user_context(session, user_context)

                return self.response_formatter.format_text_response(
                    text=f"Чтобы дать точную консультацию по теме '{consultation_type}', мне нужно знать ваш знак зодиака. Какой у вас знак?",
                    buttons=["Овен", "Телец", "Близнецы", "Рак", "Лев"],
                )

            # Подготавливаем данные рождения (если есть)
            birth_data = None
            if all(
                [
                    user_context.birth_date,
                    user_context.birth_time,
                    user_context.birth_place,
                ]
            ):
                birth_data = {
                    "name": user_context.name or "Пользователь",
                    "birth_date": user_context.birth_date,
                    "birth_time": user_context.birth_time,
                    "birth_place": user_context.birth_place,
                    "timezone": "Europe/Moscow",
                }

            # Генерируем специализированную консультацию
            consultation = await self.ai_horoscope_service.generate_specialized_consultation(
                zodiac_sign=user_context.zodiac_sign,
                consultation_type=consultation_type,
                user_context={
                    "mood": getattr(user_context, "mood", None),
                    "challenges": getattr(
                        user_context, "current_challenges", None
                    ),
                    "focus_area": consultation_type,
                },
                birth_data=birth_data,
            )

            if consultation.get("advice"):
                logger.info(
                    f"AI_SPECIALIZED_CONSULTATION_SUCCESS: {consultation_type}"
                )

                response_text = consultation["advice"]

                # Добавляем контекстную информацию
                if consultation.get("data_source") == "personalized_ai":
                    if birth_data:
                        response_text += "\n\nСовет основан на анализе вашей натальной карты."
                    else:
                        response_text += f"\n\nСовет для знака {user_context.zodiac_sign.value}."

                # Подходящие кнопки для каждого типа консультации
                buttons = {
                    "карьера": ["Финансы", "Развитие", "Ещё совет"],
                    "любовь": ["Совместимость", "Отношения", "Ещё совет"],
                    "здоровье": ["Энергия", "Профилактика", "Ещё совет"],
                    "финансы": ["Карьера", "Инвестиции", "Ещё совет"],
                    "духовность": ["Развитие", "Медитация", "Ещё совет"],
                }

                response_buttons = buttons.get(
                    consultation_type, ["Ещё совет", "Другая тема"]
                )

                return self.response_formatter.format_text_response(
                    text=response_text, buttons=response_buttons
                )
            else:
                logger.warning(
                    f"AI_SPECIALIZED_CONSULTATION_NO_RESULT: {consultation_type}"
                )
                return self.response_formatter.format_error_response(
                    "consultation"
                )

        except Exception as e:
            logger.error(f"AI_SPECIALIZED_CONSULTATION_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "consultation"
            )

    async def _handle_ai_enhanced_compatibility(
        self, user_context: UserContext, session, partner_name: str = None
    ) -> Any:
        """
        Обрабатывает улучшенный анализ совместимости с AI.

        Args:
            user_context: Контекст пользователя
            session: Сессия
            partner_name: Имя партнера

        Returns:
            Ответ с улучшенным анализом совместимости
        """
        logger.info(f"AI_ENHANCED_COMPATIBILITY_START: partner={partner_name}")

        try:
            # Проверяем наличие данных пользователя
            if not user_context.zodiac_sign:
                logger.info(
                    "AI_ENHANCED_COMPATIBILITY_NO_USER_SIGN: Requesting user sign"
                )

                user_context.awaiting_data = "zodiac_for_ai_compatibility"
                if partner_name:
                    user_context.partner_name = partner_name
                self.session_manager.update_user_context(session, user_context)

                return self.response_formatter.format_text_response(
                    text="Для анализа совместимости мне нужен ваш знак зодиака. Какой у вас знак?",
                    buttons=["Овен", "Телец", "Близнецы", "Рак", "Лев"],
                )

            # Проверяем наличие данных партнера
            if not user_context.partner_sign:
                logger.info(
                    "AI_ENHANCED_COMPATIBILITY_NO_PARTNER_SIGN: Requesting partner sign"
                )

                user_context.awaiting_data = (
                    "partner_sign_for_ai_compatibility"
                )
                if partner_name:
                    user_context.partner_name = partner_name
                self.session_manager.update_user_context(session, user_context)

                partner_text = (
                    f"партнера {partner_name}" if partner_name else "партнера"
                )
                return self.response_formatter.format_text_response(
                    text=f"Теперь мне нужен знак зодиака {partner_text}. Какой у него знак?",
                    buttons=["Овен", "Телец", "Близнецы", "Рак", "Лев"],
                )

            # Подготавливаем данные для анализа
            person1_data = {
                "name": user_context.name or "Вы",
                "zodiac_sign": user_context.zodiac_sign.value,
            }

            person2_data = {
                "name": user_context.partner_name or partner_name or "Партнер",
                "zodiac_sign": user_context.partner_sign.value,
            }

            # Добавляем данные рождения если есть
            if all(
                [
                    user_context.birth_date,
                    user_context.birth_time,
                    user_context.birth_place,
                ]
            ):
                person1_data.update(
                    {
                        "birth_date": user_context.birth_date.isoformat(),
                        "birth_datetime": user_context.birth_time.isoformat(),
                        "birth_place": user_context.birth_place,
                    }
                )

            # Генерируем улучшенный анализ совместимости
            compatibility = await self.ai_horoscope_service.generate_enhanced_compatibility_analysis(
                person1_data=person1_data,
                person2_data=person2_data,
                relationship_type="романтические",
                context={
                    "relationship_stage": getattr(
                        user_context, "relationship_stage", "знакомство"
                    ),
                    "challenges": getattr(
                        user_context, "relationship_challenges", None
                    ),
                },
            )

            if compatibility.get("ai_analysis"):
                logger.info(
                    "AI_ENHANCED_COMPATIBILITY_SUCCESS: Generated enhanced analysis"
                )

                response_text = compatibility["ai_analysis"]

                # Добавляем оценку совместимости если есть
                if (
                    compatibility.get("chart_data", {})
                    .get("synastry_analysis", {})
                    .get("overall_score")
                ):
                    score = compatibility["chart_data"]["synastry_analysis"][
                        "overall_score"
                    ]
                    response_text = (
                        f"Совместимость: {score}%\n\n{response_text}"
                    )

                # Очищаем данные партнера для следующего запроса
                user_context.partner_name = None
                user_context.partner_sign = None
                self.session_manager.update_user_context(session, user_context)

                return self.response_formatter.format_text_response(
                    text=response_text,
                    buttons=[
                        "Другой партнер",
                        "Советы для отношений",
                        "Ещё вопрос",
                    ],
                )
            else:
                logger.warning(
                    "AI_ENHANCED_COMPATIBILITY_NO_RESULT: No analysis generated"
                )
                return self.response_formatter.format_error_response(
                    "compatibility"
                )

        except Exception as e:
            logger.error(f"AI_ENHANCED_COMPATIBILITY_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "compatibility"
            )

    async def _handle_ai_transit_forecast(
        self,
        user_context: UserContext,
        session,
        period_days: int = 30,
        focus_area: str = None,
    ) -> Any:
        """
        Обрабатывает AI прогноз на основе транзитов.

        Args:
            user_context: Контекст пользователя
            session: Сессия
            period_days: Период прогноза в днях
            focus_area: Область фокусировки

        Returns:
            Ответ с прогнозом на основе транзитов
        """
        logger.info(
            f"AI_TRANSIT_FORECAST_START: period={period_days}, focus={focus_area}"
        )

        try:
            if not user_context.zodiac_sign:
                logger.info(
                    "AI_TRANSIT_FORECAST_NO_SIGN: Requesting zodiac sign"
                )

                user_context.awaiting_data = (
                    f"zodiac_for_ai_transit_{period_days}"
                )
                user_context.consultation_focus = focus_area
                self.session_manager.update_user_context(session, user_context)

                return self.response_formatter.format_text_response(
                    text=f"Для создания прогноза на {period_days} дней мне нужен ваш знак зодиака. Какой у вас знак?",
                    buttons=["Овен", "Телец", "Близнецы", "Рак", "Лев"],
                )

            # Генерируем прогноз на основе транзитов
            forecast = await self.ai_horoscope_service.generate_transit_forecast_analysis(
                zodiac_sign=user_context.zodiac_sign,
                birth_date=user_context.birth_date,
                birth_time=user_context.birth_time,
                birth_place=user_context.birth_place,
                forecast_period=period_days,
                focus_area=focus_area,
            )

            if forecast.get("ai_forecast"):
                logger.info(
                    f"AI_TRANSIT_FORECAST_SUCCESS: Generated {period_days}-day forecast"
                )

                response_text = forecast["ai_forecast"]

                # Добавляем информацию о периоде
                period_text = {
                    7: "на неделю",
                    30: "на месяц",
                    90: "на квартал",
                }.get(period_days, f"на {period_days} дней")

                response_text = f"Прогноз {period_text}:\n\n{response_text}"

                # Подходящие кнопки
                buttons = [
                    "Другой период",
                    "Фокус на карьере",
                    "Фокус на любви",
                ]
                if period_days != 7:
                    buttons.insert(0, "На неделю")
                if period_days != 30:
                    buttons.insert(1, "На месяц")

                return self.response_formatter.format_text_response(
                    text=response_text,
                    buttons=buttons[:5],  # Ограничиваем до 5 кнопок для Alice
                )
            else:
                logger.warning(
                    "AI_TRANSIT_FORECAST_NO_RESULT: No forecast generated"
                )
                return self.response_formatter.format_error_response(
                    "transit_forecast"
                )

        except Exception as e:
            logger.error(f"AI_TRANSIT_FORECAST_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "transit_forecast"
            )

    async def _handle_ai_service_status(
        self, user_context: UserContext, session
    ) -> Any:
        """
        Обрабатывает запрос статуса AI сервисов.

        Returns:
            Ответ со статусом доступных AI сервисов
        """
        logger.info("AI_SERVICE_STATUS_REQUEST")

        try:
            status = (
                await self.ai_horoscope_service.get_enhanced_service_status()
            )

            # Формируем понятный ответ для пользователя
            features = []

            if status.get("yandex_gpt_available"):
                features.append("✅ ИИ-генерация текста")
            else:
                features.append("❌ ИИ-генерация недоступна")

            if status.get("astro_ai_service_available"):
                enhanced = status.get("enhanced_features", {})
                kerykeion_available = enhanced.get(
                    "feature_availability", {}
                ).get("kerykeion_service", False)

                if kerykeion_available:
                    features.append("✅ Профессиональные расчеты")
                    features.append("✅ Детальные интерпретации")
                    features.append("✅ Анализ совместимости")
                else:
                    features.append("⚠️ Базовые расчеты")
            else:
                features.append("❌ Расширенные функции недоступны")

            response_text = "Статус астро-ИИ сервисов:\n\n" + "\n".join(
                features
            )

            if status.get("yandex_gpt_available") and status.get(
                "astro_ai_service_available"
            ):
                response_text += "\n\nВсе функции работают! Попробуйте интерпретацию натальной карты или специализированные консультации."
                buttons = [
                    "Натальная карта",
                    "Карьера",
                    "Любовь",
                    "Совместимость",
                ]
            else:
                response_text += "\n\nНекоторые функции могут быть ограничены."
                buttons = ["Обычный гороскоп", "Совместимость знаков"]

            return self.response_formatter.format_text_response(
                text=response_text, buttons=buttons
            )

        except Exception as e:
            logger.error(f"AI_SERVICE_STATUS_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "service_status"
            )

    # NEW RUSSIAN LOCALIZATION HANDLERS - Issue #68
    async def _handle_sign_description(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос описания знака зодиака."""
        logger.info("RUSSIAN_LOCALIZATION_SIGN_DESCRIPTION_START")

        try:
            # Импорт адаптера русификации
            from app.services.russian_astrology_adapter import russian_adapter

            # Получаем знак пользователя из контекста или запрашиваем
            user_sign = user_context.zodiac_sign
            if not user_sign and entities.get("zodiac_sign"):
                user_sign = entities["zodiac_sign"]

            if not user_sign:
                response_text = (
                    "Чтобы рассказать о вашем знаке зодиака, мне нужно его знать. "
                    "Скажите, например: 'Мой знак - Лев' или 'Я Близнецы'."
                )
                buttons = ["Мой гороскоп", "Совместимость", "Помощь"]
                return self.response_formatter.format_text_response(
                    text=response_text, buttons=buttons
                )

            # Получаем детальное описание знака
            sign_description = russian_adapter.get_russian_sign_description(
                user_sign
            )

            if "error" in sign_description:
                logger.warning(
                    f"SIGN_DESCRIPTION_ERROR: {sign_description['error']}"
                )
                response_text = (
                    f"Извините, не могу найти информацию о знаке '{user_sign}'"
                )
                return self.response_formatter.format_text_response(
                    text=response_text
                )

            sign_name = sign_description["name"]

            # Формируем детальное описание
            response_text = f"Ваш знак зодиака - {sign_name}.\n\n"

            # Получаем дополнительную информацию о знаке
            if russian_adapter.subject and hasattr(
                russian_adapter.subject, "sun"
            ):
                sun_info = russian_adapter.get_russian_planet_description(
                    "Sun"
                )
                if "keywords" in sun_info:
                    keywords = ", ".join(sun_info["keywords"][:5])
                    response_text += f"Ключевые качества: {keywords}.\n\n"

                if "description" in sun_info:
                    response_text += f"{sun_info['description']}\n\n"
            else:
                # Базовые характеристики знаков
                sign_traits = {
                    "овен": "Энергичные, инициативные лидеры с сильной волей",
                    "телец": "Практичные, стабильные люди, ценящие комфорт",
                    "близнецы": "Общительные, любознательные интеллектуалы",
                    "рак": "Чувствительные, заботливые домашние люди",
                    "лев": "Творческие, великодушные лидеры с королевским нравом",
                    "дева": "Аналитичные, перфекционисты с практическим складом ума",
                    "весы": "Гармоничные, дипломатичные ценители красоты",
                    "скорпион": "Интенсивные, проницательные трансформаторы",
                    "стрелец": "Оптимистичные, свободолюбивые философы",
                    "козерог": "Целеустремленные, дисциплинированные строители",
                    "водолей": "Независимые, инновационные гуманисты",
                    "рыбы": "Мечтательные, интуитивные эмпаты",
                }

                trait = sign_traits.get(
                    user_sign.lower(), "Уникальные личности"
                )
                response_text += f"{trait}."

            # Форматируем для голосового вывода
            voice_text = russian_adapter.format_for_voice(response_text)

            buttons = [
                "Мой гороскоп",
                "Натальная карта",
                "Совместимость",
                "Планеты",
            ]

            logger.info("RUSSIAN_LOCALIZATION_SIGN_DESCRIPTION_SUCCESS")
            return self.response_formatter.format_text_response(
                text=voice_text, buttons=buttons
            )

        except Exception as e:
            logger.error(f"SIGN_DESCRIPTION_HANDLER_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "sign_description"
            )

    async def _handle_planet_in_sign(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос о планете в знаке."""
        logger.info("RUSSIAN_LOCALIZATION_PLANET_IN_SIGN_START")

        try:
            from app.services.russian_astrology_adapter import russian_adapter

            # Извлекаем планету и знак из запроса
            request_text = entities.get("original_text", "").lower()

            # Простая логика извлечения планеты и знака
            planet_matches = {
                "солнце": "Sun",
                "луна": "Moon",
                "меркурий": "Mercury",
                "венера": "Venus",
                "марс": "Mars",
                "юпитер": "Jupiter",
                "сатурн": "Saturn",
                "уран": "Uranus",
                "нептун": "Neptune",
                "плутон": "Pluto",
                "хирон": "Chiron",
            }

            sign_matches = {
                "овне": "Aries",
                "тельце": "Taurus",
                "близнецах": "Gemini",
                "раке": "Cancer",
                "льве": "Leo",
                "деве": "Virgo",
                "весах": "Libra",
                "скорпионе": "Scorpio",
                "стрельце": "Sagittarius",
                "козероге": "Capricorn",
                "водолее": "Aquarius",
                "рыбах": "Pisces",
            }

            found_planet = None
            found_sign = None

            for ru_planet, en_planet in planet_matches.items():
                if ru_planet in request_text:
                    found_planet = en_planet
                    break

            for ru_sign, en_sign in sign_matches.items():
                if ru_sign in request_text:
                    found_sign = en_sign
                    break

            if not found_planet or not found_sign:
                response_text = (
                    "Спросите, например: 'Что означает Солнце в Овне?' или "
                    "'Венера в Весах что значит?'. Я расскажу о влиянии планеты в знаке."
                )
                buttons = ["Мой гороскоп", "Натальная карта", "Помощь"]
                return self.response_formatter.format_text_response(
                    text=response_text, buttons=buttons
                )

            # Получаем описания планеты и знака
            planet_desc = russian_adapter.get_russian_planet_description(
                found_planet
            )
            sign_desc = russian_adapter.get_russian_sign_description(
                found_sign
            )

            if "error" in planet_desc or "error" in sign_desc:
                response_text = (
                    "Извините, не могу найти информацию об этой комбинации."
                )
                return self.response_formatter.format_text_response(
                    text=response_text
                )

            planet_name = planet_desc["name"]
            sign_name = sign_desc["name"]

            # Формируем ответ
            response_text = f"{planet_name} в знаке {sign_name}:\n\n"

            # Базовые интерпретации комбинаций
            planet_keywords = planet_desc.get("keywords", [])
            planet_description = planet_desc.get("description", "")

            if planet_keywords:
                keywords_text = ", ".join(planet_keywords[:3])
                response_text += (
                    f"Эта комбинация влияет на: {keywords_text}.\n\n"
                )

            if planet_description:
                response_text += f"{planet_description} проявляется в стиле знака {sign_name}.\n\n"

            # Простые интерпретации для популярных комбинаций
            interpretations = {
                (
                    "Sun",
                    "Aries",
                ): "Сильные лидерские качества, инициативность, пионерский дух.",
                (
                    "Sun",
                    "Leo",
                ): "Творческая натура, великодушие, естественная харизма.",
                (
                    "Moon",
                    "Cancer",
                ): "Глубокая эмоциональность, забота о семье, интуитивность.",
                (
                    "Venus",
                    "Libra",
                ): "Тонкий эстетический вкус, дипломатичность в отношениях.",
                (
                    "Mars",
                    "Scorpio",
                ): "Интенсивная энергия, решительность, способность к трансформации.",
            }

            interpretation = interpretations.get((found_planet, found_sign))
            if interpretation:
                response_text += f"Особенности: {interpretation}"
            else:
                response_text += "Это уникальное сочетание создает особый характер проявления энергии."

            # Форматируем для голоса
            voice_text = russian_adapter.format_for_voice(response_text)

            buttons = [
                "Мой гороскоп",
                "Натальная карта",
                "Другая планета",
                "Совместимость",
            ]

            logger.info("RUSSIAN_LOCALIZATION_PLANET_IN_SIGN_SUCCESS")
            return self.response_formatter.format_text_response(
                text=voice_text, buttons=buttons
            )

        except Exception as e:
            logger.error(f"PLANET_IN_SIGN_HANDLER_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "planet_in_sign"
            )

    async def _handle_house_characteristics(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос о характеристиках домов гороскопа."""
        logger.info("RUSSIAN_LOCALIZATION_HOUSE_CHARACTERISTICS_START")

        try:
            from app.services.russian_astrology_adapter import russian_adapter

            request_text = entities.get("original_text", "").lower()

            # Извлекаем номер дома из запроса
            house_numbers = {
                "первом": 1,
                "втором": 2,
                "третьем": 3,
                "четвертом": 4,
                "пятом": 5,
                "шестом": 6,
                "седьмом": 7,
                "восьмом": 8,
                "девятом": 9,
                "десятом": 10,
                "одиннадцатом": 11,
                "двенадцатом": 12,
            }

            found_house = None
            for house_word, house_num in house_numbers.items():
                if house_word in request_text:
                    found_house = house_num
                    break

            # Если дом не найден, предлагаем выбор
            if not found_house:
                response_text = (
                    "В астрологии есть 12 домов гороскопа. Каждый дом отвечает за определенную "
                    "сферу жизни. Спросите, например: 'Что означает седьмой дом?' или "
                    "'Солнце в четвертом доме'."
                )
                buttons = ["1-й дом", "7-й дом", "10-й дом", "Натальная карта"]
                return self.response_formatter.format_text_response(
                    text=response_text, buttons=buttons
                )

            # Получаем описание дома
            house_desc = russian_adapter.get_russian_house_description(
                found_house
            )

            if "error" in house_desc:
                response_text = (
                    f"Извините, не могу найти информацию о {found_house} доме."
                )
                return self.response_formatter.format_text_response(
                    text=response_text
                )

            # Формируем детальный ответ
            response_text = (
                f"{house_desc['roman']} ({house_desc['name']}):\n\n"
            )
            response_text += f"{house_desc['description']}\n\n"

            if house_desc.get("keywords"):
                keywords = ", ".join(house_desc["keywords"][:5])
                response_text += f"Ключевые темы: {keywords}.\n\n"

            # Дополнительная информация о важных домах
            house_details = {
                1: "Определяет вашу личность и первое впечатление на окружающих.",
                4: "Показывает ваши корни, семью и потребность в безопасности.",
                7: "Раскрывает ваш подход к партнерству и браку.",
                10: "Указывает на карьерные цели и общественное признание.",
            }

            if found_house in house_details:
                response_text += house_details[found_house]

            # Форматируем для голоса
            voice_text = russian_adapter.format_for_voice(response_text)

            buttons = [
                "Мой гороскоп",
                "Натальная карта",
                "Другой дом",
                "Планеты в домах",
            ]

            logger.info("RUSSIAN_LOCALIZATION_HOUSE_CHARACTERISTICS_SUCCESS")
            return self.response_formatter.format_text_response(
                text=voice_text, buttons=buttons
            )

        except Exception as e:
            logger.error(f"HOUSE_CHARACTERISTICS_HANDLER_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "house_characteristics"
            )

    async def _handle_enhanced_compatibility_analysis(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает расширенный анализ совместимости с русскими терминами."""
        logger.info("RUSSIAN_LOCALIZATION_ENHANCED_COMPATIBILITY_START")

        try:
            from app.services.russian_astrology_adapter import russian_adapter

            # Извлекаем знаки из запроса
            request_text = entities.get("original_text", "").lower()

            sign_matches = {
                "овен": "aries",
                "телец": "taurus",
                "близнецы": "gemini",
                "рак": "cancer",
                "лев": "leo",
                "дева": "virgo",
                "весы": "libra",
                "скорпион": "scorpio",
                "стрелец": "sagittarius",
                "козерог": "capricorn",
                "водолей": "aquarius",
                "рыбы": "pisces",
            }

            found_signs = []
            for ru_sign, en_sign in sign_matches.items():
                if ru_sign in request_text:
                    found_signs.append(en_sign)

            # Если знаки не найдены, используем знак пользователя
            user_sign = user_context.zodiac_sign
            if len(found_signs) < 2 and user_sign:
                if user_sign.lower() not in [s.lower() for s in found_signs]:
                    found_signs.append(user_sign.lower())

            if len(found_signs) < 2:
                response_text = (
                    "Для анализа совместимости мне нужны два знака зодиака. "
                    "Скажите, например: 'Совместимость Льва и Стрельца' или "
                    "'Подходят ли Весы и Водолей?'"
                )
                buttons = ["Мой знак", "Обычная совместимость", "Помощь"]
                return self.response_formatter.format_text_response(
                    text=response_text, buttons=buttons
                )

            sign1, sign2 = found_signs[:2]

            # Получаем русские названия знаков
            sign1_ru = russian_adapter.get_russian_sign_description(sign1)[
                "name"
            ]
            sign2_ru = russian_adapter.get_russian_sign_description(sign2)[
                "name"
            ]

            # Используем существующий анализатор совместимости
            compatibility_result = (
                await self.compatibility_analyzer.analyze_compatibility(
                    sign1, sign2, CompatibilityType.ROMANTIC
                )
            )

            if "error" in compatibility_result:
                response_text = "Извините, не могу проанализировать совместимость этих знаков."
                return self.response_formatter.format_text_response(
                    text=response_text
                )

            # Формируем расширенный ответ на русском
            percentage = compatibility_result.get("percentage", 0)
            category = compatibility_result.get("category", "")

            # Переводим категории на русский
            category_translations = {
                "excellent": "отличная",
                "very_good": "очень хорошая",
                "good": "хорошая",
                "moderate": "умеренная",
                "challenging": "сложная",
                "difficult": "трудная",
            }
            category_ru = category_translations.get(category, category)

            response_text = f"Совместимость {sign1_ru} и {sign2_ru}:\n\n"
            response_text += f"Общий показатель: {percentage}% ({category_ru} совместимость)\n\n"

            # Детальный анализ
            strengths = compatibility_result.get("strengths", [])
            challenges = compatibility_result.get("challenges", [])
            advice = compatibility_result.get("advice", [])

            if strengths:
                response_text += "Сильные стороны:\n"
                for strength in strengths[:2]:  # Ограничиваем для голоса
                    response_text += f"• {strength}\n"
                response_text += "\n"

            if challenges and len(challenges) > 0:
                response_text += f"Вызовы: {challenges[0]}\n\n"

            if advice and len(advice) > 0:
                response_text += f"Рекомендация: {advice[0]}"

            # Форматируем для голоса
            voice_text = russian_adapter.format_for_voice(response_text)

            # Ограничиваем длину для Alice
            if len(voice_text) > 800:
                voice_text = (
                    voice_text[:750] + "... Подробности в натальной карте."
                )

            buttons = [
                "Синастрия",
                "Мой гороскоп",
                "Другая пара",
                "Натальная карта",
            ]

            logger.info("RUSSIAN_LOCALIZATION_ENHANCED_COMPATIBILITY_SUCCESS")
            return self.response_formatter.format_text_response(
                text=voice_text, buttons=buttons
            )

        except Exception as e:
            logger.error(f"ENHANCED_COMPATIBILITY_HANDLER_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "enhanced_compatibility"
            )

    async def _handle_retrograde_influence(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос о влиянии ретроградных планет."""
        logger.info("RUSSIAN_LOCALIZATION_RETROGRADE_INFLUENCE_START")

        try:
            from app.services.russian_astrology_adapter import russian_adapter

            request_text = entities.get("original_text", "").lower()

            # Извлекаем планету из запроса
            planet_matches = {
                "меркурий": "Mercury",
                "венера": "Venus",
                "марс": "Mars",
                "юпитер": "Jupiter",
                "сатурн": "Saturn",
                "уран": "Uranus",
                "нептун": "Neptune",
                "плутон": "Pluto",
            }

            found_planet = None
            for ru_planet, en_planet in planet_matches.items():
                if ru_planet in request_text:
                    found_planet = en_planet
                    break

            if not found_planet:
                # Общая информация о ретроградах
                response_text = (
                    "Ретроградное движение планет - это иллюзия обратного движения "
                    "планеты на небе, если смотреть с Земли.\n\n"
                    "Влияние ретроградов:\n"
                    "• Меркурий: проблемы с коммуникацией, техникой, документами\n"
                    "• Венера: пересмотр отношений, финансовых вопросов\n"
                    "• Марс: снижение энергии, задержки в делах\n\n"
                    "Спросите про конкретную планету для подробностей."
                )
                buttons = [
                    "Меркурий ретро",
                    "Венера ретро",
                    "Марс ретро",
                    "Мой гороскоп",
                ]
                return self.response_formatter.format_text_response(
                    text=response_text, buttons=buttons
                )

            # Получаем описание планеты
            planet_desc = russian_adapter.get_russian_planet_description(
                found_planet
            )
            planet_name = planet_desc["name"]

            # Специфические описания ретроградов
            retrograde_descriptions = {
                "Mercury": (
                    f"Ретроградный {planet_name} влияет на:\n\n"
                    "• Общение и коммуникацию - возможны недопонимания\n"
                    "• Технику и транспорт - чаще ломается и глючит\n"
                    "• Документы и договоры - внимательно перечитывайте\n"
                    "• Поездки - возможны задержки и изменения планов\n\n"
                    "Совет: не подписывайте важных договоров, делайте резервные копии файлов."
                ),
                "Venus": (
                    f"Ретроградная {planet_name} влияет на:\n\n"
                    "• Любовные отношения - время переосмысления чувств\n"
                    "• Финансы - не лучший период для крупных покупок\n"
                    "• Красоту и стиль - пересмотр имиджа\n"
                    "• Ценности - переоценка приоритетов\n\n"
                    "Совет: время для внутренней работы, а не новых романов."
                ),
                "Mars": (
                    f"Ретроградный {planet_name} влияет на:\n\n"
                    "• Энергию и активность - снижение мотивации\n"
                    "• Конфликты - старые споры могут возобновиться\n"
                    "• Спорт и физическую активность - больше травм\n"
                    "• Начинания - лучше завершать старые дела\n\n"
                    "Совет: время планирования, а не активных действий."
                ),
                "Jupiter": (
                    f"Ретроградный {planet_name}:\n\n"
                    "• Философские взгляды подвергаются пересмотру\n"
                    "• Образование - время переосмысления знаний\n"
                    "• Путешествия - возможны отмены поездок\n"
                    "• Духовный рост через внутреннюю работу"
                ),
                "Saturn": (
                    f"Ретроградный {planet_name}:\n\n"
                    "• Пересмотр жизненных структур и правил\n"
                    "• Работа с ограничениями и дисциплиной\n"
                    "• Уроки прошлого становятся актуальными\n"
                    "• Время внутренней дисциплины"
                ),
            }

            response_text = retrograde_descriptions.get(
                found_planet,
                f"Ретроградный {planet_name} требует пересмотра связанных с ним сфер жизни.",
            )

            # Форматируем для голоса
            voice_text = russian_adapter.format_for_voice(response_text)

            buttons = [
                "Мой гороскоп",
                "Транзиты",
                "Другая планета",
                "Натальная карта",
            ]

            logger.info("RUSSIAN_LOCALIZATION_RETROGRADE_INFLUENCE_SUCCESS")
            return self.response_formatter.format_text_response(
                text=voice_text, buttons=buttons
            )

        except Exception as e:
            logger.error(f"RETROGRADE_INFLUENCE_HANDLER_ERROR: {e}")
            return self.response_formatter.format_error_response(
                "retrograde_influence"
            )


# Глобальный экземпляр обработчика диалогов
dialog_handler = DialogHandler()
