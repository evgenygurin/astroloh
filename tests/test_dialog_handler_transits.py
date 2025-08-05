"""
Тесты для обработчика диалогов с новой функциональностью транзитов.
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.yandex_models import YandexIntent, YandexRequestModel, YandexSession
from app.services.dialog_handler import DialogHandler


class TestDialogHandlerTransits:
    """Тесты для новой функциональности транзитов в DialogHandler."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.dialog_handler = DialogHandler()
        self.test_session = YandexSession(
            session_id="test_session",
            message_id=1,
            user_id="test_user",
            new=False,
        )

    @pytest.mark.asyncio
    async def test_handle_transits_without_birth_date(self):
        """Тест обработки запроса транзитов без даты рождения."""
        # Мокаем session_manager
        mock_user_context = MagicMock()
        mock_user_context.birth_date = None

        with patch.object(
            self.dialog_handler.session_manager,
            "get_user_context",
            return_value=mock_user_context,
        ), patch.object(
            self.dialog_handler.session_manager, "set_awaiting_data"
        ) as mock_set_awaiting, patch.object(
            self.dialog_handler.response_formatter,
            "format_birth_date_request_for_transits",
        ) as mock_format_request:
            
            mock_format_request.return_value = MagicMock()

            result = await self.dialog_handler._handle_transits(
                {}, mock_user_context, self.test_session
            )

            mock_set_awaiting.assert_called_once_with(
                self.test_session,
                mock_user_context,
                "birth_date",
                YandexIntent.TRANSITS,
            )
            mock_format_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_transits_with_birth_date(self):
        """Тест обработки запроса транзитов с датой рождения."""
        # Мокаем user_context с датой рождения
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "1990-03-15"

        # Мокаем результат расчета транзитов
        mock_transits = {
            "summary": {"overall_influence": "благоприятный"},
            "significant_transits": [],
        }

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_current_transits",
            return_value=mock_transits,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_transits_response",
        ) as mock_format_response:
            
            mock_format_response.return_value = MagicMock()

            result = await self.dialog_handler._handle_transits(
                {}, mock_user_context, self.test_session
            )

            mock_format_response.assert_called_once_with(mock_transits)

    @pytest.mark.asyncio
    async def test_handle_transits_calculation_error(self):
        """Тест обработки ошибки при расчете транзитов."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "1990-03-15"

        # Мокаем ошибку в расчете транзитов
        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_current_transits",
            side_effect=Exception("Test error"),
        ), patch.object(
            self.dialog_handler.error_handler, "log_error"
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_error_response",
        ) as mock_format_error:
            
            mock_format_error.return_value = MagicMock()

            result = await self.dialog_handler._handle_transits(
                {}, mock_user_context, self.test_session
            )

            mock_format_error.assert_called_once_with("general")

    @pytest.mark.asyncio
    async def test_handle_progressions_without_birth_date(self):
        """Тест обработки запроса прогрессий без даты рождения."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = None

        with patch.object(
            self.dialog_handler.session_manager, "set_awaiting_data"
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_birth_date_request_for_progressions",
        ) as mock_format_request:
            
            mock_format_request.return_value = MagicMock()

            result = await self.dialog_handler._handle_progressions(
                {}, mock_user_context, self.test_session
            )

            mock_format_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_progressions_with_birth_date(self):
        """Тест обработки запроса прогрессий с датой рождения."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "1990-03-15"

        mock_progressions = {
            "interpretation": {"life_phase": "период развития"},
            "years_lived": 34.0,
            "progressions": [],
        }

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_progressions",
            return_value=mock_progressions,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_progressions_response",
        ) as mock_format_response:
            
            mock_format_response.return_value = MagicMock()

            result = await self.dialog_handler._handle_progressions(
                {}, mock_user_context, self.test_session
            )

            mock_format_response.assert_called_once_with(mock_progressions)

    @pytest.mark.asyncio
    async def test_handle_solar_return_without_birth_date(self):
        """Тест обработки запроса соляра без даты рождения."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = None

        with patch.object(
            self.dialog_handler.session_manager, "set_awaiting_data"
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_birth_date_request_for_solar",
        ) as mock_format_request:
            
            mock_format_request.return_value = MagicMock()

            result = await self.dialog_handler._handle_solar_return(
                {}, mock_user_context, self.test_session
            )

            mock_format_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_solar_return_with_birth_date(self):
        """Тест обработки запроса соляра с датой рождения."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "1990-03-15"

        mock_solar_return = {
            "solar_year": 2024,
            "interpretation": {"year_theme": "личностное развитие"},
        }

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_solar_return",
            return_value=mock_solar_return,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_solar_return_response",
        ) as mock_format_response:
            
            mock_format_response.return_value = MagicMock()

            result = await self.dialog_handler._handle_solar_return(
                {}, mock_user_context, self.test_session
            )

            mock_format_response.assert_called_once_with(mock_solar_return)

    @pytest.mark.asyncio
    async def test_handle_lunar_return_without_birth_date(self):
        """Тест обработки запроса лунара без даты рождения."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = None

        with patch.object(
            self.dialog_handler.session_manager, "set_awaiting_data"
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_birth_date_request_for_lunar",
        ) as mock_format_request:
            
            mock_format_request.return_value = MagicMock()

            result = await self.dialog_handler._handle_lunar_return(
                {}, mock_user_context, self.test_session
            )

            mock_format_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_lunar_return_with_birth_date(self):
        """Тест обработки запроса лунара с датой рождения."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "1990-03-15"

        mock_lunar_return = {
            "lunar_date": "2024-03-15",
            "interpretation": {"monthly_theme": "семейные вопросы"},
        }

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_lunar_return",
            return_value=mock_lunar_return,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_lunar_return_response",
        ) as mock_format_response:
            
            mock_format_response.return_value = MagicMock()

            result = await self.dialog_handler._handle_lunar_return(
                {}, mock_user_context, self.test_session
            )

            mock_format_response.assert_called_once_with(mock_lunar_return)

    @pytest.mark.asyncio
    async def test_process_intent_transits(self):
        """Тест обработки интента транзитов через основной метод."""
        mock_processed_request = MagicMock()
        mock_processed_request.intent = YandexIntent.TRANSITS
        mock_processed_request.entities = {}
        mock_processed_request.user_context = MagicMock()
        mock_processed_request.user_context.birth_date = "1990-03-15"

        mock_transits = {"summary": {"overall_influence": "смешанный"}}

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_current_transits",
            return_value=mock_transits,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_transits_response",
        ) as mock_format_response:
            
            mock_format_response.return_value = MagicMock()

            result = await self.dialog_handler._process_intent(
                mock_processed_request, self.test_session
            )

            mock_format_response.assert_called_once_with(mock_transits)

    @pytest.mark.asyncio
    async def test_process_intent_progressions(self):
        """Тест обработки интента прогрессий через основной метод."""
        mock_processed_request = MagicMock()
        mock_processed_request.intent = YandexIntent.PROGRESSIONS
        mock_processed_request.entities = {}
        mock_processed_request.user_context = MagicMock()
        mock_processed_request.user_context.birth_date = "1990-03-15"

        mock_progressions = {"interpretation": {"life_phase": "стабильность"}}

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_progressions",
            return_value=mock_progressions,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_progressions_response",
        ) as mock_format_response:
            
            mock_format_response.return_value = MagicMock()

            result = await self.dialog_handler._process_intent(
                mock_processed_request, self.test_session
            )

            mock_format_response.assert_called_once_with(mock_progressions)

    @pytest.mark.asyncio
    async def test_error_handling_in_transits(self):
        """Тест обработки ошибок в транзитах с fallback."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "1990-03-15"

        # Мокаем транзитный ответ с ошибкой
        mock_transits_with_error = {"error": "Calculation failed"}

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_current_transits",
            return_value=mock_transits_with_error,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_error_response",
        ) as mock_format_error:
            
            mock_format_error.return_value = MagicMock()

            result = await self.dialog_handler._handle_transits(
                {}, mock_user_context, self.test_session
            )

            mock_format_error.assert_called_once_with("general")

    def test_transit_calculator_initialization(self):
        """Тест инициализации TransitCalculator в DialogHandler."""
        # Проверяем, что TransitCalculator создается при инициализации
        handler = DialogHandler()
        assert hasattr(handler, "transit_calculator")
        assert handler.transit_calculator is not None

    @pytest.mark.asyncio
    async def test_invalid_birth_date_format(self):
        """Тест обработки некорректного формата даты рождения."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "invalid-date"

        with patch("app.services.dialog_handler.date") as mock_date:
            mock_date.fromisoformat.side_effect = ValueError("Invalid date format")
            
            with patch.object(
                self.dialog_handler.error_handler, "log_error"
            ), patch.object(
                self.dialog_handler.response_formatter,
                "format_error_response",
            ) as mock_format_error:
                
                mock_format_error.return_value = MagicMock()

                result = await self.dialog_handler._handle_transits(
                    {}, mock_user_context, self.test_session
                )

                mock_format_error.assert_called_once_with("general")

    @pytest.mark.asyncio
    async def test_multiple_transit_calculations(self):
        """Тест последовательных вызовов разных типов транзитов."""
        mock_user_context = MagicMock()
        mock_user_context.birth_date = "1990-03-15"

        # Мокаем разные типы ответов
        mock_transits = {"summary": {"overall_influence": "активный"}}
        mock_progressions = {"interpretation": {"life_phase": "развитие"}}
        mock_solar = {"solar_year": 2024}
        mock_lunar = {"lunar_date": "2024-03-15"}

        with patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_current_transits",
            return_value=mock_transits,
        ), patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_progressions",
            return_value=mock_progressions,
        ), patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_solar_return",
            return_value=mock_solar,
        ), patch.object(
            self.dialog_handler.transit_calculator,
            "calculate_lunar_return",
            return_value=mock_lunar,
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_transits_response",
            return_value=MagicMock(),
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_progressions_response",
            return_value=MagicMock(),
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_solar_return_response",
            return_value=MagicMock(),
        ), patch.object(
            self.dialog_handler.response_formatter,
            "format_lunar_return_response",
            return_value=MagicMock(),
        ):

            # Последовательно тестируем все типы
            await self.dialog_handler._handle_transits(
                {}, mock_user_context, self.test_session
            )
            await self.dialog_handler._handle_progressions(
                {}, mock_user_context, self.test_session
            )
            await self.dialog_handler._handle_solar_return(
                {}, mock_user_context, self.test_session
            )
            await self.dialog_handler._handle_lunar_return(
                {}, mock_user_context, self.test_session
            )

            # Все вызовы должны пройти без ошибок

    @pytest.mark.parametrize(
        "intent,handler_method",
        [
            (YandexIntent.TRANSITS, "_handle_transits"),
            (YandexIntent.PROGRESSIONS, "_handle_progressions"),
            (YandexIntent.SOLAR_RETURN, "_handle_solar_return"),
            (YandexIntent.LUNAR_RETURN, "_handle_lunar_return"),
        ],
    )
    @pytest.mark.asyncio
    async def test_intent_routing(self, intent, handler_method):
        """Тест маршрутизации интентов к соответствующим обработчикам."""
        mock_processed_request = MagicMock()
        mock_processed_request.intent = intent
        mock_processed_request.entities = {}
        mock_processed_request.user_context = MagicMock()

        with patch.object(
            self.dialog_handler, handler_method, return_value=MagicMock()
        ) as mock_handler:
            
            await self.dialog_handler._process_intent(
                mock_processed_request, self.test_session
            )

            mock_handler.assert_called_once()

    def test_new_intents_in_enum(self):
        """Тест наличия новых интентов в перечислении."""
        # Проверяем, что новые интенты добавлены в YandexIntent
        assert hasattr(YandexIntent, "TRANSITS")
        assert hasattr(YandexIntent, "PROGRESSIONS")
        assert hasattr(YandexIntent, "SOLAR_RETURN")
        assert hasattr(YandexIntent, "LUNAR_RETURN")

        assert YandexIntent.TRANSITS == "transits"
        assert YandexIntent.PROGRESSIONS == "progressions"
        assert YandexIntent.SOLAR_RETURN == "solar_return"
        assert YandexIntent.LUNAR_RETURN == "lunar_return"