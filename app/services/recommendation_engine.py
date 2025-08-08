"""
Comprehensive recommendation engine for personalized astrological content.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import (
    ABTestGroup,
    Recommendation,
    RecommendationMetrics,
    User,
    UserCluster,
    UserInteraction,
    UserPreference,
)
from app.services.astrology_calculator import AstrologyCalculator
from app.services.user_manager import UserManager


class CollaborativeFiltering:
    """Коллаборативная фильтрация на основе похожих пользователей."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def find_similar_users(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> List[Tuple[uuid.UUID, float]]:
        """
        Находит похожих пользователей на основе астрологических данных и предпочтений.

        Args:
            user_id: ID пользователя
            limit: Максимальное количество похожих пользователей

        Returns:
            Список кортежей (user_id, similarity_score)
        """
        # Получаем данные текущего пользователя
        result = await self.db.execute(
            select(User, UserPreference)
            .outerjoin(UserPreference, UserPreference.user_id == User.id)
            .where(User.id == user_id)
        )
        current_user_data = result.first()

        if not current_user_data:
            return []

        current_user, current_prefs = current_user_data

        # Получаем всех других пользователей с их предпочтениями
        result = await self.db.execute(
            select(User, UserPreference)
            .outerjoin(UserPreference, UserPreference.user_id == User.id)
            .where(User.id != user_id)
        )
        other_users = result.all()

        similarities = []

        for other_user, other_prefs in other_users:
            similarity = self._calculate_user_similarity(
                current_user, current_prefs, other_user, other_prefs
            )
            if similarity > 0.3:  # Минимальный порог схожести
                similarities.append((other_user.id, similarity))

        # Сортируем по убыванию схожести
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def _calculate_user_similarity(
        self,
        user1: User,
        prefs1: Optional[UserPreference],
        user2: User,
        prefs2: Optional[UserPreference],
    ) -> float:
        """Вычисляет схожесть между двумя пользователями."""
        similarity_score = 0.0
        total_weight = 0.0

        # Схожесть по знаку зодиака (вес 0.3)
        if user1.zodiac_sign and user2.zodiac_sign:
            if user1.zodiac_sign == user2.zodiac_sign:
                similarity_score += 0.3
            total_weight += 0.3

        # Схожесть по полу (вес 0.1)
        if user1.gender and user2.gender:
            if user1.gender == user2.gender:
                similarity_score += 0.1
            total_weight += 0.1

        # Схожесть по предпочтениям (общий вес 0.6)
        if prefs1 and prefs2:
            # Стиль общения (вес 0.2)
            if prefs1.communication_style and prefs2.communication_style:
                if prefs1.communication_style == prefs2.communication_style:
                    similarity_score += 0.2
                total_weight += 0.2

            # Уровень сложности (вес 0.2)
            if prefs1.complexity_level and prefs2.complexity_level:
                if prefs1.complexity_level == prefs2.complexity_level:
                    similarity_score += 0.2
                total_weight += 0.2

            # Культурный контекст (вес 0.2)
            if prefs1.cultural_context and prefs2.cultural_context:
                if prefs1.cultural_context == prefs2.cultural_context:
                    similarity_score += 0.2
                total_weight += 0.2

        # Возвращаем нормализованный результат
        return similarity_score / total_weight if total_weight > 0 else 0.0


class ContentBasedFiltering:
    """Контентная фильтрация на основе астрологических характеристик."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.astrology = AstrologyCalculator()

    async def get_content_recommendations(
        self, user_id: uuid.UUID, content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Генерирует рекомендации на основе астрологического профиля пользователя.

        Args:
            user_id: ID пользователя
            content_types: Типы контента для рекомендаций

        Returns:
            Список рекомендаций с их характеристиками
        """
        if content_types is None:
            content_types = ["daily", "weekly", "compatibility", "lunar"]

        # Получаем пользователя и его предпочтения
        result = await self.db.execute(
            select(User, UserPreference)
            .outerjoin(UserPreference)
            .where(User.id == user_id)
        )
        user_data = result.first()

        if not user_data:
            return []

        user, preferences = user_data

        recommendations = []

        for content_type in content_types:
            rec = await self._generate_content_recommendation(
                user, preferences, content_type
            )
            if rec:
                recommendations.append(rec)

        return recommendations

    async def _generate_content_recommendation(
        self,
        user: User,
        preferences: Optional[UserPreference],
        content_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Генерирует рекомендацию для конкретного типа контента."""

        # Анализ текущих астрологических условий
        current_transits = await self._get_current_transits(user)

        recommendation = {
            "content_type": content_type,
            "confidence_score": 0,
            "factors": [],
            "data": {},
        }

        if content_type == "daily":
            recommendation.update(
                await self._recommend_daily_content(
                    user, preferences, current_transits
                )
            )
        elif content_type == "weekly":
            recommendation.update(
                await self._recommend_weekly_content(user, preferences)
            )
        elif content_type == "compatibility":
            recommendation.update(
                await self._recommend_compatibility_content(user, preferences)
            )
        elif content_type == "lunar":
            recommendation.update(
                await self._recommend_lunar_content(user, preferences)
            )

        return (
            recommendation if recommendation["confidence_score"] > 50 else None
        )

    async def _get_current_transits(self, user: User) -> Dict[str, Any]:
        """Получает текущие астрологические транзиты для пользователя."""
        try:
            # Получаем натальную карту пользователя
            user_manager = UserManager(self.db)
            birth_data = await user_manager.get_user_birth_data(user.id)

            if not birth_data or not birth_data.get("birth_date"):
                return {}

            # Вычисляем транзиты
            natal_chart = await self.astrology.calculate_natal_chart(
                birth_data["birth_date"],
                birth_data.get("birth_time", "12:00"),
                birth_data.get("birth_location", "Moscow"),
            )

            current_planets = (
                await self.astrology.get_current_planetary_positions()
            )

            return {
                "natal": natal_chart,
                "current": current_planets,
                "transits": self.astrology.calculate_transits(
                    natal_chart, current_planets
                ),
            }
        except Exception:
            return {}

    async def _recommend_daily_content(
        self,
        user: User,
        preferences: Optional[UserPreference],
        transits: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Рекомендации для ежедневного гороскопа."""

        confidence = 60
        factors = ["zodiac_sign"]

        # Учитываем предпочтения по интересам
        if preferences and preferences.interests:
            interests = preferences.interests
            if isinstance(interests, str):
                interests = json.loads(interests)

            # Приоритизируем контент по интересам
            if interests.get("career", 0) > 0.7:
                factors.append("career_focus")
                confidence += 15
            if interests.get("love", 0) > 0.7:
                factors.append("love_focus")
                confidence += 15
            if interests.get("health", 0) > 0.7:
                factors.append("health_focus")
                confidence += 15

        # Учитываем транзиты
        if transits and transits.get("transits"):
            factors.append("current_transits")
            confidence += 20

        return {
            "confidence_score": min(confidence, 95),
            "factors": factors,
            "data": {
                "focus_areas": self._extract_focus_areas(preferences),
                "timing": "today",
                "transits": transits.get("transits", {}),
            },
        }

    async def _recommend_weekly_content(
        self, user: User, preferences: Optional[UserPreference]
    ) -> Dict[str, Any]:
        """Рекомендации для недельного прогноза."""

        confidence = 70
        factors = ["zodiac_sign", "weekly_trends"]

        return {
            "confidence_score": confidence,
            "factors": factors,
            "data": {"period": "week", "focus": "general_trends"},
        }

    async def _recommend_compatibility_content(
        self, user: User, preferences: Optional[UserPreference]
    ) -> Dict[str, Any]:
        """Рекомендации для совместимости."""

        confidence = 50
        factors = ["zodiac_sign"]

        # Повышаем рейтинг если пользователь интересуется любовными отношениями
        if preferences and preferences.interests:
            interests = preferences.interests
            if isinstance(interests, str):
                interests = json.loads(interests)

            if interests.get("love", 0) > 0.5:
                confidence += 25
                factors.append("love_interest")

        return {
            "confidence_score": confidence,
            "factors": factors,
            "data": {
                "type": "romantic_compatibility",
                "suggestions": ["leo", "sagittarius", "gemini"],  # Пример
            },
        }

    async def _recommend_lunar_content(
        self, user: User, preferences: Optional[UserPreference]
    ) -> Dict[str, Any]:
        """Рекомендации для лунного календаря."""

        confidence = 65
        factors = ["lunar_phase", "zodiac_sign"]

        return {
            "confidence_score": confidence,
            "factors": factors,
            "data": {
                "type": "lunar_calendar",
                "current_phase": "waxing_moon",  # Получается из астрологических расчетов
            },
        }

    def _extract_focus_areas(
        self, preferences: Optional[UserPreference]
    ) -> List[str]:
        """Извлекает области фокуса из предпочтений пользователя."""
        if not preferences or not preferences.interests:
            return ["general"]

        interests = preferences.interests
        if isinstance(interests, str):
            interests = json.loads(interests)

        focus_areas = []
        for area, score in interests.items():
            if score > 0.6:
                focus_areas.append(area)

        return focus_areas or ["general"]


class HybridRecommendationEngine:
    """Гибридная рекомендательная система, объединяющая разные подходы."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.collaborative = CollaborativeFiltering(db_session)
        self.content_based = ContentBasedFiltering(db_session)

    async def generate_recommendations(
        self, user_id: uuid.UUID, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Генерирует персонализированные рекомендации для пользователя.

        Args:
            user_id: ID пользователя
            limit: Максимальное количество рекомендаций

        Returns:
            Список рекомендаций с их характеристиками
        """
        # Получаем рекомендации от обеих систем
        collaborative_recs = await self._get_collaborative_recommendations(
            user_id
        )
        content_recs = await self.content_based.get_content_recommendations(
            user_id
        )

        # Объединяем и ранжируем рекомендации
        hybrid_recs = await self._merge_recommendations(
            collaborative_recs, content_recs, user_id
        )

        # Применяем персонализацию
        personalized_recs = await self._personalize_recommendations(
            hybrid_recs, user_id
        )

        return personalized_recs[:limit]

    async def _get_collaborative_recommendations(
        self, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Получает рекомендации от коллаборативной фильтрации."""

        similar_users = await self.collaborative.find_similar_users(user_id)

        if not similar_users:
            return []

        recommendations = []

        # Анализируем предпочтения похожих пользователей
        for similar_user_id, similarity_score in similar_users:
            # Получаем популярные взаимодействия похожего пользователя
            result = await self.db.execute(
                select(UserInteraction)
                .where(UserInteraction.user_id == similar_user_id)
                .where(UserInteraction.rating >= 4)
                .order_by(desc(UserInteraction.timestamp))
                .limit(3)
            )
            interactions = result.scalars().all()

            for interaction in interactions:
                recommendations.append(
                    {
                        "content_type": interaction.content_type,
                        "confidence_score": int(similarity_score * 100),
                        "algorithm": "collaborative",
                        "source_similarity": similarity_score,
                        "data": {
                            "recommended_by": "similar_users",
                            "interaction_type": interaction.interaction_type,
                        },
                    }
                )

        return recommendations

    async def _merge_recommendations(
        self,
        collaborative_recs: List[Dict[str, Any]],
        content_recs: List[Dict[str, Any]],
        user_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Объединяет рекомендации от разных алгоритмов."""

        merged_recs = []

        # Добавляем контентные рекомендации с весом 0.6
        for rec in content_recs:
            rec["final_score"] = rec["confidence_score"] * 0.6
            rec["algorithm"] = "content_based"
            merged_recs.append(rec)

        # Добавляем коллаборативные рекомендации с весом 0.4
        for rec in collaborative_recs:
            rec["final_score"] = rec["confidence_score"] * 0.4
            merged_recs.append(rec)

        # Применяем временные паттерны
        merged_recs = await self._apply_temporal_patterns(merged_recs, user_id)

        # Сортируем по финальному скору
        merged_recs.sort(key=lambda x: x["final_score"], reverse=True)

        return merged_recs

    async def _apply_temporal_patterns(
        self, recommendations: List[Dict[str, Any]], user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Применяет временные паттерны активности пользователя."""

        # Получаем историю активности пользователя
        result = await self.db.execute(
            select(UserInteraction)
            .where(UserInteraction.user_id == user_id)
            .order_by(desc(UserInteraction.timestamp))
            .limit(50)
        )
        interactions = result.scalars().all()

        if not interactions:
            return recommendations

        # Анализируем временные паттерны
        time_preferences = self._analyze_time_patterns(interactions)
        current_hour = datetime.utcnow().hour

        # Корректируем скоры на основе временных предпочтений
        for rec in recommendations:
            time_boost = time_preferences.get(current_hour, 0.5)
            rec["final_score"] *= 1 + time_boost

        return recommendations

    def _analyze_time_patterns(
        self, interactions: List[UserInteraction]
    ) -> Dict[int, float]:
        """Анализирует временные паттерны активности пользователя."""

        hour_counts = {}

        for interaction in interactions:
            hour = interaction.timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        if not hour_counts:
            return {}

        max_count = max(hour_counts.values())

        # Нормализуем в диапазон 0-0.5 для бустинга
        return {
            hour: (count / max_count) * 0.5
            for hour, count in hour_counts.items()
        }

    async def _personalize_recommendations(
        self, recommendations: List[Dict[str, Any]], user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Применяет финальную персонализацию к рекомендациям."""

        # Получаем предпочтения пользователя
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()

        if not preferences:
            return recommendations

        # Применяем персонализацию стиля и сложности
        for rec in recommendations:
            rec["personalization"] = {
                "communication_style": preferences.communication_style,
                "complexity_level": preferences.complexity_level,
                "cultural_context": preferences.cultural_context,
                "content_length": preferences.content_length_preference,
            }

        return recommendations


class TemporalPatternAnalyzer:
    """Анализатор временных паттернов для сезонной адаптации."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_seasonal_recommendations(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Получает рекомендации с учетом сезонных астрологических циклов."""

        current_date = datetime.utcnow()
        season = self._get_current_season(current_date)

        # Получаем астрологические особенности текущего периода
        seasonal_features = await self._get_seasonal_features(current_date)

        return {
            "season": season,
            "features": seasonal_features,
            "recommendations": await self._generate_seasonal_content(
                user_id, season, seasonal_features
            ),
        }

    def _get_current_season(self, date: datetime) -> str:
        """Определяет текущий астрологический сезон."""

        month = date.month
        day = date.day

        # Астрологические сезоны (примерные даты)
        if (
            (month == 3 and day >= 20)
            or month in [4, 5]
            or (month == 6 and day <= 20)
        ):
            return "spring"
        elif (
            (month == 6 and day >= 21)
            or month in [7, 8]
            or (month == 9 and day <= 22)
        ):
            return "summer"
        elif (
            (month == 9 and day >= 23)
            or month in [10, 11]
            or (month == 12 and day <= 20)
        ):
            return "autumn"
        else:
            return "winter"

    async def _get_seasonal_features(self, date: datetime) -> Dict[str, Any]:
        """Получает астрологические особенности текущего сезона."""

        # Получаем позиции планет
        try:
            astrology = AstrologyCalculator()
            planetary_positions = (
                await astrology.get_current_planetary_positions()
            )

            return {
                "dominant_elements": self._get_dominant_elements(
                    planetary_positions
                ),
                "major_aspects": self._get_major_aspects(planetary_positions),
                "retrograde_planets": self._get_retrograde_planets(
                    planetary_positions
                ),
            }
        except Exception:
            return {}

    def _get_dominant_elements(self, planetary_positions: Dict) -> List[str]:
        """Определяет доминирующие элементы в текущий период."""
        # Упрощенная логика - можно расширить
        return ["fire", "earth"]

    def _get_major_aspects(self, planetary_positions: Dict) -> List[str]:
        """Определяет основные аспекты планет."""
        # Упрощенная логика - можно расширить
        return ["conjunction", "trine"]

    def _get_retrograde_planets(self, planetary_positions: Dict) -> List[str]:
        """Определяет ретроградные планеты."""
        # Упрощенная логика - можно расширить
        return []

    async def _generate_seasonal_content(
        self, user_id: uuid.UUID, season: str, features: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Генерирует контент с учетом сезонных особенностей."""

        seasonal_recommendations = []

        if season == "spring":
            seasonal_recommendations.extend(
                [
                    {
                        "type": "growth_focus",
                        "title": "Время новых начинаний",
                        "description": "Весенняя энергия благоприятствует новым проектам",
                    },
                    {
                        "type": "relationship_focus",
                        "title": "Обновление отношений",
                        "description": "Время для укрепления связей с близкими",
                    },
                ]
            )
        elif season == "summer":
            seasonal_recommendations.extend(
                [
                    {
                        "type": "action_focus",
                        "title": "Активные действия",
                        "description": "Летняя энергия поддерживает активность и решительность",
                    }
                ]
            )
        elif season == "autumn":
            seasonal_recommendations.extend(
                [
                    {
                        "type": "reflection_focus",
                        "title": "Время подведения итогов",
                        "description": "Осень - период анализа и планирования",
                    }
                ]
            )
        else:  # winter
            seasonal_recommendations.extend(
                [
                    {
                        "type": "inner_work",
                        "title": "Внутренняя работа",
                        "description": "Зима благоприятствует самопознанию и медитации",
                    }
                ]
            )

        return seasonal_recommendations


class UserClusteringManager:
    """Менеджер кластеризации пользователей для ML-компонентов."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def update_user_clusters(self) -> int:
        """Обновляет кластеры пользователей на основе их характеристик."""

        # Получаем всех активных пользователей
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_interactions))
            .where(User.data_consent)
        )
        users = result.scalars().all()

        if len(users) < 10:  # Минимум для кластеризации
            return 0

        # Извлекаем признаки для каждого пользователя
        user_features = []
        user_ids = []

        for user in users:
            features = await self._extract_user_features(user)
            if features:
                user_features.append(features)
                user_ids.append(user.id)

        if len(user_features) < 5:
            return 0

        # Кластеризация (упрощенная версия)
        clusters = self._perform_clustering(user_features, user_ids)

        # Сохраняем результаты в БД
        updated_count = 0
        for user_id, cluster_info in clusters.items():
            # Удаляем старые кластеры пользователя
            await self.db.execute(
                select(UserCluster).where(UserCluster.user_id == user_id)
            )

            # Создаем новый кластер
            cluster = UserCluster(
                user_id=user_id,
                cluster_id=cluster_info["cluster_id"],
                cluster_name=cluster_info["cluster_name"],
                cluster_features=cluster_info["features"],
                similarity_score=cluster_info["similarity_score"],
                algorithm_version="1.0",
            )

            self.db.add(cluster)
            updated_count += 1

        await self.db.commit()
        return updated_count

    async def _extract_user_features(
        self, user: User
    ) -> Optional[List[float]]:
        """Извлекает признаки пользователя для кластеризации."""

        features = []

        # Астрологические признаки
        zodiac_features = self._encode_zodiac_sign(user.zodiac_sign)
        features.extend(zodiac_features)

        # Демографические признаки
        gender_features = self._encode_gender(user.gender)
        features.extend(gender_features)

        # Поведенческие признаки
        behavioral_features = await self._extract_behavioral_features(user)
        features.extend(behavioral_features)

        return features if len(features) > 0 else None

    def _encode_zodiac_sign(self, zodiac_sign: Optional[str]) -> List[float]:
        """Кодирует знак зодиака в числовые признаки."""

        zodiac_mapping = {
            "aries": [1, 0, 0, 0],
            "taurus": [0, 1, 0, 0],
            "gemini": [0, 0, 1, 0],
            "cancer": [0, 0, 0, 1],
            # ... остальные знаки
        }

        return zodiac_mapping.get(
            zodiac_sign.lower() if zodiac_sign else "", [0, 0, 0, 0]
        )

    def _encode_gender(self, gender: Optional[str]) -> List[float]:
        """Кодирует пол в числовые признаки."""

        if not gender:
            return [0, 0, 1]  # unknown

        gender_mapping = {
            "male": [1, 0, 0],
            "female": [0, 1, 0],
        }

        return gender_mapping.get(gender.lower(), [0, 0, 1])

    async def _extract_behavioral_features(self, user: User) -> List[float]:
        """Извлекает поведенческие признаки пользователя."""

        # Анализируем взаимодействия пользователя
        total_interactions = len(user.user_interactions)
        positive_interactions = sum(
            1
            for interaction in user.user_interactions
            if interaction.rating and interaction.rating >= 4
        )

        avg_session_duration = 0
        if user.user_interactions:
            durations = [
                interaction.session_duration
                for interaction in user.user_interactions
                if interaction.session_duration
            ]
            if durations:
                avg_session_duration = sum(durations) / len(durations)

        return [
            total_interactions / 100.0,  # нормализация
            positive_interactions / max(total_interactions, 1),
            avg_session_duration / 3600.0,  # в часах
        ]

    def _perform_clustering(
        self, features: List[List[float]], user_ids: List[uuid.UUID]
    ) -> Dict[uuid.UUID, Dict[str, Any]]:
        """Выполняет кластеризацию пользователей (упрощенная версия)."""

        # В реальной реализации здесь был бы алгоритм кластеризации (K-means, DBSCAN)
        # Для демонстрации создаем простую группировку

        clusters = {}

        for i, user_id in enumerate(user_ids):
            cluster_id = f"cluster_{i % 3}"  # 3 кластера для примера

            clusters[user_id] = {
                "cluster_id": cluster_id,
                "cluster_name": f"Group {cluster_id}",
                "features": features[i],
                "similarity_score": 85,  # Примерное значение
            }

        return clusters


class ABTestManager:
    """Менеджер A/B тестирования рекомендательной системы."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def assign_user_to_test(
        self, user_id: uuid.UUID, test_name: str
    ) -> str:
        """Назначает пользователя в A/B тест."""

        # Проверяем, не участвует ли уже пользователь в этом тесте
        result = await self.db.execute(
            select(ABTestGroup).where(
                and_(
                    ABTestGroup.user_id == user_id,
                    ABTestGroup.test_name == test_name,
                    ABTestGroup.is_active,
                )
            )
        )
        existing_assignment = result.scalar_one_or_none()

        if existing_assignment:
            return existing_assignment.group_name

        # Определяем группу (простая случайная выборка)
        import random

        groups = ["control", "variant_a", "variant_b"]
        assigned_group = random.choice(groups)

        # Создаем запись в БД
        ab_test = ABTestGroup(
            user_id=user_id,
            test_name=test_name,
            group_name=assigned_group,
            test_parameters=self._get_test_parameters(
                test_name, assigned_group
            ),
            test_start_date=datetime.utcnow(),
            test_end_date=datetime.utcnow() + timedelta(days=30),
        )

        self.db.add(ab_test)
        await self.db.commit()

        return assigned_group

    def _get_test_parameters(
        self, test_name: str, group_name: str
    ) -> Dict[str, Any]:
        """Получает параметры для A/B теста."""

        test_configs = {
            "recommendation_algorithm": {
                "control": {"algorithm": "content_based", "weight": 1.0},
                "variant_a": {"algorithm": "collaborative", "weight": 1.0},
                "variant_b": {"algorithm": "hybrid", "weight": 0.6},
            },
            "ui_layout": {
                "control": {"layout": "standard", "colors": "default"},
                "variant_a": {"layout": "compact", "colors": "dark"},
                "variant_b": {"layout": "expanded", "colors": "light"},
            },
        }

        return test_configs.get(test_name, {}).get(group_name, {})


class MetricsCollector:
    """Сборщик метрик для мониторинга эффективности рекомендаций."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def record_recommendation_view(
        self,
        user_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        session_id: Optional[str] = None,
    ) -> bool:
        """Записывает просмотр рекомендации."""

        metric = RecommendationMetrics(
            user_id=user_id,
            recommendation_id=recommendation_id,
            metric_name="view",
            metric_value=1,
            session_id=session_id,
            context_data={"action": "view"},
        )

        self.db.add(metric)

        # Обновляем статус рекомендации
        await self.db.execute(
            select(Recommendation).where(
                Recommendation.id == recommendation_id
            )
        )

        await self.db.commit()
        return True

    async def record_recommendation_click(
        self,
        user_id: uuid.UUID,
        recommendation_id: uuid.UUID,
        session_id: Optional[str] = None,
    ) -> bool:
        """Записывает клик по рекомендации."""

        metric = RecommendationMetrics(
            user_id=user_id,
            recommendation_id=recommendation_id,
            metric_name="click",
            metric_value=1,
            session_id=session_id,
            context_data={"action": "click"},
        )

        self.db.add(metric)
        await self.db.commit()
        return True

    async def get_recommendation_metrics(
        self, time_period_days: int = 7
    ) -> Dict[str, float]:
        """Получает агрегированные метрики рекомендаций."""

        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)

        # CTR (Click-Through Rate)
        views_result = await self.db.execute(
            select(RecommendationMetrics).where(
                and_(
                    RecommendationMetrics.metric_name == "view",
                    RecommendationMetrics.recorded_at >= cutoff_date,
                )
            )
        )
        total_views = len(views_result.scalars().all())

        clicks_result = await self.db.execute(
            select(RecommendationMetrics).where(
                and_(
                    RecommendationMetrics.metric_name == "click",
                    RecommendationMetrics.recorded_at >= cutoff_date,
                )
            )
        )
        total_clicks = len(clicks_result.scalars().all())

        ctr = (total_clicks / total_views) if total_views > 0 else 0

        return {
            "ctr": ctr,
            "total_views": total_views,
            "total_clicks": total_clicks,
            "period_days": time_period_days,
        }
