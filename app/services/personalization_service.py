"""
Personalization service for dynamic content generation and style adaptation.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User, UserPreference, UserInteraction, Recommendation
from app.services.astrology_calculator import AstrologyCalculator
from app.services.horoscope_generator import HoroscopeGenerator
from app.services.user_manager import UserManager


class DynamicHoroscopeGenerator:
    """Генератор динамических гороскопов, адаптированных под жизненную ситуацию."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.astrology = AstrologyCalculator()
        self.horoscope_generator = HoroscopeGenerator()
        
    async def generate_personalized_horoscope(
        self,
        user_id: uuid.UUID,
        horoscope_type: str = "daily"
    ) -> Dict[str, Any]:
        """
        Генерирует персонализированный гороскоп для пользователя.
        
        Args:
            user_id: ID пользователя
            horoscope_type: Тип гороскопа (daily, weekly, monthly)
            
        Returns:
            Персонализированный гороскоп
        """
        # Получаем пользователя и его предпочтения
        result = await self.db.execute(
            select(User, UserPreference)
            .outerjoin(UserPreference)
            .where(User.id == user_id)
        )
        user_data = result.first()
        
        if not user_data:
            return {}
            
        user, preferences = user_data
        
        # Анализируем жизненную ситуацию пользователя
        life_situation = await self._analyze_life_situation(user_id)
        
        # Получаем базовый гороскоп
        base_horoscope = await self._generate_base_horoscope(
            user, horoscope_type
        )
        
        # Адаптируем под жизненную ситуацию и предпочтения
        personalized_horoscope = await self._adapt_horoscope_to_situation(
            base_horoscope, life_situation, preferences
        )
        
        return personalized_horoscope
    
    async def _analyze_life_situation(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Анализирует текущую жизненную ситуацию пользователя."""
        
        # Анализируем недавние взаимодействия
        result = await self.db.execute(
            select(UserInteraction)
            .where(UserInteraction.user_id == user_id)
            .order_by(UserInteraction.timestamp.desc())
            .limit(20)
        )
        recent_interactions = result.scalars().all()
        
        situation = {
            "focus_areas": {},
            "emotional_state": "neutral",
            "activity_level": "normal",
            "concerns": []
        }
        
        # Анализируем фокус интересов
        content_counts = {}
        total_interactions = len(recent_interactions)
        
        for interaction in recent_interactions:
            content_type = interaction.content_type
            content_counts[content_type] = content_counts.get(content_type, 0) + 1
        
        for content_type, count in content_counts.items():
            situation["focus_areas"][content_type] = count / total_interactions
        
        # Определяем эмоциональное состояние по рейтингам
        ratings = [
            interaction.rating for interaction in recent_interactions
            if interaction.rating is not None
        ]
        
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            if avg_rating >= 4:
                situation["emotional_state"] = "positive"
            elif avg_rating <= 2:
                situation["emotional_state"] = "negative"
        
        # Определяем уровень активности по продолжительности сессий
        durations = [
            interaction.session_duration for interaction in recent_interactions
            if interaction.session_duration is not None
        ]
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            if avg_duration > 300:  # 5 минут
                situation["activity_level"] = "high"
            elif avg_duration < 60:  # 1 минута
                situation["activity_level"] = "low"
        
        return situation
    
    async def _generate_base_horoscope(
        self, 
        user: User, 
        horoscope_type: str
    ) -> Dict[str, Any]:
        """Генерирует базовый гороскоп для пользователя."""
        
        try:
            if horoscope_type == "daily":
                return await self.horoscope_generator.generate_daily_horoscope(
                    user.zodiac_sign or "aries"
                )
            elif horoscope_type == "weekly":
                return await self.horoscope_generator.generate_weekly_horoscope(
                    user.zodiac_sign or "aries"
                )
            elif horoscope_type == "monthly":
                return await self.horoscope_generator.generate_monthly_horoscope(
                    user.zodiac_sign or "aries"
                )
            else:
                return {}
        except Exception:
            # Фоллбэк на простой гороскоп
            return {
                "content": "Сегодня звёзды благоприятствуют новым начинаниям.",
                "areas": ["general"],
                "mood": "positive",
                "advice": "Доверьтесь своей интуиции."
            }
    
    async def _adapt_horoscope_to_situation(
        self,
        base_horoscope: Dict[str, Any],
        life_situation: Dict[str, Any],
        preferences: Optional[UserPreference]
    ) -> Dict[str, Any]:
        """Адаптирует гороскоп под жизненную ситуацию пользователя."""
        
        adapted_horoscope = base_horoscope.copy()
        
        # Адаптируем фокус под интересы пользователя
        focus_areas = life_situation.get("focus_areas", {})
        
        if focus_areas.get("compatibility", 0) > 0.3:
            adapted_horoscope = self._add_relationship_focus(adapted_horoscope)
        
        if focus_areas.get("horoscope", 0) > 0.5:
            adapted_horoscope = self._add_career_focus(adapted_horoscope)
        
        # Адаптируем тон под эмоциональное состояние
        emotional_state = life_situation.get("emotional_state", "neutral")
        adapted_horoscope = self._adapt_emotional_tone(
            adapted_horoscope, emotional_state
        )
        
        # Применяем предпочтения пользователя
        if preferences:
            adapted_horoscope = self._apply_user_preferences(
                adapted_horoscope, preferences
            )
        
        return adapted_horoscope
    
    def _add_relationship_focus(self, horoscope: Dict[str, Any]) -> Dict[str, Any]:
        """Добавляет фокус на отношения в гороскоп."""
        
        relationship_advice = [
            "Обратите особое внимание на общение с близкими.",
            "Сегодня благоприятное время для романтических встреч.",
            "Звёзды советуют быть более открытыми в отношениях."
        ]
        
        horoscope["relationship_focus"] = True
        if "advice" in horoscope:
            horoscope["advice"] += f" {relationship_advice[0]}"
        else:
            horoscope["advice"] = relationship_advice[0]
            
        return horoscope
    
    def _add_career_focus(self, horoscope: Dict[str, Any]) -> Dict[str, Any]:
        """Добавляет карьерный фокус в гороскоп."""
        
        career_advice = [
            "Отличное время для карьерных решений.",
            "Сосредоточьтесь на профессиональных целях.",
            "Планеты благоприятствуют деловой активности."
        ]
        
        horoscope["career_focus"] = True
        if "advice" in horoscope:
            horoscope["advice"] += f" {career_advice[0]}"
        else:
            horoscope["advice"] = career_advice[0]
            
        return horoscope
    
    def _adapt_emotional_tone(
        self, 
        horoscope: Dict[str, Any], 
        emotional_state: str
    ) -> Dict[str, Any]:
        """Адаптирует эмоциональный тон гороскопа."""
        
        if emotional_state == "negative":
            # Добавляем поддерживающий тон
            horoscope["tone"] = "supportive"
            if "content" in horoscope:
                horoscope["content"] = "Помните, что трудности временны. " + horoscope["content"]
        elif emotional_state == "positive":
            # Усиливаем позитивный настрой
            horoscope["tone"] = "encouraging"
            if "content" in horoscope:
                horoscope["content"] = "Ваш позитивный настрой привлекает удачу! " + horoscope["content"]
        
        return horoscope
    
    def _apply_user_preferences(
        self, 
        horoscope: Dict[str, Any], 
        preferences: UserPreference
    ) -> Dict[str, Any]:
        """Применяет пользовательские предпочтения к гороскопу."""
        
        # Адаптируем длину контента
        if preferences.content_length_preference == "short":
            horoscope = self._shorten_content(horoscope)
        elif preferences.content_length_preference == "long":
            horoscope = self._extend_content(horoscope)
        
        # Адаптируем уровень детализации
        if preferences.detail_level == "brief":
            horoscope = self._simplify_content(horoscope)
        elif preferences.detail_level == "detailed":
            horoscope = self._add_details(horoscope)
        
        return horoscope
    
    def _shorten_content(self, horoscope: Dict[str, Any]) -> Dict[str, Any]:
        """Сокращает содержание гороскопа."""
        if "content" in horoscope and len(horoscope["content"]) > 100:
            sentences = horoscope["content"].split(". ")
            horoscope["content"] = ". ".join(sentences[:2]) + "."
        return horoscope
    
    def _extend_content(self, horoscope: Dict[str, Any]) -> Dict[str, Any]:
        """Расширяет содержание гороскопа."""
        extensions = [
            "Астрологические влияния сегодня особенно сильны.",
            "Планеты располагают к активным действиям.",
            "Ваша интуиция будет особенно точной."
        ]
        
        if "content" in horoscope:
            horoscope["content"] += f" {extensions[0]}"
            
        return horoscope
    
    def _simplify_content(self, horoscope: Dict[str, Any]) -> Dict[str, Any]:
        """Упрощает содержание для начинающих."""
        horoscope["complexity"] = "beginner"
        return horoscope
    
    def _add_details(self, horoscope: Dict[str, Any]) -> Dict[str, Any]:
        """Добавляет детали для продвинутых пользователей."""
        horoscope["complexity"] = "advanced"
        if "planetary_influences" not in horoscope:
            horoscope["planetary_influences"] = [
                "Влияние Венеры усиливает творческие способности",
                "Марс активизирует энергетические процессы"
            ]
        return horoscope


class InterestProfilingSystem:
    """Система профилирования интересов пользователя."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def update_user_profile(self, user_id: uuid.UUID) -> Dict[str, float]:
        """
        Обновляет профиль интересов пользователя на основе его активности.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Обновленный профиль интересов
        """
        # Получаем историю взаимодействий
        result = await self.db.execute(
            select(UserInteraction)
            .where(UserInteraction.user_id == user_id)
            .order_by(UserInteraction.timestamp.desc())
            .limit(100)
        )
        interactions = result.scalars().all()
        
        if not interactions:
            return {}
        
        # Анализируем интересы
        interests = await self._analyze_interests(interactions)
        
        # Обновляем профиль в БД
        await self._save_interest_profile(user_id, interests)
        
        return interests
    
    async def _analyze_interests(
        self, 
        interactions: List[UserInteraction]
    ) -> Dict[str, float]:
        """Анализирует интересы на основе взаимодействий."""
        
        interest_scores = {
            "career": 0.0,
            "love": 0.0, 
            "health": 0.0,
            "finances": 0.0,
            "spirituality": 0.0,
            "family": 0.0
        }
        
        total_weight = 0
        
        for interaction in interactions:
            # Вес взаимодействия зависит от его типа и времени
            weight = self._calculate_interaction_weight(interaction)
            
            # Определяем область интереса по типу контента
            interest_area = self._map_content_to_interest(
                interaction.content_type, 
                interaction.feedback_text
            )
            
            if interest_area in interest_scores:
                interest_scores[interest_area] += weight
                
            total_weight += weight
        
        # Нормализуем скоры
        if total_weight > 0:
            for area in interest_scores:
                interest_scores[area] = min(interest_scores[area] / total_weight, 1.0)
        
        return interest_scores
    
    def _calculate_interaction_weight(self, interaction: UserInteraction) -> float:
        """Вычисляет вес взаимодействия."""
        
        base_weight = 1.0
        
        # Увеличиваем вес для позитивных взаимодействий
        if interaction.rating and interaction.rating >= 4:
            base_weight *= 1.5
        elif interaction.rating and interaction.rating <= 2:
            base_weight *= 0.5
        
        # Увеличиваем вес для длительных сессий
        if interaction.session_duration and interaction.session_duration > 180:
            base_weight *= 1.3
        
        # Уменьшаем вес для старых взаимодействий
        days_ago = (datetime.utcnow() - interaction.timestamp).days
        if days_ago > 30:
            base_weight *= 0.7
        elif days_ago > 7:
            base_weight *= 0.9
        
        return base_weight
    
    def _map_content_to_interest(
        self, 
        content_type: str, 
        feedback_text: Optional[str]
    ) -> str:
        """Сопоставляет тип контента с областью интереса."""
        
        content_mapping = {
            "compatibility": "love",
            "daily": "general",
            "weekly": "general", 
            "lunar": "spirituality",
            "natal": "spirituality"
        }
        
        base_interest = content_mapping.get(content_type, "general")
        
        # Дополнительный анализ по тексту отзыва
        if feedback_text:
            feedback_lower = feedback_text.lower()
            
            if any(word in feedback_lower for word in ["работа", "карьера", "деньги"]):
                return "career"
            elif any(word in feedback_lower for word in ["любовь", "отношения", "партнер"]):
                return "love"
            elif any(word in feedback_lower for word in ["здоровье", "самочувствие"]):
                return "health"
            elif any(word in feedback_lower for word in ["семья", "дети", "родители"]):
                return "family"
            elif any(word in feedback_lower for word in ["духовность", "медитация", "развитие"]):
                return "spirituality"
        
        return base_interest if base_interest != "general" else "career"  # Дефолт
    
    async def _save_interest_profile(
        self, 
        user_id: uuid.UUID, 
        interests: Dict[str, float]
    ) -> None:
        """Сохраняет профиль интересов в БД."""
        
        # Получаем или создаем запись предпочтений
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if preferences:
            preferences.interests = interests
            preferences.updated_at = datetime.utcnow()
        else:
            preferences = UserPreference(
                user_id=user_id,
                interests=interests
            )
            self.db.add(preferences)
        
        await self.db.commit()


class CommunicationStyleAdapter:
    """Адаптер стиля общения под предпочтения пользователя."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def adapt_content_style(
        self, 
        content: str, 
        user_id: uuid.UUID
    ) -> str:
        """
        Адаптирует контент под стиль общения пользователя.
        
        Args:
            content: Исходный контент
            user_id: ID пользователя
            
        Returns:
            Адаптированный контент
        """
        # Получаем предпочтения пользователя
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            return content
        
        style = preferences.communication_style or "balanced"
        
        return self._apply_communication_style(content, style)
    
    def _apply_communication_style(self, content: str, style: str) -> str:
        """Применяет определенный стиль общения к контенту."""
        
        if style == "formal":
            return self._make_formal(content)
        elif style == "casual":
            return self._make_casual(content)
        elif style == "friendly":
            return self._make_friendly(content)
        elif style == "mystical":
            return self._make_mystical(content)
        else:  # balanced
            return content
    
    def _make_formal(self, content: str) -> str:
        """Делает контент более формальным."""
        
        formal_replacements = {
            "ты": "вы",
            "твой": "ваш",
            "тебе": "вам",
            "тебя": "вас",
            "привет": "добро пожаловать",
            "пока": "до свидания"
        }
        
        adapted_content = content
        for informal, formal in formal_replacements.items():
            adapted_content = adapted_content.replace(informal, formal)
        
        return adapted_content
    
    def _make_casual(self, content: str) -> str:
        """Делает контент более неформальным."""
        
        casual_additions = [
            "Кстати, ",
            "Между прочим, ",
            "А знаешь что? "
        ]
        
        # Добавляем неформальные элементы
        if not any(addition in content for addition in casual_additions):
            return f"{casual_additions[0]}{content.lower()}"
        
        return content
    
    def _make_friendly(self, content: str) -> str:
        """Делает контент более дружелюбным."""
        
        friendly_additions = [
            "😊 ",
            "✨ ",
            "🌟 "
        ]
        
        friendly_phrases = [
            "Дорогой друг, ",
            "Милый, ",
            "Дорогой, "
        ]
        
        # Добавляем дружелюбные элементы
        adapted_content = f"{friendly_phrases[0]}{content}"
        
        return adapted_content
    
    def _make_mystical(self, content: str) -> str:
        """Делает контент более мистическим."""
        
        mystical_prefixes = [
            "Звёзды шепчут: ",
            "Древние мудрецы говорили: ",
            "Космические силы предрекают: ",
            "Планеты открывают тайну: "
        ]
        
        mystical_additions = [
            " Пусть звёздный свет озарит ваш путь.",
            " Да пребудет с вами мудрость веков.",
            " Пусть космическая энергия поддержит вас."
        ]
        
        prefix = mystical_prefixes[0]
        suffix = mystical_additions[0]
        
        return f"{prefix}{content}{suffix}"


class ComplexityLevelAdjuster:
    """Настройщик уровня сложности контента."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def adjust_content_complexity(
        self, 
        content: Dict[str, Any], 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Настраивает сложность контента под уровень пользователя.
        
        Args:
            content: Исходный контент
            user_id: ID пользователя
            
        Returns:
            Контент с настроенной сложностью
        """
        # Получаем предпочтения пользователя
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        complexity_level = "intermediate"
        if preferences and preferences.complexity_level:
            complexity_level = preferences.complexity_level
        
        return self._adjust_for_complexity(content, complexity_level)
    
    def _adjust_for_complexity(
        self, 
        content: Dict[str, Any], 
        level: str
    ) -> Dict[str, Any]:
        """Настраивает контент под уровень сложности."""
        
        adjusted_content = content.copy()
        
        if level == "beginner":
            adjusted_content = self._simplify_for_beginner(adjusted_content)
        elif level == "advanced":
            adjusted_content = self._enhance_for_advanced(adjusted_content)
        # intermediate остается без изменений
        
        return adjusted_content
    
    def _simplify_for_beginner(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Упрощает контент для начинающих."""
        
        # Убираем сложные астрологические термины
        if "content" in content:
            simplified_text = content["content"]
            
            # Заменяем сложные термины простыми
            term_replacements = {
                "транзит": "влияние планет",
                "аспект": "взаимодействие планет", 
                "ретроградный": "обратное движение",
                "конъюнкция": "соединение планет",
                "оппозиция": "противостояние планет"
            }
            
            for complex_term, simple_term in term_replacements.items():
                simplified_text = simplified_text.replace(complex_term, simple_term)
            
            content["content"] = simplified_text
        
        # Добавляем пояснения
        if "explanations" not in content:
            content["explanations"] = {
                "zodiac_sign": "Ваш знак зодиака определяется положением Солнца в день рождения",
                "planets": "Планеты в астрологии символизируют разные аспекты жизни"
            }
        
        return content
    
    def _enhance_for_advanced(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Усиливает контент для продвинутых пользователей."""
        
        # Добавляем астрологические детали
        if "technical_details" not in content:
            content["technical_details"] = {
                "planetary_degrees": "Точные градусы планет для расчетов",
                "aspects": "Детальный анализ аспектов",
                "houses": "Влияние астрологических домов"
            }
        
        # Добавляем исторический контекст
        if "historical_context" not in content:
            content["historical_context"] = [
                "Древние астрологи использовали эти методы",
                "Традиционная интерпретация символов"
            ]
        
        return content


class CulturalSensitivityManager:
    """Менеджер культурной чувствительности и традиций."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def adapt_cultural_context(
        self, 
        content: Dict[str, Any], 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Адаптирует контент под культурный контекст пользователя.
        
        Args:
            content: Исходный контент
            user_id: ID пользователя
            
        Returns:
            Культурно адаптированный контент
        """
        # Получаем культурные предпочтения пользователя
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        cultural_context = "western"
        if preferences and preferences.cultural_context:
            cultural_context = preferences.cultural_context
        
        return self._apply_cultural_adaptation(content, cultural_context)
    
    def _apply_cultural_adaptation(
        self, 
        content: Dict[str, Any], 
        context: str
    ) -> Dict[str, Any]:
        """Применяет культурную адаптацию к контенту."""
        
        adapted_content = content.copy()
        
        if context == "vedic":
            adapted_content = self._adapt_for_vedic(adapted_content)
        elif context == "chinese":
            adapted_content = self._adapt_for_chinese(adapted_content)
        # western остается по умолчанию
        
        return adapted_content
    
    def _adapt_for_vedic(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Адаптирует контент для ведической астрологии."""
        
        # Добавляем ведические концепции
        vedic_additions = {
            "cultural_note": "В ведической традиции особое внимание уделяется лунным циклам",
            "terminology": "vedic",
            "planetary_system": "sidereal"
        }
        
        content.update(vedic_additions)
        
        # Адаптируем названия планет
        if "planets" in content:
            vedic_names = {
                "sun": "Сурья",
                "moon": "Чандра", 
                "mars": "Мангал",
                "mercury": "Буддха",
                "jupiter": "Гуру",
                "venus": "Шукра",
                "saturn": "Шани"
            }
            
            content["vedic_planet_names"] = vedic_names
        
        return content
    
    def _adapt_for_chinese(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Адаптирует контент для китайской астрологии."""
        
        # Добавляем китайские концепции
        chinese_additions = {
            "cultural_note": "Китайская астрология основана на 12-летнем цикле животных",
            "elements": ["металл", "вода", "дерево", "огонь", "земля"],
            "yin_yang": "Важно учитывать баланс Инь и Ян"
        }
        
        content.update(chinese_additions)
        
        return content