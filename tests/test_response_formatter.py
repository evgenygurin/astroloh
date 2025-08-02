"""
Tests for response formatter functionality.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.response_formatter import ResponseFormatter
from app.models.yandex_models import (
    YandexResponse, YandexButton, YandexZodiacSign
)


@pytest.mark.unit
class TestResponseFormatter:
    """Tests for response formatter."""
    
    def setup_method(self):
        """Setup before each test."""
        self.formatter = ResponseFormatter()
    
    def test_init(self):
        """Test formatter initialization."""
        assert isinstance(self.formatter.welcome_messages, list)
        assert len(self.formatter.welcome_messages) > 0
        assert isinstance(self.formatter.help_buttons, list)
        assert len(self.formatter.help_buttons) > 0
        
        for button in self.formatter.help_buttons:
            assert isinstance(button, YandexButton)
            assert button.title
            assert button.payload
    
    def test_format_welcome_response_new_user(self):
        """Test welcome response for new user."""
        response = self.formatter.format_welcome_response(is_returning_user=False)
        
        assert isinstance(response, YandexResponse)
        assert response.text == self.formatter.welcome_messages[0]
        assert response.tts
        assert response.buttons == self.formatter.help_buttons
        assert response.end_session is False
    
    def test_format_welcome_response_returning_user(self):
        """Test welcome response for returning user."""
        response = self.formatter.format_welcome_response(is_returning_user=True)
        
        assert isinstance(response, YandexResponse)
        assert "возвращением" in response.text.lower()
        assert response.tts
        assert response.buttons == self.formatter.help_buttons
        assert response.end_session is False
    
    def test_format_personalized_birth_date_request_new_user(self):
        """Test birth date request for new user."""
        response = self.formatter.format_personalized_birth_date_request(
            user_returning=False
        )
        
        assert isinstance(response, YandexResponse)
        assert "персонального гороскопа" in response.text
        assert response.tts
        assert len(response.buttons) >= 2
        assert response.end_session is False
        
        # Check for help and example buttons
        button_titles = [btn.title for btn in response.buttons]
        assert any("помощь" in title.lower() for title in button_titles)
        assert any("пример" in title.lower() for title in button_titles)
    
    def test_format_personalized_birth_date_request_returning_user(self):
        """Test birth date request for returning user."""
        response = self.formatter.format_personalized_birth_date_request(
            user_returning=True
        )
        
        assert isinstance(response, YandexResponse)
        assert "напомните" in response.text.lower()
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_personalized_birth_date_request_with_suggestions(self):
        """Test birth date request with suggestions."""
        suggestions = ["15 марта", "Сегодня"]
        response = self.formatter.format_personalized_birth_date_request(
            suggestions=suggestions
        )
        
        assert isinstance(response, YandexResponse)
        assert len(response.buttons) >= 4  # Help, example + 2 suggestions
        
        # Check that suggestions were added as buttons
        button_titles = [btn.title for btn in response.buttons]
        for suggestion in suggestions:
            assert suggestion in button_titles
    
    def test_format_personalized_advice_response_positive_sentiment(self):
        """Test advice response with positive sentiment."""
        response = self.formatter.format_personalized_advice_response(
            sentiment="positive"
        )
        
        assert isinstance(response, YandexResponse)
        assert "благоволят" in response.text
        assert response.tts
        assert len(response.buttons) >= 2
        assert response.end_session is False
    
    def test_format_personalized_advice_response_negative_sentiment(self):
        """Test advice response with negative sentiment."""
        response = self.formatter.format_personalized_advice_response(
            sentiment="negative"
        )
        
        assert isinstance(response, YandexResponse)
        assert "трудности временны" in response.text.lower()
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_personalized_advice_response_with_topics(self):
        """Test advice response with preferred topics."""
        preferred_topics = ["horoscope"]
        response = self.formatter.format_personalized_advice_response(
            preferred_topics=preferred_topics
        )
        
        assert isinstance(response, YandexResponse)
        assert "знаками судьбы" in response.text
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_personalized_advice_response_with_suggestions(self):
        """Test advice response with suggestions."""
        suggestions = ["Натальная карта", "Лунный календарь"]
        response = self.formatter.format_personalized_advice_response(
            suggestions=suggestions
        )
        
        assert isinstance(response, YandexResponse)
        assert response.buttons
        
        # Check that suggestions were added
        button_titles = [btn.title for btn in response.buttons]
        for suggestion in suggestions:
            assert suggestion in button_titles
    
    def test_format_clarification_response_no_context(self):
        """Test clarification response without context."""
        response = self.formatter.format_clarification_response()
        
        assert isinstance(response, YandexResponse)
        assert "не поняла" in response.text
        assert response.tts
        assert len(response.buttons) == 4  # Default menu buttons
        assert response.end_session is False
        
        # Check for standard menu buttons
        button_titles = [btn.title for btn in response.buttons]
        assert "гороскоп" in " ".join(button_titles).lower()
        assert "совместимость" in " ".join(button_titles).lower()
    
    def test_format_clarification_response_with_context(self):
        """Test clarification response with recent context."""
        recent_context = ["предыдущий запрос"]
        response = self.formatter.format_clarification_response(
            recent_context=recent_context
        )
        
        assert isinstance(response, YandexResponse)
        assert "не совсем поняла" in response.text
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_clarification_response_with_suggestions(self):
        """Test clarification response with personalized suggestions."""
        suggestions = ["Мой гороскоп", "Совет дня", "Помощь", "Выход"]
        response = self.formatter.format_clarification_response(
            suggestions=suggestions
        )
        
        assert isinstance(response, YandexResponse)
        assert len(response.buttons) <= 4  # Max 4 buttons
        
        # Check that suggestions replaced standard buttons
        button_titles = [btn.title for btn in response.buttons]
        for suggestion in suggestions:
            assert suggestion in button_titles
    
    def test_format_error_recovery_response(self):
        """Test error recovery response."""
        error_suggestions = ["Попробовать снова", "Помощь"]
        response = self.formatter.format_error_recovery_response(error_suggestions)
        
        assert isinstance(response, YandexResponse)
        assert "неполадка" in response.text
        assert response.tts
        assert len(response.buttons) <= 4
        assert response.end_session is False
        
        # Check that suggestions are included
        button_titles = [btn.title for btn in response.buttons]
        for suggestion in error_suggestions:
            assert suggestion in button_titles
    
    def test_format_error_recovery_response_few_suggestions(self):
        """Test error recovery response with few suggestions."""
        error_suggestions = ["Повторить"]  # Only one suggestion
        response = self.formatter.format_error_recovery_response(error_suggestions)
        
        assert isinstance(response, YandexResponse)
        # Should add default buttons when few suggestions
        assert len(response.buttons) >= 3
        
        button_titles = [btn.title for btn in response.buttons]
        assert "Повторить" in button_titles
        assert any("начать" in title.lower() for title in button_titles)
        assert any("помощь" in title.lower() for title in button_titles)
    
    def test_format_horoscope_request_response_no_birth_date(self):
        """Test horoscope request without birth date."""
        response = self.formatter.format_horoscope_request_response(
            has_birth_date=False
        )
        
        assert isinstance(response, YandexResponse)
        assert "дата рождения" in response.text
        assert response.tts
        assert response.buttons is None  # No buttons when no birth date
        assert response.end_session is False
    
    def test_format_horoscope_request_response_has_birth_date(self):
        """Test horoscope request with birth date."""
        response = self.formatter.format_horoscope_request_response(
            has_birth_date=True
        )
        
        assert isinstance(response, YandexResponse)
        assert "время рождения" in response.text
        assert response.tts
        assert response.buttons  # Should have buttons when has birth date
        assert response.end_session is False
        
        button_titles = [btn.title for btn in response.buttons]
        assert any("не знаю" in title.lower() for title in button_titles)
    
    def test_format_compatibility_request_response_step1(self):
        """Test compatibility request response step 1."""
        response = self.formatter.format_compatibility_request_response(step=1)
        
        assert isinstance(response, YandexResponse)
        assert "ваш знак зодиака" in response.text
        assert response.tts
        assert response.buttons  # Should have zodiac sign buttons
        assert response.end_session is False
    
    def test_format_compatibility_request_response_step2(self):
        """Test compatibility request response step 2."""
        response = self.formatter.format_compatibility_request_response(step=2)
        
        assert isinstance(response, YandexResponse)
        assert "партнера" in response.text
        assert response.tts
        assert response.buttons  # Should have zodiac sign buttons
        assert response.end_session is False
    
    def test_format_horoscope_response_with_data(self):
        """Test horoscope response with personalized data."""
        horoscope_data = {
            "general_forecast": "Отличный день для новых дел",
            "spheres": {
                "love": {"rating": 4, "forecast": "Гармония в отношениях"},
                "career": {"rating": 5, "forecast": "Успехи в работе"}
            },
            "energy_level": {"level": 80, "description": "Высокая энергия"},
            "lucky_numbers": [7, 14, 21, 28],
            "lucky_colors": ["синий", "зелёный"]
        }
        
        response = self.formatter.format_horoscope_response(
            zodiac_sign=YandexZodiacSign.LEO,
            horoscope_data=horoscope_data,
            period="день"
        )
        
        assert isinstance(response, YandexResponse)
        assert "Персональный гороскоп" in response.text
        assert "Отличный день для новых дел" in response.text
        assert "💕 Любовь" in response.text
        assert "💼 Карьера" in response.text
        assert "Уровень энергии: 80%" in response.text
        assert "7, 14, 21, 28" in response.text
        assert "синий, зелёный" in response.text
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_horoscope_response_without_data(self):
        """Test horoscope response without personalized data."""
        response = self.formatter.format_horoscope_response(
            zodiac_sign=YandexZodiacSign.ARIES
        )
        
        assert isinstance(response, YandexResponse)
        assert "Гороскоп для Овен" in response.text
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_compatibility_response_with_data(self):
        """Test compatibility response with calculated data."""
        compatibility_data = {
            "total_score": 85,
            "description": "Отличная совместимость",
            "element1": "огонь",
            "element2": "воздух"
        }
        
        response = self.formatter.format_compatibility_response(
            sign1=YandexZodiacSign.LEO,
            sign2=YandexZodiacSign.GEMINI,
            compatibility_data=compatibility_data
        )
        
        assert isinstance(response, YandexResponse)
        assert "Совместимость Лев и Близнецы" in response.text
        assert "85/100" in response.text
        assert "огонь + воздух" in response.text
        assert "Прекрасная пара" in response.text  # High score message
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_compatibility_response_different_scores(self):
        """Test compatibility response with different score ranges."""
        test_cases = [
            (90, "Прекрасная пара"),
            (70, "Хорошая совместимость"),
            (50, "Умеренная совместимость"),
            (30, "Сложная совместимость")
        ]
        
        for score, expected_text in test_cases:
            compatibility_data = {
                "total_score": score,
                "description": "Тест",
                "element1": "огонь",
                "element2": "вода"
            }
            
            response = self.formatter.format_compatibility_response(
                sign1=YandexZodiacSign.LEO,
                sign2=YandexZodiacSign.CANCER,
                compatibility_data=compatibility_data
            )
            
            assert expected_text in response.text
    
    def test_format_compatibility_response_without_data(self):
        """Test compatibility response without calculated data."""
        response = self.formatter.format_compatibility_response(
            sign1=YandexZodiacSign.VIRGO,
            sign2=YandexZodiacSign.PISCES
        )
        
        assert isinstance(response, YandexResponse)
        assert "Совместимость Дева и Рыбы" in response.text
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_advice_response(self):
        """Test advice response."""
        with patch.object(self.formatter, '_generate_advice_text', return_value="Тестовый совет"):
            response = self.formatter.format_advice_response()
        
        assert isinstance(response, YandexResponse)
        assert "Астрологический совет дня" in response.text
        assert "Тестовый совет" in response.text
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_help_response(self):
        """Test help response."""
        response = self.formatter.format_help_response()
        
        assert isinstance(response, YandexResponse)
        assert "Я умею:" in response.text
        assert "гороскопы" in response.text
        assert "совместимость" in response.text
        assert response.tts
        assert response.buttons == self.formatter.help_buttons
        assert response.end_session is False
    
    def test_format_error_response_general(self):
        """Test general error response."""
        response = self.formatter.format_error_response()
        
        assert isinstance(response, YandexResponse)
        assert "произошла ошибка" in response.text.lower()
        assert response.tts == response.text
        assert response.buttons == self.formatter.help_buttons
        assert response.end_session is False
    
    def test_format_error_response_specific_types(self):
        """Test specific error response types."""
        error_types = {
            "invalid_date": "дату",
            "invalid_sign": "знак зодиака",
            "no_data": "недостаточно данных"
        }
        
        for error_type, expected_keyword in error_types.items():
            response = self.formatter.format_error_response(error_type=error_type)
            
            assert isinstance(response, YandexResponse)
            assert expected_keyword.lower() in response.text.lower()
            assert response.buttons == self.formatter.help_buttons
            assert response.end_session is False
    
    def test_format_goodbye_response(self):
        """Test goodbye response."""
        response = self.formatter.format_goodbye_response()
        
        assert isinstance(response, YandexResponse)
        assert "до свидания" in response.text.lower()
        assert "звёзды" in response.text
        assert response.tts == response.text
        assert response.end_session is True
    
    def test_format_natal_chart_request_response(self):
        """Test natal chart request response."""
        response = self.formatter.format_natal_chart_request_response()
        
        assert isinstance(response, YandexResponse)
        assert "натальной карты" in response.text
        assert "дата рождения" in response.text
        assert response.tts
        assert response.buttons is None
        assert response.end_session is False
    
    def test_format_natal_chart_response(self):
        """Test natal chart response."""
        natal_chart_data = {
            "interpretation": {
                "personality": {
                    "core_self": "Сильная личность",
                    "emotional_nature": "Глубокие эмоции"
                },
                "life_purpose": "Творческое самовыражение",
                "strengths": ["лидерство", "творчество", "интуиция"]
            },
            "chart_signature": {
                "dominant_element": "огонь",
                "dominant_quality": "кардинальное"
            }
        }
        
        response = self.formatter.format_natal_chart_response(natal_chart_data)
        
        assert isinstance(response, YandexResponse)
        assert "Ваша натальная карта" in response.text
        assert "Сильная личность" in response.text
        assert "Глубокие эмоции" in response.text
        assert "Творческое самовыражение" in response.text
        assert "огонь" in response.text
        assert "кардинальное" in response.text
        assert "лидерство" in response.text
        assert "творчество" in response.text
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_format_lunar_calendar_response(self):
        """Test lunar calendar response."""
        lunar_info = {
            "lunar_day": 15,
            "name": "День гармонии",
            "description": "Отличный день для медитации",
            "energy_level": "высокая",
            "moon_phase": {
                "phase_name": "Полнолуние",
                "illumination_percent": 100
            },
            "recommendations": [
                "Занимайтесь творчеством",
                "Проводите время с близкими",
                "Избегайте конфликтов"
            ]
        }
        
        response = self.formatter.format_lunar_calendar_response(lunar_info)
        
        assert isinstance(response, YandexResponse)
        assert "Лунный календарь" in response.text
        assert "15-й лунный день" in response.text
        assert "День гармонии" in response.text
        assert "Полнолуние (100%)" in response.text
        assert "высокая" in response.text
        assert "медитации" in response.text
        assert "Занимайтесь творчеством" in response.text
        assert "🌕" in response.text  # Full moon emoji
        assert response.tts
        assert response.buttons
        assert response.end_session is False
    
    def test_lunar_calendar_response_different_phases(self):
        """Test lunar calendar response with different moon phases."""
        phases = [
            ("Новолуние", "🌑"),
            ("Растущая Луна", "🌓"),
            ("Убывающая Луна", "🌗"),
            ("Полнолуние", "🌕")
        ]
        
        for phase_name, expected_emoji in phases:
            lunar_info = {
                "lunar_day": 1,
                "name": "Тест",
                "description": "Тест",
                "energy_level": "средняя",
                "moon_phase": {
                    "phase_name": phase_name,
                    "illumination_percent": 50
                },
                "recommendations": []
            }
            
            response = self.formatter.format_lunar_calendar_response(lunar_info)
            assert expected_emoji in response.text
    
    def test_get_zodiac_buttons(self):
        """Test zodiac buttons generation."""
        buttons = self.formatter._get_zodiac_buttons()
        
        assert isinstance(buttons, list)
        assert len(buttons) == 6  # Six zodiac signs shown
        
        for button in buttons:
            assert isinstance(button, YandexButton)
            assert button.title
            assert button.payload
            assert "sign" in button.payload
    
    def test_add_tts_pauses(self):
        """Test TTS pause addition."""
        text = "Привет! Как дела? Хорошо: отлично; супер."
        tts = self.formatter._add_tts_pauses(text)
        
        assert "! <pause=300ms>" in tts
        assert "? <pause=300ms>" in tts
        assert ": <pause=200ms>" in tts
        assert "; <pause=200ms>" in tts
        assert ". <pause=300ms>" in tts
    
    def test_generate_horoscope_text(self):
        """Test horoscope text generation."""
        # Test known sign
        text = self.formatter._generate_horoscope_text(
            YandexZodiacSign.ARIES, 
            "день"
        )
        assert "новых начинаний" in text
        
        # Test unknown sign (should return default)
        text = self.formatter._generate_horoscope_text(
            YandexZodiacSign.CANCER,  # Not in the predefined list
            "день"
        )
        assert "интуицию" in text
    
    def test_generate_compatibility_text(self):
        """Test compatibility text generation."""
        # Same element compatibility
        text = self.formatter._generate_compatibility_text(
            YandexZodiacSign.ARIES,
            YandexZodiacSign.LEO
        )
        assert "отличная совместимость" in text.lower()
        
        # Compatible elements (fire + air)
        text = self.formatter._generate_compatibility_text(
            YandexZodiacSign.ARIES,
            YandexZodiacSign.GEMINI
        )
        assert "хорошая совместимость" in text.lower()
        
        # Opposite elements (fire + water)
        text = self.formatter._generate_compatibility_text(
            YandexZodiacSign.ARIES,
            YandexZodiacSign.CANCER
        )
        assert "противоположности" in text.lower()
    
    def test_generate_advice_text(self):
        """Test advice text generation."""
        # Mock random to ensure deterministic test
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "Тестовый совет"
            
            advice = self.formatter._generate_advice_text()
            assert advice == "Тестовый совет"
            
            # Verify it was called with the advice list
            mock_choice.assert_called_once()
            args = mock_choice.call_args[0][0]
            assert isinstance(args, list)
            assert len(args) > 0