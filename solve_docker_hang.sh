#!/bin/bash

echo "=== Решение проблемы зависания Docker Compose ==="
echo ""

# Останавливаем все запущенные контейнеры
echo "1. Останавливаем все контейнеры..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true
docker-compose -f docker-compose.optimized.yml down 2>/dev/null || true
docker-compose -f docker-compose.test.yml down 2>/dev/null || true

# Очищаем Docker кэш
echo "2. Очищаем Docker кэш..."
docker system prune -f 2>/dev/null || echo "Docker недоступен"

# Увеличиваем энтропию
echo "3. Увеличиваем энтропию системы..."
sudo pkill haveged 2>/dev/null || true
sudo haveged -F &
HAVEGED_PID=$!
sleep 10

# Проверяем энтропию
ENTROPY=$(cat /proc/sys/kernel/random/entropy_avail)
echo "   Уровень энтропии: $ENTROPY"

echo ""
echo "4. Пробуем запустить тестовую версию..."
echo "   Это поможет определить, в чем проблема"
echo ""

# Запускаем тестовую версию
if docker-compose -f docker-compose.test.yml up --build -d; then
    echo "✅ Тестовая версия запущена успешно!"
    echo ""
    echo "Теперь попробуйте запустить основную версию:"
    echo "   docker-compose up --build"
    echo ""
    echo "Или минимальную версию:"
    echo "   docker-compose -f docker-compose.minimal.yml up --build"
else
    echo "❌ Тестовая версия не запустилась"
    echo ""
    echo "Попробуйте следующие шаги:"
    echo "1. Перезапустите Docker: sudo systemctl restart docker"
    echo "2. Проверьте логи: docker-compose -f docker-compose.test.yml logs"
    echo "3. Попробуйте сборку без кэша: docker-compose -f docker-compose.test.yml build --no-cache"
fi

# Останавливаем haveged
kill $HAVEGED_PID 2>/dev/null || true

echo ""
echo "=== Альтернативные решения ==="
echo "Если проблема сохраняется:"
echo ""
echo "1. Используйте Docker BuildKit:"
echo "   DOCKER_BUILDKIT=1 docker-compose up --build"
echo ""
echo "2. Запустите с увеличенным таймаутом:"
echo "   COMPOSE_HTTP_TIMEOUT=300 docker-compose up --build"
echo ""
echo "3. Попробуйте пошаговую сборку:"
echo "   docker-compose build --no-cache backend"
echo "   docker-compose up db"
echo "   docker-compose up backend"
echo ""
echo "4. Проверьте системные ресурсы:"
echo "   free -h"
echo "   df -h"
echo "   cat /proc/sys/kernel/random/entropy_avail"