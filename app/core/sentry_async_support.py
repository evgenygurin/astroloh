"""
Расширенная поддержка AsyncIO для Sentry.
Реализация согласно https://docs.sentry.io/platforms/python/integrations/asyncio/
"""

import asyncio
import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, cast

import sentry_sdk
from sentry_sdk import start_span

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

# ==================== ASYNC INITIALIZATION ====================


async def init_sentry_async():
    """
    Асинхронная инициализация Sentry.
    Должна вызываться в начале первой async функции.
    """
    if not hasattr(init_sentry_async, "_initialized"):
        # Импортируем и запускаем основную инициализацию
        from .sentry import init_sentry

        init_sentry()

        # Дополнительная настройка для async
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("runtime.async", True)
            scope.set_tag("runtime.loop", "asyncio")

        init_sentry_async._initialized = True


# ==================== ASYNC DECORATORS ====================


def trace_async_operation(
    operation_name: str, operation_type: str = "async_task", **trace_metadata
):
    """
    Декоратор для трейсинга асинхронных операций.

    Args:
        operation_name: Название операции
        operation_type: Тип операции
        **trace_metadata: Дополнительные метаданные
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with start_span(
                op=operation_type, description=operation_name
            ) as span:
                # Добавляем метаданные
                span.set_tag("async.operation", operation_name)
                span.set_tag("async.function", func.__name__)
                span.set_tag("async.module", func.__module__)

                for key, value in trace_metadata.items():
                    span.set_tag(f"async.{key}", str(value))

                try:
                    start_time = time.time()

                    # Выполняем асинхронную функцию
                    result = await func(*args, **kwargs)

                    # Успешное завершение
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_data("async.duration_ms", duration_ms)
                    span.set_tag("async.status", "success")

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_data("async.duration_ms", duration_ms)
                    span.set_tag("async.status", "error")
                    span.set_tag("async.error_type", type(e).__name__)
                    span.set_data("async.error_message", str(e))
                    raise

        return cast(F, wrapper)

    return decorator


def monitor_async_task(task_name: Optional[str] = None, **task_metadata):
    """
    Декоратор для мониторинга asyncio задач.

    Args:
        task_name: Название задачи
        **task_metadata: Метаданные задачи
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Автоматическое определение имени задачи
            if task_name is None:
                name = f"{func.__module__}.{func.__name__}"
            else:
                name = task_name

            with start_span(
                op="asyncio.task", description=f"Task: {name}"
            ) as span:
                # Информация о задаче
                current_task = asyncio.current_task()
                span.set_tag("asyncio.task_name", name)
                if current_task:
                    span.set_tag("asyncio.task_id", str(id(current_task)))
                    span.set_tag("asyncio.task_done", current_task.done())
                    span.set_tag(
                        "asyncio.task_cancelled", current_task.cancelled()
                    )

                # Информация о event loop
                try:
                    loop = asyncio.get_event_loop()
                    span.set_tag("asyncio.loop_running", loop.is_running())
                    span.set_tag("asyncio.loop_debug", loop.get_debug())
                except Exception:
                    pass

                # Дополнительные метаданные
                for key, value in task_metadata.items():
                    span.set_tag(f"task.{key}", str(value))

                try:
                    result = await func(*args, **kwargs)
                    span.set_tag("asyncio.completion_status", "success")
                    return result
                except asyncio.CancelledError:
                    span.set_tag("asyncio.completion_status", "cancelled")
                    raise
                except Exception as e:
                    span.set_tag("asyncio.completion_status", "error")
                    span.set_tag("asyncio.error_type", type(e).__name__)
                    raise

        return cast(F, wrapper)

    return decorator


# ==================== ASYNC CONTEXT MANAGERS ====================


@asynccontextmanager
async def trace_async_context(context_name: str, **context_metadata):
    """
    Асинхронный context manager для трейсинга.

    Args:
        context_name: Название контекста
        **context_metadata: Метаданные контекста
    """
    with start_span(op="async.context", description=context_name) as span:
        # Метаданные контекста
        span.set_tag("async.context_name", context_name)
        for key, value in context_metadata.items():
            span.set_tag(f"context.{key}", str(value))

        try:
            start_time = time.time()
            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("async.context.duration_ms", duration_ms)
            span.set_tag("async.context.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("async.context.duration_ms", duration_ms)
            span.set_tag("async.context.status", "error")
            span.set_tag("async.context.error_type", type(e).__name__)
            raise


@asynccontextmanager
async def trace_concurrent_operations(
    operation_group: str,
    max_concurrency: Optional[int] = None,
    **group_metadata,
):
    """
    Трейсинг параллельных операций.

    Args:
        operation_group: Группа операций
        max_concurrency: Максимальная конкурентность
        **group_metadata: Метаданные группы
    """
    with start_span(
        op="async.concurrent", description=f"Concurrent: {operation_group}"
    ) as span:
        # Информация о конкурентности
        span.set_tag("async.operation_group", operation_group)
        if max_concurrency:
            span.set_tag("async.max_concurrency", max_concurrency)

        # Метаданные группы
        for key, value in group_metadata.items():
            span.set_tag(f"concurrent.{key}", str(value))

        try:
            start_time = time.time()
            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("async.concurrent.duration_ms", duration_ms)
            span.set_tag("async.concurrent.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("async.concurrent.duration_ms", duration_ms)
            span.set_tag("async.concurrent.status", "error")
            span.set_tag("async.concurrent.error_type", type(e).__name__)
            raise


# ==================== АСТРОЛОГИЧЕСКИЕ ASYNC ОПЕРАЦИИ ====================


@trace_async_operation("astro_calculation", "astrology.async")
async def trace_astro_async_calculation(
    calculation_type: str, **calculation_params
):
    """
    Трейсинг асинхронных астрологических вычислений.

    Args:
        calculation_type: Тип вычисления
        **calculation_params: Параметры вычисления
    """
    async with trace_async_context(
        f"astro_calculation_{calculation_type}",
        calculation_type=calculation_type,
        domain="astrology",
        **calculation_params,
    ) as span:
        # Специфичные теги для астрологии
        span.set_tag("astro.calculation_type", calculation_type)
        span.set_tag("astro.async_execution", True)

        for key, value in calculation_params.items():
            span.set_tag(f"astro.{key}", str(value))

        yield span


@asynccontextmanager
async def trace_astro_concurrent_analysis(
    analysis_types: list,
    zodiac_sign: Optional[str] = None,
    **analysis_metadata,
):
    """
    Трейсинг параллельного анализа астрологических данных.

    Args:
        analysis_types: Типы анализа
        zodiac_sign: Знак зодиака
        **analysis_metadata: Метаданные анализа
    """
    async with trace_concurrent_operations(
        operation_group="astro_parallel_analysis",
        max_concurrency=len(analysis_types),
        **analysis_metadata,
    ) as span:
        # Астрологические теги
        span.set_tag("astro.analysis_count", len(analysis_types))
        span.set_tag("astro.analysis_types", ",".join(analysis_types))
        if zodiac_sign:
            span.set_tag("astro.zodiac_sign", zodiac_sign)

        span.set_tag("astro.domain", "astrology")
        span.set_tag("astro.execution_mode", "concurrent")

        yield span


# ==================== ASYNC UTILITIES ====================


async def capture_async_exception_context(
    exception: Exception, context_data: Dict[str, Any]
):
    """
    Захватывает контекст для исключений в async операциях.

    Args:
        exception: Исключение
        context_data: Данные контекста
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_context(
            "async_exception",
            {
                "exception_type": type(exception).__name__,
                "task_info": _get_current_task_info(),
                "loop_info": _get_event_loop_info(),
                **context_data,
            },
        )

        sentry_sdk.capture_exception(exception)


def _get_current_task_info() -> Dict[str, Any]:
    """Получает информацию о текущей задаче."""
    try:
        current_task = asyncio.current_task()
        if current_task:
            return {
                "task_name": getattr(current_task, "_name", "unnamed"),
                "task_id": str(id(current_task)),
                "task_done": current_task.done(),
                "task_cancelled": current_task.cancelled(),
            }
    except Exception:
        pass
    return {}


def _get_event_loop_info() -> Dict[str, Any]:
    """Получает информацию о event loop."""
    try:
        loop = asyncio.get_event_loop()
        return {
            "loop_running": loop.is_running(),
            "loop_debug": loop.get_debug(),
            "loop_id": str(id(loop)),
        }
    except Exception:
        pass
    return {}


# ==================== BACKGROUND TASKS MONITORING ====================


class BackgroundTaskMonitor:
    """
    Мониторинг фоновых задач.
    """

    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def create_monitored_task(
        self, coro: Awaitable, name: str, **task_metadata
    ) -> asyncio.Task:
        """
        Создает отслеживаемую фоновую задачу.

        Args:
            coro: Корутина
            name: Имя задачи
            **task_metadata: Метаданные задачи

        Returns:
            Asyncio Task
        """

        async def monitored_coro():
            async with trace_async_context(
                f"background_task_{name}",
                task_name=name,
                task_type="background",
                **task_metadata,
            ):
                try:
                    result = await coro
                    return result
                except Exception as e:
                    await capture_async_exception_context(
                        e,
                        {
                            "task_name": name,
                            "task_type": "background",
                            **task_metadata,
                        },
                    )
                    raise
                finally:
                    # Удаляем задачу из активных
                    if name in self.active_tasks:
                        del self.active_tasks[name]

        # Создаем задачу
        task = asyncio.create_task(monitored_coro(), name=name)
        self.active_tasks[name] = task

        return task

    def get_active_tasks_info(self) -> Dict[str, Dict[str, Any]]:
        """Получает информацию об активных задачах."""
        info = {}
        for name, task in self.active_tasks.items():
            info[name] = {
                "done": task.done(),
                "cancelled": task.cancelled(),
                "task_id": str(id(task)),
            }
        return info


# Глобальный экземпляр монитора фоновых задач
background_task_monitor = BackgroundTaskMonitor()


# ==================== USAGE EXAMPLES ====================


"""
Примеры использования async поддержки Sentry:

1. Инициализация в главной async функции:

    async def main():
        await init_sentry_async()
        
        # Ваш код приложения
        await run_application()

2. Декоратор для async операций:

    @trace_async_operation("generate_horoscope", "astrology.generation")
    async def generate_horoscope_async(zodiac_sign: str):
        # Async генерация гороскопа
        horoscope = await ai_service.generate(zodiac_sign)
        return horoscope

3. Мониторинг async задач:

    @monitor_async_task("background_ephemeris_update", data_type="ephemeris")
    async def update_ephemeris_data():
        # Фоновое обновление эфемеридных данных
        await ephemeris_service.update()

4. Context manager для async операций:

    async def complex_astro_analysis(birth_data: dict):
        async with trace_async_context("complex_analysis", analysis_type="full"):
            natal_chart = await calculate_natal_chart(birth_data)
            transits = await calculate_transits(birth_data)
            return {"natal_chart": natal_chart, "transits": transits}

5. Параллельные астрологические вычисления:

    async def parallel_horoscope_generation(zodiac_signs: list):
        async with trace_astro_concurrent_analysis(
            analysis_types=["horoscope"],
            signs_count=len(zodiac_signs)
        ):
            tasks = [
                generate_horoscope_async(sign) 
                for sign in zodiac_signs
            ]
            horoscopes = await asyncio.gather(*tasks)
            return horoscopes

6. Фоновые задачи:

    async def start_background_tasks():
        # Создаем отслеживаемую фоновую задачу
        task = background_task_monitor.create_monitored_task(
            update_daily_horoscopes(),
            name="daily_horoscope_updater",
            schedule="daily",
            priority="high"
        )
        
        return task
"""
