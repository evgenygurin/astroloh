# Astroloh с Kerykeion - Docker инструкции

## 🚀 Быстрый старт

### По умолчанию (с Kerykeion)
```bash
# Запуск с полной поддержкой Kerykeion (рекомендуется)
make docker-up

# Или напрямую
docker-compose up -d
```

### Минимальная версия (без Kerykeion)
```bash
# Запуск без Kerykeion для быстрого тестирования
make minimal-up

# Или напрямую
docker-compose -f docker-compose.minimal.yml up -d
```

## 📋 Доступные команды

### Основные команды
```bash
# Сборка образов
make docker-build

# Запуск сервисов
make docker-up          # С Kerykeion (по умолчанию)
make minimal-up         # Без Kerykeion

# Остановка сервисов
make docker-down
make minimal-down

# Просмотр логов
make docker-logs
```

### Kerykeion команды
```bash
# Проверка работы Kerykeion
make kerykeion-check

# Сборка образа с Kerykeion
make kerykeion-build

# Запуск только Kerykeion сервисов
make kerykeion-up
make kerykeion-down

# Тестирование в Docker
make kerykeion-test

# Shell в контейнере
make kerykeion-shell
```

## 🔧 Конфигурация

### Переменные окружения
Создайте файл `.env` в корне проекта:

```env
# Яндекс API
YANDEX_API_KEY=your_api_key
YANDEX_FOLDER_ID=your_folder_id
YANDEX_CATALOG_ID=your_catalog_id

# Безопасность
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key

# Ngrok (опционально)
NGROK_AUTHTOKEN=your_ngrok_token
```

### Включение/отключение Kerykeion
- **По умолчанию**: Kerykeion включен в основном `docker-compose.yml`
- **Минимальная версия**: Kerykeion отключен в `docker-compose.minimal.yml`

## 🐛 Устранение проблем

### Проблема: "No module named 'kerykeion'"
```bash
# Пересоберите образ
make docker-rebuild

# Или проверьте установку
make kerykeion-check
```

### Проблема: Зависание при сборке
```bash
# Очистите Docker кэш
docker system prune -a

# Пересоберите без кэша
make docker-rebuild
```

### Проблема: Недостаточно места на диске
```bash
# Очистите неиспользуемые образы
docker image prune -a

# Очистите все Docker данные
docker system prune -a --volumes
```

## 📊 Проверка работоспособности

### Проверка Kerykeion
```bash
# Локальная проверка
python check_kerykeion.py

# Проверка в Docker
make kerykeion-check
```

### Проверка API
```bash
# Проверка здоровья
curl http://localhost:8000/health

# Проверка документации
open http://localhost:8000/docs
```

## 🔄 Миграция между версиями

### Переход с Kerykeion на минимальную версию
```bash
# Остановите текущие сервисы
make docker-down

# Запустите минимальную версию
make minimal-up
```

### Переход с минимальной на полную версию
```bash
# Остановите минимальную версию
make minimal-down

# Запустите полную версию
make docker-up
```

## 📝 Логи и отладка

### Просмотр логов
```bash
# Все сервисы
make docker-logs

# Только backend
docker-compose logs -f backend

# Только Kerykeion сервисы
make kerykeion-logs
```

### Отладка в контейнере
```bash
# Shell в backend контейнере
docker-compose exec backend /bin/bash

# Shell в Kerykeion контейнере
make kerykeion-shell
```

## 🏗️ Архитектура

### Сервисы с Kerykeion
- `backend` - FastAPI приложение с полной поддержкой астрологии
- `frontend` - Веб-интерфейс
- `db` - PostgreSQL база данных
- `redis` - Кэширование и сессии
- `ngrok-backend` - Туннель для backend API
- `ngrok-frontend` - Туннель для frontend

### Зависимости Kerykeion
- `kerykeion>=4.26.0` - Основная астрологическая библиотека
- `pyswisseph==2.10.3.2` - Swiss Ephemeris для точных расчетов
- `skyfield==1.49` - Астрономические расчеты
- `astropy==6.0.0` - Профессиональная астрономия

## 🚀 Production развертывание

### Рекомендуемая конфигурация
```bash
# Сборка production образов
make docker-build

# Запуск production сервисов
make docker-up

# Проверка работоспособности
make kerykeion-check
```

### Мониторинг
```bash
# Проверка статуса сервисов
docker-compose ps

# Проверка здоровья
curl http://localhost:8000/health

# Просмотр логов
make docker-logs
```

## 📚 Дополнительные ресурсы

- [Kerykeion документация](https://github.com/g-b-r/kerykeion)
- [Swiss Ephemeris](https://www.astro.com/swisseph/)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Docker Compose документация](https://docs.docker.com/compose/)
