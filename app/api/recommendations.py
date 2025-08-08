"""
API endpoints for recommendation and personalization system.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.services.ml_analytics_service import (
    AnomalyDetectionSystem,
    ChurnPredictionModel,
    EngagementOptimizer,
    PreferenceLearningEngine,
)
from app.services.personalization_service import (
    CommunicationStyleAdapter,
    ComplexityLevelAdjuster,
    CulturalSensitivityManager,
    DynamicHoroscopeGenerator,
    InterestProfilingSystem,
)
from app.services.recommendation_engine import (
    ABTestManager,
    HybridRecommendationEngine,
    MetricsCollector,
    TemporalPatternAnalyzer,
    UserClusteringManager,
)
from app.services.user_manager import UserManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# Response models
class RecommendationResponse(BaseModel):
    content_type: str
    confidence_score: int
    algorithm: str
    data: Dict[str, Any]
    personalization: Optional[Dict[str, Any]] = None


class PersonalizedHoroscopeResponse(BaseModel):
    content: str
    horoscope_type: str
    personalization_applied: List[str]
    complexity_level: str
    cultural_context: str


class UserAnalyticsResponse(BaseModel):
    engagement_level: str
    churn_risk: str
    interests: Dict[str, float]
    recommendations_count: int


class ABTestResponse(BaseModel):
    test_name: str
    assigned_group: str
    test_parameters: Dict[str, Any]


# Recommendation endpoints
@router.get("/user/{user_id}", response_model=List[RecommendationResponse])
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_database),
) -> List[RecommendationResponse]:
    """
    Получает персонализированные рекомендации для пользователя.

    Args:
        user_id: ID пользователя в Яндексе
        limit: Максимальное количество рекомендаций
        db: Сессия базы данных

    Returns:
        Список рекомендаций
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Генерируем рекомендации
        recommendation_engine = HybridRecommendationEngine(db)
        recommendations = await recommendation_engine.generate_recommendations(
            user.id, limit
        )

        # Формируем ответ
        response = []
        for rec in recommendations:
            response.append(
                RecommendationResponse(
                    content_type=rec.get("content_type", "unknown"),
                    confidence_score=rec.get("final_score", 0),
                    algorithm=rec.get("algorithm", "hybrid"),
                    data=rec.get("data", {}),
                    personalization=rec.get("personalization"),
                )
            )

        return response

    except Exception as e:
        logger.error(
            f"Error getting recommendations for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/user/{user_id}/horoscope", response_model=PersonalizedHoroscopeResponse
)
async def get_personalized_horoscope(
    user_id: str,
    horoscope_type: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    db: AsyncSession = Depends(get_database),
) -> PersonalizedHoroscopeResponse:
    """
    Генерирует персонализированный гороскоп для пользователя.

    Args:
        user_id: ID пользователя в Яндексе
        horoscope_type: Тип гороскопа (daily, weekly, monthly)
        db: Сессия базы данных

    Returns:
        Персонализированный гороскоп
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Генерируем персонализированный гороскоп
        horoscope_generator = DynamicHoroscopeGenerator(db)
        horoscope_data = (
            await horoscope_generator.generate_personalized_horoscope(
                user.id, horoscope_type
            )
        )

        if not horoscope_data:
            raise HTTPException(
                status_code=500, detail="Could not generate horoscope"
            )

        # Адаптируем стиль общения
        style_adapter = CommunicationStyleAdapter(db)
        adapted_content = await style_adapter.adapt_content_style(
            horoscope_data.get("content", ""), user.id
        )

        # Настраиваем сложность
        complexity_adjuster = ComplexityLevelAdjuster(db)
        adjusted_horoscope = (
            await complexity_adjuster.adjust_content_complexity(
                horoscope_data, user.id
            )
        )

        # Применяем культурную адаптацию
        cultural_manager = CulturalSensitivityManager(db)
        culturally_adapted = await cultural_manager.adapt_cultural_context(
            adjusted_horoscope, user.id
        )

        return PersonalizedHoroscopeResponse(
            content=adapted_content,
            horoscope_type=horoscope_type,
            personalization_applied=[
                "communication_style",
                "complexity_level",
                "cultural_context",
                "life_situation",
            ],
            complexity_level=adjusted_horoscope.get(
                "complexity", "intermediate"
            ),
            cultural_context=culturally_adapted.get(
                "cultural_note", "western"
            ),
        )

    except Exception as e:
        logger.error(
            f"Error generating personalized horoscope for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}/analytics", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user_id: str, db: AsyncSession = Depends(get_database)
) -> UserAnalyticsResponse:
    """
    Получает аналитику пользователя для персонализации.

    Args:
        user_id: ID пользователя в Яндексе
        db: Сессия базы данных

    Returns:
        Аналитические данные пользователя
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Анализируем предпочтения
        interest_profiler = InterestProfilingSystem(db)
        interests = await interest_profiler.update_user_profile(user.id)

        # Предсказываем риск оттока
        churn_model = ChurnPredictionModel(db)
        churn_prediction = await churn_model.predict_churn_risk(user.id)

        # Анализируем вовлеченность
        engagement_optimizer = EngagementOptimizer(db)
        engagement_analysis = (
            await engagement_optimizer.optimize_user_engagement(user.id)
        )

        # Получаем количество рекомендаций
        recommendation_engine = HybridRecommendationEngine(db)
        recommendations = await recommendation_engine.generate_recommendations(
            user.id
        )

        return UserAnalyticsResponse(
            engagement_level=engagement_analysis["current_engagement"][
                "overall_level"
            ],
            churn_risk=churn_prediction["risk_level"],
            interests=interests,
            recommendations_count=len(recommendations),
        )

    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/user/{user_id}/interaction")
async def record_user_interaction(
    user_id: str,
    interaction_data: Dict[str, Any],
    db: AsyncSession = Depends(get_database),
) -> Dict[str, str]:
    """
    Записывает взаимодействие пользователя для обучения модели.

    Args:
        user_id: ID пользователя в Яндексе
        interaction_data: Данные о взаимодействии
        db: Сессия базы данных

    Returns:
        Статус операции
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Записываем метрику
        metrics_collector = MetricsCollector(db)

        if interaction_data.get("type") == "recommendation_view":
            await metrics_collector.record_recommendation_view(
                user.id,
                interaction_data.get("recommendation_id"),
                interaction_data.get("session_id"),
            )
        elif interaction_data.get("type") == "recommendation_click":
            await metrics_collector.record_recommendation_click(
                user.id,
                interaction_data.get("recommendation_id"),
                interaction_data.get("session_id"),
            )

        return {"status": "success", "message": "Interaction recorded"}

    except Exception as e:
        logger.error(
            f"Error recording interaction for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}/seasonal")
async def get_seasonal_recommendations(
    user_id: str, db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """
    Получает сезонные рекомендации с астрологической адаптацией.

    Args:
        user_id: ID пользователя в Яндексе
        db: Сессия базы данных

    Returns:
        Сезонные рекомендации
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Получаем сезонные рекомендации
        temporal_analyzer = TemporalPatternAnalyzer(db)
        seasonal_data = await temporal_analyzer.get_seasonal_recommendations(
            user.id
        )

        return seasonal_data

    except Exception as e:
        logger.error(
            f"Error getting seasonal recommendations for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


# A/B Testing endpoints
@router.post("/ab-test/{user_id}/{test_name}", response_model=ABTestResponse)
async def assign_ab_test(
    user_id: str, test_name: str, db: AsyncSession = Depends(get_database)
) -> ABTestResponse:
    """
    Назначает пользователя в A/B тест.

    Args:
        user_id: ID пользователя в Яндексе
        test_name: Название теста
        db: Сессия базы данных

    Returns:
        Информация о назначении в тест
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Назначаем в тест
        ab_test_manager = ABTestManager(db)
        assigned_group = await ab_test_manager.assign_user_to_test(
            user.id, test_name
        )

        # Получаем параметры теста
        test_parameters = ab_test_manager._get_test_parameters(
            test_name, assigned_group
        )

        return ABTestResponse(
            test_name=test_name,
            assigned_group=assigned_group,
            test_parameters=test_parameters,
        )

    except Exception as e:
        logger.error(f"Error assigning A/B test for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Machine Learning endpoints
@router.post("/ml/update-clusters")
async def update_user_clusters(
    db: AsyncSession = Depends(get_database),
) -> Dict[str, Any]:
    """
    Обновляет кластеры пользователей для коллаборативной фильтрации.

    Args:
        db: Сессия базы данных

    Returns:
        Результат обновления кластеров
    """
    try:
        clustering_manager = UserClusteringManager(db)
        updated_count = await clustering_manager.update_user_clusters()

        return {
            "status": "success",
            "updated_users": updated_count,
            "message": "User clusters updated successfully",
        }

    except Exception as e:
        logger.error(f"Error updating user clusters: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ml/user/{user_id}/preferences")
async def learn_user_preferences(
    user_id: str, db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """
    Обновляет изученные предпочтения пользователя.

    Args:
        user_id: ID пользователя в Яндексе
        db: Сессия базы данных

    Returns:
        Изученные предпочтения
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Обучаемся на предпочтениях
        preference_engine = PreferenceLearningEngine(db)
        learned_preferences = await preference_engine.learn_user_preferences(
            user.id
        )

        return {
            "status": "success",
            "learned_preferences": learned_preferences,
        }

    except Exception as e:
        logger.error(
            f"Error learning preferences for user {user_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/ml/user/{user_id}/anomalies")
async def detect_user_anomalies(
    user_id: str, db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """
    Выявляет аномалии в поведении пользователя.

    Args:
        user_id: ID пользователя в Яндексе
        db: Сессия базы данных

    Returns:
        Выявленные аномалии и рекомендации
    """
    try:
        # Получаем пользователя
        user_manager = UserManager(db)
        user = await user_manager.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Выявляем аномалии
        anomaly_detector = AnomalyDetectionSystem(db)
        anomalies = await anomaly_detector.detect_anomalies(user.id)

        return anomalies

    except Exception as e:
        logger.error(f"Error detecting anomalies for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Metrics endpoints
@router.get("/metrics")
async def get_recommendation_metrics(
    period_days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_database),
) -> Dict[str, Any]:
    """
    Получает метрики эффективности рекомендательной системы.

    Args:
        period_days: Период для анализа в днях
        db: Сессия базы данных

    Returns:
        Агрегированные метрики
    """
    try:
        metrics_collector = MetricsCollector(db)
        metrics = await metrics_collector.get_recommendation_metrics(
            period_days
        )

        return {
            "status": "success",
            "metrics": metrics,
            "analysis_period": f"{period_days} days",
        }

    except Exception as e:
        logger.error(f"Error getting recommendation metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Проверка здоровья системы рекомендаций.

    Returns:
        Статус системы рекомендаций
    """
    try:
        return {
            "status": "healthy",
            "service": "recommendation_system",
            "components": {
                "recommendation_engine": "ok",
                "personalization_service": "ok",
                "ml_analytics": "ok",
                "metrics_collector": "ok",
                "ab_testing": "ok",
            },
        }
    except Exception as e:
        logger.error(f"Recommendation system health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
