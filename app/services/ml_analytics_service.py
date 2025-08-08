"""
Machine Learning analytics service for user behavior analysis and predictions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    HoroscopeRequest,
    User,
    UserInteraction,
    UserPreference,
    UserSession,
)


class PreferenceLearningEngine:
    """Движок обучения предпочтений на основе поведения пользователей."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def learn_user_preferences(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Обучается на поведении пользователя и обновляет его предпочтения.

        Args:
            user_id: ID пользователя

        Returns:
            Изученные предпочтения
        """
        # Собираем данные о поведении пользователя
        behavior_data = await self._collect_behavior_data(user_id)

        if not behavior_data:
            return {}

        # Анализируем паттерны
        learned_preferences = await self._analyze_behavior_patterns(
            behavior_data
        )

        # Обновляем предпочтения в БД
        await self._update_learned_preferences(user_id, learned_preferences)

        return learned_preferences

    async def _collect_behavior_data(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Собирает данные о поведении пользователя."""

        # Взаимодействия за последние 3 месяца
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        interactions_result = await self.db.execute(
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= cutoff_date,
                )
            )
            .order_by(desc(UserInteraction.timestamp))
        )
        interactions = interactions_result.scalars().all()

        # Сессии пользователя
        sessions_result = await self.db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.created_at >= cutoff_date,
                )
            )
        )
        sessions = sessions_result.scalars().all()

        # Запросы гороскопов
        requests_result = await self.db.execute(
            select(HoroscopeRequest).where(
                and_(
                    HoroscopeRequest.user_id == user_id,
                    HoroscopeRequest.processed_at >= cutoff_date,
                )
            )
        )
        requests = requests_result.scalars().all()

        return {
            "interactions": interactions,
            "sessions": sessions,
            "horoscope_requests": requests,
            "analysis_period": cutoff_date,
        }

    async def _analyze_behavior_patterns(
        self, behavior_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Анализирует паттерны поведения и выводит предпочтения."""

        interactions = behavior_data["interactions"]
        sessions = behavior_data["sessions"]
        requests = behavior_data["horoscope_requests"]

        preferences = {
            "content_preferences": {},
            "temporal_preferences": {},
            "interaction_patterns": {},
            "engagement_level": "medium",
        }

        # Анализ предпочтений по контенту
        if interactions:
            content_prefs = self._analyze_content_preferences(interactions)
            preferences["content_preferences"] = content_prefs

        # Анализ временных предпочтений
        if sessions:
            temporal_prefs = self._analyze_temporal_preferences(sessions)
            preferences["temporal_preferences"] = temporal_prefs

        # Анализ паттернов взаимодействия
        interaction_patterns = self._analyze_interaction_patterns(
            interactions, sessions, requests
        )
        preferences["interaction_patterns"] = interaction_patterns

        # Определение уровня вовлеченности
        engagement = self._calculate_engagement_level(interactions, sessions)
        preferences["engagement_level"] = engagement

        return preferences

    def _analyze_content_preferences(
        self, interactions: List[UserInteraction]
    ) -> Dict[str, float]:
        """Анализирует предпочтения по типам контента."""

        content_scores = {}
        len(interactions)

        for interaction in interactions:
            content_type = interaction.content_type

            # Базовый скор за взаимодействие
            score = 1.0

            # Увеличиваем за положительную оценку
            if interaction.rating and interaction.rating >= 4:
                score *= 1.5
            elif interaction.rating and interaction.rating <= 2:
                score *= 0.5

            # Увеличиваем за длительное взаимодействие
            if (
                interaction.session_duration
                and interaction.session_duration > 120
            ):
                score *= 1.2

            # Увеличиваем за позитивную обратную связь
            if interaction.interaction_type in ["like", "save", "share"]:
                score *= 1.3

            content_scores[content_type] = (
                content_scores.get(content_type, 0) + score
            )

        # Нормализуем скоры
        if content_scores:
            max_score = max(content_scores.values())
            for content_type in content_scores:
                content_scores[content_type] /= max_score

        return content_scores

    def _analyze_temporal_preferences(
        self, sessions: List[UserSession]
    ) -> Dict[str, Any]:
        """Анализирует временные предпочтения пользователя."""

        hour_counts = {}
        day_counts = {}

        for session in sessions:
            # Анализ по часам
            hour = session.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

            # Анализ по дням недели
            weekday = session.created_at.weekday()
            day_counts[weekday] = day_counts.get(weekday, 0) + 1

        # Находим предпочтительные временные слоты
        preferred_hours = []
        if hour_counts:
            max_hour_count = max(hour_counts.values())
            preferred_hours = [
                hour
                for hour, count in hour_counts.items()
                if count >= max_hour_count * 0.7
            ]

        preferred_days = []
        if day_counts:
            max_day_count = max(day_counts.values())
            preferred_days = [
                day
                for day, count in day_counts.items()
                if count >= max_day_count * 0.7
            ]

        return {
            "preferred_hours": preferred_hours,
            "preferred_weekdays": preferred_days,
            "activity_pattern": self._determine_activity_pattern(hour_counts),
        }

    def _determine_activity_pattern(self, hour_counts: Dict[int, int]) -> str:
        """Определяет паттерн активности (утро, день, вечер, ночь)."""

        if not hour_counts:
            return "unknown"

        period_counts = {
            "morning": sum(hour_counts.get(h, 0) for h in range(6, 12)),
            "afternoon": sum(hour_counts.get(h, 0) for h in range(12, 18)),
            "evening": sum(hour_counts.get(h, 0) for h in range(18, 24)),
            "night": sum(hour_counts.get(h, 0) for h in range(0, 6)),
        }

        return max(period_counts, key=period_counts.get)

    def _analyze_interaction_patterns(
        self,
        interactions: List[UserInteraction],
        sessions: List[UserSession],
        requests: List[HoroscopeRequest],
    ) -> Dict[str, Any]:
        """Анализирует паттерны взаимодействия."""

        patterns = {}

        # Средняя продолжительность сессии
        session_durations = [
            (session.last_activity - session.created_at).total_seconds()
            for session in sessions
            if session.last_activity
        ]

        patterns["avg_session_duration"] = (
            sum(session_durations) / len(session_durations)
            if session_durations
            else 0
        )

        # Частота обращений
        if requests:
            request_dates = [req.processed_at.date() for req in requests]
            unique_dates = len(set(request_dates))
            total_days = (
                datetime.utcnow().date() - min(request_dates)
            ).days + 1
            patterns["usage_frequency"] = unique_dates / total_days
        else:
            patterns["usage_frequency"] = 0

        # Предпочтительные типы взаимодействий
        interaction_types = {}
        for interaction in interactions:
            i_type = interaction.interaction_type
            interaction_types[i_type] = interaction_types.get(i_type, 0) + 1

        patterns["preferred_interaction_types"] = interaction_types

        return patterns

    def _calculate_engagement_level(
        self, interactions: List[UserInteraction], sessions: List[UserSession]
    ) -> str:
        """Вычисляет уровень вовлеченности пользователя."""

        if not interactions and not sessions:
            return "low"

        # Метрики вовлеченности
        total_interactions = len(interactions)
        sum(
            1
            for interaction in interactions
            if interaction.rating and interaction.rating >= 4
        )

        avg_rating = 0
        if interactions:
            ratings = [i.rating for i in interactions if i.rating is not None]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)

        session_count = len(sessions)

        # Вычисляем скор вовлеченности
        engagement_score = 0

        if total_interactions > 20:
            engagement_score += 30
        elif total_interactions > 10:
            engagement_score += 20
        elif total_interactions > 5:
            engagement_score += 10

        if avg_rating >= 4:
            engagement_score += 30
        elif avg_rating >= 3:
            engagement_score += 20
        elif avg_rating >= 2:
            engagement_score += 10

        if session_count > 15:
            engagement_score += 20
        elif session_count > 10:
            engagement_score += 15
        elif session_count > 5:
            engagement_score += 10

        # Определяем уровень
        if engagement_score >= 70:
            return "high"
        elif engagement_score >= 40:
            return "medium"
        else:
            return "low"

    async def _update_learned_preferences(
        self, user_id: uuid.UUID, learned_preferences: Dict[str, Any]
    ) -> None:
        """Обновляет изученные предпочтения в базе данных."""

        # Получаем или создаем запись предпочтений
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()

        if not preferences:
            preferences = UserPreference(user_id=user_id)
            self.db.add(preferences)

        # Обновляем предпочтения (сохраняем как JSON)
        if (
            not hasattr(preferences, "preferences")
            or not preferences.preferences
        ):
            preferences.preferences = {}

        # Объединяем с существующими предпочтениями
        existing_prefs = preferences.preferences or {}
        existing_prefs.update(learned_preferences)
        preferences.preferences = existing_prefs

        preferences.updated_at = datetime.utcnow()

        await self.db.commit()


class ChurnPredictionModel:
    """Модель предсказания оттока пользователей."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def predict_churn_risk(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Предсказывает риск оттока пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Прогноз риска оттока с объяснением
        """
        # Собираем признаки для модели
        features = await self._extract_churn_features(user_id)

        if not features:
            return {"risk_level": "unknown", "probability": 0}

        # Вычисляем риск (упрощенная модель)
        risk_score = self._calculate_churn_score(features)

        # Определяем уровень риска
        risk_level = self._categorize_risk(risk_score)

        # Определяем факторы риска
        risk_factors = self._identify_risk_factors(features)

        return {
            "risk_level": risk_level,
            "probability": risk_score,
            "risk_factors": risk_factors,
            "recommendations": self._get_retention_recommendations(
                risk_factors
            ),
        }

    async def _extract_churn_features(
        self, user_id: uuid.UUID
    ) -> Dict[str, float]:
        """Извлекает признаки для предсказания оттока."""

        # Временные рамки для анализа
        now = datetime.utcnow()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        features = {}

        # Получаем пользователя
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return {}

        # Признак 1: Дни с момента последней активности
        if user.last_accessed:
            days_since_last_access = (now - user.last_accessed).days
            features["days_since_last_access"] = min(
                days_since_last_access / 30.0, 2.0
            )
        else:
            features["days_since_last_access"] = 2.0  # Максимальный риск

        # Признак 2: Активность за последнюю неделю
        week_interactions = await self.db.execute(
            select(func.count(UserInteraction.id)).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= last_week,
                )
            )
        )
        week_count = week_interactions.scalar() or 0
        features["weekly_activity"] = 1.0 - min(week_count / 10.0, 1.0)

        # Признак 3: Тренд активности (сравнение последнего месяца с предыдущим)
        month_interactions = await self.db.execute(
            select(func.count(UserInteraction.id)).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= last_month,
                )
            )
        )
        month_count = month_interactions.scalar() or 0

        prev_month = last_month - timedelta(days=30)
        prev_month_interactions = await self.db.execute(
            select(func.count(UserInteraction.id)).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= prev_month,
                    UserInteraction.timestamp < last_month,
                )
            )
        )
        prev_month_count = (
            prev_month_interactions.scalar() or 1
        )  # Избегаем деления на 0

        activity_trend = month_count / prev_month_count
        features["activity_trend"] = max(1.0 - activity_trend, 0)

        # Признак 4: Средний рейтинг взаимодействий
        ratings_result = await self.db.execute(
            select(func.avg(UserInteraction.rating)).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.rating.isnot(None),
                    UserInteraction.timestamp >= last_month,
                )
            )
        )
        avg_rating = ratings_result.scalar()

        if avg_rating is not None:
            features["satisfaction"] = max(
                (3.0 - avg_rating) / 3.0, 0
            )  # Инвертируем
        else:
            features[
                "satisfaction"
            ] = 0.5  # Нейтральная оценка при отсутствии данных

        # Признак 5: Разнообразие взаимодействий
        interaction_types = await self.db.execute(
            select(
                func.count(func.distinct(UserInteraction.interaction_type))
            ).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= last_month,
                )
            )
        )
        type_count = interaction_types.scalar() or 0
        features["interaction_diversity"] = max(1.0 - (type_count / 5.0), 0)

        return features

    def _calculate_churn_score(self, features: Dict[str, float]) -> float:
        """Вычисляет скор риска оттока."""

        # Веса для разных признаков
        weights = {
            "days_since_last_access": 0.3,
            "weekly_activity": 0.25,
            "activity_trend": 0.2,
            "satisfaction": 0.15,
            "interaction_diversity": 0.1,
        }

        score = 0.0
        total_weight = 0.0

        for feature, value in features.items():
            if feature in weights:
                score += value * weights[feature]
                total_weight += weights[feature]

        return score / total_weight if total_weight > 0 else 0

    def _categorize_risk(self, score: float) -> str:
        """Категоризирует уровень риска."""

        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"

    def _identify_risk_factors(self, features: Dict[str, float]) -> List[str]:
        """Определяет основные факторы риска."""

        risk_factors = []

        if features.get("days_since_last_access", 0) > 0.5:
            risk_factors.append("long_absence")

        if features.get("weekly_activity", 0) > 0.7:
            risk_factors.append("low_recent_activity")

        if features.get("activity_trend", 0) > 0.5:
            risk_factors.append("declining_engagement")

        if features.get("satisfaction", 0) > 0.6:
            risk_factors.append("low_satisfaction")

        if features.get("interaction_diversity", 0) > 0.7:
            risk_factors.append("limited_feature_usage")

        return risk_factors

    def _get_retention_recommendations(
        self, risk_factors: List[str]
    ) -> List[str]:
        """Получает рекомендации по удержанию пользователя."""

        recommendations = []

        if "long_absence" in risk_factors:
            recommendations.append(
                "Отправить персонализированное уведомление с интересным контентом"
            )

        if "low_recent_activity" in risk_factors:
            recommendations.append(
                "Предложить простые и интересные взаимодействия"
            )

        if "declining_engagement" in risk_factors:
            recommendations.append("Провести A/B тест новых форматов контента")

        if "low_satisfaction" in risk_factors:
            recommendations.append(
                "Собрать обратную связь и улучшить качество рекомендаций"
            )

        if "limited_feature_usage" in risk_factors:
            recommendations.append(
                "Познакомить с дополнительными возможностями сервиса"
            )

        if not recommendations:
            recommendations.append(
                "Продолжать мониторинг и поддерживать текущий уровень сервиса"
            )

        return recommendations


class EngagementOptimizer:
    """Оптимизатор вовлеченности пользователей."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def optimize_user_engagement(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Оптимизирует вовлеченность конкретного пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Рекомендации по оптимизации
        """
        # Анализируем текущий уровень вовлеченности
        engagement_analysis = await self._analyze_current_engagement(user_id)

        # Определяем возможности для улучшения
        opportunities = await self._identify_optimization_opportunities(
            user_id, engagement_analysis
        )

        # Генерируем стратегии оптимизации
        strategies = self._generate_optimization_strategies(opportunities)

        return {
            "current_engagement": engagement_analysis,
            "opportunities": opportunities,
            "strategies": strategies,
            "expected_impact": self._estimate_impact(strategies),
        }

    async def _analyze_current_engagement(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Анализирует текущий уровень вовлеченности."""

        # Период анализа - последние 30 дней
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        # Получаем метрики активности
        interactions_result = await self.db.execute(
            select(UserInteraction).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= cutoff_date,
                )
            )
        )
        interactions = interactions_result.scalars().all()

        sessions_result = await self.db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.created_at >= cutoff_date,
                )
            )
        )
        sessions = sessions_result.scalars().all()

        # Вычисляем метрики
        analysis = {
            "total_interactions": len(interactions),
            "unique_sessions": len(sessions),
            "avg_session_duration": self._calculate_avg_session_duration(
                sessions
            ),
            "interaction_frequency": len(interactions) / 30.0,  # в день
            "content_diversity": self._calculate_content_diversity(
                interactions
            ),
            "satisfaction_score": self._calculate_satisfaction(interactions),
            "retention_pattern": self._analyze_retention_pattern(sessions),
        }

        # Определяем общий уровень вовлеченности
        analysis["overall_level"] = self._calculate_overall_engagement(
            analysis
        )

        return analysis

    def _calculate_avg_session_duration(
        self, sessions: List[UserSession]
    ) -> float:
        """Вычисляет среднюю продолжительность сессии в минутах."""

        if not sessions:
            return 0.0

        durations = []
        for session in sessions:
            if session.last_activity and session.created_at:
                duration = (
                    session.last_activity - session.created_at
                ).total_seconds() / 60
                durations.append(duration)

        return sum(durations) / len(durations) if durations else 0.0

    def _calculate_content_diversity(
        self, interactions: List[UserInteraction]
    ) -> float:
        """Вычисляет разнообразие потребляемого контента."""

        if not interactions:
            return 0.0

        content_types = set(
            interaction.content_type for interaction in interactions
        )
        return (
            len(content_types) / 5.0
        )  # Предполагаем максимум 5 типов контента

    def _calculate_satisfaction(
        self, interactions: List[UserInteraction]
    ) -> float:
        """Вычисляет средний уровень удовлетворенности."""

        ratings = [
            interaction.rating
            for interaction in interactions
            if interaction.rating is not None
        ]

        if not ratings:
            return 3.0  # Нейтральная оценка

        return sum(ratings) / len(ratings)

    def _analyze_retention_pattern(self, sessions: List[UserSession]) -> str:
        """Анализирует паттерн возвратов пользователя."""

        if len(sessions) < 3:
            return "new_user"

        # Анализируем промежутки между сессиями
        session_dates = sorted(
            [session.created_at.date() for session in sessions]
        )
        intervals = []

        for i in range(1, len(session_dates)):
            interval = (session_dates[i] - session_dates[i - 1]).days
            intervals.append(interval)

        if not intervals:
            return "single_session"

        avg_interval = sum(intervals) / len(intervals)

        if avg_interval <= 1:
            return "daily"
        elif avg_interval <= 3:
            return "frequent"
        elif avg_interval <= 7:
            return "weekly"
        else:
            return "irregular"

    def _calculate_overall_engagement(self, analysis: Dict[str, Any]) -> str:
        """Вычисляет общий уровень вовлеченности."""

        score = 0

        # Частота взаимодействий
        if analysis["interaction_frequency"] >= 2:
            score += 30
        elif analysis["interaction_frequency"] >= 1:
            score += 20
        elif analysis["interaction_frequency"] >= 0.5:
            score += 10

        # Продолжительность сессий
        if analysis["avg_session_duration"] >= 5:
            score += 25
        elif analysis["avg_session_duration"] >= 3:
            score += 15
        elif analysis["avg_session_duration"] >= 1:
            score += 10

        # Разнообразие контента
        if analysis["content_diversity"] >= 0.6:
            score += 20
        elif analysis["content_diversity"] >= 0.4:
            score += 15
        elif analysis["content_diversity"] >= 0.2:
            score += 10

        # Удовлетворенность
        if analysis["satisfaction_score"] >= 4:
            score += 25
        elif analysis["satisfaction_score"] >= 3:
            score += 15
        elif analysis["satisfaction_score"] >= 2:
            score += 5

        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"

    async def _identify_optimization_opportunities(
        self, user_id: uuid.UUID, engagement_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Определяет возможности для оптимизации вовлеченности."""

        opportunities = []

        # Низкая частота взаимодействий
        if engagement_analysis["interaction_frequency"] < 1:
            opportunities.append(
                {
                    "type": "frequency",
                    "description": "Увеличить частоту взаимодействий",
                    "current_value": engagement_analysis[
                        "interaction_frequency"
                    ],
                    "target_value": 1.5,
                    "priority": "high",
                }
            )

        # Короткие сессии
        if engagement_analysis["avg_session_duration"] < 3:
            opportunities.append(
                {
                    "type": "session_length",
                    "description": "Увеличить продолжительность сессий",
                    "current_value": engagement_analysis[
                        "avg_session_duration"
                    ],
                    "target_value": 5.0,
                    "priority": "medium",
                }
            )

        # Низкое разнообразие контента
        if engagement_analysis["content_diversity"] < 0.4:
            opportunities.append(
                {
                    "type": "content_diversity",
                    "description": "Расширить потребление разных типов контента",
                    "current_value": engagement_analysis["content_diversity"],
                    "target_value": 0.6,
                    "priority": "medium",
                }
            )

        # Низкая удовлетворенность
        if engagement_analysis["satisfaction_score"] < 3.5:
            opportunities.append(
                {
                    "type": "satisfaction",
                    "description": "Повысить качество и релевантность контента",
                    "current_value": engagement_analysis["satisfaction_score"],
                    "target_value": 4.0,
                    "priority": "high",
                }
            )

        # Нерегулярность возвратов
        if engagement_analysis["retention_pattern"] == "irregular":
            opportunities.append(
                {
                    "type": "retention",
                    "description": "Установить регулярный паттерн использования",
                    "current_value": "irregular",
                    "target_value": "weekly",
                    "priority": "high",
                }
            )

        return opportunities

    def _generate_optimization_strategies(
        self, opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Генерирует стратегии оптимизации."""

        strategies = []

        for opportunity in opportunities:
            if opportunity["type"] == "frequency":
                strategies.append(
                    {
                        "name": "Персонализированные уведомления",
                        "description": "Отправка персонализированного контента в оптимальное время",
                        "actions": [
                            "Определить лучшее время для уведомлений",
                            "Создать персонализированный контент",
                            "Настроить автоматические уведомления",
                        ],
                        "expected_improvement": 0.5,
                        "timeframe": "2 недели",
                    }
                )

            elif opportunity["type"] == "session_length":
                strategies.append(
                    {
                        "name": "Интерактивный контент",
                        "description": "Добавление интерактивных элементов для удержания внимания",
                        "actions": [
                            "Создать интерактивные гороскопы",
                            "Добавить викторины и опросы",
                            "Внедрить прогрессивное раскрытие информации",
                        ],
                        "expected_improvement": 2.0,
                        "timeframe": "1 месяц",
                    }
                )

            elif opportunity["type"] == "content_diversity":
                strategies.append(
                    {
                        "name": "Рекомендации новых разделов",
                        "description": "Умные рекомендации неиспользуемых функций",
                        "actions": [
                            "Анализ неиспользуемых функций",
                            "Создание вводных материалов",
                            "Мягкое знакомство с новыми возможностями",
                        ],
                        "expected_improvement": 0.3,
                        "timeframe": "3 недели",
                    }
                )

            elif opportunity["type"] == "satisfaction":
                strategies.append(
                    {
                        "name": "Улучшение качества контента",
                        "description": "Оптимизация алгоритмов и персонализации",
                        "actions": [
                            "A/B тест новых алгоритмов рекомендаций",
                            "Сбор детальной обратной связи",
                            "Настройка персонализации",
                        ],
                        "expected_improvement": 0.7,
                        "timeframe": "6 недель",
                    }
                )

            elif opportunity["type"] == "retention":
                strategies.append(
                    {
                        "name": "Программа лояльности",
                        "description": "Создание регулярных активностей и поощрений",
                        "actions": [
                            "Создать систему достижений",
                            "Настроить регулярные челленджи",
                            "Внедрить программу лояльности",
                        ],
                        "expected_improvement": "weekly",
                        "timeframe": "2 месяца",
                    }
                )

        return strategies

    def _estimate_impact(
        self, strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Оценивает ожидаемое влияние стратегий."""

        if not strategies:
            return {"overall_improvement": 0, "confidence": 0}

        # Простая оценка воздействия
        total_improvement = sum(
            s.get("expected_improvement", 0)
            for s in strategies
            if isinstance(s.get("expected_improvement"), (int, float))
        )

        return {
            "overall_improvement": min(
                total_improvement, 100
            ),  # Максимум 100%
            "confidence": min(len(strategies) * 20, 100),
            "implementation_time": max(
                self._parse_timeframe(s.get("timeframe", "1 week"))
                for s in strategies
            ),
        }

    def _parse_timeframe(self, timeframe: str) -> int:
        """Парсит временные рамки в дни."""

        timeframe_map = {
            "1 week": 7,
            "2 weeks": 14,
            "2 недели": 14,
            "3 weeks": 21,
            "3 недели": 21,
            "1 month": 30,
            "1 месяц": 30,
            "6 weeks": 42,
            "6 недель": 42,
            "2 months": 60,
            "2 месяца": 60,
        }

        return timeframe_map.get(timeframe, 30)


class AnomalyDetectionSystem:
    """Система выявления аномалий в поведении пользователей."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def detect_anomalies(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Выявляет аномалии в поведении пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Список выявленных аномалий
        """
        # Собираем данные о поведении
        behavior_data = (
            await self._collect_behavior_data_for_anomaly_detection(user_id)
        )

        if not behavior_data:
            return {"anomalies": [], "status": "insufficient_data"}

        # Выявляем различные типы аномалий
        anomalies = []

        # Аномалии активности
        activity_anomalies = self._detect_activity_anomalies(behavior_data)
        anomalies.extend(activity_anomalies)

        # Аномалии взаимодействий
        interaction_anomalies = self._detect_interaction_anomalies(
            behavior_data
        )
        anomalies.extend(interaction_anomalies)

        # Аномалии предпочтений
        preference_anomalies = self._detect_preference_anomalies(behavior_data)
        anomalies.extend(preference_anomalies)

        return {
            "anomalies": anomalies,
            "total_count": len(anomalies),
            "status": "analyzed",
            "recommendations": self._generate_anomaly_recommendations(
                anomalies
            ),
        }

    async def _collect_behavior_data_for_anomaly_detection(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Собирает данные для выявления аномалий."""

        # Анализируем последние 60 дней
        cutoff_date = datetime.utcnow() - timedelta(days=60)

        # Получаем взаимодействия по дням
        interactions_result = await self.db.execute(
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= cutoff_date,
                )
            )
            .order_by(UserInteraction.timestamp)
        )
        interactions = interactions_result.scalars().all()

        if not interactions:
            return {}

        # Группируем данные по дням
        daily_data = {}
        for interaction in interactions:
            date_key = interaction.timestamp.date().isoformat()

            if date_key not in daily_data:
                daily_data[date_key] = {
                    "interactions": [],
                    "total_duration": 0,
                    "content_types": set(),
                    "ratings": [],
                }

            daily_data[date_key]["interactions"].append(interaction)
            daily_data[date_key]["content_types"].add(interaction.content_type)

            if interaction.session_duration:
                daily_data[date_key][
                    "total_duration"
                ] += interaction.session_duration

            if interaction.rating:
                daily_data[date_key]["ratings"].append(interaction.rating)

        return {
            "daily_data": daily_data,
            "total_interactions": len(interactions),
            "date_range": (cutoff_date, datetime.utcnow()),
        }

    def _detect_activity_anomalies(
        self, behavior_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Выявляет аномалии в уровне активности."""

        anomalies = []
        daily_data = behavior_data["daily_data"]

        if len(daily_data) < 7:  # Недостаточно данных
            return anomalies

        # Вычисляем статистики активности
        daily_counts = [
            len(day_data["interactions"]) for day_data in daily_data.values()
        ]
        daily_durations = [
            day_data["total_duration"] for day_data in daily_data.values()
        ]

        avg_count = sum(daily_counts) / len(daily_counts)
        avg_duration = sum(daily_durations) / len(daily_durations)

        # Находим аномально высокую активность
        for date, day_data in daily_data.items():
            interaction_count = len(day_data["interactions"])
            total_duration = day_data["total_duration"]

            # Аномально высокая активность (> 3x среднего)
            if interaction_count > avg_count * 3 and avg_count > 1:
                anomalies.append(
                    {
                        "type": "high_activity",
                        "date": date,
                        "description": f"Необычно высокая активность: {interaction_count} взаимодействий",
                        "severity": "medium",
                        "value": interaction_count,
                        "baseline": avg_count,
                    }
                )

            # Аномально долгие сессии
            if total_duration > avg_duration * 4 and avg_duration > 60:
                anomalies.append(
                    {
                        "type": "long_session",
                        "date": date,
                        "description": f"Необычно долгая сессия: {total_duration // 60} минут",
                        "severity": "low",
                        "value": total_duration,
                        "baseline": avg_duration,
                    }
                )

        # Находим периоды полного отсутствия активности
        dates = sorted(daily_data.keys())
        for i in range(1, len(dates)):
            current_date = datetime.fromisoformat(dates[i]).date()
            prev_date = datetime.fromisoformat(dates[i - 1]).date()

            gap_days = (current_date - prev_date).days
            if gap_days > 7:  # Пропуск более недели
                anomalies.append(
                    {
                        "type": "activity_gap",
                        "date_range": f"{prev_date} - {current_date}",
                        "description": f"Отсутствие активности в течение {gap_days} дней",
                        "severity": "high",
                        "value": gap_days,
                        "baseline": 1,
                    }
                )

        return anomalies

    def _detect_interaction_anomalies(
        self, behavior_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Выявляет аномалии в типах взаимодействий."""

        anomalies = []
        daily_data = behavior_data["daily_data"]

        # Анализируем паттерны рейтингов
        all_ratings = []
        for day_data in daily_data.values():
            all_ratings.extend(day_data["ratings"])

        if len(all_ratings) < 10:  # Недостаточно данных
            return anomalies

        avg_rating = sum(all_ratings) / len(all_ratings)

        # Находим дни с аномально низкими рейтингами
        for date, day_data in daily_data.items():
            ratings = day_data["ratings"]

            if ratings:
                day_avg_rating = sum(ratings) / len(ratings)

                # Аномально низкие рейтинги
                if day_avg_rating < avg_rating - 1.5 and len(ratings) >= 3:
                    anomalies.append(
                        {
                            "type": "low_satisfaction",
                            "date": date,
                            "description": f"Необычно низкие оценки: {day_avg_rating:.1f}",
                            "severity": "high",
                            "value": day_avg_rating,
                            "baseline": avg_rating,
                        }
                    )

                # Только негативные оценки в день
                if (
                    all(rating <= 2 for rating in ratings)
                    and len(ratings) >= 2
                ):
                    anomalies.append(
                        {
                            "type": "negative_feedback",
                            "date": date,
                            "description": "Только негативные оценки в этот день",
                            "severity": "high",
                            "value": len(ratings),
                            "baseline": 0,
                        }
                    )

        return anomalies

    def _detect_preference_anomalies(
        self, behavior_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Выявляет аномалии в предпочтениях контента."""

        anomalies = []
        daily_data = behavior_data["daily_data"]

        # Анализируем разнообразие контента
        all_content_types = set()
        daily_diversity = []

        for day_data in daily_data.values():
            content_types = day_data["content_types"]
            all_content_types.update(content_types)
            daily_diversity.append(len(content_types))

        avg_diversity = (
            sum(daily_diversity) / len(daily_diversity)
            if daily_diversity
            else 0
        )

        # Находим дни с необычно ограниченным разнообразием
        for date, day_data in daily_data.items():
            interactions = day_data["interactions"]
            content_types = day_data["content_types"]

            if len(interactions) >= 5 and len(content_types) == 1:
                anomalies.append(
                    {
                        "type": "content_fixation",
                        "date": date,
                        "description": f"Фокус только на одном типе контента: {list(content_types)[0]}",
                        "severity": "medium",
                        "value": len(content_types),
                        "baseline": avg_diversity,
                    }
                )

        # Анализируем резкие изменения в предпочтениях
        content_type_trends = {}
        for date, day_data in daily_data.items():
            for content_type in day_data["content_types"]:
                if content_type not in content_type_trends:
                    content_type_trends[content_type] = []
                content_type_trends[content_type].append(date)

        # Находим типы контента, которые внезапно исчезли
        for content_type, dates in content_type_trends.items():
            if len(dates) >= 3:  # Был активен минимум 3 дня
                sorted_dates = sorted(dates)
                last_date = datetime.fromisoformat(sorted_dates[-1]).date()
                days_since_last = (datetime.utcnow().date() - last_date).days

                if days_since_last > 14:  # Не использовался больше 2 недель
                    anomalies.append(
                        {
                            "type": "preference_abandonment",
                            "content_type": content_type,
                            "description": f"Прекращение использования {content_type}",
                            "severity": "medium",
                            "value": days_since_last,
                            "baseline": 7,
                        }
                    )

        return anomalies

    def _generate_anomaly_recommendations(
        self, anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """Генерирует рекомендации на основе выявленных аномалий."""

        recommendations = []

        anomaly_types = set(anomaly["type"] for anomaly in anomalies)

        if "high_activity" in anomaly_types:
            recommendations.append(
                "Рассмотреть возможность предложения премиум-функций для активных пользователей"
            )

        if "activity_gap" in anomaly_types:
            recommendations.append(
                "Настроить уведомления для возврата неактивных пользователей"
            )

        if (
            "low_satisfaction" in anomaly_types
            or "negative_feedback" in anomaly_types
        ):
            recommendations.append(
                "Провести анализ качества контента и собрать детальную обратную связь"
            )

        if "content_fixation" in anomaly_types:
            recommendations.append(
                "Предложить разнообразный контент для расширения интересов"
            )

        if "preference_abandonment" in anomaly_types:
            recommendations.append(
                "Исследовать причины отказа от определенных типов контента"
            )

        if not recommendations:
            recommendations.append(
                "Продолжать мониторинг поведения пользователя"
            )

        return recommendations
