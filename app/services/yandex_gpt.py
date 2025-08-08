"""
Клиент для работы с Yandex GPT API.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class YandexGPTMessage(BaseModel):
    """Сообщение для Yandex GPT."""

    role: str
    text: str


class YandexGPTRequest(BaseModel):
    """Запрос к Yandex GPT."""

    modelUri: str
    completionOptions: Dict[str, Any]
    messages: List[YandexGPTMessage]


class YandexGPTClient:
    """Клиент для работы с Yandex GPT API."""

    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.catalog_id = settings.YANDEX_CATALOG_ID or self.folder_id

        # Yandex GPT API endpoints
        self.base_url = "https://llm.api.cloud.yandex.net"
        self.completion_url = f"{self.base_url}/foundationModels/v1/completion"

        # Default model URI
        self.model_uri = f"gpt://{self.folder_id}/yandexgpt-lite/latest"

        # HTTP client session
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает HTTP сессию."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Api-Key {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._session

    async def close(self):
        """Закрывает HTTP сессию."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: str = "yandexgpt-lite",
    ) -> Optional[str]:
        """
        Генерирует текст с помощью Yandex GPT.

        Args:
            prompt: Пользовательский запрос
            system_prompt: Системный промпт
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов
            model: Модель для использования

        Returns:
            Сгенерированный текст или None при ошибке
        """
        request_id = f"ygpt_{int(asyncio.get_event_loop().time() * 1000)}"
        logger.info(
            f"[{request_id}] YANDEX_GPT_GENERATION_START: model={model}, temp={temperature}, tokens={max_tokens}"
        )
        logger.debug(
            f"[{request_id}] YANDEX_GPT_PROMPT_LENGTH: {len(prompt)} chars"
        )
        logger.debug(
            f"[{request_id}] YANDEX_GPT_PROMPT: {prompt[:200]}{'...' if len(prompt) > 200 else ''}"
        )
        logger.debug(
            f"[{request_id}] YANDEX_GPT_CONFIG: api_key_exists={bool(self.api_key)}, folder_id={self.folder_id}"
        )

        try:
            # Подготавливаем сообщения
            messages = []

            if system_prompt:
                messages.append(
                    YandexGPTMessage(role="system", text=system_prompt)
                )
                logger.debug(
                    f"[{request_id}] YANDEX_GPT_SYSTEM_PROMPT: {system_prompt[:200]}{'...' if len(system_prompt) > 200 else ''}"
                )

            messages.append(YandexGPTMessage(role="user", text=prompt))

            # Подготавливаем запрос
            model_uri = f"gpt://{self.folder_id}/{model}/latest"
            request_data = YandexGPTRequest(
                modelUri=model_uri,
                completionOptions={
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": str(max_tokens),
                },
                messages=messages,
            )

            logger.info(
                f"[{request_id}] YANDEX_GPT_API_CALL: uri={model_uri}, folder={self.folder_id}"
            )

            # Отправляем запрос
            session = await self._get_session()

            async with session.post(
                self.completion_url, json=request_data.dict()
            ) as response:
                logger.info(
                    f"[{request_id}] YANDEX_GPT_HTTP_STATUS: {response.status}"
                )

                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"[{request_id}] YANDEX_GPT_ERROR {response.status}: {error_text}"
                    )
                    return None

                result = await response.json()
                logger.debug(
                    f"[{request_id}] YANDEX_GPT_RAW_RESPONSE: {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}"
                )

                # Извлекаем текст ответа
                if "result" in result and "alternatives" in result["result"]:
                    alternatives = result["result"]["alternatives"]
                    if alternatives and "message" in alternatives[0]:
                        generated_text = alternatives[0]["message"]["text"]
                        logger.info(
                            f"[{request_id}] YANDEX_GPT_SUCCESS: generated {len(generated_text)} chars"
                        )
                        logger.debug(
                            f"[{request_id}] YANDEX_GPT_TEXT: {generated_text[:200]}{'...' if len(generated_text) > 200 else ''}"
                        )
                        return generated_text

                logger.warning(
                    f"[{request_id}] YANDEX_GPT_UNEXPECTED_FORMAT: {result}"
                )
                return None

        except asyncio.TimeoutError:
            logger.error(f"[{request_id}] YANDEX_GPT_TIMEOUT")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"[{request_id}] YANDEX_GPT_CLIENT_ERROR: {e}")
            return None
        except Exception as e:
            logger.error(f"[{request_id}] YANDEX_GPT_EXCEPTION: {e}")
            return None

    async def generate_horoscope(
        self,
        zodiac_sign: str,
        period: str = "день",
        birth_date: Optional[str] = None,
        forecast_date: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Генерирует персональный гороскоп с помощью Yandex GPT.

        Args:
            zodiac_sign: Знак зодиака
            period: Период (день, неделя, месяц)
            birth_date: Дата рождения
            additional_context: Дополнительный контекст

        Returns:
            Сгенерированный гороскоп или None при ошибке
        """
        system_prompt = """Ты - профессиональный астролог с многолетним опытом. 
Создавай персональные гороскопы, учитывая особенности знаков зодиака, текущие планетарные влияния и лунные фазы.
Твои прогнозы должны быть:
- Позитивными и вдохновляющими
- Конкретными и применимыми в жизни
- Написанными понятным и дружелюбным языком
- Содержать практические советы
- Не превышать 800 символов для голосового интерфейса Alice

Используй русский язык. Избегай слишком сложных терминов."""

        # Подготавливаем промпт
        date_text = period
        if forecast_date:
            date_text = f"{forecast_date}"

        prompt_parts = [
            f"Составь персональный гороскоп для знака {zodiac_sign} на {date_text}."
        ]

        if birth_date:
            prompt_parts.append(f"Дата рождения: {birth_date}")

        if additional_context:
            if "moon_phase" in additional_context:
                prompt_parts.append(
                    f"Текущая фаза Луны: {additional_context['moon_phase']}"
                )

            if "season" in additional_context:
                prompt_parts.append(f"Сезон: {additional_context['season']}")

            if "energy_level" in additional_context:
                prompt_parts.append(
                    f"Уровень энергии: {additional_context['energy_level']}%"
                )

        prompt_parts.extend(
            [
                "Включи:",
                "- Общий прогноз",
                "- Совет для любовных отношений",
                "- Рекомендации для карьеры",
                "- Совет по здоровью",
                "- 2-3 счастливых числа",
                "",
                "Ответ должен быть структурированным и оптимистичным.",
            ]
        )

        prompt = "\n".join(prompt_parts)

        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800,
        )

    async def generate_compatibility_analysis(
        self, sign1: str, sign2: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерирует анализ совместимости знаков зодиака.

        Args:
            sign1: Первый знак зодиака
            sign2: Второй знак зодиака
            context: Дополнительный контекст

        Returns:
            Анализ совместимости или None при ошибке
        """
        system_prompt = """Ты - эксперт по астрологической совместимости.
Анализируй совместимость знаков зодиака с учетом их элементов, качеств и планетарных влияний.
Твой анализ должен быть:
- Сбалансированным (указывай и сильные стороны, и вызовы)
- Конструктивным (давай советы по улучшению отношений)
- Написанным понятным языком
- Не превышать 600 символов для голосового интерфейса

Используй русский язык."""

        prompt_parts = [
            f"Проанализируй совместимость между {sign1} и {sign2}.",
            "",
            "Включи:",
            "- Общую оценку совместимости (в процентах)",
            "- Сильные стороны пары",
            "- Возможные трудности",
            "- Совет для гармоничных отношений",
            "",
            "Будь позитивным, но честным.",
        ]

        if context:
            if "relationship_type" in context:
                prompt_parts.insert(
                    1, f"Тип отношений: {context['relationship_type']}"
                )

        prompt = "\n".join(prompt_parts)

        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=600,
        )

    async def generate_advice(
        self,
        zodiac_sign: str,
        topic: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Генерирует астрологический совет.

        Args:
            zodiac_sign: Знак зодиака
            topic: Тема для совета (любовь, карьера, здоровье, финансы)
            context: Дополнительный контекст

        Returns:
            Астрологический совет или None при ошибке
        """
        system_prompt = """Ты - мудрый астролог-консультант.
Давай практические советы, основанные на астрологических знаниях.
Твои советы должны быть:
- Практичными и применимыми
- Вдохновляющими и поддерживающими
- Краткими (до 300 символов для голосового интерфейса)
- Написанными дружелюбным тоном

Используй русский язык."""

        prompt_parts = [f"Дай астрологический совет для знака {zodiac_sign}"]

        if topic:
            prompt_parts.append(f"по теме '{topic}'")

        if context:
            if "mood" in context:
                prompt_parts.append(f"Настроение: {context['mood']}")
            if "current_challenges" in context:
                prompt_parts.append(
                    f"Текущие вызовы: {context['current_challenges']}"
                )

        prompt_parts.extend(
            [
                "",
                "Совет должен быть мотивирующим и содержать конкретные действия.",
            ]
        )

        prompt = ". ".join(prompt_parts)

        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=300,
        )

    async def generate_natal_chart_interpretation(
        self,
        chart_data: Dict[str, Any],
        arabic_parts: Dict[str, Any],
        focus_area: Optional[str] = None
    ) -> Optional[str]:
        """
        Генерирует интерпретацию натальной карты на основе Kerykeion данных.
        
        Args:
            chart_data: Данные натальной карты от Kerykeion
            arabic_parts: Арабские части
            focus_area: Область фокусировки
            
        Returns:
            AI интерпретация натальной карты
        """
        system_prompt = """Ты — профессиональный астролог с глубокими знаниями западной астрологии.
Интерпретируй натальные карты на основе точных астрологических данных.

Твои интерпретации должны быть:
- Психологически проницательными
- Практически применимыми
- Сбалансированными (сильные стороны и области роста)
- Написанными профессиональным, но доступным языком
- Длиной 600-800 символов для голосового интерфейса

Используй традиционные астрологические принципы."""

        # Extract key elements from chart data
        planets = chart_data.get("planets", {})
        houses = chart_data.get("houses", {})
        angles = chart_data.get("angles", {})
        aspects = chart_data.get("aspects", [])
        dominant_planets = chart_data.get("dominant_planets", [])
        chart_shape = chart_data.get("chart_shape", {})
        
        prompt_parts = ["Интерпретируй натальную карту со следующими данными:"]
        
        # Add planetary positions
        sun = planets.get("sun", {})
        moon = planets.get("moon", {})
        if sun.get("sign") and moon.get("sign"):
            prompt_parts.extend([
                f"Солнце в {sun['sign']} в {sun.get('house', '?')} доме",
                f"Луна в {moon['sign']} в {moon.get('house', '?')} доме"
            ])
        
        # Add ascendant
        ascendant = angles.get("ascendant", {})
        if ascendant.get("sign"):
            prompt_parts.append(f"Асцендент в {ascendant['sign']}")
        
        # Add dominant planets
        if dominant_planets:
            prompt_parts.append(f"Доминирующие планеты: {', '.join(dominant_planets[:3])}")
        
        # Add chart shape
        if chart_shape.get("shape"):
            prompt_parts.append(f"Форма карты: {chart_shape['shape']}")
        
        # Add strongest aspects
        major_aspects = [asp for asp in aspects[:3] if asp.get("strength") in ["Very Strong", "Strong"]]
        if major_aspects:
            prompt_parts.append("Ключевые аспекты:")
            for asp in major_aspects:
                prompt_parts.append(f"- {asp['planet1']} {asp['aspect']} {asp['planet2']}")
        
        # Add Arabic parts if available
        if arabic_parts:
            parts_info = []
            for part_key, part_data in list(arabic_parts.items())[:2]:
                if isinstance(part_data, dict) and part_data.get("name"):
                    parts_info.append(f"- {part_data['name']} в {part_data.get('sign', 'неизвестно')}")
            
            if parts_info:
                prompt_parts.extend(["", "Арабские части:"] + parts_info)
        
        if focus_area:
            prompt_parts.append(f"\nОсобое внимание области: {focus_area}")
        
        prompt_parts.extend([
            "",
            "Создай целостную характеристику включающую:",
            "- Основные черты характера",
            "- Таланты и способности",
            "- Жизненные задачи",
            "- Практические рекомендации"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800
        )

    async def generate_synastry_analysis(
        self,
        person1_chart: Dict[str, Any],
        person2_chart: Dict[str, Any],
        synastry_data: Dict[str, Any],
        relationship_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерирует анализ синастрии на основе астрологических данных.
        
        Args:
            person1_chart: Натальная карта первого человека
            person2_chart: Натальная карта второго человека
            synastry_data: Данные синастрии
            relationship_type: Тип отношений
            context: Дополнительный контекст
            
        Returns:
            AI анализ синастрии
        """
        system_prompt = f"""Ты — эксперт по астрологической совместимости и синастрии.
Анализируй совместимость пар для {relationship_type} отношений на основе точных астрологических расчетов.

Твой анализ должен быть:
- Сбалансированным (плюсы и вызовы)
- Конструктивным (советы для гармонии)
- Психологически глубоким
- Практически применимым
- Длиной 500-700 символов для голосового интерфейса

Используй профессиональную астрологическую терминологию доступно."""

        # Extract luminaries
        person1_sun = person1_chart.get("planets", {}).get("sun", {})
        person1_moon = person1_chart.get("planets", {}).get("moon", {})
        person2_sun = person2_chart.get("planets", {}).get("sun", {})
        person2_moon = person2_chart.get("planets", {}).get("moon", {})
        
        prompt_parts = [
            f"Проанализируй синастрию для {relationship_type} отношений:",
            "",
            f"Партнер 1: Солнце в {person1_sun.get('sign', '?')}, Луна в {person1_moon.get('sign', '?')}",
            f"Партнер 2: Солнце в {person2_sun.get('sign', '?')}, Луна в {person2_moon.get('sign', '?')}"
        ]
        
        # Add overall compatibility score
        overall_score = synastry_data.get("overall_score", 50)
        prompt_parts.append(f"Общая совместимость: {overall_score}%")
        
        # Add significant connections
        sun_moon_connections = synastry_data.get("sun_moon_connections", [])
        if sun_moon_connections:
            prompt_parts.extend([
                "",
                "Связи светил:",
                *[f"- {conn['connection']}: {conn['aspect']}" for conn in sun_moon_connections[:3]]
            ])
        
        venus_mars_connections = synastry_data.get("venus_mars_connections", [])
        if venus_mars_connections:
            prompt_parts.extend([
                "",
                "Романтические связи:",
                *[f"- {conn['connection']}: {conn['aspect']}" for conn in venus_mars_connections[:3]]
            ])
        
        if context and context.get("challenges"):
            prompt_parts.append(f"\nТекущие вызовы: {context['challenges']}")
        
        prompt_parts.extend([
            "",
            "Включи в анализ:",
            "- Общую оценку совместимости",
            "- Сильные стороны союза",
            "- Потенциальные сложности",
            "- Практические советы для гармонии"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=700
        )

    async def generate_transit_forecast(
        self,
        natal_data: Dict[str, Any],
        current_transits: Dict[str, Any],
        period_forecast: Dict[str, Any],
        important_transits: Dict[str, Any],
        focus_area: Optional[str] = None
    ) -> Optional[str]:
        """
        Генерирует прогноз на основе транзитов.
        
        Args:
            natal_data: Натальная карта
            current_transits: Текущие транзиты
            period_forecast: Прогноз на период
            important_transits: Важные транзиты
            focus_area: Область фокусировки
            
        Returns:
            AI прогноз на основе транзитов
        """
        system_prompt = """Ты — опытный астролог-предсказатель, специализирующийся на транзитной астрологии.
Создавай точные прогнозы на основе реальных планетарных влияний.

Твои прогнозы должны быть:
- Основанными на астрологических транзитах
- Практически применимыми
- Сбалансированными (возможности и вызовы)
- Содержащими временные рекомендации
- Длиной 600-800 символов для голосового интерфейса

Используй профессиональную транзитную терминологию доступно."""

        prompt_parts = ["Создай прогноз на основе текущих транзитов:"]
        
        # Add current transits
        if not current_transits.get("error"):
            transits_list = current_transits.get("transits", [])[:3]
            if transits_list:
                prompt_parts.extend([
                    "",
                    "Текущие транзиты:",
                    *[f"- {transit.get('transiting_planet', '?')} {transit.get('aspect', '?')} натальная {transit.get('natal_planet', '?')}" 
                      for transit in transits_list]
                ])
        
        # Add upcoming events
        if period_forecast.get("daily_forecasts"):
            upcoming_events = period_forecast.get("upcoming_key_transits", [])[:2]
            if upcoming_events:
                prompt_parts.extend([
                    "",
                    "Предстоящие ключевые события:",
                    *[f"- {event.get('date', '?')}: {event.get('description', '?')}" 
                      for event in upcoming_events]
                ])
        
        # Add important long-term transits
        if not important_transits.get("error"):
            major_transits = important_transits.get("major_transits", [])[:2]
            if major_transits:
                prompt_parts.extend([
                    "",
                    "Важные долгосрочные влияния:",
                    *[f"- {transit.get('planet', '?')}: {transit.get('description', '?')}" 
                      for transit in major_transits]
                ])
        
        if focus_area:
            prompt_parts.append(f"\nОсобое внимание области: {focus_area}")
        
        prompt_parts.extend([
            "",
            "Создай прогноз включающий:",
            "- Общую энергетику периода",
            "- Ключевые возможности и вызовы",
            "- Рекомендации по планированию",
            "- Оптимальное время для решений"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800
        )

    async def generate_specialized_consultation(
        self,
        zodiac_sign: str,
        consultation_type: str,
        context: Dict[str, Any],
        natal_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерирует специализированную консультацию.
        
        Args:
            zodiac_sign: Знак зодиака
            consultation_type: Тип консультации
            context: Контекст консультации
            natal_data: Данные натальной карты (опционально)
            
        Returns:
            Специализированная консультация
        """
        consultation_configs = {
            "career_guidance": {
                "system": "Ты — астролог-консультант по карьере, помогающий найти профессиональное призвание.",
                "focus": "карьерные возможности, профессиональные таланты, призвание"
            },
            "love_analysis": {
                "system": "Ты — эксперт по астрологии любви и отношений.",
                "focus": "любовные перспективы, привлечение партнера, гармония в отношениях"
            },
            "health_advice": {
                "system": "Ты — астро-консультант по здоровью и жизненной энергии.",
                "focus": "здоровье, жизненная энергия, профилактика, восстановление"
            },
            "financial_guidance": {
                "system": "Ты — астролог-консультант по финансовым вопросам.",
                "focus": "финансовые возможности, денежные потоки, инвестиции"
            },
            "spiritual_guidance": {
                "system": "Ты — духовный астролог, помогающий в личностном росте.",
                "focus": "духовное развитие, жизненные уроки, кармические задачи"
            }
        }
        
        config = consultation_configs.get(
            consultation_type, 
            {
                "system": "Ты — профессиональный астролог-консультант.",
                "focus": "общие жизненные вопросы"
            }
        )
        
        system_prompt = f"""{config['system']}
Давай практические советы на основе астрологических принципов.

Твои советы должны быть:
- Конкретными и применимыми
- Основанными на астрологии
- Вдохновляющими и поддерживающими
- Учитывающими текущие влияния
- Длиной 400-500 символов для голосового интерфейса"""

        prompt_parts = [
            f"Дай астрологический совет для {zodiac_sign}",
            f"по теме: {config['focus']}"
        ]
        
        # Add natal chart context if available
        if natal_data and not natal_data.get("error"):
            sun = natal_data.get("planets", {}).get("sun", {})
            moon = natal_data.get("planets", {}).get("moon", {})
            if sun.get("sign") and moon.get("sign"):
                prompt_parts.append(f"Натальная карта: Солнце в {sun['sign']}, Луна в {moon['sign']}")
        
        # Add user context
        user_context = context.get("user_context", {})
        if user_context.get("mood"):
            prompt_parts.append(f"Настроение: {user_context['mood']}")
        if user_context.get("challenges"):
            prompt_parts.append(f"Текущие вызовы: {user_context['challenges']}")
        if user_context.get("focus_area"):
            prompt_parts.append(f"Фокус: {user_context['focus_area']}")
        
        prompt_parts.extend([
            "",
            "Совет должен содержать:",
            "- Астрологическое обоснование",
            "- Конкретные действия",
            "- Оптимальное время",
            "- Поддерживающие слова"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=500
        )

    async def is_available(self) -> bool:
        """
        Проверяет доступность Yandex GPT API.

        Returns:
            True если API доступен, False иначе
        """
        if not self.api_key or not self.folder_id:
            logger.warning("Yandex GPT credentials not configured")
            return False

        try:
            # Простая проверка с коротким запросом
            result = await self.generate_text(
                prompt="Привет", temperature=0.1, max_tokens=10
            )
            return result is not None
        except Exception as e:
            logger.error(f"Yandex GPT availability check failed: {e}")
            return False


# Глобальный экземпляр клиента
yandex_gpt_client = YandexGPTClient()
