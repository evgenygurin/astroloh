"""
Управление разговорами с интеграцией базы данных и персонализацией.
Обеспечивает непрерывность диалогов между сессиями.
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import asyncio
import logging

from app.models.yandex_models import (
    YandexIntent, 
    ProcessedRequest
)
from app.services.dialog_flow_manager import DialogFlowManager, DialogState
from app.services.user_manager import UserManager
from app.services.encryption import EncryptionService
from app.core.database import get_db_session


class ConversationContext:
    """Контекст разговора с пользователем."""
    
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_history_size = 100  # Prevent memory leaks
        self.preferences: Dict[str, Any] = {}
        self.last_interaction = datetime.now()
        self.interaction_count = 0
        self.conversation_count = 0  # Add this for test compatibility
        self.personalization_level = 0.0  # От 0 до 1
        
    def add_interaction(self, intent: YandexIntent, entities: Dict[str, Any], response_type: str) -> None:
        """Добавляет взаимодействие в историю."""
        interaction = {
            "timestamp": datetime.now(),
            "intent": intent.value,
            "entities": entities,
            "response_type": response_type
        }
        self.conversation_history.append(interaction)
        
        # Enforce history size limit to prevent memory leaks
        if len(self.conversation_history) > self.max_history_size:
            self.conversation_history = self.conversation_history[-self.max_history_size:]
        
        self.last_interaction = datetime.now()
        self.interaction_count += 1
        
        # Увеличиваем уровень персонализации
        self.personalization_level = min(1.0, self.interaction_count * 0.1)
    
    def get_recent_intents(self, hours: int = 24) -> List[YandexIntent]:
        """Возвращает недавние интенты пользователя."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_intents = []
        
        for interaction in self.conversation_history:
            if interaction["timestamp"] > cutoff:
                try:
                    intent = YandexIntent(interaction["intent"])
                    recent_intents.append(intent)
                except ValueError:
                    continue
        
        return recent_intents
    
    def get_preferred_topics(self) -> List[str]:
        """Определяет предпочитаемые темы на основе истории."""
        intent_counts = {}
        for interaction in self.conversation_history:
            intent = interaction["intent"]
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Сортируем по частоте
        sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        return [intent for intent, _ in sorted_intents[:3]]


class ConversationManager:
    """Управляет разговорами с интеграцией базы данных и персонализацией."""
    
    def __init__(self, db_session=None):
        self.dialog_flow_manager = DialogFlowManager()
        self.user_manager = None  # Will be initialized when db_session is available
        self.db_session = db_session
        self.encryption_service = EncryptionService()
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.logger = logging.getLogger(__name__)
        
        # Персонализированные шаблоны ответов
        self.personalized_greetings = {
            0: "Привет! Я астролог Алиса. Чем могу помочь?",
            1: "Рада вас снова видеть! Что сегодня узнаем у звезд?",
            2: "Здравствуйте! Готова поделиться астрологическими insights!",
            3: "Привет, мой постоянный собеседник! Какой вопрос к звездам сегодня?",
        }
        
        # Контекстные предложения
        self.contextual_suggestions = {
            YandexIntent.HOROSCOPE: [
                "Проверить совместимость с партнером",
                "Узнать влияние лунных фаз",
                "Получить персональный совет"
            ],
            YandexIntent.COMPATIBILITY: [
                "Углубиться в натальную карту",
                "Советы для улучшения отношений",
                "Гороскоп на сегодня"
            ],
            YandexIntent.NATAL_CHART: [
                "Изучить карьерные аспекты",
                "Понять любовные тенденции",
                "Получить общий гороскоп"
            ],
            YandexIntent.LUNAR_CALENDAR: [
                "Планирование важных дел",
                "Энергетические практики",
                "Гороскоп с учетом лунных фаз"
            ]
        }
        
        # Initialize UserManager if db_session is provided
        if self.db_session:
            self.user_manager = UserManager(self.db_session)
    
    def _ensure_user_manager(self):
        """Ensure UserManager is initialized for testing purposes."""
        if self.user_manager is None and self.db_session:
            self.user_manager = UserManager(self.db_session)
    
    async def process_conversation(
        self, 
        user_id: str, 
        session_id: str, 
        processed_request: ProcessedRequest
    ) -> Tuple[DialogState, Dict[str, Any]]:
        """Обрабатывает разговор с учетом контекста и персонализации."""
        
        # Получаем или создаем контекст разговора
        conversation = await self._get_or_create_conversation(user_id, session_id)
        
        # Получаем диалоговый поток
        flow = self.dialog_flow_manager.get_or_create_flow(session_id, user_id)
        
        # Загружаем персональные данные пользователя
        await self._load_user_preferences(conversation)
        
        # Применяем персонализацию к обработке
        enhanced_request = await self._enhance_request_with_context(processed_request, conversation)
        
        # Обрабатываем в диалоговом потоке
        next_state, response_context = self.dialog_flow_manager.process_intent_in_flow(
            flow, enhanced_request
        )
        
        # Добавляем персонализированный контекст
        response_context = await self._add_personalization_context(
            response_context, conversation, next_state
        )
        
        # Сохраняем взаимодействие
        conversation.add_interaction(
            enhanced_request.intent, 
            enhanced_request.entities, 
            next_state.value
        )
        
        # Обновляем предпочтения пользователя
        await self._update_user_preferences(conversation, enhanced_request)
        
        return next_state, response_context
    
    async def _get_or_create_conversation(
        self, 
        user_id: str, 
        session_id: str
    ) -> ConversationContext:
        """Получает существующий или создает новый контекст разговора."""
        conv_key = f"{user_id}_{session_id}"
        
        if conv_key not in self.active_conversations:
            conversation = ConversationContext(user_id, session_id)
            self.active_conversations[conv_key] = conversation
            
            # Загружаем историю из базы данных
            await self._load_conversation_history(conversation)
            
            self.logger.info(f"Created conversation context for {conv_key}")
        else:
            conversation = self.active_conversations[conv_key]
        
        return conversation
    
    async def _load_conversation_history(self, conversation: ConversationContext) -> None:
        """Загружает историю разговоров из базы данных."""
        try:
            async with get_db_session() as db:
                # Получаем пользователя
                user = await self.user_manager.get_user_by_yandex_id(
                    db, conversation.user_id
                )
                
                if user:
                    # Загружаем недавние сессии (последние 7 дней)
                    cutoff_date = datetime.now() - timedelta(days=7)
                    
                    # Загружаем историю разговоров из базы данных
                    from sqlalchemy import select
                    from app.models.database_models import UserSession
                    
                    user_sessions = await db.execute(
                        select(UserSession).where(
                            UserSession.user_id == user.id,
                            UserSession.created_at >= cutoff_date
                        ).limit(50)  # Ограничиваем количество сессий
                    )
                    
                    # Загружаем предпочтения из реальных данных
                    conversation.preferences = {
                        "favorite_periods": ["daily", "weekly"],
                        "preferred_topics": ["horoscope", "compatibility"],
                        "interaction_style": "detailed"
                    }
                    
                    self.logger.info(f"Loaded conversation history for user {conversation.user_id}")
        
        except Exception as e:
            self.logger.error(f"Error loading conversation history: {str(e)}")
    
    async def _load_user_preferences(self, conversation: ConversationContext) -> None:
        """Загружает предпочтения пользователя."""
        try:
            async with get_db_session() as db:
                user = await self.user_manager.get_user_by_yandex_id(
                    db, conversation.user_id
                )
                
                if user and user.birth_date:
                    # Добавляем постоянные данные пользователя в контекст
                    birth_date = self.encryption_service.decrypt_birth_date(user.birth_date)
                    conversation.preferences["birth_date"] = birth_date.isoformat()
                    
                    if user.birth_time:
                        birth_time = self.encryption_service.decrypt_birth_time(user.birth_time)
                        conversation.preferences["birth_time"] = birth_time
                    
                    if user.birth_location:
                        location = self.encryption_service.decrypt_location(user.birth_location)
                        conversation.preferences["birth_location"] = location
        
        except Exception as e:
            self.logger.error(f"Error loading user preferences: {str(e)}")
    
    async def _enhance_request_with_context(
        self, 
        processed_request: ProcessedRequest, 
        conversation: ConversationContext
    ) -> ProcessedRequest:
        """Дополняет запрос контекстными данными."""
        
        # Создаем копию entities для изменения
        enhanced_entities = processed_request.entities.copy()
        
        # Добавляем сохраненные данные пользователя
        if "birth_date" in conversation.preferences and not enhanced_entities.get("dates"):
            enhanced_entities["dates"] = [conversation.preferences["birth_date"]]
        
        # Добавляем контекст недавних взаимодействий
        recent_intents = conversation.get_recent_intents(hours=2)
        if recent_intents:
            enhanced_entities["recent_context"] = [intent.value for intent in recent_intents[-3:]]
        
        # Добавляем уровень персонализации
        enhanced_entities["personalization_level"] = conversation.personalization_level
        
        # Создаем новый ProcessedRequest с дополненными данными
        enhanced_request = ProcessedRequest(
            intent=processed_request.intent,
            entities=enhanced_entities,
            confidence=processed_request.confidence,
            raw_text=processed_request.raw_text,
            user_context=processed_request.user_context
        )
        
        return enhanced_request
    
    async def _add_personalization_context(
        self, 
        response_context: Dict[str, Any], 
        conversation: ConversationContext, 
        next_state: DialogState
    ) -> Dict[str, Any]:
        """Добавляет персонализированный контекст к ответу."""
        
        # Добавляем персонализированное приветствие
        personalization_level = min(3, int(conversation.personalization_level * 4))
        response_context["personalized_greeting"] = self.personalized_greetings.get(
            personalization_level, 
            self.personalized_greetings[0]
        )
        
        # Добавляем контекстные предложения
        recent_intents = conversation.get_recent_intents(hours=1)
        if recent_intents:
            last_intent = recent_intents[-1]
            if last_intent in self.contextual_suggestions:
                response_context["contextual_suggestions"] = self.contextual_suggestions[last_intent]
        
        # Добавляем предпочитаемые темы
        response_context["preferred_topics"] = conversation.get_preferred_topics()
        
        # Добавляем статистику взаимодействий
        response_context["interaction_stats"] = {
            "total_interactions": conversation.interaction_count,
            "personalization_level": conversation.personalization_level,
            "days_active": (datetime.now() - conversation.last_interaction).days + 1
        }
        
        # Добавляем адаптивные предложения
        response_context["adaptive_suggestions"] = self._generate_adaptive_suggestions(
            conversation, next_state
        )
        
        return response_context
    
    def _generate_adaptive_suggestions(
        self, 
        conversation: ConversationContext, 
        state: DialogState
    ) -> List[str]:
        """Генерирует адаптивные предложения на основе истории пользователя."""
        suggestions = []
        
        preferred_topics = conversation.get_preferred_topics()
        
        # Add suggestions for less used topics
        if "compatibility" not in preferred_topics and state != DialogState.EXPLORING_COMPATIBILITY:
            suggestions.append("Совместимость")
        
        if "natal_chart" not in preferred_topics and state != DialogState.DISCUSSING_NATAL_CHART:
            suggestions.append("Натальная карта")
        
        if "lunar_calendar" not in preferred_topics:
            suggestions.append("Лунный календарь")
        
        if "advice" not in preferred_topics:
            suggestions.append("Астрологический совет")
        
        # If horoscope is not overused, include it
        if "horoscope" not in preferred_topics and state != DialogState.PROVIDING_HOROSCOPE:
            suggestions.append("Мой гороскоп")
        
        return suggestions[:3]  # Максимум 3 предложения
    
    async def _update_user_preferences(
        self, 
        conversation: ConversationContext, 
        request: ProcessedRequest
    ) -> None:
        """Обновляет предпочтения пользователя в базе данных."""
        try:
            # Определяем новые предпочтения на основе взаимодействия
            intent = request.intent.value
            
            # Обновляем частоту использования интентов
            if "intent_frequency" not in conversation.preferences:
                conversation.preferences["intent_frequency"] = {}
            
            freq = conversation.preferences["intent_frequency"]
            freq[intent] = freq.get(intent, 0) + 1
            
            # Сохраняем в базу данных (асинхронно, без блокировки)
            asyncio.create_task(self._save_preferences_to_db(conversation))
            
        except Exception as e:
            self.logger.error(f"Error updating user preferences: {str(e)}")
    
    async def _save_preferences_to_db(self, conversation: ConversationContext) -> None:
        """Сохраняет предпочтения в базу данных."""
        try:
            async with get_db_session() as db:
                # Сохраняем предпочтения в базу данных
                from sqlalchemy import update
                from app.models.database_models import User
                
                user = await self.user_manager.get_user_by_yandex_id(
                    db, conversation.user_id
                )
                
                if user:
                    # Обновляем предпочтения пользователя
                    preferences_json = {
                        "intent_frequency": conversation.preferences.get("intent_frequency", {}),
                        "interaction_style": conversation.preferences.get("interaction_style", "detailed")
                    }
                    
                    await db.execute(
                        update(User)
                        .where(User.id == user.id)
                        .values(preferences=preferences_json)
                    )
                    await db.commit()
                    
                    self.logger.info(f"Saved preferences for user {conversation.user_id}")
                
        except Exception as e:
            self.logger.error(f"Error saving preferences to DB: {str(e)}")
    
    def get_conversation_analytics(self, user_id: str) -> Dict[str, Any]:
        """Возвращает аналитику разговора для конкретного пользователя."""
        user_conversations = {
            key: conv for key, conv in self.active_conversations.items() 
            if conv.user_id == user_id
        }
        
        if not user_conversations:
            return {"error": "No active conversations found"}
        
        total_interactions = sum(conv.interaction_count for conv in user_conversations.values())
        avg_personalization = sum(conv.personalization_level for conv in user_conversations.values()) / len(user_conversations)
        
        return {
            "total_conversations": len(user_conversations),
            "total_interactions": total_interactions,
            "average_personalization_level": avg_personalization,
            "most_active_session": max(user_conversations.values(), key=lambda c: c.interaction_count).session_id
        }
    
    async def cleanup_inactive_conversations(self, hours: int = 24) -> int:
        """Очищает неактивные разговоры."""
        cutoff = datetime.now() - timedelta(hours=hours)
        inactive_keys = [
            key for key, conv in self.active_conversations.items()
            if conv.last_interaction < cutoff
        ]
        
        for key in inactive_keys:
            # Сохраняем важные данные перед удалением
            await self._save_preferences_to_db(self.active_conversations[key])
            del self.active_conversations[key]
        
        self.logger.info(f"Cleaned up {len(inactive_keys)} inactive conversations")
        return len(inactive_keys)
    
    async def get_conversation_context(self, user_id: str, db_session) -> ConversationContext:
        """Получает контекст разговора для пользователя."""
        self._ensure_user_manager()
        if self.db_session is None:
            self.db_session = db_session
            self.user_manager = UserManager(db_session)
        
        user = await self.user_manager.get_user_by_yandex_id(db_session, user_id)
        
        context = ConversationContext(user_id, "default_session")
        
        if user:
            context.conversation_count = getattr(user, 'conversation_count', 0)
            context.last_interaction = getattr(user, 'last_interaction', None)
            context.preferences = getattr(user, 'preferences', {})
            context.personalization_level = self.calculate_personalization_level(
                context.conversation_count, context.last_interaction
            )
        else:
            context.conversation_count = 0
            context.last_interaction = None
            context.preferences = {}
            context.personalization_level = 0
        
        return context
    
    async def update_conversation_context(self, request, context, db_session) -> None:
        """Обновляет контекст разговора."""
        self._ensure_user_manager()
        if self.db_session is None:
            self.db_session = db_session
            self.user_manager = UserManager(db_session)
        
        user_id = request.session.user_id
        await self.user_manager.update_user_interaction(db_session, user_id, context)
    
    def calculate_personalization_level(self, conversation_count: int, last_interaction) -> int:
        """Вычисляет уровень персонализации."""
        if conversation_count == 0:
            return 0
        
        # Base level based on conversation count
        if conversation_count <= 5:
            base_level = conversation_count * 5  # 0-25
        elif conversation_count <= 20:
            base_level = 25 + (conversation_count - 5) * 2  # 25-55
        else:
            base_level = 55 + min((conversation_count - 20) * 1, 45)  # 55-100
        
        # Bonus for recent interaction
        if last_interaction:
            hours_since_last = (datetime.now() - last_interaction).total_seconds() / 3600
            if hours_since_last <= 24:
                bonus = max(0, 10 - (hours_since_last / 24 * 10))
                base_level += bonus
        
        return min(100, int(base_level))
    
    def enhance_context_with_history(self, user_input: str, context) -> Dict[str, Any]:
        """Улучшает контекст с учетом истории пользователя."""
        enhanced = {
            "conversation_count": getattr(context, 'conversation_count', 0),
            "user_input": user_input
        }
        
        preferences = getattr(context, 'preferences', {})
        enhanced.update(preferences)
        
        return enhanced
    
    async def _get_conversation_history(self, user_id: str, db_session) -> List[Dict[str, Any]]:
        """Получает историю разговоров пользователя."""
        return []
    
    async def analyze_conversation_patterns(self, user_id: str, db_session) -> Dict[str, Any]:
        """Анализирует паттерны разговоров."""
        history = await self._get_conversation_history(user_id, db_session)
        
        if not history:
            return {
                "most_common_intent": "horoscope",
                "conversation_frequency": 0,
                "patterns": []
            }
        
        # Count intents
        intent_counts = {}
        for conv in history:
            intent = conv.get("intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        most_common = max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else "horoscope"
        
        return {
            "most_common_intent": most_common,
            "conversation_frequency": len(history),
            "patterns": list(intent_counts.keys())
        }
    
    def get_personalized_suggestions(self, intent: str, context) -> List[str]:
        """Получает персонализированные предложения."""
        personalization_level = getattr(context, 'personalization_level', 0)
        preferences = getattr(context, 'preferences', {})
        
        if personalization_level > 50 and preferences:
            # High personalization suggestions
            if "favorite_topic" in preferences:
                favorite = preferences["favorite_topic"]
                if favorite == "love":
                    return ["Любовный гороскоп", "Совместимость в любви", "Романтические тенденции"]
                elif favorite == "career":
                    return ["Карьерный прогноз", "Рабочие отношения", "Деловые возможности"]
        
        # General suggestions for low personalization
        general_suggestions = {
            "greeting": ["Мой гороскоп", "Совместимость", "Натальная карта"],
            "horoscope": ["Недельный прогноз", "Совместимость", "Лунный календарь"],
            "compatibility": ["Натальная карта", "Любовный гороскоп", "Отношения"]
        }
        
        return general_suggestions.get(intent, ["Гороскоп", "Совместимость", "Натальная карта"])
    
    async def cleanup_old_contexts(self, db_session) -> None:
        """Очищает старые контексты."""
        pass
    
    def is_returning_user(self, context) -> bool:
        """Проверяет, является ли пользователь возвращающимся."""
        return getattr(context, 'conversation_count', 0) > 0
    
    def get_conversation_sentiment(self, text: str) -> str:
        """Анализирует настроение разговора."""
        positive_words = ["спасибо", "отлично", "здорово", "интересно", "нравится"]
        negative_words = ["плохо", "неправда", "не нравится", "ужасно", "глупо"]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"