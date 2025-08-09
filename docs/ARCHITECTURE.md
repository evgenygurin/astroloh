# System Architecture

- Backend: FastAPI (`app/main.py`) exposing unified API + Yandex Dialogs webhook.
- Services: astrology, natal chart, dialog handling, caching, personalization.
- Data: PostgreSQL (async), Redis cache.
- Integrations: Yandex Dialogs webhook (`/api/v1/yandex/webhook`), Telegram/Google (later).
- Frontend: React + TS.

Key Modules:
- `app/services/dialog_handler.py`: orchestration for intents and responses.
- `app/api/astrology.py`: REST endpoints for natal/horoscope/compatibility.
- `app/core/config.py`: settings and env.

Non-Goals for MVP: IoT, complex ML analytics.

Diagrams: see `docs/SYSTEM_MAP.md`.

## Overview

Astroloh is a sophisticated multi-platform astrological assistant built using modern microservices architecture principles. The system provides voice-enabled astrological consultations across Yandex Alice, Telegram Bot, Google Assistant, and IoT Smart Home devices.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client Layer                                │
├─────────────────┬─────────────────┬─────────────────┬────────────────┤
│   Yandex Alice  │   Telegram Bot  │ Google Assistant│ IoT Smart Home │
└─────────────────┴─────────────────┴─────────────────┴────────────────┘
           │                 │                 │                │
           ▼                 ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                           │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────────┐  │
│  │ Yandex  │Telegram │ Google  │   IoT   │  Auth   │ Astrology   │  │
│  │ Router  │ Router  │ Router  │ Router  │ Router  │   Router    │  │
│  └─────────┴─────────┴─────────┴─────────┴─────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Business Logic Layer                         │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                    Core Services                                │ │
│ │ • Dialog Handler     • Intent Recognition  • Session Manager   │ │
│ │ • Response Formatter • Conversation Manager • Error Handler     │ │
│ │ • Multi-Platform Handler • Dialog Flow Manager                 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                  Astrological Services                          │ │
│ │ • Astrology Calculator    • Kerykeion Service                   │ │
│ │ • Enhanced Transit Service • Progression Service               │ │  
│ │ • Natal Chart Calculator  • Synastry Service                   │ │
│ │ • Horoscope Generator     • Compatibility Analyzer             │ │
│ │ • Lunar Calendar          • Russian Astrology Adapter          │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                    AI & ML Services                             │ │
│ │ • Astro AI Service      • AI Content Filter                    │ │
│ │ • AI Horoscope Service  • ML Analytics Service                 │ │
│ │ • Recommendation Engine • Personalization Service              │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                Performance & Infrastructure                     │ │
│ │ • Astro Cache Service    • Async Kerykeion Service             │ │
│ │ • Performance Monitor    • Precompute Service                  │ │
│ │ • Startup Manager        • Cache Service                       │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                 │
│ ┌─────────────┬─────────────┬─────────────┬─────────────────────── ┐ │
│ │ PostgreSQL  │    Redis    │  External   │     File System        │ │
│ │ Database    │   Cache     │    APIs     │   (Ephemeris Data)     │ │
│ │             │             │             │                        │ │
│ │ • Users     │ • Sessions  │ • Yandex    │ • Swiss Ephemeris      │ │
│ │ • Sessions  │ • Ephemeris │   GPT API   │ • Timezone Data        │ │
│ │ • Requests  │ • Horoscopes│ • Astro APIs│ • Configuration Files  │ │
│ │ • Analytics │ • Transits  │             │                        │ │
│ └─────────────┴─────────────┴─────────────┴─────────────────────── ┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend Framework
- **FastAPI**: Modern, high-performance Python web framework
- **Python 3.11**: Latest stable Python with performance optimizations
- **Uvicorn**: Lightning-fast ASGI server with async support
- **Pydantic**: Data validation and serialization with type hints

### Database Layer
- **PostgreSQL 15**: Primary database with advanced JSON support
- **SQLAlchemy 2.0**: Modern ORM with async support
- **Alembic**: Database migration management
- **asyncpg**: High-performance async PostgreSQL driver

### Caching & Performance
- **Redis 7**: Primary caching layer with intelligent TTL policies
- **Custom Cache Service**: Multi-level caching with fallback strategies
- **Async Kerykeion Service**: Thread pool for CPU-intensive calculations
- **Performance Monitor**: Real-time metrics and alerting

### Astronomical Calculations
- **Kerykeion ≥4.11.0**: Primary professional astrology library
- **pyswisseph**: High-precision ephemeris calculations (fallback)
- **Skyfield**: Pure Python astronomical library (fallback)
- **Astropy**: Professional astronomy calculations (fallback)

### External Integrations
- **Yandex GPT API**: AI-powered astrological consultations
- **Yandex Dialogs Platform**: Voice interface for Alice
- **Telegram Bot API**: Messaging platform integration
- **Google Actions**: Google Assistant integration

### Security & Compliance
- **Encryption Service**: AES-256 for sensitive user data
- **GDPR Compliance Module**: Data retention and deletion
- **Security Headers Middleware**: Comprehensive security policies
- **Rate Limiting**: slowapi-based request throttling

## Service Architecture Details

### Core Services Layer

#### Dialog Handler (`dialog_handler.py`)
Central orchestrator for all user interactions across platforms.

**Key Features**:
- 23 intent handlers covering all astrological consultations
- Context-aware conversation management
- Multi-platform response formatting
- Error recovery and graceful degradation
- Session state management with PostgreSQL persistence

**Intent Processing Pipeline**:
```
User Input → Intent Recognition → Entity Extraction → Context Loading → 
Service Selection → Response Generation → Platform Formatting → Response
```

#### Intent Recognition Service (`intent_recognition.py`)
Advanced NLP engine for understanding user requests in multiple languages.

**Capabilities**:
- 60+ voice command patterns in Russian
- Entity extraction (zodiac signs, dates, names, locations)
- Sentiment analysis and mood detection
- Caching with MD5-based keys (1000 item limit)
- Voice preprocessing for common speech recognition errors

**Supported Entities**:
- Zodiac signs with full Russian declensions
- Dates in multiple formats (DD.MM.YYYY, relative dates)
- Time expressions (HH:MM, natural language)
- Astrological periods (daily, weekly, monthly)
- Sentiment classification (positive, negative, neutral)

#### Session Manager (`session_manager.py`)
Sophisticated session management with Alice voice interface compliance.

**Features**:
- User context persistence across conversations
- Conversation flow tracking with message counting
- Session timeout detection (10-minute Alice limit)
- Awaiting data state management for multi-turn conversations
- Session analytics for compliance monitoring

### Astrological Services Layer

#### Enhanced Transit Service (`enhanced_transit_service.py`)
Professional-grade astrological transit analysis using Kerykeion.

**Advanced Features**:
- TransitsTimeRangeFactory integration for professional calculations
- Support for all 11 major and minor aspects with configurable orbs
- Period forecasts (7, 30, or custom day periods)
- Important transit detection from slow-moving planets
- Energy pattern analysis with daily guidance
- Timing recommendations for various life activities

**Performance Optimizations**:
- Full async integration with proper error handling
- Intelligent caching strategies per operation type
- Batch processing for multi-day forecasts
- Performance monitoring integration

#### Kerykeion Service (`kerykeion_service.py`)
Advanced interface to the professional Kerykeion astrology library.

**Professional Features**:
- Complete natal chart calculation including Chiron, Lilith, Lunar Nodes
- 11 aspect types with color coding and strength ratings
- Multiple house systems (Placidus, Koch, Equal, Whole Sign, etc.)
- Tropical and Sidereal zodiac support
- Arabic Parts calculation (Fortune, Spirit, Love, Marriage, Career)
- SVG chart generation with customizable themes
- Advanced synastry and compatibility analysis

#### Russian Localization Service (`russian_astrology_adapter.py`)
Comprehensive Russian localization for native Yandex Alice experience.

**Localization Features**:
- Complete Russian terminology for planets, signs, houses, aspects
- All 6 Russian grammatical cases (nominative, genitive, dative, accusative, instrumental, prepositional)
- Support for all 11 Russian time zones with automatic city detection
- Voice optimization with proper stress marks for TTS
- Cultural adaptation of astrological interpretations

### AI & Machine Learning Layer

#### Astro AI Service (`astro_ai_service.py`)
Advanced AI consultation platform combining Kerykeion with Yandex GPT.

**AI Capabilities**:
- Professional natal chart interpretation with full Kerykeion integration
- Specialized consultations (career, love, health, financial, spiritual)
- Enhanced compatibility analysis with AI insights
- Transit-based forecasting with timing recommendations
- Content safety filtering with multi-level validation

#### AI Content Filter (`ai_content_filter.py`)
Comprehensive content validation and safety system.

**Safety Features**:
- Harmful content detection and removal
- Medical advice filtering
- Financial advice risk assessment
- Quality assessment for astrological relevance
- Automatic disclaimers based on consultation type
- Alice voice interface compliance (character limits)

#### Recommendation Engine (`recommendation_engine.py`)
ML-powered personalization system for astrological content.

**ML Algorithms**:
- Collaborative filtering based on user behavior
- Content-based recommendations using astrological features
- Hybrid approaches combining multiple signals
- A/B testing framework for optimization
- User clustering for improved targeting

### Performance & Infrastructure Layer

#### Astro Cache Service (`astro_cache_service.py`)
Sophisticated caching system optimized for astrological data patterns.

**Caching Strategy**:
- Redis primary cache with in-memory fallback
- Data-type specific TTL policies:
  - Natal charts: 30 days (permanent birth data)
  - Ephemeris data: 6 hours (daily positions)
  - Current transits: 1 hour (real-time)
  - Period forecasts: 2 hours (weekly/monthly)
  - Compatibility: 7 days (relationship analysis)

**Performance Features**:
- Built-in hit rate monitoring
- Response time tracking
- Intelligent cleanup with LRU eviction
- Memory usage optimization
- Automatic Redis connectivity detection

#### Performance Monitor (`performance_monitor.py`)
Real-time system monitoring with alerting capabilities.

**Monitoring Features**:
- Operation tracking with P50, P95, P99 percentiles
- Memory and CPU usage per operation
- Configurable alert thresholds:
  - Slow operations: >2000ms
  - High memory usage: >500MB
  - High CPU usage: >80%
- Background metrics collection every 30 seconds
- Human-readable performance reports

#### Startup Manager (`startup_manager.py`)
Orchestrated system initialization with health diagnostics.

**Initialization Features**:
- Sequential service startup with dependency management
- Cache warmup with critical data pre-population
- Comprehensive health diagnostics
- Graceful shutdown with proper cleanup
- System status monitoring and reporting

## Data Architecture

### Database Schema Overview

#### User Management Tables
- **users**: Encrypted personal data with GDPR compliance
- **user_sessions**: Dialog state management
- **user_preferences**: Personalization settings
- **user_interactions**: Behavior tracking for ML

#### Astrological Data Tables
- **horoscope_requests**: Request history with encrypted parameters
- **recommendations**: Personalized content suggestions
- **user_clusters**: ML-based user grouping
- **ab_test_groups**: A/B testing assignments

#### System Tables
- **data_deletion_requests**: GDPR deletion workflow
- **security_logs**: Audit trail for compliance
- **recommendation_metrics**: Performance tracking

#### Encryption Strategy
- **AES-256** encryption for all sensitive personal data
- **Separate encryption keys** for different data types
- **Encrypted fields**: birth_date, birth_time, birth_location, name, partner_data
- **Hashed fields**: IP addresses, user agents for analytics
- **Clear fields**: zodiac_sign, gender, preferences (non-sensitive)

### Caching Architecture

#### Multi-Level Caching Strategy

```
Request → L1 Cache (Redis) → L2 Cache (Memory) → Database/Calculation
                ↓                    ↓                    ↓
            60-80% hit         15-20% hit         5-20% miss
             <100ms            <200ms             >1000ms
```

#### Cache Hierarchy
1. **Redis (Primary)**: Distributed cache for scalability
2. **In-Memory (Fallback)**: Local cache for high availability
3. **Database (Persistent)**: PostgreSQL with JSON for complex queries
4. **External APIs (Source)**: Yandex GPT, astronomical services

#### Intelligent TTL Policies
- **Static Data**: 30 days (birth charts, user profiles)
- **Semi-Dynamic**: 6 hours (daily ephemeris, transits)
- **Dynamic**: 1 hour (current positions, real-time data)
- **Session Data**: 10 minutes (Alice compliance)

## Multi-Backend Astronomical System

### Library Priority System
1. **Kerykeion** (Primary): Professional astrology with full features
2. **Swiss Ephemeris** (Fallback): High-precision calculations
3. **Skyfield** (Fallback): Pure Python alternative
4. **Built-in Algorithms** (Emergency): Basic calculations

### Graceful Degradation Strategy
```python
try:
    # Professional calculation with Kerykeion
    result = await kerykeion_service.calculate_natal_chart(params)
    if result.get("source") == "kerykeion":
        return enhanced_response(result)
except KerykeionUnavailable:
    # Fallback to Swiss Ephemeris
    result = await swiss_ephemeris.calculate_natal_chart(params)
    return standard_response(result)
except SwissEphemerisUnavailable:
    # Final fallback to basic calculations
    result = basic_calculator.calculate_natal_chart(params)
    return basic_response(result)
```

## Voice Interface Architecture

### Alice Voice Optimization
- **Response Time**: <3 seconds for Alice compliance
- **Character Limits**: 800 characters for detailed responses
- **Button Limits**: Maximum 5 buttons per response
- **TTS Optimization**: Automatic pause insertion, emoji removal
- **Russian Language**: Native support with proper declensions

### Multi-Platform Response Formatting
```python
class ResponseFormatter:
    def format_for_platform(self, content, platform):
        if platform == "yandex_alice":
            return self.format_alice_response(content)
        elif platform == "telegram":
            return self.format_telegram_response(content)
        elif platform == "google":
            return self.format_google_response(content)
        elif platform == "iot":
            return self.format_iot_response(content)
```

## Security Architecture

### Data Protection
- **Encryption at Rest**: AES-256 for PostgreSQL
- **Encryption in Transit**: TLS 1.3 for all communications
- **Key Management**: Environment-based key rotation
- **GDPR Compliance**: Automated data retention and deletion

### API Security
- **Rate Limiting**: slowapi with Redis backend
- **Security Headers**: Comprehensive CSP, HSTS, etc.
- **Input Validation**: Pydantic with custom validators
- **Error Handling**: No sensitive data in error messages

### Audit and Compliance
- **Security Logs**: All access attempts and data operations
- **Request Correlation**: UUID tracking across services
- **Performance Monitoring**: Suspicious activity detection
- **GDPR Workflows**: Automated compliance procedures

## Deployment Architecture

### Container Infrastructure
```yaml
Services:
  - backend: FastAPI application (port 8000)
  - frontend: React/TypeScript (port 80)
  - database: PostgreSQL 15 (port 5432)
  - cache: Redis 7 (port 6379)
  - ngrok: Development tunneling (ports 4040-4041)

Networks:
  - astroloh-network: Internal bridge network

Volumes:
  - postgres_data: Database persistence
  - redis_data: Cache persistence
```

### Environment Configuration
- **Development**: Full debugging, hot reload, docs enabled
- **Staging**: Production-like with monitoring
- **Production**: Optimized, secure, monitoring enabled

### Scaling Considerations
- **Horizontal Scaling**: FastAPI supports multiple workers
- **Database Scaling**: PostgreSQL read replicas
- **Cache Scaling**: Redis clustering
- **Background Tasks**: Celery integration ready

## Monitoring and Observability

### Performance Metrics
- **Response Times**: P50, P95, P99 tracking
- **Cache Hit Rates**: Per-service monitoring
- **Error Rates**: Automated alerting
- **Resource Usage**: Memory, CPU, disk monitoring

### Business Metrics
- **User Engagement**: Session duration, interaction frequency
- **Feature Usage**: Intent popularity, platform distribution
- **AI Performance**: Quality ratings, user satisfaction
- **Astrological Accuracy**: User feedback integration

### Logging Strategy
- **Structured Logging**: JSON format with correlation IDs
- **Service-Level Patterns**: `SERVICE_OPERATION_STAGE` format
- **Log Aggregation**: Centralized logging with search
- **Alert Integration**: Critical error notifications

## Future Architecture Evolution

### Planned Enhancements
- **Microservices Migration**: Service decomposition
- **Event-Driven Architecture**: Message queuing with Redis Streams
- **GraphQL API**: Flexible client-server communication
- **WebSocket Support**: Real-time astrological events
- **Mobile SDK**: Native iOS/Android libraries

### Scalability Roadmap
- **Kubernetes Deployment**: Container orchestration
- **Database Sharding**: User-based data distribution
- **CDN Integration**: Global content delivery
- **Edge Computing**: Reduced latency for calculations
- **ML Model Serving**: Dedicated inference infrastructure

This architecture supports the current multi-platform requirements while providing a foundation for future growth and feature expansion.

