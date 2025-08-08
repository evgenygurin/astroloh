"""
Сервис распознавания интентов для Яндекс.Диалогов.
"""

import hashlib
import logging
import re
from typing import Any, Dict, List, Tuple

from app.models.yandex_models import (
    ProcessedRequest,
    UserContext,
    YandexIntent,
    YandexZodiacSign,
)

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """Класс для распознавания интентов пользователя."""

    def __init__(self) -> None:
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
                # Alice-специфичные паттерны приветствия
                r"алиса.*астролог",
                r"откр.*навык",
                r"включ.*астролог",
                r"поговори.*звезд",
                r"давай.*гороскоп",
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
                # Голосовые варианты
                r"расскажи.*гороскоп",
                r"какой.*гороскоп",
                r"что.*звезды.*говорят",
                r"астрологический.*прогноз",
                r"что.*день.*готовит",
                r"планеты.*сегодня",
                r"мой.*знак.*сегодня",
                r"что.*ждет.*день",
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
                # Голосовые варианты для совместимости
                r"подходит.*ли",
                r"сочетаются.*ли",
                r"как.*уживаемся",
                r"отношения.*с",
                r"любовная.*совместимость",
                r"проверь.*совместимость",
                r"мы.*подходим",
                r"хорошая.*ли.*пара",
            ],
            YandexIntent.SYNASTRY: [
                r"синастрия",
                r"анализ отношений",
                r"карта отношений",
                r"совместимость с",
                r"что говорят звезды о наших отношениях",
                r"композитная карта",
                r"анализ пары",
                r"астрологический анализ отношений",
                r"synastry",
                r"composite chart",
                # Голосовые варианты для синастрии
                r"расскажи.*отношени",
                r"проанализируй.*отношения",
                r"какие.*отношения.*с",
                r"как.*сочетаемся.*астрологически",
                r"что.*карты.*говорят.*отношени",
                r"астрологический.*портрет.*пары",
                r"звездный.*анализ.*отношений",
                r"планетарная.*совместимость",
                r"глубокий.*анализ.*совместимости",
                r"детальная.*совместимость",
            ],
            YandexIntent.NATAL_CHART: [
                r"натальная карта",
                r"карта рождения",
                r"натальная",
                r"астрологическая карта",
                r"персональная карта",
                r"birth chart",
                r"natal chart",
                r"расскажи.*карту",
                r"моя.*карта",
                r"персональный.*гороскоп",
            ],
            YandexIntent.TRANSITS: [
                r"транзит",
                r"транзиты",
                r"текущие.*планеты",
                r"влияние.*планет",
                r"что.*сейчас.*происходит",
                r"астрологическая.*ситуация",
                r"planetary.*transits",
                r"current.*influences",
                r"какие.*транзиты",
                r"планетные.*влияния",
                r"что.*показывают.*планеты",
                r"астрологический.*прогноз.*сейчас",
            ],
            YandexIntent.PROGRESSIONS: [
                r"прогресс",
                r"прогрессии",
                r"развитие.*личности",
                r"эволюция.*карты",
                r"внутренние.*изменения",
                r"progressions",
                r"personal.*development",
                r"что.*показывают.*прогрессии",
                r"как.*развиваюсь",
                r"внутренний.*рост",
                r"психологическое.*развитие",
            ],
            YandexIntent.SOLAR_RETURN: [
                r"соляр",
                r"солярный.*возврат",
                r"годовая.*карта",
                r"на.*год",
                r"день.*рождения",
                r"solar.*return",
                r"birthday.*chart",
                r"годовой.*прогноз",
                r"что.*ждет.*в.*году",
                r"астрологический.*год",
                r"тема.*года",
            ],
            YandexIntent.LUNAR_RETURN: [
                r"лунар",
                r"лунный.*возврат",
                r"месячная.*карта",
                r"на.*месяц",
                r"новолуние",
                r"lunar.*return",
                r"monthly.*chart",
                r"месячный.*прогноз",
                r"что.*ждет.*в.*месяце",
                r"лунный.*цикл",
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
                # Голосовые варианты для советов
                r"дай.*совет",
                r"что.*посоветуешь",
                r"как.*лучше.*поступить",
                r"астрологический.*совет",
                r"совет.*дня",
                r"что.*звезды.*советуют",
                r"мудрость.*звезд",
            ],
            YandexIntent.HELP: [
                r"помощь",
                r"справка",
                r"что умеешь",
                r"возможности",
                r"команды",
                r"функции",
                r"помоги",
                # Alice-специфичные паттерны помощи
                r"как.*работать",
                r"что.*можешь",
                r"как.*пользоваться",
                r"инструкция",
                r"как.*спросить",
                r"что.*спросить",
                r"покажи.*возможности",
                r"список.*команд",
            ],
            YandexIntent.EXIT: [
                r"выход",
                r"завершить",
                r"окончить",
                r"стоп",
                r"хватит",
                r"всё",
                r"баста",
                r"до свидания",
                r"пока",
                r"уходить",
                r"закрыть",
                r"конец",
                # Alice-специфичные паттерны выхода
                r"закрой.*навык",
                r"выйти.*из.*навыка",
                r"отключи.*астролог",
                r"заверши.*работу",
                r"не.*нужно.*больше",
                r"спасибо.*до.*свидания",
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
            r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)",  # DD месяца (текущего года)
        ]

        self.time_patterns = [
            r"(\d{1,2}):(\d{2})",  # HH:MM
            r"(\d{1,2})\s*час",  # X час(ов)
        ]

    def recognize_intent(
        self, text: str, user_context: UserContext
    ) -> ProcessedRequest:
        """Распознает интент из текста пользователя."""
        logger.info(
            f"INTENT_RECOGNITION_START: text='{text[:100]}{'...' if len(text) > 100 else ''}'"
        )
        text_lower = text.lower()

        # Проверяем ожидание данных от пользователя
        if user_context.awaiting_data:
            logger.info("INTENT_AWAITING_DATA: processing awaited data")
            return self._process_awaited_data(text, text_lower, user_context)

        # Распознаем новый интент
        intent, confidence = self._match_intent(text_lower)
        entities = self._extract_entities(text_lower)
        logger.info(
            f"INTENT_RECOGNIZED: intent={intent.value}, confidence={confidence:.2f}, entities={list(entities.keys())}"
        )

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
        """Определяет интент по тексту с улучшенной обработкой для Alice."""
        logger.debug(f"INTENT_MATCH_START: analyzing text='{text[:100]}'")

        # Проверяем кеш
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._intent_cache:
            cached_intent, cached_confidence = self._intent_cache[cache_key]
            logger.debug(
                f"INTENT_MATCH_CACHE_HIT: intent={cached_intent.value}, confidence={cached_confidence:.2f}"
            )
            return self._intent_cache[cache_key]

        # Преобразуем текст для лучшей обработки голосового ввода
        processed_text = self._preprocess_voice_input(text)
        logger.debug(
            f"INTENT_MATCH_PROCESSED: original='{text}', processed='{processed_text}'"
        )

        best_intent = YandexIntent.UNKNOWN
        max_confidence = 0.0

        for intent, patterns in self.intent_patterns.items():
            confidence = 0.0
            matches = 0
            exact_match = False
            voice_match = False

            for pattern in patterns:
                # Проверяем оригинальный текст
                if re.search(pattern, text):
                    matches += 1
                    if re.fullmatch(pattern, text):
                        exact_match = True
                        confidence += 0.9
                    else:
                        confidence += 0.4 + (0.6 / len(patterns))

                # Проверяем обработанный текст
                elif re.search(pattern, processed_text):
                    matches += 1
                    voice_match = True
                    confidence += 0.5 + (0.4 / len(patterns))

            # Бонус за множественные совпадения
            if matches > 1:
                confidence *= 1.2 + (matches - 1) * 0.3

            # Высокая уверенность для точных совпадений
            if exact_match:
                confidence = max(confidence, 0.85)
            elif voice_match and matches >= 2:
                confidence = max(confidence, 0.75)

            # Бонус за множественные паттерны
            if matches >= 3:
                confidence = max(confidence, 0.95)

            # Минимальный порог для одиночных совпадений
            if matches == 1 and len(text.split()) > 3:
                confidence = max(confidence, 0.35)

            if confidence > max_confidence:
                max_confidence = confidence
                best_intent = intent
                logger.debug(
                    f"INTENT_MATCH_NEW_BEST: intent={intent.value}, confidence={confidence:.2f}, matches={matches}"
                )

        result = (best_intent, min(max_confidence, 1.0))
        logger.debug(
            f"INTENT_MATCH_RESULT: final_intent={best_intent.value}, final_confidence={result[1]:.2f}"
        )

        # Сохраняем в кеш
        if len(self._intent_cache) >= self.cache_size_limit:
            logger.debug(
                f"INTENT_MATCH_CACHE_CLEAR: clearing cache (size={len(self._intent_cache)})"
            )
            self._intent_cache.clear()
        self._intent_cache[cache_key] = result

        return result

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Извлекает сущности из текста."""
        logger.debug(f"ENTITY_EXTRACTION_START: text='{text[:100]}'")

        # Проверяем кеш
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._entity_cache:
            cached_entities = self._entity_cache[cache_key]
            logger.debug(
                f"ENTITY_EXTRACTION_CACHE_HIT: entities={list(cached_entities.keys())}"
            )
            return self._entity_cache[cache_key]

        entities: Dict[str, Any] = {}

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

        # Извлечение имен партнеров для синастрии
        partner_names = self._extract_partner_names(text)
        if partner_names:
            entities["partner_names"] = partner_names

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
        logger.debug(f"ZODIAC_EXTRACTION_START: text='{text[:50]}'")
        found_signs = []

        for sign, patterns in self.zodiac_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    found_signs.append(sign)
                    logger.debug(
                        f"ZODIAC_EXTRACTION_MATCH: sign={sign.value}, pattern='{pattern}'"
                    )
                    break

        logger.debug(
            f"ZODIAC_EXTRACTION_RESULT: found_signs={[s.value for s in found_signs]}"
        )
        return found_signs

    def _extract_dates(self, text: str) -> List[str]:
        """Извлекает даты из текста."""
        logger.debug(f"DATE_EXTRACTION_START: text='{text[:50]}'")
        dates = []

        # Извлекаем обычные даты
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                date_found = match.group()
                dates.append(date_found)
                logger.debug(
                    f"DATE_EXTRACTION_PATTERN_MATCH: date='{date_found}', pattern='{pattern}'"
                )

        # Извлекаем относительные даты
        from datetime import date, timedelta

        today = date.today()

        if re.search(r"сегодня", text):
            today_str = today.strftime("%d.%m.%Y")
            dates.append(today_str)
            logger.debug(f"DATE_EXTRACTION_RELATIVE: today='{today_str}'")
        if re.search(r"вчера", text):
            yesterday_str = (today - timedelta(days=1)).strftime("%d.%m.%Y")
            dates.append(yesterday_str)
            logger.debug(
                f"DATE_EXTRACTION_RELATIVE: yesterday='{yesterday_str}'"
            )
        if re.search(r"завтра", text):
            tomorrow_str = (today + timedelta(days=1)).strftime("%d.%m.%Y")
            dates.append(tomorrow_str)
            logger.debug(
                f"DATE_EXTRACTION_RELATIVE: tomorrow='{tomorrow_str}'"
            )

        logger.debug(f"DATE_EXTRACTION_RESULT: dates={dates}")
        return dates

    def _extract_times(self, text: str) -> List[str]:
        """Извлекает время из текста."""
        logger.debug(f"TIME_EXTRACTION_START: text='{text[:50]}'")
        times = []

        for pattern in self.time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                time_found = match.group()
                times.append(time_found)
                logger.debug(
                    f"TIME_EXTRACTION_MATCH: time='{time_found}', pattern='{pattern}'"
                )

        logger.debug(f"TIME_EXTRACTION_RESULT: times={times}")
        return times

    def _extract_periods(self, text: str) -> List[str]:
        """Извлекает периоды времени из текста."""
        logger.debug(f"PERIOD_EXTRACTION_START: text='{text[:50]}'")
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
                    logger.debug(
                        f"PERIOD_EXTRACTION_MATCH: period='{period}', pattern='{pattern}'"
                    )
                    break  # Avoid duplicates for same period

        logger.debug(f"PERIOD_EXTRACTION_RESULT: periods={periods}")
        return periods

    def _extract_partner_names(self, text: str) -> List[str]:
        """Извлекает имена партнеров из текста для синастрии."""
        logger.debug(f"PARTNER_NAME_EXTRACTION_START: text='{text[:50]}'")
        partner_names = []
        
        # Паттерны для распознавания имен в контексте синастрии
        name_patterns = [
            r"с\s+([А-ЯЁ][а-яё]+)(?:\s|$)",  # "с Марией"
            r"совместимость\s+с\s+([А-ЯЁ][а-яё]+)",  # "совместимость с Иваном"
            r"отношения\s+с\s+([А-ЯЁ][а-яё]+)",  # "отношения с Анной"
            r"мой\s+([А-ЯЁ][а-яё]+)",  # "мой Александр"
            r"моя\s+([А-ЯЁ][а-яё]+)",  # "моя Елена"
            r"партнер\s+([А-ЯЁ][а-яё]+)",  # "партнер Дмитрий"
            r"партнерша\s+([А-ЯЁ][а-яё]+)",  # "партнерша Ольга"
            r"и\s+([А-ЯЁ][а-яё]+)(?:\s|$)",  # "Лев и Мария"
            r"([А-ЯЁ][а-яё]+)\s+и\s+",  # "Иван и..."
            r"между\s+мной\s+и\s+([А-ЯЁ][а-яё]+)",  # "между мной и Петром"
            r"меня\s+и\s+([А-ЯЁ][а-яё]+)",  # "меня и Светлана"
            r"([А-ЯЁ][а-яё]+)\s+родил[аос]я",  # "Анна родилась"
            r"имя\s+([А-ЯЁ][а-яё]+)",  # "имя Михаил"
        ]
        
        for pattern in name_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip().title()
                # Фильтруем слишком короткие имена и служебные слова
                if len(name) >= 3 and name.lower() not in [
                    'для', 'при', 'мне', 'нем', 'ней', 'тем', 'той', 'том', 'все', 'что', 'как'
                ]:
                    partner_names.append(name)
                    logger.debug(f"PARTNER_NAME_MATCH: found_name='{name}', pattern='{pattern}'")
        
        # Убираем дубликаты, сохраняя порядок
        unique_names = []
        for name in partner_names:
            if name not in unique_names:
                unique_names.append(name)
        
        logger.debug(f"PARTNER_NAME_EXTRACTION_RESULT: names={unique_names}")
        return unique_names

    def _analyze_sentiment(self, text: str) -> str:
        """Анализирует настроение в тексте."""
        logger.debug(f"SENTIMENT_ANALYSIS_START: text='{text[:50]}'")

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

        logger.debug(
            f"SENTIMENT_ANALYSIS_COUNTS: positive={positive_count}, negative={negative_count}"
        )

        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        logger.debug(f"SENTIMENT_ANALYSIS_RESULT: sentiment='{sentiment}'")
        return sentiment

    def _process_awaited_data(
        self, text: str, text_lower: str, user_context: UserContext
    ) -> ProcessedRequest:
        """Обрабатывает ожидаемые данные от пользователя."""
        logger.debug(
            f"AWAITED_DATA_PROCESSING_START: awaiting='{user_context.awaiting_data}', text='{text[:50]}'"
        )
        entities = self._extract_entities(text_lower)

        if user_context.awaiting_data == "birth_date":
            logger.debug(
                f"AWAITED_DATA_BIRTH_DATE: extracted_entities={list(entities.keys())}"
            )
            if entities.get("dates"):
                entities["birth_date"] = entities["dates"][0]
                logger.info(
                    f"AWAITED_DATA_SUCCESS: birth_date='{entities['birth_date']}'"
                )
                return ProcessedRequest(
                    intent=YandexIntent.HOROSCOPE,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )

        elif user_context.awaiting_data == "zodiac_sign":
            logger.debug(
                f"AWAITED_DATA_ZODIAC_SIGN: extracted_entities={list(entities.keys())}"
            )
            if entities.get("zodiac_signs"):
                entities["zodiac_sign"] = entities["zodiac_signs"][0]
                logger.info(
                    f"AWAITED_DATA_SUCCESS: zodiac_sign='{entities['zodiac_sign'].value}'"
                )
                return ProcessedRequest(
                    intent=user_context.intent or YandexIntent.COMPATIBILITY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )

        elif user_context.awaiting_data == "partner_sign":
            logger.debug(
                f"AWAITED_DATA_PARTNER_SIGN: extracted_entities={list(entities.keys())}"
            )
            if entities.get("zodiac_signs"):
                entities["partner_sign"] = entities["zodiac_signs"][0]
                logger.info(
                    f"AWAITED_DATA_SUCCESS: partner_sign='{entities['partner_sign'].value}'"
                )
                return ProcessedRequest(
                    intent=YandexIntent.COMPATIBILITY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )
        elif user_context.awaiting_data == "partner_name":
            logger.debug(
                f"AWAITED_DATA_PARTNER_NAME: extracted_entities={list(entities.keys())}"
            )
            if entities.get("partner_names"):
                entities["partner_name"] = entities["partner_names"][0]
                logger.info(
                    f"AWAITED_DATA_SUCCESS: partner_name='{entities['partner_name']}'"
                )
                return ProcessedRequest(
                    intent=YandexIntent.SYNASTRY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )
        elif user_context.awaiting_data == "partner_birth_date":
            logger.debug(
                f"AWAITED_DATA_PARTNER_BIRTH_DATE: extracted_entities={list(entities.keys())}"
            )
            if entities.get("dates"):
                entities["partner_birth_date"] = entities["dates"][0]
                logger.info(
                    f"AWAITED_DATA_SUCCESS: partner_birth_date='{entities['partner_birth_date']}'"
                )
                return ProcessedRequest(
                    intent=YandexIntent.SYNASTRY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )
        elif user_context.awaiting_data == "partner_zodiac_sign":
            logger.debug(
                f"AWAITED_DATA_PARTNER_ZODIAC_SIGN: extracted_entities={list(entities.keys())}"
            )
            if entities.get("zodiac_signs"):
                entities["partner_zodiac_sign"] = entities["zodiac_signs"][0]
                logger.info(
                    f"AWAITED_DATA_SUCCESS: partner_zodiac_sign='{entities['partner_zodiac_sign'].value}'"
                )
                return ProcessedRequest(
                    intent=YandexIntent.SYNASTRY,
                    entities=entities,
                    confidence=1.0,
                    raw_text=text,
                    user_context=user_context,
                )

        # Если ожидаемые данные не найдены, пытаемся распознать как новый интент
        logger.warning(
            "AWAITED_DATA_NOT_FOUND: falling_back_to_intent_recognition"
        )
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
        stats = {
            "intent_frequency": dict(self._intent_frequency),
            "cache_size": len(self._intent_cache),
            "entity_cache_size": len(self._entity_cache),
        }
        logger.debug(f"INTENT_STATISTICS: {stats}")
        return stats

    def clear_cache(self) -> None:
        """Очищает кеш."""
        intent_cache_size = len(self._intent_cache)
        entity_cache_size = len(self._entity_cache)

        self._intent_cache.clear()
        self._entity_cache.clear()

        logger.info(
            f"CACHE_CLEARED: intent_cache_size={intent_cache_size}, entity_cache_size={entity_cache_size}"
        )

    def _preprocess_voice_input(self, text: str) -> str:
        """Преобразует текст для лучшей обработки голосового ввода."""
        logger.debug(f"VOICE_PREPROCESSING_START: text='{text[:50]}'")

        # Общие ошибки распознавания речи
        voice_corrections = {
            r"гороскоп.*на.*сигодня": "гороскоп на сегодня",
            r"асталог": "астролог",
            r"совместимост": "совместимость",
            r"гороскоп.*ля.*льва": "гороскоп для льва",
        }

        processed = text.lower()
        corrections_applied = 0

        for pattern, replacement in voice_corrections.items():
            if re.search(pattern, processed):
                processed = re.sub(pattern, replacement, processed)
                corrections_applied += 1
                logger.debug(
                    f"VOICE_PREPROCESSING_CORRECTION: pattern='{pattern}' -> '{replacement}'"
                )

        logger.debug(
            f"VOICE_PREPROCESSING_RESULT: corrections={corrections_applied}, processed='{processed[:50]}'"
        )
        return processed

    def get_user_preferences(self, user_id: str) -> List[YandexIntent]:
        """Получает предпочтения пользователя."""
        logger.debug(f"USER_PREFERENCES_START: user_id='{user_id}'")

        if user_id not in self._user_patterns:
            self._user_patterns[user_id] = []
            logger.debug(
                f"USER_PREFERENCES_NEW_USER: created pattern list for user_id='{user_id}'"
            )

        # Подсчитываем частоту интентов
        from collections import Counter

        counter = Counter(self._user_patterns[user_id])
        preferences = [intent for intent, _count in counter.most_common()]

        logger.debug(
            f"USER_PREFERENCES_RESULT: user_id='{user_id}', preferences={[p.value for p in preferences]}"
        )
        return preferences
