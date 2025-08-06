"""
API endpoints for recommendation and personalization system.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.services.recommendation_engine import (
    HybridRecommendationEngine,
    TemporalPatternAnalyzer,
    SeasonalAdaptationEngine
)
from app.services.personalization_service import PersonalizationService, InterestProfilingService
from app.services.ml_analytics import (
    UserClusteringService,
    ChurnPredictionService,
    EngagementOptimizationService,
    AnomalyDetectionService
)
from app.services.ab_testing_service import ABTestingService, MetricsCollectionService
from app.services.user_manager import UserManager

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


# Pydantic models for request/response
class UserPreferenceUpdate(BaseModel):
    career_interest: Optional[float] = Field(None, ge=0.0, le=1.0)
    love_interest: Optional[float] = Field(None, ge=0.0, le=1.0)
    health_interest: Optional[float] = Field(None, ge=0.0, le=1.0)
    finance_interest: Optional[float] = Field(None, ge=0.0, le=1.0)
    family_interest: Optional[float] = Field(None, ge=0.0, le=1.0)
    spiritual_interest: Optional[float] = Field(None, ge=0.0, le=1.0)
    communication_style: Optional[str] = Field(None, regex="^(formal|casual|balanced)$")
    complexity_level: Optional[str] = Field(None, regex="^(beginner|intermediate|advanced)$")
    preferred_length: Optional[str] = Field(None, regex="^(short|medium|long)$")
    emotional_tone: Optional[str] = Field(None, regex="^(positive|neutral|realistic)$")
    cultural_context: Optional[str] = None
    timezone: Optional[str] = None
    use_name_in_responses: Optional[bool] = None
    include_lucky_numbers: Optional[bool] = None
    include_lucky_colors: Optional[bool] = None
    include_compatibility_hints: Optional[bool] = None


class InteractionTrackingRequest(BaseModel):
    interaction_type: str = Field(..., description="Type of interaction")
    content_category: Optional[str] = None
    content_id: Optional[str] = None
    session_duration: Optional[int] = Field(None, ge=0)
    response_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    feedback_text: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None


class RecommendationRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    limit: Optional[int] = Field(10, ge=1, le=50)
    include_reasoning: Optional[bool] = True
    algorithm_preference: Optional[str] = Field(None, regex="^(collaborative|content_based|hybrid)$")


class ABTestRequest(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=100)
    test_groups: List[Dict[str, Any]] = Field(..., min_items=2)
    description: Optional[str] = None
    duration_days: Optional[int] = Field(30, ge=1, le=365)
    created_by: Optional[str] = None


# Recommendation endpoints
@router.get("/users/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    include_reasoning: bool = Query(True),
    algorithm: Optional[str] = Query(None, regex="^(collaborative|content_based|hybrid)$"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get personalized recommendations for a user.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        
        # Initialize recommendation engine
        hybrid_engine = HybridRecommendationEngine(db)
        seasonal_engine = SeasonalAdaptationEngine(db)
        
        # Get base recommendations
        if algorithm == "collaborative":
            recommendations = await hybrid_engine.collaborative_filter.generate_collaborative_recommendations(
                user_uuid, limit
            )
        elif algorithm == "content_based":
            recommendations = await hybrid_engine.content_filter.generate_content_recommendations(
                user_uuid, limit
            )
        else:  # Default to hybrid
            recommendations = await hybrid_engine.generate_hybrid_recommendations(
                user_uuid, limit, include_reasoning
            )
        
        # Apply seasonal adaptation
        adapted_recs = await seasonal_engine.apply_seasonal_adaptation(recommendations, user_uuid)
        
        return {
            "user_id": user_id,
            "algorithm_used": algorithm or "hybrid",
            "recommendations": adapted_recs,
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(adapted_recs)
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {e}")


@router.get("/users/{user_id}/preferences")
async def get_user_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get user preferences and personalization settings.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        personalization_service = PersonalizationService(db)
        
        preferences = await personalization_service.get_user_preferences(user_uuid)
        profile_summary = await personalization_service.get_user_profile_summary(user_uuid)
        
        return {
            "user_id": user_id,
            "preferences": preferences,
            "profile_summary": profile_summary,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving preferences: {e}")


@router.put("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update user preferences and personalization settings.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        personalization_service = PersonalizationService(db)
        
        # Convert to dict and remove None values
        pref_dict = {k: v for k, v in preferences.dict().items() if v is not None}
        
        updated_prefs = await personalization_service.create_user_preference(user_uuid, pref_dict)
        
        return {
            "user_id": user_id,
            "updated_preferences": updated_prefs,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {e}")


@router.post("/users/{user_id}/interactions")
async def track_user_interaction(
    user_id: str,
    interaction: InteractionTrackingRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Track user interaction for learning and personalization.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        personalization_service = PersonalizationService(db)
        
        tracked_interaction = await personalization_service.track_user_interaction(
            user_uuid,
            interaction.interaction_type,
            interaction.content_category,
            interaction.content_id,
            interaction.session_duration,
            interaction.response_rating,
            interaction.feedback_text,
            interaction.context_data
        )
        
        return {
            "user_id": user_id,
            "interaction_id": str(tracked_interaction.id),
            "tracked_at": tracked_interaction.timestamp.isoformat(),
            "status": "recorded"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking interaction: {e}")


@router.get("/users/{user_id}/personalization")
async def get_personalization_settings(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get personalized content settings for a user.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        personalization_service = PersonalizationService(db)
        
        settings = await personalization_service.get_personalized_content_settings(user_uuid)
        cultural_adaptations = await personalization_service.get_cultural_adaptations(user_uuid)
        
        return {
            "user_id": user_id,
            "content_settings": settings,
            "cultural_adaptations": cultural_adaptations,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving personalization settings: {e}")


@router.post("/users/{user_id}/horoscope/personalize")
async def personalize_horoscope_content(
    user_id: str,
    horoscope_type: str = Query(..., regex="^(daily|weekly|monthly|natal)$"),
    base_content: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate personalized horoscope prompt based on user preferences.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        personalization_service = PersonalizationService(db)
        
        personalized_prompt = await personalization_service.generate_dynamic_horoscope_prompt(
            user_uuid, horoscope_type, base_content
        )
        
        adapted_content = await personalization_service.adapt_communication_style(
            user_uuid, personalized_prompt
        )
        
        return {
            "user_id": user_id,
            "horoscope_type": horoscope_type,
            "personalized_prompt": adapted_content,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error personalizing content: {e}")


# Analytics endpoints
@router.get("/users/{user_id}/analytics/cluster")
async def get_user_cluster(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get user's cluster assignment and characteristics.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        clustering_service = UserClusteringService(db)
        
        cluster_info = await clustering_service.get_user_cluster(user_uuid)
        
        return {
            "user_id": user_id,
            "cluster_info": cluster_info,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cluster info: {e}")


@router.get("/users/{user_id}/analytics/churn-risk")
async def get_churn_risk_prediction(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get churn risk prediction for a user.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        churn_service = ChurnPredictionService(db)
        
        churn_prediction = await churn_service.predict_user_churn_risk(user_uuid)
        
        return {
            "user_id": user_id,
            "churn_prediction": churn_prediction,
            "predicted_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting churn risk: {e}")


@router.get("/users/{user_id}/analytics/engagement")
async def get_engagement_analysis(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get user engagement analysis and optimization recommendations.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        engagement_service = EngagementOptimizationService(db)
        temporal_analyzer = TemporalPatternAnalyzer(db)
        
        engagement_score = await engagement_service.calculate_engagement_score(user_uuid)
        timing_optimization = await engagement_service.optimize_content_timing(user_uuid)
        temporal_patterns = await temporal_analyzer.analyze_user_temporal_patterns(user_uuid)
        
        return {
            "user_id": user_id,
            "engagement_score": engagement_score,
            "timing_optimization": timing_optimization,
            "temporal_patterns": temporal_patterns,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing engagement: {e}")


@router.get("/users/{user_id}/analytics/anomalies")
async def detect_user_anomalies(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Detect anomalies in user behavior patterns.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        anomaly_service = AnomalyDetectionService(db)
        
        anomaly_detection = await anomaly_service.detect_user_anomalies(user_uuid)
        
        return {
            "user_id": user_id,
            "anomaly_analysis": anomaly_detection,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {e}")


@router.get("/users/{user_id}/interests")
async def analyze_user_interests(
    user_id: str,
    update_preferences: bool = Query(False),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Analyze user interests from interaction history.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        interest_service = InterestProfilingService(db)
        
        interests = await interest_service.analyze_user_interests(user_uuid)
        
        if update_preferences:
            await interest_service.update_user_interests(user_uuid, interests)
        
        return {
            "user_id": user_id,
            "interests": interests,
            "preferences_updated": update_preferences,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing interests: {e}")


# A/B Testing endpoints
@router.post("/ab-tests")
async def create_ab_test(
    test_config: ABTestRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new A/B test for recommendation algorithms.
    """
    try:
        ab_service = ABTestingService(db)
        
        test_result = await ab_service.create_ab_test(
            test_config.test_name,
            test_config.test_groups,
            test_config.description,
            test_config.duration_days,
            test_config.created_by
        )
        
        return {
            "test_created": test_result,
            "created_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating A/B test: {e}")


@router.get("/ab-tests")
async def get_active_ab_tests(db: AsyncSession = Depends(get_db_session)):
    """
    Get all currently active A/B tests.
    """
    try:
        ab_service = ABTestingService(db)
        active_tests = await ab_service.get_active_tests()
        
        return {
            "active_tests": active_tests,
            "count": len(active_tests),
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving active tests: {e}")


@router.get("/ab-tests/{test_name}/results")
async def get_ab_test_results(
    test_name: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get A/B test results and statistical analysis.
    """
    try:
        ab_service = ABTestingService(db)
        test_results = await ab_service.get_test_results(test_name)
        
        return {
            "test_results": test_results,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving test results: {e}")


@router.post("/ab-tests/{test_name}/assign/{user_id}")
async def assign_user_to_test(
    test_name: str,
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Assign a user to an A/B test group.
    """
    try:
        user_uuid = uuid.UUID(user_id)
        ab_service = ABTestingService(db)
        
        assignment = await ab_service.assign_user_to_test(user_uuid, test_name)
        
        return {
            "user_id": user_id,
            "test_name": test_name,
            "assignment": assignment,
            "assigned_at": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning user to test: {e}")


@router.delete("/ab-tests/{test_name}")
async def end_ab_test(
    test_name: str,
    winning_group: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    End an A/B test and optionally declare a winner.
    """
    try:
        ab_service = ABTestingService(db)
        end_result = await ab_service.end_ab_test(test_name, winning_group)
        
        return {
            "test_ended": end_result,
            "ended_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending A/B test: {e}")


# System metrics endpoints
@router.get("/metrics/dashboard")
async def get_metrics_dashboard(db: AsyncSession = Depends(get_db_session)):
    """
    Get recommendation system KPI dashboard.
    """
    try:
        metrics_service = MetricsCollectionService(db)
        dashboard = await metrics_service.calculate_kpi_dashboard()
        
        return {
            "dashboard": dashboard,
            "retrieved_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard: {e}")


@router.get("/analytics/clustering/perform")
async def perform_system_clustering(db: AsyncSession = Depends(get_db_session)):
    """
    Perform system-wide user clustering analysis.
    """
    try:
        clustering_service = UserClusteringService(db)
        clustering_results = await clustering_service.perform_user_clustering()
        
        return {
            "clustering_results": clustering_results,
            "performed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing clustering: {e}")


@router.get("/analytics/churn/at-risk")
async def get_at_risk_users(
    risk_threshold: float = Query(0.6, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get users at risk of churning.
    """
    try:
        churn_service = ChurnPredictionService(db)
        at_risk_users = await churn_service.identify_at_risk_users(risk_threshold)
        
        return {
            "at_risk_users": at_risk_users,
            "risk_threshold": risk_threshold,
            "count": len(at_risk_users),
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying at-risk users: {e}")


@router.get("/interests/trending")
async def get_trending_interests(
    timeframe_days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get trending interest categories across all users.
    """
    try:
        interest_service = InterestProfilingService(db)
        trending_interests = await interest_service.get_trending_interests(timeframe_days)
        
        return {
            "trending_interests": trending_interests,
            "timeframe_days": timeframe_days,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending interests: {e}")