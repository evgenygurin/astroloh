FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей, код приложения и конфигурацию для миграций
COPY requirements.txt .
COPY pyproject.toml .
COPY alembic.ini .
COPY migrations/ ./migrations/
COPY app/ ./app/

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию для Swiss Ephemeris данных
RUN mkdir -p /app/swisseph

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash astroloh
RUN chown -R astroloh:astroloh /app
USER astroloh

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]