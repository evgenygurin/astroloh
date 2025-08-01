"""
Тесты для системы распознавания интентов.
"""
import pytest
from app.services.intent_recognition import IntentRecognizer
from app.models.yandex_models import YandexIntent, YandexZodiacSign, UserContext


class TestIntentRecognizer:
    """Тесты для класса IntentRecognizer."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.recognizer = IntentRecognizer()
        self.user_context = UserContext()

    def test_greet_intent_recognition(self):
        """Тест распознавания интента приветствия."""
        test_phrases = [
            "привет",
            "здравствуй",
            "добрый день",
            "начать",
            "старт"
        ]
        
        for phrase in test_phrases:
            processed = self.recognizer.recognize_intent(phrase, self.user_context)
            assert processed.intent == YandexIntent.GREET
            assert processed.confidence > 0

    def test_horoscope_intent_recognition(self):
        """Тест распознавания интента гороскопа."""
        test_phrases = [
            "гороскоп",
            "мой прогноз",
            "что меня ждет", 
            "астрологический прогноз",
            "предсказание"
        ]
        
        for phrase in test_phrases:
            processed = self.recognizer.recognize_intent(phrase, self.user_context)
            assert processed.intent == YandexIntent.HOROSCOPE
            assert processed.confidence > 0

    def test_compatibility_intent_recognition(self):
        """Тест распознавания интента совместимости."""
        test_phrases = [
            "совместимость",
            "подходим ли мы",
            "отношения",
            "совместимы ли знаки"
        ]
        
        for phrase in test_phrases:
            processed = self.recognizer.recognize_intent(phrase, self.user_context)
            assert processed.intent == YandexIntent.COMPATIBILITY
            assert processed.confidence > 0

    def test_zodiac_sign_extraction(self):
        """Тест извлечения знаков зодиака."""
        test_cases = [
            ("я овен", [YandexZodiacSign.ARIES]),
            ("мой знак телец", [YandexZodiacSign.TAURUS]),
            ("овен и лев", [YandexZodiacSign.ARIES, YandexZodiacSign.LEO]),
            ("совместимость близнецов и рака", [YandexZodiacSign.GEMINI, YandexZodiacSign.CANCER])
        ]
        
        for text, expected_signs in test_cases:
            entities = self.recognizer._extract_entities(text)
            zodiac_signs = entities.get("zodiac_signs", [])
            assert zodiac_signs == expected_signs

    def test_date_extraction(self):
        """Тест извлечения дат."""
        test_cases = [
            "15.03.1990",
            "15 марта 1990",
            "15/03/1990", 
            "1990.03.15"
        ]
        
        for text in test_cases:
            entities = self.recognizer._extract_entities(text)
            dates = entities.get("dates", [])
            assert len(dates) > 0

    def test_awaiting_data_processing(self):
        """Тест обработки ожидаемых данных."""
        # Настраиваем контекст ожидания даты рождения
        self.user_context.awaiting_data = "birth_date"
        self.user_context.intent = YandexIntent.HOROSCOPE
        
        # Тестируем обработку даты
        processed = self.recognizer.recognize_intent("15.03.1990", self.user_context)
        assert processed.intent == YandexIntent.HOROSCOPE
        assert "birth_date" in processed.entities

    def test_unknown_intent(self):
        """Тест обработки неизвестного интента."""
        processed = self.recognizer.recognize_intent("абракадабра", self.user_context)
        assert processed.intent == YandexIntent.UNKNOWN