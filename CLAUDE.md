# Claude Development Guidelines

This file contains guidelines and instructions for Claude AI when working with the Astroloh project.

## Project Overview

Astroloh is a voice skill for Yandex Alice that provides personalized astrological forecasts and consultations. The project is built with Python 3.11, FastAPI, PostgreSQL, and integrates with Swiss Ephemeris for astronomical calculations.

## Development Environment Setup

### Installation

For development work, use the appropriate installation command based on your system:

**Linux/Windows (full installation):**

```bash
pip install -e ".[full,dev]"
```

**macOS (without C library compilation):**

```bash
pip install -e ".[macos,dev]"
```

**Minimal installation:**

```bash
pip install -e ".[minimal,dev]"
```

### Running the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Code Quality and Testing

### Formatting

Always run code formatting before committing:

```bash
black app/ tests/
isort app/ tests/
```

### Linting

Run linting to ensure code quality:

```bash
flake8 app/ tests/
mypy app/
```

### Testing

Run the full test suite:

```bash
pytest
```

The project maintains 80% test coverage minimum. Tests are organized by categories:

- Unit tests: `pytest -m unit`
- Integration tests: `pytest -m integration`
- Performance tests: `pytest -m performance`
- Security tests: `pytest -m security`

## Project Structure

```
astroloh/
├── app/                    # Main application code
│   ├── api/               # API routers (Yandex Dialogs integration)
│   ├── core/              # Configuration and settings
│   ├── models/            # Data models
│   ├── services/          # Business logic (astrology, lunar calendar, etc.)
│   ├── utils/             # Utilities
│   └── main.py           # FastAPI entry point
├── tests/                 # Test suite
├── docs/                  # Documentation
├── migrations/            # Database migrations
└── docker-compose.yml    # Docker configuration
```

## Key Services

- **astrology_calculator.py**: Core astrological calculations with multi-backend support
- **kerykeion_service.py**: ⭐ **NEW** - Advanced Kerykeion-based astrological service with full professional features
- **enhanced_transit_service.py**: ⭐ **NEW** - Professional transit analysis with Kerykeion TransitsTimeRangeFactory integration
- **progression_service.py**: ⭐ **NEW** - Secondary progressions, solar/lunar returns, and temporal astrology techniques
- **transit_calculator.py**: Enhanced with new transit services integration and comprehensive analysis
- **astrology_calculator.py**: Core astrological calculations
- **synastry_service.py**: Synastry and relationship analysis using Kerykeion
- **compatibility_analyzer.py**: Advanced multi-type compatibility analysis
- **kerykeion_service.py**: Advanced Kerykeion-based astrological service with full professional features
- **natal_chart.py**: Enhanced birth chart calculations with Kerykeion integration
- **horoscope_generator.py**: Enhanced with transit integration for personalized forecasts
- **conversation_manager.py**: Dialog flow management
- **lunar_calendar.py**: Lunar calendar functionality
- **session_manager.py**: User session handling

## Security Considerations

- Personal data is encrypted (encryption.py)
- GDPR compliance implemented (gdpr_compliance.py)
- Input validation through validators.py
- Security tests are mandatory for sensitive areas

## Astronomical Libraries

The project supports multiple astronomical calculation libraries with automatic fallbacks and priority system:

- **pyswisseph**: Primary library (high accuracy, requires C compilation)
- **skyfield**: Alternative (good accuracy, pure Python)
- **astropy**: Professional astronomy (full-featured)
- **Kerykeion**: Modern astrology library for synastry and advanced calculations

## Synastry and Compatibility Analysis (NEW 2025-01-08)

The project now includes comprehensive synastry and relationship analysis capabilities:

### Core Features

- **Synastry Service** (`synastry_service.py`): Full relationship analysis using Kerykeion
  - Inter-chart aspects calculation
  - Composite midpoints
  - House overlays
  - Relationship themes and growth potential

- **Compatibility Analyzer** (`compatibility_analyzer.py`): Multi-type compatibility analysis
  - Romantic relationships
  - Business partnerships  
  - Friendships
  - Family dynamics

### Voice Interface Integration

The synastry functionality is fully integrated with Yandex Alice:

- **Intent Recognition**: `YandexIntent.SYNASTRY` with partner name extraction
- **Dialog Flow**: Multi-step data collection for partner information
- **Session Management**: Partner data stored in `UserContext`
- **Response Formatting**: Beautiful, voice-optimized synastry reports

### Usage Patterns

```python
# Voice commands supported:
"Синастрия с Марией"
"Анализ отношений"
"Совместимость с Иваном" 
"Что говорят звезды о наших отношениях"
"Композитная карта"
```

### Data Collection Flow

1. User zodiac sign (if not already known)
2. Partner name extraction from voice input
3. Partner zodiac sign
4. Optional: Partner birth date for enhanced analysis
5. Generate comprehensive compatibility report

1. **Kerykeion** >=4.11.0: **PRIMARY** library for professional astrology (highest priority)
   - Complete natal chart calculation with all planets including Chiron, Lilith, Lunar Nodes
   - Advanced aspect calculation with color coding and configurable orbs
   - Multiple house systems support (Placidus, Koch, Equal, Whole Sign, etc.)
   - Tropical and Sidereal zodiac types
   - Synastry (chart compatibility) calculations
   - Transits and progressions
   - SVG chart generation
   - Arabic Parts (Lots) calculation
   - Comprehensive astrological analysis and interpretations

2. **pyswisseph**: High accuracy library (requires C compilation, fallback)
3. **skyfield**: Good accuracy, pure Python (fallback)
4. **astropy**: Professional astronomy (full-featured, fallback)

**Priority System**: Kerykeion → Swiss Ephemeris → Skyfield → Built-in algorithms

## API Integration

- Main webhook: `POST /api/v1/yandex/webhook`
- Health check: `GET /health`
- API documentation available at `/docs`

## Development Workflow

1. Always run formatting and linting before commits
2. Ensure tests pass with minimum 80% coverage
3. Follow existing code patterns and service architecture
4. Use type hints consistently (mypy enforced)
5. Handle errors gracefully with proper logging (loguru)

## Database

- Uses PostgreSQL with SQLAlchemy 2.0
- Migrations managed with Alembic
- Async operations with asyncpg

## Deployment

- Docker-based deployment with docker-compose
- Environment variables configured via .env
- CI/CD pipeline enforces quality checks

When making changes, always consider the astrological domain context and maintain the existing service-oriented architecture.

## Enhanced Kerykeion Integration (Updated 2025-01-08)

### New KerykeionService Features

**Complete Professional Astrology Support:**

- **Enhanced Natal Charts**: Full planet calculation including Chiron, Lilith (Mean Apogee), True/Mean Nodes
- **Advanced Aspects**: 11 aspect types with color coding, configurable orbs, and strength ratings
- **Multiple House Systems**: Placidus, Koch, Equal, Whole Sign, Regiomontanus, Campanus, etc.
- **Zodiac Types**: Both Tropical and Sidereal zodiac calculations with automatic conversion
- **Arabic Parts**: Extended calculation of Lots including Fortune, Spirit, Love, Marriage, Career
- **Chart Analysis**: Automatic shape detection, element/quality distribution, dominant planets
- **SVG Generation**: Professional chart rendering with customizable themes
- **Detailed Compatibility**: Advanced synastry calculations with relationship advice

### Enhanced NatalChartCalculator Methods

**New calculate_enhanced_natal_chart() method:**
```python
calculate_enhanced_natal_chart(
    name="User Name",
    birth_date=date(1990, 8, 15),
    birth_time=time(14, 30),
    birth_place={"latitude": 55.7558, "longitude": 37.6176},
    timezone_str="Europe/Moscow",
    house_system="Placidus",  # or Koch, Equal, etc.
    zodiac_type="Tropical",   # or Sidereal
    include_arabic_parts=True,
    include_fixed_stars=True,
    generate_svg=False        # Set True for SVG chart generation
)
```

**Enhanced Interpretations:**
- Psychological analysis with dominant planet influences
- Life themes based on strong aspects
- Career guidance by MC sign
- Spiritual path analysis by element distribution
- Karmic indicators and growth patterns

### Backend Priority System

**Automatic Library Selection:**
1. **Kerykeion** (primary) - Full professional features
2. **Swiss Ephemeris** (fallback) - High precision calculations
3. **Skyfield** (fallback) - Pure Python alternative  
4. **Built-in** (fallback) - Basic calculations

**Graceful Degradation:** If Kerykeion is unavailable, the system automatically falls back to Swiss Ephemeris while maintaining API compatibility.

### Aspect Color Coding System

**Traditional Astrological Colors:**
- Conjunction: #FF0000 (Red)
- Opposition: #0000FF (Blue)
- Trine: #00FF00 (Green)
- Square: #FF8000 (Orange)
- Sextile: #8000FF (Purple)
- Minor aspects: Gray/Pink/Gold variations

### Development Best Practices

**When working with Kerykeion features:**
1. Always check `kerykeion_service.is_available()` before using advanced features
2. Implement graceful fallbacks to basic astrology_calculator methods
3. Use appropriate logging patterns: `KERYKEION_SERVICE_*` prefixes
4. Test both Kerykeion-available and fallback scenarios
5. Respect the multi-backend architecture for compatibility

**Error Handling:**
- KerykeionService methods return error dictionaries on failure
- Always check for "error" key in returned data
- Log both successes and failures with correlation IDs

### Configuration Requirements

**For full Kerykeion functionality, ensure:**
- Kerykeion >=4.11.0 is installed in the environment
- Proper timezone handling (uses pytz)
- Sufficient memory for complex chart calculations
- Optional: SVG rendering libraries for chart generation

## Critical Operational Knowledge (Updated 2025-01-08)

### Docker Environment Variable Issue (CRITICAL)

**Problem**: The most common deployment issue is Yandex GPT API returning 401 "Unknown api key" errors.

**Root Cause**: Docker containers don't automatically receive environment variables from .env files.

**Solution**: Environment variables must be explicitly mapped in docker-compose.yml:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql+asyncpg://astroloh_user:astroloh_password@db:5432/astroloh_db
      - YANDEX_API_KEY=${YANDEX_API_KEY}
      - YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
      - YANDEX_CATALOG_ID=${YANDEX_CATALOG_ID}
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
```

**Important**: After adding environment variables, containers require full restart:

```bash
docker-compose down && docker-compose up
```

### Comprehensive Logging Architecture (Updated 2025-01-08)

The application now implements systematic logging across **ALL** services with consistent patterns:

**Service-Level Logging Pattern**: `SERVICE_OPERATION_STAGE: contextual_information`

**Logging Levels**:

- **DEBUG**: Detailed flow tracking, calculations, cache operations, pattern matching
- **INFO**: Main operations, successful completions, key metrics, request starts/ends
- **WARNING**: Fallback scenarios, data not found cases, degraded functionality
- **ERROR**: Failures, exceptions, critical issues requiring attention

**Complete Logged Services** (Full Coverage):

- `yandex_dialogs.py`: Webhook entry with correlation IDs
- `dialog_handler.py`: All 13 intent handlers (START/CONTEXT/SUCCESS/ERROR)
- `intent_recognition.py`: Intent matching, entity extraction, cache tracking, voice preprocessing
- `response_formatter.py`: Response creation with metrics and mode detection
- `session_manager.py`: Session lifecycle, state management, conversation flow tracking
- `horoscope_generator.py`: Complete horoscope generation pipeline with step tracking
- `astrology_calculator.py`: Astronomical calculations with backend detection and fallbacks
- `yandex_gpt.py`: API requests with unique request IDs and configuration validation

**New Logging Patterns Added**:

- **Request Correlation**: Unique identifiers track requests across service boundaries
- **Backend Detection**: Astronomical library selection logging (SwissEph/Skyfield/Astropy)
- **Calculation Tracking**: Detailed logging of astrological calculations and energy levels
- **Session Analytics**: Conversation flow tracking for Alice compliance
- **Entity Extraction**: Detailed zodiac sign, date, and sentiment analysis logging
- **Fallback Logging**: Clear indication when fallback mechanisms activate

**Force Logging Requirement**: When debugging Yandex GPT issues, standard logging may be insufficient. Use "force logging" with emojis (🚀, ✅, ❌) and print statements to ensure visibility in container logs.

### Webhook Processing Flow (Complete)

```
POST /api/v1/yandex/webhook
├── yandex_dialogs.py (entry point, correlation ID generation)
├── intent_recognition.py (intent + entity extraction with caching)
├── dialog_handler.py (13 intent handlers with context management)
│   ├── handle_greet() - Welcome flow
│   ├── handle_horoscope() - Horoscope generation (traditional + AI)
│   ├── handle_compatibility() - Zodiac compatibility analysis
│   ├── handle_natal_chart() - Birth chart calculations
│   ├── handle_lunar_calendar() - Moon phase information
│   ├── handle_transits() - Current planetary influences
│   ├── handle_progressions() - Personal development analysis
│   ├── handle_solar_return() - Annual forecast
│   ├── handle_lunar_return() - Monthly forecast
│   ├── handle_advice() - Personalized recommendations
│   ├── handle_help() - Capability information
│   ├── handle_exit() - Session termination
│   └── handle_unknown() - Fallback handler
├── Service Layer (astrology calculations, AI generation)
├── response_formatter.py (Alice-compatible response formatting)
└── Return YandexResponseModel
```

### Yandex GPT Integration Architecture

**Service Flow**: `ai_horoscope_service.py` → `yandex_gpt.py`

**Configuration Dependencies**:

- `ENABLE_AI_GENERATION`: Feature flag controlling AI vs traditional horoscope
- `YANDEX_API_KEY`: Required for GPT API access
- `YANDEX_FOLDER_ID`: Yandex Cloud folder identifier
- `YANDEX_CATALOG_ID`: Optional catalog identifier (defaults to folder_id)

**Request Tracking**: Each GPT request gets unique ID: `ygpt_{timestamp}`

**Fallback Mechanism**:

1. Attempt AI generation via Yandex GPT
2. On failure, fallback to traditional horoscope generation
3. Always return response (never fail completely)

**Common Issues**:

- API key not properly set in environment
- Containers not restarted after environment changes
- Rate limiting or quota exceeded
- Network connectivity to Yandex Cloud

### Intent Recognition & Entity Extraction

**Supported Entities**:

- **Zodiac Signs**: All 12 signs with Russian declensions
- **Dates**: Multiple formats (DD.MM.YYYY, relative dates like "сегодня")
- **Times**: HH:MM format and natural language ("15 часов")
- **Periods**: daily, weekly, monthly, current
- **Sentiment**: positive, negative, neutral analysis

**Caching Strategy**: MD5-based caching for intent matching and entity extraction (limit: 1000 items)

**Voice Input Processing**: Special handling for common speech recognition errors in Russian

### Response Formatting for Alice

**Multi-Mode Support**:

- **Test Mode**: Dictionary input for testing
- **Production Mode**: Zodiac sign + data dictionary
- **Basic Mode**: Zodiac sign only with generated content

**TTS Processing**: Automatic emoji removal and pause insertion for voice output

**Button Limitations**: Maximum 5 buttons per response (Alice requirement)

### Astrological Services Architecture (Detailed)

**Multi-Backend Astronomical Calculations**:

- `astrology_calculator.py` supports SwissEph (primary), Skyfield, and Astropy with automatic fallback
- Backend selection logged at startup: "Using [backend] backend for astronomical calculations"
- Each backend handles different calculation types with different accuracy levels
- Fallback mechanisms ensure production reliability even with missing dependencies

**Horoscope Generation Pipeline**:

1. **Influence Calculation**: Moon phases, planetary hours, seasonal effects, simplified transits
2. **Spheres Forecast**: Love, career, health, finances with 1-5 star ratings
3. **Energy Level**: Calculated from moon phase, season, zodiac element (10-100%)
4. **Lucky Elements**: Numbers and colors based on sign characteristics and date
5. **Personalized Advice**: Generated from sign keywords and moon phase

**Compatibility Analysis**:

- Element compatibility matrix (fire/earth/air/water interactions)
- Quality compatibility (cardinal/fixed/mutable relationships)
- Combined scoring with percentage results and descriptive categories

### Alice Voice Interface Optimization

**Russian Language Processing**:

- Comprehensive zodiac sign patterns with all case declensions
- Voice preprocessing corrects common speech recognition errors:
  - "асталог" → "астролог"
  - "гороскоп ля льва" → "гороскоп для льва"
- Entity extraction handles relative dates ("сегодня", "завтра", "вчера")
- Sentiment analysis for user mood detection

**Response Formatting for Voice**:

- Character limits: horoscopes max 800 chars, compatibility max 600 chars
- TTS optimization: automatic pause insertion, emoji removal
- Button limits: maximum 5 buttons per response (Alice requirement)
- Multi-mode support: test/production/basic modes for different data sources

**Session Management for Alice**:

- Message counting for conversation flow tracking
- Conversation timeout detection (10 minutes for Alice compliance)
- Awaiting data state management for multi-turn conversations
- Session analytics for monitoring Alice interaction patterns

### Development Debugging Best Practices (Enhanced)

1. **Environment Variable Issues**: Always check docker logs first, then verify .env mapping
2. **AI Service Issues**: Use force logging with emojis to trace execution
3. **Intent Recognition Issues**: Check entity extraction logs for pattern matching
4. **Container Issues**: Full restart required after environment changes
5. **Log Analysis**: Correlation IDs help track requests across services
6. **Astrological Calculations**: Check backend selection and fallback activation
7. **Voice Interface**: Monitor TTS processing and Alice-specific constraints
8. **Session Debugging**: Track conversation states and timeout scenarios
9. **Performance Issues**: Review energy calculations and horoscope generation timing
10. **API Integration**: Monitor Yandex GPT request IDs and response processing

### Service Dependencies

**Critical Dependencies**:

- PostgreSQL database for user sessions and data persistence
- Yandex GPT API for AI-powered horoscope generation
- Swiss Ephemeris data for astronomical calculations (optional with fallbacks)

**Internal Service Dependencies**:

- `session_manager` ↔ `dialog_handler` (user context management)
- `intent_recognition` → `dialog_handler` (request routing)
- `dialog_handler` → `response_formatter` (response creation)
- `ai_horoscope_service` → `yandex_gpt` (AI generation)

### Testing Strategy Notes (Enhanced)

**Current State**: Some tests failing due to environment and dependency issues

**Integration Testing Approach**:

- Docker environment testing critical for production parity
- Full webhook flow testing from curl to response validation
- AI service testing requires real API keys or proper mocking
- Astronomical calculations testing across multiple backends
- Session management testing for Alice conversation flows

**Performance Requirements**:

- Response time critical for voice interface (Yandex Alice requirements)
- Horoscope generation should complete within 2-3 seconds
- Database queries optimized for session lookup performance
- Fallback mechanisms must activate quickly without user-visible delays

**Production Testing Commands**:

```bash
# Test horoscope generation
curl -X POST http://localhost:8000/api/v1/yandex/webhook \
  -H "Content-Type: application/json" \
  -d '{"request": {"command": "дай гороскоп для льва"}, "session": {"user_id": "test", "session_id": "test"}, "version": "1.0"}'

# Test compatibility
curl -X POST http://localhost:8000/api/v1/yandex/webhook \
  -H "Content-Type: application/json" \
  -d '{"request": {"command": "совместимость льва и овна"}, "session": {"user_id": "test", "session_id": "test"}, "version": "1.0"}'
```

### Production Monitoring and Maintenance

**Key Metrics to Monitor**:

- Yandex GPT API success/failure rates with 401 error tracking
- Astronomical calculation backend usage and fallback frequency
- Session management statistics (active sessions, timeouts, success rates)
- Response time distribution for voice interface compliance
- Intent recognition accuracy and unknown intent frequency

**Regular Maintenance Tasks**:

1. Monitor Docker container logs for environment variable issues
2. Check Yandex GPT quota usage and API key validity
3. Verify astronomical data backend availability
4. Review session analytics for Alice compliance patterns
5. Update voice preprocessing patterns based on recognition errors

**Critical Production Alerts**:

- Yandex GPT 401 errors (environment variable issue)
- High unknown intent rates (may indicate user pattern changes)
- Database connection failures affecting session management
- All astronomical backends failing (calculation fallback issues)
- Response time exceeding Alice voice interface limits

## Enhanced Transit and Progression System (Updated 2025-08-08)

### New Professional Transit Analysis

**Enhanced Transit Service** (`enhanced_transit_service.py`):
- **Kerykeion Integration**: Uses `TransitsTimeRangeFactory` and `EphemerisDataFactory` for professional-grade calculations
- **Comprehensive Aspect Analysis**: Supports all 11 major and minor aspects with configurable orbs
- **Period Forecasts**: Generates detailed forecasts for 7, 30, or custom day periods
- **Important Transits Detection**: Identifies life-changing transits from slow-moving planets (Jupiter, Saturn, Uranus, Neptune, Pluto)
- **Energy Pattern Analysis**: Assesses daily energy levels based on transit combinations
- **Timing Recommendations**: Provides optimal timing advice for various activities
- **Graceful Fallbacks**: Automatically falls back to basic calculations when Kerykeion unavailable

**Key Methods**:
```python
# Current transits with professional accuracy
get_current_transits(natal_chart, transit_date, include_minor_aspects=True)

# Period forecast with daily guidance
get_period_forecast(natal_chart, days=7, start_date=None)

# Major life transit analysis (90 days ahead, 30 days back)
get_important_transits(natal_chart, lookback_days=30, lookahead_days=90)
```

### Advanced Progression Service

**Progression Service** (`progression_service.py`):
- **Secondary Progressions**: Day-for-year progression calculations with life phase analysis
- **Solar Returns**: Annual chart calculations with exact solar return timing
- **Lunar Returns**: Monthly new moon charts with emotional guidance
- **Life Phase Integration**: Age-appropriate interpretations and spiritual evolution tracking
- **Enhanced Interpretations**: Detailed analysis of progressed planets and their meanings

**Key Methods**:
```python
# Secondary progressions with life phase analysis
get_secondary_progressions(natal_chart, target_date=None)

# Enhanced solar return with seasonal themes
get_solar_return(natal_chart, year, location=None)

# Lunar return with emotional guidance
get_lunar_return(natal_chart, month, year, location=None)
```

### Comprehensive Transit Calculator Enhancement

**Updated Transit Calculator** (`transit_calculator.py`):
- **Unified Interface**: Combines all transit and progression services under one interface
- **Comprehensive Analysis**: `get_comprehensive_transit_analysis()` method for complete astrological overview
- **Feature Detection**: `is_enhanced_features_available()` checks Kerykeion availability
- **Intelligent Fallbacks**: Seamless degradation to basic calculations when advanced features unavailable

**New Comprehensive Analysis Features**:
```python
comprehensive_analysis = {
    "current_transits": {...},          # Current planetary influences
    "period_forecast": {...},           # 30-day forecast
    "important_transits": {...},        # Major life transitions
    "progressions": {...},              # Secondary progressions
    "solar_return": {...},              # Annual chart
    "lunar_return": {...},              # Monthly chart
    "integrated_themes": [...],         # Combined life themes
    "life_phase_analysis": {...},       # Current life stage
    "timing_recommendations": [...],     # Optimal action timing
    "spiritual_guidance": "...",         # Spiritual insights
    "executive_summary": "..."           # Overview for users
}
```

### Enhanced Horoscope Generation

**Updated Horoscope Generator** (`horoscope_generator.py`):
- **Transit-Integrated Horoscopes**: `generate_enhanced_horoscope()` combines traditional horoscopes with transit analysis
- **Transit Forecasts**: `generate_transit_forecast()` creates period-based predictions
- **Comprehensive Analysis**: `generate_comprehensive_analysis()` for full astrological insights
- **Energy Analysis**: Detailed energy level calculations based on multiple astrological factors
- **Practical Guidance**: Categorized recommendations (general, relationships, career, health, spiritual)

**Enhanced Features**:
- Automatic transit overlay on base horoscopes
- Energy synthesis from multiple sources (sign, transits, moon phase)
- Timing-specific recommendations
- Spiritual insights integration
- User-friendly interpretation of complex astrological data

### Dialog Handler Extensions

**New Alice Voice Commands** supported by `dialog_handler.py`:
- **Enhanced Transits**: "что меня ждет сегодня", "покажи транзиты"
- **Period Forecasts**: "прогноз на неделю", "что будет в ближайшие дни"
- **Important Transits**: "важные транзиты", "что меня ждет в будущем"
- **Timing Questions**: "когда лучше начать дело", "хорошее ли время для..."
- **Comprehensive Analysis**: "полный анализ", "детальный прогноз"

**Enhanced Handler Methods**:
```python
_handle_enhanced_transits()          # Professional transit analysis
_handle_period_forecast()            # Time-based forecasts
_handle_important_transits()         # Major life transits
_handle_timing_question()           # Optimal timing advice
_handle_comprehensive_analysis()     # Complete astrological overview
_handle_enhanced_horoscope_with_transits()  # Transit-integrated horoscopes
```

### Technical Architecture

**Multi-Backend Compatibility**:
1. **Kerykeion** (primary): Full professional features with TransitsTimeRangeFactory
2. **Swiss Ephemeris** (fallback): High precision backup calculations  
3. **Skyfield** (fallback): Pure Python alternative
4. **Built-in** (fallback): Basic calculation methods

**Error Handling & Logging**:
- Comprehensive logging with `ENHANCED_TRANSIT_SERVICE_*` and `PROGRESSION_SERVICE_*` prefixes
- Graceful degradation when advanced features unavailable
- Detailed error tracking with correlation IDs
- Performance monitoring for complex calculations

**Data Models**:
- Full Pydantic models in `transit_models.py` for all transit and progression data
- Request/response models for API integration
- Comprehensive analysis result models
- Timing and forecast data structures

### Configuration Requirements

**For Full Transit/Progression Functionality**:
- Kerykeion >=4.11.0 (included in `full` and `professional` dependency sets)
- Sufficient memory for complex ephemeris calculations
- Proper timezone handling (pytz dependency)
- Optional: Enhanced error handling for large dataset processing

**Feature Availability Checking**:
```python
# Check what features are available
availability = transit_calculator.is_enhanced_features_available()
# Returns: {"kerykeion_transits": bool, "kerykeion_progressions": bool, ...}
```

### Alice Voice Interface Optimizations

**New Voice Commands Supported**:
- "Что меня ждет сегодня" → Enhanced current transits
- "Прогноз на неделю" → 7-day transit forecast  
- "Важные транзиты" → Major life transition analysis
- "Когда лучше начать дело" → Timing optimization
- "Полный астрологический анализ" → Comprehensive overview

**Response Optimizations**:
- Voice-friendly transit descriptions (max 800 characters)
- Prioritized information based on strength and relevance
- Emotional context from lunar returns
- Practical timing advice in accessible language
- Spiritual guidance integration

### Development Best Practices

**Working with Enhanced Transit System**:
1. Always check `is_enhanced_features_available()` before using advanced features
2. Implement proper fallback chains (Kerykeion → SwissEph → Basic)
3. Use comprehensive logging patterns for debugging complex calculations
4. Test both enhanced and fallback scenarios
5. Respect Alice voice interface constraints (response length, complexity)

**Error Handling Patterns**:
```python
try:
    enhanced_result = transit_service.get_current_transits(natal_chart)
    if enhanced_result.get("source") == "basic":
        logger.warning("Enhanced features unavailable, using basic calculations")
except Exception as e:
    logger.error(f"Transit calculation failed: {e}")
    return fallback_response()
```

### Performance Considerations

**Optimization Techniques**:
- Intelligent caching of ephemeris data for repeated calculations
- Batch processing of multiple transit calculations
- Asynchronous handling of complex analysis requests
- Memory-efficient handling of large time range calculations
- Progressive loading for comprehensive analysis

**Response Time Targets**:
- Current transits: <2 seconds
- Period forecasts: <5 seconds  
- Comprehensive analysis: <10 seconds
- Important transits: <8 seconds (due to extended time range)

## Performance Optimization and Caching System (NEW 2025-08-08)

The project now includes a comprehensive performance optimization system designed specifically for Alice voice interface requirements, featuring intelligent caching, async processing, and background pre-computation.

### Core Performance Services

**AstroCacheService** (`astro_cache_service.py`): Enhanced caching system for astrological data
- **Redis Integration**: Primary caching with Redis 5.0.1, graceful fallback to memory cache
- **Astrological Data Specialization**: Optimized TTL settings for different data types
  - Natal charts: 30 days (permanent birth data)
  - Ephemeris data: 6 hours (daily planetary positions)
  - Current transits: 1 hour (real-time calculations)
  - Period forecasts: 2 hours (weekly/monthly forecasts)
  - Compatibility: 7 days (relationship analysis)
- **Performance Metrics**: Built-in hit rate monitoring, response time tracking
- **Intelligent Cleanup**: Automatic expired entry removal, memory usage optimization

**AsyncKerykeionService** (`async_kerykeion_service.py`): Non-blocking wrapper for CPU-intensive calculations
- **Thread Pool Execution**: 4-worker thread pool for parallel processing
- **Batch Operations**: Parallel calculation of multiple natal charts
- **Smart Caching Integration**: Cache-first strategy with configurable TTL
- **Performance Statistics**: P50, P95, P99 percentile tracking
- **Graceful Fallbacks**: Seamless degradation when Kerykeion unavailable

**PerformanceMonitor** (`performance_monitor.py`): Comprehensive system monitoring
- **Operation Tracking**: Response time analysis with statistical breakdowns
- **Resource Monitoring**: Memory and CPU usage per operation
- **Alert System**: Configurable thresholds for slow operations (>2s), high memory (>500MB), high CPU (>80%)
- **Background Monitoring**: System metrics collection every 30 seconds
- **Reporting**: Human-readable performance reports with trend analysis

**PrecomputeService** (`precompute_service.py`): Background data pre-generation
- **Scheduled Tasks**: Configurable intervals (6-48 hours) for different data types
- **Popular Data Pre-generation**:
  - Daily ephemeris for 7 days ahead
  - Popular zodiac chart combinations (12 signs × 5 major locations)
  - Lunar phases for 30 days ahead
  - Popular compatibility combinations
- **Background Processing**: Non-blocking execution with error recovery
- **Cache Integration**: Automatic population of frequently accessed data

**Enhanced TransitService** (`enhanced_transit_service.py`): Optimized transit calculations
- **Full Async Integration**: All methods converted to async with proper error handling
- **Intelligent Caching**: Configurable cache strategies per operation type
- **Batch Processing**: Multi-day forecasts processed in parallel batches
- **Performance Monitoring**: Integrated operation tracking and metrics
- **Cache Management**: Built-in cache warming and cleanup operations

**StartupManager** (`startup_manager.py`): Orchestrated system initialization
- **Service Coordination**: Sequential startup with dependency management
- **Cache Warmup**: Pre-population of critical data during application startup
- **Health Diagnostics**: System health checks with performance validation
- **Graceful Shutdown**: Proper cleanup of background services and connections
- **Status Monitoring**: Comprehensive system status reporting

### Performance Targets and Achievements

**Response Time Optimization**:
- **Simple Requests** (cached data): <500ms target ✅
- **Complex Calculations** (Kerykeion + caching): <2s target ✅
- **Batch Operations** (multiple charts): 3-5s per batch ✅
- **Period Forecasts** (7-30 days): <10s target ✅

**Caching Efficiency**:
- **Expected Cache Hit Rate**: 60-80% for popular requests
- **Memory Usage**: Configurable limits with intelligent cleanup
- **TTL Optimization**: Data-type specific expiration policies
- **Background Refresh**: Proactive cache warming for critical data

**System Resource Usage**:
- **Additional Memory**: 50-100MB for caching layer
- **Background CPU**: <1% for monitoring and pre-computation
- **Network Overhead**: Minimal with Redis connection pooling

### Redis Integration Architecture

**Connection Management**:
```python
# Automatic Redis detection with fallback
try:
    import redis.asyncio as redis
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Redis cache initialized")
except ImportError:
    logger.warning("Redis not available. Using in-memory cache fallback.")
    redis_client = None
```

**Failover Strategy**:
1. **Primary**: Redis-based caching with connection pooling
2. **Fallback**: In-memory cache with configurable size limits (1000 items default)
3. **Cleanup**: Background tasks for expired entry removal
4. **Monitoring**: Automatic detection of Redis connectivity issues

### Alice Voice Interface Optimizations

**Response Time Requirements**:
- Alice voice interface requires responses within 3-5 seconds maximum
- Complex astrological calculations can exceed this limit
- Async processing with intelligent caching ensures sub-second responses for cached data
- Background pre-computation reduces calculation overhead during peak usage

**Memory Management for Voice Interface**:
- Limited memory environment in voice processing servers
- Intelligent TTL prevents memory bloat
- Configurable cache size limits with LRU eviction
- Background cleanup tasks maintain optimal memory usage

### Development Best Practices for Performance

**Service Integration Pattern**:
```python
# Performance-optimized service call
async def optimized_calculation(self, params):
    # Start performance monitoring
    op_id = performance_monitor.start_operation("ServiceName", "operation")
    
    try:
        # Check cache first
        if cached_result := await astro_cache.get_cached_data(cache_key):
            performance_monitor.end_operation(op_id, success=True, cache_hit=True)
            return cached_result
        
        # Perform async calculation
        result = await async_kerykeion.calculate_data(params, use_cache=True)
        
        performance_monitor.end_operation(op_id, success=True, cache_hit=False)
        return result
        
    except Exception as e:
        performance_monitor.end_operation(op_id, success=False, error_message=str(e))
        return fallback_response()
```

**Configuration Requirements**:
- **Dependencies**: `redis==5.0.1`, `psutil==5.9.6` added to requirements
- **Environment Variables**: `REDIS_URL` for Redis connection (optional)
- **Memory Allocation**: Minimum 512MB RAM recommended for full functionality
- **Background Processing**: Ensure container/process allows background tasks

### Monitoring and Diagnostics

**Real-time Performance Metrics**:
```python
# Get comprehensive performance stats
performance_stats = await startup_manager.get_system_status()

# Monitor specific service performance
service_stats = performance_monitor.get_service_statistics("TransitService")

# Check cache efficiency
cache_stats = await astro_cache.get_cache_stats()
```

**Alert Configuration**:
- **Slow Operations**: >2000ms (configurable)
- **High Memory Usage**: >500MB per operation (configurable)
- **High CPU Usage**: >80% sustained (configurable)
- **Cache Hit Rate**: <50% (indicates need for cache warming)

### Production Deployment Considerations

**Resource Requirements**:
- **Minimum RAM**: 512MB (1GB recommended)
- **Redis Memory**: 64-128MB for typical usage
- **Background CPU**: Reserve 10-20% for monitoring/pre-computation
- **Storage**: Minimal additional storage requirements

**Configuration Options**:
```python
# Startup configuration example
await startup_manager.initialize_performance_systems(
    enable_cache_warmup=True,      # Pre-populate cache on startup
    enable_background_monitoring=True,  # Real-time performance monitoring
    enable_precomputation=True,    # Background data pre-generation
    redis_url="redis://localhost:6379/0"  # Optional Redis connection
)
```

## Enhanced AI Astrological Consultation System (NEW 2025-08-08)

The project now features a comprehensive AI-powered astrological consultation system that combines professional Kerykeion calculations with advanced Yandex GPT generation.

### Core AI Services

**AstroAIService** (`astro_ai_service.py`): Advanced AI consultation platform
- **Professional Natal Chart Interpretation**: Full Kerykeion data integration with AI analysis
- **Specialized Consultations**: Career, love, health, financial, and spiritual guidance
- **Enhanced Compatibility Analysis**: Advanced synastry with AI interpretation
- **Transit-Based Forecasting**: AI-powered predictions using professional calculations
- **Content Quality Control**: Built-in safety filters and disclaimers
- **Multi-Backend Support**: Graceful fallbacks when advanced features unavailable

**Enhanced AIHoroscopeService** (`ai_horoscope_service.py`): Extended integration
- **Natal Chart Interpretations**: `generate_natal_chart_interpretation()`
- **Enhanced Compatibility**: `generate_enhanced_compatibility_analysis()`
- **Transit Forecasts**: `generate_transit_forecast_analysis()` 
- **Specialized Consultations**: `generate_specialized_consultation()`
- **Service Status Monitoring**: `get_enhanced_service_status()`

### Sophisticated Prompt Engineering

**YandexGPTClient Enhanced** (`yandex_gpt.py`): Professional prompt templates
- **Natal Chart Prompts**: Professional interpretation using Kerykeion data
- **Synastry Analysis Prompts**: Relationship compatibility with aspect analysis
- **Transit Forecast Prompts**: Predictive astrology with timing recommendations
- **Specialized Consultation Prompts**: Topic-specific guidance (career, love, health, finances, spiritual)
- **Context-Aware Generation**: Adapts prompts based on available astrological data

### New Voice Commands for Alice

**Enhanced Intent Recognition** (`intent_recognition.py`): 60+ new voice patterns
- "интерпретация натальной карты" → AI_NATAL_INTERPRETATION
- "карьерный совет" / "совет по работе" → AI_CAREER_CONSULTATION  
- "любовная консультация" / "совет по любви" → AI_LOVE_CONSULTATION
- "здоровье и звезды" / "совет по здоровью" → AI_HEALTH_CONSULTATION
- "финансовая консультация" / "деньги и звезды" → AI_FINANCIAL_CONSULTATION
- "духовная консультация" / "кармические задачи" → AI_SPIRITUAL_CONSULTATION
- "улучшенная совместимость" / "детальная совместимость" → AI_ENHANCED_COMPATIBILITY
- "прогноз транзитов" / "транзитный прогноз" → AI_TRANSIT_FORECAST
- "статус ии" / "проверь ии" → AI_SERVICE_STATUS

### Content Safety and Quality Control

**AIContentFilter** (`ai_content_filter.py`): Comprehensive content validation
- **Safety Filtering**: Removes harmful, medical, and risky financial advice
- **Quality Assessment**: Evaluates astrological relevance and coherence
- **Content Enhancement**: Adds appropriate disclaimers based on consultation type
- **Length Optimization**: Ensures Alice voice interface compliance
- **Multi-Level Validation**: Safe/Warning/Blocked classification system

### Development Patterns for AI Features

**Service Integration Pattern**:
```python
# Check availability and generate with professional data
if self.astro_ai_service and settings.ENABLE_AI_GENERATION:
    try:
        result = await self.astro_ai_service.generate_consultation(...)
        return result  # Content validation happens automatically
    except Exception as e:
        logger.error(f"AI_CONSULTATION_ERROR: {e}")
        return traditional_fallback()  # Graceful degradation
```

**Configuration Requirements**:
- Kerykeion >=4.11.0 (professional calculations)
- ENABLE_AI_GENERATION=True (feature flag)
- YANDEX_API_KEY (GPT integration)
- Proper Docker environment variable mapping

## Russian Localization System (NEW 2025-08-08) - Issue #68

The project now features comprehensive Russian localization for all astrological data, providing native Russian experience for Yandex Alice users.

### Core Russian Localization Service

**RussianAstrologyAdapter** (`russian_astrology_adapter.py`): Complete localization platform
- **Comprehensive Terminology**: Full Russian names for planets, signs, houses, aspects
- **Grammatical Declensions**: All 6 Russian cases (nominative, genitive, dative, accusative, instrumental, prepositional)
- **Timezone Integration**: Support for all 11 Russian time zones with city detection
- **Voice Optimization**: Proper stress marks and pronunciation rules for TTS
- **Cultural Adaptation**: Russian interpretations and cultural context
- **Kerykeion Integration**: Seamless integration with professional astrological calculations

### Russian Astrological Terminology

**Russian Zodiac Signs** (RussianZodiacSign enum):
```python
ARIES = {"ru": "Овен", "genitive": "Овна", "dative": "Овну", ...}
TAURUS = {"ru": "Телец", "genitive": "Тельца", "dative": "Тельцу", ...}
# All 12 signs with complete grammatical declensions
```

**Russian Planets** (RussianPlanet enum):
- Complete planetary names with keywords and descriptions
- Cultural meanings: Солнце, Луна, Меркурий, Венера, Марс, Юпитер, Сатурн, Уран, Нептун, Плутон, Хирон, Лилит
- Node support: Северный Узел, Лунный Узел
- Professional descriptions with astrological keywords

**Russian Houses** (RussianHouse enum):
- All 12 astrological houses with Russian names
- Detailed descriptions: "Дом Личности", "Дом Ресурсов", etc.
- Keyword associations for each house

**Russian Aspects** (RussianAspect enum):
- Complete aspect terminology: Соединение, Оппозиция, Тригон, Квадрат, etc.
- Orb information and nature classifications
- Professional astrological interpretations

### Russian Timezone Support

**Russian Timezone System** (RussianTimezone enum):
- Complete support for all 11 Russian time zones
- Automatic city detection for major Russian cities
- Timezone mapping: Калининградское, Московское, Самарское, Екатеринбургское, etc.
- Historical timezone data support

**City-to-Timezone Mapping**:
```python
city_timezone_map = {
    "москва": RussianTimezone.MOSCOW.value,
    "санкт-петербург": RussianTimezone.MOSCOW.value,
    "екатеринбург": RussianTimezone.YEKATERINBURG.value,
    "новосибирск": RussianTimezone.KRASNOYARSK.value,
    "владивосток": RussianTimezone.VLADIVOSTOK.value,
    # 50+ major Russian cities supported
}
```

### New Russian Intent Handlers

**Enhanced Intent Recognition** (5 new intents):

1. **SIGN_DESCRIPTION**: "Расскажи про мой знак зодиака"
   - Detailed zodiac sign characteristics
   - Cultural Russian interpretations
   - Voice-optimized responses

2. **PLANET_IN_SIGN**: "Что означает Солнце в Овне?"
   - Planetary placements analysis  
   - Combined interpretations
   - Professional astrological meanings

3. **HOUSE_CHARACTERISTICS**: "Характеристика седьмого дома"
   - Complete house system descriptions
   - Life area explanations
   - Astrological house meanings

4. **ENHANCED_COMPATIBILITY**: "Совместимость Льва и Стрельца"
   - Advanced compatibility analysis in Russian
   - Professional relationship insights
   - Cultural relationship context

5. **RETROGRADE_INFLUENCE**: "Влияние Меркурия в ретрограде"
   - Retrograde planetary effects
   - Practical advice and interpretations
   - Russian astrological context

### Voice Interface Optimization

**Russian TTS Enhancement**:
- Stress mark dictionary for proper pronunciation
- Astrological term stress patterns: овéн, мерку́рий, юпи́тер
- Natural Russian speech patterns
- Alice voice interface compliance

**Grammatical Case Usage**:
```python
# Automatic case selection based on context
planet_name = get_russian_planet_description("Venus", case="instrumental")
# Returns: "Венерой" (instrumental case)
```

### Development Patterns for Russian Features

**Service Integration Pattern**:
```python
# Import and use Russian adapter
from app.services.russian_astrology_adapter import russian_adapter

# Get localized descriptions
sign_desc = russian_adapter.get_russian_sign_description("Leo", case="genitive")
planet_desc = russian_adapter.get_russian_planet_description("Mars")
house_desc = russian_adapter.get_russian_house_description(7)

# Format for voice output
voice_text = russian_adapter.format_for_voice(response_text, add_stress_marks=True)
```

**Timezone Detection**:
```python
# Automatic timezone detection for Russian cities
timezone_info = russian_adapter.detect_russian_timezone("Екатеринбург")
# Returns: {"zone": "Asia/Yekaterinburg", "offset": "+05:00", "name": "Екатеринбургское время"}
```

### Configuration Requirements

**For Full Russian Localization**:
- Kerykeion >=4.11.0 (professional calculations)
- pytz for Russian timezone handling
- Proper UTF-8 encoding for Cyrillic characters
- Alice voice interface compliance

**Performance Optimizations**:
- Localization data caching for repeated requests
- Efficient grammatical case lookup
- Memory-optimized terminology storage
- Fast timezone detection algorithms

### Alice Voice Commands Integration

**New Voice Patterns** (60+ new Russian patterns added):
- Natural language zodiac sign descriptions
- Planet-in-sign combinations with proper grammar
- House characteristic requests
- Enhanced compatibility questions with Russian sign names
- Retrograde influence inquiries

**Voice Response Optimization**:
- Character limits for Alice TTS (800 chars for detailed responses)
- Proper Russian stress marks for natural pronunciation
- Cultural context in astrological interpretations
- Button limitations compliance (5 buttons maximum)

### Testing and Quality Assurance

**Russian Localization Testing**:
- Comprehensive terminology coverage tests
- Grammatical case accuracy validation
- Timezone detection accuracy for Russian cities
- Voice interface TTS optimization testing
- Cultural interpretation appropriateness

**Production Deployment Notes**:
- Full Russian localization available in production
- Graceful fallback to English terminology if needed
- Performance monitoring for localized responses
- Alice voice interface compliance validation

### Knowledge Update History

**2025-08-08**: 
- **MAJOR UPDATE**: Added comprehensive performance optimization system for Alice voice interface requirements
- Implemented Redis-based caching with intelligent TTL policies for astrological data types
- Created async Kerykeion wrapper with thread pool execution and batch processing capabilities
- Added real-time performance monitoring with percentile analysis and configurable alert system
- Implemented background pre-computation service for popular astrological data with scheduled tasks
- Enhanced transit service with full async integration and intelligent cache strategies
- Created startup manager for orchestrated system initialization with health diagnostics

**2025-08-08**: 
- **MAJOR UPDATE**: Added comprehensive AI astrological consultation system integrating Kerykeion professional calculations with advanced Yandex GPT generation
- Enhanced dialog handlers with 60+ new voice command patterns for specialized AI consultations
- Implemented robust content safety filtering with multi-level validation and automatic disclaimer systems
- Created sophisticated prompt engineering templates for natal charts, synastry, transits, and specialized guidance
- Added complete Alice voice interface optimization for AI-powered consultations

**2025-08-08 (Issue #68)**: 
- **MAJOR RUSSIAN LOCALIZATION**: Implemented comprehensive Russian localization system for Kerykeion astrological data
- Added RussianAstrologyAdapter with 800+ lines of code providing full terminology localization
- Implemented grammatical declensions for all astrological terms (6 Russian cases)
- Added support for all 11 Russian time zones with automatic city detection
- Created 5 new intent handlers for Russian astrological queries
- Enhanced voice interface with proper Russian stress marks and pronunciation
- Added cultural adaptation of astrological interpretations for Russian audience
- Integrated seamless Russian timezone support with major Russian cities mapping

**2025-08-08**: Added comprehensive transit and progression system with full Kerykeion integration, enhanced dialog handlers for new Alice voice commands, professional-grade astrological calculations, and intelligent fallback mechanisms for production reliability.

**2025-01-08**: Added comprehensive logging architecture across all services, documented astrological calculation details, enhanced Alice voice interface specifications, and expanded debugging practices based on Docker environment variable resolution and systematic webhook flow analysis.
