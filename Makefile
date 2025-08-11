# ==============================================================================
# Makefile for NGDB Classifier
#
# Современный Makefile с оптимизированными командами Ruff.
# Использует последние возможности Ruff для максимальной эффективности.
# ==============================================================================

# ------------------------------------------------------------------------------
# Переменные и конфигурация
# ------------------------------------------------------------------------------

.DEFAULT_GOAL := help

# Используем uv для управления виртуальным окружением и пакетами
UV := uv
PYTHON_VERSION := 3.12

# Директории с исходным кодом
PYTHON_DIRS := app tests

# Основные команды с унифицированными параметрами
RUFF := $(UV) run --python $(PYTHON_VERSION) ruff
MYPY := $(UV) run --python $(PYTHON_VERSION) mypy $(PYTHON_DIRS)
PYTEST := $(UV) run --python $(PYTHON_VERSION) pytest

# Цвета для улучшения читаемости вывода
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RED := \033[0;31m
RESET := \033[0m

# ------------------------------------------------------------------------------
# Основные команды для разработчика
# ------------------------------------------------------------------------------

.PHONY: help setup dev clean lint format fix test coverage check-strict security check-env validate
.PHONY: quick-start dev-setup ci-check prod-ready debug restart full-check quick-fix

help:
	@echo "✅ $(GREEN)NGDB Classifier - Современный Makefile с Ruff$(RESET)"
	@echo "-------------------------------------------------------------------"
	@echo "  $(YELLOW)🚀 Сборные команды (workflows):$(RESET)"
	@echo "    make quick-start - Быстрый старт: setup + dev + run"
	@echo "    make dev-setup   - Полная настройка для разработки"
	@echo "    make ci-check    - Проверки для CI/CD (lint + test + security)"
	@echo "    make prod-ready  - Готовность к production"
	@echo "    make restart     - Перезапуск: kill + clean + run"
	@echo "    make quick-fix   - Быстрое исправление: fix + test"
	@echo "    make full-check  - Полная проверка проекта"
	@echo ""
	@echo "  $(YELLOW)Основные команды для ежедневной работы:$(RESET)"
	@echo "    make setup      - Полная первоначальная настройка проекта"
	@echo "    make fix        - ✨ Автоматическое исправление + форматирование"
	@echo "    make lint       - Проверка кода с подробным выводом"
	@echo "    make test       - Запуск тестов с покрытием"
	@echo "    make test-v     - Подробный вывод тестов"
	@echo "    make run        - Запуск приложения для разработки"
	@echo "    make kill       - Остановка процессов на порту 8000"
	@echo ""
	@echo "  $(YELLOW)Команды качества кода:$(RESET)"
	@echo "    make format     - Только форматирование кода"
	@echo "    make check      - Быстрая проверка без исправлений"
	@echo "    make check-strict - Строгая проверка для CI/CD"
	@echo "    make stats      - Статистика проблем по категориям"
	@echo ""
	@echo "  $(YELLOW)Команды Ruff:$(RESET)"
	@echo "    make ruff-docs  - Проверка docstrings"
	@echo "    make ruff-format - Форматирование с Ruff"
	@echo "    make ruff-format-check - Проверка форматирования"
	@echo ""
	@echo "  $(YELLOW)Отчеты для CI/CD:$(RESET)"
	@echo "    make report-json   - Отчет в формате JSON"
	@echo "    make report-github - Отчет для GitHub Actions"
	@echo "    make report-sarif  - Отчет SARIF для безопасности"
	@echo ""
	@echo "  $(YELLOW)Безопасность:$(RESET)"
	@echo "    make security   - Полная проверка безопасности"
	@echo "    make bandit     - Анализ безопасности кода"
	@echo "    make safety     - Проверка уязвимостей зависимостей"
	@echo ""
	@echo "  $(YELLOW)Разработка:$(RESET)"
	@echo "    make hooks      - Установка pre-commit хуков"
	@echo "    make pre-commit - Запуск всех pre-commit проверок"
	@echo "    make clean      - Очистка кэша и временных файлов"
	@echo "    make coverage   - Детальный отчет о покрытии тестами"
	@echo "    make check-env  - Проверка окружения разработки"
	@echo "    make validate   - Полная валидация проекта"
	@echo "    make debug      - Диагностика и отладка"
	@echo ""
	@echo "  $(YELLOW)Docker команды:$(RESET)"
	@echo "    make docker-dev    - 🔧 Запуск development окружения (hot reload)"
	@echo "    make docker-prod   - 🏭 Запуск production окружения"
	@echo "    make docker-up     - Запуск production сервисов"
	@echo "    make docker-down   - Остановка всех Docker сервисов"
	@echo "    make docker-build  - Сборка Docker образов"
	@echo "    make docker-rebuild - Пересборка образов без кэша"
	@echo "    make docker-logs   - Просмотр логов сервисов"
	@echo ""
	@echo "  $(YELLOW)Kerykeion команды:$(RESET)"
	@echo "    make kerykeion-build    - 🏗️ Сборка Docker образа с Kerykeion"
	@echo "    make kerykeion-up       - 🚀 Запуск сервисов с Kerykeion"
	@echo "    make kerykeion-down     - ⏹️ Остановка сервисов с Kerykeion"
	@echo "    make kerykeion-test     - 🧪 Тестирование Kerykeion в Docker"
	@echo "    make kerykeion-logs     - 📋 Логи сервиса с Kerykeion"
	@echo "    make kerykeion-shell    - 🐚 Shell в контейнере с Kerykeion"
	@echo "    make kerykeion-check    - 🔍 Проверка работы Kerykeion"
	@echo "-------------------------------------------------------------------"

# ------------------------------------------------------------------------------
# Установка и настройка
# ------------------------------------------------------------------------------

setup:
	@echo "$(BLUE)🚀 Настройка окружения для разработки...$(RESET)"
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "$(YELLOW)⚠️  uv не найден. Установите uv: https://docs.astral.sh/uv/getting-started/installation/$(RESET)"; \
		exit 1; \
	fi
	@$(UV) sync --dev
	@$(UV) run --python $(PYTHON_VERSION) pre-commit install
	@echo "$(GREEN)✅ Окружение готово! Используйте 'make lint' для проверки$(RESET)"

install:
	@echo "$(BLUE)📦 Установка производственных зависимостей...$(RESET)"
	@$(UV) sync --no-dev

dev:
	@echo "$(BLUE)🔧 Установка зависимостей для разработки...$(RESET)"
	@$(UV) sync --dev

hooks:
	@echo "$(BLUE)🪝 Установка pre-commit хуков...$(RESET)"
	@$(UV) run --python $(PYTHON_VERSION) pre-commit install
	@echo "$(GREEN)✅ Pre-commit хуки активированы$(RESET)"

clean:
	@echo "$(BLUE)🧹 Очистка кэша и временных файлов...$(RESET)"
	@find . -type f -name '*.py[cod]' -delete 2>/dev/null || true
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .ruff_cache/ .mypy_cache/ 2>/dev/null || true
	@echo "$(GREEN)✅ Очистка завершена$(RESET)"

check-env:
	@echo "$(BLUE)🔍 Проверка окружения разработки...$(RESET)"
	@command -v uv >/dev/null 2>&1 || (echo "$(RED)❌ uv не найден$(RESET)" && exit 1)
	@echo "$(BLUE)Версия uv:$(RESET) $$($(UV) --version)"
	@echo "$(BLUE)Проверка зависимостей...$(RESET)"
	@if $(UV) tree 2>/dev/null | head -10; then \
		echo "$(GREEN)Дерево зависимостей доступно$(RESET)"; \
	elif $(UV) run python -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then \
		echo "$(GREEN)Python окружение активно$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Виртуальное окружение может быть не активировано$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Окружение проверено$(RESET)"

validate:
	@echo "$(BLUE)🎯 Полная валидация проекта...$(RESET)"
	@$(MAKE) check-env
	@$(MAKE) lint
	@$(MAKE) test
	@echo "$(GREEN)✅ Проект валиден$(RESET)"

# ------------------------------------------------------------------------------
# Проверка и форматирование кода
# ------------------------------------------------------------------------------

.PHONY: lint format fix check check-strict stats report-json report-github report-sarif ruff-docs ruff-format ruff-format-check ruff-json ruff-github ruff-sarif

lint:
	@echo "$(BLUE)🔍 Полная проверка кода...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --preview
	@$(MYPY)
	@echo "$(GREEN)✅ Проверка завершена$(RESET)"

check:
	@echo "$(BLUE)⚡ Быстрая проверка без исправлений...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --no-fix --preview

format:
	@echo "$(BLUE)🎨 Форматирование кода...$(RESET)"
	@$(RUFF) format $(PYTHON_DIRS) --preview
	@echo "$(GREEN)✅ Код отформатирован$(RESET)"

fix:
	@echo "$(BLUE)🔧 Автоматическое исправление + форматирование...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --fix --preview
	@$(RUFF) format $(PYTHON_DIRS) --preview
	@echo "$(GREEN)✅ Код исправлен и отформатирован$(RESET)"

check-strict:
	@echo "$(BLUE)🎯 Строгая проверка для CI/CD...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --diff --preview
	@$(RUFF) format $(PYTHON_DIRS) --check --diff --preview
	@$(MYPY)

stats:
	@echo "$(BLUE)📊 Статистика проблем по категориям...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --statistics --preview

# Дополнительные команды Ruff (для совместимости с документацией)
ruff-docs:
	@echo "$(BLUE)📚 Проверка docstrings...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --select=D --preview

ruff-format:
	@echo "$(BLUE)🎨 Форматирование с Ruff...$(RESET)"
	@$(RUFF) format $(PYTHON_DIRS) --preview

ruff-format-check:
	@echo "$(BLUE)🔍 Проверка форматирования без изменений...$(RESET)"
	@$(RUFF) format $(PYTHON_DIRS) --check --preview

ruff-json:
	@echo "$(BLUE)📄 JSON отчет Ruff...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --output-format=json --preview

ruff-github:
	@echo "$(BLUE)🐙 GitHub отчет Ruff...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --output-format=github --preview

ruff-sarif:
	@echo "$(BLUE)🔒 SARIF отчет Ruff...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --output-format=sarif --preview

# ------------------------------------------------------------------------------
# Отчеты для CI/CD
# ------------------------------------------------------------------------------

report-json:
	@echo "$(BLUE)📄 Генерация JSON отчета...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --output-format=json --preview

report-github:
	@echo "$(BLUE)🐙 Генерация отчета для GitHub Actions...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --output-format=github --preview

report-sarif:
	@echo "$(BLUE)🔒 Генерация SARIF отчета для безопасности...$(RESET)"
	@$(RUFF) check $(PYTHON_DIRS) --output-format=sarif --preview

# ------------------------------------------------------------------------------
# Безопасность
# ------------------------------------------------------------------------------

.PHONY: security bandit safety

bandit:
	@echo "$(BLUE)🔐 Анализ безопасности кода...$(RESET)"
	@$(UV) run --python $(PYTHON_VERSION) bandit -r app/ -f json -o bandit-report.json || true
	@$(UV) run --python $(PYTHON_VERSION) bandit -r app/

safety:
	@echo "$(BLUE)🛡️  Проверка уязвимостей зависимостей...$(RESET)"
	@$(UV) run --python $(PYTHON_VERSION) safety scan --save-as json safety-report.json || true
	@$(UV) run --python $(PYTHON_VERSION) safety scan

security: bandit safety
	@echo "$(GREEN)✅ Проверки безопасности завершены$(RESET)"

# ------------------------------------------------------------------------------
# Pre-commit и Git хуки
# ------------------------------------------------------------------------------

.PHONY: pre-commit

pre-commit:
	@echo "$(BLUE)🔄 Запуск всех pre-commit проверок...$(RESET)"
	@$(UV) run --python $(PYTHON_VERSION) pre-commit run --all-files

# ------------------------------------------------------------------------------
# Тестирование и покрытие
# ------------------------------------------------------------------------------

.PHONY: test test-v coverage

test:
	@echo "$(BLUE)🧪 Запуск тестов с базовым покрытием...$(RESET)"
	@$(PYTEST) --cov=$(firstword $(PYTHON_DIRS)) --cov-report=term
	@echo "$(GREEN)✅ Тесты завершены$(RESET)"

test-v:
	@echo "$(BLUE)🧪 Запуск тестов с подробным выводом...$(RESET)"
	@$(PYTEST) --cov=$(firstword $(PYTHON_DIRS)) --cov-report=term -v
	@echo "$(GREEN)✅ Тесты завершены$(RESET)"

coverage:
	@echo "$(BLUE)📊 Детальный отчет о покрытии тестами...$(RESET)"
	@$(PYTEST) --cov=$(firstword $(PYTHON_DIRS)) --cov-report=term-missing --cov-report=html --cov-report=json
	@echo "$(GREEN)✅ Отчет сохранен в htmlcov/index.html$(RESET)"

# ------------------------------------------------------------------------------
# Запуск приложения
# ------------------------------------------------------------------------------

.PHONY: run kill docker-up docker-down docker-dev docker-prod docker-logs docker-build docker-rebuild

kill:
	@echo "$(BLUE)🔪 Остановка процессов на порту 8000...$(RESET)"
	@pkill -f "uvicorn.*8000" 2>/dev/null || true
	@if command -v lsof >/dev/null 2>&1; then \
		PIDS=$$(lsof -ti:8000 2>/dev/null) && \
		if [ -n "$$PIDS" ]; then echo "$$PIDS" | xargs kill -9 2>/dev/null || true; fi; \
	else \
		echo "$(YELLOW)⚠️  lsof недоступен, используем только pkill$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Процессы остановлены$(RESET)"

run:
	@echo "$(BLUE)🚀 Запуск FastAPI приложения для разработки...$(RESET)"
	@if [ ! -f .env ]; then echo "$(YELLOW)⚠️  .env файл не найден. Создайте его для настройки$(RESET)"; fi
	@if [ -f .env ]; then \
		set -a && . ./.env && set +a && \
		$(UV) run uvicorn app.main:app --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8000} --reload; \
	else \
		$(UV) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload; \
	fi

# ------------------------------------------------------------------------------
# Docker команды
# ------------------------------------------------------------------------------

docker-build:
	@echo "$(BLUE)🏗️  Сборка Docker образов...$(RESET)"
	@docker-compose build
	@echo "$(GREEN)✅ Образы собраны$(RESET)"

docker-rebuild:
	@echo "$(BLUE)🔄 Пересборка Docker образов без кэша...$(RESET)"
	@docker-compose build --no-cache
	@echo "$(GREEN)✅ Образы пересобраны$(RESET)"

docker-up:
	@echo "$(BLUE)🚀 Запуск production окружения в Docker...$(RESET)"
	@docker-compose up -d
	@echo "$(GREEN)✅ Сервисы запущены:$(RESET)"
	@echo "  - Frontend: http://localhost"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@docker-compose ps

docker-dev:
	@echo "$(BLUE)🔧 Запуск development окружения в Docker...$(RESET)"
	@docker-compose -f docker-compose.dev.yml up
	@echo "$(GREEN)✅ Development сервисы запущены:$(RESET)"
	@echo "  - Frontend (hot reload): http://localhost:3000"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"

docker-down:
	@echo "$(BLUE)⏹️  Остановка Docker сервисов...$(RESET)"
	@docker-compose down
	@docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
	@echo "$(GREEN)✅ Сервисы остановлены$(RESET)"

docker-logs:
	@echo "$(BLUE)📋 Просмотр логов Docker сервисов...$(RESET)"
	@docker-compose logs -f

docker-prod:
	@echo "$(BLUE)🏭 Запуск production окружения...$(RESET)"
	@$(MAKE) docker-build
	@$(MAKE) docker-up

# ==============================================================================
# Сборные команды для различных workflow сценариев
# ==============================================================================

.PHONY: quick-start dev-setup ci-check prod-ready debug restart full-check quick-fix

quick-start:
	@echo "$(BLUE)🚀 Быстрый старт разработки...$(RESET)"
	@$(MAKE) setup
	@$(MAKE) dev
	@$(MAKE) run

dev-setup:
	@echo "$(BLUE)🔧 Полная настройка окружения для разработки...$(RESET)"
	@$(MAKE) setup
	@$(MAKE) dev
	@$(MAKE) hooks
	@$(MAKE) check-env
	@echo "$(GREEN)✅ Окружение разработки готово!$(RESET)"

ci-check:
	@echo "$(BLUE)🎯 Проверки для CI/CD...$(RESET)"
	@$(MAKE) check-strict
	@$(MAKE) test
	@$(MAKE) security
	@echo "$(GREEN)✅ CI/CD проверки пройдены$(RESET)"

prod-ready:
	@echo "$(BLUE)🏭 Проверка готовности к production...$(RESET)"
	@$(MAKE) install
	@$(MAKE) ci-check
	@$(MAKE) coverage
	@echo "$(GREEN)✅ Готов к production deployment$(RESET)"

restart:
	@echo "$(BLUE)🔄 Перезапуск приложения...$(RESET)"
	@$(MAKE) kill
	@$(MAKE) clean
	@$(MAKE) run

quick-fix:
	@echo "$(BLUE)⚡ Быстрое исправление и проверка...$(RESET)"
	@$(MAKE) fix
	@$(MAKE) test
	@echo "$(GREEN)✅ Исправления применены$(RESET)"

full-check:
	@echo "$(BLUE)🔍 Полная проверка проекта...$(RESET)"
	@$(MAKE) check-env
	@$(MAKE) lint
	@$(MAKE) test-v
	@$(MAKE) security
	@$(MAKE) coverage
	@echo "$(GREEN)✅ Полная проверка завершена$(RESET)"

debug:
	@echo "$(BLUE)🐛 Диагностика и отладка...$(RESET)"
	@echo "$(YELLOW)=== Информация о системе ====$(RESET)"
	@$(UV) --version || echo "$(RED)uv не найден$(RESET)"
	@$(UV) run python --version || python --version || echo "$(RED)Python не найден$(RESET)"
	@echo "$(YELLOW)=== Статус виртуального окружения ====$(RESET)"
	@if $(UV) tree 2>/dev/null | head -10; then \
		echo "$(GREEN)Дерево зависимостей активно$(RESET)"; \
	elif $(UV) run python -c "import sys; print('Пакеты:'); import pkg_resources; [print(f'  {d.project_name}=={d.version}') for d in sorted(pkg_resources.working_set, key=lambda x: x.project_name)[:10]]" 2>/dev/null; then \
		echo "$(GREEN)Основные пакеты доступны$(RESET)"; \
	else \
		echo "$(RED)Окружение не активировано$(RESET)"; \
	fi
	@echo "$(YELLOW)=== Статус процессов на порту 8000 ====$(RESET)"
	@if command -v lsof >/dev/null 2>&1; then \
		lsof -i :8000 || echo "$(GREEN)Порт 8000 свободен$(RESET)"; \
	else \
		echo "$(YELLOW)lsof недоступен для проверки портов$(RESET)"; \
	fi
	@echo "$(YELLOW)=== Проверка конфигурации ====$(RESET)"
	@[ -f .env ] && echo "$(GREEN).env найден$(RESET)" || echo "$(YELLOW).env отсутствует$(RESET)"
	@[ -f pyproject.toml ] && echo "$(GREEN)pyproject.toml найден$(RESET)" || echo "$(RED)pyproject.toml отсутствует$(RESET)"
	@[ -f uv.lock ] && echo "$(GREEN)uv.lock найден$(RESET)" || echo "$(YELLOW)uv.lock отсутствует$(RESET)"
	@echo "$(GREEN)✅ Диагностика завершена$(RESET)"

# ------------------------------------------------------------------------------
# Kerykeion команды для работы с профессиональной астрологией
# ------------------------------------------------------------------------------

.PHONY: kerykeion-build kerykeion-up kerykeion-down kerykeion-test kerykeion-logs kerykeion-shell kerykeion-check

kerykeion-build:
	@echo "$(BLUE)🏗️ Сборка Docker образа с Kerykeion...$(RESET)"
	@docker build -f Dockerfile.kerykeion -t astroloh-kerykeion --load .
	@echo "$(GREEN)✅ Образ с Kerykeion собран$(RESET)"

kerykeion-up:
	@echo "$(BLUE)🚀 Запуск сервисов с Kerykeion...$(RESET)"
	@docker-compose -f docker-compose.kerykeion.yml up -d
	@echo "$(GREEN)✅ Сервисы с Kerykeion запущены$(RESET)"
	@docker-compose -f docker-compose.kerykeion.yml ps

kerykeion-down:
	@echo "$(BLUE)⏹️ Остановка сервисов с Kerykeion...$(RESET)"
	@docker-compose -f docker-compose.kerykeion.yml down
	@echo "$(GREEN)✅ Сервисы с Kerykeion остановлены$(RESET)"

kerykeion-test:
	@echo "$(BLUE)🧪 Тестирование Kerykeion в Docker...$(RESET)"
	@docker-compose -f docker-compose.kerykeion.yml exec backend-kerykeion python test_kerykeion_docker.py

kerykeion-logs:
	@echo "$(BLUE)📋 Логи сервиса с Kerykeion...$(RESET)"
	@docker-compose -f docker-compose.kerykeion.yml logs -f backend-kerykeion

kerykeion-shell:
	@echo "$(BLUE)🐚 Открытие shell в контейнере с Kerykeion...$(RESET)"
	@docker-compose -f docker-compose.kerykeion.yml exec backend-kerykeion /bin/bash

kerykeion-check:
	@echo "$(BLUE)🔍 Проверка работы Kerykeion...$(RESET)"
	@docker run --rm astroloh-kerykeion python -c "import kerykeion; print('✅ Kerykeion доступен')"
	@docker run --rm astroloh-kerykeion python -c "import swisseph as swe; print('✅ Swiss Ephemeris доступен')"
	@docker run --rm astroloh-kerykeion python -c "from app.services.astrology_calculator import AstrologyCalculator; calc = AstrologyCalculator(); print('✅ AstrologyCalculator работает с бэкендами:', calc._get_available_backends())"
