# Astroloh Agent Skills Configuration

This file defines specialized agents (skills) for Claude Code and other AI assistants working with the Astroloh project.

## 📚 Core Documentation

Before using any agent, always read:

- `CLAUDE.md` - Complete project guidelines and architecture
- `PROJECT_MEMORY.md` - Current project state and context
- `.cursorrules` - Quick reference rules for Cursor AI
- `README.md` - Project overview and setup instructions

## 🤖 Available Agents

### 1. Astrology Backend Expert

**Name:** `astrology-backend`

**Description:** Use this agent for astronomical calculations, Kerykeion integration, and multi-backend fallback systems. Specializes in natal charts, transits, progressions, synastry, and Arabic parts.

**When to use:**

- Working with `app/services/kerykeion_service.py`
- Debugging astronomical calculation issues
- Implementing new astrological features
- Optimizing calculation performance
- Adding fallback mechanisms

**Key expertise:**

- Kerykeion 4.x API and configuration
- Swiss Ephemeris integration
- Skyfield astronomical calculations
- House systems (Placidus, Koch, Equal, etc.)
- Aspect calculation with orbs
- Russian astrological terminology

**Example usage:**

```text
@astrology-backend I need to add Moon phases to natal chart calculations
@astrology-backend Fix the fallback mechanism when Kerykeion service is unavailable
@astrology-backend Implement Vedic astrology house system support
```

**Commands:**

```bash
/test app/services/kerykeion_service.py
/lint app/services/
/analyze-performance natal-chart-calculation
```

---

### 2. Russian Localization Expert

**Name:** `russian-localization`

**Description:** Use this agent for Russian language localization, grammatical declensions, TTS optimization, and cultural adaptation. Specializes in all 6 Russian grammatical cases and voice interface optimization.

**When to use:**

- Working with `app/services/russian_astrology_adapter.py`
- Generating Russian astrological text
- Fixing grammatical errors in responses
- Optimizing Alice TTS output
- Cultural adaptation of interpretations

**Key expertise:**

- Russian grammatical cases (именительный, родительный, дательный, винительный, творительный, предложный)
- TTS stress marks and pronunciation
- Zodiac sign declensions
- Voice preprocessing for speech recognition
- Russian astrological terminology
- Cultural context and traditions

**Example usage:**

```text
@russian-localization Fix grammatical cases in compatibility response
@russian-localization Optimize this horoscope text for Alice voice
@russian-localization Add proper stress marks for TTS pronunciation
```

**Commands:**

```bash
/test app/services/russian_astrology_adapter.py
/generate-horoscope leo --language ru --optimize-tts
/validate-declensions
```

---

### 3. Alice Voice Interface Expert

**Name:** `alice-voice`

**Description:** Use this agent for Yandex Alice integration, intent recognition, dialog flow, and response formatting. Specializes in Alice API constraints, webhook handling, and voice optimization.

**When to use:**

- Working with `app/api/yandex_dialogs.py`
- Debugging intent recognition issues
- Implementing new voice commands
- Fixing Alice response formatting
- Optimizing dialog flow

**Key expertise:**

- Yandex Dialogs API protocol
- Intent recognition patterns
- Entity extraction (dates, zodiac signs)
- Response constraints (800 chars horoscopes, 600 chars compatibility)
- Button limits (maximum 5 buttons)
- Session management
- Voice command preprocessing

**Example usage:**

```text
@alice-voice Add new intent for lunar calendar queries
@alice-voice Fix response exceeding Alice character limit
@alice-voice Improve intent recognition accuracy for compatibility queries
```

**Commands:**

```bash
/test app/api/yandex_dialogs.py
/test-webhook --intent horoscope --sign leo
/validate-response-constraints
```

---

### 4. Time & Timezone Expert

**Name:** `time-timezone`

**Description:** Use this agent for time handling, timezone management, datetime validation, and coordinate-based calculations. Specializes in `astro_time_utils.py` and astrological time precision.

**When to use:**

- Working with `app/utils/astro_time_utils.py`
- Debugging timezone conversion issues
- Implementing birth time validation
- Fixing datetime parsing errors
- Coordinate-based timezone detection

**Key expertise:**

- Python `zoneinfo` and timezone management
- Russian city timezone mappings
- Coordinate-based timezone detection
- Local solar time calculations
- Historical date support (1000-3000 CE)
- Security validation and sanitization
- Multi-format datetime parsing

**Example usage:**

```text
@time-timezone Add support for new Russian city timezones
@time-timezone Fix birth time validation for historical dates
@time-timezone Implement daylight saving time handling
```

**Commands:**

```bash
/test tests/test_astro_time_utils.py
/validate-timezone-mappings
/test-date-parsing --format "dd.mm.yyyy HH:MM"
```

**Critical rules:**

- NEVER import `datetime` directly in any file except `astro_time_utils.py`
- Always use `from app.utils.astro_time_utils import utcnow, now`
- Use `db_timestamp_default()` for SQLAlchemy defaults

---

### 5. AI Consultation Expert

**Name:** `ai-consultation`

**Description:** Use this agent for Yandex GPT integration, AI-powered astrological consultations, prompt engineering, and content safety. Specializes in AI interpretation generation and quality control.

**When to use:**

- Working with `app/services/ai_horoscope_service.py` or `astro_ai_service.py`
- Debugging Yandex GPT API issues
- Implementing new AI consultation types
- Optimizing prompt engineering
- Content safety filtering

**Key expertise:**

- Yandex GPT API integration
- Prompt engineering for astrological interpretations
- Context-aware AI consultations
- Content safety filtering
- Russian cultural adaptation
- AI confidence scoring
- Fallback mechanisms

**Example usage:**

```text
@ai-consultation Improve prompt for career consultation
@ai-consultation Add content safety check for AI responses
@ai-consultation Optimize AI consultation performance
```

**Commands:**

```bash
/test app/services/ai_horoscope_service.py
/test-ai-consultation --type career --sign virgo
/validate-prompt-effectiveness
```

---

### 6. Performance & Caching Expert

**Name:** `performance-cache`

**Description:** Use this agent for Redis caching, performance monitoring, async optimization, and resource management. Specializes in cache strategies and performance optimization.

**When to use:**

- Working with `app/services/astro_cache_service.py`
- Debugging cache hit rate issues
- Implementing new caching strategies
- Optimizing async operations
- Performance monitoring

**Key expertise:**

- Redis caching patterns
- TTL strategies (natal charts: 30d, transits: 1h)
- Cache warming and pre-computation
- Async/await patterns
- Performance monitoring
- Memory optimization
- Background task scheduling

**Example usage:**

```text
@performance-cache Implement cache warming for popular birth dates
@performance-cache Fix cache invalidation on data updates
@performance-cache Optimize Redis memory usage
```

**Commands:**

```bash
/test app/services/astro_cache_service.py
/analyze-cache-hit-rate
/monitor-performance --duration 1h
```

**Performance targets:**

- Cached requests: <500ms
- Complex calculations: <2s
- Alice interface: <5s maximum

---

### 7. Testing & Quality Expert

**Name:** `testing-qa`

**Description:** Use this agent for test implementation, coverage analysis, mocking strategies, and quality assurance. Specializes in pytest, async testing, and integration tests.

**When to use:**

- Writing new tests
- Improving test coverage
- Debugging failing tests
- Implementing mocking strategies
- Integration testing

**Key expertise:**

- Pytest framework and markers
- Async testing with pytest-asyncio
- Mocking external services
- Test coverage analysis
- Unit vs integration test design
- Test data factories
- Fixture management

**Example usage:**

```text
@testing-qa Add tests for new synastry feature with 80% coverage
@testing-qa Fix failing async tests in test_kerykeion.py
@testing-qa Implement mocks for Yandex GPT API
```

**Commands:**

```bash
/test --coverage --target 80
/test -m unit
/test -m integration
/generate-coverage-report
```

---

### 8. Database & Migration Expert

**Name:** `database-migrations`

**Description:** Use this agent for PostgreSQL schema design, Alembic migrations, database optimization, and data model design. Specializes in SQLAlchemy ORM and database performance.

**When to use:**

- Creating database migrations
- Optimizing database queries
- Designing data models
- Debugging database issues
- Index optimization

**Key expertise:**

- PostgreSQL database design
- Alembic migration scripts
- SQLAlchemy ORM patterns
- Database indexing strategies
- Query optimization
- Connection pooling
- Async database operations

**Example usage:**

```text
@database-migrations Create migration for new astrological aspect table
@database-migrations Optimize slow query in natal chart retrieval
@database-migrations Add database indexes for performance
```

**Commands:**

```bash
/create-migration --message "Add aspect_orbs table"
/upgrade-database
/analyze-query-performance
```

---

### 9. Security & GDPR Expert

**Name:** `security-gdpr`

**Description:** Use this agent for security validation, GDPR compliance, data encryption, and sensitive data handling. Specializes in personal data protection and security best practices.

**When to use:**

- Implementing data encryption
- GDPR compliance reviews
- Security audit fixes
- Sensitive data handling
- JWT token management

**Key expertise:**

- Personal data encryption
- GDPR compliance requirements
- JWT token security
- Input validation and sanitization
- Secure password handling
- Data retention policies
- Security logging

**Example usage:**

```text
@security-gdpr Review encryption implementation for birth data
@security-gdpr Implement GDPR data export feature
@security-gdpr Add security validation for user inputs
```

**Commands:**

```bash
/security-audit
/validate-encryption
/check-gdpr-compliance
```

**Critical security rules:**

- Never log API keys, secrets, or personal astrological data
- All user datetime inputs must go through `parse_birth_datetime()`
- Use encryption utilities for storing personal birth data

---

## 🔧 Agent Usage Guidelines

### General workflow:

1. **Identify the domain** of your task (astrology, localization, testing, etc.)
2. **Tag the appropriate agent** with `@agent-name` in your prompt
3. **Be specific** about what you need: files, functions, expected behavior
4. **Include context** about the current problem or feature request
5. **Specify test requirements** if applicable (80% coverage target)

### Multi-agent collaboration:

For complex tasks involving multiple domains, you can tag multiple agents:

```text
@astrology-backend @time-timezone Implement birth chart calculation with proper timezone handling and coordinate-based detection

@alice-voice @russian-localization Fix horoscope response to respect Alice character limits and Russian grammatical cases

@performance-cache @testing-qa Add Redis caching for natal charts with comprehensive tests
```

### Agent interaction patterns:

**Sequential work:**

```text
1. @database-migrations Create migration for new feature
2. @testing-qa Add tests for the new data model
3. @security-gdpr Review data encryption implementation
```

**Parallel work (independent tasks):**

```text
- @astrology-backend: Implement new aspect calculations
- @russian-localization: Update terminology for new aspects
- @testing-qa: Write tests for both features
```

### Best practices:

✅ **DO:**

- Always specify which files/modules you're working with
- Include error messages or logs when debugging
- Specify desired test coverage percentage
- Mention performance requirements
- Reference existing patterns in codebase

❌ **DON'T:**

- Mix unrelated concerns in one agent request
- Skip testing requirements
- Ignore existing architectural patterns
- Forget to check CLAUDE.md for project guidelines

### Example session:

```text
User: We need to add a new feature for calculating planetary hours

@astrology-backend Can you implement planetary hours calculation using Kerykeion? 
Follow the existing multi-backend pattern with fallbacks.

@time-timezone Ensure proper timezone and local solar time handling for accurate calculations.

@russian-localization Add Russian translations for planetary hour names and descriptions.

@testing-qa Write comprehensive tests with 80% coverage, mock external services.

@performance-cache Implement Redis caching with 1-hour TTL for planetary hour data.
```

## 📊 Agent Performance Metrics

Track agent effectiveness:

- **Task completion rate**: % of tasks successfully completed
- **Code quality**: Test coverage, linting compliance
- **Response accuracy**: Adherence to project guidelines
- **Context awareness**: Proper use of existing patterns

## 🔄 Agent Skill Updates

This file should be updated when:

- New project domains are added
- Agent expertise areas expand
- Best practices evolve
- New tools or frameworks are integrated

**Last updated:** 2024-12-03

**Version:** 1.0.0

---

## 📖 Related Documentation

- `CLAUDE.md` - Complete project documentation
- `.cursorrules` - Quick reference rules
- `README.md` - Project overview
- `PROJECT_MEMORY.md` - Current project context
- `CONTRIBUTING.md` - Contribution guidelines
