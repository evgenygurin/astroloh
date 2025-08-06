# Astroloh Recommendation & Personalization System

## Overview

The Astroloh recommendation and personalization system provides intelligent content recommendations and user experience adaptation for astrological services. The system implements state-of-the-art machine learning algorithms to deliver personalized horoscopes, recommendations, and user engagement optimization.

## Architecture

### Core Components

1. **Recommendation Engine** (`app/services/recommendation_engine.py`)
   - **Collaborative Filtering**: Recommends content based on similar users' preferences
   - **Content-Based Filtering**: Recommends content based on user's interest profile
   - **Hybrid Approach**: Combines collaborative and content-based methods
   - **Temporal Pattern Analysis**: Analyzes user behavior patterns over time
   - **Seasonal Adaptation**: Adapts recommendations based on astrological cycles

2. **Personalization Service** (`app/services/personalization_service.py`)
   - Dynamic content adaptation based on user preferences
   - Communication style adaptation (formal, casual, balanced)
   - Cultural sensitivity and localization
   - Interest profiling and learning from user interactions

3. **ML Analytics** (`app/services/ml_analytics.py`)
   - **User Clustering**: Segments users based on astrological and behavioral patterns
   - **Churn Prediction**: Identifies users at risk of disengagement
   - **Engagement Optimization**: Optimizes content timing and delivery
   - **Anomaly Detection**: Detects unusual user behavior patterns

4. **A/B Testing Framework** (`app/services/ab_testing_service.py`)
   - Experimentation platform for testing recommendation algorithms
   - Statistical analysis and performance tracking
   - Automated user assignment and traffic splitting

5. **Database Models** (`app/models/recommendation_models.py`)
   - Comprehensive data models for storing user preferences, interactions, and recommendations
   - Support for A/B testing, metrics collection, and personalization data

## Key Features

### Recommendation Algorithms

#### Collaborative Filtering
- Calculates user similarity based on:
  - Interest preferences (career, love, health, finance, family, spiritual)
  - Behavioral patterns (interaction frequency, session duration)
  - Astrological compatibility (zodiac signs, elements, modalities)
- Recommends content liked by similar users
- Handles cold start problems with hybrid approaches

#### Content-Based Filtering
- Analyzes content characteristics:
  - Astrological relevance (zodiac signs, planets, aspects)
  - Content categories and tags
  - Quality metrics (popularity, engagement, feedback scores)
  - Temporal relevance and seasonal appropriateness
- Matches content to user interest profiles

#### Hybrid Recommendations
- Combines collaborative and content-based scores with configurable weights
- Applies diversity filtering to ensure variety
- Includes explanation generation for recommendation transparency

### Personalization Features

#### Dynamic Content Adaptation
- **Communication Style**: Formal, casual, or balanced tone adaptation
- **Complexity Level**: Beginner, intermediate, or advanced astrological content
- **Content Length**: Short, medium, or long format preferences
- **Emotional Tone**: Positive, neutral, or realistic outlook
- **Cultural Context**: Localized content and cultural sensitivity

#### User Interest Profiling
- Automatic learning from user interactions
- Real-time preference updates based on feedback
- Interest scoring across six main categories
- Trending interest analysis across user base

### Machine Learning Analytics

#### User Clustering
- K-means clustering based on behavioral and preference features
- Automatic optimal cluster number detection using elbow method
- Cluster characterization and naming based on dominant interests
- Feature importance analysis for understanding user segments

#### Churn Prediction
- Rule-based churn risk scoring with following factors:
  - Days since last activity
  - Interaction frequency trends
  - User satisfaction scores
  - Session quality metrics
- Risk level classification (high, medium, low, very low)
- Automated intervention strategy suggestions

#### Engagement Optimization
- Temporal pattern analysis for optimal content delivery timing
- Personalized frequency recommendations
- Engagement score calculation based on multiple factors
- Content type preference analysis

### A/B Testing Framework

#### Test Management
- Create multi-group experiments with configurable traffic allocation
- Consistent user assignment using deterministic hashing
- Automatic test duration management
- Statistical significance testing

#### Metrics Collection
- Key Performance Indicators (KPIs) tracking:
  - Click-through rates (CTR)
  - Conversion rates
  - User satisfaction scores
  - Engagement metrics
  - Retention rates
- Real-time dashboard with health scoring
- Historical trend analysis

## API Endpoints

### Recommendation Endpoints
- `GET /api/v1/recommendations/users/{user_id}/recommendations` - Get personalized recommendations
- `GET /api/v1/recommendations/users/{user_id}/preferences` - Get user preferences
- `PUT /api/v1/recommendations/users/{user_id}/preferences` - Update user preferences
- `POST /api/v1/recommendations/users/{user_id}/interactions` - Track user interactions
- `POST /api/v1/recommendations/users/{user_id}/horoscope/personalize` - Personalize horoscope content

### Analytics Endpoints
- `GET /api/v1/recommendations/users/{user_id}/analytics/cluster` - Get user cluster info
- `GET /api/v1/recommendations/users/{user_id}/analytics/churn-risk` - Get churn prediction
- `GET /api/v1/recommendations/users/{user_id}/analytics/engagement` - Get engagement analysis
- `GET /api/v1/recommendations/users/{user_id}/analytics/anomalies` - Detect behavioral anomalies

### A/B Testing Endpoints
- `POST /api/v1/recommendations/ab-tests` - Create A/B test
- `GET /api/v1/recommendations/ab-tests` - List active tests
- `GET /api/v1/recommendations/ab-tests/{test_name}/results` - Get test results
- `DELETE /api/v1/recommendations/ab-tests/{test_name}` - End A/B test

### System Analytics
- `GET /api/v1/recommendations/metrics/dashboard` - System KPI dashboard
- `GET /api/v1/recommendations/analytics/clustering/perform` - Run user clustering
- `GET /api/v1/recommendations/analytics/churn/at-risk` - Get at-risk users
- `GET /api/v1/recommendations/interests/trending` - Get trending interests

## Database Schema

### User Preferences (`user_preferences`)
- Interest scores for different categories
- Communication and content preferences
- Cultural and localization settings
- Personalization feature flags

### User Interactions (`user_interactions`)
- Detailed interaction tracking
- Engagement metrics and feedback
- Temporal context data
- Content category and type information

### Recommendation Items (`recommendation_items`)
- Content metadata and categorization
- Astrological relevance data
- Quality and performance metrics
- Temporal and seasonal relevance

### A/B Testing (`ab_test_groups`, `user_ab_test_assignments`)
- Test configuration and group definitions
- User assignments and traffic allocation
- Statistical tracking and analysis

## Security and Privacy

### Data Protection
- Integration with existing encryption service
- GDPR compliance for user data
- Anonymized analytics and clustering
- Secure storage of sensitive preference data

### User Consent
- Explicit consent for personalization features
- Granular privacy controls
- Data retention and deletion support
- Transparent data usage policies

## Performance Considerations

### Scalability
- Efficient database queries with proper indexing
- Batch processing for large-scale analytics
- Caching strategies for frequently accessed data
- Asynchronous processing for ML operations

### Optimization
- Lazy loading of complex recommendation algorithms
- Pre-computed similarity matrices for collaborative filtering
- Efficient vector operations using NumPy
- Database query optimization and connection pooling

## Usage Examples

### Basic Recommendation Generation
```python
from app.services.recommendation_engine import HybridRecommendationEngine

async def get_recommendations(db_session, user_id):
    engine = HybridRecommendationEngine(db_session)
    recommendations = await engine.generate_hybrid_recommendations(
        user_id, limit=10, include_reasoning=True
    )
    return recommendations
```

### Personalization
```python
from app.services.personalization_service import PersonalizationService

async def personalize_content(db_session, user_id, content):
    service = PersonalizationService(db_session)
    settings = await service.get_personalized_content_settings(user_id)
    personalized = await service.adapt_communication_style(user_id, content)
    return personalized
```

### A/B Testing
```python
from app.services.ab_testing_service import ABTestingService

async def setup_ab_test(db_session):
    service = ABTestingService(db_session)
    
    test_groups = [
        {
            'group_name': 'control',
            'traffic_percentage': 0.5,
            'algorithm_config': {'type': 'current', 'version': '1.0'}
        },
        {
            'group_name': 'variant',
            'traffic_percentage': 0.5,
            'algorithm_config': {'type': 'new', 'version': '2.0'}
        }
    ]
    
    result = await service.create_ab_test(
        "recommendation_algorithm_test",
        test_groups,
        duration_days=14
    )
    return result
```

## Testing

The system includes comprehensive unit and integration tests covering:
- All recommendation algorithms
- Personalization features
- ML analytics components
- A/B testing functionality
- API endpoint validation
- Database model relationships

Run tests with:
```bash
pytest tests/test_recommendation_system.py -v
```

## Future Enhancements

### Planned Features
1. **Deep Learning Models**: Neural collaborative filtering and content embeddings
2. **Real-time Recommendations**: Streaming recommendation updates
3. **Multi-armed Bandits**: Dynamic exploration-exploitation for recommendations
4. **Graph Neural Networks**: Social network analysis for collaborative filtering
5. **Reinforcement Learning**: Adaptive recommendation strategy learning
6. **Advanced Seasonality**: Integration with precise astrological calculations
7. **Cross-platform Sync**: Unified recommendations across Alice, Telegram, and Google Assistant

### Technical Improvements
1. **Distributed Computing**: Spark integration for large-scale ML processing
2. **Model Serving**: TensorFlow Serving or MLflow integration
3. **Feature Store**: Centralized feature management system
4. **Real-time Analytics**: Stream processing with Apache Kafka
5. **Advanced Monitoring**: MLOps pipeline with model performance tracking

## Configuration

### Environment Variables
- `RECOMMENDATION_COLLABORATIVE_WEIGHT`: Weight for collaborative filtering (default: 0.6)
- `RECOMMENDATION_CONTENT_WEIGHT`: Weight for content-based filtering (default: 0.4)
- `RECOMMENDATION_DIVERSITY_FACTOR`: Diversity bonus factor (default: 0.3)
- `CHURN_THRESHOLD_DAYS`: Days without activity for churn classification (default: 30)
- `MIN_INTERACTIONS_SIMILARITY`: Minimum interactions for similarity calculation (default: 5)

### Algorithm Parameters
All recommendation algorithms support configurable parameters for fine-tuning:
- Similarity thresholds
- Learning rates for preference updates
- Clustering parameters
- A/B test traffic allocation
- Metrics calculation windows

This comprehensive recommendation system provides Astroloh with advanced personalization capabilities while maintaining security, performance, and user privacy standards.