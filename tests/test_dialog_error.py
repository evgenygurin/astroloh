"""
Tests for dialog error handling.
"""
import pytest

from app.services.dialog_error import (
    CalculationError,
    DataMissingError,
    DialogError,
    ExternalServiceError,
    ValidationError,
)
from app.services.error_recovery import ErrorType


class TestDialogError:
    """Test dialog error classes."""

    def test_dialog_error_initialization(self):
        """Test DialogError initialization."""
        error = DialogError(ErrorType.VALIDATION_ERROR, "Test error message")

        assert str(error) == "Test error message"
        assert error.error_type == ErrorType.VALIDATION_ERROR

    def test_dialog_error_with_context(self):
        """Test DialogError with context and user info."""
        context = {"field": "birth_date"}
        error = DialogError(
            ErrorType.DATA_MISSING,
            "Test error",
            context=context,
            user_id="test_user",
            session_id="test_session",
        )

        assert str(error) == "Test error"
        assert error.error_type == ErrorType.DATA_MISSING
        assert error.context == context
        assert error.user_id == "test_user"
        assert error.session_id == "test_session"

    def test_validation_error_initialization(self):
        """Test ValidationError initialization."""
        error = ValidationError("Invalid input")

        assert str(error) == "Invalid input"
        assert error.error_type == ErrorType.VALIDATION_ERROR

    def test_data_missing_error_initialization(self):
        """Test DataMissingError initialization."""
        error = DataMissingError("Birth date required")

        assert str(error) == "Birth date required"
        assert error.error_type == ErrorType.DATA_MISSING

    def test_calculation_error_initialization(self):
        """Test CalculationError initialization."""
        error = CalculationError("Calculation failed")

        assert str(error) == "Calculation failed"
        assert error.error_type == ErrorType.CALCULATION_ERROR

    def test_external_service_error_initialization(self):
        """Test ExternalServiceError initialization."""
        error = ExternalServiceError("Service unavailable")

        assert str(error) == "Service unavailable"
        assert error.error_type == ErrorType.EXTERNAL_SERVICE_ERROR

    def test_error_inheritance(self):
        """Test that all errors inherit from Exception."""
        assert issubclass(DialogError, Exception)
        assert issubclass(ValidationError, DialogError)
        assert issubclass(DataMissingError, DialogError)
        assert issubclass(CalculationError, DialogError)
        assert issubclass(ExternalServiceError, DialogError)

    def test_error_can_be_raised(self):
        """Test that errors can be raised and caught."""
        with pytest.raises(DialogError) as exc_info:
            raise DialogError(ErrorType.VALIDATION_ERROR, "Test error")

        assert str(exc_info.value) == "Test error"

    def test_validation_error_can_be_raised(self):
        """Test ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid date")

        error = exc_info.value
        assert str(error) == "Invalid date"

    def test_data_missing_error_can_be_raised(self):
        """Test DataMissingError can be raised and caught."""
        with pytest.raises(DataMissingError) as exc_info:
            raise DataMissingError("Missing zodiac sign")

        error = exc_info.value
        assert str(error) == "Missing zodiac sign"

    def test_calculation_error_can_be_raised(self):
        """Test CalculationError can be raised and caught."""
        with pytest.raises(CalculationError) as exc_info:
            raise CalculationError("Failed to calculate")

        error = exc_info.value
        assert str(error) == "Failed to calculate"

    def test_external_service_error_can_be_raised(self):
        """Test ExternalServiceError can be raised and caught."""
        with pytest.raises(ExternalServiceError) as exc_info:
            raise ExternalServiceError("Service down")

        error = exc_info.value
        assert str(error) == "Service down"

    def test_error_attributes_are_accessible(self):
        """Test that error attributes are properly accessible."""
        validation_error = ValidationError("Invalid input")
        data_error = DataMissingError("Missing data")
        calc_error = CalculationError("Calc failed")
        service_error = ExternalServiceError("Service failed")

        # Check common attributes are accessible
        assert hasattr(validation_error, "error_type")
        assert hasattr(data_error, "error_type")
        assert hasattr(calc_error, "error_type")
        assert hasattr(service_error, "error_type")

        # Check error types
        assert validation_error.error_type == ErrorType.VALIDATION_ERROR
        assert data_error.error_type == ErrorType.DATA_MISSING
        assert calc_error.error_type == ErrorType.CALCULATION_ERROR
        assert service_error.error_type == ErrorType.EXTERNAL_SERVICE_ERROR

    def test_error_types_are_correct(self):
        """Test that error types are set correctly."""
        assert (
            DialogError(ErrorType.VALIDATION_ERROR, "msg").error_type
            == ErrorType.VALIDATION_ERROR
        )
        assert ValidationError("msg").error_type == ErrorType.VALIDATION_ERROR
        assert DataMissingError("msg").error_type == ErrorType.DATA_MISSING
        assert (
            CalculationError("msg").error_type == ErrorType.CALCULATION_ERROR
        )
        assert (
            ExternalServiceError("msg").error_type
            == ErrorType.EXTERNAL_SERVICE_ERROR
        )

    def test_empty_message_handling(self):
        """Test error handling with empty messages."""
        error = DialogError(ErrorType.VALIDATION_ERROR, "")
        assert str(error) == ""

    def test_context_handling(self):
        """Test error handling with context."""
        context = {"field": "test_field", "value": "invalid"}
        error = DialogError(
            ErrorType.VALIDATION_ERROR, "Validation failed", context=context
        )
        assert error.context == context
        assert error.context["field"] == "test_field"
        assert error.context["value"] == "invalid"
