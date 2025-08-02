"""
Сервис распознавания интентов для Яндекс.Диалогов.
"""
import re
import hashlib
from typing import Dict, Any, Tuple, List

from app.models.yandex_models import (
    YandexIntent, 
    YandexZodiacSign, 
    ProcessedRequest, 
    UserContext
)


class IntentRecognizer:
    """Класс для распознавания интентов пользователя."""
    
    def __init__(self):
        # Кеширование для производительности
        self._intent_cache: Dict[str, Tuple[YandexIntent, float]] = {}
        self._entity_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_size_limit = 1000
        
        self.intent_patterns = {
            YandexIntent.GREET: [
                r"привет", r"здравствуй", r"добрый", r"начать", r"старт",
                r"hello", r"hi", r"начни", r"запуск"
            ],
            YandexIntent.HOROSCOPE: [
                r"гороскоп", r"прогноз", r"предсказание", r"что меня ждет",
                r"мой гороскоп", r"звезды", r"астрология"
            ],
            YandexIntent.COMPATIBILITY: [
                r"совместимость", r"подходим", r"отношения", r"совместим",
                r"пара", r"партнер", r"любовь", r"вместе"
            ],
            YandexIntent.NATAL_CHART: [
                r"натальная карта", r"карта рождения", r"натальная",
                r"астрологическая карта", r"персональная карта"
            ],
            YandexIntent.LUNAR_CALENDAR: [
                r"лунный календарь", r"фазы луны", r"луна", r"лунные",
                r"новолуние", r"полнолуние"
            ],
            YandexIntent.ADVICE: [
                r"совет", r"рекомендация", r"что делать", r"подскажи",
                r"посоветуй", r"помоги"
            ],
            YandexIntent.HELP: [
                r"помощь", r"справка", r"что умеешь", r"возможности",
                r"команды", r"функции", r"помоги"
            ]
        }
        
        self.zodiac_patterns = {
            YandexZodiacSign.ARIES: [r"овен", r"aries"],
            YandexZodiacSign.TAURUS: [r"телец", r"taurus"],
            YandexZodiacSign.GEMINI: [r"близнецы", r"близнецов", r"gemini"],
            YandexZodiacSign.CANCER: [r"рак", r"cancer"],
            YandexZodiacSign.LEO: [r"лев", r"leo"],
            YandexZodiacSign.VIRGO: [r"дева", r"virgo"],
            YandexZodiacSign.LIBRA: [r"весы", r"libra"],
            YandexZodiacSign.SCORPIO: [r"скорпион", r"scorpio"],
            YandexZodiacSign.SAGITTARIUS: [r"стрелец", r"sagittarius"],
            YandexZodiacSign.CAPRICORN: [r"козерог", r"capricorn"],
            YandexZodiacSign.AQUARIUS: [r"водолей", r"aquarius"],
            YandexZodiacSign.PISCES: [r"рыбы", r"pisces"]
        }
        
        self.date_patterns = [
            r"(\d{1,2})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{4})",  # DD.MM.YYYY
            r"(\d{1,2})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{2})",   # DD.MM.YY
            r"(\d{4})[\.\/\-\s](\d{1,2})[\.\/\-\s](\d{1,2})",  # YYYY.MM.DD
            r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})"  # DD месяца YYYY
        ]
        
        self.time_patterns = [
            r"(\d{1,2}):(\d{2})",  # HH:MM
            r"(\d{1,2})\s*час",    # X час(ов)
        ]

    def recognize_intent(self, text: str, user_context: UserContext) -> ProcessedRequest:
        """Распознает интент из текста пользователя."""
        text_lower = text.lower()
        
        # Проверяем ожидание данных от пользователя
        if user_context.awaiting_data:
            return self._process_awaited_data(text, text_lower, user_context)
        
        # Распознаем новый интент
        intent, confidence = self._match_intent(text_lower)
        entities = self._extract_entities(text_lower)
        
        return ProcessedRequest(
            intent=intent,
            entities=entities,
            confidence=confidence,
            raw_text=text,
            user_context=user_context
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
            
            for pattern in patterns:
                if re.search(pattern, text):
                    matches += 1
                    confidence += 1.0 / len(patterns)
            
            # Бонус за множественные совпадения
            if matches > 1:
                confidence *= 1.2
                
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
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                dates.append(match.group())
        
        return dates

    def _extract_times(self, text: str) -> List[str]:
        """Извлекает время из текста."""
        times = []
        
        for pattern in self.time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                times.append(match.group())
        
        return times

    def _process_awaited_data(
        self, 
        text: str, 
        text_lower: str, 
        user_context: UserContext
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
                    user_context=user_context
                )
        
        elif user_context.awaiting_data == "zodiac_sign":
            if entities.get("zodiac_signs"):
                entities["zodiac_sign"] = entities["zodiac_signs"][0]
                return ProcessedRequest(
                    intent=user_context.intent or YandexIntent.COMPATIBILITY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context
                )
        
        elif user_context.awaiting_data == "partner_sign":
            if entities.get("zodiac_signs"):
                entities["partner_sign"] = entities["zodiac_signs"][0]
                return ProcessedRequest(
                    intent=YandexIntent.COMPATIBILITY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context
                )
        
        # Если ожидаемые данные не найдены, пытаемся распознать как новый интент
        intent, confidence = self._match_intent(text_lower)
        return ProcessedRequest(
            intent=intent,
            entities=entities,
            confidence=confidence * 0.8,  # Снижаем уверенность
            raw_text=text,
            user_context=user_context
        )