"""
Продвинутое управление диалоговыми потоками для навыка астролога.
Обеспечивает сложные многоходовые диалоги и контекстную обработку.
"""
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Tuple

from app.models.yandex_models import ProcessedRequest, YandexIntent


class DialogState(Enum):
    """Состояния диалога для сложных сценариев."""

    INITIAL = "initial"
    COLLECTING_BIRTH_DATA = "collecting_birth_data"
    COLLECTING_PARTNER_DATA = "collecting_partner_data"
    PROVIDING_HOROSCOPE = "providing_horoscope"
    EXPLORING_COMPATIBILITY = "exploring_compatibility"
    DISCUSSING_NATAL_CHART = "discussing_natal_chart"
    LUNAR_GUIDANCE = "lunar_guidance"
    GIVING_ADVICE = "giving_advice"
    CLARIFYING_REQUEST = "clarifying_request"
    ERROR_RECOVERY = "error_recovery"


class DialogFlow:
    """Представляет отдельный диалоговый поток."""

    def __init__(
        self, flow_id: str, state: DialogState, context: Dict[str, Any]
    ):
        self.flow_id = flow_id
        self.state = state
        self.context = context
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.step_count = 0
        self.fallback_count = 0

    def update_state(self, new_state: DialogState) -> None:
        """Обновляет состояние диалога."""
        self.state = new_state
        self.updated_at = datetime.now()
        self.step_count += 1

    def add_context(self, key: str, value: Any) -> None:
        """Добавляет данные в контекст диалога."""
        self.context[key] = value
        self.updated_at = datetime.now()

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Проверяет, истек ли диалог."""
        return datetime.now() - self.updated_at > timedelta(
            minutes=timeout_minutes
        )


class DialogFlowManager:
    """Управляет сложными диалоговыми потоками и состояниями."""

    def __init__(self):
        self.active_flows: Dict[str, DialogFlow] = {}
        self.flow_transitions: Dict[
            DialogState, Dict[YandexIntent, DialogState]
        ] = {
            DialogState.INITIAL: {
                YandexIntent.GREET: DialogState.INITIAL,
                YandexIntent.HOROSCOPE: DialogState.COLLECTING_BIRTH_DATA,
                YandexIntent.COMPATIBILITY: DialogState.COLLECTING_PARTNER_DATA,
                YandexIntent.NATAL_CHART: DialogState.COLLECTING_BIRTH_DATA,
                YandexIntent.LUNAR_CALENDAR: DialogState.LUNAR_GUIDANCE,
                YandexIntent.ADVICE: DialogState.GIVING_ADVICE,
                YandexIntent.HELP: DialogState.INITIAL,
            },
            DialogState.COLLECTING_BIRTH_DATA: {
                YandexIntent.HOROSCOPE: DialogState.PROVIDING_HOROSCOPE,
                YandexIntent.NATAL_CHART: DialogState.DISCUSSING_NATAL_CHART,
                YandexIntent.COMPATIBILITY: DialogState.COLLECTING_PARTNER_DATA,
            },
            DialogState.COLLECTING_PARTNER_DATA: {
                YandexIntent.COMPATIBILITY: DialogState.EXPLORING_COMPATIBILITY,
            },
            DialogState.PROVIDING_HOROSCOPE: {
                YandexIntent.HOROSCOPE: DialogState.PROVIDING_HOROSCOPE,
                YandexIntent.COMPATIBILITY: DialogState.COLLECTING_PARTNER_DATA,
                YandexIntent.NATAL_CHART: DialogState.DISCUSSING_NATAL_CHART,
                YandexIntent.LUNAR_CALENDAR: DialogState.LUNAR_GUIDANCE,
            },
            DialogState.EXPLORING_COMPATIBILITY: {
                YandexIntent.COMPATIBILITY: DialogState.EXPLORING_COMPATIBILITY,
                YandexIntent.HOROSCOPE: DialogState.PROVIDING_HOROSCOPE,
                YandexIntent.ADVICE: DialogState.GIVING_ADVICE,
            },
            DialogState.DISCUSSING_NATAL_CHART: {
                YandexIntent.NATAL_CHART: DialogState.DISCUSSING_NATAL_CHART,
                YandexIntent.HOROSCOPE: DialogState.PROVIDING_HOROSCOPE,
                YandexIntent.COMPATIBILITY: DialogState.COLLECTING_PARTNER_DATA,
            },
            DialogState.LUNAR_GUIDANCE: {
                YandexIntent.LUNAR_CALENDAR: DialogState.LUNAR_GUIDANCE,
                YandexIntent.ADVICE: DialogState.GIVING_ADVICE,
                YandexIntent.HOROSCOPE: DialogState.PROVIDING_HOROSCOPE,
            },
            DialogState.GIVING_ADVICE: {
                YandexIntent.ADVICE: DialogState.GIVING_ADVICE,
                YandexIntent.HOROSCOPE: DialogState.PROVIDING_HOROSCOPE,
                YandexIntent.LUNAR_CALENDAR: DialogState.LUNAR_GUIDANCE,
            },
        }

        # Условия для переходов между состояниями
        self.transition_conditions: Dict[
            Tuple[DialogState, YandexIntent], callable
        ] = {
            (
                DialogState.COLLECTING_BIRTH_DATA,
                YandexIntent.HOROSCOPE,
            ): self._has_birth_date,
            (
                DialogState.COLLECTING_BIRTH_DATA,
                YandexIntent.NATAL_CHART,
            ): self._has_birth_date,
            (
                DialogState.COLLECTING_PARTNER_DATA,
                YandexIntent.COMPATIBILITY,
            ): self._has_partner_data,
        }

        self.logger = logging.getLogger(__name__)

    def get_or_create_flow(self, session_id: str, user_id: str) -> DialogFlow:
        """Получает существующий или создает новый диалоговый поток."""
        flow_key = f"{user_id}_{session_id}"

        if flow_key in self.active_flows:
            flow = self.active_flows[flow_key]
            if flow.is_expired():
                self.logger.info(
                    f"Dialog flow {flow_key} expired, creating new one"
                )
                flow = DialogFlow(flow_key, DialogState.INITIAL, {})
                self.active_flows[flow_key] = flow
        else:
            flow = DialogFlow(flow_key, DialogState.INITIAL, {})
            self.active_flows[flow_key] = flow
            self.logger.info(f"Created new dialog flow {flow_key}")

        return flow

    def process_intent_in_flow(
        self, flow: DialogFlow, processed_request: ProcessedRequest
    ) -> Tuple[DialogState, Dict[str, Any]]:
        """Обрабатывает интент в контексте диалогового потока."""
        current_state = flow.state
        intent = processed_request.intent
        entities = processed_request.entities

        # Обновляем контекст потока новыми данными
        self._update_flow_context(flow, entities)

        # Определяем следующее состояние
        next_state = self._determine_next_state(flow, intent, entities)

        # Формируем рекомендации для ответа
        response_context = self._build_response_context(
            flow, next_state, entities
        )

        # Обновляем состояние потока
        if next_state != current_state:
            flow.update_state(next_state)
            self.logger.info(
                f"Dialog flow {flow.flow_id} transitioned from {current_state} to {next_state}"
            )

        return next_state, response_context

    def _determine_next_state(
        self, flow: DialogFlow, intent: YandexIntent, entities: Dict[str, Any]
    ) -> DialogState:
        """Определяет следующее состояние на основе текущего состояния и интента."""
        current_state = flow.state

        # Проверяем возможные переходы из текущего состояния
        if current_state in self.flow_transitions:
            possible_transitions = self.flow_transitions[current_state]

            if intent in possible_transitions:
                target_state = possible_transitions[intent]

                # Проверяем условия перехода
                transition_key = (current_state, intent)
                if transition_key in self.transition_conditions:
                    condition_func = self.transition_conditions[transition_key]
                    if condition_func(flow, entities):
                        return target_state
                    else:
                        # Условие не выполнено, остаемся в том же состоянии
                        return current_state
                else:
                    # Нет специальных условий, переходим
                    return target_state

        # Если нет подходящего перехода, проверяем специальные случаи
        if intent == YandexIntent.HELP:
            return DialogState.INITIAL
        elif intent == YandexIntent.GREET:
            return DialogState.INITIAL
        elif intent == YandexIntent.UNKNOWN:
            return DialogState.CLARIFYING_REQUEST

        # По умолчанию остаемся в текущем состоянии
        return current_state

    def _update_flow_context(
        self, flow: DialogFlow, entities: Dict[str, Any]
    ) -> None:
        """Обновляет контекст потока новыми сущностями."""
        if entities.get("zodiac_signs"):
            if "user_zodiac" not in flow.context:
                flow.add_context("user_zodiac", entities["zodiac_signs"][0])
            elif (
                "partner_zodiac" not in flow.context
                and len(entities["zodiac_signs"]) > 0
            ):
                flow.add_context("partner_zodiac", entities["zodiac_signs"][0])

        if entities.get("dates"):
            flow.add_context("birth_date", entities["dates"][0])

        if entities.get("times"):
            flow.add_context("birth_time", entities["times"][0])

        if entities.get("names"):
            flow.add_context("names", entities["names"])

        if entities.get("sentiment"):
            flow.add_context("current_sentiment", entities["sentiment"])

        if entities.get("periods"):
            flow.add_context("requested_periods", entities["periods"])

    def _build_response_context(
        self,
        flow: DialogFlow,
        next_state: DialogState,
        entities: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Формирует контекст для генерации ответа."""
        context = {
            "current_state": flow.state.value,
            "next_state": next_state.value,
            "flow_context": flow.context.copy(),
            "step_count": flow.step_count,
            "suggestions": self._get_state_suggestions(next_state),
            "required_data": self._get_required_data(next_state, flow.context),
            "can_provide_service": self._can_provide_service(
                next_state, flow.context
            ),
        }

        # Добавляем специфичную для состояния информацию
        if next_state == DialogState.COLLECTING_BIRTH_DATA:
            context["missing_birth_info"] = self._get_missing_birth_info(
                flow.context
            )
        elif next_state == DialogState.COLLECTING_PARTNER_DATA:
            context["missing_partner_info"] = self._get_missing_partner_info(
                flow.context
            )
        elif next_state == DialogState.ERROR_RECOVERY:
            context[
                "error_suggestions"
            ] = self._get_error_recovery_suggestions(flow)

        return context

    def _get_state_suggestions(self, state: DialogState) -> List[str]:
        """Возвращает предложения для пользователя в зависимости от состояния."""
        suggestions = {
            DialogState.INITIAL: [
                "Узнать гороскоп",
                "Проверить совместимость",
                "Натальная карта",
                "Лунный календарь",
            ],
            DialogState.COLLECTING_BIRTH_DATA: [
                "Назвать дату рождения",
                "Указать время рождения",
                "Выбрать другой сервис",
            ],
            DialogState.COLLECTING_PARTNER_DATA: [
                "Назвать знак партнера",
                "Указать дату рождения партнера",
                "Вернуться к гороскопу",
            ],
            DialogState.PROVIDING_HOROSCOPE: [
                "Гороскоп на другой период",
                "Проверить совместимость",
                "Лунный календарь",
                "Получить совет",
            ],
            DialogState.EXPLORING_COMPATIBILITY: [
                "Подробнее о совместимости",
                "Советы для отношений",
                "Мой гороскоп",
                "Другая пара",
            ],
            DialogState.DISCUSSING_NATAL_CHART: [
                "Подробнее о характере",
                "Карьерные аспекты",
                "Отношения и любовь",
                "Мой гороскоп",
            ],
            DialogState.LUNAR_GUIDANCE: [
                "Советы на сегодня",
                "Фазы луны",
                "Мой гороскоп",
                "Планы на неделю",
            ],
            DialogState.GIVING_ADVICE: [
                "Другой совет",
                "Мой гороскоп",
                "Лунный календарь",
                "Помощь",
            ],
        }

        return suggestions.get(state, ["Помощь", "Начать сначала"])

    def _get_required_data(
        self, state: DialogState, context: Dict[str, Any]
    ) -> List[str]:
        """Определяет, какие данные необходимы для текущего состояния."""
        required = []

        if state in [
            DialogState.COLLECTING_BIRTH_DATA,
            DialogState.PROVIDING_HOROSCOPE,
            DialogState.DISCUSSING_NATAL_CHART,
        ]:
            if "birth_date" not in context:
                required.append("birth_date")

        if state == DialogState.COLLECTING_PARTNER_DATA:
            if "user_zodiac" not in context:
                required.append("user_zodiac")
            if "partner_zodiac" not in context:
                required.append("partner_zodiac")

        return required

    def _can_provide_service(
        self, state: DialogState, context: Dict[str, Any]
    ) -> bool:
        """Проверяет, можно ли предоставить запрашиваемую услугу."""
        required_data = self._get_required_data(state, context)
        return len(required_data) == 0

    def _get_missing_birth_info(self, context: Dict[str, Any]) -> List[str]:
        """Определяет недостающую информацию о рождении."""
        missing = []
        if "birth_date" not in context:
            missing.append("birth_date")
        if "birth_time" not in context:
            missing.append("birth_time")
        return missing

    def _get_missing_partner_info(self, context: Dict[str, Any]) -> List[str]:
        """Определяет недостающую информацию о партнере."""
        missing = []
        if "partner_zodiac" not in context:
            missing.append("partner_zodiac")
        return missing

    def _get_error_recovery_suggestions(self, flow: DialogFlow) -> List[str]:
        """Возвращает предложения для восстановления после ошибки."""
        return [
            "Попробуйте переформулировать вопрос",
            "Скажите 'помощь' для получения справки",
            "Начните с простого запроса гороскопа",
            "Назовите свой знак зодиака",
        ]

    def _has_birth_date(
        self, flow: DialogFlow, entities: Dict[str, Any]
    ) -> bool:
        """Проверяет наличие даты рождения."""
        return "birth_date" in flow.context or entities.get("dates")

    def _has_partner_data(
        self, flow: DialogFlow, entities: Dict[str, Any]
    ) -> bool:
        """Проверяет наличие данных о партнере."""
        return (
            "user_zodiac" in flow.context and "partner_zodiac" in flow.context
        ) or len(entities.get("zodiac_signs", [])) >= 2

    def cleanup_expired_flows(self) -> int:
        """Удаляет истекшие диалоговые потоки."""
        expired_keys = [
            key for key, flow in self.active_flows.items() if flow.is_expired()
        ]

        for key in expired_keys:
            del self.active_flows[key]
            self.logger.info(f"Cleaned up expired dialog flow {key}")

        return len(expired_keys)

    def get_flow_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику диалоговых потоков."""
        if not self.active_flows:
            return {"total_flows": 0, "states": {}, "average_steps": 0}

        state_counts = {}
        total_steps = 0

        for flow in self.active_flows.values():
            state = flow.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
            total_steps += flow.step_count

        return {
            "total_flows": len(self.active_flows),
            "states": state_counts,
            "average_steps": total_steps / len(self.active_flows)
            if self.active_flows
            else 0,
        }
