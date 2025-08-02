"""
Tests for error recovery functionality.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.models.yandex_models import (
    YandexRequestData,
    YandexRequestMeta,
    YandexRequestModel,
    YandexRequestType,
    YandexSession,
)
from app.services.error_recovery import (
    ErrorRecoveryManager,
    ErrorSeverity,
    ErrorType,
    RecoveryStrategy,
)


class TestErrorRecoveryService:
    """Tests for error recovery service."""

    def setup_method(self):
        """Setup before each test."""
        self.error_recovery = ErrorRecoveryManager()

    def create_mock_request(
        self, command: str = "тест", user_id: str = "test_user"
    ) -> YandexRequestModel:
        """Create mock Yandex request."""
        return YandexRequestModel(
            meta=YandexRequestMeta(
                locale="ru-RU",
                timezone="Europe/Moscow",
                client_id="test_client",
            ),
            request=YandexRequestData(
                command=command,
                original_utterance=command,
                type=YandexRequestType.SIMPLE_UTTERANCE,
            ),
            session=YandexSession(
                message_id=1,
                session_id="test_session",
                skill_id="test_skill",
                user_id=user_id,
                user={"user_id": user_id},
                application={"application_id": "test_app"},
                new=False,
            ),
            version="1.0",
        )

    def test_classify_error_validation_error(self):
        """Test classification of validation errors."""
        error = ValueError("Invalid date format")
        request = self.create_mock_request("гороскоп на 32 января")

        error_type, severity = self.error_recovery.classify_error(
            error, request
        )

        assert error_type == ErrorType.VALIDATION_ERROR
        assert severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]

    def test_classify_error_missing_data(self):
        """Test classification of missing data errors."""
        error = KeyError("birth_date")
        request = self.create_mock_request("составь натальную карту")

        error_type, severity = self.error_recovery.classify_error(
            error, request
        )

        assert error_type == ErrorType.MISSING_DATA
        assert severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]

    def test_classify_error_calculation_error(self):
        """Test classification of calculation errors."""
        error = Exception("Swiss Ephemeris calculation failed")
        request = self.create_mock_request("мой гороскоп")

        error_type, severity = self.error_recovery.classify_error(
            error, request
        )

        assert error_type == ErrorType.CALCULATION_ERROR
        assert severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]

    def test_classify_error_database_error(self):
        """Test classification of database errors."""
        error = ConnectionError("Database connection failed")
        request = self.create_mock_request("сохрани мои данные")

        error_type, severity = self.error_recovery.classify_error(
            error, request
        )

        assert error_type == ErrorType.DATABASE_ERROR
        assert severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]

    def test_get_recovery_strategy_validation_error(self):
        """Test recovery strategy for validation errors."""
        strategy = self.error_recovery.get_recovery_strategy(
            ErrorType.VALIDATION_ERROR, ErrorSeverity.MEDIUM
        )

        assert strategy == RecoveryStrategy.REQUEST_CLARIFICATION

    def test_get_recovery_strategy_missing_data(self):
        """Test recovery strategy for missing data."""
        strategy = self.error_recovery.get_recovery_strategy(
            ErrorType.MISSING_DATA, ErrorSeverity.MEDIUM
        )

        assert strategy == RecoveryStrategy.REQUEST_ADDITIONAL_DATA

    def test_get_recovery_strategy_critical_error(self):
        """Test recovery strategy for critical errors."""
        strategy = self.error_recovery.get_recovery_strategy(
            ErrorType.SYSTEM_ERROR, ErrorSeverity.CRITICAL
        )

        assert strategy == RecoveryStrategy.GRACEFUL_DEGRADATION

    @pytest.mark.asyncio
    async def test_handle_error_with_clarification(self):
        """Test error handling with clarification strategy."""
        error = ValueError("Invalid date")
        request = self.create_mock_request("гороскоп на вчера")
        mock_context = MagicMock()

        with patch(
            "app.services.error_recovery.ResponseFormatter"
        ) as mock_formatter:
            mock_response = MagicMock()
            mock_formatter.return_value.format_clarification_response.return_value = (
                mock_response
            )

            result = await self.error_recovery.handle_error(
                error, request, mock_context
            )

            assert result == mock_response
            mock_formatter.return_value.format_clarification_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_error_with_fallback(self):
        """Test error handling with fallback strategy."""
        error = ConnectionError("Service unavailable")
        request = self.create_mock_request("мой гороскоп")
        mock_context = MagicMock()

        with patch(
            "app.services.error_recovery.ResponseFormatter"
        ) as mock_formatter:
            mock_response = MagicMock()
            mock_formatter.return_value.format_fallback_response.return_value = (
                mock_response
            )

            result = await self.error_recovery.handle_error(
                error, request, mock_context
            )

            assert result == mock_response
            mock_formatter.return_value.format_fallback_response.assert_called_once()

    def test_generate_error_suggestions_validation(self):
        """Test generation of error suggestions for validation errors."""
        request = self.create_mock_request("гороскоп на 30 февраля")
        mock_context = MagicMock()
        mock_context.preferences = {}

        suggestions = self.error_recovery.generate_error_suggestions(
            ErrorType.VALIDATION_ERROR, request, mock_context
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("дата" in suggestion.lower() for suggestion in suggestions)

    def test_generate_error_suggestions_missing_data(self):
        """Test generation of error suggestions for missing data."""
        request = self.create_mock_request("составь натальную карту")
        mock_context = MagicMock()
        mock_context.preferences = {}

        suggestions = self.error_recovery.generate_error_suggestions(
            ErrorType.MISSING_DATA, request, mock_context
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any(
            "дата рождения" in suggestion.lower() for suggestion in suggestions
        )

    def test_generate_error_suggestions_personalized(self):
        """Test generation of personalized error suggestions."""
        request = self.create_mock_request("мой гороскоп")
        mock_context = MagicMock()
        mock_context.preferences = {
            "zodiac_sign": "leo",
            "favorite_topic": "love",
        }

        suggestions = self.error_recovery.generate_error_suggestions(
            ErrorType.MISSING_DATA, request, mock_context
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should include personalized suggestions based on user preferences

    @pytest.mark.asyncio
    async def test_log_error(self):
        """Test error logging functionality."""
        error = ValueError("Test error")
        request = self.create_mock_request("test command")
        error_type = ErrorType.VALIDATION_ERROR
        severity = ErrorSeverity.MEDIUM

        # Should not raise any exceptions
        await self.error_recovery.log_error(
            error, request, error_type, severity
        )
        assert True  # If we get here, logging worked

    def test_is_recoverable_error(self):
        """Test recoverable error detection."""
        # Recoverable errors
        assert self.error_recovery.is_recoverable_error(
            ErrorType.VALIDATION_ERROR, ErrorSeverity.MEDIUM
        )
        assert self.error_recovery.is_recoverable_error(
            ErrorType.MISSING_DATA, ErrorSeverity.LOW
        )

        # Non-recoverable errors
        assert not self.error_recovery.is_recoverable_error(
            ErrorType.SYSTEM_ERROR, ErrorSeverity.CRITICAL
        )

    def test_get_fallback_content(self):
        """Test fallback content generation."""
        request = self.create_mock_request("мой гороскоп")

        content = self.error_recovery.get_fallback_content(request)

        assert isinstance(content, str)
        assert len(content) > 0
        assert "извинения" in content.lower() or "sorry" in content.lower()

    def test_should_retry_operation(self):
        """Test retry operation decision."""
        # Should retry for temporary errors
        assert self.error_recovery.should_retry_operation(
            ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM, attempt_count=1
        )

        # Should not retry after too many attempts
        assert not self.error_recovery.should_retry_operation(
            ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM, attempt_count=5
        )

        # Should not retry critical errors
        assert not self.error_recovery.should_retry_operation(
            ErrorType.SYSTEM_ERROR, ErrorSeverity.CRITICAL, attempt_count=1
        )

    @pytest.mark.asyncio
    async def test_attempt_recovery(self):
        """Test recovery attempt functionality."""
        error = ValueError("Invalid input")
        request = self.create_mock_request("неправильная команда")
        mock_context = MagicMock()

        # Mock successful recovery
        with patch.object(self.error_recovery, "handle_error") as mock_handle:
            mock_response = MagicMock()
            mock_handle.return_value = mock_response

            result = await self.error_recovery.attempt_recovery(
                error, request, mock_context
            )

            assert result == mock_response
            mock_handle.assert_called_once_with(error, request, mock_context)

    def test_get_error_message_localization(self):
        """Test error message localization."""
        error_type = ErrorType.VALIDATION_ERROR

        # Russian localization
        message_ru = self.error_recovery.get_localized_error_message(
            error_type, "ru"
        )
        assert isinstance(message_ru, str)
        assert len(message_ru) > 0

        # English fallback
        message_en = self.error_recovery.get_localized_error_message(
            error_type, "en"
        )
        assert isinstance(message_en, str)
        assert len(message_en) > 0
