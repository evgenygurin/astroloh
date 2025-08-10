"""
Sentry инициализация и настройка расширенного мониторинга.
Поддержка: Logs, Metrics, Warnings, Traces, Profiling
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union

import sentry_sdk
from sentry_sdk import metrics
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.asyncpg import AsyncPGIntegration
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

    # Настройка интеграций (расширенный список)
    integrations = [
        # FastAPI интеграция (полная конфигурация)
        FastApiIntegration(
            transaction_style="endpoint",  # "url" или "endpoint"
            failed_request_status_codes=[400, 401, 403, 404, 422, 500, 502, 503, 504],
            http_methods_to_capture=["GET", "POST", "PUT", "DELETE", "PATCH"],
        ),
        # Starlette интеграция для middleware
        StarletteIntegration(
            transaction_style="endpoint",
            failed_request_status_codes=[400, 401, 403, 404, 422, 500, 503]
        ),
        # HTTP клиент интеграция (для Yandex API и внешних сервисов)
        HttpxIntegration(),
        # AIOHTTP интеграция (если используется)
        AioHttpIntegration(),
        # Async интеграция с улучшенным отслеживанием
        AsyncioIntegration(),
        # PostgreSQL интеграция (asyncpg)
        AsyncPGIntegration(),
        # SQLAlchemy интеграция (расширенные настройки)
        SqlalchemyIntegration(
            # Автоматически включает query профилирование
        ),
        # Redis интеграция для кэширования
        RedisIntegration(),
        # Расширенная logging интеграция
        LoggingIntegration(
            level=logging.INFO,  # Минимальный уровень для breadcrumb
            event_level=logging.ERROR,  # Минимальный уровень для событий
        ),
    ]

    # Инициализация Sentry с современными настройками
    try:
        sentry_sdk.init(
            # 🏗️ CORE CONFIGURATION
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            release=settings.SENTRY_RELEASE,
            dist=settings.SENTRY_DIST,
            integrations=integrations,
            
            # 📊 ERROR MONITORING
            sample_rate=settings.SENTRY_SAMPLE_RATE,
            attach_stacktrace=settings.SENTRY_ATTACH_STACKTRACE,
            send_default_pii=settings.SENTRY_SEND_DEFAULT_PII,
            max_breadcrumbs=settings.SENTRY_MAX_BREADCRUMBS,
            ignore_errors=settings.SENTRY_IGNORE_ERRORS,
            
            # 🔥 PERFORMANCE MONITORING & TRACING
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            enable_tracing=settings.SENTRY_ENABLE_TRACING,
            
            # 📈 PROFILING (Continuous Profiling)
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            profile_lifecycle=settings.SENTRY_PROFILE_LIFECYCLE,
            
            # 📊 METRICS (New metrics system)
            _experiments={
                "enable_metrics": settings.SENTRY_ENABLE_METRICS,
                "enable_metrics_summaries": settings.SENTRY_ENABLE_METRICS_SUMMARIES,
                "metric_code_locations": settings.SENTRY_METRIC_CODE_LOCATIONS,
            },
            
            # 🌐 TRANSPORT & NETWORK
            shutdown_timeout=settings.SENTRY_SHUTDOWN_TIMEOUT,
            max_request_body_size=settings.SENTRY_MAX_REQUEST_BODY_SIZE,
            
            # 🐛 DEBUG & DEVELOPMENT
            debug=settings.SENTRY_DEBUG,
            auto_enabling_integrations=settings.SENTRY_AUTO_ENABLING_INTEGRATIONS,
            
            # 🎯 FILTERING & DATA PROCESSING
            before_send=filter_sensitive_data,
            before_send_transaction=filter_transaction_data,
            before_breadcrumb=filter_breadcrumb_data,
            before_emit_metric=filter_metric_data,  # New metric filtering
            
            # 🔄 SAMPLING FUNCTIONS (for advanced control)
            traces_sampler=custom_traces_sampler,
            profiles_sampler=custom_profiles_sampler,
            error_sampler=custom_error_sampler,
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
    event.setdefault("tags", {}).update({
        "application": "astroloh",
        "service": "yandex_alice",
    })

    # Добавляем пользовательский контекст для астрологии
    if "user" in event:
        user_data = event["user"]
        # Убираем персональные данные, оставляем только идентификатор сессии
        if "id" in user_data and len(str(user_data["id"])) > 10:
            user_data["id"] = f"session_{hash(str(user_data['id'])) % 10000}"

    return event


def filter_metric_data(key: str, value: float, unit: str, tags: Dict[str, str]) -> bool:
    """
    Фильтрация метрик перед отправкой в Sentry.
    
    Args:
        key: Ключ метрики
        value: Значение метрики
        unit: Единица измерения
        tags: Теги метрики
    
    Returns:
        True если метрику нужно отправить, False если пропустить
    """
    # Пропускаем системные метрики в development режиме
    if settings.SENTRY_ENVIRONMENT == "development":
        if key.startswith("system.") or key.startswith("runtime."):
            return False
    
    # Пропускаем слишком частые метрики
    frequent_metrics = [
        "astroloh.cache.get",
        "astroloh.request.small",
    ]
    if any(key.startswith(fm) for fm in frequent_metrics):
        # Сэмплинг 10% для частых метрик
        return hash(key) % 10 == 0
    
    # Фильтруем метрики по значениям (избегаем аномалий)
    if unit in ["millisecond", "second"]:
        # Пропускаем слишком большие значения времени (возможные ошибки)
        if value > 300000:  # > 5 минут
            return False
    
    return True


def custom_traces_sampler(sampling_context: Dict[str, Any]) -> Optional[float]:
    """
    Динамический сэмплинг трейсов на основе контекста.
    
    Args:
        sampling_context: Контекст трейса (transaction, parent_sampled, etc.)
    
    Returns:
        Sampling rate (0.0-1.0) или None для дефолтного значения
    """
    transaction_context = sampling_context.get("transaction_context", {})
    transaction_name = transaction_context.get("name", "")
    
    # Высокий приоритет для критических операций
    high_priority_operations = [
        "yandex_webhook",
        "horoscope_generation", 
        "ai_consultation",
        "compatibility_analysis"
    ]
    
    if any(op in transaction_name.lower() for op in high_priority_operations):
        return 0.5  # 50% для важных операций
    
    # Низкий приоритет для служебных операций
    if transaction_name.startswith("/health") or transaction_name.startswith("/metrics"):
        return 0.01  # 1% для health checks
    
    # Адаптивный сэмплинг в зависимости от нагрузки
    current_hour = time.localtime().tm_hour
    if 9 <= current_hour <= 21:  # Дневные часы (больше пользователей)
        return 0.2  # 20%
    else:  # Ночные часы
        return 0.05  # 5%


def custom_profiles_sampler(sampling_context: Dict[str, Any]) -> Optional[float]:
    """
    Динамический сэмплинг профилирования.
    
    Args:
        sampling_context: Контекст профилирования
    
    Returns:
        Sampling rate для профилей
    """
    transaction_context = sampling_context.get("transaction_context", {})
    transaction_name = transaction_context.get("name", "")
    
    # Профилируем только CPU-интенсивные операции
    cpu_intensive_operations = [
        "natal_chart_calculation",
        "kerykeion_calculation", 
        "transit_analysis",
        "ai_generation"
    ]
    
    if any(op in transaction_name.lower() for op in cpu_intensive_operations):
        return 0.3  # 30% для CPU-интенсивных операций
    
    # Не профилируем простые операции
    if transaction_name.startswith("/health") or "static" in transaction_name:
        return 0.0
    
    return 0.05  # 5% по умолчанию


def custom_error_sampler(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[float]:
    """
    Динамический сэмплинг ошибок.
    
    Args:
        event: Событие ошибки
        hint: Дополнительная информация
    
    Returns:
        Sampling rate для ошибок
    """
    exception = hint.get("exc_info")
    if exception:
        exc_type, exc_value, exc_traceback = exception
        
        # Всегда отправляем критические ошибки
        critical_errors = [
            "DatabaseError",
            "ConnectionError", 
            "YandexAPIError",
            "ConfigurationError"
        ]
        
        if exc_type.__name__ in critical_errors:
            return 1.0  # 100% для критических ошибок
        
        # Сэмплируем частые некритические ошибки
        frequent_errors = [
            "ValidationError",
            "HTTPException",
            "RequestTimeout"
        ]
        
        if exc_type.__name__ in frequent_errors:
            return 0.1  # 10% для частых ошибок
    
    return 1.0  # 100% по умолчанию


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
    if crumb.get("category") == "query" and "SELECT" in str(crumb.get("message", "")):
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
    event.setdefault("tags", {}).update({
        "service_type": "astrology_api",
        "integration": "yandex_alice",
    })

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
                "utterance_length": len(user_utterance) if user_utterance else 0,
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
    Отправка кастомной метрики в Sentry (Counter).

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
        logger.warning(f"🔶 Ошибка отправки counter метрики {key}: {e}")


def capture_counter_metric(
    key: str,
    value: Union[int, float] = 1,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Отправка counter метрики (подсчет событий).
    
    Args:
        key: Название метрики
        value: Значение для добавления (по умолчанию 1)
        tags: Дополнительные теги
    """
    capture_custom_metric(key=key, value=value, unit="count", tags=tags)


def capture_gauge_metric(
    key: str,
    value: Union[int, float],
    unit: str = "none",
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Отправка gauge метрики (текущее значение).
    
    Args:
        key: Название метрики
        value: Текущее значение
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

        metrics.gauge(key=key, value=value, tags=default_tags, unit=unit)
    except Exception as e:
        logger.warning(f"🔶 Ошибка отправки gauge метрики {key}: {e}")


def capture_set_metric(
    key: str,
    value: Union[str, int],
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Отправка set метрики (уникальные значения).
    
    Args:
        key: Название метрики
        value: Уникальное значение для добавления в сет
        tags: Дополнительные теги
    """
    try:
        default_tags = {
            "service": "astroloh",
            "environment": settings.SENTRY_ENVIRONMENT,
        }
        if tags:
            default_tags.update(tags)

        metrics.set(key=key, value=value, tags=default_tags)
    except Exception as e:
        logger.warning(f"🔶 Ошибка отправки set метрики {key}: {e}")


def capture_timer_metric(
    key: str,
    duration_ms: float,
    tags: Optional[Dict[str, str]] = None,
) -> None:
    """
    Отправка timer метрики (измерение времени).
    
    Args:
        key: Название метрики
        duration_ms: Длительность в миллисекундах
        tags: Дополнительные теги
    """
    capture_distribution_metric(
        key=key,
        value=duration_ms,
        unit="millisecond",
        tags=tags
    )


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

        metrics.distribution(key=key, value=value, tags=default_tags, unit=unit)
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
        "severity": "medium" if actual_duration_ms < threshold_ms * 2 else "high",
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
    Context manager для автоматического создания трейсов с метриками.

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
            # Отправляем counter метрику о начале операции
            capture_counter_metric(
                key="astroloh.operation.started",
                tags={"operation": operation_name, **trace_data}
            )

            yield transaction

            duration_ms = (time.time() - start_time) * 1000
            transaction.set_tag("success", "true")
            transaction.set_measurement("duration_ms", duration_ms)

            # Отправляем успешные метрики
            capture_counter_metric(
                key="astroloh.operation.completed",
                tags={"operation": operation_name, "status": "success", **trace_data}
            )
            
            capture_timer_metric(
                key="astroloh.operation.duration",
                duration_ms=duration_ms,
                tags={"operation": operation_name, **trace_data}
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            transaction.set_tag("success", "false")
            transaction.set_tag("error_type", type(e).__name__)
            transaction.set_measurement("duration_ms", duration_ms)

            # Отправляем метрики об ошибках
            capture_counter_metric(
                key="astroloh.operation.failed",
                tags={
                    "operation": operation_name, 
                    "error_type": type(e).__name__,
                    **trace_data
                }
            )

            sentry_sdk.capture_exception(e)
            raise


# ==================== MODERN SENTRY FEATURES ====================


@contextmanager
def sentry_profiler(profile_name: str, **profile_data):
    """
    Context manager для профилирования с дополнительными метриками.
    
    Usage:
        with sentry_profiler("kerykeion_calculation", chart_type="natal"):
            # CPU-интенсивный код
            pass
    """
    start_time = time.time()
    
    # Устанавливаем теги для профилирования
    with sentry_sdk.configure_scope() as scope:
        for key, value in profile_data.items():
            scope.set_tag(f"profile.{key}", str(value))
        
        scope.set_tag("profile.operation", profile_name)
    
    try:
        # Отправляем метрику о начале профилирования
        capture_counter_metric(
            key="astroloh.profiling.started",
            tags={"profile_name": profile_name, **profile_data}
        )
        
        yield
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Отправляем метрики профилирования
        capture_timer_metric(
            key="astroloh.profiling.duration",
            duration_ms=duration_ms,
            tags={"profile_name": profile_name, **profile_data}
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        capture_counter_metric(
            key="astroloh.profiling.failed",
            tags={
                "profile_name": profile_name,
                "error_type": type(e).__name__,
                **profile_data
            }
        )
        raise


def add_user_context(
    user_id: str, 
    user_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Добавление пользовательского контекста в Sentry.
    
    Args:
        user_id: Идентификатор пользователя (хешированный)
        user_data: Дополнительные данные пользователя
    """
    with sentry_sdk.configure_scope() as scope:
        # Хешируем ID для приватности
        hashed_id = f"user_{hash(user_id) % 100000}"
        
        user_context = {
            "id": hashed_id,
            "timestamp": time.time()
        }
        
        if user_data:
            # Фильтруем чувствительные данные
            safe_data = {}
            for key, value in user_data.items():
                if key not in ["birth_time", "birth_place", "real_name", "email"]:
                    safe_data[key] = value
            
            user_context.update(safe_data)
        
        scope.set_user(user_context)


def add_business_context(
    operation_type: str,
    business_data: Dict[str, Any]
) -> None:
    """
    Добавление бизнес-контекста для астрологических операций.
    
    Args:
        operation_type: Тип операции (horoscope, natal_chart, etc.)
        business_data: Бизнес-данные операции
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_context("astrology_business", {
            "operation_type": operation_type,
            "timestamp": time.time(),
            **business_data
        })
        
        # Добавляем теги для бизнес-аналитики
        scope.set_tag("business.operation", operation_type)
        if "zodiac_sign" in business_data:
            scope.set_tag("business.zodiac_sign", business_data["zodiac_sign"])
        if "ai_enabled" in business_data:
            scope.set_tag("business.ai_enabled", str(business_data["ai_enabled"]))


def capture_feature_flag_context(
    flag_name: str,
    flag_value: Any,
    user_id: Optional[str] = None
) -> None:
    """
    Отслеживание использования feature flags.
    
    Args:
        flag_name: Название feature flag
        flag_value: Значение флага
        user_id: ID пользователя (опционально)
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_context("feature_flags", {
            flag_name: flag_value,
            "timestamp": time.time()
        })
        
        scope.set_tag(f"feature.{flag_name}", str(flag_value))
    
    # Отправляем метрику использования feature flag
    tags = {
        "flag_name": flag_name,
        "flag_value": str(flag_value)
    }
    
    if user_id:
        tags["user_segment"] = f"segment_{hash(user_id) % 10}"
    
    capture_counter_metric(
        key="astroloh.feature_flag.used",
        tags=tags
    )


def track_external_api_call(
    api_name: str,
    endpoint: str,
    method: str = "GET",
    response_time_ms: Optional[float] = None,
    status_code: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Отслеживание вызовов внешних API.
    
    Args:
        api_name: Название API (yandex_gpt, etc.)
        endpoint: Эндпоинт API
        method: HTTP метод
        response_time_ms: Время ответа
        status_code: HTTP статус код
        error: Ошибка (если есть)
    """
    tags = {
        "api_name": api_name,
        "endpoint": endpoint,
        "method": method
    }
    
    if status_code:
        tags["status_code"] = str(status_code)
        tags["status_class"] = f"{status_code // 100}xx"
    
    if error:
        tags["error"] = error
        
    # Счетчик вызовов API
    capture_counter_metric(
        key="astroloh.external_api.calls",
        tags=tags
    )
    
    # Время ответа API
    if response_time_ms:
        capture_timer_metric(
            key="astroloh.external_api.response_time",
            duration_ms=response_time_ms,
            tags=tags
        )
    
    # Ошибки API
    if error or (status_code and status_code >= 400):
        capture_counter_metric(
            key="astroloh.external_api.errors",
            tags=tags
        )


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

    with sentry_sdk.start_span(op="astrology_span", description=span_name) as span:
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


# ==================== USAGE EXAMPLES ====================


"""
Примеры использования новых функций Sentry:

1. Базовое использование с трейсингом и метриками:

    with sentry_trace("horoscope_generation", zodiac_sign="leo", ai_enabled=True):
        horoscope = generate_horoscope("leo")
        
        # Дополнительные метрики
        capture_counter_metric("astroloh.horoscope.generated", tags={"sign": "leo"})
        capture_timer_metric("astroloh.generation.time", 1200, tags={"type": "ai"})

2. Профилирование CPU-интенсивных операций:

    with sentry_profiler("kerykeion_natal_chart", chart_type="natal"):
        chart_data = kerykeion_service.calculate_natal_chart(birth_data)

3. Отслеживание внешних API:

    start_time = time.time()
    try:
        response = httpx.post("https://api.yandex.gpt", json=payload)
        duration_ms = (time.time() - start_time) * 1000
        
        track_external_api_call(
            api_name="yandex_gpt",
            endpoint="/generate", 
            method="POST",
            response_time_ms=duration_ms,
            status_code=response.status_code
        )
    except Exception as e:
        track_external_api_call(
            api_name="yandex_gpt",
            endpoint="/generate",
            method="POST", 
            error=str(e)
        )

4. Пользовательский контекст:

    add_user_context(
        user_id=session_id,
        user_data={
            "preferred_language": "ru",
            "zodiac_sign": "leo",
            "session_duration": 300
        }
    )

5. Бизнес-контекст для операций:

    add_business_context(
        operation_type="compatibility_analysis",
        business_data={
            "zodiac_sign_1": "leo",
            "zodiac_sign_2": "aries", 
            "ai_enabled": True,
            "cache_used": False
        }
    )

6. Feature flags:

    capture_feature_flag_context(
        flag_name="enable_enhanced_ai",
        flag_value=True,
        user_id=session_id
    )

7. Различные типы метрик:

    # Counter (события)
    capture_counter_metric("astroloh.user.login")
    
    # Gauge (текущее значение)
    capture_gauge_metric("astroloh.active_sessions", 42, unit="count")
    
    # Set (уникальные значения)
    capture_set_metric("astroloh.unique_users", user_id)
    
    # Distribution (время выполнения)
    capture_distribution_metric("astroloh.response_time", 850, unit="millisecond")
    
    # Timer (измерение времени)
    capture_timer_metric("astroloh.processing_time", 1200)

8. Комплексный пример астрологической операции:

    async def generate_astrology_consultation(user_id: str, request_data: dict):
        # Устанавливаем пользовательский контекст
        add_user_context(user_id, {"zodiac_sign": request_data["zodiac_sign"]})
        
        # Бизнес-контекст
        add_business_context("ai_consultation", {
            "zodiac_sign": request_data["zodiac_sign"],
            "consultation_type": request_data["type"],
            "ai_enabled": True
        })
        
        # Основная операция с трейсингом
        with sentry_trace("ai_consultation", **request_data) as transaction:
            # Профилирование AI генерации
            with sentry_profiler("ai_generation", model="yandex_gpt"):
                consultation = await ai_service.generate_consultation(request_data)
            
            # Метрики успеха
            capture_counter_metric("astroloh.consultation.completed")
            capture_set_metric("astroloh.daily_users", user_id)
            
            return consultation
"""
