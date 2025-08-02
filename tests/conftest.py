"""
Pytest configuration and shared fixtures.
"""
import asyncio
import os
import secrets
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# Set test environment variables
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Generate secure random keys for testing
os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)
os.environ["ENCRYPTION_KEY"] = secrets.token_urlsafe(32)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_database():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def mock_yandex_request():
    """Create a mock Yandex request."""
    from app.models.yandex_models import (
        YandexRequestData,
        YandexRequestModel,
        YandexSession,
    )

    return YandexRequestModel(
        meta=MagicMock(),
        request=YandexRequestData(
            command="тест",
            original_utterance="тест",
            type="SimpleUtterance",
            markup=MagicMock(),
            payload={},
        ),
        session=YandexSession(
            message_id=1,
            session_id="test_session",
            skill_id="test_skill",
            user_id="test_user",
            user={"user_id": "test_user"},
            application=MagicMock(),
            new=False,
        ),
        version="1.0",
    )


@pytest.fixture
def mock_user_context():
    """Mock user conversation context."""
    context = MagicMock()
    context.user_id = "test_user"
    context.personalization_level = 50
    context.conversation_count = 5
    context.preferences = {"zodiac_sign": "leo"}
    context.last_interaction = datetime.now()
    return context


@pytest.fixture
def sample_birth_data():
    """Sample birth data for testing."""
    return {
        "birth_date": datetime(1990, 5, 15, 14, 30),
        "birth_location": {
            "latitude": 55.7558,
            "longitude": 37.6176,
            "name": "Moscow",
        },
    }


@pytest.fixture
def sample_horoscope_data():
    """Sample horoscope data for testing."""
    return {
        "prediction": "Отличный день для новых начинаний!",
        "love": "В отношениях ожидается гармония",
        "career": "Возможны интересные предложения по работе",
        "health": "Уделите внимание физической активности",
        "finances": "Избегайте крупных трат",
        "lucky_numbers": [7, 14, 21],
        "lucky_color": "синий",
        "energy_level": 75,
    }


@pytest.fixture
def sample_compatibility_data():
    """Sample compatibility data for testing."""
    return {
        "score": 85,
        "description": "Отличная совместимость!",
        "strengths": ["понимание", "гармония", "общие интересы"],
        "challenges": ["разные темпераменты", "различные подходы к жизни"],
        "advice": "Больше общайтесь и учитесь идти на компромиссы",
    }


@pytest.fixture
def sample_natal_chart():
    """Sample natal chart data for testing."""
    return {
        "planets": {
            "sun": {"sign": "taurus", "house": 2, "longitude": 54.5},
            "moon": {"sign": "scorpio", "house": 8, "longitude": 234.5},
            "mercury": {"sign": "gemini", "house": 3, "longitude": 64.5},
        },
        "houses": {
            "1": {"cusp": 0, "sign": "aries"},
            "2": {"cusp": 30, "sign": "taurus"},
            "3": {"cusp": 60, "sign": "gemini"},
        },
        "aspects": [
            {
                "planet1": "sun",
                "planet2": "moon",
                "type": "opposition",
                "orb": 1.2,
            },
            {
                "planet1": "sun",
                "planet2": "mercury",
                "type": "conjunction",
                "orb": 0.8,
            },
        ],
        "chart_signature": {
            "dominant_element": "earth",
            "dominant_quality": "fixed",
        },
    }


@pytest.fixture
def mock_encryption_service():
    """Mock encryption service."""
    from unittest.mock import MagicMock

    service = MagicMock()
    service.encrypt.return_value = b"encrypted_data"
    service.decrypt.return_value = "decrypted_data"
    service.encrypt_dict.return_value = {"encrypted": "data"}
    service.decrypt_dict.return_value = {"original": "data"}
    return service


@pytest.fixture
def mock_astrology_calculator():
    """Mock astrology calculator."""
    from app.models.yandex_models import YandexZodiacSign

    calculator = MagicMock()
    calculator.get_zodiac_sign_by_date.return_value = YandexZodiacSign.LEO
    calculator.calculate_compatibility.return_value = {
        "score": 85,
        "description": "Отличная совместимость!",
    }
    calculator.calculate_moon_phase.return_value = {
        "phase": "Full Moon",
        "illumination": 100,
        "energy_level": 90,
    }
    return calculator


@pytest.fixture
def mock_horoscope_generator():
    """Mock horoscope generator."""
    generator = MagicMock()
    generator.generate_horoscope.return_value = {
        "prediction": "Отличный день для новых начинаний!",
        "lucky_numbers": [7, 14, 21],
        "lucky_color": "синий",
    }
    generator.generate_personal_horoscope.return_value = {
        "prediction": "Персональный прогноз",
        "energy_level": 75,
    }
    return generator


@pytest.fixture
def mock_response_formatter():
    """Mock response formatter."""
    formatter = MagicMock()
    formatter.format_greeting_response.return_value = MagicMock()
    formatter.format_horoscope_response.return_value = MagicMock()
    formatter.format_compatibility_response.return_value = MagicMock()
    formatter.format_error_response.return_value = MagicMock()
    return formatter


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test."""
    # Import all services that have caches
    try:
        from app.services.intent_recognition import IntentRecognizer

        # Clear intent recognizer caches if they exist
        recognizer = IntentRecognizer()
        recognizer.clear_cache()
    except (ImportError, AttributeError):
        pass

    yield

    # Clear caches after test
    try:
        from app.services.intent_recognition import IntentRecognizer

        recognizer = IntentRecognizer()
        recognizer.clear_cache()
    except (ImportError, AttributeError):
        pass


@pytest.fixture(scope="session")
def test_config():
    """Test configuration."""
    return {
        "database_url": "sqlite:///:memory:",
        "secret_key": secrets.token_urlsafe(32),
        "encryption_key": secrets.token_urlsafe(32),
        "environment": "testing",
    }


# Pytest markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security
pytest.mark.slow = pytest.mark.slow
