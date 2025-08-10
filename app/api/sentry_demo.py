"""
Демонстрационный эндпоинт для тестирования всех функций Sentry.
"""

import asyncio
import random
import time
from typing import Optional

import sentry_sdk
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.sentry import (
    capture_alice_context,
    capture_astrology_context,
    capture_astrology_log,
    capture_business_metric,
    capture_business_warning,
    capture_custom_metric,
    capture_distribution_metric,
    capture_performance_warning,
    capture_structured_log,
    sentry_span,
    sentry_trace,
)

router = APIRouter(prefix="/api/sentry-demo", tags=["Sentry Demo"])


class SentryTestRequest(BaseModel):
    """Запрос для тестирования Sentry"""

    test_type: str = "all"  # all, logs, metrics, warnings, traces, profiling
    zodiac_sign: Optional[str] = "leo"
    simulate_error: bool = False
    simulate_slow: bool = False
    duration_ms: Optional[int] = None


@router.post("/test-all")
async def test_all_sentry_features(request: SentryTestRequest):
    """
    Тестирует все функции Sentry:
    - Logs (логи)
    - Metrics (метрики)
    - Warnings (предупреждения)
    - Traces (трассировки)
    - Profiling (профилирование)
    """

    results = {}

    # 🔥 TRACES - Начинаем основную трассировку
    with sentry_trace(
        "sentry_demo_test",
        test_type=request.test_type,
        zodiac_sign=request.zodiac_sign,
    ):
        # ==================== 1. LOGS ====================
        if request.test_type in ["all", "logs"]:
            with sentry_span("test_logs", feature="logs"):
                # Структурированный лог
                capture_structured_log(
                    level="info",
                    message="📝 Тестирование Sentry Logs",
                    extra_data={
                        "test_id": time.time(),
                        "zodiac_sign": request.zodiac_sign,
                        "feature": "logs",
                    },
                    tags={"test": "sentry_demo", "feature": "logs"},
                )

                # Астрологический лог
                capture_astrology_log(
                    operation="test_horoscope",
                    message=f"🌟 Генерация тестового гороскопа для {request.zodiac_sign}",
                    level="info",
                    zodiac_sign=request.zodiac_sign,
                    backend="kerykeion",
                    accuracy=95.5,
                    cache_hit=False,
                )

                results["logs"] = "✅ Logs отправлены"

        # ==================== 2. METRICS ====================
        if request.test_type in ["all", "metrics"]:
            with sentry_span("test_metrics", feature="metrics"):
                # Кастомная метрика
                capture_custom_metric(
                    key="sentry_demo.test_count",
                    value=1,
                    unit="count",
                    tags={"zodiac_sign": request.zodiac_sign},
                )

                # Distribution метрика
                test_duration = request.duration_ms or random.randint(100, 500)
                capture_distribution_metric(
                    key="sentry_demo.response_time",
                    value=test_duration,
                    unit="millisecond",
                    tags={
                        "endpoint": "test",
                        "zodiac_sign": request.zodiac_sign,
                    },
                )

                # Бизнес-метрика
                capture_business_metric(
                    operation="horoscope_test",
                    zodiac_sign=request.zodiac_sign,
                    ai_used=True,
                    cache_hit=False,
                    duration_ms=test_duration,
                )

                results[
                    "metrics"
                ] = f"✅ Metrics отправлены (duration: {test_duration}ms)"

        # ==================== 3. WARNINGS ====================
        if request.test_type in ["all", "warnings"]:
            with sentry_span("test_warnings", feature="warnings"):
                # Performance warning
                if request.simulate_slow:
                    actual_duration = 3000
                    threshold = 1000
                    capture_performance_warning(
                        operation="slow_horoscope_generation",
                        actual_duration_ms=actual_duration,
                        threshold_ms=threshold,
                        additional_context={
                            "zodiac_sign": request.zodiac_sign,
                            "backend": "kerykeion",
                            "reason": "complex_calculations",
                        },
                    )
                    results[
                        "warnings"
                    ] = f"⚠️ Performance warning: {actual_duration}ms > {threshold}ms"

                # Business warning
                capture_business_warning(
                    warning_type="fallback_used",
                    message=f"🔄 Использован fallback для {request.zodiac_sign} из-за недоступности AI",
                    severity="medium",
                    additional_data={
                        "zodiac_sign": request.zodiac_sign,
                        "original_backend": "yandex_gpt",
                        "fallback_backend": "traditional",
                    },
                )

                if not request.simulate_slow:
                    results["warnings"] = "✅ Business warnings отправлены"

        # ==================== 4. TRACES ====================
        if request.test_type in ["all", "traces"]:
            with sentry_span("test_traces", feature="traces"):
                # Добавляем контекст
                capture_astrology_context(
                    operation="trace_test",
                    zodiac_sign=request.zodiac_sign,
                    calculation_backend="kerykeion",
                    ai_enabled=True,
                    natal_chart=True,
                )

                capture_alice_context(
                    intent="horoscope_request",
                    user_utterance="дай гороскоп для льва",
                    session_id="test_session_123",
                    response_type="text_with_buttons",
                )

                # Симулируем вложенные операции
                with sentry_span("database_query", db="postgresql"):
                    await asyncio.sleep(0.05)  # Симуляция DB запроса

                with sentry_span("cache_check", cache="redis"):
                    await asyncio.sleep(0.02)  # Симуляция проверки кэша

                with sentry_span("ai_generation", backend="yandex_gpt"):
                    await asyncio.sleep(0.1)  # Симуляция AI генерации

                results["traces"] = "✅ Traces с вложенными spans созданы"

        # ==================== 5. PROFILING ====================
        if request.test_type in ["all", "profiling"]:
            with sentry_span("test_profiling", feature="profiling"):
                # CPU-интенсивная операция для профилирования
                def fibonacci(n):
                    if n <= 1:
                        return n
                    return fibonacci(n - 1) + fibonacci(n - 2)

                # Профилируемая операция
                with sentry_sdk.start_span(
                    op="cpu_intensive", description="fibonacci_calculation"
                ):
                    result = fibonacci(20)  # Достаточно для профилирования

                results[
                    "profiling"
                ] = f"✅ Profiling выполнен (fibonacci(20) = {result})"

        # ==================== 6. ERRORS (опционально) ====================
        if request.simulate_error:
            with sentry_span("test_error", feature="error"):
                try:
                    # Симулируем ошибку
                    raise ValueError(
                        f"🔥 Тестовая ошибка для {request.zodiac_sign}"
                    )
                except ValueError as e:
                    sentry_sdk.capture_exception(e)
                    results[
                        "error"
                    ] = f"❌ Ошибка отправлена в Sentry: {str(e)}"

    # Итоговый результат
    return {
        "status": "success",
        "message": "✅ Sentry функции протестированы",
        "results": results,
        "request": request.dict(),
        "sentry_features": {
            "logs": "📝 Структурированные логи с контекстом",
            "metrics": "📊 Кастомные и бизнес-метрики",
            "warnings": "⚠️ Performance и business предупреждения",
            "traces": "🔥 Распределенная трассировка со spans",
            "profiling": "📈 CPU профилирование",
        },
    }


@router.get("/test-metrics-breach")
async def test_metrics_breach():
    """
    Тестирует превышение метрик (Breached Metrics).
    Симулирует медленную операцию для срабатывания алертов.
    """

    # Обертываем в трассировку
    with sentry_trace("metrics_breach_test", test_type="breach"):
        # Устанавливаем пороги
        thresholds = {
            "response_time": 500,  # ms
            "memory_usage": 100,  # MB
            "error_rate": 0.05,  # 5%
        }

        # Симулируем медленную операцию
        start_time = time.time()
        await asyncio.sleep(0.8)  # 800ms - превышает порог
        duration_ms = (time.time() - start_time) * 1000

        # Отправляем метрику превышения
        if duration_ms > thresholds["response_time"]:
            capture_performance_warning(
                operation="metrics_breach_test",
                actual_duration_ms=duration_ms,
                threshold_ms=thresholds["response_time"],
                additional_context={
                    "severity": "high",
                    "action_required": "optimize_query",
                    "affected_users": 100,
                },
            )

            # Отправляем alert метрику
            capture_custom_metric(
                key="sentry_demo.threshold_breach",
                value=1,
                unit="count",
                tags={"metric": "response_time", "severity": "high"},
            )

        return {
            "status": "breach_detected",
            "metric": "response_time",
            "actual": f"{duration_ms:.0f}ms",
            "threshold": f"{thresholds['response_time']}ms",
            "breach_ratio": duration_ms / thresholds["response_time"],
            "alert_sent": True,
        }


@router.get("/test-continuous-monitoring")
async def test_continuous_monitoring():
    """
    Запускает непрерывный мониторинг с периодической отправкой метрик.
    """

    monitoring_data = []

    for i in range(5):
        iteration_data = {"iteration": i + 1, "timestamp": time.time()}

        # Симулируем различные метрики
        cpu_usage = random.uniform(20, 80)
        memory_usage = random.uniform(50, 150)
        request_count = random.randint(10, 100)
        error_count = random.randint(0, 5)

        # Отправляем метрики
        capture_custom_metric(
            key="sentry_demo.cpu_usage",
            value=cpu_usage,
            unit="percent",
            tags={"iteration": str(i + 1)},
        )

        capture_custom_metric(
            key="sentry_demo.memory_usage",
            value=memory_usage,
            unit="megabyte",
            tags={"iteration": str(i + 1)},
        )

        capture_custom_metric(
            key="sentry_demo.request_count",
            value=request_count,
            unit="count",
            tags={"iteration": str(i + 1)},
        )

        if error_count > 0:
            capture_custom_metric(
                key="sentry_demo.error_count",
                value=error_count,
                unit="count",
                tags={"iteration": str(i + 1), "severity": "medium"},
            )

        iteration_data.update(
            {
                "cpu_usage": f"{cpu_usage:.1f}%",
                "memory_usage": f"{memory_usage:.1f}MB",
                "request_count": request_count,
                "error_count": error_count,
            }
        )

        monitoring_data.append(iteration_data)

        # Проверяем на превышения
        if cpu_usage > 70:
            capture_business_warning(
                warning_type="high_cpu_usage",
                message=f"⚠️ Высокая загрузка CPU: {cpu_usage:.1f}%",
                severity="high",
                additional_data={"cpu_usage": cpu_usage, "iteration": i + 1},
            )

        await asyncio.sleep(0.5)  # Пауза между итерациями

    return {
        "status": "monitoring_complete",
        "iterations": 5,
        "monitoring_data": monitoring_data,
        "metrics_sent": [
            "cpu_usage",
            "memory_usage",
            "request_count",
            "error_count",
        ],
    }


@router.get("/health")
async def sentry_demo_health():
    """Проверка здоровья Sentry Demo API."""
    return {
        "status": "healthy",
        "service": "sentry_demo",
        "features": ["logs", "metrics", "warnings", "traces", "profiling"],
        "endpoints": [
            "/api/sentry-demo/test-all",
            "/api/sentry-demo/test-metrics-breach",
            "/api/sentry-demo/test-continuous-monitoring",
        ],
    }
