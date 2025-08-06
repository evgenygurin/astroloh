"""
Database models for recommendation and personalization system.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.database import Base, GUID


class UserPreference(Base):
    """
    User preferences and personalization settings.
    """

    __tablename__ = "user_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Interest categories (0.0-1.0 scores)
    career_interest = Column(Float, default=0.5, nullable=False)
    love_interest = Column(Float, default=0.5, nullable=False)
    health_interest = Column(Float, default=0.5, nullable=False)
    finance_interest = Column(Float, default=0.5, nullable=False)
    family_interest = Column(Float, default=0.5, nullable=False)
    spiritual_interest = Column(Float, default=0.5, nullable=False)

    # Communication style preferences
    communication_style = Column(
        String(20), default="balanced", nullable=False
    )  # formal, casual, balanced
    complexity_level = Column(
        String(20), default="intermediate", nullable=False
    )  # beginner, intermediate, advanced
    
    # Content preferences
    preferred_length = Column(
        String(20), default="medium", nullable=False
    )  # short, medium, long
    emotional_tone = Column(
        String(20), default="neutral", nullable=False
    )  # positive, neutral, realistic
    
    # Cultural settings
    cultural_context = Column(String(50), nullable=True)  # Cultural background
    timezone = Column(String(50), nullable=True)
    language_preference = Column(String(10), default="ru", nullable=False)

    # Engagement patterns
    preferred_time_slot = Column(
        String(20), nullable=True
    )  # morning, afternoon, evening, night
    optimal_frequency = Column(Integer, default=1, nullable=False)  # Days between messages
    
    # Personalization flags
    use_name_in_responses = Column(Boolean, default=False, nullable=False)
    include_lucky_numbers = Column(Boolean, default=True, nullable=False)
    include_lucky_colors = Column(Boolean, default=True, nullable=False)
    include_compatibility_hints = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="preference")


class UserInteraction(Base):
    """
    User interaction tracking for learning preferences.
    """

    __tablename__ = "user_interactions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Interaction details
    interaction_type = Column(
        String(50), nullable=False
    )  # request, feedback, rating, share, save
    content_category = Column(String(50), nullable=True)  # horoscope, compatibility, etc.
    content_id = Column(String(100), nullable=True)  # Reference to specific content

    # Engagement metrics
    session_duration = Column(Integer, nullable=True)  # Seconds
    response_rating = Column(Float, nullable=True)  # 1.0-5.0 rating
    feedback_text = Column(Text, nullable=True)

    # Context data
    time_of_day = Column(String(20), nullable=True)  # morning, afternoon, evening, night
    day_of_week = Column(String(10), nullable=True)
    context_data = Column(JSON, nullable=True)  # Additional context as JSON

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_hash = Column(String(64), nullable=True)  # Hashed IP for analytics

    # Relationships
    user = relationship("User", backref="interactions")


class RecommendationItem(Base):
    """
    Items that can be recommended to users.
    """

    __tablename__ = "recommendation_items"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Item identification
    item_type = Column(
        String(50), nullable=False
    )  # horoscope, compatibility, lunar, transit
    item_category = Column(String(50), nullable=True)  # daily, weekly, monthly, etc.
    item_identifier = Column(String(200), nullable=False)  # Unique identifier

    # Content metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags for content-based filtering

    # Astrological metadata
    zodiac_signs = Column(JSON, nullable=True)  # Relevant zodiac signs
    planets = Column(JSON, nullable=True)  # Relevant planets
    aspects = Column(JSON, nullable=True)  # Relevant aspects
    houses = Column(JSON, nullable=True)  # Relevant houses

    # Quality metrics
    popularity_score = Column(Float, default=0.0, nullable=False)
    engagement_score = Column(Float, default=0.0, nullable=False)
    feedback_score = Column(Float, default=0.0, nullable=False)

    # Temporal relevance
    seasonal_relevance = Column(JSON, nullable=True)  # Relevance by season
    time_sensitivity = Column(Boolean, default=False, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("item_type", "item_identifier", name="uq_item_type_identifier"),
    )


class UserRecommendation(Base):
    """
    Generated recommendations for users.
    """

    __tablename__ = "user_recommendations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    item_id = Column(GUID(), ForeignKey("recommendation_items.id"), nullable=False)

    # Recommendation scoring
    relevance_score = Column(Float, nullable=False)  # 0.0-1.0
    confidence_score = Column(Float, nullable=False)  # 0.0-1.0
    priority_score = Column(Float, nullable=False)  # 0.0-1.0

    # Algorithm attribution
    algorithm_used = Column(
        String(50), nullable=False
    )  # collaborative, content_based, hybrid
    algorithm_version = Column(String(20), default="1.0", nullable=False)

    # Recommendation context
    recommendation_reason = Column(Text, nullable=True)
    context_factors = Column(JSON, nullable=True)  # Factors that influenced recommendation

    # Engagement tracking
    presented_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    feedback_given = Column(Boolean, default=False, nullable=False)
    user_rating = Column(Float, nullable=True)  # User's rating if provided

    # Status
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, presented, clicked, dismissed
    expires_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
    item = relationship("RecommendationItem")

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uq_user_item_recommendation"),
    )


class UserSimilarity(Base):
    """
    User similarity scores for collaborative filtering.
    """

    __tablename__ = "user_similarities"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id_1 = Column(GUID(), ForeignKey("users.id"), nullable=False)
    user_id_2 = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Similarity scores
    overall_similarity = Column(Float, nullable=False)  # 0.0-1.0
    preference_similarity = Column(Float, nullable=True)
    behavior_similarity = Column(Float, nullable=True)
    astrological_similarity = Column(Float, nullable=True)

    # Calculation metadata
    calculation_method = Column(String(50), nullable=False)
    calculation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_points_used = Column(Integer, nullable=False)

    # Relationships
    user1 = relationship("User", foreign_keys=[user_id_1])
    user2 = relationship("User", foreign_keys=[user_id_2])

    __table_args__ = (
        UniqueConstraint("user_id_1", "user_id_2", name="uq_user_similarity_pair"),
    )


class ABTestGroup(Base):
    """
    A/B testing groups for recommendation experiments.
    """

    __tablename__ = "ab_test_groups"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Test configuration
    test_name = Column(String(100), nullable=False)
    group_name = Column(String(50), nullable=False)  # control, variant_a, variant_b, etc.
    description = Column(Text, nullable=True)

    # Algorithm configuration
    algorithm_config = Column(JSON, nullable=False)  # Configuration parameters
    
    # Test parameters
    traffic_percentage = Column(Float, nullable=False)  # 0.0-1.0
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Test duration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("test_name", "group_name", name="uq_test_group"),
    )


class UserABTestAssignment(Base):
    """
    User assignments to A/B test groups.
    """

    __tablename__ = "user_ab_test_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    test_group_id = Column(GUID(), ForeignKey("ab_test_groups.id"), nullable=False)

    # Assignment details
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assignment_method = Column(String(50), default="random", nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User")
    test_group = relationship("ABTestGroup")

    __table_args__ = (
        UniqueConstraint("user_id", "test_group_id", name="uq_user_test_assignment"),
    )


class RecommendationMetrics(Base):
    """
    Metrics tracking for recommendation system performance.
    """

    __tablename__ = "recommendation_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Metric identification
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(
        String(50), nullable=False
    )  # ctr, engagement, conversion, satisfaction
    
    # Aggregation details
    aggregation_period = Column(
        String(20), nullable=False
    )  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Metric values
    metric_value = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=True)
    confidence_interval = Column(JSON, nullable=True)  # [lower, upper] bounds

    # Segmentation
    user_segment = Column(String(50), nullable=True)  # new, returning, premium, etc.
    algorithm_version = Column(String(20), nullable=True)
    test_group = Column(String(50), nullable=True)

    # Context
    additional_data = Column(JSON, nullable=True)

    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "metric_name", "aggregation_period", "period_start", "user_segment",
            name="uq_metric_period_segment"
        ),
    )