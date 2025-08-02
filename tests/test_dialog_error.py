"""
Tests for dialog error classes.
"""
import pytest

from app.services.dialog_error import (
    DialogError,
    ValidationError,
    DataMissingError,
    CalculationError,
    ExternalServiceError,
    AmbiguousIntentError,
    UserInputUnclearError,
    SystemOverloadError,
    PermissionDeniedError
)
from app.services.error_recovery import ErrorType


@pytest.mark.unit
class TestDialogError:
    """Tests for base DialogError class."""
    
    def test_dialog_error_basic_init(self):
        """Test basic DialogError initialization."""
        error = DialogError(
            error_type=ErrorType.UNKNOWN_ERROR,
            message="Test error message"
        )
        
        assert error.error_type == ErrorType.UNKNOWN_ERROR
        assert str(error) == "Test error message"
        assert error.context == {}
        assert error.user_id is None
        assert error.session_id is None
    
    def test_dialog_error_full_init(self):
        """Test DialogError with all parameters."""
        context = {"key": "value", "data": 123}
        error = DialogError(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            context=context,
            user_id="test_user",
            session_id="test_session"
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert str(error) == "Validation failed"
        assert error.context == context
        assert error.user_id == "test_user"
        assert error.session_id == "test_session"
    
    def test_dialog_error_inheritance(self):
        """Test that DialogError inherits from Exception."""
        error = DialogError(ErrorType.UNKNOWN_ERROR, "Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, DialogError)
    
    def test_dialog_error_none_context(self):
        """Test DialogError with None context."""
        error = DialogError(
            error_type=ErrorType.DATA_MISSING,
            message="No data",
            context=None
        )
        
        assert error.context == {}  # Should default to empty dict


@pytest.mark.unit
class TestValidationError:
    """Tests for ValidationError class."""
    
    def test_validation_error_basic(self):
        """Test basic ValidationError initialization."""
        error = ValidationError("Invalid input format")
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert str(error) == "Invalid input format"
        assert error.context == {}
        assert error.user_id is None
        assert error.session_id is None
    
    def test_validation_error_with_context(self):
        """Test ValidationError with additional context."""
        context = {"field": "birth_date", "value": "invalid_date"}
        error = ValidationError(
            "Date format invalid",
            context=context,
            user_id="user123",
            session_id="session456"
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert str(error) == "Date format invalid"
        assert error.context == context
        assert error.user_id == "user123"
        assert error.session_id == "session456"
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inheritance."""
        error = ValidationError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, ValidationError)
        assert isinstance(error, Exception)


@pytest.mark.unit
class TestDataMissingError:
    """Tests for DataMissingError class."""
    
    def test_data_missing_error_basic(self):
        """Test basic DataMissingError initialization."""
        error = DataMissingError("Birth date required")
        
        assert error.error_type == ErrorType.DATA_MISSING
        assert str(error) == "Birth date required"
        assert error.context == {}
    
    def test_data_missing_error_with_context(self):
        """Test DataMissingError with context."""
        context = {"required_fields": ["birth_date", "birth_time"]}
        error = DataMissingError(
            "Missing required data",
            context=context,
            user_id="user789"
        )
        
        assert error.error_type == ErrorType.DATA_MISSING
        assert error.context == context
        assert error.user_id == "user789"
    
    def test_data_missing_error_inheritance(self):
        """Test DataMissingError inheritance."""
        error = DataMissingError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, DataMissingError)


@pytest.mark.unit
class TestCalculationError:
    """Tests for CalculationError class."""
    
    def test_calculation_error_basic(self):
        """Test basic CalculationError initialization."""
        error = CalculationError("Ephemeris calculation failed")
        
        assert error.error_type == ErrorType.CALCULATION_ERROR
        assert str(error) == "Ephemeris calculation failed"
    
    def test_calculation_error_with_context(self):
        """Test CalculationError with context."""
        context = {
            "calculation_type": "natal_chart",
            "julian_day": 2451545.0,
            "error_details": "Invalid coordinates"
        }
        error = CalculationError(
            "Astronomical calculation error",
            context=context,
            user_id="calc_user",
            session_id="calc_session"
        )
        
        assert error.error_type == ErrorType.CALCULATION_ERROR
        assert error.context["calculation_type"] == "natal_chart"
        assert error.context["julian_day"] == 2451545.0
    
    def test_calculation_error_inheritance(self):
        """Test CalculationError inheritance."""
        error = CalculationError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, CalculationError)


@pytest.mark.unit
class TestExternalServiceError:
    """Tests for ExternalServiceError class."""
    
    def test_external_service_error_basic(self):
        """Test basic ExternalServiceError initialization."""
        error = ExternalServiceError("Database connection failed")
        
        assert error.error_type == ErrorType.EXTERNAL_SERVICE_ERROR
        assert str(error) == "Database connection failed"
    
    def test_external_service_error_with_context(self):
        """Test ExternalServiceError with service details."""
        context = {
            "service": "postgresql",
            "host": "localhost",
            "port": 5432,
            "timeout": 30,
            "retry_count": 3
        }
        error = ExternalServiceError(
            "Service unavailable",
            context=context,
            user_id="ext_user"
        )
        
        assert error.error_type == ErrorType.EXTERNAL_SERVICE_ERROR
        assert error.context["service"] == "postgresql"
        assert error.context["retry_count"] == 3
    
    def test_external_service_error_inheritance(self):
        """Test ExternalServiceError inheritance."""
        error = ExternalServiceError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, ExternalServiceError)


@pytest.mark.unit
class TestAmbiguousIntentError:
    """Tests for AmbiguousIntentError class."""
    
    def test_ambiguous_intent_error_basic(self):
        """Test basic AmbiguousIntentError initialization."""
        error = AmbiguousIntentError("Multiple intents detected")
        
        assert error.error_type == ErrorType.INTENT_AMBIGUOUS
        assert str(error) == "Multiple intents detected"
    
    def test_ambiguous_intent_error_with_context(self):
        """Test AmbiguousIntentError with intent details."""
        context = {
            "possible_intents": ["horoscope", "compatibility"],
            "confidence_scores": [0.7, 0.65],
            "user_input": "расскажи про совместимость моего гороскопа"
        }
        error = AmbiguousIntentError(
            "Cannot determine user intent",
            context=context,
            user_id="intent_user",
            session_id="intent_session"
        )
        
        assert error.error_type == ErrorType.INTENT_AMBIGUOUS
        assert len(error.context["possible_intents"]) == 2
        assert "horoscope" in error.context["possible_intents"]
        assert "compatibility" in error.context["possible_intents"]
    
    def test_ambiguous_intent_error_inheritance(self):
        """Test AmbiguousIntentError inheritance."""
        error = AmbiguousIntentError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, AmbiguousIntentError)


@pytest.mark.unit
class TestUserInputUnclearError:
    """Tests for UserInputUnclearError class."""
    
    def test_user_input_unclear_error_basic(self):
        """Test basic UserInputUnclearError initialization."""
        error = UserInputUnclearError("User input not understood")
        
        assert error.error_type == ErrorType.USER_INPUT_UNCLEAR
        assert str(error) == "User input not understood"
    
    def test_user_input_unclear_error_with_context(self):
        """Test UserInputUnclearError with input details."""
        context = {
            "raw_input": "вчерашний завтрашний гороскоп",
            "processed_tokens": ["вчерашний", "завтрашний", "гороскоп"],
            "confidence": 0.2,
            "suggestions": ["вчерашний гороскоп", "завтрашний гороскоп"]
        }
        error = UserInputUnclearError(
            "Conflicting temporal indicators",
            context=context,
            user_id="unclear_user"
        )
        
        assert error.error_type == ErrorType.USER_INPUT_UNCLEAR
        assert error.context["confidence"] == 0.2
        assert len(error.context["suggestions"]) == 2
    
    def test_user_input_unclear_error_inheritance(self):
        """Test UserInputUnclearError inheritance."""
        error = UserInputUnclearError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, UserInputUnclearError)


@pytest.mark.unit
class TestSystemOverloadError:
    """Tests for SystemOverloadError class."""
    
    def test_system_overload_error_basic(self):
        """Test basic SystemOverloadError initialization."""
        error = SystemOverloadError("System overloaded")
        
        assert error.error_type == ErrorType.SYSTEM_OVERLOAD
        assert str(error) == "System overloaded"
    
    def test_system_overload_error_with_context(self):
        """Test SystemOverloadError with system metrics."""
        context = {
            "cpu_usage": 95.2,
            "memory_usage": 89.7,
            "active_sessions": 1500,
            "queue_length": 250,
            "response_time": 15.5
        }
        error = SystemOverloadError(
            "High resource utilization",
            context=context,
            session_id="overload_session"
        )
        
        assert error.error_type == ErrorType.SYSTEM_OVERLOAD
        assert error.context["cpu_usage"] == 95.2
        assert error.context["active_sessions"] == 1500
    
    def test_system_overload_error_inheritance(self):
        """Test SystemOverloadError inheritance."""
        error = SystemOverloadError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, SystemOverloadError)


@pytest.mark.unit
class TestPermissionDeniedError:
    """Tests for PermissionDeniedError class."""
    
    def test_permission_denied_error_basic(self):
        """Test basic PermissionDeniedError initialization."""
        error = PermissionDeniedError("Access denied")
        
        assert error.error_type == ErrorType.PERMISSION_DENIED
        assert str(error) == "Access denied"
    
    def test_permission_denied_error_with_context(self):
        """Test PermissionDeniedError with access details."""
        context = {
            "resource": "user_birth_data",
            "requested_action": "read",
            "user_role": "guest",
            "required_role": "authenticated",
            "gdpr_consent": False
        }
        error = PermissionDeniedError(
            "Insufficient permissions",
            context=context,
            user_id="denied_user",
            session_id="denied_session"
        )
        
        assert error.error_type == ErrorType.PERMISSION_DENIED
        assert error.context["resource"] == "user_birth_data"
        assert error.context["gdpr_consent"] is False
    
    def test_permission_denied_error_inheritance(self):
        """Test PermissionDeniedError inheritance."""
        error = PermissionDeniedError("Test")
        
        assert isinstance(error, DialogError)
        assert isinstance(error, PermissionDeniedError)


@pytest.mark.unit
class TestErrorHierarchy:
    """Tests for error class hierarchy and relationships."""
    
    def test_all_error_types_inherit_dialog_error(self):
        """Test that all specific error types inherit from DialogError."""
        error_classes = [
            ValidationError,
            DataMissingError,
            CalculationError,
            ExternalServiceError,
            AmbiguousIntentError,
            UserInputUnclearError,
            SystemOverloadError,
            PermissionDeniedError
        ]
        
        for error_class in error_classes:
            error = error_class("Test message")
            assert isinstance(error, DialogError)
            assert isinstance(error, Exception)
    
    def test_error_type_mapping(self):
        """Test that each error class maps to correct ErrorType."""
        mappings = [
            (ValidationError, ErrorType.VALIDATION_ERROR),
            (DataMissingError, ErrorType.DATA_MISSING),
            (CalculationError, ErrorType.CALCULATION_ERROR),
            (ExternalServiceError, ErrorType.EXTERNAL_SERVICE_ERROR),
            (AmbiguousIntentError, ErrorType.INTENT_AMBIGUOUS),
            (UserInputUnclearError, ErrorType.USER_INPUT_UNCLEAR),
            (SystemOverloadError, ErrorType.SYSTEM_OVERLOAD),
            (PermissionDeniedError, ErrorType.PERMISSION_DENIED)
        ]
        
        for error_class, expected_type in mappings:
            error = error_class("Test message")
            assert error.error_type == expected_type
    
    def test_error_context_preservation(self):
        """Test that context is preserved across all error types."""
        context = {"test_key": "test_value", "number": 42}
        
        error_classes = [
            ValidationError,
            DataMissingError,
            CalculationError,
            ExternalServiceError,
            AmbiguousIntentError,
            UserInputUnclearError,
            SystemOverloadError,
            PermissionDeniedError
        ]
        
        for error_class in error_classes:
            error = error_class("Test", context=context)
            assert error.context == context
            assert error.context["test_key"] == "test_value"
            assert error.context["number"] == 42
    
    def test_error_user_session_preservation(self):
        """Test that user_id and session_id are preserved across all error types."""
        user_id = "test_user_123"
        session_id = "test_session_456"
        
        error_classes = [
            ValidationError,
            DataMissingError,
            CalculationError,
            ExternalServiceError,
            AmbiguousIntentError,
            UserInputUnclearError,
            SystemOverloadError,
            PermissionDeniedError
        ]
        
        for error_class in error_classes:
            error = error_class(
                "Test",
                user_id=user_id,
                session_id=session_id
            )
            assert error.user_id == user_id
            assert error.session_id == session_id


@pytest.mark.unit
class TestErrorUsageScenarios:
    """Tests for realistic error usage scenarios."""
    
    def test_validation_error_birth_date_scenario(self):
        """Test ValidationError for invalid birth date scenario."""
        error = ValidationError(
            "Invalid birth date format",
            context={
                "input": "32/15/1990",
                "expected_format": "DD.MM.YYYY",
                "field": "birth_date"
            },
            user_id="user_abc",
            session_id="session_xyz"
        )
        
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert "Invalid birth date format" in str(error)
        assert error.context["input"] == "32/15/1990"
    
    def test_calculation_error_ephemeris_scenario(self):
        """Test CalculationError for ephemeris calculation failure."""
        error = CalculationError(
            "Swiss Ephemeris calculation failed",
            context={
                "julian_day": 2451545.0,
                "coordinates": {"lat": 55.7558, "lon": 37.6176},
                "planet": "Mars",
                "error_code": -1
            },
            user_id="astro_user"
        )
        
        assert error.error_type == ErrorType.CALCULATION_ERROR
        assert error.context["planet"] == "Mars"
        assert error.context["error_code"] == -1
    
    def test_external_service_error_db_scenario(self):
        """Test ExternalServiceError for database failure."""
        error = ExternalServiceError(
            "Database connection timeout",
            context={
                "service": "PostgreSQL",
                "operation": "SELECT user_data",
                "timeout_seconds": 30,
                "retry_attempts": 3
            },
            user_id="db_user",
            session_id="db_session"
        )
        
        assert error.error_type == ErrorType.EXTERNAL_SERVICE_ERROR
        assert error.context["operation"] == "SELECT user_data"
        assert error.context["retry_attempts"] == 3
    
    def test_permission_denied_gdpr_scenario(self):
        """Test PermissionDeniedError for GDPR compliance."""
        error = PermissionDeniedError(
            "GDPR consent required for birth data access",
            context={
                "requested_data": ["birth_date", "birth_location"],
                "consent_status": "not_given",
                "data_category": "personal_sensitive"
            },
            user_id="privacy_user"
        )
        
        assert error.error_type == ErrorType.PERMISSION_DENIED
        assert "GDPR" in str(error)
        assert error.context["consent_status"] == "not_given"