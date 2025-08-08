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
- **natal_chart.py**: Enhanced birth chart calculations with Kerykeion integration
- **horoscope_generator.py**: Horoscope generation with AI and traditional methods
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

### Knowledge Update History

**2025-01-08**: Added comprehensive logging architecture across all services, documented astrological calculation details, enhanced Alice voice interface specifications, and expanded debugging practices based on Docker environment variable resolution and systematic webhook flow analysis.
