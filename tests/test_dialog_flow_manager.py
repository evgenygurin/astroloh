"""
Тесты для системы управления диалоговыми потоками Stage 5.
"""
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.yandex_models import (
    ProcessedRequest,
    UserContext,
    YandexIntent,
    YandexZodiacSign,
)
from app.services.conversation_manager import ConversationContext, ConversationManager
from app.services.dialog_flow_manager import DialogFlow, DialogFlowManager, DialogState


class TestDialogFlowManager:
    """Тесты для DialogFlowManager."""

    @pytest.fixture
    def dialog_manager(self):
        return DialogFlowManager()

    @pytest.fixture
    def sample_flow(self):
        return DialogFlow("test_flow", DialogState.INITIAL, {})

    @pytest.fixture
    def processed_request(self):
        return ProcessedRequest(
            intent=YandexIntent.HOROSCOPE,
            entities={"dates": ["15.03.1990"]},
            confidence=0.9,
            raw_text="мой гороскоп",
            user_context=UserContext(user_id="test_user"),
        )

    def test_dialog_flow_creation(self, dialog_manager):
        """Тест создания диалогового потока."""
        flow = dialog_manager.get_or_create_flow("session1", "user1")

        assert flow.flow_id == "user1_session1"
        assert flow.state == DialogState.INITIAL
        assert isinstance(flow.context, dict)
        assert flow.step_count == 0

    def test_dialog_flow_reuse(self, dialog_manager):
        """Тест повторного использования существующего потока."""
        # Создаем поток
        flow1 = dialog_manager.get_or_create_flow("session1", "user1")
        flow1.update_state(DialogState.COLLECTING_BIRTH_DATA)

        # Получаем тот же поток
        flow2 = dialog_manager.get_or_create_flow("session1", "user1")

        assert flow1 is flow2
        assert flow2.state == DialogState.COLLECTING_BIRTH_DATA

    def test_intent_processing_in_flow(
        self, dialog_manager, sample_flow, processed_request
    ):
        """Тест обработки интента в диалоговом потоке."""
        next_state, response_context = dialog_manager.process_intent_in_flow(
            sample_flow, processed_request
        )

        assert next_state == DialogState.COLLECTING_BIRTH_DATA
        assert "flow_context" in response_context
        assert "suggestions" in response_context
        assert "required_data" in response_context

    def test_state_transitions(self, dialog_manager):
        """Тест переходов между состояниями."""
        flow = DialogFlow("test", DialogState.INITIAL, {})

        # Тестируем переход от INITIAL к COLLECTING_BIRTH_DATA
        _ = ProcessedRequest(
            intent=YandexIntent.HOROSCOPE,
            entities={},
            confidence=0.9,
            raw_text="гороскоп",
            user_context=UserContext(),
        )

        next_state = dialog_manager._determine_next_state(
            flow, YandexIntent.HOROSCOPE, {}
        )
        assert next_state == DialogState.COLLECTING_BIRTH_DATA

    def test_context_update(self, dialog_manager, sample_flow):
        """Тест обновления контекста потока."""
        entities = {
            "zodiac_signs": [YandexZodiacSign.LEO],
            "dates": ["15.08.1990"],
            "sentiment": "positive",
        }

        dialog_manager._update_flow_context(sample_flow, entities)

        assert sample_flow.context["user_zodiac"] == YandexZodiacSign.LEO
        assert sample_flow.context["birth_date"] == "15.08.1990"
        assert sample_flow.context["current_sentiment"] == "positive"

    def test_required_data_detection(self, dialog_manager):
        """Тест определения требуемых данных."""
        # Для состояния COLLECTING_BIRTH_DATA без даты рождения
        required = dialog_manager._get_required_data(
            DialogState.COLLECTING_BIRTH_DATA, {}
        )
        assert "birth_date" in required

        # Для состояния с имеющейся датой
        required = dialog_manager._get_required_data(
            DialogState.COLLECTING_BIRTH_DATA, {"birth_date": "15.03.1990"}
        )
        assert "birth_date" not in required

    def test_transition_conditions(self, dialog_manager):
        """Тест условий переходов."""
        flow_with_data = DialogFlow(
            "test",
            DialogState.COLLECTING_BIRTH_DATA,
            {"birth_date": "15.03.1990"},
        )

        flow_without_data = DialogFlow(
            "test", DialogState.COLLECTING_BIRTH_DATA, {}
        )

        # С данными можем перейти к гороскопу
        assert dialog_manager._has_birth_date(flow_with_data, {})

        # Без данных не можем
        assert not dialog_manager._has_birth_date(flow_without_data, {})

    def test_flow_expiration(self, dialog_manager):
        """Тест истечения диалогового потока."""
        flow = dialog_manager.get_or_create_flow("session1", "user1")

        # Поток не должен быть истекшим сразу после создания
        assert not flow.is_expired(timeout_minutes=30)

        # Принудительно устанавливаем старое время
        from datetime import timedelta

        flow.updated_at = datetime.now() - timedelta(hours=2)

        assert flow.is_expired(timeout_minutes=30)

    def test_cleanup_expired_flows(self, dialog_manager):
        """Тест очистки истекших потоков."""
        # Создаем несколько потоков
        flow1 = dialog_manager.get_or_create_flow("session1", "user1")
        _ = dialog_manager.get_or_create_flow("session2", "user2")

        # Помечаем один как истекший
        from datetime import timedelta

        flow1.updated_at = datetime.now() - timedelta(hours=2)

        cleaned_count = dialog_manager.cleanup_expired_flows()

        assert cleaned_count == 1
        assert "user2_session2" in dialog_manager.active_flows
        assert "user1_session1" not in dialog_manager.active_flows


class TestConversationManager:
    """Тесты для ConversationManager."""

    @pytest.fixture
    def conversation_manager(self):
        manager = ConversationManager()
        # Мокаем зависимости
        manager.user_manager = Mock()
        manager.encryption_service = Mock()
        return manager

    @pytest.fixture
    def conversation_context(self):
        return ConversationContext("test_user", "test_session")

    @pytest.fixture
    def processed_request(self):
        return ProcessedRequest(
            intent=YandexIntent.HOROSCOPE,
            entities={"dates": ["15.03.1990"]},
            confidence=0.9,
            raw_text="мой гороскоп",
            user_context=UserContext(user_id="test_user"),
        )

    def test_conversation_context_creation(self, conversation_context):
        """Тест создания контекста разговора."""
        assert conversation_context.user_id == "test_user"
        assert conversation_context.session_id == "test_session"
        assert conversation_context.interaction_count == 0
        assert conversation_context.personalization_level == 0.0

    def test_interaction_tracking(self, conversation_context):
        """Тест отслеживания взаимодействий."""
        conversation_context.add_interaction(
            YandexIntent.HOROSCOPE,
            {"dates": ["15.03.1990"]},
            "horoscope_response",
        )

        assert conversation_context.interaction_count == 1
        assert conversation_context.personalization_level == 0.1
        assert len(conversation_context.conversation_history) == 1

    def test_recent_intents(self, conversation_context):
        """Тест получения недавних интентов."""
        # Добавляем несколько взаимодействий
        intents = [
            YandexIntent.HOROSCOPE,
            YandexIntent.COMPATIBILITY,
            YandexIntent.ADVICE,
        ]

        for intent in intents:
            conversation_context.add_interaction(intent, {}, "response")

        recent = conversation_context.get_recent_intents(hours=24)
        assert len(recent) == 3
        assert recent == intents

    def test_preferred_topics(self, conversation_context):
        """Тест определения предпочитаемых тем."""
        # Добавляем разные интенты с разной частотой
        for _ in range(3):
            conversation_context.add_interaction(
                YandexIntent.HOROSCOPE, {}, "response"
            )

        for _ in range(2):
            conversation_context.add_interaction(
                YandexIntent.COMPATIBILITY, {}, "response"
            )

        conversation_context.add_interaction(
            YandexIntent.ADVICE, {}, "response"
        )

        preferred = conversation_context.get_preferred_topics()
        assert preferred[0] == "horoscope"  # Самый частый
        assert preferred[1] == "compatibility"  # Второй по частоте
        assert preferred[2] == "advice"  # Третий

    @pytest.mark.asyncio
    async def test_conversation_processing(
        self, conversation_manager, processed_request
    ):
        """Тест обработки разговора."""
        # Мокаем async методы
        conversation_manager._load_conversation_history = AsyncMock()
        conversation_manager._load_user_preferences = AsyncMock()
        conversation_manager._update_user_preferences = AsyncMock()

        (
            dialog_state,
            response_context,
        ) = await conversation_manager.process_conversation(
            "test_user", "test_session", processed_request
        )

        assert isinstance(dialog_state, DialogState)
        assert isinstance(response_context, dict)
        assert "personalized_greeting" in response_context
        assert "interaction_stats" in response_context

    def test_personalization_levels(self, conversation_manager):
        """Тест уровней персонализации."""
        greetings = conversation_manager.personalized_greetings

        # Проверяем что есть разные уровни приветствий
        assert len(greetings) >= 4
        assert 0 in greetings
        assert 3 in greetings

        # Проверяем что приветствия различаются
        assert greetings[0] != greetings[3]

    def test_contextual_suggestions(self, conversation_manager):
        """Тест контекстных предложений."""
        suggestions = conversation_manager.contextual_suggestions

        # Проверяем что есть предложения для основных интентов
        assert YandexIntent.HOROSCOPE in suggestions
        assert YandexIntent.COMPATIBILITY in suggestions
        assert YandexIntent.NATAL_CHART in suggestions

        # Проверяем что предложения логичны
        horoscope_suggestions = suggestions[YandexIntent.HOROSCOPE]
        assert any("совместимость" in s.lower() for s in horoscope_suggestions)

    def test_adaptive_suggestions_generation(self, conversation_manager):
        """Тест генерации адаптивных предложений."""
        conversation = ConversationContext("user1", "session1")

        # Добавляем историю взаимодействий
        for _ in range(3):
            conversation.add_interaction(
                YandexIntent.HOROSCOPE, {}, "response"
            )

        suggestions = conversation_manager._generate_adaptive_suggestions(
            conversation, DialogState.INITIAL
        )

        # Должны быть предложения, но не гороскоп (так как он уже часто используется)
        assert len(suggestions) <= 3
        for suggestion in suggestions:
            assert "гороскоп" not in suggestion.lower()

    @pytest.mark.asyncio
    async def test_request_enhancement(self, conversation_manager):
        """Тест дополнения запроса контекстом."""
        conversation = ConversationContext("user1", "session1")
        conversation.preferences["birth_date"] = "1990-03-15"

        original_request = ProcessedRequest(
            intent=YandexIntent.HOROSCOPE,
            entities={},
            confidence=0.9,
            raw_text="гороскоп",
            user_context=UserContext(),
        )

        enhanced_request = (
            await conversation_manager._enhance_request_with_context(
                original_request, conversation
            )
        )

        # Проверяем что добавлены сохраненные данные
        assert "dates" in enhanced_request.entities
        assert enhanced_request.entities["dates"][0] == "1990-03-15"
        assert "personalization_level" in enhanced_request.entities

    def test_conversation_analytics(self, conversation_manager):
        """Тест аналитики разговоров."""
        # Создаем несколько разговоров
        conv1 = ConversationContext("user1", "session1")
        conv2 = ConversationContext("user1", "session2")

        for _ in range(5):
            conv1.add_interaction(YandexIntent.HOROSCOPE, {}, "response")

        for _ in range(3):
            conv2.add_interaction(YandexIntent.COMPATIBILITY, {}, "response")

        conversation_manager.active_conversations["user1_session1"] = conv1
        conversation_manager.active_conversations["user1_session2"] = conv2

        analytics = conversation_manager.get_conversation_analytics("user1")

        assert analytics["total_conversations"] == 2
        assert analytics["total_interactions"] == 8
        assert analytics["average_personalization_level"] > 0
        assert "most_active_session" in analytics


class TestIntegration:
    """Интеграционные тесты для Stage 5."""

    @pytest.fixture
    def managers(self):
        dialog_manager = DialogFlowManager()
        conversation_manager = ConversationManager()
        conversation_manager.user_manager = Mock()
        conversation_manager.encryption_service = Mock()
        return dialog_manager, conversation_manager

    @pytest.mark.asyncio
    async def test_full_dialog_scenario(self, managers):
        """Тест полного сценария диалога."""
        dialog_manager, conversation_manager = managers

        # Мокаем async методы
        conversation_manager._load_conversation_history = AsyncMock()
        conversation_manager._load_user_preferences = AsyncMock()
        conversation_manager._update_user_preferences = AsyncMock()

        # Сценарий: пользователь запрашивает гороскоп
        request1 = ProcessedRequest(
            intent=YandexIntent.HOROSCOPE,
            entities={},
            confidence=0.9,
            raw_text="мой гороскоп",
            user_context=UserContext(user_id="test_user"),
        )

        # Первый запрос - должен перейти к сбору данных
        state1, context1 = await conversation_manager.process_conversation(
            "test_user", "test_session", request1
        )

        assert state1 == DialogState.COLLECTING_BIRTH_DATA
        assert "birth_date" in context1.get("required_data", [])

        # Второй запрос - предоставляем дату рождения
        request2 = ProcessedRequest(
            intent=YandexIntent.HOROSCOPE,
            entities={"dates": ["15.03.1990"]},
            confidence=0.9,
            raw_text="15 марта 1990",
            user_context=UserContext(user_id="test_user"),
        )

        state2, context2 = await conversation_manager.process_conversation(
            "test_user", "test_session", request2
        )

        assert state2 == DialogState.PROVIDING_HOROSCOPE
        assert context2.get("can_provide_service", False)

    @pytest.mark.asyncio
    async def test_personalization_progression(self, managers):
        """Тест прогрессии персонализации."""
        dialog_manager, conversation_manager = managers

        # Мокаем async методы
        conversation_manager._load_conversation_history = AsyncMock()
        conversation_manager._load_user_preferences = AsyncMock()
        conversation_manager._update_user_preferences = AsyncMock()

        user_id = "test_user"
        session_id = "test_session"

        # Симулируем несколько взаимодействий
        intents = [
            YandexIntent.HOROSCOPE,
            YandexIntent.COMPATIBILITY,
            YandexIntent.ADVICE,
        ]

        personalization_levels = []

        for i, intent in enumerate(intents):
            request = ProcessedRequest(
                intent=intent,
                entities={},
                confidence=0.9,
                raw_text=f"request {i}",
                user_context=UserContext(user_id=user_id),
            )

            state, context = await conversation_manager.process_conversation(
                user_id, session_id, request
            )

            personalization_level = context.get("interaction_stats", {}).get(
                "personalization_level", 0
            )
            personalization_levels.append(personalization_level)

        # Проверяем что персонализация растет
        assert personalization_levels[1] > personalization_levels[0]
        assert personalization_levels[2] > personalization_levels[1]

    def test_error_recovery_flow(self, managers):
        """Тест потока восстановления после ошибок."""
        dialog_manager, conversation_manager = managers

        # Создаем поток в состоянии ошибки
        flow = dialog_manager.get_or_create_flow("session1", "user1")
        flow.update_state(DialogState.ERROR_RECOVERY)

        # Проверяем что есть предложения для восстановления
        response_context = dialog_manager._build_response_context(
            flow, DialogState.ERROR_RECOVERY, {}
        )

        assert "error_suggestions" in response_context
        assert len(response_context["error_suggestions"]) > 0
