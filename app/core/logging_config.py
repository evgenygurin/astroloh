"""
Конфигурация логирования для приложения Astroloh.
Поддерживает запись в файл с ротацией и вывод в консоль.
"""

import logging
import logging.handlers
from pathlib import Path

from app.core.config import settings


def setup_logging() -> None:
    """
    Настраивает логирование для приложения.

    Создает следующие хэндлеры:
    - Консольный вывод с цветной подсветкой
    - Файловый вывод с ротацией
    """
    # Создаем директорию для логов если не существует
    log_file_path = Path(settings.LOG_FILE_PATH)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Получаем уровень логирования
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Создаем форматтеры
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Очищаем существующие хэндлеры
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Консольный хэндлер
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Файловый хэндлер с ротацией (если включено)
    if settings.LOG_TO_FILE:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOG_FILE_PATH,
            maxBytes=settings.LOG_MAX_SIZE
            * 1024
            * 1024,  # Конвертируем MB в байты
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Настраиваем специфичные логгеры для приложения
    app_loggers = [
        "app",
        "app.api",
        "app.api.yandex_dialogs",
        "app.services",
        "app.services.dialog_handler",
        "app.services.ai_horoscope_service",
        "app.services.conversation_manager",
        "app.core",
        "uvicorn.access",
        "uvicorn.error",
    ]

    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        # Не добавляем хэндлеры - они наследуются от корневого
        logger.propagate = True

    # Уменьшаем уровень для сторонних библиотек
    external_loggers = {
        "httpx": logging.WARNING,
        "urllib3": logging.WARNING,
        "requests": logging.WARNING,
        "asyncio": logging.WARNING,
        "slowapi": logging.WARNING,
        "fastapi": logging.INFO,
    }

    for logger_name, level in external_loggers.items():
        logging.getLogger(logger_name).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    Получает логгер с заданным именем.

    Args:
        name: Имя логгера

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)


def log_startup_info() -> None:
    """Логирует информацию о запуске приложения."""
    logger = get_logger(__name__)

    logger.info("🚀 ASTROLOH STARTUP")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Log to file: {settings.LOG_TO_FILE}")

    if settings.LOG_TO_FILE:
        logger.info(f"Log file: {settings.LOG_FILE_PATH}")
        logger.info(
            f"Log rotation: {settings.LOG_MAX_SIZE}MB, {settings.LOG_BACKUP_COUNT} backups"
        )

    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("Logging configuration applied successfully")


def log_request_info(
    method: str,
    url: str,
    status_code: int,
    process_time: float,
    user_id: str = None,
) -> None:
    """
    Логирует информацию о HTTP запросе.

    Args:
        method: HTTP метод
        url: URL запроса
        status_code: Код ответа
        process_time: Время обработки в секундах
        user_id: ID пользователя (опционально)
    """
    logger = get_logger("app.api.requests")

    user_info = f" user_id={user_id}" if user_id else ""
    logger.info(
        f"{method} {url} - {status_code} - {process_time:.3f}s{user_info}"
    )


def log_ai_operation(
    operation: str,
    zodiac_sign: str = None,
    success: bool = True,
    duration: float = None,
    error: str = None,
) -> None:
    """
    Логирует AI операции.

    Args:
        operation: Тип операции (horoscope, compatibility, advice)
        zodiac_sign: Знак зодиака
        success: Успешность операции
        duration: Длительность в секундах
        error: Текст ошибки если есть
    """
    logger = get_logger("app.services.ai")

    status = "SUCCESS" if success else "FAILED"
    sign_info = f" sign={zodiac_sign}" if zodiac_sign else ""
    duration_info = f" duration={duration:.3f}s" if duration else ""
    error_info = f" error={error}" if error else ""

    logger.info(
        f"AI_{operation.upper()}_{status}{sign_info}{duration_info}{error_info}"
    )


def log_dialog_flow(
    user_id: str,
    session_id: str,
    intent: str,
    confidence: float,
    dialog_state: str = None,
    processing_time: float = None,
) -> None:
    """
    Логирует диалоговые потоки.

    Args:
        user_id: ID пользователя
        session_id: ID сессии
        intent: Распознанный интент
        confidence: Уверенность распознавания
        dialog_state: Состояние диалога
        processing_time: Время обработки
    """
    logger = get_logger("app.services.dialog")

    state_info = f" state={dialog_state}" if dialog_state else ""
    time_info = f" time={processing_time:.3f}s" if processing_time else ""

    logger.info(
        f"DIALOG user_id={user_id} session_id={session_id} "
        f"intent={intent} confidence={confidence:.2f}{state_info}{time_info}"
    )
