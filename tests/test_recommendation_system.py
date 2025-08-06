"""
Comprehensive tests for the recommendation and personalization system.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User
from app.models.recommendation_models import (
    UserPreference,
    UserInteraction,
    RecommendationItem,
    UserRecommendation,
    ABTestGroup,
)
from app.services.recommendation_engine import (
    CollaborativeFilter,
    ContentBasedFilter,
    HybridRecommendationEngine,
    TemporalPatternAnalyzer,
    SeasonalAdaptationEngine,
)
from app.services.personalization_service import (
    PersonalizationService,
    InterestProfilingService,
)
from app.services.ml_analytics import (
    UserClusteringService,
    ChurnPredictionService,
    EngagementOptimizationService,
    AnomalyDetectionService,
)
from app.services.ab_testing_service import ABTestingService, MetricsCollectionService


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid.uuid4(),
        yandex_user_id="test_user_123",
        zodiac_sign="leo",
        gender="female",
        data_consent=True,
        created_at=datetime.utcnow() - timedelta(days=30),
        last_accessed=datetime.utcnow()
    )


@pytest.fixture
def sample_user_preference():
    """Sample user preference for testing."""
    return UserPreference(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        career_interest=0.8,
        love_interest=0.6,
        health_interest=0.4,
        finance_interest=0.7,
        family_interest=0.5,
        spiritual_interest=0.3,
        communication_style="casual",
        complexity_level="intermediate",
        preferred_length="medium",
        emotional_tone="positive",
        cultural_context="russian",
        language_preference="ru",
        use_name_in_responses=True,
    )


@pytest.fixture
def sample_interactions():
    """Sample user interactions for testing."""
    base_time = datetime.utcnow() - timedelta(days=10)
    user_id = uuid.uuid4()
    
    interactions = []
    for i in range(10):
        interaction = UserInteraction(
            id=uuid.uuid4(),
            user_id=user_id,
            interaction_type="request",
            content_category="career" if i % 3 == 0 else "love",
            content_id=f"content_{i}",
            session_duration=60 + i * 10,
            response_rating=3.5 + (i % 3) * 0.5,
            time_of_day="morning" if i < 5 else "evening",
            day_of_week="monday",
            timestamp=base_time + timedelta(days=i),
        )
        interactions.append(interaction)
    
    return interactions


class TestCollaborativeFilter:
    """Test collaborative filtering algorithm."""

    @pytest.mark.asyncio
    async def test_calculate_user_similarities(self, mock_db_session, sample_user):
        """Test user similarity calculation."""
        collaborative_filter = CollaborativeFilter(mock_db_session)
        
        # Mock database responses
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
            uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        ]
        
        # Mock preference vector method
        collaborative_filter._get_user_preference_vector = AsyncMock(
            return_value=[0.8, 0.6, 0.4, 0.7, 0.5, 0.3, 0.5, 0.5, 0.8, 0.3]
        )
        collaborative_filter._calculate_behavioral_similarity = AsyncMock(return_value=0.7)
        collaborative_filter._calculate_astrological_similarity = AsyncMock(return_value=0.6)
        collaborative_filter._store_user_similarities = AsyncMock()

        similarities = await collaborative_filter.calculate_user_similarities(sample_user.id)
        
        assert isinstance(similarities, list)
        # Verify that _store_user_similarities was called
        collaborative_filter._store_user_similarities.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_collaborative_recommendations(self, mock_db_session):
        """Test collaborative recommendation generation."""
        collaborative_filter = CollaborativeFilter(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock similar users
        collaborative_filter._get_stored_similarities = AsyncMock(return_value=[
            {
                'user_id': uuid.uuid4(),
                'similarity_score': 0.8,
                'preference_similarity': 0.7,
                'behavior_similarity': 0.8,
                'astrological_similarity': 0.9
            }
        ])
        
        # Mock positive interactions
        mock_interactions = [
            MagicMock(content_category="career", content_id="career_1", response_rating=4.5),
            MagicMock(content_category="love", content_id="love_1", response_rating=4.0),
        ]
        collaborative_filter._get_positive_user_interactions = AsyncMock(
            return_value=mock_interactions
        )
        collaborative_filter._get_user_interaction_history = AsyncMock(return_value=[])
        collaborative_filter._get_interaction_weight = MagicMock(return_value=0.8)

        recommendations = await collaborative_filter.generate_collaborative_recommendations(
            user_id, limit=5
        )
        
        assert isinstance(recommendations, list)
        if recommendations:  # If any recommendations were generated
            assert all('content_category' in rec for rec in recommendations)
            assert all('score' in rec for rec in recommendations)
            assert all('algorithm' in rec for rec in recommendations)


class TestContentBasedFilter:
    """Test content-based filtering algorithm."""

    @pytest.mark.asyncio
    async def test_generate_content_recommendations(self, mock_db_session):
        """Test content-based recommendation generation."""
        content_filter = ContentBasedFilter(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock user profile
        content_filter._build_user_content_profile = AsyncMock(return_value={
            'interest_scores': {'career': 0.8, 'love': 0.6},
            'zodiac_sign': 'leo',
            'communication_style': 'casual',
            'complexity_level': 'intermediate'
        })
        
        # Mock recommendation items
        mock_items = [
            MagicMock(
                item_category="career",
                item_identifier="career_item_1",
                zodiac_signs=["leo", "aries"],
                tags=["professional", "growth"],
                popularity_score=0.8,
                engagement_score=0.7,
                feedback_score=0.9,
                is_active=True
            )
        ]
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_items
        
        content_filter._get_user_content_history = AsyncMock(return_value=[])
        content_filter._has_user_seen_item = MagicMock(return_value=False)
        content_filter._calculate_content_similarity = AsyncMock(return_value=0.7)
        content_filter._generate_content_reason = MagicMock(return_value="Matches your interests")

        recommendations = await content_filter.generate_content_recommendations(
            user_id, limit=5
        )
        
        assert isinstance(recommendations, list)


class TestPersonalizationService:
    """Test personalization service."""

    @pytest.mark.asyncio
    async def test_create_user_preference(self, mock_db_session):
        """Test user preference creation."""
        personalization_service = PersonalizationService(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock no existing preferences
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        preferences = {
            'career_interest': 0.8,
            'communication_style': 'casual',
            'complexity_level': 'advanced'
        }

        result = await personalization_service.create_user_preference(user_id, preferences)
        
        assert isinstance(result, UserPreference)
        assert result.career_interest == 0.8
        assert result.communication_style == 'casual'
        assert result.complexity_level == 'advanced'

    @pytest.mark.asyncio
    async def test_track_user_interaction(self, mock_db_session):
        """Test user interaction tracking."""
        personalization_service = PersonalizationService(mock_db_session)
        user_id = uuid.uuid4()
        
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        personalization_service.update_preferences_from_interaction = AsyncMock()

        interaction = await personalization_service.track_user_interaction(
            user_id,
            interaction_type="request",
            content_category="career",
            response_rating=4.5,
            session_duration=120
        )
        
        assert isinstance(interaction, UserInteraction)
        assert interaction.user_id == user_id
        assert interaction.interaction_type == "request"
        assert interaction.content_category == "career"
        assert interaction.response_rating == 4.5

    @pytest.mark.asyncio
    async def test_generate_dynamic_horoscope_prompt(self, mock_db_session, sample_user_preference):
        """Test dynamic horoscope prompt generation."""
        personalization_service = PersonalizationService(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock get personalized content settings
        personalization_service.get_personalized_content_settings = AsyncMock(return_value={
            'communication_style': 'casual',
            'complexity_level': 'intermediate',
            'preferred_length': 'medium',
            'emotional_tone': 'positive',
            'user_name': 'Anna',
            'zodiac_sign': 'leo',
            'interest_weights': {'career': 0.8, 'love': 0.6, 'health': 0.4},
            'include_features': {
                'lucky_numbers': True,
                'lucky_colors': True,
                'compatibility_hints': True
            }
        })

        base_content = "Your daily horoscope shows positive energy."
        
        prompt = await personalization_service.generate_dynamic_horoscope_prompt(
            user_id, "daily", base_content
        )
        
        assert isinstance(prompt, str)
        assert "casual" in prompt or "friendly" in prompt
        assert "intermediate" in prompt or "balanced" in prompt
        assert base_content in prompt


class TestUserClusteringService:
    """Test user clustering service."""

    @pytest.mark.asyncio
    async def test_get_user_cluster(self, mock_db_session):
        """Test user cluster assignment."""
        clustering_service = UserClusteringService(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock user features
        clustering_service._get_single_user_features = AsyncMock(return_value={
            'interests': {
                'career': 0.9,
                'love': 0.4,
                'health': 0.3,
                'finance': 0.6,
                'family': 0.5,
                'spiritual': 0.2,
            },
            'zodiac_sign': 'leo'
        })

        cluster_info = await clustering_service.get_user_cluster(user_id)
        
        assert isinstance(cluster_info, dict)
        assert 'cluster_id' in cluster_info
        assert 'cluster_name' in cluster_info
        assert 'primary_interest' in cluster_info
        assert cluster_info['primary_interest'] == 'career'  # Highest interest


class TestChurnPredictionService:
    """Test churn prediction service."""

    @pytest.mark.asyncio
    async def test_predict_user_churn_risk(self, mock_db_session):
        """Test churn risk prediction."""
        churn_service = ChurnPredictionService(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock user features with high risk indicators
        churn_service._extract_churn_features = AsyncMock(return_value={
            'days_since_last_activity': 15,  # Somewhat inactive
            'total_interactions': 5,
            'avg_rating': 2.5,  # Low satisfaction
            'interaction_frequency': 0.03,  # Low frequency
            'recent_frequency': 0.0,  # No recent activity
            'avg_session_duration': 20,  # Short sessions
            'content_diversity': 1,
            'risk_factors': ['inactive_recently', 'low_satisfaction', 'low_frequency']
        })

        prediction = await churn_service.predict_user_churn_risk(user_id)
        
        assert isinstance(prediction, dict)
        assert 'churn_risk_score' in prediction
        assert 'risk_level' in prediction
        assert 'suggested_interventions' in prediction
        assert prediction['churn_risk_score'] >= 0.0
        assert prediction['churn_risk_score'] <= 1.0


class TestEngagementOptimizationService:
    """Test engagement optimization service."""

    @pytest.mark.asyncio
    async def test_optimize_content_timing(self, mock_db_session, sample_interactions):
        """Test content timing optimization."""
        engagement_service = EngagementOptimizationService(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock interactions
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_interactions

        timing_optimization = await engagement_service.optimize_content_timing(user_id)
        
        assert isinstance(timing_optimization, dict)
        assert 'optimal_hours' in timing_optimization
        assert 'optimal_days' in timing_optimization
        assert 'recommended_frequency' in timing_optimization
        assert 'consistency_score' in timing_optimization

    @pytest.mark.asyncio
    async def test_calculate_engagement_score(self, mock_db_session, sample_interactions):
        """Test engagement score calculation."""
        engagement_service = EngagementOptimizationService(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock interactions
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_interactions

        engagement_score = await engagement_service.calculate_engagement_score(user_id)
        
        assert isinstance(engagement_score, float)
        assert 0.0 <= engagement_score <= 1.0


class TestABTestingService:
    """Test A/B testing service."""

    @pytest.mark.asyncio
    async def test_create_ab_test(self, mock_db_session):
        """Test A/B test creation."""
        ab_service = ABTestingService(mock_db_session)
        
        test_groups = [
            {
                'group_name': 'control',
                'traffic_percentage': 0.5,
                'algorithm_config': {'type': 'current_algorithm', 'version': '1.0'}
            },
            {
                'group_name': 'variant_a',
                'traffic_percentage': 0.5,
                'algorithm_config': {'type': 'new_algorithm', 'version': '2.0'}
            }
        ]
        
        mock_db_session.flush = AsyncMock()
        mock_db_session.commit = AsyncMock()

        result = await ab_service.create_ab_test(
            test_name="recommendation_algorithm_test",
            test_groups=test_groups,
            description="Testing new recommendation algorithm",
            duration_days=14
        )
        
        assert isinstance(result, dict)
        assert result['test_name'] == "recommendation_algorithm_test"
        assert 'groups' in result
        assert len(result['groups']) == 2

    @pytest.mark.asyncio
    async def test_assign_user_to_test(self, mock_db_session):
        """Test user assignment to A/B test."""
        ab_service = ABTestingService(mock_db_session)
        user_id = uuid.uuid4()
        test_name = "test_algorithm"
        
        # Mock no existing assignment
        ab_service._get_user_assignment = AsyncMock(return_value=None)
        
        # Mock test groups
        mock_group = MagicMock()
        mock_group.id = uuid.uuid4()
        mock_group.group_name = "control"
        mock_group.algorithm_config = {"type": "current"}
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_group]
        ab_service._assign_user_to_group = MagicMock(return_value=mock_group)
        mock_db_session.commit = AsyncMock()

        assignment = await ab_service.assign_user_to_test(user_id, test_name)
        
        assert isinstance(assignment, dict)
        assert assignment['test_name'] == test_name
        assert assignment['group_name'] == "control"


class TestHybridRecommendationEngine:
    """Test hybrid recommendation engine."""

    @pytest.mark.asyncio
    async def test_generate_hybrid_recommendations(self, mock_db_session):
        """Test hybrid recommendation generation."""
        hybrid_engine = HybridRecommendationEngine(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock collaborative and content recommendations
        collaborative_recs = [
            {
                'content_category': 'career',
                'content_id': 'career_1',
                'score': 0.8,
                'reason': 'Similar users liked this'
            }
        ]
        
        content_recs = [
            {
                'item': MagicMock(item_category='love', item_identifier='love_1'),
                'score': 0.7,
                'reason': 'Matches your interests'
            }
        ]
        
        hybrid_engine.collaborative_filter.generate_collaborative_recommendations = AsyncMock(
            return_value=collaborative_recs
        )
        hybrid_engine.content_filter.generate_content_recommendations = AsyncMock(
            return_value=content_recs
        )
        hybrid_engine._store_recommendations = AsyncMock()

        recommendations = await hybrid_engine.generate_hybrid_recommendations(
            user_id, limit=5, include_reasoning=True
        )
        
        assert isinstance(recommendations, list)
        if recommendations:
            assert all('hybrid_score' in rec for rec in recommendations)
            assert all('algorithm' in rec for rec in recommendations)


class TestSeasonalAdaptationEngine:
    """Test seasonal adaptation engine."""

    @pytest.mark.asyncio
    async def test_apply_seasonal_adaptation(self, mock_db_session):
        """Test seasonal adaptation of recommendations."""
        seasonal_engine = SeasonalAdaptationEngine(mock_db_session)
        user_id = uuid.uuid4()
        
        base_recommendations = [
            {
                'content_category': 'career',
                'content_id': 'career_1',
                'hybrid_score': 0.8,
            },
            {
                'content_category': 'love',
                'content_id': 'love_1',
                'hybrid_score': 0.7,
            }
        ]
        
        # Mock astrological context
        seasonal_engine._get_current_astrological_context = AsyncMock(return_value={
            'season': 'spring',
            'moon_phase': 'new',
            'astrological_season': 'aries'
        })
        seasonal_engine._get_user_seasonal_context = AsyncMock(return_value={
            'zodiac_sign': 'leo'
        })

        adapted_recs = await seasonal_engine.apply_seasonal_adaptation(
            base_recommendations, user_id
        )
        
        assert isinstance(adapted_recs, list)
        assert len(adapted_recs) == len(base_recommendations)
        if adapted_recs:
            assert all('seasonal_score' in rec for rec in adapted_recs)
            assert all('adapted_score' in rec for rec in adapted_recs)


class TestInterestProfilingService:
    """Test interest profiling service."""

    @pytest.mark.asyncio
    async def test_analyze_user_interests(self, mock_db_session, sample_interactions):
        """Test user interest analysis."""
        interest_service = InterestProfilingService(mock_db_session)
        user_id = uuid.uuid4()
        
        # Mock interactions with different categories and ratings
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = sample_interactions

        interests = await interest_service.analyze_user_interests(user_id)
        
        assert isinstance(interests, dict)
        assert all(category in interests for category in [
            'career', 'love', 'health', 'finance', 'family', 'spiritual'
        ])
        assert all(0.0 <= score <= 1.0 for score in interests.values())


# Integration test
class TestRecommendationSystemIntegration:
    """Integration tests for the complete recommendation system."""

    @pytest.mark.asyncio
    async def test_complete_recommendation_flow(self, mock_db_session):
        """Test the complete recommendation flow from user interaction to recommendations."""
        # This would be a comprehensive test that goes through:
        # 1. User interaction tracking
        # 2. Preference learning
        # 3. Recommendation generation
        # 4. Personalization
        # 5. A/B testing
        
        user_id = uuid.uuid4()
        
        # Step 1: Track user interaction
        personalization_service = PersonalizationService(mock_db_session)
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        personalization_service.update_preferences_from_interaction = AsyncMock()
        
        interaction = await personalization_service.track_user_interaction(
            user_id,
            interaction_type="request",
            content_category="career",
            response_rating=4.5
        )
        
        assert interaction.user_id == user_id
        
        # Step 2: Generate recommendations
        hybrid_engine = HybridRecommendationEngine(mock_db_session)
        hybrid_engine.collaborative_filter.generate_collaborative_recommendations = AsyncMock(
            return_value=[]
        )
        hybrid_engine.content_filter.generate_content_recommendations = AsyncMock(
            return_value=[]
        )
        hybrid_engine._store_recommendations = AsyncMock()
        
        recommendations = await hybrid_engine.generate_hybrid_recommendations(user_id, limit=5)
        
        assert isinstance(recommendations, list)
        
        # Step 3: Apply personalization
        personalization_service.get_personalized_content_settings = AsyncMock(return_value={
            'communication_style': 'casual',
            'complexity_level': 'intermediate',
            'user_name': 'Test User'
        })
        
        settings = await personalization_service.get_personalized_content_settings(user_id)
        assert settings['communication_style'] == 'casual'


# Test utilities and helpers
@pytest.mark.asyncio
async def test_recommendation_system_dependencies():
    """Test that all recommendation system components can be imported without errors."""
    try:
        from app.services.recommendation_engine import HybridRecommendationEngine
        from app.services.personalization_service import PersonalizationService
        from app.services.ml_analytics import UserClusteringService
        from app.services.ab_testing_service import ABTestingService
        from app.models.recommendation_models import UserPreference
        
        # If we get here, all imports are successful
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import recommendation system components: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])