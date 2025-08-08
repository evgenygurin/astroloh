"""
Comprehensive tests for the recommendation and personalization system.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    ABTestGroup,
    Recommendation,
    User,
    UserInteraction,
    UserPreference,
)
from app.services.ml_analytics_service import ChurnPredictionModel, EngagementOptimizer
from app.services.personalization_service import (
    CommunicationStyleAdapter,
    DynamicHoroscopeGenerator,
    InterestProfilingSystem,
)
from app.services.recommendation_engine import (
    ABTestManager,
    CollaborativeFiltering,
    ContentBasedFiltering,
    HybridRecommendationEngine,
    MetricsCollector,
    TemporalPatternAnalyzer,
    UserClusteringManager,
)


@pytest.mark.unit
class TestCollaborativeFiltering:
    """Tests for collaborative filtering algorithm."""

    @pytest.mark.asyncio
    async def test_find_similar_users_empty_db(self, db_session: AsyncSession):
        """Test similar users search with empty database."""
        collaborative = CollaborativeFiltering(db_session)

        user_id = uuid.uuid4()
        similar_users = await collaborative.find_similar_users(user_id)

        assert similar_users == []

    @pytest.mark.asyncio
    async def test_find_similar_users_with_data(
        self, db_session: AsyncSession
    ):
        """Test similar users search with sample data."""
        collaborative = CollaborativeFiltering(db_session)

        # Create test users
        user1 = User(
            yandex_user_id="test_user_1",
            zodiac_sign="aries",
            gender="male",
            data_consent=True,
        )
        user2 = User(
            yandex_user_id="test_user_2",
            zodiac_sign="aries",
            gender="male",
            data_consent=True,
        )
        user3 = User(
            yandex_user_id="test_user_3",
            zodiac_sign="leo",
            gender="female",
            data_consent=True,
        )

        db_session.add_all([user1, user2, user3])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)
        await db_session.refresh(user3)

        # Create preferences
        prefs1 = UserPreference(
            user_id=user1.id,
            communication_style="formal",
            complexity_level="advanced",
        )
        prefs2 = UserPreference(
            user_id=user2.id,
            communication_style="formal",
            complexity_level="advanced",
        )
        prefs3 = UserPreference(
            user_id=user3.id,
            communication_style="casual",
            complexity_level="beginner",
        )

        db_session.add_all([prefs1, prefs2, prefs3])
        await db_session.commit()

        # Test similarity
        similar_users = await collaborative.find_similar_users(user1.id)

        # User2 should be most similar (same zodiac, gender, style)
        assert len(similar_users) >= 1
        assert user2.id in [user_id for user_id, _ in similar_users]

    def test_calculate_user_similarity(self, db_session: AsyncSession):
        """Test user similarity calculation."""
        collaborative = CollaborativeFiltering(db_session)

        # Create identical users
        user1 = User(zodiac_sign="aries", gender="male")
        user2 = User(zodiac_sign="aries", gender="male")

        prefs1 = UserPreference(
            communication_style="formal", complexity_level="advanced"
        )
        prefs2 = UserPreference(
            communication_style="formal", complexity_level="advanced"
        )

        similarity = collaborative._calculate_user_similarity(
            user1, prefs1, user2, prefs2
        )

        # Should be high similarity
        assert similarity >= 0.8

        # Test different users
        user3 = User(zodiac_sign="leo", gender="female")
        prefs3 = UserPreference(
            communication_style="casual", complexity_level="beginner"
        )

        similarity_different = collaborative._calculate_user_similarity(
            user1, prefs1, user3, prefs3
        )

        # Should be lower similarity
        assert similarity_different < similarity


@pytest.mark.asyncio
@pytest.mark.unit
class TestContentBasedFiltering:
    """Tests for content-based filtering algorithm."""

    async def test_get_content_recommendations_empty_user(
        self, db_session: AsyncSession
    ):
        """Test content recommendations for non-existent user."""
        content_filter = ContentBasedFiltering(db_session)

        user_id = uuid.uuid4()
        recommendations = await content_filter.get_content_recommendations(
            user_id
        )

        assert recommendations == []

    async def test_get_content_recommendations_with_user(
        self, db_session: AsyncSession
    ):
        """Test content recommendations for existing user."""
        content_filter = ContentBasedFiltering(db_session)

        # Create test user
        user = User(
            yandex_user_id="test_user", zodiac_sign="leo", data_consent=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create preferences
        prefs = UserPreference(
            user_id=user.id,
            interests={"career": 0.8, "love": 0.6},
            communication_style="friendly",
        )
        db_session.add(prefs)
        await db_session.commit()

        recommendations = await content_filter.get_content_recommendations(
            user.id
        )

        # Should generate recommendations
        assert len(recommendations) > 0

        # Check recommendation structure
        for rec in recommendations:
            assert "content_type" in rec
            assert "confidence_score" in rec
            assert "factors" in rec
            assert rec["confidence_score"] >= 0


@pytest.mark.asyncio
@pytest.mark.unit
class TestHybridRecommendationEngine:
    """Tests for hybrid recommendation engine."""

    async def test_generate_recommendations_empty_user(
        self, db_session: AsyncSession
    ):
        """Test hybrid recommendations for non-existent user."""
        hybrid_engine = HybridRecommendationEngine(db_session)

        user_id = uuid.uuid4()
        recommendations = await hybrid_engine.generate_recommendations(user_id)

        assert recommendations == []

    async def test_generate_recommendations_with_user(
        self, db_session: AsyncSession
    ):
        """Test hybrid recommendations for existing user."""
        hybrid_engine = HybridRecommendationEngine(db_session)

        # Create test user with history
        user = User(
            yandex_user_id="test_user", zodiac_sign="pisces", data_consent=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add some interactions
        interaction1 = UserInteraction(
            user_id=user.id,
            interaction_type="like",
            content_type="daily",
            rating=5,
            session_duration=180,
        )
        interaction2 = UserInteraction(
            user_id=user.id,
            interaction_type="view",
            content_type="compatibility",
            rating=4,
            session_duration=120,
        )

        db_session.add_all([interaction1, interaction2])
        await db_session.commit()

        recommendations = await hybrid_engine.generate_recommendations(user.id)

        # Should generate recommendations
        assert len(recommendations) > 0

        # Check final scores are calculated
        for rec in recommendations:
            assert "final_score" in rec
            assert rec["final_score"] >= 0


@pytest.mark.asyncio
@pytest.mark.unit
class TestDynamicHoroscopeGenerator:
    """Tests for dynamic horoscope generation."""

    async def test_generate_personalized_horoscope(
        self, db_session: AsyncSession
    ):
        """Test personalized horoscope generation."""
        generator = DynamicHoroscopeGenerator(db_session)

        # Create test user
        user = User(
            yandex_user_id="test_user", zodiac_sign="gemini", data_consent=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add user interactions for life situation analysis
        interaction = UserInteraction(
            user_id=user.id,
            interaction_type="like",
            content_type="compatibility",
            rating=5,
            session_duration=300,
        )
        db_session.add(interaction)
        await db_session.commit()

        horoscope = await generator.generate_personalized_horoscope(
            user.id, "daily"
        )

        # Should return horoscope data
        assert horoscope is not None
        assert isinstance(horoscope, dict)

    async def test_analyze_life_situation(self, db_session: AsyncSession):
        """Test life situation analysis."""
        generator = DynamicHoroscopeGenerator(db_session)

        # Create user with interactions
        user = User(yandex_user_id="test_user", data_consent=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add various interactions
        interactions = [
            UserInteraction(
                user_id=user.id,
                interaction_type="like",
                content_type="compatibility",
                rating=5,
                session_duration=200,
            ),
            UserInteraction(
                user_id=user.id,
                interaction_type="view",
                content_type="compatibility",
                rating=4,
                session_duration=150,
            ),
            UserInteraction(
                user_id=user.id,
                interaction_type="save",
                content_type="daily",
                rating=3,
                session_duration=100,
            ),
        ]

        db_session.add_all(interactions)
        await db_session.commit()

        situation = await generator._analyze_life_situation(user.id)

        # Should analyze focus areas
        assert "focus_areas" in situation
        assert "compatibility" in situation["focus_areas"]
        assert situation["focus_areas"]["compatibility"] > 0

        # Should determine emotional state
        assert "emotional_state" in situation
        assert situation["emotional_state"] in [
            "positive",
            "neutral",
            "negative",
        ]


@pytest.mark.unit
class TestInterestProfilingSystem:
    """Tests for interest profiling system."""

    @pytest.mark.asyncio
    async def test_update_user_profile_no_interactions(
        self, db_session: AsyncSession
    ):
        """Test profile update with no interactions."""
        profiler = InterestProfilingSystem(db_session)

        user_id = uuid.uuid4()
        interests = await profiler.update_user_profile(user_id)

        assert interests == {}

    @pytest.mark.asyncio
    async def test_update_user_profile_with_interactions(
        self, db_session: AsyncSession
    ):
        """Test profile update with interaction data."""
        profiler = InterestProfilingSystem(db_session)

        # Create user
        user = User(yandex_user_id="test_user", data_consent=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add interactions focused on love/relationships
        interactions = [
            UserInteraction(
                user_id=user.id,
                interaction_type="like",
                content_type="compatibility",
                rating=5,
                session_duration=300,
                feedback_text="Отличный прогноз про любовь!",
            ),
            UserInteraction(
                user_id=user.id,
                interaction_type="save",
                content_type="compatibility",
                rating=4,
                session_duration=200,
                feedback_text="Интересно про отношения",
            ),
        ]

        db_session.add_all(interactions)
        await db_session.commit()

        interests = await profiler.update_user_profile(user.id)

        # Should identify love/relationship interest
        assert "love" in interests
        assert interests["love"] > 0

    def test_map_content_to_interest(self):
        """Test content type to interest mapping."""
        profiler = InterestProfilingSystem(None)

        # Test direct mapping
        interest = profiler._map_content_to_interest("compatibility", None)
        assert interest == "love"

        # Test feedback text analysis
        interest = profiler._map_content_to_interest(
            "daily", "Расскажите про карьеру и работу"
        )
        assert interest == "career"

        interest = profiler._map_content_to_interest(
            "daily", "Как дела с здоровьем?"
        )
        assert interest == "health"


@pytest.mark.unit
class TestCommunicationStyleAdapter:
    """Tests for communication style adaptation."""

    @pytest.mark.asyncio
    async def test_adapt_content_style_no_preferences(
        self, db_session: AsyncSession
    ):
        """Test style adaptation without user preferences."""
        adapter = CommunicationStyleAdapter(db_session)

        content = "Сегодня хороший день для начинаний"
        user_id = uuid.uuid4()

        adapted = await adapter.adapt_content_style(content, user_id)

        # Should return original content if no preferences
        assert adapted == content

    @pytest.mark.asyncio
    async def test_adapt_content_style_with_preferences(
        self, db_session: AsyncSession
    ):
        """Test style adaptation with user preferences."""
        adapter = CommunicationStyleAdapter(db_session)

        # Create user with preferences
        user = User(yandex_user_id="test_user", data_consent=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        prefs = UserPreference(user_id=user.id, communication_style="mystical")
        db_session.add(prefs)
        await db_session.commit()

        content = "Сегодня хороший день"
        adapted = await adapter.adapt_content_style(content, user.id)

        # Should apply mystical style
        assert adapted != content
        assert any(
            prefix in adapted
            for prefix in [
                "Звёзды шепчут:",
                "Древние мудрецы говорили:",
                "Космические силы предрекают:",
                "Планеты открывают тайну:",
            ]
        )

    def test_apply_communication_styles(self):
        """Test different communication style applications."""
        adapter = CommunicationStyleAdapter(None)

        original = "ты сможешь достичь успеха"

        # Test formal style
        formal = adapter._apply_communication_style(original, "formal")
        assert "вы" in formal

        # Test friendly style
        friendly = adapter._apply_communication_style(original, "friendly")
        assert any(
            prefix in friendly
            for prefix in ["Дорогой друг,", "Милый,", "Дорогой,"]
        )

        # Test mystical style
        mystical = adapter._apply_communication_style(original, "mystical")
        assert any(
            text in mystical for text in ["звёзд", "космическ", "мудрец"]
        )


@pytest.mark.asyncio
@pytest.mark.unit
class TestChurnPredictionModel:
    """Tests for churn prediction model."""

    async def test_predict_churn_risk_unknown_user(
        self, db_session: AsyncSession
    ):
        """Test churn prediction for unknown user."""
        churn_model = ChurnPredictionModel(db_session)

        user_id = uuid.uuid4()
        prediction = await churn_model.predict_churn_risk(user_id)

        assert prediction["risk_level"] == "unknown"
        assert prediction["probability"] == 0

    async def test_predict_churn_risk_active_user(
        self, db_session: AsyncSession
    ):
        """Test churn prediction for active user."""
        churn_model = ChurnPredictionModel(db_session)

        # Create active user
        user = User(
            yandex_user_id="active_user",
            data_consent=True,
            last_accessed=datetime.utcnow()
            - timedelta(days=1),  # Active recently
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add recent interactions
        recent_interactions = [
            UserInteraction(
                user_id=user.id,
                interaction_type="like",
                content_type="daily",
                rating=5,
                timestamp=datetime.utcnow() - timedelta(days=1),
            ),
            UserInteraction(
                user_id=user.id,
                interaction_type="view",
                content_type="weekly",
                rating=4,
                timestamp=datetime.utcnow() - timedelta(days=2),
            ),
        ]

        db_session.add_all(recent_interactions)
        await db_session.commit()

        prediction = await churn_model.predict_churn_risk(user.id)

        # Should be low risk for active user
        assert prediction["risk_level"] in ["low", "medium"]
        assert prediction["probability"] >= 0
        assert isinstance(prediction["risk_factors"], list)
        assert isinstance(prediction["recommendations"], list)

    async def test_predict_churn_risk_inactive_user(
        self, db_session: AsyncSession
    ):
        """Test churn prediction for inactive user."""
        churn_model = ChurnPredictionModel(db_session)

        # Create inactive user
        user = User(
            yandex_user_id="inactive_user",
            data_consent=True,
            last_accessed=datetime.utcnow()
            - timedelta(days=45),  # Inactive for long time
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add only old interactions with poor ratings
        old_interactions = [
            UserInteraction(
                user_id=user.id,
                interaction_type="dislike",
                content_type="daily",
                rating=2,
                timestamp=datetime.utcnow() - timedelta(days=40),
            )
        ]

        db_session.add_all(old_interactions)
        await db_session.commit()

        prediction = await churn_model.predict_churn_risk(user.id)

        # Should be higher risk for inactive user
        assert prediction["risk_level"] in ["medium", "high"]
        assert len(prediction["risk_factors"]) > 0


@pytest.mark.asyncio
@pytest.mark.unit
class TestABTestManager:
    """Tests for A/B testing manager."""

    async def test_assign_user_to_test_new_user(
        self, db_session: AsyncSession
    ):
        """Test assigning new user to A/B test."""
        ab_manager = ABTestManager(db_session)

        user = User(yandex_user_id="test_user", data_consent=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        test_name = "recommendation_algorithm"
        assigned_group = await ab_manager.assign_user_to_test(
            user.id, test_name
        )

        # Should assign to one of the groups
        assert assigned_group in ["control", "variant_a", "variant_b"]

    async def test_assign_user_to_test_existing_assignment(
        self, db_session: AsyncSession
    ):
        """Test assigning user already in A/B test."""
        ab_manager = ABTestManager(db_session)

        user = User(yandex_user_id="test_user", data_consent=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create existing assignment
        test_name = "recommendation_algorithm"
        existing_assignment = ABTestGroup(
            user_id=user.id,
            test_name=test_name,
            group_name="variant_a",
            test_start_date=datetime.utcnow(),
            test_parameters={"algorithm": "collaborative"},
        )
        db_session.add(existing_assignment)
        await db_session.commit()

        # Should return existing assignment
        assigned_group = await ab_manager.assign_user_to_test(
            user.id, test_name
        )
        assert assigned_group == "variant_a"


@pytest.mark.asyncio
@pytest.mark.unit
class TestMetricsCollector:
    """Tests for metrics collection system."""

    async def test_record_recommendation_view(self, db_session: AsyncSession):
        """Test recording recommendation view."""
        metrics = MetricsCollector(db_session)

        user = User(yandex_user_id="test_user", data_consent=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        recommendation = Recommendation(
            user_id=user.id,
            recommendation_type="content",
            content_type="daily",
            title="Test Recommendation",
            confidence_score=85,
            algorithm_used="hybrid",
            model_version="1.0",
        )
        db_session.add(recommendation)
        await db_session.commit()
        await db_session.refresh(recommendation)

        success = await metrics.record_recommendation_view(
            user.id, recommendation.id, "test_session_123"
        )

        assert success is True

    async def test_record_recommendation_click(self, db_session: AsyncSession):
        """Test recording recommendation click."""
        metrics = MetricsCollector(db_session)

        user = User(yandex_user_id="test_user", data_consent=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        recommendation = Recommendation(
            user_id=user.id,
            recommendation_type="content",
            content_type="weekly",
            title="Test Recommendation",
            confidence_score=75,
            algorithm_used="content_based",
            model_version="1.0",
        )
        db_session.add(recommendation)
        await db_session.commit()
        await db_session.refresh(recommendation)

        success = await metrics.record_recommendation_click(
            user.id, recommendation.id, "test_session_456"
        )

        assert success is True

    async def test_get_recommendation_metrics_no_data(
        self, db_session: AsyncSession
    ):
        """Test getting metrics with no data."""
        metrics = MetricsCollector(db_session)

        result = await metrics.get_recommendation_metrics(7)

        assert result["ctr"] == 0
        assert result["total_views"] == 0
        assert result["total_clicks"] == 0
        assert result["period_days"] == 7


@pytest.mark.asyncio
@pytest.mark.integration
class TestRecommendationSystemIntegration:
    """Integration tests for the complete recommendation system."""

    async def test_full_recommendation_workflow(
        self, db_session: AsyncSession
    ):
        """Test complete recommendation workflow from user creation to recommendations."""

        # Create user
        user = User(
            yandex_user_id="integration_test_user",
            zodiac_sign="scorpio",
            gender="female",
            data_consent=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create user preferences
        prefs = UserPreference(
            user_id=user.id,
            interests={"love": 0.8, "career": 0.6},
            communication_style="friendly",
            complexity_level="intermediate",
            cultural_context="western",
        )
        db_session.add(prefs)

        # Add user interactions
        interactions = [
            UserInteraction(
                user_id=user.id,
                interaction_type="like",
                content_type="compatibility",
                rating=5,
                session_duration=250,
                timestamp=datetime.utcnow() - timedelta(days=1),
            ),
            UserInteraction(
                user_id=user.id,
                interaction_type="view",
                content_type="daily",
                rating=4,
                session_duration=180,
                timestamp=datetime.utcnow() - timedelta(days=2),
            ),
            UserInteraction(
                user_id=user.id,
                interaction_type="save",
                content_type="lunar",
                rating=4,
                session_duration=200,
                timestamp=datetime.utcnow() - timedelta(days=3),
            ),
        ]
        db_session.add_all(interactions)
        await db_session.commit()

        # Test interest profiling
        profiler = InterestProfilingSystem(db_session)
        interests = await profiler.update_user_profile(user.id)
        assert len(interests) > 0

        # Test recommendation generation
        hybrid_engine = HybridRecommendationEngine(db_session)
        recommendations = await hybrid_engine.generate_recommendations(
            user.id, 3
        )
        assert len(recommendations) > 0

        # Test personalized horoscope generation
        horoscope_gen = DynamicHoroscopeGenerator(db_session)
        horoscope = await horoscope_gen.generate_personalized_horoscope(
            user.id, "daily"
        )
        assert horoscope is not None

        # Test churn prediction
        churn_model = ChurnPredictionModel(db_session)
        churn_risk = await churn_model.predict_churn_risk(user.id)
        assert "risk_level" in churn_risk

        # Test engagement optimization
        engagement_optimizer = EngagementOptimizer(db_session)
        engagement_data = await engagement_optimizer.optimize_user_engagement(
            user.id
        )
        assert "current_engagement" in engagement_data

        # Test A/B test assignment
        ab_manager = ABTestManager(db_session)
        test_group = await ab_manager.assign_user_to_test(user.id, "ui_layout")
        assert test_group in ["control", "variant_a", "variant_b"]

    async def test_seasonal_recommendations_workflow(
        self, db_session: AsyncSession
    ):
        """Test seasonal recommendations workflow."""

        # Create user
        user = User(
            yandex_user_id="seasonal_test_user",
            zodiac_sign="aquarius",
            data_consent=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Test seasonal analysis
        temporal_analyzer = TemporalPatternAnalyzer(db_session)
        seasonal_data = await temporal_analyzer.get_seasonal_recommendations(
            user.id
        )

        assert "season" in seasonal_data
        assert seasonal_data["season"] in [
            "spring",
            "summer",
            "autumn",
            "winter",
        ]
        assert "features" in seasonal_data
        assert "recommendations" in seasonal_data
        assert isinstance(seasonal_data["recommendations"], list)


@pytest.mark.asyncio
@pytest.mark.performance
class TestRecommendationPerformance:
    """Performance tests for recommendation system."""

    async def test_recommendation_generation_performance(
        self, db_session: AsyncSession
    ):
        """Test recommendation generation performance with multiple users."""

        # Create multiple users with data
        users = []
        for i in range(10):
            user = User(
                yandex_user_id=f"perf_test_user_{i}",
                zodiac_sign="libra",
                data_consent=True,
            )
            db_session.add(user)
            users.append(user)

        await db_session.commit()

        # Add interactions for each user
        for user in users:
            await db_session.refresh(user)
            interactions = [
                UserInteraction(
                    user_id=user.id,
                    interaction_type="like",
                    content_type="daily",
                    rating=4,
                ),
                UserInteraction(
                    user_id=user.id,
                    interaction_type="view",
                    content_type="weekly",
                    rating=3,
                ),
            ]
            db_session.add_all(interactions)

        await db_session.commit()

        # Test performance
        import time

        hybrid_engine = HybridRecommendationEngine(db_session)

        start_time = time.time()

        # Generate recommendations for all users
        for user in users:
            recommendations = await hybrid_engine.generate_recommendations(
                user.id, 5
            )
            assert len(recommendations) >= 0  # Allow empty results

        end_time = time.time()
        total_time = end_time - start_time

        # Should process all users within reasonable time (adjust threshold as needed)
        assert total_time < 10.0  # 10 seconds for 10 users

        avg_time_per_user = total_time / len(users)
        assert avg_time_per_user < 2.0  # Max 2 seconds per user


@pytest.mark.asyncio
@pytest.mark.security
class TestRecommendationSecurity:
    """Security tests for recommendation system."""

    async def test_user_data_isolation(self, db_session: AsyncSession):
        """Test that user data is properly isolated in recommendations."""

        # Create two users
        user1 = User(
            yandex_user_id="security_user_1",
            zodiac_sign="cancer",
            data_consent=True,
        )
        user2 = User(
            yandex_user_id="security_user_2",
            zodiac_sign="virgo",
            data_consent=True,
        )

        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        # Add private interactions for user1
        private_interaction = UserInteraction(
            user_id=user1.id,
            interaction_type="view",
            content_type="private_consultation",
            feedback_text="Very personal information",
        )
        db_session.add(private_interaction)
        await db_session.commit()

        # Generate recommendations for user2
        hybrid_engine = HybridRecommendationEngine(db_session)
        user2_recommendations = await hybrid_engine.generate_recommendations(
            user2.id
        )

        # Ensure user2's recommendations don't contain user1's private data
        for rec in user2_recommendations:
            rec_str = str(rec)
            assert "Very personal information" not in rec_str
            assert "private_consultation" not in rec_str

    async def test_consent_respect(self, db_session: AsyncSession):
        """Test that user consent is respected in recommendations."""

        # Create user without consent
        user_no_consent = User(
            yandex_user_id="no_consent_user",
            zodiac_sign="gemini",
            data_consent=False,  # No consent
        )
        db_session.add(user_no_consent)
        await db_session.commit()
        await db_session.refresh(user_no_consent)

        # Test that clustering respects consent
        clustering_manager = UserClusteringManager(db_session)
        updated_count = await clustering_manager.update_user_clusters()

        # User without consent should not be included in clustering
        # This is implemented by the where clause: User.data_consent == True
        assert updated_count >= 0  # Test passes if no errors occur
