"""
Тесты для менеджера сессий.
"""

from datetime import datetime, timedelta

from app.models.yandex_models import UserContext, YandexIntent, YandexSession
from app.services.session_manager import SessionManager


class TestSessionManager:
    """Тесты для класса SessionManager."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.session_manager = SessionManager()
        self.test_session = YandexSession(
            message_id=1,
            session_id="test-session-123",
            skill_id="test-skill",
            user_id="test-user-456",
            new=True,
        )

    def test_get_user_context_new_session(self):
        """Тест получения контекста для новой сессии."""
        context = self.session_manager.get_user_context(self.test_session)
        assert isinstance(context, UserContext)
        assert context.intent is None
        assert context.awaiting_data is None
        assert context.conversation_step == 0

    def test_update_and_get_user_context(self):
        """Тест обновления и получения контекста пользователя."""
        # Создаем и обновляем контекст
        context = UserContext(
            intent=YandexIntent.HOROSCOPE,
            awaiting_data="birth_date",
            conversation_step=1,
        )

        self.session_manager.update_user_context(self.test_session, context)

        # Получаем обновленный контекст
        retrieved_context = self.session_manager.get_user_context(self.test_session)
        assert retrieved_context.intent == YandexIntent.HOROSCOPE
        assert retrieved_context.awaiting_data == "birth_date"
        assert retrieved_context.conversation_step == 1

    def test_set_awaiting_data(self):
        """Тест установки ожидания данных."""
        context = UserContext()

        self.session_manager.set_awaiting_data(
            self.test_session, context, "birth_date", YandexIntent.HOROSCOPE
        )

        updated_context = self.session_manager.get_user_context(self.test_session)
        assert updated_context.awaiting_data == "birth_date"
        assert updated_context.intent == YandexIntent.HOROSCOPE
        assert updated_context.conversation_step == 1

    def test_clear_awaiting_data(self):
        """Тест очистки ожидания данных."""
        context = UserContext(
            awaiting_data="birth_date",
            intent=YandexIntent.HOROSCOPE,
            conversation_step=1,
        )

        self.session_manager.update_user_context(self.test_session, context)
        self.session_manager.clear_awaiting_data(self.test_session, context)

        updated_context = self.session_manager.get_user_context(self.test_session)
        assert updated_context.awaiting_data is None
        assert updated_context.conversation_step == 2

    def test_clear_user_context(self):
        """Тест очистки контекста пользователя."""
        # Создаем контекст
        context = UserContext(intent=YandexIntent.HOROSCOPE)
        self.session_manager.update_user_context(self.test_session, context)

        # Очищаем контекст
        self.session_manager.clear_user_context(self.test_session)

        # Проверяем, что контекст очищен
        new_context = self.session_manager.get_user_context(self.test_session)
        assert new_context.intent is None

    def test_is_new_session(self):
        """Тест проверки новой сессии."""
        # Для новой сессии
        assert self.session_manager.is_new_session(self.test_session) is True

        # После создания контекста сессия больше не новая
        context = UserContext()
        self.session_manager.update_user_context(self.test_session, context)

        self.test_session.new = False
        assert self.session_manager.is_new_session(self.test_session) is False

    def test_get_active_sessions_count(self):
        """Тест подсчета активных сессий."""
        initial_count = self.session_manager.get_active_sessions_count()

        # Добавляем сессию
        context = UserContext()
        self.session_manager.update_user_context(self.test_session, context)

        new_count = self.session_manager.get_active_sessions_count()
        assert new_count == initial_count + 1

    def test_cleanup_expired_sessions(self):
        """Тест очистки устаревших сессий."""
        # Создаем сессию
        context = UserContext()
        self.session_manager.update_user_context(self.test_session, context)

        # Имитируем устаревшую сессию, изменив время последней активности
        session_key = f"{self.test_session.user_id}:{self.test_session.session_id}"
        old_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        self.session_manager._sessions[session_key]["last_activity"] = old_time

        # Очищаем устаревшие сессии
        cleaned_count = self.session_manager.cleanup_expired_sessions()
        assert cleaned_count == 1

        # Проверяем, что сессия удалена
        assert self.session_manager.get_active_sessions_count() == 0

    def test_get_session_history(self):
        """Тест получения истории сессии."""
        # Создаем контекст
        context = UserContext(intent=YandexIntent.ADVICE)
        self.session_manager.update_user_context(self.test_session, context)

        # Получаем историю
        history = self.session_manager.get_session_history(self.test_session)
        assert history is not None
        assert "context" in history
        assert "last_activity" in history
        assert "session_id" in history
        assert "user_id" in history
