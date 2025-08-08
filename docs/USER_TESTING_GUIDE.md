# User Testing Guide: Kerykeion Integration

## Overview

This guide helps developers and QA testers manually validate the Kerykeion integration features in the Astroloh voice skill for Yandex Alice.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Testing Environment Setup](#testing-environment-setup)
3. [Voice Interface Testing](#voice-interface-testing)
4. [Astrological Features Testing](#astrological-features-testing)
5. [Russian Localization Testing](#russian-localization-testing)
6. [Performance Testing](#performance-testing)
7. [Error Scenarios Testing](#error-scenarios-testing)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- Yandex Alice device or Yandex Station
- Yandex Developer Console access
- Postman or curl for API testing
- Browser for web interface testing

### Required Knowledge

- Basic understanding of astrology (zodiac signs, houses, aspects)
- Familiarity with Russian language (for localization testing)
- Understanding of voice interface constraints

### Test Data

Common test cases to use:
- **Birth Date**: August 15, 1990, 14:30 Moscow time
- **Zodiac Signs**: Leo, Aries, Cancer, Scorpio
- **Cities**: Moscow, St. Petersburg, Yekaterinburg, Vladivostok

## Testing Environment Setup

### 1. Local Development Setup

```bash
# Clone and setup
git clone <repository>
cd astroloh

# Install with full features
pip install -e ".[full,dev]"

# Set environment variables
export YANDEX_API_KEY="your_api_key"
export YANDEX_FOLDER_ID="your_folder_id" 
export ENABLE_AI_GENERATION=true

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Docker Setup

```bash
# Build and run with docker-compose
docker-compose -f docker-compose.dev.yml up --build

# Check logs for errors
docker-compose -f docker-compose.dev.yml logs backend
```

### 3. Health Check

```bash
# Test API health
curl http://localhost:8000/health

# Expected response:
{"status": "healthy", "timestamp": "..."}
```

## Voice Interface Testing

### Basic Voice Commands

#### Greeting Tests
Say to Alice:
- "Привет, Астролог"
- "Здравствуй"
- "Добро утро"
- "Помоги с астрологией"

**Expected**: Friendly greeting, introduction to capabilities

#### Horoscope Tests
Say to Alice:
- "Дай гороскоп для Льва"
- "Гороскоп Овна на сегодня" 
- "Что говорят звезды Льву?"
- "Расскажи про гороскоп"

**Expected**: 
- Personalized horoscope (if AI enabled)
- Energy level (1-100%)
- Lucky numbers and colors
- Response length ≤800 characters
- Russian language output

#### Compatibility Tests
Say to Alice:
- "Совместимость Льва и Овна"
- "Подходит ли Дева Скорпиону?"
- "Синастрия с партнером"
- "Что говорят звезды о наших отношениях?"

**Expected**:
- Compatibility percentage
- Strengths and challenges
- Relationship advice
- Response length ≤600 characters

#### Transit Tests (NEW)
Say to Alice:
- "Что меня ждет сегодня?"
- "Покажи транзиты"
- "Прогноз на неделю"
- "Важные транзиты"

**Expected**:
- Current planetary influences
- Period forecasts
- Energy analysis
- Timing recommendations

#### AI Consultation Tests (NEW)
Say to Alice:
- "Карьерный совет"
- "Любовная консультация"
- "Интерпретация натальной карты"
- "Духовная консультация"

**Expected** (if AI enabled):
- Specialized advice
- Professional interpretation
- Russian cultural context
- Content safety filtering

### Multi-Turn Conversation Testing

#### Scenario 1: Gradual Data Collection
1. Say: "Дай гороскоп"
2. Alice asks: "Какой у вас знак зодиака?"
3. Say: "Лев"
4. Alice provides Leo horoscope

#### Scenario 2: Context Persistence
1. Say: "Я Лев"
2. Alice: "Хорошо, запомнил"
3. Say: "Дай гороскоп"
4. Alice provides Leo horoscope without asking

#### Scenario 3: Partner Information
1. Say: "Совместимость с партнером"
2. Alice asks for your sign and partner's sign
3. Provide information step by step
4. Receive compatibility analysis

### Voice Quality Testing

#### TTS Optimization Tests
Test that responses are properly optimized for Text-to-Speech:

**Problematic Input**:
```
"Солнце в ♌ Льве на 22°30' с аспектом ⚹ к Луне"
```

**Expected TTS Output**:
```
"Солнце в Льве на двадцать два градуса тридцать минут с аспектом к Луне"
```

#### Russian Pronunciation Tests
Test proper stress marks for astrological terms:
- овéн (Aries)
- мерку́рий (Mercury)
- юпи́тер (Jupiter)
- астроло́гия (Astrology)

## Astrological Features Testing

### Natal Chart Features

#### Basic Natal Chart Test
Use API endpoint directly:
```bash
curl -X POST http://localhost:8000/api/v1/calculate-natal-chart \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "birth_date": "1990-08-15",
    "birth_time": "14:30",
    "birth_place": {
      "latitude": 55.7558,
      "longitude": 37.6176,
      "timezone": "Europe/Moscow"
    }
  }'
```

**Expected Response**:
```json
{
  "planets": {
    "sun": {"sign": "leo", "degree": 22.5, "house": 5},
    "moon": {"sign": "sagittarius", "degree": 15.3, "house": 9}
  },
  "houses": {...},
  "aspects": [...],
  "enhanced_features_available": true
}
```

#### House System Testing
Test different house systems:
- Placidus (default)
- Koch
- Equal House
- Whole Sign

#### Zodiac Type Testing
Test both zodiac types:
- Tropical (default)
- Sidereal

### Enhanced Features Testing

#### Arabic Parts Test
Check for Arabic parts in natal chart:
- Part of Fortune
- Part of Spirit
- Part of Love
- Part of Career

#### Aspect Color Coding Test
Verify aspects have proper colors:
- Conjunction: Red (#FF0000)
- Opposition: Blue (#0000FF)
- Trine: Green (#00FF00)
- Square: Orange (#FF8000)
- Sextile: Purple (#8000FF)

#### Transit Features Test
Test enhanced transit calculations:
- Current transits
- Period forecasts (7, 30 days)
- Important life transits
- Energy pattern analysis

## Russian Localization Testing

### Zodiac Signs in All Cases

Test Russian zodiac signs in different grammatical cases:

| English | Nominative | Genitive | Dative | Accusative | Instrumental | Prepositional |
|---------|------------|----------|--------|------------|--------------|---------------|
| Leo | Лев | Льва | Льву | Льва | Львом | Льве |
| Virgo | Дева | Девы | Деве | Деву | Девой | Деве |
| Gemini | Близнецы | Близнецов | Близнецам | Близнецов | Близнецами | Близнецах |

**Test Commands**:
- "Гороскоп для Льва" (genitive case)
- "Расскажи про Льва" (accusative case)  
- "Совместимость с Львом" (instrumental case)

### Russian Timezone Testing

Test timezone detection for Russian cities:

| City | Expected Timezone | UTC Offset |
|------|------------------|------------|
| Москва | Europe/Moscow | +03:00 |
| Екатеринбург | Asia/Yekaterinburg | +05:00 |
| Новосибирск | Asia/Novosibirsk | +07:00 |
| Владивосток | Asia/Vladivostok | +10:00 |

**Test Method**:
Use birth place with Russian city names and verify correct timezone handling.

### Planet Names Testing

Test Russian planet names:
- Солнце (Sun)
- Луна (Moon) 
- Меркурий (Mercury)
- Венера (Venus)
- Марс (Mars)
- Юпитер (Jupiter)
- Сатурн (Saturn)
- Уран (Uranus)
- Нептун (Neptune)
- Плутон (Pluto)

## Performance Testing

### Response Time Testing

#### Basic Performance Test
Measure response times for common operations:

```bash
# Time a horoscope request
time curl -X POST http://localhost:8000/api/v1/yandex/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "request": {"command": "дай гороскоп для льва"},
    "session": {"user_id": "test", "session_id": "test"},
    "version": "1.0"
  }'
```

**Expected**: Response within 3-5 seconds

#### Load Testing
Use multiple concurrent requests:

```bash
# Install Apache Bench
apt-get install apache2-utils

# Run load test (10 requests, 2 concurrent)
ab -n 10 -c 2 -T 'application/json' \
   -p request.json \
   http://localhost:8000/api/v1/yandex/webhook
```

**Expected**:
- 90% of requests complete within 5 seconds
- No errors under normal load
- Memory usage stable

### Memory Usage Testing

Monitor memory usage during extended operation:

```bash
# Monitor memory usage
top -p $(pgrep -f uvicorn)

# Or use docker stats
docker stats astroloh_backend_1
```

**Expected**:
- Memory usage stable over time
- No memory leaks detected
- Peak memory <1GB for normal operations

## Error Scenarios Testing

### Invalid Input Testing

#### Invalid Zodiac Signs
Test with non-existent zodiac signs:
- "Гороскоп для дракона"
- "Совместимость кота и собаки"

**Expected**: Graceful error handling, helpful error messages

#### Invalid Dates
Test with impossible dates:
- "Родился 32 января"
- "Дата рождения 2025-13-40"

**Expected**: Date validation errors, fallback to current date or request clarification

#### Invalid Coordinates
Test with out-of-range coordinates:
- Latitude > 90 or < -90
- Longitude > 180 or < -180

**Expected**: Coordinate validation, fallback to default location

### API Error Testing

#### Database Connection Errors
Simulate database unavailability:
```bash
# Stop database
docker-compose stop db

# Test API
curl http://localhost:8000/api/v1/yandex/webhook -d '{...}'
```

**Expected**: Graceful degradation, fallback responses

#### Yandex GPT API Errors
Disable AI generation:
```bash
export ENABLE_AI_GENERATION=false
```

**Expected**: Fallback to traditional horoscope generation

#### Missing Environment Variables
Remove required environment variables:
```bash
unset YANDEX_API_KEY
```

**Expected**: Clear error messages, fallback behavior

## Troubleshooting

### Common Issues

#### Issue: "Kerykeion not available"
**Symptoms**: Features missing, basic calculations only
**Solutions**:
1. Install Kerykeion: `pip install kerykeion>=4.11.0`
2. Check system requirements
3. Verify installation: `python -c "import kerykeion; print('OK')"`

#### Issue: "401 Unknown API key"
**Symptoms**: AI features not working, Yandex GPT errors
**Solutions**:
1. Check environment variables: `echo $YANDEX_API_KEY`
2. Verify API key in Yandex Console
3. Restart containers: `docker-compose restart`

#### Issue: Russian text not displaying correctly
**Symptoms**: Garbled Cyrillic characters
**Solutions**:
1. Check UTF-8 encoding
2. Verify locale settings: `locale -a | grep ru`
3. Check database charset

#### Issue: Slow response times
**Symptoms**: Responses taking >10 seconds
**Solutions**:
1. Check system resources: `htop`
2. Enable caching: Verify Redis connection
3. Check Kerykeion installation
4. Review logs for bottlenecks

#### Issue: Memory leaks
**Symptoms**: Memory usage constantly growing
**Solutions**:
1. Monitor with: `docker stats`
2. Check for unclosed connections
3. Review caching configuration
4. Restart services periodically

### Debug Commands

#### Check Service Status
```bash
# Check all services
curl http://localhost:8000/health

# Check specific service availability
python -c "
from app.services.kerykeion_service import KerykeionService
service = KerykeionService()
print(f'Kerykeion available: {service.is_available()}')
"
```

#### View Logs
```bash
# Application logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f db

# Specific service logs
docker-compose logs -f redis
```

#### Test Configuration
```bash
# Check environment variables
docker-compose exec backend env | grep -E "(YANDEX|ENABLE)"

# Test database connection
docker-compose exec backend python -c "
from app.core.database import get_database_session
import asyncio
async def test_db():
    async with get_database_session() as db:
        print('Database connection OK')
asyncio.run(test_db())
"
```

### Performance Debugging

#### Identify Bottlenecks
```bash
# Profile API request
pip install line_profiler

# Add @profile decorators to functions
# Run with: kernprof -l -v script.py
```

#### Memory Profiling
```bash
# Install memory profiler
pip install memory_profiler psutil

# Profile memory usage
python -m memory_profiler script.py
```

## Test Report Template

Use this template for documenting test results:

```markdown
# Test Report: Kerykeion Integration

**Date**: YYYY-MM-DD
**Tester**: Your Name
**Environment**: [Local/Docker/Production]
**Kerykeion Version**: [Available/Not Available]

## Voice Interface Tests
- [ ] Basic greetings ✓/✗
- [ ] Horoscope generation ✓/✗
- [ ] Compatibility analysis ✓/✗
- [ ] Transit features ✓/✗
- [ ] AI consultations ✓/✗

## Performance Tests
- Response time: X.X seconds (target: <5s)
- Memory usage: XXX MB (target: <1GB)
- Concurrent users: XX (target: >10)

## Issues Found
1. Issue description
   - Steps to reproduce
   - Expected vs actual behavior
   - Workaround (if any)

## Recommendations
- Priority fixes needed
- Performance optimizations
- User experience improvements
```

## Test Automation Integration

This manual testing guide complements the automated test suite. For continuous testing:

1. **Run automated tests first**: `pytest -m "unit and integration"`
2. **Manual validation**: Use this guide for edge cases and UX testing  
3. **Performance validation**: Run load tests before releases
4. **User acceptance testing**: Test with real Alice devices

The combination of automated and manual testing ensures comprehensive coverage of the Kerykeion integration features.