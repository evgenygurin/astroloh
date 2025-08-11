# 🐳 Astroloh с Kerykeion в Docker

Этот документ описывает, как запустить Astroloh с полной поддержкой Kerykeion в Docker окружении.

## 🚀 Быстрый старт

### 1. Сборка и запуск

```bash
# Собрать образ с Kerykeion
make -f Makefile.kerykeion build

# Запустить сервисы
make -f Makefile.kerykeion up

# Проверить статус
make -f Makefile.kerykeion status
```

### 2. Проверка работы Kerykeion

```bash
# Полная проверка всех компонентов
make -f Makefile.kerykeion full-check

# Или отдельные проверки:
make -f Makefile.kerykeion check-kerykeion
make -f Makefile.kerykeion check-swisseph
make -f Makefile.kerykeion check-backends
```

### 3. Просмотр логов

```bash
make -f Makefile.kerykeion logs
```

## 📋 Доступные команды

### Основные команды

| Команда | Описание |
|---------|----------|
| `make -f Makefile.kerykeion help` | Показать справку |
| `make -f Makefile.kerykeion build` | Собрать Docker образ |
| `make -f Makefile.kerykeion up` | Запустить сервисы |
| `make -f Makefile.kerykeion down` | Остановить сервисы |
| `make -f Makefile.kerykeion logs` | Показать логи |
| `make -f Makefile.kerykeion status` | Статус сервисов |

### Команды для разработки

| Команда | Описание |
|---------|----------|
| `make -f Makefile.kerykeion dev` | Запуск в режиме разработки |
| `make -f Makefile.kerykeion test` | Запустить тесты |
| `make -f Makefile.kerykeion test-shell` | Открыть shell в контейнере |
| `make -f Makefile.kerykeion migrate` | Запустить миграции БД |

### Команды проверки

| Команда | Описание |
|---------|----------|
| `make -f Makefile.kerykeion check-kerykeion` | Проверить Kerykeion |
| `make -f Makefile.kerykeion check-swisseph` | Проверить Swiss Ephemeris |
| `make -f Makefile.kerykeion check-backends` | Проверить доступные бэкенды |
| `make -f Makefile.kerykeion full-check` | Полная проверка |

## 🔧 Конфигурация

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# База данных
DATABASE_URL=postgresql+asyncpg://astroloh_user:astroloh_password@db:5432/astroloh_db

# Yandex API
YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_folder_id
YANDEX_CATALOG_ID=your_catalog_id

# Безопасность
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key

# Kerykeion
KERYKEION_ENABLED=true
SWISSEPH_ENABLED=true
```

### Структура файлов

```text
astroloh/
├── Dockerfile.kerykeion          # Dockerfile с Kerykeion
├── docker-compose.kerykeion.yml  # Docker Compose для Kerykeion
├── Makefile.kerykeion            # Makefile для управления
├── test_kerykeion_docker.py      # Тесты Kerykeion
└── DOCKER_KERYKEION_README.md    # Этот файл
```

## 🧪 Тестирование

### Автоматические тесты

```bash
# Запустить все тесты
make -f Makefile.kerykeion test
```

### Ручное тестирование

```bash
# Открыть shell в контейнере
make -f Makefile.kerykeion test-shell

# Внутри контейнера:
python test_kerykeion_docker.py
```

## 🔍 Диагностика

### Проверка доступности сервисов

```bash
# Проверить здоровье
make -f Makefile.kerykeion health

# Проверить логи
make -f Makefile.kerykeion logs
```

### Проверка зависимостей

```bash
# Проверить установленные пакеты
docker-compose -f docker-compose.kerykeion.yml exec backend-kerykeion pip list | grep -E "(kerykeion|swisseph|skyfield|astropy)"
```

## 🐛 Устранение неполадок

### Проблема: Ошибка компиляции pyswisseph

**Решение:** Убедитесь, что используются правильные системные зависимости:

```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    libc6-dev \
    libsqlite3-dev \
    libswe-dev
```

### Проблема: Kerykeion не импортируется

**Решение:** Проверьте установку зависимостей:

```bash
make -f Makefile.kerykeion install-deps
```

### Проблема: База данных не подключается

**Решение:** Проверьте переменные окружения и миграции:

```bash
make -f Makefile.kerykeion migrate
```

## 📊 Мониторинг

### Логи приложения

```bash
# Логи в реальном времени
make -f Makefile.kerykeion logs

# Логи с фильтрацией
docker-compose -f docker-compose.kerykeion.yml logs -f backend-kerykeion | grep -i kerykeion
```

### Метрики производительности

```bash
# Использование ресурсов
docker stats

# Проверка здоровья
curl http://localhost:8000/health
```

## 🔄 Обновление

### Обновление зависимостей

```bash
# Пересобрать образ
make -f Makefile.kerykeion build-dev

# Перезапустить сервисы
make -f Makefile.kerykeion restart
```

### Очистка

```bash
# Очистить все Docker ресурсы
make -f Makefile.kerykeion clean
```

## 📚 Дополнительные ресурсы

- [Kerykeion Documentation](https://github.com/g-b-r/kerykeion)
- [Swiss Ephemeris](https://www.astro.com/swisseph/)
- [Docker Documentation](https://docs.docker.com/)

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи: `make -f Makefile.kerykeion logs`
2. Запустите диагностику: `make -f Makefile.kerykeion full-check`
3. Проверьте статус сервисов: `make -f Makefile.kerykeion status`
