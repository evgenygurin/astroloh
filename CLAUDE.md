# Claude Development Guidelines

This file contains guidelines and instructions for Claude AI when working with the Astroloh project.

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

## Astronomical Calculation System

### Multi-Backend Architecture

**Priority System:**

1. **Kerykeion** >=4.11.0 (primary): Full professional features
2. **Swiss Ephemeris** (fallback): High precision calculations
3. **Skyfield** (fallback): Pure Python alternative
4. **Built-in** (fallback): Basic calculation methods

**Key Features:**

- Automatic fallback mechanisms for production reliability
- Professional-grade calculations with multiple house systems
- Support for all major and minor aspects with configurable orbs
- Comprehensive ephemeris data with intelligent caching

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

### Professional Astrology with Kerykeion

**Enhanced Capabilities:**

- Complete natal chart calculation with all planets including Chiron, Lilith
- Advanced aspect calculation with color coding
- Multiple house systems (Placidus, Koch, Equal, Whole Sign, etc.)
- Synastry calculations for relationship analysis
- Transit analysis with timing recommendations
- Arabic Parts (Lots) calculation

### AI-Powered Consultations

**AI Services:**

- Professional natal chart interpretations using Kerykeion data
- Specialized consultations (career, love, health, financial, spiritual)
- Enhanced compatibility analysis with AI interpretation
- Content safety filtering and quality control

### Russian Localization System

**Complete Localization:**

- Full Russian terminology for planets, signs, houses, aspects
- Grammatical declensions for all 6 Russian cases
- Support for all 11 Russian time zones with city detection
- Voice optimization with proper stress marks for TTS
- Cultural adaptation of astrological interpretations

### Performance Optimization

**Caching Strategy:**

- Redis-based caching with intelligent TTL policies
- Data-type specific expiration (natal charts: 30 days, transits: 1 hour)
- Background pre-computation for popular data
- Performance monitoring with configurable alerts

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

### Service Integration Patterns

**Multi-Backend Usage:**

```python
# Always check availability before using advanced features
if kerykeion_service.is_available():
    result = await kerykeion_service.calculate_natal_chart(...)
else:
    result = astrology_calculator.calculate_basic_chart(...)
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

## OpenMemory Best Practices

### Core MCP OpenMemory Tools

**Available Tools:**

- `mcp__openmemory__add-memory` - Add new memory with content string
- `mcp__openmemory__search-memories` - Semantic search with relevance scoring (0.0-1.0)
- `mcp__openmemory__list-memories` - List all memories with UUID and content
- `mcp__openmemory__delete-all-memories` - Delete all memories (DANGEROUS - use with caution!)

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

**CRITICAL BEHAVIORAL PATTERN**: When user mentions previous work or context, IMMEDIATELY use `mcp__openmemory__search-memories` FIRST before responding. Don't wait for explicit instruction to use memory tools.

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
