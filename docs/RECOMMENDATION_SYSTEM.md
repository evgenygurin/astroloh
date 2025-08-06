# Recommendation and Personalization System

This document describes the comprehensive recommendation and personalization system implemented in Astroloh.

## Overview

The recommendation system provides personalized astrological content to users based on their preferences, behavior, and astrological profile. It combines multiple approaches including collaborative filtering, content-based filtering, machine learning, and temporal analysis.

## Architecture

### Core Components

1. **Recommendation Engine** (`app/services/recommendation_engine.py`)
   - Collaborative Filtering
   - Content-Based Filtering  
   - Hybrid Recommendation Engine
   - Temporal Pattern Analysis
   - User Clustering
   - A/B Testing Framework
   - Metrics Collection

2. **Personalization Service** (`app/services/personalization_service.py`)
   - Dynamic Horoscope Generation
   - Interest Profiling System
   - Communication Style Adaptation
   - Complexity Level Adjustment
   - Cultural Sensitivity Management

3. **ML Analytics Service** (`app/services/ml_analytics_service.py`)
   - Preference Learning Engine
   - Churn Prediction Model
   - Engagement Optimization
   - Anomaly Detection System

4. **API Layer** (`app/api/recommendations.py`)
   - REST endpoints for recommendations
   - User analytics endpoints
   - A/B testing endpoints
   - Metrics collection endpoints

### Database Models

New models added to `app/models/database.py`:

- `UserPreference` - User preferences and settings
- `UserInteraction` - User behavior and interaction history
- `Recommendation` - Generated recommendations
- `UserCluster` - User clustering for collaborative filtering
- `ABTestGroup` - A/B test assignments
- `RecommendationMetrics` - Performance metrics

## Features

### 1. Collaborative Filtering

Finds users with similar astrological profiles and preferences to generate recommendations.

**Algorithm:**
- Analyzes zodiac signs, gender, preferences, and interaction patterns
- Calculates user similarity scores
- Recommends content liked by similar users

**Usage:**
```python
from app.services.recommendation_engine import CollaborativeFiltering

collaborative = CollaborativeFiltering(db_session)
similar_users = await collaborative.find_similar_users(user_id, limit=10)
```

### 2. Content-Based Filtering

Generates recommendations based on user's astrological characteristics and current celestial conditions.

**Features:**
- Analyzes current transits and planetary positions
- Considers user's birth chart
- Adapts to interests (career, love, health, etc.)
- Seasonal astological adaptation

**Usage:**
```python
from app.services.recommendation_engine import ContentBasedFiltering

content_filter = ContentBasedFiltering(db_session)
recommendations = await content_filter.get_content_recommendations(user_id)
```

### 3. Hybrid Approach

Combines collaborative and content-based filtering with temporal patterns for optimal results.

**Algorithm:**
- Content-based recommendations: 60% weight
- Collaborative filtering: 40% weight
- Temporal pattern adjustments
- Personalization overlay

**Usage:**
```python
from app.services.recommendation_engine import HybridRecommendationEngine

hybrid = HybridRecommendationEngine(db_session)
recommendations = await hybrid.generate_recommendations(user_id, limit=5)
```

### 4. Dynamic Horoscope Generation

Creates personalized horoscopes adapted to user's current life situation.

**Features:**
- Analyzes recent user interactions to understand life focus
- Adapts content tone based on emotional state
- Applies communication style preferences
- Adjusts complexity level and cultural context

**Usage:**
```python
from app.services.personalization_service import DynamicHoroscopeGenerator

generator = DynamicHoroscopeGenerator(db_session)
horoscope = await generator.generate_personalized_horoscope(user_id, "daily")
```

### 5. Interest Profiling

Learns user interests from behavior patterns.

**Tracked Interests:**
- Career and professional life
- Love and relationships
- Health and wellness
- Finances
- Spirituality and personal growth
- Family matters

**Usage:**
```python
from app.services.personalization_service import InterestProfilingSystem

profiler = InterestProfilingSystem(db_session)
interests = await profiler.update_user_profile(user_id)
```

### 6. Communication Style Adaptation

Adapts content to match user's preferred communication style.

**Available Styles:**
- **Formal** - Professional, respectful tone
- **Casual** - Relaxed, informal approach
- **Friendly** - Warm, personal communication
- **Mystical** - Esoteric, spiritual language
- **Balanced** - Default neutral style

**Usage:**
```python
from app.services.personalization_service import CommunicationStyleAdapter

adapter = CommunicationStyleAdapter(db_session)
adapted_content = await adapter.adapt_content_style(content, user_id)
```

### 7. Complexity Level Adjustment

Adjusts content complexity based on user's astrological knowledge level.

**Levels:**
- **Beginner** - Simple language, basic concepts, explanations included
- **Intermediate** - Standard astrological terms, moderate detail
- **Advanced** - Technical terms, detailed analysis, historical context

**Usage:**
```python
from app.services.personalization_service import ComplexityLevelAdjuster

adjuster = ComplexityLevelAdjuster(db_session)
adjusted_content = await adjuster.adjust_content_complexity(content, user_id)
```

### 8. Cultural Sensitivity

Adapts content for different astrological traditions.

**Supported Contexts:**
- **Western** - Tropical zodiac, Western astrology (default)
- **Vedic** - Sidereal zodiac, Indian astrology concepts
- **Chinese** - Chinese zodiac, elements, Yin/Yang principles

**Usage:**
```python
from app.services.personalization_service import CulturalSensitivityManager

cultural_mgr = CulturalSensitivityManager(db_session)
adapted_content = await cultural_mgr.adapt_cultural_context(content, user_id)
```

### 9. Machine Learning Components

#### Preference Learning
Automatically learns user preferences from behavior.

```python
from app.services.ml_analytics_service import PreferenceLearningEngine

learning_engine = PreferenceLearningEngine(db_session)
preferences = await learning_engine.learn_user_preferences(user_id)
```

#### Churn Prediction
Predicts user churn risk with explanations.

**Risk Factors:**
- Days since last access
- Recent activity levels
- Activity trends
- Satisfaction scores
- Feature usage diversity

```python
from app.services.ml_analytics_service import ChurnPredictionModel

churn_model = ChurnPredictionModel(db_session)
risk_assessment = await churn_model.predict_churn_risk(user_id)
```

#### Engagement Optimization
Provides strategies to improve user engagement.

```python
from app.services.ml_analytics_service import EngagementOptimizer

optimizer = EngagementOptimizer(db_session)
optimization = await optimizer.optimize_user_engagement(user_id)
```

#### Anomaly Detection
Detects unusual patterns in user behavior.

**Detected Anomalies:**
- Unusually high/low activity
- Activity gaps
- Satisfaction drops
- Content fixation
- Preference abandonment

```python
from app.services.ml_analytics_service import AnomalyDetectionSystem

detector = AnomalyDetectionSystem(db_session)
anomalies = await detector.detect_anomalies(user_id)
```

### 10. Seasonal Adaptation

Adapts recommendations based on astrological seasons and current planetary conditions.

**Features:**
- Determines current astrological season
- Analyzes dominant elements and aspects
- Identifies retrograde planets
- Provides season-specific recommendations

**Usage:**
```python
from app.services.recommendation_engine import TemporalPatternAnalyzer

analyzer = TemporalPatternAnalyzer(db_session)
seasonal_recs = await analyzer.get_seasonal_recommendations(user_id)
```

### 11. A/B Testing Framework

Enables testing different recommendation algorithms and UI variations.

**Test Types:**
- Recommendation algorithms (collaborative vs content-based vs hybrid)
- UI layouts and designs
- Content variations
- Personalization depth levels

**Usage:**
```python
from app.services.recommendation_engine import ABTestManager

ab_manager = ABTestManager(db_session)
assigned_group = await ab_manager.assign_user_to_test(user_id, "algorithm_test")
```

### 12. Metrics Collection

Comprehensive metrics for monitoring and optimization.

**Tracked Metrics:**
- Click-through rates (CTR)
- Conversion rates
- User satisfaction scores
- Session duration
- Feature usage
- Recommendation effectiveness

**Usage:**
```python
from app.services.recommendation_engine import MetricsCollector

metrics = MetricsCollector(db_session)
await metrics.record_recommendation_view(user_id, recommendation_id)
await metrics.record_recommendation_click(user_id, recommendation_id)
performance = await metrics.get_recommendation_metrics(period_days=7)
```

## API Endpoints

### User Recommendations

```http
GET /api/v1/recommendations/user/{user_id}
```

Returns personalized recommendations for a user.

**Parameters:**
- `user_id` (string): Yandex user ID
- `limit` (int): Maximum number of recommendations (1-20, default: 5)

**Response:**
```json
[
  {
    "content_type": "daily",
    "confidence_score": 85,
    "algorithm": "hybrid",
    "data": {
      "focus_areas": ["career", "love"],
      "timing": "today"
    },
    "personalization": {
      "communication_style": "friendly",
      "complexity_level": "intermediate"
    }
  }
]
```

### Personalized Horoscope

```http
GET /api/v1/recommendations/user/{user_id}/horoscope
```

Generates a personalized horoscope.

**Parameters:**
- `user_id` (string): Yandex user ID
- `horoscope_type` (string): Type of horoscope ("daily", "weekly", "monthly")

**Response:**
```json
{
  "content": "Дорогой друг, сегодня звёзды благоприятствуют новым начинаниям...",
  "horoscope_type": "daily",
  "personalization_applied": [
    "communication_style",
    "complexity_level", 
    "cultural_context",
    "life_situation"
  ],
  "complexity_level": "intermediate",
  "cultural_context": "western"
}
```

### User Analytics

```http
GET /api/v1/recommendations/user/{user_id}/analytics
```

Returns user analytics for personalization.

**Response:**
```json
{
  "engagement_level": "high",
  "churn_risk": "low",
  "interests": {
    "career": 0.8,
    "love": 0.6,
    "health": 0.4
  },
  "recommendations_count": 5
}
```

### Seasonal Recommendations

```http
GET /api/v1/recommendations/user/{user_id}/seasonal
```

Returns seasonal astrological recommendations.

**Response:**
```json
{
  "season": "spring",
  "features": {
    "dominant_elements": ["fire", "earth"],
    "major_aspects": ["conjunction", "trine"]
  },
  "recommendations": [
    {
      "type": "growth_focus",
      "title": "Время новых начинаний",
      "description": "Весенняя энергия благоприятствует новым проектам"
    }
  ]
}
```

### A/B Testing

```http
POST /api/v1/recommendations/ab-test/{user_id}/{test_name}
```

Assigns user to A/B test group.

**Response:**
```json
{
  "test_name": "recommendation_algorithm",
  "assigned_group": "variant_a",
  "test_parameters": {
    "algorithm": "collaborative",
    "weight": 1.0
  }
}
```

### Record User Interaction

```http
POST /api/v1/recommendations/user/{user_id}/interaction
```

Records user interaction for learning.

**Request Body:**
```json
{
  "type": "recommendation_click",
  "recommendation_id": "uuid",
  "session_id": "session_123"
}
```

### System Metrics

```http
GET /api/v1/recommendations/metrics
```

Returns system-wide recommendation metrics.

**Parameters:**
- `period_days` (int): Analysis period in days (1-30, default: 7)

**Response:**
```json
{
  "status": "success",
  "metrics": {
    "ctr": 0.15,
    "total_views": 1200,
    "total_clicks": 180,
    "period_days": 7
  }
}
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Recommendation System Settings
RECOMMENDATION_DEFAULT_ALGORITHM=hybrid
RECOMMENDATION_CACHE_TTL=3600
RECOMMENDATION_MAX_PER_USER=20

# A/B Testing
AB_TEST_ENABLED=true
AB_TEST_DEFAULT_SPLIT=33

# ML Settings  
ML_MODEL_UPDATE_INTERVAL=24
ML_CLUSTERING_MIN_USERS=10
ML_CHURN_PREDICTION_THRESHOLD=0.7

# Metrics Collection
METRICS_ENABLED=true
METRICS_RETENTION_DAYS=90
```

### Database Migrations

Run database migrations to create new tables:

```bash
alembic revision --autogenerate -m "Add recommendation system tables"
alembic upgrade head
```

## Performance Considerations

### Caching

- Recommendations are cached for 1 hour by default
- User profiles are cached after updates
- Seasonal data is cached daily

### Database Optimization

- Proper indexing on user_id, timestamp columns
- Partitioning for large metrics tables
- Regular cleanup of old interaction data

### Scalability

- Asynchronous processing for all operations
- Background tasks for ML model updates
- Horizontal scaling support with session affinity

## Security and Privacy

### Data Protection

- All personal data encrypted at rest
- GDPR compliance with data retention policies
- User consent required for profiling
- Data anonymization for analytics

### Access Control

- User data isolation enforced at database level
- API authentication required
- Rate limiting on recommendation endpoints
- Audit logging for sensitive operations

## Monitoring and Metrics

### Key Performance Indicators

1. **Recommendation Quality**
   - Click-through rate (CTR)
   - Conversion rate
   - User satisfaction scores
   - Recommendation diversity

2. **User Engagement**
   - Session duration
   - Return rate
   - Feature adoption
   - Churn rate

3. **System Performance**
   - Response times
   - Cache hit rates
   - Error rates
   - Resource utilization

### Alerting

Set up alerts for:
- CTR drops below threshold (< 10%)
- High churn risk user count increases
- System errors in recommendation generation
- Performance degradation

## Development and Testing

### Running Tests

```bash
# Unit tests
pytest tests/test_recommendation_system.py -m unit

# Integration tests
pytest tests/test_recommendation_system.py -m integration

# Performance tests
pytest tests/test_recommendation_system.py -m performance

# Security tests
pytest tests/test_recommendation_system.py -m security
```

### Local Development

1. Set up development database
2. Run migrations
3. Create test users with sample data
4. Test API endpoints with Postman/curl
5. Monitor logs for debugging

### Code Quality

- Type hints enforced with mypy
- Code formatting with black
- Security scanning with bandit
- Test coverage minimum 80%

## Future Enhancements

### Planned Features

1. **Advanced ML Models**
   - Deep learning for complex patterns
   - Natural language processing for feedback analysis
   - Reinforcement learning for optimization

2. **Real-time Features**
   - Live astronomical event alerts
   - Push notifications for optimal timing
   - Real-time recommendation updates

3. **Social Features**
   - Community recommendations
   - Friend compatibility analysis
   - Shared reading experiences

4. **Enhanced Personalization**
   - Voice tone adaptation
   - Multi-language support
   - Accessibility features

### Technical Improvements

1. **Performance**
   - GraphQL API for efficient data fetching
   - Edge caching for global users
   - Machine learning pipeline optimization

2. **Analytics**
   - Advanced user journey analysis
   - Cohort analysis
   - Attribution modeling

3. **Platform**
   - Mobile app integration
   - Web dashboard for users
   - Third-party integrations

## Troubleshooting

### Common Issues

1. **Recommendations Not Generated**
   - Check user consent settings
   - Verify database connectivity
   - Review error logs for ML service issues

2. **Poor Recommendation Quality**
   - Insufficient user interaction data
   - Model needs retraining
   - A/B test different algorithms

3. **Performance Issues**
   - Check database query performance
   - Monitor cache hit rates
   - Scale recommendation service instances

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('app.services.recommendation_engine').setLevel(logging.DEBUG)
```

### Health Checks

Monitor system health:

```http
GET /api/v1/recommendations/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "recommendation_system",
  "components": {
    "recommendation_engine": "ok",
    "personalization_service": "ok",
    "ml_analytics": "ok",
    "metrics_collector": "ok",
    "ab_testing": "ok"
  }
}
```