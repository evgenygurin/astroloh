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
                }
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
        model: str = "yandexgpt-lite"
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
        try:
            # Подготавливаем сообщения
            messages = []
            
            if system_prompt:
                messages.append(YandexGPTMessage(
                    role="system",
                    text=system_prompt
                ))
            
            messages.append(YandexGPTMessage(
                role="user", 
                text=prompt
            ))
            
            # Подготавливаем запрос
            request_data = YandexGPTRequest(
                modelUri=f"gpt://{self.folder_id}/{model}/latest",
                completionOptions={
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": str(max_tokens)
                },
                messages=messages
            )
            
            # Отправляем запрос
            session = await self._get_session()
            
            async with session.post(
                self.completion_url,
                json=request_data.dict()
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Yandex GPT API error {response.status}: {error_text}")
                    return None
                
                result = await response.json()
                
                # Извлекаем текст ответа
                if "result" in result and "alternatives" in result["result"]:
                    alternatives = result["result"]["alternatives"]
                    if alternatives and "message" in alternatives[0]:
                        return alternatives[0]["message"]["text"]
                
                logger.warning(f"Unexpected Yandex GPT response format: {result}")
                return None
                
        except asyncio.TimeoutError:
            logger.error("Yandex GPT API timeout")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Yandex GPT API client error: {e}")
            return None
        except Exception as e:
            logger.error(f"Yandex GPT API error: {e}")
            return None
    
    async def generate_horoscope(
        self,
        zodiac_sign: str,
        period: str = "день",
        birth_date: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
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
        prompt_parts = [
            f"Составь персональный гороскоп для знака {zodiac_sign} на {period}."
        ]
        
        if birth_date:
            prompt_parts.append(f"Дата рождения: {birth_date}")
        
        if additional_context:
            if "moon_phase" in additional_context:
                prompt_parts.append(f"Текущая фаза Луны: {additional_context['moon_phase']}")
            
            if "season" in additional_context:
                prompt_parts.append(f"Сезон: {additional_context['season']}")
            
            if "energy_level" in additional_context:
                prompt_parts.append(f"Уровень энергии: {additional_context['energy_level']}%")
        
        prompt_parts.extend([
            "Включи:",
            "- Общий прогноз",
            "- Совет для любовных отношений", 
            "- Рекомендации для карьеры",
            "- Совет по здоровью",
            "- 2-3 счастливых числа",
            "",
            "Ответ должен быть структурированным и оптимистичным."
        ])
        
        prompt = "\n".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800
        )
    
    async def generate_compatibility_analysis(
        self,
        sign1: str,
        sign2: str,
        context: Optional[Dict[str, Any]] = None
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
            "Будь позитивным, но честным."
        ]
        
        if context:
            if "relationship_type" in context:
                prompt_parts.insert(1, f"Тип отношений: {context['relationship_type']}")
        
        prompt = "\n".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=600
        )
    
    async def generate_advice(
        self,
        zodiac_sign: str,
        topic: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
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
                prompt_parts.append(f"Текущие вызовы: {context['current_challenges']}")
        
        prompt_parts.extend([
            "",
            "Совет должен быть мотивирующим и содержать конкретные действия."
        ])
        
        prompt = ". ".join(prompt_parts)
        
        return await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=300
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
                prompt="Привет",
                temperature=0.1,
                max_tokens=10
            )
            return result is not None
        except Exception as e:
            logger.error(f"Yandex GPT availability check failed: {e}")
            return False


# Глобальный экземпляр клиента
yandex_gpt_client = YandexGPTClient()