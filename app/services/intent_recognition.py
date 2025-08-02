"""
Сервис распознавания интентов для Яндекс.Диалогов.
"""
import hashlib
import re
from typing import Any, Dict, List, Tuple

from app.models.yandex_models import (
    ProcessedRequest,
    UserContext,
    YandexIntent,
    YandexZodiacSign,
)


class IntentRecognizer:
    """Класс для распознавания интентов пользователя."""

    def __init__(self):
        # Кеширование для производительности
        self._intent_cache: Dict[str, Tuple[YandexIntent, float]] = {}
        self._entity_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_size_limit = 1000

        # Статистика и пользовательские паттерны
        self._user_patterns: Dict[str, List[YandexIntent]] = {}
        self._intent_frequency: Dict[YandexIntent, int] = {}

        self.intent_patterns = {
            YandexIntent.GREET: [
                r"привет",
                r"здравствуй",
                r"добрый",
                r"начать",
                r"старт",
                r"hello",
                r"hi",
                r"начни",
                r"запуск",
            ],
            YandexIntent.HOROSCOPE: [
                r"гороскоп",
                r"прогноз",
                r"предсказание",
                r"что меня ждет",
                r"мой гороскоп",
                r"звезды",
                r"астрология",
                r"на сегодня",
                r"на завтра",
                r"на неделю",
                r"horoscope",
                r"horoscope.*for",
                r"forecast",
                r"prediction",
            ],
            YandexIntent.COMPATIBILITY: [
                r"совместимость",
                r"подходим",
                r"отношения",
                r"совместим",
                r"пара",
                r"партнер",
                r"любовь",
                r"вместе",
                r"compatibility",
                r"compatible",
                r"match",
                r"relationship",
            ],
            YandexIntent.NATAL_CHART: [
                r"натальная карта",
                r"карта рождения",
                r"натальная",
                r"астрологическая карта",
                r"персональная карта",
            ],
            YandexIntent.LUNAR_CALENDAR: [
                r"лунный календарь",
                r"фазы луны",
                r"луна",
                r"лунные",
                r"новолуние",
                r"полнолуние",
                r"лунный.*календарь",
                r"календарь.*лун",
                r"неделю.*лун",
                r"эту.*неделю",
            ],
            YandexIntent.ADVICE: [
                r"совет",
                r"рекомендация",
                r"что делать",
                r"подскажи",
                r"посоветуй",
                r"помоги",
                r"советы",
                r"рекомендации",
                r"с советами",
            ],
            YandexIntent.HELP: [
                r"помощь",
                r"справка",
                r"что умеешь",
                r"возможности",
                r"команды",
                r"функции",
                r"помоги",
            ],
        }

        self.zodiac_patterns = {
            YandexZodiacSign.ARIES: [
                r"овен",
                r"овна",
                r"овном",
                r"овне",
                r"aries",
            ],
            YandexZodiacSign.TAURUS: [
                r"телец",
                r"тельца",
                r"тельцом",
                r"тельце",
                r"taurus",
            ],
            YandexZodiacSign.GEMINI: [
                r"близнецы",
                r"близнецов",
                r"близнецами",
                r"близнецах",
                r"gemini",
            ],
            YandexZodiacSign.CANCER: [
                r"рак",
                r"рака",
                r"раком",
                r"раке",
                r"cancer",
            ],
            YandexZodiacSign.LEO: [r"лев", r"льва", r"львом", r"льве", r"leo"],
            YandexZodiacSign.VIRGO: [
                r"дева",
                r"девы",
                r"девой",
                r"деве",
                r"virgo",
            ],
            YandexZodiacSign.LIBRA: [
                r"весы",
                r"весов",
                r"весами",
                r"весах",
                r"libra",
            ],
            YandexZodiacSign.SCORPIO: [
                r"скорпион",
                r"скорпиона",
                r"скорпионом",
                r"скорпионе",
                r"scorpio",
            ],
            YandexZodiacSign.SAGITTARIUS: [
                r"стрелец",
                r"стрельца",
                r"стрельцом",
                r"стрельце",
                r"sagittarius",
            ],
            YandexZodiacSign.CAPRICORN: [
                r"козерог",
                r"козерога",
                r"козерогом",
                r"козероге",
                r"capricorn",
            ],
            YandexZodiacSign.AQUARIUS: [
                r"водолей",
                r"водолея",
                r"водолеем",
                r"водолее",
                r"aquarius",
            ],
            YandexZodiacSign.PISCES: [
                r"рыбы",
                r"рыб",
                r"рыбами",
                r"рыбах",
                r"pisces",
            ],
        }

        self.date_patterns = [
            r"(\d{1,2})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{4})",  # DD.MM.YYYY
            r"(\d{1,2})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{2})",  # DD.MM.YY
            r"(\d{4})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{1,2})",  # YYYY.MM.DD
            r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})",  # DD месяца YYYY
        ]

        self.time_patterns = [
            r"(\d{1,2}):(\d{2})",  # HH:MM
            r"(\d{1,2})\s*час",  # X час(ов)
        ]

    def recognize_intent(
        self, text: str, user_context: UserContext
    ) -> ProcessedRequest:
        """Распознает интент из текста пользователя."""
        text_lower = text.lower()

        # Проверяем ожидание данных от пользователя
        if user_context.awaiting_data:
            return self._process_awaited_data(text, text_lower, user_context)

        # Распознаем новый интент
        intent, confidence = self._match_intent(text_lower)
        entities = self._extract_entities(text_lower)

        # Обновляем статистику
        self._intent_frequency[intent] = (
            self._intent_frequency.get(intent, 0) + 1
        )
        user_id = getattr(user_context, "user_id", None)
        if user_id:
            if user_id not in self._user_patterns:
                self._user_patterns[user_id] = []
            self._user_patterns[user_id].append(intent)

        return ProcessedRequest(
            intent=intent,
            entities=entities,
            confidence=confidence,
            raw_text=text,
            user_context=user_context,
        )

    def _match_intent(self, text: str) -> Tuple[YandexIntent, float]:
        """Определяет интент по тексту."""
        # Проверяем кеш
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._intent_cache:
            return self._intent_cache[cache_key]

        best_intent = YandexIntent.UNKNOWN
        max_confidence = 0.0

        for intent, patterns in self.intent_patterns.items():
            confidence = 0.0
            matches = 0
            exact_match = False

            for pattern in patterns:
                if re.search(pattern, text):
                    matches += 1
                    # Check for exact match (pattern equals the entire text)
                    if re.fullmatch(pattern, text):
                        exact_match = True
                        confidence += 0.9  # High confidence for exact matches
                    else:
                        # Give higher base confidence for pattern matches
                        confidence += 0.4 + (0.6 / len(patterns))

            # Bonus for multiple matches
            if matches > 1:
                confidence *= (
                    1.2 + (matches - 1) * 0.3
                )  # More bonus for more matches

            # Ensure exact matches have high confidence
            if exact_match:
                confidence = max(confidence, 0.85)

            # Boost confidence for multiple pattern matches
            if matches >= 3:
                confidence = max(confidence, 0.95)

            # Minimum threshold for single matches in complex text
            if matches == 1 and len(text.split()) > 3:
                confidence = max(confidence, 0.35)

            if confidence > max_confidence:
                max_confidence = confidence
                best_intent = intent

        result = (best_intent, min(max_confidence, 1.0))

        # Сохраняем в кеш с ограничением размера
        if len(self._intent_cache) >= self.cache_size_limit:
            # Удаляем самые старые записи
            self._intent_cache.clear()
        self._intent_cache[cache_key] = result

        return result

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Извлекает сущности из текста."""
        # Проверяем кеш
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._entity_cache:
            return self._entity_cache[cache_key]

        entities = {}

        # Извлечение знаков зодиака
        zodiac_signs = self._extract_zodiac_signs(text)
        if zodiac_signs:
            entities["zodiac_signs"] = zodiac_signs

        # Извлечение дат
        dates = self._extract_dates(text)
        if dates:
            entities["dates"] = dates

        # Извлечение времени
        times = self._extract_times(text)
        if times:
            entities["times"] = times

        # Извлечение периодов времени
        periods = self._extract_periods(text)
        if periods:
            entities["periods"] = periods

        # Анализ настроения
        sentiment = self._analyze_sentiment(text)
        if sentiment:
            entities["sentiment"] = sentiment

        # Сохраняем в кеш с ограничением размера
        if len(self._entity_cache) >= self.cache_size_limit:
            self._entity_cache.clear()
        self._entity_cache[cache_key] = entities

        return entities

    def _extract_zodiac_signs(self, text: str) -> List[YandexZodiacSign]:
        """Извлекает знаки зодиака из текста."""
        found_signs = []

        for sign, patterns in self.zodiac_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    found_signs.append(sign)
                    break

        return found_signs

    def _extract_dates(self, text: str) -> List[str]:
        """Извлекает даты из текста."""
        dates = []

        # Извлекаем обычные даты
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                dates.append(match.group())

        # Извлекаем относительные даты
        from datetime import date, timedelta

        today = date.today()

        if re.search(r"сегодня", text):
            dates.append(today.strftime("%d.%m.%Y"))
        if re.search(r"вчера", text):
            dates.append((today - timedelta(days=1)).strftime("%d.%m.%Y"))
        if re.search(r"завтра", text):
            dates.append((today + timedelta(days=1)).strftime("%d.%m.%Y"))

        return dates

    def _extract_times(self, text: str) -> List[str]:
        """Извлекает время из текста."""
        times = []

        for pattern in self.time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                times.append(match.group())

        return times

    def _extract_periods(self, text: str) -> List[str]:
        """Извлекает периоды времени из текста."""
        periods = []

        period_patterns = {
            "daily": [
                r"сегодня",
                r"на сегодня",
                r"сейчас",
                r"в данный момент",
            ],
            "weekly": [r"на неделю", r"недельный", r"эту неделю"],
            "monthly": [r"на месяц", r"месячный", r"этот месяц"],
            "current": [r"сейчас", r"в данный момент", r"что происходит"],
        }

        for period, patterns in period_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    periods.append(period)
                    break  # Avoid duplicates for same period

        return periods

    def _analyze_sentiment(self, text: str) -> str:
        """Анализирует настроение в тексте."""
        positive_words = [
            r"отлично",
            r"хорошо",
            r"замечательно",
            r"прекрасно",
            r"супер",
        ]
        negative_words = [
            r"плохо",
            r"ужасно",
            r"грустно",
            r"депрессия",
            r"болею",
        ]

        positive_count = sum(
            1 for word in positive_words if re.search(word, text)
        )
        negative_count = sum(
            1 for word in negative_words if re.search(word, text)
        )

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def _process_awaited_data(
        self, text: str, text_lower: str, user_context: UserContext
    ) -> ProcessedRequest:
        """Обрабатывает ожидаемые данные от пользователя."""
        entities = self._extract_entities(text_lower)

        if user_context.awaiting_data == "birth_date":
            if entities.get("dates"):
                entities["birth_date"] = entities["dates"][0]
                return ProcessedRequest(
                    intent=YandexIntent.HOROSCOPE,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )

        elif user_context.awaiting_data == "zodiac_sign":
            if entities.get("zodiac_signs"):
                entities["zodiac_sign"] = entities["zodiac_signs"][0]
                return ProcessedRequest(
                    intent=user_context.intent or YandexIntent.COMPATIBILITY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )

        elif user_context.awaiting_data == "partner_sign":
            if entities.get("zodiac_signs"):
                entities["partner_sign"] = entities["zodiac_signs"][0]
                return ProcessedRequest(
                    intent=YandexIntent.COMPATIBILITY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )

        # Если ожидаемые данные не найдены, пытаемся распознать как новый интент
        intent, confidence = self._match_intent(text_lower)
        return ProcessedRequest(
            intent=intent,
            entities=entities,
            confidence=confidence * 0.8,  # Снижаем уверенность
            raw_text=text,
            user_context=user_context,
        )

    def get_intent_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику интентов."""
        return {
            "intent_frequency": dict(self._intent_frequency),
            "cache_size": len(self._intent_cache),
            "entity_cache_size": len(self._entity_cache),
        }

    def clear_cache(self):
        """Очищает кеш."""
        self._intent_cache.clear()
        self._entity_cache.clear()

    def get_user_preferences(self, user_id: str) -> List[YandexIntent]:
        """Получает предпочтения пользователя."""
        if user_id not in self._user_patterns:
            self._user_patterns[user_id] = []

        # Подсчитываем частоту интентов
        from collections import Counter

        counter = Counter(self._user_patterns[user_id])

        # Возвращаем отсортированные по частоте интенты
        return [intent for intent, _count in counter.most_common()]
