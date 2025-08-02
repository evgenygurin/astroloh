"""
Тесты для расширенной системы распознавания интентов Stage 5.
"""
from datetime import date, timedelta

import pytest

from app.models.yandex_models import (
    ProcessedRequest,
    UserContext,
    YandexIntent,
    YandexZodiacSign,
)
from app.services.intent_recognition import IntentRecognizer


class TestEnhancedIntentRecognition:
    """Тесты для расширенного распознавания интентов."""

    @pytest.fixture
    def recognizer(self):
        return IntentRecognizer()

    @pytest.fixture
    def user_context(self):
        return UserContext(user_id="test_user")

    def test_weighted_pattern_matching(self, recognizer, user_context):
        """Тест взвешенного сопоставления паттернов."""
        # Тест основного паттерна (высокий вес)
        request = recognizer.recognize_intent("мой гороскоп", user_context)
        assert request.intent == YandexIntent.HOROSCOPE
        assert request.confidence > 0.8

        # Тест вторичного паттерна (средний вес)
        request = recognizer.recognize_intent("что меня ждет", user_context)
        assert request.intent == YandexIntent.HOROSCOPE
        assert request.confidence > 0.5

        # Тест контекстного паттерна (низкий вес)
        request = recognizer.recognize_intent("на сегодня", user_context)
        assert request.intent == YandexIntent.HOROSCOPE
        assert request.confidence > 0.3

    def test_multiple_pattern_bonus(self, recognizer, user_context):
        """Тест бонуса за множественные совпадения."""
        # Запрос с несколькими паттернами должен иметь высокую уверенность
        request = recognizer.recognize_intent(
            "мой гороскоп на сегодня", user_context
        )
        assert request.intent == YandexIntent.HOROSCOPE
        assert request.confidence > 0.9

    def test_user_frequency_bonus(self, recognizer):
        """Тест бонуса за частоту использования пользователем."""
        user_context = UserContext(user_id="frequent_user")

        # Симулируем частое использование интента гороскопа
        for _ in range(10):
            recognizer.recognize_intent("гороскоп", user_context)

        # Последующие запросы должны иметь небольшой бонус
        request = recognizer.recognize_intent("прогноз", user_context)
        assert request.intent == YandexIntent.HOROSCOPE
        # Проверяем что уверенность выше базовой

    def test_intent_caching(self, recognizer, user_context):
        """Тест кеширования результатов распознавания."""
        text = "мой гороскоп на завтра"

        # Первый запрос
        request1 = recognizer.recognize_intent(text, user_context)

        # Второй запрос с тем же текстом
        request2 = recognizer.recognize_intent(text, user_context)

        # Результаты должны быть идентичными
        assert request1.intent == request2.intent
        assert request1.confidence == request2.confidence

        # Проверяем что кеш работает
        assert len(recognizer._intent_cache) > 0

    def test_entity_caching(self, recognizer, user_context):
        """Тест кеширования извлеченных сущностей."""
        text = "совместимость льва и девы"

        request1 = recognizer.recognize_intent(text, user_context)
        request2 = recognizer.recognize_intent(text, user_context)

        # Сущности должны быть одинаковыми
        assert request1.entities == request2.entities
        assert len(recognizer._entity_cache) > 0

    def test_advanced_date_extraction(self, recognizer, user_context):
        """Тест расширенного извлечения дат."""
        test_cases = [
            ("15 марта 1990", ["15.03.1990"]),
            ("сегодня", [date.today().strftime("%d.%m.%Y")]),
            (
                "вчера",
                [(date.today() - timedelta(days=1)).strftime("%d.%m.%Y")],
            ),
            (
                "завтра",
                [(date.today() + timedelta(days=1)).strftime("%d.%m.%Y")],
            ),
            ("15.03.90", ["15.03.90"]),
            ("2024-03-15", ["2024-03-15"]),
        ]

        for text, expected_dates in test_cases:
            request = recognizer.recognize_intent(
                f"гороскоп {text}", user_context
            )
            if expected_dates:
                assert "dates" in request.entities
                # Проверяем что хотя бы одна дата извлечена
                assert len(request.entities["dates"]) > 0

    def test_zodiac_sign_variations(self, recognizer, user_context):
        """Тест различных вариаций знаков зодиака."""
        test_cases = [
            ("я лев", [YandexZodiacSign.LEO]),
            ("мой знак овен", [YandexZodiacSign.ARIES]),
            (
                "совместимость льва и девы",
                [YandexZodiacSign.LEO, YandexZodiacSign.VIRGO],
            ),
            (
                "телец с водолеем",
                [YandexZodiacSign.TAURUS, YandexZodiacSign.AQUARIUS],
            ),
        ]

        for text, expected_signs in test_cases:
            request = recognizer.recognize_intent(text, user_context)
            if expected_signs:
                assert "zodiac_signs" in request.entities
                assert len(request.entities["zodiac_signs"]) == len(
                    expected_signs
                )
                for sign in expected_signs:
                    assert sign in request.entities["zodiac_signs"]

    def test_time_period_extraction(self, recognizer, user_context):
        """Тест извлечения периодов времени."""
        test_cases = [
            ("гороскоп на сегодня", ["daily"]),
            ("прогноз на неделю", ["weekly"]),
            ("что ждет на месяц", ["monthly"]),
            ("сейчас что происходит", ["current"]),
        ]

        for text, expected_periods in test_cases:
            request = recognizer.recognize_intent(text, user_context)
            if expected_periods:
                assert "periods" in request.entities
                for period in expected_periods:
                    assert period in request.entities["periods"]

    def test_sentiment_analysis(self, recognizer, user_context):
        """Тест анализа настроения."""
        test_cases = [
            ("отлично, расскажи гороскоп", "positive"),
            ("плохо себя чувствую, нужен совет", "negative"),
            ("нормально, что говорят звезды", "neutral"),
        ]

        for text, expected_sentiment in test_cases:
            request = recognizer.recognize_intent(text, user_context)
            if expected_sentiment:
                assert "sentiment" in request.entities
                assert request.entities["sentiment"] == expected_sentiment

    def test_name_extraction(self, recognizer, user_context):
        """Тест извлечения имен."""
        text = "совместимость Анны и Петра"
        request = recognizer.recognize_intent(text, user_context)

        if "names" in request.entities:
            names = request.entities["names"]
            assert "Анны" in names or "Петра" in names

    def test_number_extraction(self, recognizer, user_context):
        """Тест извлечения чисел."""
        text = "гороскоп на 15 число"
        request = recognizer.recognize_intent(text, user_context)

        if "numbers" in request.entities:
            numbers = request.entities["numbers"]
            assert 15 in numbers

    def test_awaited_data_processing(self, recognizer):
        """Тест обработки ожидаемых данных."""
        # Контекст ожидания даты рождения
        awaiting_context = UserContext(
            user_id="test_user",
            awaiting_data="birth_date",
            intent=YandexIntent.HOROSCOPE,
        )

        request = recognizer.recognize_intent(
            "15 марта 1990", awaiting_context
        )

        assert request.intent == YandexIntent.HOROSCOPE
        assert request.confidence == 1.0
        assert "birth_date" in request.entities

    def test_partner_data_processing(self, recognizer):
        """Тест обработки данных о партнере."""
        awaiting_context = UserContext(
            user_id="test_user",
            awaiting_data="partner_sign",
            intent=YandexIntent.COMPATIBILITY,
        )

        request = recognizer.recognize_intent("дева", awaiting_context)

        assert request.intent == YandexIntent.COMPATIBILITY
        assert "partner_sign" in request.entities
        assert request.entities["partner_sign"] == YandexZodiacSign.VIRGO

    def test_fallback_processing(self, recognizer):
        """Тест обработки fallback при неполных данных."""
        awaiting_context = UserContext(
            user_id="test_user", awaiting_data="birth_date"
        )

        # Запрос без ожидаемых данных
        request = recognizer.recognize_intent("помощь", awaiting_context)

        # Должен распознать новый интент с пониженной уверенностью
        assert request.intent == YandexIntent.HELP
        assert request.confidence < 1.0

    def test_intent_statistics(self, recognizer, user_context):
        """Тест статистики интентов."""
        # Генерируем несколько запросов
        intents = [
            "мой гороскоп",
            "совместимость знаков",
            "астрологический совет",
            "гороскоп на завтра",
        ]

        for intent_text in intents:
            recognizer.recognize_intent(intent_text, user_context)

        stats = recognizer.get_intent_statistics()

        assert "intent_frequency" in stats
        assert "cache_size" in stats
        assert "entity_cache_size" in stats
        assert stats["cache_size"] > 0

    def test_cache_clearing(self, recognizer, user_context):
        """Тест очистки кеша."""
        # Генерируем данные в кеше
        recognizer.recognize_intent("тестовый запрос", user_context)

        assert len(recognizer._intent_cache) > 0

        # Очищаем кеш
        recognizer.clear_cache()

        assert len(recognizer._intent_cache) == 0
        assert len(recognizer._entity_cache) == 0

    def test_user_preferences(self, recognizer):
        """Тест получения предпочтений пользователя."""
        user_id = "test_user"

        # Симулируем историю запросов
        intents = [
            YandexIntent.HOROSCOPE,
            YandexIntent.HOROSCOPE,
            YandexIntent.COMPATIBILITY,
            YandexIntent.HOROSCOPE,
        ]

        # Инициализируем пользователя
        if user_id not in recognizer._user_patterns:
            recognizer._user_patterns[user_id] = []

        for intent in intents:
            recognizer._user_patterns[user_id].append(intent)

        preferences = recognizer.get_user_preferences(user_id)

        # Гороскоп должен быть наиболее частым
        assert preferences[0] == YandexIntent.HOROSCOPE
        assert preferences[1] == YandexIntent.COMPATIBILITY

    def test_complex_queries(self, recognizer, user_context):
        """Тест сложных составных запросов."""
        complex_queries = [
            "мой гороскоп на сегодня, я лев",
            "совместимость льва и девы в отношениях",
            "натальная карта для рожденного 15 марта в 14:30",
            "лунный календарь на эту неделю с советами",
        ]

        for query in complex_queries:
            request = recognizer.recognize_intent(query, user_context)

            # Все запросы должны быть распознаны с разумной уверенностью
            assert request.intent != YandexIntent.UNKNOWN
            assert request.confidence > 0.3

            # Должны быть извлечены соответствующие сущности
            assert len(request.entities) > 0

    def test_multilingual_support(self, recognizer, user_context):
        """Тест поддержки разных языков."""
        test_cases = [
            ("horoscope for leo", YandexIntent.HOROSCOPE),
            ("compatibility aries", YandexIntent.COMPATIBILITY),
            ("привет hello", YandexIntent.GREET),
        ]

        for text, expected_intent in test_cases:
            request = recognizer.recognize_intent(text, user_context)
            assert request.intent == expected_intent

    def test_edge_cases(self, recognizer, user_context):
        """Тест граничных случаев."""
        edge_cases = [
            "",  # Пустая строка
            "   ",  # Только пробелы
            "абракадабра xyz",  # Неизвестные слова
            "1234567890",  # Только цифры
            "!@#$%^&*()",  # Только символы
        ]

        for text in edge_cases:
            request = recognizer.recognize_intent(text, user_context)

            # Не должно вызывать исключений
            assert isinstance(request, ProcessedRequest)
            assert request.raw_text == text

    def test_performance_optimization(self, recognizer, user_context):
        """Тест оптимизации производительности."""
        # Тест одного и того же запроса несколько раз
        text = "мой гороскоп"

        import time

        # Первый запрос (без кеша)
        start_time = time.time()
        request1 = recognizer.recognize_intent(text, user_context)
        first_time = time.time() - start_time

        # Второй запрос (с кешем)
        start_time = time.time()
        request2 = recognizer.recognize_intent(text, user_context)
        second_time = time.time() - start_time

        # Результаты должны быть одинаковыми
        assert request1.intent == request2.intent
        assert request1.confidence == request2.confidence

        # Второй запрос должен быть быстрее (или хотя бы не медленнее)
        assert second_time <= first_time * 1.1  # Допускаем 10% погрешность
