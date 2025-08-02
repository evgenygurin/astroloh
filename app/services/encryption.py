"""
Encryption and security utilities for protecting sensitive user data.
"""
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


class EncryptionService:
    """
    Сервис шифрования для защиты персональных данных пользователей.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Инициализация сервиса шифрования.

        Args:
            encryption_key: Ключ шифрования. Если не указан, берется из настроек.
        """
        if encryption_key:
            self._key = encryption_key.encode()
        elif settings.ENCRYPTION_KEY:
            self._key = settings.ENCRYPTION_KEY.encode()
        else:
            # Генерируем ключ на основе SECRET_KEY
            self._key = self._derive_key_from_secret(settings.SECRET_KEY)

        # Ensure we have exactly 32 bytes for Fernet
        key_bytes = self._key[:32].ljust(32, b'\0')
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self._fernet = Fernet(fernet_key)

    def _derive_key_from_secret(self, secret: str) -> bytes:
        """
        Генерация ключа шифрования из секретного ключа.

        Args:
            secret: Секретный ключ

        Returns:
            Производный ключ для шифрования
        """
        salt = (
            b"astroloh_salt_2024"  # Фиксированная соль для воспроизводимости
        )
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return kdf.derive(secret.encode())

    def encrypt(self, data: str) -> bytes:
        """
        Шифрование строки.

        Args:
            data: Данные для шифрования

        Returns:
            Зашифрованные данные
        """
        if not data:
            return b""

        try:
            return self._fernet.encrypt(data.encode("utf-8"))
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")

    def decrypt(self, encrypted_data: bytes) -> str:
        """
        Расшифровка данных.

        Args:
            encrypted_data: Зашифрованные данные

        Returns:
            Расшифрованная строка
        """
        if not encrypted_data:
            return ""

        try:
            return self._fernet.decrypt(encrypted_data).decode("utf-8")
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt data: {str(e)}")

    def encrypt_dict(self, data: dict) -> bytes:
        """
        Шифрование словаря (преобразование в JSON и шифрование).

        Args:
            data: Словарь для шифрования

        Returns:
            Зашифрованные данные
        """
        import json

        json_str = json.dumps(data, ensure_ascii=False, default=str)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: bytes) -> dict:
        """
        Расшифровка словаря.

        Args:
            encrypted_data: Зашифрованные данные

        Returns:
            Расшифрованный словарь
        """
        import json

        decrypted_str = self.decrypt(encrypted_data)
        if not decrypted_str:
            return {}
        return json.loads(decrypted_str)


class SecurityUtils:
    """
    Утилиты безопасности для обработки и защиты данных.
    """

    @staticmethod
    def hash_ip(ip_address: str) -> str:
        """
        Хеширование IP адреса для аналитики без хранения реального IP.

        Args:
            ip_address: IP адрес

        Returns:
            Хеш IP адреса
        """
        if not ip_address:
            return ""

        # Добавляем соль для усложнения восстановления
        salt = settings.SECRET_KEY[:16]
        return hashlib.sha256((ip_address + salt).encode()).hexdigest()

    @staticmethod
    def hash_user_agent(user_agent: str) -> str:
        """
        Хеширование User-Agent для аналитики.

        Args:
            user_agent: User-Agent строка

        Returns:
            Хеш User-Agent
        """
        if not user_agent:
            return ""

        salt = (
            settings.SECRET_KEY[16:32]
            if len(settings.SECRET_KEY) > 16
            else settings.SECRET_KEY
        )
        return hashlib.sha256((user_agent + salt).encode()).hexdigest()

    @staticmethod
    def generate_verification_code() -> str:
        """
        Генерация кода верификации для GDPR запросов.

        Returns:
            Код верификации
        """
        return secrets.token_hex(16)

    @staticmethod
    def sanitize_input(data: str, max_length: int = 1000) -> str:
        """
        Очистка пользовательского ввода от потенциально опасных символов.

        Args:
            data: Входные данные
            max_length: Максимальная длина

        Returns:
            Очищенные данные
        """
        if not data:
            return ""

        # Обрезаем до максимальной длины
        data = data[:max_length]

        # Удаляем потенциально опасные символы
        dangerous_chars = [
            "<",
            ">",
            '"',
            "'",
            "&",
            "\x00",
            "\x08",
            "\x0b",
            "\x0c",
            "\x0e",
        ]
        for char in dangerous_chars:
            data = data.replace(char, "")

        return data.strip()

    @staticmethod
    def is_session_expired(expires_at: datetime) -> bool:
        """
        Проверка истечения сессии.

        Args:
            expires_at: Время истечения сессии

        Returns:
            True если сессия истекла
        """
        return datetime.utcnow() > expires_at

    @staticmethod
    def generate_session_expiry(hours: int = 24) -> datetime:
        """
        Генерация времени истечения сессии.

        Args:
            hours: Количество часов до истечения

        Returns:
            Время истечения сессии
        """
        return datetime.utcnow() + timedelta(hours=hours)


class DataProtectionManager:
    """
    Менеджер защиты персональных данных с поддержкой GDPR.
    """

    def __init__(self, encryption_service: EncryptionService):
        self.encryption = encryption_service

    def encrypt_birth_data(
        self,
        birth_date: str,
        birth_time: str = None,
        birth_location: str = None,
    ) -> dict:
        """
        Шифрование данных о рождении.

        Args:
            birth_date: Дата рождения (YYYY-MM-DD)
            birth_time: Время рождения (HH:MM)
            birth_location: Место рождения

        Returns:
            Словарь с зашифрованными данными
        """
        result = {}

        if birth_date:
            result["encrypted_birth_date"] = self.encryption.encrypt(
                SecurityUtils.sanitize_input(birth_date, 50)
            )

        if birth_time:
            result["encrypted_birth_time"] = self.encryption.encrypt(
                SecurityUtils.sanitize_input(birth_time, 20)
            )

        if birth_location:
            result["encrypted_birth_location"] = self.encryption.encrypt(
                SecurityUtils.sanitize_input(birth_location, 200)
            )

        return result

    def decrypt_birth_data(
        self,
        encrypted_birth_date: bytes = None,
        encrypted_birth_time: bytes = None,
        encrypted_birth_location: bytes = None,
    ) -> dict:
        """
        Расшифровка данных о рождении.

        Args:
            encrypted_birth_date: Зашифрованная дата рождения
            encrypted_birth_time: Зашифрованное время рождения
            encrypted_birth_location: Зашифрованное место рождения

        Returns:
            Словарь с расшифрованными данными
        """
        result = {}

        if encrypted_birth_date:
            result["birth_date"] = self.encryption.decrypt(
                encrypted_birth_date
            )

        if encrypted_birth_time:
            result["birth_time"] = self.encryption.decrypt(
                encrypted_birth_time
            )

        if encrypted_birth_location:
            result["birth_location"] = self.encryption.decrypt(
                encrypted_birth_location
            )

        return result

    def encrypt_name(self, name: str) -> bytes:
        """
        Шифрование имени пользователя.

        Args:
            name: Имя пользователя

        Returns:
            Зашифрованное имя
        """
        sanitized_name = SecurityUtils.sanitize_input(name, 100)
        return self.encryption.encrypt(sanitized_name)

    def decrypt_name(self, encrypted_name: bytes) -> str:
        """
        Расшифровка имени пользователя.

        Args:
            encrypted_name: Зашифрованное имя

        Returns:
            Расшифрованное имя
        """
        return self.encryption.decrypt(encrypted_name)

    def should_delete_user_data(
        self, created_at: datetime, data_retention_days: int
    ) -> bool:
        """
        Проверка необходимости удаления данных пользователя согласно политике хранения.

        Args:
            created_at: Дата создания пользователя
            data_retention_days: Количество дней хранения данных

        Returns:
            True если данные должны быть удалены
        """
        expiry_date = created_at + timedelta(days=data_retention_days)
        return datetime.utcnow() > expiry_date


class EncryptionError(Exception):
    """Исключение для ошибок шифрования."""

    pass


# Глобальный экземпляр сервиса шифрования
encryption_service = EncryptionService()
data_protection = DataProtectionManager(encryption_service)
