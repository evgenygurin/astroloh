"""
Sentry инициализация и настройка расширенного мониторинга.
Поддержка: Logs, Metrics, Warnings, Traces, Profiling
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union

import sentry_sdk
from sentry_sdk import metrics
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from .config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Инициализация Sentry для мониторинга ошибок и производительности.
    """
    if not settings.SENTRY_DSN:
        logger.info("🔍 Sentry DSN не настроен, мониторинг отключен")
        return

    # Настройка интеграций
    integrations = [
        # FastAPI интеграция (без параметров для совместимости)
        FastApiIntegration(),
        # Starlette интеграция для middleware
        StarletteIntegration(),
        # HTTP клиент интеграция (для Yandex API)
        HttpxIntegration(),
        # Async интеграция
        AsyncioIntegration(),
        # SQL интеграция для PostgreSQL
        SqlalchemyIntegration(),
        # Redis интеграция для кэширования
        RedisIntegration(),
        # Расширенная logging интеграция
        LoggingIntegration(
            level=logging.INFO,  # Минимальный уровень для breadcrumb
            event_level=logging.ERROR,  # Минимальный уровень для событий
        ),
    ]

    # Инициализация Sentry с расширенными настройками
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            release=settings.SENTRY_RELEASE,
            integrations=integrations,
            # 🔥 TRACES & PROFILING
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            enable_tracing=True,
            # 📊 METRICS
            _experiments={
                "enable_metrics": True,
                "enable_metrics_summaries": True,
            },
            # 📝 LOGS
            auto_enabling_integrations=False,  # Отключаем авто-интеграции
            max_breadcrumbs=100,  # Увеличиваем количество breadcrumbs
            # 🛡️ SECURITY
            send_default_pii=False,  # Не отправляем персональные данные
            attach_stacktrace=True,
            debug=False,
            # 🎯 FILTERING
            before_send=filter_sensitive_data,
            before_send_transaction=filter_transaction_data,
            before_breadcrumb=filter_breadcrumb_data,
            # 📈 PERFORMANCE
            max_request_body_size="medium",  # medium = 10KB
            request_bodies="medium",
            with_locals=False,  # Отключаем локальные переменные в трассировке
        )
        logger.info(
            "🚀 Sentry успешно инициализирован для среды: %s",
            settings.SENTRY_ENVIRONMENT,
        )
    except Exception as e:
        logger.error("❌ Ошибка инициализации Sentry: %s", str(e))
        logger.warning("⚠️ Продолжаем работу без Sentry мониторинга")


def filter_sensitive_data(
    event: Dict[str, Any], hint: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Фильтрация чувствительных данных перед отправкой в Sentry.

    Args:
        event: Событие Sentry
        hint: Дополнительная информация о событии

    Returns:
        Отфильтрованное событие или None если событие нужно пропустить
    """
    # Удаляем чувствительные данные из запросов
    if "request" in event:
        request_data = event["request"]

        # Удаляем токены и ключи API
        sensitive_headers = [
            "authorization",
            "x-api-key",
            "yandex-api-key",
            "cookie",
            "x-session-id",
        ]

        if "headers" in request_data:
            for header in sensitive_headers:
                if header in request_data["headers"]:
                    request_data["headers"][header] = "[Filtered]"

        # Фильтруем данные формы и JSON
        if "data" in request_data:
            data = request_data["data"]
            if isinstance(data, dict):
                sensitive_fields = [
                    "password",
                    "token",
                    "secret",
                    "key",
                    "birth_time",
                    "birth_place",
                    "user_id",
                ]
                for field in sensitive_fields:
                    if field in data:
                        data[field] = "[Filtered]"

    # Добавляем контекст астрологического приложения
    event.setdefault("tags", {}).update(
        {
            "application": "astroloh",
            "service": "yandex_alice",
        }
    )

    # Добавляем пользовательский контекст для астрологии
    if "user" in event:
        user_data = event["user"]
        # Убираем персональные данные, оставляем только идентификатор сессии
        if "id" in user_data and len(str(user_data["id"])) > 10:
            user_data["id"] = f"session_{hash(str(user_data['id'])) % 10000}"

    return event


def filter_breadcrumb_data(
    crumb: Dict[str, Any], hint: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Фильтрация breadcrumbs для логов.

    Args:
        crumb: Breadcrumb данные
        hint: Дополнительная информация

    Returns:
        Отфильтрованный breadcrumb или None если нужно пропустить
    """
    # Пропускаем некритические SQL запросы
    if crumb.get("category") == "query" and "SELECT" in str(
        crumb.get("message", "")
    ):
        return None

    # Фильтруем чувствительные HTTP заголовки
    if crumb.get("category") == "httplib" and "data" in crumb:
        data = crumb["data"]
        if "headers" in data:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in data["headers"]:
                    data["headers"][header] = "[Filtered]"

    # Добавляем контекст для астрологических операций
    if crumb.get("category") == "console" and crumb.get("level") == "info":
        message = str(crumb.get("message", ""))
        if any(
            keyword in message.lower()
            for keyword in ["kerykeion", "horoscope", "compatibility", "lunar"]
        ):
            crumb["data"] = crumb.get("data", {})
            crumb["data"]["astro_operation"] = True

    return crumb


def filter_transaction_data(
    event: Dict[str, Any], hint: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Фильтрация данных транзакций для производительности.

    Args:
        event: Событие транзакции
        hint: Дополнительная информация

    Returns:
        Отфильтрованное событие
    """
    # Добавляем теги для транзакций
    event.setdefault("tags", {}).update(
        {
            "service_type": "astrology_api",
            "integration": "yandex_alice",
        }
    )

    # Классифицируем типы операций
    transaction_name = event.get("transaction", "")
    if "horoscope" in transaction_name.lower():
        event["tags"]["operation_type"] = "horoscope_generation"
    elif "compatibility" in transaction_name.lower():
        event["tags"]["operation_type"] = "compatibility_analysis"
    elif "natal" in transaction_name.lower():
        event["tags"]["operation_type"] = "natal_chart"
    elif "yandex" in transaction_name.lower():
        event["tags"]["operation_type"] = "alice_webhook"

    return event


def capture_astrology_context(
    operation: str,
    zodiac_sign: str = None,
    calculation_backend: str = None,
    ai_enabled: bool = False,
    **kwargs,
) -> None:
    """
    Добавление астрологического контекста в Sentry.

    Args:
        operation: Тип астрологической операции
        zodiac_sign: Знак зодиака
        calculation_backend: Бэкенд для расчетов (kerykeion, skyfield, etc.)
        ai_enabled: Использование AI для генерации
        **kwargs: Дополнительные параметры
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("astro.operation", operation)

        if zodiac_sign:
            scope.set_tag("astro.zodiac_sign", zodiac_sign)

        if calculation_backend:
            scope.set_tag("astro.backend", calculation_backend)

        scope.set_tag("astro.ai_enabled", ai_enabled)

        # Добавляем дополнительный контекст
        scope.set_context(
            "astrology",
            {
                "operation": operation,
                "backend": calculation_backend,
                "ai_generation": ai_enabled,
                **kwargs,
            },
        )


def capture_alice_context(
    intent: str,
    user_utterance: str = None,
    session_id: str = None,
    response_type: str = None,
) -> None:
    """
    Добавление контекста Yandex Alice в Sentry.

    Args:
        intent: Распознанный интент
        user_utterance: Команда пользователя (без персональных данных)
        session_id: Хешированный ID сессии
        response_type: Тип ответа
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("alice.intent", intent)

        if response_type:
            scope.set_tag("alice.response_type", response_type)

        # Хешируем ID сессии для приватности
        if session_id:
            hashed_session = f"session_{hash(session_id) % 10000}"
            scope.set_tag("alice.session", hashed_session)

        # Добавляем контекст Alice
        scope.set_context(
            "yandex_alice",
            {
                "intent": intent,
                "response_type": response_type,
                "has_utterance": bool(user_utterance),
                "utterance_length": len(user_utterance)
                if user_utterance
                else 0,
            },
        )


def capture_performance_metrics(
    operation_name: str,
    duration_ms: float,
    success: bool = True,
    backend_used: str = None,
    cache_hit: bool = False,
    **metrics,
) -> None:
    """
    Отправка метрик производительности в Sentry.

    Args:
        operation_name: Название операции
        duration_ms: Длительность в миллисекундах
        success: Успешность операции
        backend_used: Использованный бэкенд
        cache_hit: Использование кэша
        **metrics: Дополнительные метрики
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("perf.operation", operation_name)
        scope.set_tag("perf.success", success)
        scope.set_tag("perf.cache_hit", cache_hit)

        if backend_used:
            scope.set_tag("perf.backend", backend_used)

        # Отправляем кастомные метрики
        sentry_sdk.set_measurement("duration_ms", duration_ms)

        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                sentry_sdk.set_measurement(metric_name, metric_value)


# Декоратор для автоматического мониторинга функций
def monitor_operation(operation_name: str):
    """
    Декоратор для мониторинга астрологических операций.

    Args:
        operation_name: Название операции для Sentry
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            with sentry_sdk.start_transaction(
                op="astrology_operation",
                name=f"{operation_name}:{func.__name__}",
            ):
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    capture_performance_metrics(
                        operation_name=operation_name,
                        duration_ms=duration_ms,
                        success=True,
                        function=func.__name__,
                    )

                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000

                    capture_performance_metrics(
                        operation_name=operation_name,
                        duration_ms=duration_ms,
                        success=False,
                        function=func.__name__,
                        error_type=type(e).__name__,
                    )

                    sentry_sdk.capture_exception(e)
                    raise

        def sync_wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            with sentry_sdk.start_transaction(
                op="astrology_operation",
                name=f"{operation_name}:{func.__name__}",
            ):
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    capture_performance_metrics(
                        operation_name=operation_name,
                        duration_ms=duration_ms,
                        success=True,
                        function=func.__name__,
                    )

                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000

                    capture_performance_metrics(
                        operation_name=operation_name,
                        duration_ms=duration_ms,
                        success=False,
                        function=func.__name__,
                        error_type=type(e).__name__,
                    )

                    sentry_sdk.capture_exception(e)
                    raise

        # Возвращаем правильный wrapper в зависимости от типа функции
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ==================== SENTRY METRICS ====================


def capture_custom_metric(
    key: str,
    value: Union[int, float],
    unit: str = "none",
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Отправка кастомной метрики в Sentry.

    Args:
        key: Название метрики (например, "astroloh.horoscope.generation_time")
        value: Значение метрики
        unit: Единица измерения (millisecond, second, count, byte, etc.)
        tags: Дополнительные теги для фильтрации
    """
    try:
        default_tags = {
            "service": "astroloh",
            "environment": settings.SENTRY_ENVIRONMENT,
        }
        if tags:
            default_tags.update(tags)

        metrics.incr(key=key, value=value, tags=default_tags, unit=unit)
    except Exception as e:
        logger.warning(f"🔶 Ошибка отправки метрики {key}: {e}")


def capture_distribution_metric(
    key: str,
    value: Union[int, float],
    unit: str = "millisecond",
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Отправка distribution метрики для измерения времени/размеров.

    Args:
        key: Название метрики
        value: Значение
        unit: Единица измерения
        tags: Дополнительные теги
    """
    try:
        default_tags = {
            "service": "astroloh",
            "environment": settings.SENTRY_ENVIRONMENT,
        }
        if tags:
            default_tags.update(tags)

        metrics.distribution(
            key=key, value=value, tags=default_tags, unit=unit
        )
    except Exception as e:
        logger.warning(f"🔶 Ошибка отправки distribution метрики {key}: {e}")


def capture_business_metric(
    operation: str,
    zodiac_sign: Optional[str] = None,
    ai_used: bool = False,
    cache_hit: bool = False,
    duration_ms: Optional[float] = None,
) -> None:
    """
    Отправка бизнес-метрик для астрологических операций.

    Args:
        operation: Тип операции (horoscope, compatibility, natal_chart, etc.)
        zodiac_sign: Знак зодиака
        ai_used: Использовался ли AI
        cache_hit: Было ли попадание в кэш
        duration_ms: Длительность операции в миллисекундах
    """
    tags = {
        "operation": operation,
        "ai_used": str(ai_used).lower(),
        "cache_hit": str(cache_hit).lower(),
    }

    if zodiac_sign:
        tags["zodiac_sign"] = zodiac_sign

    # Счетчик операций
    capture_custom_metric(
        key="astroloh.operation.count", value=1, unit="count", tags=tags
    )

    # Время выполнения операции
    if duration_ms is not None:
        capture_distribution_metric(
            key="astroloh.operation.duration",
            value=duration_ms,
            unit="millisecond",
            tags=tags,
        )


# ==================== SENTRY LOGS ====================


def capture_structured_log(
    level: str,
    message: str,
    extra_data: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Отправка структурированного лога в Sentry.

    Args:
        level: Уровень лога (info, warning, error, critical)
        message: Сообщение
        extra_data: Дополнительные структурированные данные
        tags: Теги для фильтрации
    """
    with sentry_sdk.configure_scope() as scope:
        # Добавляем теги
        if tags:
            for key, value in tags.items():
                scope.set_tag(f"log.{key}", value)

        # Добавляем контекст
        if extra_data:
            scope.set_context("log_data", extra_data)

        # Добавляем breadcrumb для лучшей трассировки
        sentry_sdk.add_breadcrumb(
            message=message,
            category="astroloh.log",
            level=level,
            data=extra_data or {},
        )

        # Отправляем лог
        if level.lower() == "error":
            sentry_sdk.capture_message(message, level="error")
        elif level.lower() == "warning":
            sentry_sdk.capture_message(message, level="warning")


def capture_astrology_log(
    operation: str,
    message: str,
    level: str = "info",
    zodiac_sign: Optional[str] = None,
    backend: Optional[str] = None,
    **kwargs,
) -> None:
    """
    Специализированный лог для астрологических операций.

    Args:
        operation: Тип астрологической операции
        message: Сообщение
        level: Уровень лога
        zodiac_sign: Знак зодиака
        backend: Бэкенд для расчетов
        **kwargs: Дополнительные данные
    """
    extra_data = {"operation": operation, "timestamp": time.time()}

    if zodiac_sign:
        extra_data["zodiac_sign"] = zodiac_sign
    if backend:
        extra_data["backend"] = backend

    extra_data.update(kwargs)

    tags = {"operation": operation, "service": "astroloh"}

    capture_structured_log(level, message, extra_data, tags)


# ==================== SENTRY WARNINGS & ALERTS ====================


def capture_performance_warning(
    operation: str,
    actual_duration_ms: float,
    threshold_ms: float,
    additional_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Отправка предупреждения о превышении времени выполнения.

    Args:
        operation: Название операции
        actual_duration_ms: Фактическое время выполнения
        threshold_ms: Пороговое значение
        additional_context: Дополнительный контекст
    """
    message = f"⚠️ Операция {operation} выполнялась {actual_duration_ms:.0f}ms (лимит: {threshold_ms:.0f}ms)"

    extra_data = {
        "operation": operation,
        "actual_duration_ms": actual_duration_ms,
        "threshold_ms": threshold_ms,
        "performance_ratio": actual_duration_ms / threshold_ms,
    }

    if additional_context:
        extra_data.update(additional_context)

    tags = {
        "alert_type": "performance_warning",
        "operation": operation,
        "severity": "medium"
        if actual_duration_ms < threshold_ms * 2
        else "high",
    }

    capture_structured_log("warning", message, extra_data, tags)

    # Отправляем метрику превышения
    capture_custom_metric(
        key="astroloh.performance.threshold_exceeded",
        value=1,
        unit="count",
        tags=tags,
    )


def capture_business_warning(
    warning_type: str,
    message: str,
    severity: str = "medium",
    additional_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Отправка бизнес-предупреждения.

    Args:
        warning_type: Тип предупреждения (fallback_used, data_quality, etc.)
        message: Сообщение
        severity: Уровень важности (low, medium, high, critical)
        additional_data: Дополнительные данные
    """
    tags = {
        "warning_type": warning_type,
        "severity": severity,
        "service": "astroloh",
    }

    capture_structured_log("warning", message, additional_data, tags)


# ==================== CONTEXT MANAGERS ====================


@contextmanager
def sentry_trace(operation_name: str, **trace_data):
    """
    Context manager для автоматического создания трейсов.

    Usage:
        with sentry_trace("horoscope_generation", zodiac_sign="leo"):
            # код операции
            pass
    """
    start_time = time.time()

    with sentry_sdk.start_transaction(
        op="astrology_operation", name=operation_name
    ) as transaction:
        # Добавляем данные в трейс
        for key, value in trace_data.items():
            transaction.set_tag(key, str(value))

        try:
            yield transaction

            duration_ms = (time.time() - start_time) * 1000
            transaction.set_tag("success", "true")
            transaction.set_measurement("duration_ms", duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            transaction.set_tag("success", "false")
            transaction.set_tag("error_type", type(e).__name__)
            transaction.set_measurement("duration_ms", duration_ms)

            sentry_sdk.capture_exception(e)
            raise


@contextmanager
def sentry_span(span_name: str, **span_data):
    """
    Context manager для создания дочерних спанов внутри трейса.

    Usage:
        with sentry_trace("natal_chart_calculation"):
            with sentry_span("kerykeion_calculation", backend="kerykeion"):
                # код расчета
                pass
    """
    start_time = time.time()

    with sentry_sdk.start_span(
        op="astrology_span", description=span_name
    ) as span:
        # Добавляем данные в спан
        for key, value in span_data.items():
            span.set_tag(key, str(value))

        try:
            yield span

            duration_ms = (time.time() - start_time) * 1000
            span.set_tag("success", "true")
            span.set_data("duration_ms", duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_tag("success", "false")
            span.set_tag("error_type", type(e).__name__)
            span.set_data("duration_ms", duration_ms)

            raise
