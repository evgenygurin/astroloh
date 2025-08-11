#!/bin/bash

echo "=== Диагностика проблемы зависания Docker Compose ==="

# Проверяем уровень энтропии
echo "1. Проверяем уровень энтропии системы..."
ENTROPY=$(cat /proc/sys/kernel/random/entropy_avail)
echo "   Текущий уровень энтропии: $ENTROPY"

if [ "$ENTROPY" -lt 1000 ]; then
    echo "   ⚠️  Уровень энтропии низкий! Устанавливаем haveged..."
    sudo apt-get update -qq
    sudo apt-get install -y haveged
    sudo haveged -F &
    HAVEGED_PID=$!
    sleep 10
    NEW_ENTROPY=$(cat /proc/sys/kernel/random/entropy_avail)
    echo "   ✅ Новый уровень энтропии: $NEW_ENTROPY"
else
    echo "   ✅ Уровень энтропии в норме"
fi

# Проверяем доступную память
echo "2. Проверяем доступную память..."
FREE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
echo "   Доступная память: ${FREE_MEM}MB"

if [ "$FREE_MEM" -lt 2048 ]; then
    echo "   ⚠️  Мало памяти! Рекомендуется минимум 2GB"
else
    echo "   ✅ Памяти достаточно"
fi

# Проверяем свободное место на диске
echo "3. Проверяем свободное место на диске..."
FREE_DISK=$(df -h . | awk 'NR==2{print $4}' | sed 's/G//')
echo "   Свободное место: ${FREE_DISK}GB"

if [ "$FREE_DISK" -lt 5 ]; then
    echo "   ⚠️  Мало места на диске! Рекомендуется минимум 5GB"
else
    echo "   ✅ Места на диске достаточно"
fi

# Очищаем Docker кэш (если Docker доступен)
echo "4. Очищаем Docker кэш..."
if command -v docker &> /dev/null; then
    docker system prune -f
    echo "   ✅ Docker кэш очищен"
else
    echo "   ℹ️  Docker не найден в системе"
fi

# Создаем .env файл с дефолтными значениями если его нет
echo "5. Проверяем .env файл..."
if [ ! -f .env ]; then
    echo "   Создаем .env файл с дефолтными значениями..."
    cat > .env << EOF
# Default environment variables
YANDEX_API_KEY=
YANDEX_FOLDER_ID=
YANDEX_CATALOG_ID=
SECRET_KEY=default_secret_key_change_in_production
ENCRYPTION_KEY=default_encryption_key_change_in_production
NGROK_AUTHTOKEN=
EOF
    echo "   ✅ .env файл создан"
else
    echo "   ✅ .env файл существует"
fi

echo ""
echo "=== Рекомендации ==="
echo "1. Попробуйте запустить минимальную версию:"
echo "   docker-compose -f docker-compose.minimal.yml up --build"
echo ""
echo "2. Если проблема сохраняется, попробуйте оптимизированную версию:"
echo "   docker-compose -f docker-compose.optimized.yml up --build"
echo ""
echo "3. Для отладки используйте:"
echo "   docker-compose -f docker-compose.minimal.yml up --build --verbose"
echo ""
echo "4. Если все еще зависает, попробуйте пошаговую сборку:"
echo "   docker-compose -f docker-compose.minimal.yml build --no-cache backend"
echo "   docker-compose -f docker-compose.minimal.yml up db"
echo "   docker-compose -f docker-compose.minimal.yml up backend"