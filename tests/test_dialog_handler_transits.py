"""
Тесты для обработки новых интентов в DialogHandler.
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch

from app.services.dialog_handler import DialogHandler
from app.models.yandex_models import (
    YandexIntent,
    YandexRequestModel,
    YandexRequestMeta,
    YandexRequestType,
    YandexSession,
    YandexRequestData,
    UserContext,
)


class TestDialogHandlerTransits:
    """Тесты для новых интентов в DialogHandler."""

    def setup_method(self):
        """Настройка для каждого теста."""
        self.dialog_handler = DialogHandler()

        # Мок сессии
        self.mock_session = YandexSession(
            session_id="test_session",
            user_id="test_user",
            skill_id="test_skill",
            message_id=1,
            new=False,
        )

        # Мок запроса
        self.mock_request = YandexRequestData(
            command="транзиты",
            original_utterance="какие транзиты у меня сейчас",
            type=YandexRequestType.SIMPLE_UTTERANCE,
        )

        # Мок метаданных
        self.mock_meta = YandexRequestMeta(
            locale="ru-RU", timezone="Europe/Moscow", client_id="test_client"
        )

        # Полный запрос
        self.full_request = YandexRequestModel(
            meta=self.mock_meta,
            session=self.mock_session,
            request=self.mock_request,
            version="1.0",
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_transits_without_birth_date(self):
        """Тест обработки транзитов без даты рождения."""
        entities = {}
        user_context = UserContext()

        with (
            patch.object(
                self.dialog_handler.session_manager, "set_awaiting_data"
            ) as mock_set_awaiting,
            patch.object(
                self.dialog_handler.response_formatter,
                "format_transit_request_response",
            ) as mock_format,
        ):
            mock_format.return_value = Mock()

            await self.dialog_handler._handle_transits(
                entities, user_context, self.mock_session
            )

            mock_set_awaiting.assert_called_once_with(
                self.mock_session, user_context, "birth_date", YandexIntent.TRANSITS
            )
            mock_format.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_transits_with_birth_date(self):
        """Тест обработки транзитов с датой рождения."""
        entities = {}
        user_context = UserContext()
        user_context.birth_date = "1990-03-15"

        mock_natal_chart = {
            "planets": {
                "Sun": {"longitude": 354.5, "sign": "Рыбы"},
                "Moon": {"longitude": 120.0, "sign": "Лев"},
            }
        }

        mock_transits = {
            "active_transits": [
                {
                    "transit_planet": "Jupiter",
                    "natal_planet": "Sun",
                    "aspect": "Трин",
                    "influence": "Удачный период",
                }
            ],
            "summary": "Благоприятные влияния",
        }

        with (
            patch.object(
                self.dialog_handler.natal_chart_calculator, "calculate_natal_chart"
            ) as mock_natal,
            patch.object(
                self.dialog_handler.transit_calculator, "calculate_current_transits"
            ) as mock_transits_calc,
            patch.object(
                self.dialog_handler.response_formatter, "format_transits_response"
            ) as mock_format,
        ):
            mock_natal.return_value = mock_natal_chart
            mock_transits_calc.return_value = mock_transits
            mock_format.return_value = Mock()

            await self.dialog_handler._handle_transits(
                entities, user_context, self.mock_session
            )

            mock_natal.assert_called_once()
            mock_transits_calc.assert_called_once_with(mock_natal_chart["planets"])
            mock_format.assert_called_once_with(mock_transits)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_progressions_without_birth_date(self):
        """Тест обработки прогрессий без даты рождения."""
        entities = {}
        user_context = UserContext()

        with (
            patch.object(
                self.dialog_handler.session_manager, "set_awaiting_data"
            ) as mock_set_awaiting,
            patch.object(
                self.dialog_handler.response_formatter,
                "format_progressions_request_response",
            ) as mock_format,
        ):
            mock_format.return_value = Mock()

            await self.dialog_handler._handle_progressions(
                entities, user_context, self.mock_session
            )

            mock_set_awaiting.assert_called_once_with(
                self.mock_session, user_context, "birth_date", YandexIntent.PROGRESSIONS
            )
            mock_format.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_progressions_with_birth_date(self):
        """Тест обработки прогрессий с датой рождения."""
        entities = {}
        user_context = UserContext()
        user_context.birth_date = "1985-07-20"

        mock_progressions = {
            "interpretation": {
                "current_age": 39,
                "life_stage": "Зрелость",
                "progressed_sun": {"sign": "Дева", "meaning": "Совершенствование"},
                "general_trends": ["Период анализа и детализации"],
            }
        }

        with (
            patch.object(
                self.dialog_handler.natal_chart_calculator, "calculate_progressions"
            ) as mock_progressions_calc,
            patch.object(
                self.dialog_handler.response_formatter, "format_progressions_response"
            ) as mock_format,
        ):
            mock_progressions_calc.return_value = mock_progressions
            mock_format.return_value = Mock()

            await self.dialog_handler._handle_progressions(
                entities, user_context, self.mock_session
            )

            mock_progressions_calc.assert_called_once()
            mock_format.assert_called_once_with(mock_progressions)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_solar_return_with_birth_date(self):
        """Тест обработки соляра с датой рождения."""
        entities = {}
        user_context = UserContext()
        user_context.birth_date = "1990-06-15"

        mock_solar_return = {
            "year": 2024,
            "interpretation": {
                "year_theme": "Год творческого самовыражения",
                "key_areas": ["творчество", "любовь", "самовыражение"],
                "opportunities": ["Новые творческие проекты"],
            },
        }

        with (
            patch.object(
                self.dialog_handler.transit_calculator, "calculate_solar_return"
            ) as mock_solar_calc,
            patch.object(
                self.dialog_handler.response_formatter, "format_solar_return_response"
            ) as mock_format,
        ):
            mock_solar_calc.return_value = mock_solar_return
            mock_format.return_value = Mock()

            await self.dialog_handler._handle_solar_return(
                entities, user_context, self.mock_session
            )

            birth_date = date.fromisoformat(user_context.birth_date)
            current_year = date.today().year
            mock_solar_calc.assert_called_once_with(birth_date, current_year)
            mock_format.assert_called_once_with(mock_solar_return)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_lunar_return_with_birth_date(self):
        """Тест обработки лунара с датой рождения."""
        entities = {}
        user_context = UserContext()
        user_context.birth_date = "1992-12-25"

        mock_lunar_return = {
            "month": 12,
            "year": 2024,
            "interpretation": {
                "emotional_theme": "Глубокие эмоциональные переживания",
                "action_theme": "Время рефлексии",
                "general_advice": "Следуйте интуиции",
            },
        }

        with (
            patch.object(
                self.dialog_handler.transit_calculator, "calculate_lunar_return"
            ) as mock_lunar_calc,
            patch.object(
                self.dialog_handler.response_formatter, "format_lunar_return_response"
            ) as mock_format,
        ):
            mock_lunar_calc.return_value = mock_lunar_return
            mock_format.return_value = Mock()

            await self.dialog_handler._handle_lunar_return(
                entities, user_context, self.mock_session
            )

            birth_date = date.fromisoformat(user_context.birth_date)
            current_date = date.today()
            mock_lunar_calc.assert_called_once_with(
                birth_date, current_date.month, current_date.year
            )
            mock_format.assert_called_once_with(mock_lunar_return)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transits_error_handling(self):
        """Тест обработки ошибок при расчете транзитов."""
        entities = {}
        user_context = UserContext()
        user_context.birth_date = "1988-04-12"

        with (
            patch.object(
                self.dialog_handler.natal_chart_calculator, "calculate_natal_chart"
            ) as mock_natal,
            patch("app.services.dialog_handler.logger") as mock_logger,
            patch.object(
                self.dialog_handler.response_formatter, "format_error_response"
            ) as mock_format_error,
        ):
            # Имитируем ошибку
            mock_natal.side_effect = Exception("Test error")
            mock_format_error.return_value = Mock()

            await self.dialog_handler._handle_transits(
                entities, user_context, self.mock_session
            )

            mock_logger.error.assert_called_once()
            mock_format_error.assert_called_once_with("general")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_transit_request_flow(self):
        """Интеграционный тест полного потока запроса транзитов."""
        # Создаем полный запрос
        request = YandexRequestModel(
            meta=self.mock_meta,
            session=self.mock_session,
            request=YandexRequestData(
                command="какие транзиты у меня сейчас",
                original_utterance="какие транзиты у меня сейчас",
                type=YandexRequestType.SIMPLE_UTTERANCE,
            ),
            version="1.0",
        )

        with (
            patch.object(
                self.dialog_handler.intent_recognizer, "recognize_intent"
            ) as mock_recognize,
            patch.object(
                self.dialog_handler.session_manager, "get_user_context"
            ) as mock_get_context,
            patch.object(
                self.dialog_handler.conversation_manager, "process_conversation"
            ) as mock_conversation,
        ):
            # Настраиваем моки
            mock_recognize.return_value = Mock(
                intent=YandexIntent.TRANSITS, entities={}, user_context=UserContext()
            )

            mock_get_context.return_value = UserContext()

            # Имитируем обычный поток без продвинутого управления диалогами
            mock_conversation.side_effect = Exception(
                "Conversation manager not available"
            )

            # Проверяем, что обработчик не падает
            response = await self.dialog_handler.handle_request(request)

            assert response is not None
            assert hasattr(response, "response")

    @pytest.mark.unit
    def test_new_intents_in_process_intent(self):
        """Тест обработки новых интентов в _process_intent."""
        # Проверяем, что новые интенты правильно обрабатываются в основном методе
        assert hasattr(self.dialog_handler, "_handle_transits")
        assert hasattr(self.dialog_handler, "_handle_progressions")
        assert hasattr(self.dialog_handler, "_handle_solar_return")
        assert hasattr(self.dialog_handler, "_handle_lunar_return")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_birth_date_handling(self):
        """Тест обработки некорректной даты рождения."""
        entities = {}
        user_context = UserContext()
        user_context.birth_date = "invalid-date"  # Некорректная дата

        with (
            patch("app.services.dialog_handler.logger") as mock_logger,
            patch.object(
                self.dialog_handler.response_formatter, "format_error_response"
            ) as mock_format_error,
        ):
            mock_format_error.return_value = Mock()

            await self.dialog_handler._handle_transits(
                entities, user_context, self.mock_session
            )

            # Должна быть зафиксирована ошибка
            mock_logger.error.assert_called_once()
            mock_format_error.assert_called_once_with("general")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_new_handlers_performance(self):
        """Тест производительности новых обработчиков."""
        import time

        entities = {}
        user_context = UserContext()
        user_context.birth_date = "1991-05-10"

        # Мочим внешние зависимости для измерения производительности
        with (
            patch.object(
                self.dialog_handler.natal_chart_calculator, "calculate_natal_chart"
            ) as mock_natal,
            patch.object(
                self.dialog_handler.transit_calculator, "calculate_current_transits"
            ) as mock_transits,
            patch.object(
                self.dialog_handler.response_formatter, "format_transits_response"
            ) as mock_format,
        ):
            mock_natal.return_value = {"planets": {}}
            mock_transits.return_value = {"active_transits": []}
            mock_format.return_value = Mock()

            start_time = time.time()

            # Выполняем несколько запросов
            for _ in range(10):
                await self.dialog_handler._handle_transits(
                    entities, user_context, self.mock_session
                )

            end_time = time.time()
            execution_time = end_time - start_time

            # Проверяем производительность
            assert execution_time < 1.0  # Менее 1 секунды для 10 запросов
