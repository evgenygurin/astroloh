"""
Основной обработчик диалогов для навыка Яндекс.Диалогов с расширенной функциональностью.
Интегрирует продвинутое управление диалогами, персонализацию и безопасное хранение данных.
"""
import logging
from typing import Any, Dict

from app.models.yandex_models import (
    ProcessedRequest,
    UserContext,
    YandexIntent,
    YandexRequestModel,
    YandexResponseModel,
)
from app.services.astrology_calculator import AstrologyCalculator
from app.services.conversation_manager import ConversationManager
from app.services.dialog_flow_manager import DialogFlowManager, DialogState
from app.services.horoscope_generator import HoroscopeGenerator, HoroscopePeriod
from app.services.intent_recognition import IntentRecognizer
from app.services.lunar_calendar import LunarCalendar
from app.services.natal_chart import NatalChartCalculator
from app.services.response_formatter import ResponseFormatter
from app.services.session_manager import SessionManager
from app.utils.error_handler import ErrorHandler, handle_skill_errors
from app.utils.validators import (
    DateValidator,
    TimeValidator,
    YandexRequestValidator,
    ZodiacValidator,
)


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

        # Валидация запроса
        self.request_validator.validate_request_structure(request.dict())

        # Получение контекста пользователя
        user_context = self.session_manager.get_user_context(request.session)

        # Санитизация пользовательского ввода
        clean_input = self.request_validator.sanitize_user_input(
            request.request.original_utterance
        )

        # Распознавание интента с расширенными возможностями
        processed_request = self.intent_recognizer.recognize_intent(
            clean_input, user_context
        )

        # Обработка в контексте разговора (Stage 5 enhancement)
        try:
            conversation_result = (
                await self.conversation_manager.process_conversation(
                    user_id=request.session.user_id,
                    session_id=request.session.session_id,
                    processed_request=processed_request,
                )
            )
            if (
                isinstance(conversation_result, tuple)
                and len(conversation_result) == 2
            ):
                dialog_state, response_context = conversation_result
            else:
                dialog_state = DialogState.INITIAL
                response_context = {}

            # Генерируем ответ с учетом состояния диалога и контекста
            response = await self._generate_contextual_response(
                dialog_state,
                response_context,
                processed_request,
                request.session,
            )

        except Exception as e:
            self.logger.error(f"Error in conversation processing: {str(e)}")

            # Используем систему восстановления после ошибок (Stage 5)
            (
                error_context,
                recovery_response,
            ) = self.error_recovery_manager.handle_error(
                e,
                {
                    "user_id": request.session.user_id,
                    "session_id": request.session.session_id,
                    "intent": processed_request.intent,
                    "dialog_state": None,  # Будет определено в error_recovery_manager
                },
            )

            # Используем ответ системы восстановления
            response = recovery_response

            # Если восстановление не удалось, fallback к стандартной обработке
            if not response:
                response = await self._process_intent(
                    processed_request, request.session
                )

        # Логирование обработки запроса
        self.error_handler.log_request_processing(
            user_id=request.session.user_id,
            session_id=request.session.session_id,
            intent=processed_request.intent.value,
            success=True,
        )

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
            if hasattr(result, "buttons") and response_context.get(
                "contextual_suggestions"
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
        self, entities: Dict[str, Any], user_context: UserContext, session
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
            birth_date_str = entities["dates"][0]
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

        elif user_context.birth_date:
            # Используем сохраненную дату рождения
            from datetime import date

            birth_date = date.fromisoformat(user_context.birth_date)
            zodiac_sign = self.date_validator.get_zodiac_sign_by_date(
                birth_date
            )

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

        # Если даты нет, запрашиваем её
        self.session_manager.set_awaiting_data(
            session, user_context, "birth_date", YandexIntent.HOROSCOPE
        )

        return self.response_formatter.format_horoscope_request_response()

    async def _handle_compatibility(
        self, entities: Dict[str, Any], user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос совместимости."""

        zodiac_signs = entities.get("zodiac_signs", [])

        # Если есть оба знака
        if len(zodiac_signs) >= 2:
            sign1, sign2 = zodiac_signs[0], zodiac_signs[1]
            user_context.zodiac_sign = sign1
            user_context.partner_sign = sign2
            self.session_manager.clear_awaiting_data(session, user_context)

            # Вычисляем совместимость с деталями
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

                # Вычисляем совместимость с деталями
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

            # Вычисляем совместимость с деталями
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

            # Рассчитываем натальную карту
            natal_chart = self.natal_chart_calculator.calculate_natal_chart(
                birth_date
            )

            return self.response_formatter.format_natal_chart_response(
                natal_chart
            )

        except Exception as e:
            self.error_handler.log_error(
                f"Natal chart calculation error: {str(e)}"
            )
            return self.response_formatter.format_error_response("general")

    async def _handle_lunar_calendar(
        self, user_context: UserContext, session
    ) -> Any:
        """Обрабатывает запрос лунного календаря."""

        try:
            from datetime import datetime

            # Получаем информацию о сегодняшнем лунном дне
            today = datetime.now()
            lunar_info = self.lunar_calendar.get_lunar_day_info(today)

            return self.response_formatter.format_lunar_calendar_response(
                lunar_info
            )

        except Exception as e:
            self.error_handler.log_error(f"Lunar calendar error: {str(e)}")
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
