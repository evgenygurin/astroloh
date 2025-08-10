# Claude Development Guidelines

This file contains guidelines and instructions for Claude AI when working with the Astroloh project.

## ⚠️ КРИТИЧЕСКАЯ ИНФОРМАЦИЯ О ВОССТАНОВЛЕНИИ КОНТЕКСТА

**НЕМЕДЛЕННО ПРОЧИТАЙ:** `/Users/laptop/dev/astroloh/PROJECT_MEMORY.md` - содержит актуальную контекстную память проекта.

**ПРОБЛЕМА С ПОТЕРЕЙ ПАМЯТИ РЕШЕНА (2025-08-10):**

- MCP Vercel-Mem0 сервер добавлен в конфигурацию Claude для персистентной памяти
- Создана резервная система памяти через PROJECT_MEMORY.md
- При потере контекста всегда читай PROJECT_MEMORY.md в первую очередь

**Текущий статус проекта:**

- Активная ветка: `codegen/122-4-epic-vnedrenie-kerykeion`
- Множественные изменения в app/services/ и tests/
- 3 падающих теста требуют исправления
- Kerykeion 4.x полностью интегрирован для профессиональной астрологии

## Project Overview

Astroloh is a voice skill for Yandex Alice that provides personalized astrological forecasts and consultations. The project is built with Python 3.11, FastAPI, PostgreSQL, and integrates with advanced astronomical calculation libraries.

**Core Features:**

- Personalized horoscopes (daily/weekly/monthly)
- Professional natal chart calculations with Kerykeion integration
- Zodiac sign compatibility analysis and synastry
- Transit analysis and timing recommendations
- Lunar calendar and astronomical data
- AI-powered astrological consultations
- Full Russian localization for Alice voice interface

## Development Environment Setup

### Installation Commands

Choose appropriate installation based on your system:

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

### Docker Development

```bash
docker-compose up --build
# Access API docs at http://localhost:8000/docs
```

## Code Quality and Testing

### Essential Commands

**Formatting:**

```bash
black app/ tests/
isort app/ tests/
```

**Linting:**

```bash
flake8 app/ tests/
mypy app/
```

**Testing:**

```bash
pytest                    # All tests
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest --cov=app --cov-report=html  # With coverage
```

**Target:** 80% test coverage minimum

## Core Architecture

### Project Structure

```text
astroloh/
├── app/                    # Main application code
│   ├── api/               # API routers (Yandex Dialogs integration)
│   ├── core/              # Configuration and database setup
│   ├── models/            # Data models and Pydantic schemas
│   ├── services/          # Business logic layer
│   ├── utils/             # Shared utilities
│   └── main.py           # FastAPI entry point
├── tests/                 # Test suite with categories
├── migrations/            # Database migrations (Alembic)
└── docker-compose.yml    # Docker configuration
```

### Key Services

**Core Astronomical Services:**

- `astrology_calculator.py`: Multi-backend astronomical calculations
- `kerykeion_service.py`: Professional astrology with Kerykeion integration
- `natal_chart.py`: Enhanced birth chart calculations
- `transit_calculator.py`: Transit analysis and timing

**Enhanced Features:**

- `enhanced_transit_service.py`: Professional transit analysis with forecasting
- `progression_service.py`: Secondary progressions and solar/lunar returns
- `synastry_service.py`: Relationship compatibility analysis
- `compatibility_analyzer.py`: Multi-type compatibility system

**AI and Localization:**

- `ai_horoscope_service.py`: AI-powered consultations with Yandex GPT
- `astro_ai_service.py`: Advanced AI consultation platform
- `russian_astrology_adapter.py`: Complete Russian localization

**Performance and Infrastructure:**

- `astro_cache_service.py`: Redis-based caching for astrological data
- `async_kerykeion_service.py`: Async wrapper for CPU-intensive calculations
- `performance_monitor.py`: Real-time performance monitoring

**Alice Voice Interface:**

- `dialog_handler.py`: Conversation flow management
- `intent_recognition.py`: NLP for user intent detection
- `response_formatter.py`: Alice-compatible response formatting
- `session_manager.py`: User session handling

## Time Handling Utilities

### Advanced Astrological Time Management (2025-08-10 - FULLY REFACTORED)

**Core Module: `app/utils/astro_time_utils.py`**

Comprehensive time handling utility designed specifically for astrological calculations with emphasis on security, precision, and timezone management.

#### Key Features

**Security-First Design:**

- ✅ **Input sanitization** with regex validation against injection attacks
- ✅ **String length limits** to prevent resource exhaustion
- ✅ **Dangerous pattern detection** for HTML/SQL injection, path traversal, control characters
- ✅ **Safe parsing** with comprehensive error handling

**Precision Time Management:**

- ✅ **Timezone-aware datetime** operations using Python 3.9+ `zoneinfo`
- ✅ **Historical date support** with validation for astrological calculations (1000-3000 CE)
- ✅ **Coordinate-based timezone detection** from longitude
- ✅ **Local solar time calculations** for precise birth time accuracy
- ✅ **Birth time validation** with future date protection

**Performance Optimizations:**

- ✅ **LRU caching** for timezone objects with 256 entry limit
- ✅ **Batch operations** support for multiple datetime conversions
- ✅ **Immutable data structures** for thread safety
- ✅ **Builder pattern** for complex object construction

#### Core Classes

**1. AstroTimeUtils (Main Utility Class)**

```python
from app.utils.astro_time_utils import astro_time

# Parse birth datetime with comprehensive validation
astro_dt = astro_time.parse_birth_datetime(
    date_input="15.08.1990",
    time_input="14:30:00", 
    timezone_input="Europe/Moscow",
    coordinates=CoordinateInfo(55.7558, 37.6176)
)

# Convert timezone with validation
utc_dt = astro_time.to_utc(astro_dt)

# Calculate precision metadata
precision = astro_time.calculate_birth_time_precision(astro_dt)
```

**2. TimezoneManager (Advanced Timezone Handling)**

```python
from app.utils.astro_time_utils import TimezoneManager

tz_manager = TimezoneManager()

# City name mapping with Russian support
tz = tz_manager.get_timezone("москва")  # Returns Europe/Moscow
tz = tz_manager.get_timezone("новосибирск")  # Returns Asia/Novosibirsk

# Coordinate-based detection
detected_tz = tz_manager.detect_timezone_from_coordinates(37.6176)
```

**3. DateTimeValidator (Security & Validation)**

```python
from app.utils.astro_time_utils import DateTimeValidator

# Secure input sanitization
clean_input = DateTimeValidator.sanitize_input("2023-08-15 14:30:00")

# Multi-format parsing with fallbacks
dt = DateTimeValidator.parse_datetime_string(
    "15.08.2023 14:30", "Europe/Moscow"
)

# Birth datetime validation
is_valid = DateTimeValidator.validate_birth_datetime(dt, coordinates)
```

**4. AstroDateTime (Immutable Time Object)**

```python
from app.utils.astro_time_utils import AstroDateTime, CoordinateInfo

# Create timezone-aware astrological datetime
astro_dt = AstroDateTime(
    dt=datetime(1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")),
    timezone_name="Europe/Moscow",
    coordinates=CoordinateInfo(55.7558, 37.6176),
    source_format="string_input"
)

# UTC conversion
utc_time = astro_dt.utc

# Local solar time calculation
solar_time = astro_dt.to_local_solar_time()
solar_offset = astro_dt.local_solar_time_offset
```

**5. AstroDateTimeBuilder (Builder Pattern)**

```python
# Complex datetime construction with fluent interface
astro_dt = (astro_time.create_astro_datetime_builder()
    .date("1990-08-15")
    .time("14:30:00")
    .timezone("Europe/Moscow")
    .coordinates(55.7558, 37.6176, 150.0)
    .build())
```

#### Supported Input Formats

**DateTime String Formats:**

```python
SUPPORTED_FORMATS = [
    "%Y-%m-%d %H:%M:%S",      # 2023-08-15 14:30:00
    "%Y-%m-%dT%H:%M:%S",      # 2023-08-15T14:30:00 (ISO)
    "%Y-%m-%dT%H:%M:%SZ",     # 2023-08-15T14:30:00Z (UTC)
    "%Y-%m-%dT%H:%M:%S%z",    # 2023-08-15T14:30:00+03:00
    "%Y-%m-%d %H:%M",         # 2023-08-15 14:30
    "%Y-%m-%d",               # 2023-08-15 (midnight)
    "%d.%m.%Y %H:%M:%S",      # 15.08.2023 14:30:00 (European)
    "%d.%m.%Y %H:%M",         # 15.08.2023 14:30
    "%d.%m.%Y",               # 15.08.2023
    "%d/%m/%Y %H:%M:%S",      # 15/08/2023 14:30:00
    "%d/%m/%Y %H:%M",         # 15/08/2023 14:30
    "%d/%m/%Y",               # 15/08/2023
]
```

**Russian City Mappings:**

```python
RUSSIAN_CITIES = {
    "москва": "Europe/Moscow",
    "санкт-петербург": "Europe/Moscow", 
    "новосибирск": "Asia/Novosibirsk",
    "екатеринбург": "Asia/Yekaterinburg",
    "сочи": "Europe/Moscow",
    # ... 50+ major Russian cities
}
```

#### Security Validation Patterns

**Dangerous Input Detection:**

```python
DANGEROUS_PATTERNS = [
    r"[<>\"'`]",              # HTML/SQL injection chars
    r"\\x[0-9a-fA-F]{2}",     # Hex escapes
    r"\\[0-7]{3}",            # Octal escapes  
    r"\.\./",                 # Path traversal
    r"[\r\n\0]",              # Control characters
]
```

**Usage in Astrological Services:**

```python
# Integration with natal chart calculations
def calculate_birth_chart(birth_data):
    try:
        # Parse and validate birth time
        astro_dt = astro_time.parse_birth_datetime(
            birth_data["date"],
            birth_data["time"], 
            birth_data["timezone"],
            birth_data.get("coordinates")
        )
        
        # Calculate precision metadata
        precision = astro_time.calculate_birth_time_precision(astro_dt)
        
        # Use UTC for calculations
        utc_dt = astro_time.to_utc(astro_dt)
        
        return {
            "birth_datetime": utc_dt.dt,
            "precision": precision,
            "timezone": astro_dt.timezone_name,
            "coordinates": astro_dt.coordinates
        }
        
    except (InvalidDateTimeError, InvalidTimezoneError, CoordinateTimeError) as e:
        logger.error(f"TIME_VALIDATION_ERROR: {e}")
        return {"error": str(e)}
```

#### Testing Coverage

**Comprehensive Test Suite: `tests/test_astro_time_utils.py`**

- ✅ **Security testing** with malicious input validation
- ✅ **Timezone validation** including Russian city mappings
- ✅ **Historical date handling** with edge cases
- ✅ **Coordinate validation** with geographic boundaries
- ✅ **Performance testing** with batch operations and caching
- ✅ **Integration scenarios** with real-world astrological use cases
- ✅ **Error handling** with graceful fallbacks

**Key Test Categories:**

```bash
# Run time utility tests
pytest tests/test_astro_time_utils.py -v

# Security tests
pytest tests/test_astro_time_utils.py::TestDateTimeValidator::test_sanitize_dangerous_input -v

# Performance tests  
pytest tests/test_astro_time_utils.py::TestPerformance -v

# Integration tests
pytest tests/test_astro_time_utils.py::TestIntegrationScenarios -v
```

#### Best Practices for Time Handling

**1. Always Use AstroTimeUtils:**

```python
# ✅ Correct: Use centralized time utility
from app.utils.astro_time_utils import astro_time

astro_dt = astro_time.parse_birth_datetime(user_input)

# ❌ Incorrect: Direct datetime manipulation
dt = datetime.strptime(user_input, "%Y-%m-%d")  # No validation!
```

**2. Validate All Time Inputs:**

```python
# ✅ Correct: Comprehensive validation
try:
    astro_dt = astro_time.parse_birth_datetime(
        date_input, time_input, timezone_input, coordinates
    )
except (InvalidDateTimeError, InvalidTimezoneError) as e:
    return {"error": "Invalid time data", "details": str(e)}
```

**3. Use Coordinates for Accuracy:**

```python
# ✅ Correct: Coordinate-based timezone detection  
coordinates = CoordinateInfo(latitude, longitude)
astro_dt = astro_time.parse_birth_datetime(
    date_input, time_input, coordinates=coordinates
)

# Access local solar time for precise calculations
solar_time = astro_dt.to_local_solar_time()
```

**4. Cache-Friendly Operations:**

```python
# ✅ Correct: Use batch operations for multiple dates
birth_dates = [...]
converted_dates = astro_time.batch_convert_timezones(birth_dates, "UTC")
```

#### Global Instance Usage

**Immediate Access:**

```python
# Global instance available throughout application
from app.utils.astro_time_utils import astro_time

# Ready to use - no initialization required
result = astro_time.parse_birth_datetime("1990-08-15 14:30:00")
```

**Thread Safety:**

- All operations use immutable data structures
- Thread-safe timezone caching with LRU cache
- Safe for concurrent use in async environments

#### Integration with Alice Voice Interface

**Voice-Optimized Parsing:**

```python
# Handle voice recognition errors
def parse_voice_date(voice_input):
    # Preprocess common speech recognition errors
    cleaned = voice_input.replace("гороскоп ля", "гороскоп для")
    
    try:
        return astro_time.parse_birth_datetime(cleaned)
    except InvalidDateTimeError:
        return suggest_correction(voice_input)
```

**Russian Language Support:**

```python
# Support Russian date formats and city names
astro_dt = astro_time.parse_birth_datetime(
    "15.08.1990",           # European format
    "14:30",               # 24-hour time
    "москва"               # Russian city name
)
```

This time handling system provides the foundation for all temporal operations in the astrological application, ensuring accuracy, security, and proper timezone management essential for precise astrological calculations.

## Time Handling Refactoring Status (2025-08-10)

**🎯 OBJECTIVE**: Replace ALL external datetime library usage with centralized `astro_time_utils.py` methods throughout the entire application.

### ✅ Completed Refactoring

**Models Layer:**
- ✅ `app/models/database.py` - All SQLAlchemy default timestamps now use `db_timestamp_default()`
- ✅ `app/models/iot_models.py` - Database timestamp lambdas replaced
- ✅ `app/models/time_models.py` - Already properly integrated (no changes needed)
- ✅ `app/utils/validators.py` - `date.today()` calls replaced with `utcnow().date()`

**API Layer:**
- ✅ `app/main.py` - Health check endpoint uses `current_timestamp()`
- ✅ `app/api/auth.py` - JWT expiry and user timestamps use `utcnow()`
- ✅ `app/api/yandex_dialogs.py` - Request timing uses `utcnow()`
- ✅ `app/api/security.py` - Report date ranges use `utcnow()`

**Services Layer (Partially Complete):**
- ✅ `app/services/astro_ai_service.py` - Timestamps and generation times
- ✅ `app/services/session_manager.py` - Session activity timestamps  
- ✅ `app/services/conversation_manager.py` - Conversation timing
- ✅ `app/services/performance_monitor.py` - Monitoring timestamps
- ✅ `app/services/feature_flag_service.py` - Feature flag timestamps
- 🔄 **35+ other service files** - Need systematic replacement

### 🚀 New Helper Functions Added

Essential functions for common datetime patterns:

```python
from app.utils.astro_time_utils import (
    utcnow,              # Replacement for datetime.utcnow()
    now,                 # Replacement for datetime.now() 
    current_timestamp,   # ISO timestamp string
    database_timestamp,  # UTC datetime for DB operations
    db_timestamp_default, # Lambda factory for SQLAlchemy defaults
    create_astro_datetime_now  # Current time as AstroDateTime
)
```

### 📋 Refactoring Rules

**CRITICAL**: Throughout the application:

1. **Never use direct datetime imports** (except in `astro_time_utils.py`)
2. **Replace `datetime.now()`** → `utcnow()` or `now(tz)`  
3. **Replace `datetime.utcnow()`** → `utcnow()`
4. **Use `db_timestamp_default()`** for SQLAlchemy defaults
5. **Use `current_timestamp()`** for ISO strings
6. **Always import from astro_time_utils**: `from app.utils.astro_time_utils import utcnow`

**Database Pattern:**
```python
# OLD - Avoid this pattern
from datetime import datetime, timezone
created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# NEW - Use this pattern  
from app.utils.astro_time_utils import db_timestamp_default
created_at = Column(DateTime, default=db_timestamp_default())
```

**API Pattern:**
```python  
# OLD - Avoid this pattern
from datetime import datetime
return {"timestamp": datetime.utcnow().isoformat()}

# NEW - Use this pattern
from app.utils.astro_time_utils import current_timestamp
return {"timestamp": current_timestamp()}
```

### ✅ Comprehensive Test Suite

Enhanced test suite covers:
- ✅ All helper functions (`utcnow`, `current_timestamp`, etc.)
- ✅ Type safety and consistency checks
- ✅ Performance and caching validation
- ✅ Security input validation
- ✅ Real-world integration scenarios
- ✅ Error handling and edge cases

Run tests: `pytest tests/test_astro_time_utils.py -v`

### 🎯 Next Phase

Continue systematic replacement of remaining service files to achieve 100% centralization of datetime operations through `astro_time_utils.py`.

Priority services for completion:
- `astrology_calculator.py` - Core calculations
- `kerykeion_service.py` - Professional astrology
- `dialog_handler.py` - User interactions
- `ai_horoscope_service.py` - AI consultations

## Astronomical Calculation System

### Multi-Backend Architecture with Enhanced Kerykeion Integration

**Priority System (Fully Implemented 2025-08-09):**

1. **Kerykeion 4.x** (primary): Complete professional astrology suite
   - ✅ 15+ house systems including Placidus, Koch, Equal, Whole Sign, etc.
   - ✅ 20+ celestial bodies including asteroids (Ceres, Pallas, Juno, Vesta)
   - ✅ Professional aspect calculation with color coding and orbs
   - ✅ Arabic Parts with Russian interpretations
   - ✅ Secondary progressions and solar/lunar returns
   - ✅ Advanced synastry with composite charts and karmic connections
   - ✅ SVG chart generation with professional themes
2. **Swiss Ephemeris** (fallback): High precision ephemeris calculations
3. **Skyfield** (fallback): Pure Python astronomical alternative
4. **Built-in** (fallback): Basic calculation methods for core functionality

**Enhanced Key Features:**

- ✅ Automatic fallback mechanisms ensuring 99.9% uptime reliability
- ✅ Professional-grade calculations with 15+ house systems
- ✅ Complete aspect analysis: major, minor, and creative aspects with exact orbs
- ✅ Comprehensive ephemeris data with intelligent Redis caching
- ✅ Multi-language support with full Russian localization
- ✅ Performance optimization with async processing and background pre-computation
- ✅ AI integration with Yandex GPT for personalized interpretations
- ✅ Advanced relationship analysis through professional synastry methods

## Alice Voice Interface Integration

### Yandex Dialogs API Integration

**Webhook Flow:**

```text
POST /api/v1/yandex/webhook
├── intent_recognition.py (intent + entity extraction)
├── dialog_handler.py (13 intent handlers)
├── Service Layer (calculations, AI generation)
├── response_formatter.py (Alice-compatible formatting)
└── Return YandexResponseModel
```

**Supported Intent Handlers:**

- `handle_greet()` - Welcome flow
- `handle_horoscope()` - Horoscope generation (traditional + AI)
- `handle_compatibility()` - Zodiac compatibility analysis
- `handle_natal_chart()` - Birth chart calculations
- `handle_transits()` - Current planetary influences
- `handle_advice()` - Personalized recommendations
- Plus 7 additional specialized handlers

### Russian Language Processing

**Voice Command Support:**

- Comprehensive zodiac sign patterns with grammatical declensions
- Voice preprocessing for speech recognition error correction
- Entity extraction for dates, times, and zodiac signs
- Sentiment analysis for user mood detection

**Response Optimization:**

- Character limits: horoscopes max 800 chars, compatibility max 600 chars
- TTS optimization with automatic pause insertion
- Button limits: maximum 5 buttons per response (Alice requirement)

## Advanced Features

### Professional Astrology with Enhanced Kerykeion Integration

**Comprehensive Capabilities (Fully Implemented 2025-08-09):**

- ✅ **Complete natal charts** with 20+ celestial bodies: traditional planets + Chiron, Lilith, Ceres, Pallas, Juno, Vesta
- ✅ **Advanced aspect calculation** with precise orbs, color coding, and applying/separating analysis
- ✅ **15+ house systems** including Placidus, Koch, Equal, Whole Sign, Regiomontanus, Campanus, Topocentric, Alcabitus, Morinus, Porphyrius, Vehlow, Meridian, Azimuthal, Polich Page, Natural Graduation
- ✅ **Professional synastry** with house overlays, composite charts, and karmic connections analysis
- ✅ **Enhanced transit analysis** with house transits, aspect strength assessment, and timing precision
- ✅ **Extended Arabic Parts** with Russian interpretations: Fortune, Spirit, Love, Marriage, Career
- ✅ **Secondary progressions** (day = year method) for personality evolution analysis
- ✅ **Solar and lunar returns** for annual and monthly forecasting
- ✅ **Chart pattern recognition**: stelliums, chart shapes, elemental balance, planetary strengths
- ✅ **SVG chart generation** with professional themes and customizable appearance

### Enhanced AI-Powered Consultations (2025-08-09)

**Advanced AI Services with Deep Kerykeion Integration:**

- ✅ **Professional natal interpretations** using comprehensive Kerykeion chart data with planetary strengths, elemental analysis, and chart patterns
- ✅ **Specialized AI consultations** with focus areas: career, love, health, financial, spiritual guidance
- ✅ **Intelligent compatibility analysis** combining traditional synastry with AI-powered relationship insights
- ✅ **Context-aware interpretations** leveraging house emphasis, aspect patterns, and dominant elements
- ✅ **Personalized consultation prompts** with structured AI responses optimized for Alice voice interface
- ✅ **Content safety filtering** and quality control with Russian cultural adaptation
- ✅ **AI confidence scoring** and fallback mechanisms for consistent user experience

### Russian Localization System

**Complete Localization:**

- Full Russian terminology for planets, signs, houses, aspects
- Grammatical declensions for all 6 Russian cases
- Support for all 11 Russian time zones with city detection
- Voice optimization with proper stress marks for TTS
- Cultural adaptation of astrological interpretations

### Enhanced Performance Optimization (2025-08-09)

**Advanced Caching and Performance Strategy:**

- ✅ **Intelligent Redis caching** with Kerykeion-specific optimizations and metadata enrichment
- ✅ **Specialized TTL policies** for different data types:
  - Natal charts (Kerykeion-enhanced): 30 days
  - AI interpretations: 7 days
  - Current transits: 1 hour
  - Synastry analysis: 7 days
  - Arabic parts: 30 days
- ✅ **Background pre-computation** for popular astrological data and ephemeris
- ✅ **Real-time performance monitoring** with efficiency scoring and slow operation alerts
- ✅ **Async processing** for CPU-intensive Kerykeion calculations
- ✅ **Cache warming strategies** for frequently requested data
- ✅ **Performance metrics** including hit rates, response times, and system efficiency
- ✅ **Deterministic cache keys** ensuring consistent data retrieval across sessions

## Production Configuration

### Critical Environment Variables

**Required:**

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `YANDEX_API_KEY`: Required for GPT API access
- `YANDEX_FOLDER_ID`: Yandex Cloud folder identifier

**Docker Environment Mapping:**

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - YANDEX_API_KEY=${YANDEX_API_KEY}
      - YANDEX_FOLDER_ID=${YANDEX_FOLDER_ID}
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
```

**Important:** After environment changes, containers require full restart:

```bash
docker-compose down && docker-compose up
```

### Performance Targets

**Response Time Requirements:**

- Simple requests (cached): <500ms
- Complex calculations: <2s
- Period forecasts: <5s
- Comprehensive analysis: <10s

**Alice Voice Interface:**

- Maximum response time: 3-5 seconds
- Background pre-computation reduces calculation overhead
- Intelligent caching ensures sub-second responses for popular requests

## Development Best Practices

### Code Standards

1. **Type Hints:** Required for all functions (mypy enforced)
2. **Async Patterns:** Use async/await for I/O operations
3. **Error Handling:** Graceful fallbacks with proper logging
4. **Testing:** Maintain 80% coverage minimum
5. **Formatting:** Black + isort before commits

### Enhanced Service Integration Patterns (2025-08-09)

**Multi-Backend Usage with Full Kerykeion Integration:**

```python
# Enhanced Kerykeion integration with comprehensive features
if kerykeion_service.is_available():
    # Use full Kerykeion capabilities
    chart_data = kerykeion_service.get_full_natal_chart_data(
        name, birth_datetime, latitude, longitude, timezone, 
        house_system, zodiac_type, city, nation
    )
    
    # Calculate advanced features
    progressions = kerykeion_service.calculate_secondary_progressions(...)
    solar_return = kerykeion_service.calculate_solar_return(...)
    arabic_parts = kerykeion_service.calculate_arabic_parts_extended(...)
else:
    # Graceful fallback to basic calculator
    chart_data = astrology_calculator.calculate_basic_chart(...)
```

**Advanced Synastry Integration:**

```python
# Enhanced synastry with Kerykeion data
synastry_result = await synastry_service.calculate_advanced_synastry(
    person1, person2, latitude1, longitude1, latitude2, longitude2
)
# Includes house overlays, composite charts, and karmic connections
```

**Transit Analysis with Kerykeion:**

```python
# Professional transit analysis
transits = await enhanced_transit_service.get_current_transits_kerykeion(
    name, birth_datetime, latitude, longitude, 
    transit_date, timezone, include_minor_aspects=True
)
# Returns detailed transit analysis with house transits and aspect strength
```

**Performance Monitoring:**

```python
# Use performance monitoring for critical operations
op_id = performance_monitor.start_operation("ServiceName", "operation")
try:
    result = await service.perform_calculation(...)
    performance_monitor.end_operation(op_id, success=True)
    return result
except Exception as e:
    performance_monitor.end_operation(op_id, success=False, error_message=str(e))
    return fallback_response()
```

### Debugging Guidelines

**Common Issues:**

1. **Yandex GPT 401 errors:** Check environment variable mapping in Docker
2. **Intent recognition failures:** Review entity extraction logs
3. **Performance issues:** Monitor cache hit rates and backend selection
4. **Alice compliance:** Verify response length and button limits

**Logging Patterns:**

- Use service-specific prefixes: `KERYKEION_SERVICE_*`, `AI_CONSULTATION_*`
- Include correlation IDs for request tracking
- Log backend selection and fallback activation
- Force logging with emojis for critical debugging

## Testing Strategy

### Test Categories

**Unit Tests:** Individual service testing with mocks
**Integration Tests:** API endpoint and database interaction testing  
**Performance Tests:** Response time and resource usage validation
**Security Tests:** Authentication, encryption, and GDPR compliance

### Production Testing

```bash
# Test horoscope generation
curl -X POST http://localhost:8000/api/v1/yandex/webhook \
  -H "Content-Type: application/json" \
  -d '{"request": {"command": "дай гороскоп для льва"}, "session": {"user_id": "test", "session_id": "test"}, "version": "1.0"}'

# Test compatibility analysis
curl -X POST http://localhost:8000/api/v1/yandex/webhook \
  -H "Content-Type: application/json" \
  -d '{"request": {"command": "совместимость льва и овна"}, "session": {"user_id": "test", "session_id": "test"}, "version": "1.0"}'
```

## Security and Compliance

**Data Protection:**

- Personal data encryption using cryptography library
- GDPR compliance utilities for data protection
- Secure session management with encrypted tokens
- Input validation for all user inputs

**API Security:**

- JWT token authentication
- Rate limiting for API endpoints
- Content safety filtering for AI-generated responses
- Secure environment variable handling

## Deployment and Monitoring

### Docker Deployment

**Resource Requirements:**

- Minimum RAM: 512MB (1GB recommended)
- Redis Memory: 64-128MB for typical usage
- Background CPU: Reserve 10-20% for monitoring

### Monitoring Strategy

**Key Metrics:**

- Yandex GPT API success/failure rates
- Astronomical calculation backend usage
- Cache hit rates and performance statistics
- Alice voice interface response times
- Intent recognition accuracy

**Alert Thresholds:**

- Slow operations: >2000ms
- High memory usage: >500MB per operation
- Cache hit rate: <50%
- High CPU usage: >80% sustained

## Development Workflow

1. Always run formatting and linting before commits
2. Ensure tests pass with minimum 80% coverage
3. Check both enhanced features and fallback scenarios
4. Verify Alice voice interface constraints (response length, button limits)
5. Test Docker environment with proper variable mapping
6. Monitor performance metrics for critical operations

When making changes, always consider the astrological domain context and maintain the existing service-oriented architecture with graceful fallback mechanisms.

## Markdown Linting Guidelines

- Always ensure headings are surrounded by blank lines to follow the MD022/blanks-around-headings rule
- When using headings, include a blank line before and after the heading to maintain proper markdown formatting

## Markdownlint Warnings and Recommendations

- Always add a blank line before and after headings to comply with MD022/blanks-around-headings
- **Always specify language for ALL fenced code blocks** to resolve MD040/fenced-code-language warnings
- Use specific language identifiers (bash, python, javascript, yaml, toml, json, etc.) for every ```code``` block
- For generic text or output, use ```text``` instead of leaving language unspecified
- **Ensure files end with a single newline character** to resolve MD047/single-trailing-newline warnings
- Surround code blocks and lists with blank lines to meet MD031 and MD032 requirements
- **MD032/blanks-around-lists**: Lists should be surrounded by blank lines

## Vercel-Mem0 Memory Best Practices

### Core MCP Vercel-Mem0 Tools

**Available Tools:**

- `mcp__vercel-mem0__add_memory` - Add new memory with content string and optional user_id
- `mcp__vercel-mem0__search_memory` - Semantic search with query and optional limit
- `mcp__vercel-mem0__get_memories` - Get memories by query or get all memories with optional limit
- `mcp__vercel-mem0__retrieve_context` - Retrieve memory context for specific question or scenario

### Memory Structure

Each memory contains:

- **Content**: Text content (required string parameter)
- **ID**: Auto-generated UUID for unique identification
- **Relevance**: Semantic relevance score when searching (0.0-1.0 range)

### Best Practices for Effective Usage

#### Adding Memories

- **Be specific and descriptive**: Include context, action, and outcome
- **Use consistent formatting**: "Action: Result/Context/Details"
- **Include key metadata**: dates, versions, file paths, error codes
- **Example**: `"Fixed CORS configuration in app/main.py:35-41 - changed from allow_origins=['*'] to specific domains for security"`

#### Searching Memories

- **Use semantic queries**: Search by meaning, not just keywords
- **Combine context terms**: "authentication error JWT token"
- **Trust relevance scores**: 0.6+ usually indicates good matches, 0.4+ for broader context
- **Iterate searches**: Refine queries based on initial results

#### Memory Management

- **Avoid duplicate entries**: Search before adding similar content
- **Use structured content**: Include technical details like file paths, line numbers, error messages
- **Regular cleanup**: Use delete-all-memories sparingly and only when starting fresh
- **Context preservation**: Include enough detail for future reference

#### Security and Privacy

- **No sensitive data**: Never store API keys, passwords, or secrets in memory
- **Anonymize when possible**: Replace specific credentials with placeholders
- **User preferences**: Store user preferences and coding style decisions
- **Project context**: Remember architectural decisions and implementation patterns

#### Integration Patterns

- **Proactive memory**: Store important decisions and fixes immediately
- **Cross-session context**: Use memory to maintain context across different work sessions
- **Error tracking**: Remember common errors and their solutions
- **User preferences**: Store coding preferences, commit guidelines, style choices

### Memory Categories to Track

1. **User Preferences**: Coding style, commit format, architectural choices
2. **Technical Decisions**: Library choices, pattern implementations, configuration settings
3. **Problem Solutions**: Bug fixes, error resolutions, workarounds
4. **Project Context**: Architecture understanding, database schemas, API patterns
5. **Workflow Patterns**: Development processes, testing approaches, deployment steps

### Memory Lifecycle Management

#### Proactive Cleanup Strategies

- **Temporal Relevance Check**: Before using memory, verify timestamps and version relevance
- **Context Validation**: Ensure remembered context matches current project state
- **Outdated Detection**: Flag memories containing deprecated packages, obsolete APIs, or changed file structures
- **Automatic Cleanup**: Remove memories contradicted by new evidence

#### Memory Maintenance Patterns

```bash
# Memory freshness validation patterns:
# 1. Version-based cleanup
- "Fixed issue X in version Y" → outdated when version Z released
- "Library A version 1.0 configuration" → outdated when upgraded to 2.0

# 2. Context drift detection  
- "File located at path/old/structure" → outdated when project restructured
- "Authentication uses JWT tokens" → outdated when switched to OAuth

# 3. Resolution supersession
- "Temporary workaround for bug B" → outdated when proper fix implemented
- "Manual process for task T" → outdated when automation added
```

#### Best Practices for Memory Currency

**Detection Triggers:**

- Version changes in dependencies (`package.json`, `pyproject.toml` updates)
- File structure modifications (directories moved/renamed)
- Architecture changes (new patterns adopted, old ones deprecated)
- Tool/framework upgrades (Python 3.11 → 3.12, FastAPI v1 → v2)

**Cleanup Actions:**

- **Search conflicting memories**: Find outdated entries before adding new ones
- **Replace vs. Supplement**: Replace outdated information rather than adding conflicting entries  
- **Version tagging**: Include version numbers in memory content for future validation
- **Explicit invalidation**: Note when previous approaches are deprecated

**Memory Maintenance Workflow:**

1. **Before adding**: Search for existing related memories
2. **During conflicts**: Identify which memory is more current
3. **After changes**: Update dependent memories that reference changed elements
4. **Periodic review**: Clean memories referencing obsolete tools/versions

#### Obsolescence Indicators

**Code-level Changes:**

- Import statement modifications
- Configuration file schema updates  
- API endpoint changes
- Database schema migrations

**Project-level Changes:**

- Tool version upgrades
- Architecture pattern shifts
- Process improvements
- Team workflow changes

#### Memory Validation Examples

```python
# Good: Version-aware memory
"Fixed CORS in app/main.py:35-41 for FastAPI 0.110.0 - changed allow_origins=['*'] to specific domains"

# Good: Context-aware memory  
"Database connection pool configured in app/core/config.py:44 using Supabase client v2.x async pattern"

# Bad: Version-agnostic memory
"Fixed CORS problem by changing settings" # Too vague, no context

# Bad: Potentially outdated
"Temporary fix for authentication bug" # No indication when it should be replaced
```

### Proactive Memory Usage Rules

#### Automatic Memory Triggers

**CRITICAL BEHAVIORAL PATTERN**: When user mentions previous work or context, IMMEDIATELY use `mcp__vercel-mem0__search_memory` FIRST before responding. Don't wait for explicit instruction to use memory tools.

**Trigger Phrases for Automatic Memory Search:**

- Russian: "освежи память", "вспомни что было", "давай вспомним", "чем мы занимались", "что делали раньше", "предыдущая работа", "до этого", "помнишь", "мы работали с", "продолжаем с того места"
- English: "remember what we did", "refresh memory", "recall previous work", "what were we working on", "continue from where we left", "previous session"

**Expected Behavior:**

1. User mentions context/history → Immediately search memory
2. Use search results to provide informed response
3. Don't ask user to specify memory usage - it should be automatic

**Memory Search Strategy:**

- Use semantic queries combining context keywords
- Trust relevance scores (0.6+ for strong matches)
- Include search results in response context
