"""
Расширенный мониторинг базы данных для Sentry.
Реализация согласно SQLAlchemy и AsyncPG интеграциям Sentry.
"""

import time
from contextlib import asynccontextmanager, contextmanager
from typing import Optional

import sentry_sdk
from sentry_sdk import start_span
from sqlalchemy.engine import Engine

# ==================== SQLALCHEMY ENHANCED MONITORING ====================


class SQLAlchemyMonitor:
    """
    Расширенный мониторинг SQLAlchemy операций.
    """

    def __init__(self):
        self.slow_query_threshold = 1000  # ms
        self.connection_pool_warnings = True

    def setup_engine_monitoring(self, engine: Engine):
        """
        Настройка мониторинга для SQLAlchemy engine.

        Args:
            engine: SQLAlchemy engine
        """
        from sqlalchemy import event

        # Мониторинг медленных запросов
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            if hasattr(context, "_query_start_time"):
                duration_ms = (time.time() - context._query_start_time) * 1000

                # Медленные запросы
                if duration_ms > self.slow_query_threshold:
                    with sentry_sdk.configure_scope() as scope:
                        scope.set_tag("db.slow_query", True)
                        scope.set_context(
                            "slow_query",
                            {
                                "duration_ms": duration_ms,
                                "statement": statement[:200] + "..."
                                if len(statement) > 200
                                else statement,
                                "executemany": executemany,
                            },
                        )

                    sentry_sdk.capture_message(
                        f"Медленный SQL запрос: {duration_ms:.2f}ms",
                        level="warning",
                    )

        # Мониторинг connection pool
        if self.connection_pool_warnings:

            @event.listens_for(engine.pool, "connect")
            def on_connect(dbapi_connection, connection_record):
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context(
                        "db_connection",
                        {
                            "event": "connect",
                            "pool_size": engine.pool.size(),
                            "checked_in": engine.pool.checkedin(),
                            "checked_out": engine.pool.checkedout(),
                        },
                    )

            @event.listens_for(engine.pool, "checkout")
            def on_checkout(
                dbapi_connection, connection_record, connection_proxy
            ):
                pool_stats = {
                    "pool_size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                }

                # Предупреждение если пул почти исчерпан
                if pool_stats["checked_out"] >= engine.pool.size() * 0.8:
                    sentry_sdk.capture_message(
                        f"Connection pool почти исчерпан: {pool_stats}",
                        level="warning",
                    )


@contextmanager
def trace_database_operation(
    operation_type: str,
    table_name: Optional[str] = None,
    query_type: Optional[str] = None,
    **operation_metadata,
):
    """
    Трейс для операций с базой данных.

    Args:
        operation_type: Тип операции (select, insert, update, delete)
        table_name: Название таблицы
        query_type: Тип запроса (простой, сложный, bulk)
        **operation_metadata: Дополнительные метаданные
    """
    with start_span(
        op="db.sql.query",
        description=f"Database {operation_type.upper()}"
        + (f" on {table_name}" if table_name else ""),
    ) as span:
        # Теги базы данных
        span.set_tag("db.operation", operation_type)
        span.set_tag("db.system", "postgresql")

        if table_name:
            span.set_tag("db.name", table_name)
        if query_type:
            span.set_tag("db.query_type", query_type)

        # Дополнительные метаданные
        for key, value in operation_metadata.items():
            span.set_tag(f"db.{key}", str(value))

        try:
            start_time = time.time()

            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("db.duration_ms", duration_ms)
            span.set_tag("db.status", "success")

            # Метрика для медленных запросов
            if duration_ms > 1000:  # > 1 секунды
                span.set_tag("db.slow_query", True)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("db.duration_ms", duration_ms)
            span.set_tag("db.status", "error")
            span.set_tag("db.error_type", type(e).__name__)
            span.set_data("db.error_message", str(e))
            raise


# ==================== ASYNCPG ENHANCED MONITORING ====================


@asynccontextmanager
async def trace_asyncpg_operation(
    operation_type: str,
    query: Optional[str] = None,
    params_count: Optional[int] = None,
    **operation_metadata,
):
    """
    Асинхронный трейс для AsyncPG операций.

    Args:
        operation_type: Тип операции
        query: SQL запрос (обрезанный)
        params_count: Количество параметров
        **operation_metadata: Метаданные операции
    """
    with start_span(
        op="db.sql.asyncpg", description=f"AsyncPG {operation_type.upper()}"
    ) as span:
        # Теги AsyncPG
        span.set_tag("db.system", "postgresql")
        span.set_tag("db.driver", "asyncpg")
        span.set_tag("db.operation", operation_type)

        if query:
            # Безопасное логирование запроса (первые 100 символов)
            safe_query = query.replace("\n", " ").replace("\t", " ")
            span.set_data(
                "db.statement",
                safe_query[:100] + "..."
                if len(safe_query) > 100
                else safe_query,
            )

        if params_count is not None:
            span.set_data("db.params_count", params_count)

        # Дополнительные метаданные
        for key, value in operation_metadata.items():
            span.set_tag(f"db.{key}", str(value))

        try:
            start_time = time.time()

            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("db.duration_ms", duration_ms)
            span.set_tag("db.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("db.duration_ms", duration_ms)
            span.set_tag("db.status", "error")
            span.set_tag("db.error_type", type(e).__name__)
            span.set_data("db.error_message", str(e))
            raise


# ==================== АСТРОЛОГИЧЕСКАЯ БАЗА ДАННЫХ ====================


@contextmanager
def trace_astro_database_operation(
    astro_operation: str, data_type: str, **astro_metadata
):
    """
    Специализированный трейс для астрологических операций с БД.

    Args:
        astro_operation: Астрологическая операция (save_chart, load_ephemeris, etc.)
        data_type: Тип данных (natal_chart, horoscope, compatibility, etc.)
        **astro_metadata: Астрологические метаданные
    """
    with trace_database_operation(
        operation_type="astrology_data",
        query_type="specialized",
        **astro_metadata,
    ) as span:
        # Астрологические теги
        span.set_tag("astro.operation", astro_operation)
        span.set_tag("astro.data_type", data_type)
        span.set_tag("astro.domain", "astrology")

        # Специфичные для астрологии метаданные
        for key, value in astro_metadata.items():
            span.set_tag(f"astro.{key}", str(value))

        yield span


@asynccontextmanager
async def trace_astro_cache_operation(
    cache_operation: str,
    cache_key: str,
    astro_data_type: str,
    **cache_metadata,
):
    """
    Асинхронный трейс для операций с кэшем астрологических данных.

    Args:
        cache_operation: Операция кэша (get, set, delete)
        cache_key: Ключ кэша
        astro_data_type: Тип астрологических данных
        **cache_metadata: Метаданные кэша
    """
    with start_span(
        op="cache.redis",
        description=f"Cache {cache_operation.upper()}: {astro_data_type}",
    ) as span:
        # Теги кэша
        span.set_tag("cache.operation", cache_operation)
        span.set_tag("cache.system", "redis")
        span.set_tag(
            "cache.key_prefix",
            cache_key.split(":")[0] if ":" in cache_key else cache_key,
        )

        # Астрологические теги
        span.set_tag("astro.cache.data_type", astro_data_type)
        span.set_tag("astro.domain", "astrology")

        # Метаданные кэша
        for key, value in cache_metadata.items():
            span.set_tag(f"cache.{key}", str(value))

        try:
            start_time = time.time()

            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("cache.duration_ms", duration_ms)
            span.set_tag("cache.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("cache.duration_ms", duration_ms)
            span.set_tag("cache.status", "error")
            span.set_tag("cache.error_type", type(e).__name__)
            span.set_data("cache.error_message", str(e))
            raise


# ==================== BATCH OPERATIONS ====================


@asynccontextmanager
async def trace_batch_database_operation(
    batch_type: str, batch_size: int, operation_type: str, **batch_metadata
):
    """
    Трейс для пакетных операций с базой данных.

    Args:
        batch_type: Тип пакета (bulk_insert, bulk_update, etc.)
        batch_size: Размер пакета
        operation_type: Тип операции
        **batch_metadata: Метаданные пакета
    """
    with start_span(
        op="db.sql.batch",
        description=f"Batch {batch_type}: {batch_size} items",
    ) as span:
        # Теги пакетной операции
        span.set_tag("db.batch.type", batch_type)
        span.set_tag("db.batch.size", batch_size)
        span.set_tag("db.operation", operation_type)
        span.set_tag("db.system", "postgresql")

        # Метаданные пакета
        for key, value in batch_metadata.items():
            span.set_tag(f"db.batch.{key}", str(value))

        try:
            start_time = time.time()

            yield span

            # Успешное завершение
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("db.batch.duration_ms", duration_ms)
            span.set_data(
                "db.batch.throughput_per_sec",
                batch_size / (duration_ms / 1000),
            )
            span.set_tag("db.batch.status", "success")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            span.set_data("db.batch.duration_ms", duration_ms)
            span.set_tag("db.batch.status", "error")
            span.set_tag("db.batch.error_type", type(e).__name__)
            span.set_data("db.batch.error_message", str(e))
            raise


# ==================== CONNECTION POOL MONITORING ====================


async def monitor_connection_pool_health(pool_name: str = "main"):
    """
    Мониторинг здоровья connection pool.

    Args:
        pool_name: Название пула соединений
    """
    try:
        # Здесь должна быть логика получения статистики пула
        # Это зависит от конкретной реализации connection pool

        pool_stats = {
            "pool_name": pool_name,
            "active_connections": 0,  # Получить из пула
            "idle_connections": 0,  # Получить из пула
            "max_connections": 10,  # Получить из конфигурации
        }

        with sentry_sdk.configure_scope() as scope:
            scope.set_context("connection_pool", pool_stats)

        # Предупреждения
        active_conn = pool_stats.get("active_connections", 0)
        max_conn = pool_stats.get("max_connections", 1)
        if (
            isinstance(active_conn, (int, float))
            and isinstance(max_conn, (int, float))
            and active_conn >= max_conn * 0.9
        ):
            sentry_sdk.capture_message(
                f"Connection pool {pool_name} почти исчерпан", level="warning"
            )

    except Exception as e:
        sentry_sdk.capture_exception(e)


# ==================== USAGE EXAMPLES ====================


"""
Примеры использования мониторинга базы данных:

1. Настройка мониторинга SQLAlchemy engine:

    from app.core.database import engine
    from app.core.sentry_database_monitoring import SQLAlchemyMonitor
    
    monitor = SQLAlchemyMonitor()
    monitor.setup_engine_monitoring(engine)

2. Трейс операций с базой данных:

    async def save_horoscope_data(horoscope: dict, zodiac_sign: str):
        with trace_astro_database_operation(
            astro_operation="save_horoscope",
            data_type="daily_horoscope",
            zodiac_sign=zodiac_sign
        ):
            # Сохранение в БД
            result = await db.execute(insert_query, horoscope)
            return result

3. Мониторинг AsyncPG операций:

    async def load_natal_chart(user_id: str):
        query = "SELECT * FROM natal_charts WHERE user_id = $1"
        
        async with trace_asyncpg_operation(
            operation_type="select",
            query=query,
            params_count=1,
            table="natal_charts"
        ):
            result = await connection.fetchrow(query, user_id)
            return result

4. Операции с кэшем:

    async def get_cached_ephemeris(date: str):
        cache_key = f"ephemeris:{date}"
        
        async with trace_astro_cache_operation(
            cache_operation="get",
            cache_key=cache_key,
            astro_data_type="ephemeris_data",
            date=date
        ):
            data = await redis.get(cache_key)
            return data

5. Пакетные операции:

    async def bulk_save_horoscopes(horoscopes: list):
        async with trace_batch_database_operation(
            batch_type="bulk_insert",
            batch_size=len(horoscopes),
            operation_type="insert",
            table="horoscopes"
        ):
            await db.executemany(insert_query, horoscopes)
"""
