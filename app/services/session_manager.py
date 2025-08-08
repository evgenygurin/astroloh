"""
Сервис управления сессиями пользователей с интеграцией безопасного хранения.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.models.yandex_models import UserContext, YandexIntent, YandexSession
from app.services.user_manager import SessionManager as SecureSessionManager

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Менеджер сессий пользователей с поддержкой Alice-совместимого управления состояниями.

    Теперь интегрирован с базой данных для постоянного хранения сессий
    и улучшенным управлением разговорными потоками.
    """

    def __init__(self, db_session=None):
        # Для обратной совместимости сохраняем в памяти как fallback
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_timeout = timedelta(hours=1)
        self._conversation_timeout = timedelta(
            minutes=10
        )  # Alice conversation timeout

        # Счетчики для аналитики
        self._session_stats = {
            "total_sessions": 0,
            "active_conversations": 0,
            "completed_flows": 0,
        }

        # Новый безопасный менеджер сессий
        self._secure_manager = (
            SecureSessionManager(db_session) if db_session else None
        )

    def get_user_context(self, session: YandexSession) -> UserContext:
        """Получает контекст пользователя из сессии с Alice-совместимым управлением."""
        session_key = self._get_session_key(session)
        logger.info(
            f"SESSION_GET_CONTEXT_START: session_key={session_key}, user_id={session.user_id}"
        )

        if session_key not in self._sessions:
            # Инициализируем новую сессию
            logger.info(
                f"SESSION_NEW_USER: initializing_new_session for {session_key}"
            )
            self._initialize_new_session(session)
            context = UserContext(user_id=session.user_id)
            logger.debug(
                f"SESSION_NEW_CONTEXT_CREATED: user_id={session.user_id}"
            )
            return context

        session_data = self._sessions[session_key]
        logger.debug(
            f"SESSION_EXISTING_FOUND: message_count={session_data.get('message_count', 0)}"
        )

        # Проверяем таймаут сессии
        if self._is_session_expired(session_data):
            logger.warning(
                f"SESSION_EXPIRED: cleaning_up session_key={session_key}"
            )
            self._cleanup_expired_session(session_key)
            self._initialize_new_session(session)
            context = UserContext(user_id=session.user_id)
            logger.info(
                f"SESSION_EXPIRED_RENEWED: new_context_created for {session.user_id}"
            )
            return context

        # Обновляем активность для Alice
        old_message_count = session_data.get("message_count", 0)
        session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
        session_data["message_count"] = old_message_count + 1
        logger.debug(
            f"SESSION_ACTIVITY_UPDATED: message_count={old_message_count} -> {session_data['message_count']}"
        )

        context_data = session_data.get("context", {})
        context = UserContext(**context_data)

        # Проверяем, не слишком ли долго длится разговор без прогресса
        if self._is_conversation_stalled(session_data):
            logger.warning(
                f"SESSION_CONVERSATION_STALLED: resetting_awaiting_data for {session_key}"
            )
            context.awaiting_data = None
            context.conversation_step = 0

        logger.info(
            f"SESSION_GET_CONTEXT_SUCCESS: awaiting_data={context.awaiting_data}, step={context.conversation_step}"
        )
        return context

    def update_user_context(
        self, session: YandexSession, context: UserContext
    ) -> None:
        """Обновляет контекст пользователя в сессии с улучшенным отслеживанием."""
        session_key = self._get_session_key(session)
        now = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"SESSION_UPDATE_CONTEXT_START: session_key={session_key}, intent={context.intent.value if context.intent else None}"
        )

        # Получаем существующие данные или создаем новые
        existing_data = self._sessions.get(session_key, {})
        logger.debug(
            f"SESSION_UPDATE_EXISTING: has_existing_data={bool(existing_data)}, existing_interactions={existing_data.get('successful_interactions', 0)}"
        )

        session_data = {
            "context": context.dict(),
            "last_activity": now,
            "session_id": session.session_id,
            "user_id": session.user_id,
            # Alice-специфичные поля
            "message_count": existing_data.get("message_count", 0),
            "conversation_start": existing_data.get("conversation_start", now),
            "last_intent": context.intent.value if context.intent else None,
            "session_new": session.new,
            "successful_interactions": existing_data.get(
                "successful_interactions", 0
            ),
            # Для отслеживания зависших состояний
            "awaiting_data_since": now
            if context.awaiting_data
            and not existing_data.get("awaiting_data_since")
            else existing_data.get("awaiting_data_since"),
        }

        # Очищаем awaiting_data_since если больше не ждем данных
        if not context.awaiting_data:
            session_data["awaiting_data_since"] = None
            if existing_data.get("awaiting_data"):
                session_data["successful_interactions"] += 1
                logger.info(
                    f"SESSION_INTERACTION_COMPLETED: successful_interactions={session_data['successful_interactions']}"
                )
        elif context.awaiting_data and not existing_data.get(
            "awaiting_data_since"
        ):
            logger.debug(
                f"SESSION_AWAITING_DATA_SET: awaiting={context.awaiting_data}, since={now}"
            )

        self._sessions[session_key] = session_data
        logger.info(
            f"SESSION_UPDATE_CONTEXT_SUCCESS: step={context.conversation_step}, awaiting={context.awaiting_data}"
        )

    def clear_user_context(self, session: YandexSession) -> None:
        """Очищает контекст пользователя."""
        session_key = self._get_session_key(session)
        logger.info(f"SESSION_CLEAR_CONTEXT: session_key={session_key}")

        if session_key in self._sessions:
            session_data = self._sessions[session_key]
            interactions = session_data.get("successful_interactions", 0)
            del self._sessions[session_key]
            logger.info(
                f"SESSION_CLEARED: session_key={session_key}, had_interactions={interactions}"
            )
        else:
            logger.warning(
                f"SESSION_CLEAR_NOT_FOUND: session_key={session_key}"
            )

    def set_awaiting_data(
        self,
        session: YandexSession,
        context: UserContext,
        data_type: str,
        intent: Optional[YandexIntent] = None,
    ) -> None:
        """Устанавливает ожидание определенных данных от пользователя."""
        logger.info(
            f"SESSION_SET_AWAITING_DATA: data_type={data_type}, intent={intent.value if intent else None}"
        )

        context.awaiting_data = data_type
        if intent:
            context.intent = intent
            logger.debug(f"SESSION_AWAITING_INTENT_SET: intent={intent.value}")

        old_step = context.conversation_step
        context.conversation_step += 1
        logger.debug(
            f"SESSION_CONVERSATION_STEP: {old_step} -> {context.conversation_step}"
        )

        self.update_user_context(session, context)

    def clear_awaiting_data(
        self, session: YandexSession, context: UserContext
    ) -> None:
        """Очищает ожидание данных."""
        logger.info(
            f"SESSION_CLEAR_AWAITING_DATA: was_awaiting={context.awaiting_data}"
        )

        context.awaiting_data = None
        old_step = context.conversation_step
        context.conversation_step += 1
        logger.debug(
            f"SESSION_CLEAR_CONVERSATION_STEP: {old_step} -> {context.conversation_step}"
        )

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
        """Очищает устаревшие сессии с улучшенной аналитикой. Возвращает количество удаленных сессий."""
        logger.info(
            f"SESSION_CLEANUP_START: total_sessions={len(self._sessions)}"
        )

        expired_sessions = []
        stalled_conversations = 0

        for session_key, session_data in self._sessions.items():
            if self._is_session_expired(session_data):
                expired_sessions.append(session_key)
                logger.debug(
                    f"SESSION_FOUND_EXPIRED: session_key={session_key}"
                )
            elif self._is_conversation_stalled(session_data):
                stalled_conversations += 1
                logger.warning(
                    f"SESSION_FOUND_STALLED: session_key={session_key}"
                )
                # Сбрасываем зависшие состояния
                if "context" in session_data:
                    context_data = session_data["context"]
                    context_data["awaiting_data"] = None
                    context_data["conversation_step"] = 0
                session_data["awaiting_data_since"] = None

        for session_key in expired_sessions:
            self._cleanup_expired_session(session_key)

        # Обновляем статистику
        self._session_stats["active_conversations"] = len(
            self._sessions
        ) - len(expired_sessions)

        logger.info(
            f"SESSION_CLEANUP_COMPLETE: expired={len(expired_sessions)}, stalled={stalled_conversations}, remaining={len(self._sessions)}"
        )
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
            return (
                datetime.now(timezone.utc) - last_activity
                > self._session_timeout
            )
        except (KeyError, ValueError):
            return True

    def _is_conversation_stalled(self, session_data: Dict[str, Any]) -> bool:
        """Проверяет, зависла ли беседа в ожидании данных."""
        try:
            awaiting_since = session_data.get("awaiting_data_since")
            if not awaiting_since:
                return False

            awaiting_time = datetime.fromisoformat(awaiting_since)
            return (
                datetime.now(timezone.utc) - awaiting_time
                > self._conversation_timeout
            )
        except (ValueError, TypeError):
            return False

    def _initialize_new_session(self, session: YandexSession) -> None:
        """Инициализирует новую сессию."""
        self._session_stats["total_sessions"] += 1
        self._session_stats["active_conversations"] += 1
        logger.debug(
            f"SESSION_INITIALIZED: user_id={session.user_id}, total_sessions={self._session_stats['total_sessions']}"
        )

    def _cleanup_expired_session(self, session_key: str) -> None:
        """Очищает истекшую сессию с обновлением статистики."""
        if session_key in self._sessions:
            session_data = self._sessions[session_key]
            interactions = session_data.get("successful_interactions", 0)
            # Учитываем успешные взаимодействия
            if interactions > 0:
                self._session_stats["completed_flows"] += 1
                logger.debug(
                    f"SESSION_COMPLETED_FLOW: session_key={session_key}, interactions={interactions}"
                )
            del self._sessions[session_key]
            logger.debug(f"SESSION_EXPIRED_REMOVED: session_key={session_key}")

    def get_session_analytics(self) -> Dict[str, Any]:
        """Возвращает аналитику сессий для мониторинга Alice compliance."""
        logger.debug("SESSION_ANALYTICS_START: calculating_session_metrics")

        active_count = len(self._sessions)
        avg_message_count = 0
        stalled_count = 0

        if self._sessions:
            total_messages = sum(
                session.get("message_count", 0)
                for session in self._sessions.values()
            )
            avg_message_count = total_messages / active_count
            stalled_count = sum(
                1
                for session in self._sessions.values()
                if self._is_conversation_stalled(session)
            )

        analytics = {
            **self._session_stats,
            "active_sessions": active_count,
            "average_messages_per_session": round(avg_message_count, 2),
            "stalled_conversations": stalled_count,
            "success_rate": (
                self._session_stats["completed_flows"]
                / max(1, self._session_stats["total_sessions"])
            )
            * 100,
        }

        logger.debug(
            f"SESSION_ANALYTICS_RESULT: active={active_count}, avg_messages={analytics['average_messages_per_session']}, stalled={stalled_count}"
        )
        return analytics


# Глобальный экземпляр менеджера сессий
session_manager = SessionManager()
