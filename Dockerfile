FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем директорию для Swiss Ephemeris данных
RUN mkdir -p /app/swisseph

# Копируем код приложения
COPY app/ ./app/

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash astroloh
RUN chown -R astroloh:astroloh /app
USER astroloh

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]