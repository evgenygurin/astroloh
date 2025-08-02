"""
Сервис управления сессиями пользователей с интеграцией безопасного хранения.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.models.yandex_models import UserContext, YandexIntent, YandexSession
from app.services.user_manager import SessionManager as SecureSessionManager


class SessionManager:
    """
    Менеджер сессий пользователей с поддержкой безопасного хранения.

    Теперь интегрирован с базой данных для постоянного хранения сессий.
    """

    def __init__(self, db_session=None):
        # Для обратной совместимости сохраняем в памяти как fallback
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_timeout = timedelta(hours=1)

        # Новый безопасный менеджер сессий
        self._secure_manager = (
            SecureSessionManager(db_session) if db_session else None
        )

    def get_user_context(self, session: YandexSession) -> UserContext:
        """Получает контекст пользователя из сессии."""
        session_key = self._get_session_key(session)

        if session_key not in self._sessions:
            return UserContext()

        session_data = self._sessions[session_key]

        # Проверяем таймаут сессии
        if self._is_session_expired(session_data):
            del self._sessions[session_key]
            return UserContext()

        context_data = session_data.get("context", {})
        return UserContext(**context_data)

    def update_user_context(
        self, session: YandexSession, context: UserContext
    ) -> None:
        """Обновляет контекст пользователя в сессии."""
        session_key = self._get_session_key(session)

        session_data = {
            "context": context.dict(),
            "last_activity": datetime.utcnow().isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
        }

        self._sessions[session_key] = session_data

    def clear_user_context(self, session: YandexSession) -> None:
        """Очищает контекст пользователя."""
        session_key = self._get_session_key(session)
        if session_key in self._sessions:
            del self._sessions[session_key]

    def set_awaiting_data(
        self,
        session: YandexSession,
        context: UserContext,
        data_type: str,
        intent: Optional[YandexIntent] = None,
    ) -> None:
        """Устанавливает ожидание определенных данных от пользователя."""
        context.awaiting_data = data_type
        if intent:
            context.intent = intent
        context.conversation_step += 1
        self.update_user_context(session, context)

    def clear_awaiting_data(
        self, session: YandexSession, context: UserContext
    ) -> None:
        """Очищает ожидание данных."""
        context.awaiting_data = None
        context.conversation_step += 1
        self.update_user_context(session, context)

    def is_new_session(self, session: YandexSession) -> bool:
        """Проверяет, является ли сессия новой."""
        return (
            session.new or self._get_session_key(session) not in self._sessions
        )

    def get_session_history(
        self, session: YandexSession
    ) -> Optional[Dict[str, Any]]:
        """Получает историю сессии."""
        session_key = self._get_session_key(session)
        return self._sessions.get(session_key)

    def cleanup_expired_sessions(self) -> int:
        """Очищает устаревшие сессии. Возвращает количество удаленных сессий."""
        expired_sessions = []

        for session_key, session_data in self._sessions.items():
            if self._is_session_expired(session_data):
                expired_sessions.append(session_key)

        for session_key in expired_sessions:
            del self._sessions[session_key]

        return len(expired_sessions)

    def get_active_sessions_count(self) -> int:
        """Возвращает количество активных сессий."""
        return len(self._sessions)

    def _get_session_key(self, session: YandexSession) -> str:
        """Генерирует ключ сессии."""
        return f"{session.user_id}:{session.session_id}"

    def _is_session_expired(self, session_data: Dict[str, Any]) -> bool:
        """Проверяет, истекла ли сессия."""
        try:
            last_activity = datetime.fromisoformat(
                session_data["last_activity"]
            )
            return datetime.utcnow() - last_activity > self._session_timeout
        except (KeyError, ValueError):
            return True


# Глобальный экземпляр менеджера сессий
session_manager = SessionManager()
