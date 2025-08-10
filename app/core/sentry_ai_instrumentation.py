"""
Sentry AI Agents инструментация для астрологического приложения.
Реализация согласно https://docs.sentry.io/platforms/python/tracing/instrumentation/custom-instrumentation/ai-agents-module/
"""

import json
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from sentry_sdk import start_span

from .config import settings

# ==================== AI AGENT SPANS ====================


@contextmanager
def trace_ai_agent(
    agent_name: str,
    model_name: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    **agent_metadata,
):
    """
    Трейс для выполнения AI агента (Invoke Agent Span).

    Args:
        agent_name: Название AI агента
        model_name: Модель ИИ (например, "yandex-gpt-lite")
        input_data: Входные данные для агента
        **agent_metadata: Дополнительные метаданные
    """
    with start_span(
        op="gen_ai.invoke_agent", description=f"AI Agent: {agent_name}"
    ) as span:
        # Базовые атрибуты AI агента
        span.set_tag("ai.agent.name", agent_name)
        span.set_tag("ai.model.provider", "yandex")

        if model_name:
            span.set_tag("ai.model.name", model_name)

        # Дополнительные метаданные
        for key, value in agent_metadata.items():
            span.set_tag(f"ai.agent.{key}", str(value))

        # Входные данные (JSON-stringified для сложных объектов)
        if input_data:
            span.set_data(
                "ai.agent.input", json.dumps(input_data, ensure_ascii=False)
            )

        span.set_tag("ai.domain", "astrology")
        span.set_tag("ai.operation_type", "consultation")

        try:
            start_time = time.time()

            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("ai.agent.duration_ms", duration_ms)
            span.set_tag("ai.agent.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("ai.agent.duration_ms", duration_ms)
            span.set_tag("ai.agent.status", "error")
            span.set_tag("ai.agent.error_type", type(e).__name__)
            span.set_data("ai.agent.error_message", str(e))
            raise


@contextmanager
def trace_ai_client(
    operation: str,
    model_name: str,
    messages: Optional[List[Dict[str, str]]] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **client_params,
):
    """
    Трейс для взаимодействия с AI клиентом (AI Client Span).

    Args:
        operation: Тип операции ("chat", "completion", etc.)
        model_name: Название модели
        messages: Сообщения для обработки
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        **client_params: Дополнительные параметры клиента
    """
    with start_span(
        op=f"gen_ai.{operation}", description=f"AI Client: {model_name}"
    ) as span:
        # Базовые атрибуты AI клиента
        span.set_tag("ai.model.provider", "yandex")
        span.set_tag("ai.model.name", model_name)
        span.set_tag("ai.operation", operation)

        # Параметры модели
        if temperature is not None:
            span.set_data("ai.model.temperature", temperature)
        if max_tokens is not None:
            span.set_data("ai.model.max_tokens", max_tokens)

        # Сообщения (обрезаем для безопасности)
        if messages:
            safe_messages = []
            for msg in messages[:3]:  # Только первые 3 сообщения
                safe_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")[:200] + "..."
                    if len(msg.get("content", "")) > 200
                    else msg.get("content", ""),
                }
                safe_messages.append(safe_msg)

            span.set_data(
                "ai.messages", json.dumps(safe_messages, ensure_ascii=False)
            )
            span.set_data("ai.messages.count", len(messages))

        # Дополнительные параметры
        for key, value in client_params.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_data(f"ai.client.{key}", value)

        span.set_tag("ai.domain", "astrology")

        try:
            start_time = time.time()

            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("ai.client.duration_ms", duration_ms)
            span.set_tag("ai.client.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("ai.client.duration_ms", duration_ms)
            span.set_tag("ai.client.status", "error")
            span.set_tag("ai.client.error_type", type(e).__name__)
            span.set_data("ai.client.error_message", str(e))
            raise


@contextmanager
def trace_ai_tool_execution(
    tool_name: str,
    tool_input: Optional[Dict[str, Any]] = None,
    **tool_metadata,
):
    """
    Трейс для выполнения AI инструмента (Execute Tool Span).

    Args:
        tool_name: Название инструмента
        tool_input: Входные данные для инструмента
        **tool_metadata: Метаданные инструмента
    """
    with start_span(
        op="gen_ai.execute_tool", description=f"AI Tool: {tool_name}"
    ) as span:
        # Базовые атрибуты инструмента
        span.set_tag("ai.tool.name", tool_name)
        span.set_tag("ai.tool.domain", "astrology")

        # Входные данные
        if tool_input:
            # Безопасное логирование (убираем персональные данные)
            safe_input = {}
            for key, value in tool_input.items():
                if key not in [
                    "birth_time",
                    "birth_place",
                    "user_id",
                    "session_id",
                ]:
                    safe_input[key] = value
                else:
                    safe_input[key] = "[FILTERED]"

            span.set_data(
                "ai.tool.input", json.dumps(safe_input, ensure_ascii=False)
            )

        # Метаданные инструмента
        for key, value in tool_metadata.items():
            span.set_tag(f"ai.tool.{key}", str(value))

        try:
            start_time = time.time()

            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("ai.tool.duration_ms", duration_ms)
            span.set_tag("ai.tool.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("ai.tool.duration_ms", duration_ms)
            span.set_tag("ai.tool.status", "error")
            span.set_tag("ai.tool.error_type", type(e).__name__)
            span.set_data("ai.tool.error_message", str(e))
            raise


# ==================== АСТРОЛОГИЧЕСКИЕ AI ОПЕРАЦИИ ====================


@contextmanager
def trace_horoscope_ai_generation(
    zodiac_sign: str,
    period: str = "daily",
    ai_model: str = "yandex-gpt-lite",
    **generation_params,
):
    """
    Специализированный трейс для AI генерации гороскопов.

    Args:
        zodiac_sign: Знак зодиака
        period: Период (daily, weekly, monthly)
        ai_model: AI модель
        **generation_params: Параметры генерации
    """
    with trace_ai_agent(
        agent_name="horoscope_generator",
        model_name=ai_model,
        input_data={
            "zodiac_sign": zodiac_sign,
            "period": period,
            **generation_params,
        },
        operation_type="horoscope_generation",
        domain="astrology",
    ) as span:
        # Специфичные для гороскопа теги
        span.set_tag("astro.zodiac_sign", zodiac_sign)
        span.set_tag("astro.period", period)
        span.set_tag("astro.generation_type", "ai_powered")

        yield span


@contextmanager
def trace_compatibility_ai_analysis(
    sign1: str,
    sign2: str,
    analysis_type: str = "romantic",
    ai_model: str = "yandex-gpt-lite",
):
    """
    AI трейс для анализа совместимости знаков зодиака.

    Args:
        sign1: Первый знак зодиака
        sign2: Второй знак зодиака
        analysis_type: Тип анализа (romantic, friendship, business)
        ai_model: AI модель
    """
    with trace_ai_agent(
        agent_name="compatibility_analyzer",
        model_name=ai_model,
        input_data={
            "zodiac_sign_1": sign1,
            "zodiac_sign_2": sign2,
            "analysis_type": analysis_type,
        },
        operation_type="compatibility_analysis",
        domain="astrology",
    ) as span:
        # Теги совместимости
        span.set_tag("astro.compatibility.sign1", sign1)
        span.set_tag("astro.compatibility.sign2", sign2)
        span.set_tag("astro.compatibility.type", analysis_type)

        yield span


@contextmanager
def trace_natal_chart_ai_interpretation(
    birth_data: Dict[str, Any],
    interpretation_focus: str = "general",
    ai_model: str = "yandex-gpt-lite",
):
    """
    AI трейс для интерпретации натальной карты.

    Args:
        birth_data: Данные рождения (без персональной информации)
        interpretation_focus: Фокус интерпретации
        ai_model: AI модель
    """
    # Фильтруем персональные данные
    safe_birth_data = {
        "zodiac_sign": birth_data.get("zodiac_sign"),
        "ascendant": birth_data.get("ascendant"),
        "moon_sign": birth_data.get("moon_sign"),
        "houses": birth_data.get("houses", []),
    }

    with trace_ai_agent(
        agent_name="natal_chart_interpreter",
        model_name=ai_model,
        input_data={
            "birth_data": safe_birth_data,
            "focus": interpretation_focus,
        },
        operation_type="natal_chart_interpretation",
        domain="astrology",
    ) as span:
        # Теги натальной карты
        if "zodiac_sign" in safe_birth_data:
            span.set_tag(
                "astro.natal.sun_sign", safe_birth_data["zodiac_sign"]
            )
        if "ascendant" in safe_birth_data:
            span.set_tag("astro.natal.ascendant", safe_birth_data["ascendant"])
        if "moon_sign" in safe_birth_data:
            span.set_tag("astro.natal.moon_sign", safe_birth_data["moon_sign"])

        span.set_tag("astro.natal.focus", interpretation_focus)

        yield span


# ==================== AI UTILITY FUNCTIONS ====================


def track_ai_token_usage(
    span: Any,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
):
    """
    Добавляет информацию об использовании токенов к спану.

    Args:
        span: Активный Sentry спан
        prompt_tokens: Количество токенов в промпте
        completion_tokens: Количество токенов в ответе
        total_tokens: Общее количество токенов
    """
    if prompt_tokens is not None:
        span.set_data("ai.tokens.prompt", prompt_tokens)
    if completion_tokens is not None:
        span.set_data("ai.tokens.completion", completion_tokens)
    if total_tokens is not None:
        span.set_data("ai.tokens.total", total_tokens)

    # Расчет примерной стоимости (если известно)
    if total_tokens and hasattr(settings, "AI_COST_PER_1K_TOKENS"):
        estimated_cost = (total_tokens / 1000) * settings.AI_COST_PER_1K_TOKENS
        span.set_data("ai.estimated_cost_usd", round(estimated_cost, 6))


def track_ai_response_quality(
    span: Any,
    response_length: Optional[int] = None,
    confidence_score: Optional[float] = None,
    **quality_metrics,
):
    """
    Отслеживает качество AI ответа.

    Args:
        span: Активный Sentry спан
        response_length: Длина ответа в символах
        confidence_score: Оценка уверенности (0.0-1.0)
        **quality_metrics: Дополнительные метрики качества
    """
    if response_length is not None:
        span.set_data("ai.response.length", response_length)
    if confidence_score is not None:
        span.set_data("ai.response.confidence", confidence_score)

    # Дополнительные метрики
    for metric, value in quality_metrics.items():
        if isinstance(value, (int, float, str, bool)):
            span.set_data(f"ai.quality.{metric}", value)


# ==================== USAGE EXAMPLES ====================


"""
Примеры использования AI инструментации:

1. Генерация гороскопа с AI:

    async def generate_ai_horoscope(zodiac_sign: str):
        with trace_horoscope_ai_generation(
            zodiac_sign=zodiac_sign,
            period="daily",
            ai_model="yandex-gpt-lite"
        ) as span:
            # AI клиент для генерации
            with trace_ai_client(
                operation="chat",
                model_name="yandex-gpt-lite", 
                messages=[{"role": "user", "content": f"Гороскоп для {zodiac_sign}"}],
                temperature=0.7,
                max_tokens=500
            ) as client_span:
                response = await ai_client.generate(...)
                
                # Отслеживание токенов
                track_ai_token_usage(
                    client_span,
                    prompt_tokens=50,
                    completion_tokens=200,
                    total_tokens=250
                )
                
                # Качество ответа
                track_ai_response_quality(
                    client_span,
                    response_length=len(response),
                    confidence_score=0.9
                )
            
            return response

2. Анализ совместимости:

    async def analyze_compatibility_ai(sign1: str, sign2: str):
        with trace_compatibility_ai_analysis(sign1, sign2, "romantic") as span:
            result = await compatibility_service.analyze(sign1, sign2)
            return result

3. Использование астрологических инструментов:

    async def calculate_planetary_positions(birth_data: dict):
        with trace_ai_tool_execution(
            tool_name="planetary_calculator",
            tool_input=birth_data,
            calculation_method="kerykeion"
        ) as span:
            positions = await astro_calculator.calculate_planets(birth_data)
            return positions
"""
