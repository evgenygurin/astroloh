# Sentry Advanced Monitoring Setup

## 📊 Настроенные функции Sentry

Полная интеграция расширенного мониторинга Sentry для проекта Astroloh.

### ✅ Реализованные возможности

#### 1. 📝 **Logs (Структурированные логи)**

- Структурированные логи с контекстом
- Астрологические логи с метаданными
- Автоматическая фильтрация чувствительных данных
- Breadcrumbs для трассировки

```python
capture_structured_log(
    level="info",
    message="Операция выполнена",
    extra_data={"zodiac_sign": "leo"},
    tags={"feature": "horoscope"}
)

capture_astrology_log(
    operation="horoscope_generation",
    message="Генерация гороскопа",
    zodiac_sign="leo",
    backend="kerykeion"
)
```

#### 2. 📊 **Metrics (Метрики)**

- Кастомные метрики с единицами измерения
- Distribution метрики для времени выполнения
- Бизнес-метрики для астрологических операций

```python
capture_custom_metric(
    key="astroloh.operation.count",
    value=1,
    unit="count"
)

capture_business_metric(
    operation="horoscope",
    zodiac_sign="leo",
    ai_used=True,
    duration_ms=250
)
```

#### 3. ⚠️ **Breached Metrics & Warnings**

- Автоматические алерты при превышении порогов
- Performance warnings для медленных операций
- Business warnings для fallback сценариев

```python
capture_performance_warning(
    operation="slow_operation",
    actual_duration_ms=3000,
    threshold_ms=1000
)

capture_business_warning(
    warning_type="fallback_used",
    message="Использован fallback",
    severity="medium"
)
```

#### 4. 🔥 **Traces (Распределенная трассировка)**

- Context managers для автоматической трассировки
- Вложенные spans для детализации
- Автоматический сбор метрик производительности

```python
with sentry_trace("operation_name", zodiac_sign="leo"):
    with sentry_span("database_query", db="postgresql"):
        # код операции
        pass
```

#### 5. 📈 **Profiling (Профилирование)**

- CPU профилирование для оптимизации
- Автоматическое профилирование при traces_sample_rate > 0
- Интеграция с трассировками

## 🚀 Демо-эндпоинты для тестирования

### Проверка всех функций

```bash
curl -X POST http://localhost:8000/api/sentry-demo/test-all \
  -H "Content-Type: application/json" \
  -d '{
    "test_type": "all",
    "zodiac_sign": "leo",
    "simulate_error": false,
    "simulate_slow": true
  }'
```

### Тест превышения метрик

```bash
curl http://localhost:8000/api/sentry-demo/test-metrics-breach
```

### Непрерывный мониторинг

```bash
curl http://localhost:8000/api/sentry-demo/test-continuous-monitoring
```

## 📋 Конфигурация

### Переменные окружения

```env
# Обязательные
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production

# Опциональные (с значениями по умолчанию)
SENTRY_RELEASE=1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% трейсов
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% профилей
```

### Интеграции

- ✅ FastAPI/Starlette
- ✅ SQLAlchemy (PostgreSQL)
- ✅ Redis (кэширование)
- ✅ HTTPX (HTTP клиент)
- ✅ Asyncio
- ✅ Logging

## 🛡️ Безопасность

### Автоматическая фильтрация

- Токены и API ключи
- Пароли и секреты
- Персональные данные (birth_time, birth_place)
- Session ID хеширование

### Фильтры данных

- `filter_sensitive_data()` - фильтрация событий
- `filter_breadcrumb_data()` - фильтрация breadcrumbs
- `filter_transaction_data()` - фильтрация транзакций

## 📊 Использование в коде

### Пример интеграции в сервис

```python
from app.core.sentry import (
    sentry_trace,
    sentry_span,
    capture_business_metric,
    capture_astrology_log,
    capture_performance_warning
)

async def generate_horoscope(zodiac_sign: str):
    with sentry_trace("horoscope_generation", zodiac_sign=zodiac_sign):
        # Логирование начала операции
        capture_astrology_log(
            operation="horoscope_generation",
            message=f"Начало генерации для {zodiac_sign}",
            level="info",
            zodiac_sign=zodiac_sign
        )
        
        # Основная операция с вложенными spans
        with sentry_span("ai_generation", backend="yandex_gpt"):
            result = await generate_ai_content(zodiac_sign)
        
        # Метрики
        capture_business_metric(
            operation="horoscope",
            zodiac_sign=zodiac_sign,
            ai_used=True,
            duration_ms=250
        )
        
        return result
```

## 🔍 Мониторинг в Sentry Dashboard

### Доступные представления

1. **Issues** - ошибки и исключения
2. **Performance** - трассировки и производительность
3. **Profiling** - CPU профили
4. **Metrics** - кастомные метрики
5. **Discover** - кастомные запросы

### Рекомендуемые дашборды

- Performance Overview
- Database Query Performance
- API Endpoint Monitoring
- Error Rate by Zodiac Sign
- AI vs Traditional Backend Performance

## 📈 Метрики производительности

### Ключевые метрики

- `astroloh.operation.count` - количество операций
- `astroloh.operation.duration` - время выполнения
- `astroloh.threshold_breach` - превышения порогов
- `astroloh.cpu_usage` - использование CPU
- `astroloh.memory_usage` - использование памяти

### Пороговые значения

- Response time: 500ms (warning), 2000ms (critical)
- CPU usage: 70% (warning), 90% (critical)
- Memory usage: 100MB (warning), 500MB (critical)
- Error rate: 5% (warning), 10% (critical)

## 🚨 Алерты и уведомления

### Настроенные алерты

- Превышение времени ответа > 2 секунд
- Высокая загрузка CPU > 70%
- Fallback на традиционную генерацию
- Ошибки AI генерации
- Превышение лимитов API

## 📚 Дополнительные ресурсы

- [Sentry Logs Documentation](https://docs.sentry.io/product/explore/logs/getting-started/)
- [Sentry Metrics](https://docs.sentry.io/product/metrics/)
- [Sentry Tracing](https://docs.sentry.io/product/performance/)
- [Sentry Profiling](https://docs.sentry.io/product/profiling/)

## ✅ Статус интеграции

| Функция | Статус | Описание |
|---------|--------|----------|
| Logs | ✅ Готово | Структурированные логи с контекстом |
| Metrics | ✅ Готово | Кастомные и бизнес-метрики |
| Breached Metrics | ✅ Готово | Алерты при превышении порогов |
| Warnings | ✅ Готово | Performance и business предупреждения |
| Traces | ✅ Готово | Распределенная трассировка |
| Profiling | ✅ Готово | CPU профилирование |
| Security Filtering | ✅ Готово | Фильтрация чувствительных данных |
| Integrations | ✅ Готово | FastAPI, Redis, PostgreSQL |

---

Последнее обновление: 2025-01-10
