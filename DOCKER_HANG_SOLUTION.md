# Решение проблемы зависания Docker Compose

## Проблема
Docker Compose зависает на последней строке сборки, особенно при использовании `Dockerfile.kerykeion`.

## Причины
1. **Низкий уровень энтропии системы** (основная причина)
2. Большой контекст сборки
3. Проблемы с зависимостями между сервисами
4. Недостаток системных ресурсов

## Быстрое решение

### 1. Запустите диагностический скрипт
```bash
./fix_docker_hang.sh
```

### 2. Запустите скрипт решения
```bash
./solve_docker_hang.sh
```

### 3. Альтернативные команды

#### Тестовая версия (без Kerykeion)
```bash
docker-compose -f docker-compose.test.yml up --build
```

#### Минимальная версия
```bash
docker-compose -f docker-compose.minimal.yml up --build
```

#### Оптимизированная версия
```bash
docker-compose -f docker-compose.optimized.yml up --build
```

## Ручное решение

### 1. Увеличить энтропию
```bash
# Установить haveged
sudo apt-get update && sudo apt-get install -y haveged

# Запустить haveged
sudo haveged -F &

# Проверить уровень энтропии
cat /proc/sys/kernel/random/entropy_avail
```

### 2. Очистить Docker кэш
```bash
docker system prune -f
docker volume prune -f
```

### 3. Использовать BuildKit
```bash
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose up --build
```

### 4. Увеличить таймаут
```bash
COMPOSE_HTTP_TIMEOUT=300 docker-compose up --build
```

### 5. Пошаговая сборка
```bash
# Сначала собрать образ
docker-compose build --no-cache backend

# Затем запустить базу данных
docker-compose up db

# И наконец backend
docker-compose up backend
```

## Файлы решения

### Созданные файлы:
- `docker-compose.minimal.yml` - минимальная версия без frontend и ngrok
- `docker-compose.optimized.yml` - оптимизированная версия с лимитами ресурсов
- `docker-compose.test.yml` - тестовая версия с упрощенным Dockerfile
- `Dockerfile.test` - упрощенный Dockerfile без проблемных операций
- `fix_docker_hang.sh` - диагностический скрипт
- `solve_docker_hang.sh` - скрипт решения проблемы
- `.env` - файл с дефолтными переменными окружения

## Проверка решения

### 1. Проверьте уровень энтропии
```bash
cat /proc/sys/kernel/random/entropy_avail
# Должно быть > 1000
```

### 2. Проверьте системные ресурсы
```bash
free -h  # Память
df -h    # Диск
```

### 3. Проверьте статус контейнеров
```bash
docker-compose ps
```

## Если проблема сохраняется

1. **Перезапустите Docker**
   ```bash
   sudo systemctl restart docker
   ```

2. **Проверьте логи**
   ```bash
   docker-compose logs backend
   ```

3. **Используйте verbose режим**
   ```bash
   docker-compose up --build --verbose
   ```

4. **Проверьте порты**
   ```bash
   netstat -tulpn | grep :8000
   ```

## Рекомендации для продакшена

1. Используйте `docker-compose.optimized.yml` с лимитами ресурсов
2. Настройте мониторинг уровня энтропии
3. Используйте health checks для всех сервисов
4. Настройте автоматический перезапуск контейнеров
5. Используйте Docker BuildKit для ускорения сборки

## Контакты

Если проблема не решается, проверьте:
- Логи Docker: `docker system df`
- Системные ресурсы: `htop`, `iotop`
- Сетевые соединения: `netstat -tulpn`