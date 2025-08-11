#!/bin/bash

# Увеличиваем энтропию перед запуском
echo "Увеличиваем энтропию системы..."
sudo haveged -F &
HAVEGED_PID=$!

# Ждем увеличения энтропии
echo "Ожидаем увеличения энтропии..."
sleep 10

# Проверяем уровень энтропии
ENTROPY=$(cat /proc/sys/kernel/random/entropy_avail)
echo "Текущий уровень энтропии: $ENTROPY"

# Запускаем Docker Compose с дополнительными параметрами
echo "Запускаем Docker Compose..."
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose up --build -d

# Останавливаем haveged
kill $HAVEGED_PID 2>/dev/null || true

echo "Docker Compose запущен!"