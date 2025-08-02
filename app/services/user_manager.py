"""
User management and session security system.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    DataDeletionRequest,
    HoroscopeRequest,
    SecurityLog,
    User,
    UserSession,
)
from app.services.encryption import EncryptionError, SecurityUtils, data_protection


class UserManager:
    """
    Менеджер пользователей для безопасного управления данными.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.data_protection = data_protection

    async def get_or_create_user(
        self, yandex_user_id: str, user_info: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Получение или создание пользователя.

        Args:
            yandex_user_id: ID пользователя в Яндексе
            user_info: Дополнительная информация о пользователе

        Returns:
            Объект пользователя
        """
        # Поиск существующего пользователя
        result = await self.db.execute(
            select(User).where(User.yandex_user_id == yandex_user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Создание нового пользователя
            user = User(
                yandex_user_id=yandex_user_id,
                data_consent=False,
                data_retention_days=365,
            )

            # Если есть информация о пользователе, обрабатываем её
            if user_info:
                self._update_user_info(user, user_info)

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            # Логируем создание пользователя
            await self._log_security_event(
                event_type="user_creation",
                user_id=user.id,
                description=f"New user created with Yandex ID: {yandex_user_id}",
                success=True,
            )
        else:
            # Обновляем время последнего доступа
            user.last_accessed = datetime.utcnow()
            await self.db.commit()

        return user

    async def update_user_birth_data(
        self,
        user_id: uuid.UUID,
        birth_date: str,
        birth_time: Optional[str] = None,
        birth_location: Optional[str] = None,
        zodiac_sign: Optional[str] = None,
    ) -> bool:
        """
        Обновление данных о рождении пользователя.

        Args:
            user_id: ID пользователя
            birth_date: Дата рождения
            birth_time: Время рождения
            birth_location: Место рождения
            zodiac_sign: Знак зодиака

        Returns:
            True если обновление успешно
        """
        try:
            # Шифруем персональные данные
            encrypted_data = self.data_protection.encrypt_birth_data(
                birth_date, birth_time, birth_location
            )

            # Обновляем пользователя
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    encrypted_birth_date=encrypted_data.get("encrypted_birth_date"),
                    encrypted_birth_time=encrypted_data.get("encrypted_birth_time"),
                    encrypted_birth_location=encrypted_data.get(
                        "encrypted_birth_location"
                    ),
                    zodiac_sign=zodiac_sign,
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()

            # Логируем обновление данных
            await self._log_security_event(
                event_type="data_update",
                user_id=user_id,
                description="User birth data updated",
                success=True,
            )

            return True

        except Exception as e:
            await self._log_security_event(
                event_type="data_update",
                user_id=user_id,
                description="Failed to update user birth data",
                success=False,
                error_message=str(e),
            )
            return False

    async def get_user_birth_data(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Получение расшифрованных данных о рождении пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Словарь с данными о рождении или None
        """
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Расшифровываем данные
            birth_data = self.data_protection.decrypt_birth_data(
                user.encrypted_birth_date,
                user.encrypted_birth_time,
                user.encrypted_birth_location,
            )

            # Добавляем незашифрованные данные
            birth_data["zodiac_sign"] = user.zodiac_sign
            birth_data["gender"] = user.gender

            # Логируем доступ к данным
            await self._log_security_event(
                event_type="data_access",
                user_id=user_id,
                description="User birth data accessed",
                success=True,
            )

            return birth_data

        except EncryptionError as e:
            await self._log_security_event(
                event_type="data_access",
                user_id=user_id,
                description="Failed to decrypt user birth data",
                success=False,
                error_message=str(e),
            )
            return None

    async def set_data_consent(
        self, user_id: uuid.UUID, consent: bool, retention_days: int = 365
    ) -> bool:
        """
        Установка согласия на обработку данных.

        Args:
            user_id: ID пользователя
            consent: Согласие на обработку данных
            retention_days: Количество дней хранения данных

        Returns:
            True если обновление успешно
        """
        try:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    data_consent=consent,
                    data_retention_days=retention_days,
                    updated_at=datetime.utcnow(),
                )
            )
            await self.db.commit()

            await self._log_security_event(
                event_type="consent_update",
                user_id=user_id,
                description=f"Data consent set to {consent}, retention: {retention_days} days",
                success=True,
            )

            return True

        except Exception as e:
            await self._log_security_event(
                event_type="consent_update",
                user_id=user_id,
                description="Failed to update data consent",
                success=False,
                error_message=str(e),
            )
            return False

    async def request_data_deletion(
        self, user_id: uuid.UUID, reason: str = None
    ) -> str:
        """
        Создание запроса на удаление данных (GDPR).

        Args:
            user_id: ID пользователя
            reason: Причина удаления

        Returns:
            Код верификации для подтверждения удаления
        """
        verification_code = SecurityUtils.generate_verification_code()

        deletion_request = DataDeletionRequest(
            user_id=user_id,
            request_reason=reason,
            verification_code=verification_code,
            status="pending",
        )

        self.db.add(deletion_request)
        await self.db.commit()

        await self._log_security_event(
            event_type="deletion_request",
            user_id=user_id,
            description="Data deletion requested",
            success=True,
        )

        return verification_code

    async def confirm_data_deletion(
        self, user_id: uuid.UUID, verification_code: str
    ) -> bool:
        """
        Подтверждение удаления данных.

        Args:
            user_id: ID пользователя
            verification_code: Код верификации

        Returns:
            True если удаление подтверждено и выполнено
        """
        try:
            # Найти запрос на удаление
            result = await self.db.execute(
                select(DataDeletionRequest).where(
                    DataDeletionRequest.user_id == user_id,
                    DataDeletionRequest.verification_code == verification_code,
                    DataDeletionRequest.status == "pending",
                )
            )
            deletion_request = result.scalar_one_or_none()

            if not deletion_request:
                return False

            # Обновить статус запроса
            deletion_request.status = "processing"
            deletion_request.verified = True
            deletion_request.processed_at = datetime.utcnow()

            # Удалить все данные пользователя
            await self._delete_user_data(user_id)

            # Обновить статус на завершенный
            deletion_request.status = "completed"
            await self.db.commit()

            await self._log_security_event(
                event_type="data_deletion",
                user_id=user_id,
                description="User data successfully deleted",
                success=True,
            )

            return True

        except Exception as e:
            await self._log_security_event(
                event_type="data_deletion",
                user_id=user_id,
                description="Failed to delete user data",
                success=False,
                error_message=str(e),
            )
            return False

    async def cleanup_expired_data(self) -> int:
        """
        Очистка данных с истекшим сроком хранения.

        Returns:
            Количество удаленных пользователей
        """
        # Найти пользователей с истекшим сроком хранения данных
        cutoff_date = datetime.utcnow() - timedelta(
            days=365
        )  # Максимальный срок хранения

        result = await self.db.execute(
            select(User).where(User.created_at < cutoff_date, User.data_consent)
        )
        expired_users = result.scalars().all()

        deleted_count = 0
        for user in expired_users:
            if self.data_protection.should_delete_user_data(
                user.created_at, user.data_retention_days
            ):
                await self._delete_user_data(user.id)
                deleted_count += 1

        await self.db.commit()

        if deleted_count > 0:
            await self._log_security_event(
                event_type="auto_cleanup",
                description=f"Automatically deleted {deleted_count} expired user records",
                success=True,
            )

        return deleted_count

    async def delete_user_data(self, user: User) -> None:
        """
        Delete user's sensitive data (clear encrypted fields).

        Args:
            user: User object to clear data from
        """
        user.encrypted_birth_date = None
        user.encrypted_birth_time = None
        user.encrypted_birth_location = None
        user.encrypted_name = None
        await self.db.commit()

    async def update_last_accessed(self, user: User) -> None:
        """
        Update user's last accessed timestamp.

        Args:
            user: User object to update
        """
        user.last_accessed = datetime.utcnow()
        await self.db.commit()

    async def get_user_preferences(self, user: User) -> Dict[str, Any]:
        """
        Get user preferences as a dictionary.

        Args:
            user: User object

        Returns:
            Dictionary with user preferences
        """
        return {
            "zodiac_sign": user.zodiac_sign,
            "gender": user.gender,
            "data_consent": user.data_consent,
        }

    async def set_user_consent(self, user: User, consent: bool) -> None:
        """
        Set user data consent.

        Args:
            user: User object
            consent: Consent status
        """
        user.data_consent = consent
        await self.db.commit()

    async def get_users_for_cleanup(self, days_threshold: int = 30) -> List[User]:
        """
        Get users that need data cleanup.

        Args:
            days_threshold: Days since last access threshold

        Returns:
            List of users for cleanup
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        result = await self.db.execute(
            select(User).where(User.last_accessed < cutoff_date)
        )
        return result.scalars().all()

    async def create_user_with_consent(
        self, yandex_user_id: str, consent: bool = True
    ) -> User:
        """
        Create a new user with specified consent.

        Args:
            yandex_user_id: Yandex user ID
            consent: Data consent status

        Returns:
            Created user object
        """
        user = User(
            yandex_user_id=yandex_user_id,
            data_consent=consent,
            data_retention_days=365,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    def _encrypt_data(self, data: str) -> bytes:
        """
        Encrypt data using the encryption service.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        return self.data_protection.encryption.encrypt(data)

    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """
        Decrypt data using the encryption service.

        Args:
            encrypted_data: Data to decrypt

        Returns:
            Decrypted data
        """
        return self.data_protection.encryption.decrypt(encrypted_data)

    async def get_user_statistics(self, user: User) -> Dict[str, Any]:
        """
        Get user statistics.

        Args:
            user: User object

        Returns:
            Dictionary with user statistics
        """
        now = datetime.utcnow()

        # Calculate days since registration
        days_since_registration = (now - user.created_at).days if user.created_at else 0

        # Calculate days since last access
        days_since_last_access = (
            (now - user.last_accessed).days if user.last_accessed else 0
        )

        # Get total sessions count
        result = await self.db.execute(
            select(UserSession).where(UserSession.user_id == user.id)
        )
        total_sessions = len(result.scalars().all())

        return {
            "days_since_registration": days_since_registration,
            "days_since_last_access": days_since_last_access,
            "total_sessions": total_sessions,
        }

    async def is_user_active(self, user: User, days_threshold: int = 30) -> bool:
        """
        Check if user is active based on last access.

        Args:
            user: User object
            days_threshold: Threshold in days for activity

        Returns:
            True if user is active
        """
        if not user.last_accessed:
            return False

        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        return user.last_accessed > cutoff_date

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by Yandex user ID.

        Args:
            user_id: Yandex user ID

        Returns:
            User object or None
        """
        result = await self.db.execute(
            select(User).where(User.yandex_user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_gender(self, user: User, gender: str) -> None:
        """
        Update user gender.

        Args:
            user: User object
            gender: Gender value
        """
        user.gender = gender
        await self.db.commit()

    async def update_user_zodiac_sign(self, user: User, zodiac_sign: Any) -> None:
        """
        Update user zodiac sign.

        Args:
            user: User object
            zodiac_sign: Zodiac sign value
        """
        user.zodiac_sign = str(zodiac_sign) if zodiac_sign else None
        await self.db.commit()

    async def create_user_with_full_data(
        self, yandex_user_id: str, user_data: Dict[str, Any]
    ) -> User:
        """
        Create user with full data set.

        Args:
            yandex_user_id: Yandex user ID
            user_data: User data dictionary

        Returns:
            Created user object
        """
        user = User(
            yandex_user_id=yandex_user_id,
            zodiac_sign=str(user_data.get("zodiac_sign", "")),
            gender=user_data.get("gender"),
            data_consent=user_data.get("consent", False),
            data_retention_days=user_data.get("retention_days", 365),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def bulk_update_last_accessed(self, user_ids: List[str]) -> bool:
        """
        Update last accessed time for multiple users.

        Args:
            user_ids: List of Yandex user IDs

        Returns:
            True if operation was successful
        """
        try:
            await self.db.execute(
                update(User)
                .where(User.yandex_user_id.in_(user_ids))
                .values(last_accessed=datetime.utcnow())
            )
            await self.db.commit()
            return True
        except Exception:
            return False

    async def get_user_by_yandex_id(
        self, db_session: AsyncSession, yandex_user_id: str
    ) -> Optional[User]:
        """
        Get user by Yandex user ID.

        Args:
            db_session: Database session
            yandex_user_id: Yandex user ID

        Returns:
            User object or None
        """
        result = await db_session.execute(
            select(User).where(User.yandex_user_id == yandex_user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_interaction(
        self, db_session: AsyncSession, user_id: str, context: Any
    ) -> None:
        """
        Update user interaction details.

        Args:
            db_session: Database session
            user_id: Yandex user ID
            context: Conversation context
        """
        user = await self.get_user_by_yandex_id(db_session, user_id)
        if user:
            # Update last accessed time
            user.last_accessed = datetime.utcnow()

            # Update conversation count if available
            if hasattr(context, "conversation_count"):
                # Store conversation count in preferences
                if not user.preferences:
                    user.preferences = {}
                user.preferences["conversation_count"] = context.conversation_count

            await db_session.commit()

    def _update_user_info(self, user: User, user_info: Dict[str, Any]):
        """Обновление информации о пользователе."""
        if "name" in user_info and user_info["name"]:
            user.encrypted_name = self.data_protection.encrypt_name(user_info["name"])

        if "gender" in user_info:
            user.gender = SecurityUtils.sanitize_input(user_info["gender"], 10)

    async def _delete_user_data(self, user_id: uuid.UUID):
        """Полное удаление данных пользователя."""
        # Удалить все связанные данные
        await self.db.execute(
            delete(HoroscopeRequest).where(HoroscopeRequest.user_id == user_id)
        )
        await self.db.execute(delete(UserSession).where(UserSession.user_id == user_id))
        await self.db.execute(
            delete(DataDeletionRequest).where(DataDeletionRequest.user_id == user_id)
        )
        await self.db.execute(delete(User).where(User.id == user_id))

    async def _log_security_event(
        self,
        event_type: str,
        description: str,
        success: bool,
        user_id: uuid.UUID = None,
        session_id: str = None,
        error_message: str = None,
    ):
        """Логирование события безопасности."""
        log_entry = SecurityLog(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            description=description,
            success=success,
            error_message=error_message,
            timestamp=datetime.utcnow(),
        )

        self.db.add(log_entry)
        # Не коммитим здесь, чтобы не нарушить транзакции основных операций


class SessionManager:
    """
    Менеджер сессий для безопасного управления состоянием диалога.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_session(
        self, user_id: uuid.UUID, session_id: str, expiry_hours: int = 24
    ) -> UserSession:
        """
        Создание новой сессии пользователя.

        Args:
            user_id: ID пользователя
            session_id: ID сессии от Яндекса
            expiry_hours: Время жизни сессии в часах

        Returns:
            Объект сессии
        """
        # Закрыть существующие активные сессии
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_active)
            .values(is_active=False)
        )

        # Создать новую сессию
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            current_state="initial",
            is_active=True,
            expires_at=SecurityUtils.generate_session_expiry(expiry_hours),
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def get_active_session(self, session_id: str) -> Optional[UserSession]:
        """
        Получение активной сессии.

        Args:
            session_id: ID сессии

        Returns:
            Объект сессии или None
        """
        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.session_id == session_id, UserSession.is_active)
            .options(selectinload(UserSession.user))
        )
        session = result.scalar_one_or_none()

        if session and SecurityUtils.is_session_expired(session.expires_at):
            # Сессия истекла, деактивируем её
            session.is_active = False
            await self.db.commit()
            return None

        return session

    async def update_session_state(
        self, session_id: str, state: str, context_data: Dict[str, Any] = None
    ) -> bool:
        """
        Обновление состояния сессии.

        Args:
            session_id: ID сессии
            state: Новое состояние
            context_data: Контекстные данные

        Returns:
            True если обновление успешно
        """
        try:
            update_values = {
                "current_state": SecurityUtils.sanitize_input(state, 50),
                "last_activity": datetime.utcnow(),
            }

            if context_data:
                update_values["context_data"] = json.dumps(
                    context_data, ensure_ascii=False, default=str
                )

            await self.db.execute(
                update(UserSession)
                .where(UserSession.session_id == session_id, UserSession.is_active)
                .values(**update_values)
            )
            await self.db.commit()
            return True

        except Exception:
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Очистка истекших сессий.

        Returns:
            Количество деактивированных сессий
        """
        result = await self.db.execute(
            update(UserSession)
            .where(
                UserSession.expires_at < datetime.utcnow(),
                UserSession.is_active,
            )
            .values(is_active=False)
        )
        await self.db.commit()

        return result.rowcount if result.rowcount else 0

    async def log_horoscope_request(
        self,
        user_id: uuid.UUID,
        request_type: str,
        target_date: str = None,
        partner_data: Dict = None,
        ip_address: str = None,
    ) -> bool:
        """
        Логирование запроса гороскопа.

        Args:
            user_id: ID пользователя
            request_type: Тип запроса
            target_date: Целевая дата
            partner_data: Данные партнера для совместимости
            ip_address: IP адрес пользователя

        Returns:
            True если логирование успешно
        """
        try:
            request_log = HoroscopeRequest(
                user_id=user_id,
                request_type=SecurityUtils.sanitize_input(request_type, 50),
                ip_hash=SecurityUtils.hash_ip(ip_address) if ip_address else None,
            )

            # Шифруем чувствительные данные
            if target_date:
                request_log.encrypted_target_date = data_protection.encryption.encrypt(
                    target_date
                )

            if partner_data:
                request_log.encrypted_partner_data = (
                    data_protection.encryption.encrypt_dict(partner_data)
                )

            self.db.add(request_log)
            await self.db.commit()
            return True

        except Exception:
            return False
