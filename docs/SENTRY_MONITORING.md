# Sentry мониторинг для Astroloh

## Обзор

Astroloh интегрирован с Sentry для всестороннего мониторинга ошибок, производительности и пользовательского опыта. Система обеспечивает отслеживание критических метрик для астрологического приложения и интерфейсов Yandex Alice.

## Быстрая настройка

### 1. Создание Sentry проекта

1. Зарегистрируйтесь на [sentry.io](https://sentry.io)
2. Создайте новую организацию (если нужно)
3. Создайте новый проект:
   - Platform: **Python**
   - Framework: **FastAPI**
   - Название: **Astroloh**

### 2. Получение DSN

После создания проекта скопируйте DSN из Settings → Client Keys (DSN):

```
https://your_key@sentry.io/your_project_id
```

### 3. Настройка окружения

Добавьте в `.env` файл:

```bash
SENTRY_DSN=your_dsn_here
SENTRY_ENVIRONMENT=development  # или staging/production
SENTRY_RELEASE=1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

## Возможности мониторинга

### 🚨 Отслеживание ошибок

**Автоматически отслеживаются:**

- Исключения Python во всех сервисах
- Ошибки FastAPI маршрутов
- Проблемы с базой данных PostgreSQL  
- Ошибки внешних API (Yandex GPT)
- Сбои астрологических расчетов Kerykeion

**Пример отчета об ошибке:**

```python
# Автоматически отправляется в Sentry
try:
    horoscope = await ai_horoscope_service.generate_enhanced_horoscope(
        zodiac_sign=YandexZodiacSign.LEO
    )
except Exception as e:
    # Sentry автоматически получает контекст:
    # - Знак зодиака: LEO  
    # - AI включен: True
    # - Период: DAILY
    # - Полный stack trace
    raise
```

### 📊 Мониторинг производительности

**Отслеживаемые операции:**

- Время обработки webhook'ов Alice (цель: <3000ms)
- Скорость генерации гороскопов
- Производительность Kerykeion расчетов
- Время ответа Yandex GPT API
- Эффективность кэширования

**Кастомные метрики:**

```python
capture_performance_metrics(
    operation_name="alice_webhook",
    duration_ms=1250,
    success=True,
    response_has_buttons=True,
    session_new=False,
)
```

### 🔍 Астрологический контекст

**Специализированные теги для астрологии:**

- `astro.operation`: horoscope_generation, compatibility, natal_chart
- `astro.zodiac_sign`: leo, virgo, libra, etc.
- `astro.backend`: kerykeion, skyfield, built-in
- `astro.ai_enabled`: true/false

**Alice специфичные теги:**

- `alice.intent`: horoscope, compatibility, greet, etc.
- `alice.response_type`: text, card, buttons
- `alice.session`: хешированный ID сессии

### 🔒 Защита персональных данных

**Автоматически фильтруются:**

- Точное время рождения пользователей
- Координаты места рождения  
- API ключи и токены
- Полные user_id (заменяются хешами)
- Персональная информация из запросов

**Пример фильтрации:**

```json
{
  "user": {
    "id": "session_1234"  // вместо полного Yandex user_id
  },
  "request": {
    "birth_time": "[Filtered]",
    "birth_place": "[Filtered]"
  }
}
```

## Конфигурации по средам

### Development

```bash
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0    # Все трейсы
SENTRY_PROFILES_SAMPLE_RATE=0.5  # 50% профилей
```

**Цель:** Максимальная информация для отладки

### Staging  

```bash
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.3    # 30% трейсов
SENTRY_PROFILES_SAMPLE_RATE=0.2  # 20% профилей
```

**Цель:** Валидация перед production

### Production

```bash
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1    # 10% трейсов  
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% профилей
```

**Цель:** Минимальный overhead, критические проблемы

## Интеграции

### FastAPI

- Автоматическое отслеживание всех HTTP запросов
- Трейсинг маршрутов API
- Middleware интеграция

### PostgreSQL

- SQL запросы и их производительность
- Ошибки подключения к БД
- Медленные запросы

### External APIs

- Yandex GPT API запросы
- Ошибки и таймауты
- Rate limiting статус

### Background Tasks

- Мониторинг фоновых задач
- Производительность кэш warming'а
- Статус системных компонентов

## Алерты и уведомления

### Рекомендуемые алерты

**Критичные (немедленно):**

- Error rate > 5% за 5 минут
- Response time > 5000ms для Alice webhook
- Yandex GPT API недоступен
- База данных недоступна

**Предупреждения (в течение часа):**

- Error rate > 2% за 15 минут  
- Response time > 3000ms для Alice
- Fallback rate > 25%
- Память использована > 80%

**Информационные (ежедневно):**

- Ежедневная сводка ошибок
- Статистика производительности
- Использование AI vs традиционных методов

### Настройка алертов

1. В Sentry перейдите в **Alerts** → **Create Alert Rule**
2. Выберите проект **Astroloh**
3. Настройте условия:

**Пример: Alert для медленных Alice ответов**

```
WHEN transaction.duration is greater than 3000ms
FOR transactions matching tag alice.intent:*
SEND notification to #alerts-astroloh
```

## Дашборды и аналитика

### Основной дашборд

- Общая производительность приложения
- Error rate по времени
- Топ ошибок за период  
- Производительность по операциям

### Alice-специфичный дашборд

- Время ответа по интентам
- Популярность функций (гороскопы vs совместимость)
- Успешность AI генерации
- Статистика по знакам зодиака

### Астрологический дашборд

- Производительность Kerykeion
- Использование различных бэкендов
- Кэш hit rate для расчетов
- Популярность астрологических операций

## Troubleshooting

### Sentry не получает события

1. **Проверьте DSN:**

   ```bash
   python -c "from app.core.config import settings; print(settings.SENTRY_DSN)"
   ```

2. **Тестовая отправка ошибки:**

   ```python
   import sentry_sdk
   sentry_sdk.capture_message("Тест Sentry интеграции")
   ```

3. **Проверьте логи приложения:**

   ```bash
   grep "Sentry" logs/astroloh.log
   ```

### Слишком много событий

1. **Уменьшите sample rates:**

   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.05
   SENTRY_PROFILES_SAMPLE_RATE=0.05
   ```

2. **Настройте фильтры в Sentry UI:**
   - Игнорировать определенные ошибки
   - Фильтровать по URL или тегам

### Нет данных производительности

1. **Убедитесь в включенности трейсинга:**

   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.1  # Больше 0
   ```

2. **Проверьте транзакции в коде:**

   ```python
   with sentry_sdk.start_transaction(op="astrology", name="horoscope_gen"):
       # ваш код
   ```

## Команды для управления

### Тест интеграции

```bash
python -c "
import sentry_sdk
from app.core.sentry import init_sentry
init_sentry()
sentry_sdk.capture_message('Sentry работает!', level='info')
print('Тестовое сообщение отправлено')
"
```

### Мониторинг в реальном времени

```bash
# Просмотр логов с Sentry событиями
tail -f logs/astroloh.log | grep -i sentry
```

### Docker development

```bash
docker-compose exec backend python -c "
from app.core.config import settings
print(f'Sentry DSN: {settings.SENTRY_DSN[:20]}...')
print(f'Environment: {settings.SENTRY_ENVIRONMENT}')
"
```

## Best Practices

### 1. Используйте контекст

```python
with sentry_sdk.configure_scope() as scope:
    scope.set_tag("feature", "horoscope_generation")
    scope.set_context("astrology", {"zodiac": "leo"})
    # ваш код
```

### 2. Контролируйте sample rates

- Development: высокие rates для отладки
- Production: низкие rates для производительности

### 3. Настройте алерты с умом

- Не слишком чувствительные (избежать шума)
- Не слишком грубые (пропустить проблемы)

### 4. Используйте релизы

```bash
SENTRY_RELEASE=$(git rev-parse --short HEAD)
```

### 5. Мониторьте business метрики

- Успешность генерации гороскопов
- Популярность астрологических функций
- Удовлетворенность пользователей Alice

## Интеграция с Claude MCP

Sentry MCP сервер уже настроен в Claude для:

- Просмотра ошибок в реальном времени
- Анализа производительности
- Управления релизами
- Создания и просмотра алертов

После настройки DSN вы сможете использовать Sentry команды прямо в Claude для мониторинга состояния Astroloh.

## Дополнительные ресурсы

- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Alerts & Notifications](https://docs.sentry.io/product/alerts/)
