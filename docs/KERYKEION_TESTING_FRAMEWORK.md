# Comprehensive Kerykeion Testing Framework

## Overview

This document describes the comprehensive testing framework developed for the Astroloh project's Kerykeion integration. The framework ensures reliability, accuracy, and performance of all astrological calculations and voice interface features.

## Table of Contents

1. [Testing Architecture](#testing-architecture)
2. [Test Categories](#test-categories)
3. [Service-Specific Tests](#service-specific-tests)
4. [Accuracy Validation](#accuracy-validation)
5. [Performance Testing](#performance-testing)
6. [Integration Testing](#integration-testing)
7. [Localization Testing](#localization-testing)
8. [Running Tests](#running-tests)
9. [Coverage Requirements](#coverage-requirements)
10. [Continuous Integration](#continuous-integration)

## Testing Architecture

### Framework Structure

```
tests/
├── test_kerykeion_service.py           # KerykeionService unit tests
├── test_async_kerykeion_service.py     # Async wrapper tests
├── test_enhanced_transit_service.py    # Transit service tests
├── test_russian_astrology_adapter.py   # Russian localization tests
├── test_astrological_accuracy.py       # Accuracy validation with known data
├── test_yandex_alice_integration.py    # Alice voice interface tests
├── test_kerykeion_performance_load.py  # Performance and load tests
└── conftest.py                         # Shared fixtures and configuration
```

### Test Markers

The framework uses pytest markers for test categorization:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests across services
- `@pytest.mark.performance` - Performance benchmarking tests
- `@pytest.mark.security` - Security and input validation tests
- `@pytest.mark.slow` - Long-running tests (excluded from CI by default)
- `@pytest.mark.skipif(not KERYKEION_AVAILABLE)` - Tests requiring Kerykeion

### Running Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run performance tests
pytest -m performance

# Skip slow tests
pytest -m "not slow"

# Run all tests
pytest
```

## Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Coverage**:
- Service initialization and configuration
- Method inputs/outputs validation
- Error handling and edge cases
- Enum definitions and data structures
- Caching mechanisms

**Example**:
```python
def test_kerykeion_service_initialization():
    service = KerykeionService()
    assert service.is_available() == KERYKEION_AVAILABLE
    
def test_house_system_enum_values():
    expected_systems = ["Placidus", "Koch", "Equal", "Whole Sign"]
    for system in expected_systems:
        assert any(hs.value == system for hs in HouseSystem)
```

### 2. Integration Tests

**Purpose**: Test component interactions and end-to-end workflows

**Coverage**:
- Service-to-service communication
- Database integration
- External API integration (Yandex GPT)
- Webhook processing pipeline
- Session management

**Example**:
```python
async def test_webhook_horoscope_flow():
    alice_request = create_alice_request("дай гороскоп для льва")
    response = await handle_yandex_request(alice_request)
    
    assert "response" in response
    assert len(response["response"]["text"]) <= 800  # Alice limit
```

### 3. Performance Tests

**Purpose**: Validate system performance under various conditions

**Coverage**:
- Response time requirements (Alice: <3-5 seconds)
- Memory usage stability
- Concurrent operation handling
- Caching efficiency
- Load testing scenarios

**Example**:
```python
def test_chart_calculation_performance():
    calculation_times = []
    for _ in range(10):
        start_time = time.perf_counter()
        chart_data = service.get_full_natal_chart_data(...)
        end_time = time.perf_counter()
        calculation_times.append(end_time - start_time)
    
    avg_time = statistics.mean(calculation_times)
    assert avg_time < 3.0, f"Average calculation too slow: {avg_time}s"
```

### 4. Security Tests

**Purpose**: Validate input sanitization and security measures

**Coverage**:
- SQL injection prevention
- XSS attack prevention
- Input validation for malicious data
- Coordinate boundary validation
- Voice input sanitization

## Service-Specific Tests

### KerykeionService Tests

**File**: `test_kerykeion_service.py`

**Test Classes**:
- `TestKerykeionServiceInit` - Initialization and availability
- `TestKerykeionServiceWithKerykeion` - Full functionality (when available)
- `TestKerykeionServiceWithoutKerykeion` - Fallback behavior
- `TestKerykeionServiceAdvancedFeatures` - Synastry, progressions
- `TestKerykeionServicePerformance` - Performance benchmarks
- `TestKerykeionServiceSecurity` - Security validation

**Key Features Tested**:
- Astrological subject creation
- Full natal chart calculation
- House system support (10 systems)
- Zodiac type support (Tropical/Sidereal)
- Aspect color coding
- Arabic parts calculation
- Error handling and graceful fallbacks

### AsyncKerykeionService Tests

**File**: `test_async_kerykeion_service.py`

**Test Classes**:
- `TestAsyncKerykeionServiceInit` - Service initialization
- `TestAsyncKerykeionServiceAsync` - Async functionality
- `TestAsyncKerykeionServicePerformanceStats` - Performance monitoring
- `TestAsyncKerykeionServiceWithoutKerykeion` - Fallback behavior
- `TestAsyncKerykeionServiceRealPerformance` - Real-world performance
- `TestAsyncKerykeionServiceIntegration` - Integration validation

**Key Features Tested**:
- Thread pool execution (4 workers)
- Batch processing capabilities
- Performance statistics tracking
- Cache integration
- Concurrent operation handling
- Error recovery mechanisms

### Enhanced Transit Service Tests

**File**: `test_enhanced_transit_service.py`

**Test Classes**:
- `TestEnhancedTransitServiceInit` - Service initialization
- `TestEnhancedTransitServiceAsync` - Async transit calculations
- `TestEnhancedTransitServiceCaching` - Cache optimization
- `TestEnhancedTransitServiceWithKerykeion` - Full Kerykeion features
- `TestEnhancedTransitServiceFallback` - Fallback mechanisms
- `TestEnhancedTransitServicePerformance` - Performance validation

**Key Features Tested**:
- Current transits calculation
- Period forecasts (7, 30, custom days)
- Important transits detection
- Energy pattern analysis
- Timing recommendations
- Professional Kerykeion integration

### Russian Localization Tests

**File**: `test_russian_astrology_adapter.py`

**Test Classes**:
- `TestRussianZodiacSignEnum` - Zodiac sign declensions
- `TestRussianPlanetEnum` - Planet terminology
- `TestRussianTimezoneEnum` - Russian timezone support
- `TestRussianSignDescriptions` - Sign descriptions in Russian
- `TestVoiceOptimization` - TTS optimization
- `TestKerykeionIntegration` - Kerykeion data localization

**Key Features Tested**:
- All 6 Russian grammatical cases
- 11 Russian time zones
- Voice optimization for Alice TTS
- Stress mark dictionary (proper pronunciation)
- Cultural adaptation of interpretations
- Security validation for Russian input

## Accuracy Validation

### Astrological Accuracy Tests

**File**: `test_astrological_accuracy.py`

**Known Data Sources**:
- Famous historical figures (Einstein, Curie, da Vinci)
- Verified astronomical events
- Known moon phases (2023 data)
- Zodiac sign boundary dates

**Test Categories**:

#### 1. Zodiac Sign Accuracy
```python
def test_zodiac_sign_boundaries_accuracy():
    # Tests sign calculations at boundary dates
    # Validates cusp handling
    # Checks leap year accuracy
```

#### 2. Natal Chart Accuracy
```python
def test_famous_birth_chart_accuracy():
    # Einstein: Sun in Pisces ~23°
    # Curie: Sun in Scorpio ~14°
    # da Vinci: Sun in Aries ~26°
```

#### 3. Moon Phase Accuracy
```python
def test_known_new_moon_accuracy():
    # Validates against known new moon dates
    # Checks illumination percentages
    # Tests phase name accuracy
```

#### 4. Aspect Calculation Accuracy
```python
def test_major_aspect_detection():
    # Validates aspect orb calculations
    # Checks aspect type detection
    # Tests orb accuracy within 1-2 degrees
```

### Accuracy Benchmarks

- **Zodiac Sign**: 100% accuracy for non-cusp dates, ±1 day for cusps
- **Moon Phase**: ±5% illumination accuracy, correct phase names
- **Planetary Degrees**: ±5° accuracy for historical data
- **Aspect Orbs**: ±2° accuracy for major aspects

## Performance Testing

### Performance Requirements

**Alice Voice Interface Requirements**:
- Response time: <3-5 seconds maximum
- Memory usage: <500MB per operation
- Concurrent users: Support 10+ simultaneous requests
- Cache hit rate: >60% for popular data

**Performance Test Categories**:

#### 1. Single Operation Performance
```python
def test_single_chart_calculation_performance():
    # Target: <3 seconds average
    # Acceptable: <5 seconds worst case
```

#### 2. Batch Operation Performance
```python
def test_batch_calculation_performance():
    # Target: <4 seconds per chart in batch
    # Acceptable: 80%+ success rate
```

#### 3. Concurrent Load Performance
```python
def test_concurrent_calculation_performance():
    # Target: 10 concurrent operations
    # Acceptable: <10 seconds total time
```

#### 4. Memory Stability
```python
def test_memory_usage_stability():
    # Target: <50MB increase after 20 operations
    # Acceptable: No memory leaks detected
```

### Performance Monitoring

The framework includes built-in performance monitoring:

```python
# Automatic performance tracking
stats = async_service.get_performance_stats()
print(f"Operations: {stats['total_operations']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"Average time: {stats['average_calculation_time']:.3f}s")
```

## Integration Testing

### Yandex Alice Integration

**File**: `test_yandex_alice_integration.py`

**Test Categories**:

#### 1. Webhook Processing
- Complete request/response pipeline
- Intent recognition accuracy
- Entity extraction validation
- Error handling and fallbacks

#### 2. Voice Interface Optimization
- TTS text optimization (remove symbols, etc.)
- Character limits (800 chars for horoscopes)
- Button constraints (5 buttons max)
- Russian voice patterns

#### 3. AI Integration
- Yandex GPT request/response handling
- Fallback to traditional horoscopes
- Content safety filtering
- Specialized consultation types

#### 4. Conversation Flow
- Multi-turn conversations
- Context persistence
- Session timeout handling
- Conversation state management

### Voice Command Testing

**Supported Commands**:
```python
VOICE_COMMANDS = {
    "greetings": ["привет", "здравствуй", "добро утро"],
    "horoscopes": ["дай гороскоп для льва", "гороскоп овна"],
    "compatibility": ["совместимость льва и овна", "синастрия"],
    "transits": ["что меня ждет сегодня", "прогноз на неделю"],
    "ai_features": ["карьерный совет", "любовная консультация"]
}
```

## Localization Testing

### Russian Language Support

**Test Coverage**:
- Grammatical declensions (6 cases × 12 signs)
- Planet names and descriptions
- House system terminology
- Aspect names and descriptions
- Russian time zones (11 zones)
- Voice pronunciation optimization

### Timezone Testing

**Russian Cities Tested**:
- Москва (Europe/Moscow)
- Санкт-Петербург (Europe/Moscow) 
- Екатеринбург (Asia/Yekaterinburg)
- Новосибирск (Asia/Novosibirsk)
- Владивосток (Asia/Vladivostok)

## Running Tests

### Local Testing

```bash
# Install test dependencies
pip install -e ".[full,dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_kerykeion_service.py

# Run tests with specific marker
pytest -m "unit and not slow"

# Verbose output
pytest -v -s

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

### Docker Testing

```bash
# Run tests in Docker environment
docker-compose -f docker-compose.dev.yml run --rm backend pytest

# Run with coverage in Docker
docker-compose -f docker-compose.dev.yml run --rm backend pytest --cov=app
```

### Environment Variables for Testing

```bash
# Required for integration tests
export YANDEX_API_KEY="your_api_key"
export YANDEX_FOLDER_ID="your_folder_id"
export ENABLE_AI_GENERATION=true

# Optional for enhanced testing
export REDIS_URL="redis://localhost:6379/1"  # Use different DB for tests
```

## Coverage Requirements

### Target Coverage Levels

- **Overall Coverage**: 90% minimum
- **New Kerykeion Services**: 95% minimum
- **Critical Services**: 98% minimum
  - KerykeionService
  - AsyncKerykeionService
  - RussianAstrologyAdapter
  - Enhanced Transit Service

### Coverage Reporting

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View detailed coverage
open htmlcov/index.html

# Coverage by file
pytest --cov=app --cov-report=term-missing
```

### Coverage Exclusions

Lines excluded from coverage requirements:
```python
# pragma: no cover
def __repr__(self):  # String representations
    pass

if TYPE_CHECKING:  # Type checking imports
    pass

except ImportError:  # Optional dependency handling
    pass
```

## Continuous Integration

### CI Pipeline Integration

The testing framework integrates with GitHub Actions:

```yaml
name: Comprehensive Testing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -e ".[full,dev]"
      
      - name: Run unit tests
        run: pytest -m "unit and not slow" --cov=app
      
      - name: Run integration tests
        run: pytest -m "integration and not slow"
        env:
          YANDEX_API_KEY: ${{ secrets.YANDEX_API_KEY }}
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Quality Gates

**Required for PR Merge**:
- All unit tests pass
- Integration tests pass (with proper secrets)
- Coverage ≥90% for changed files
- No security test failures
- Performance regressions <50% slower than baseline

**Optional (Run on Schedule)**:
- Full performance test suite
- Load testing scenarios
- Extended accuracy validation
- Slow/long-running tests

## Best Practices

### Test Writing Guidelines

1. **Use descriptive test names**:
   ```python
   def test_kerykeion_service_creates_subject_with_correct_timezone()
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert):
   ```python
   def test_natal_chart_calculation():
       # Arrange
       service = KerykeionService()
       birth_data = {...}
       
       # Act
       result = service.get_full_natal_chart_data(**birth_data)
       
       # Assert
       assert "planets" in result
   ```

3. **Use fixtures for common setup**:
   ```python
   @pytest.fixture
   def sample_birth_data():
       return {
           "name": "Test Subject",
           "birth_datetime": datetime(1990, 8, 15, 14, 30),
           ...
       }
   ```

4. **Mock external dependencies**:
   ```python
   with patch('app.services.yandex_gpt.YandexGPTClient') as mock_gpt:
       mock_gpt.return_value.generate_response.return_value = "test"
   ```

5. **Test both success and failure scenarios**:
   ```python
   def test_service_with_invalid_data():
       with pytest.raises(ValueError):
           service.method_with_validation(invalid_data)
   ```

### Debugging Test Failures

1. **Use verbose output**: `pytest -v -s`
2. **Run single test**: `pytest tests/file.py::TestClass::test_method`
3. **Add debugging prints**: Use `print()` statements (shown with `-s`)
4. **Use pytest fixtures**: `pytest --fixtures` to list available fixtures
5. **Check coverage**: Missing coverage often indicates untested edge cases

### Performance Test Guidelines

1. **Use statistical analysis**: Multiple runs with mean/median/std dev
2. **Set realistic thresholds**: Based on actual requirements
3. **Monitor resource usage**: Memory, CPU, network
4. **Test different scenarios**: Small/large data, concurrent operations
5. **Include regression detection**: Compare against baselines

## Maintenance and Updates

### Regular Maintenance Tasks

1. **Monthly**: Review and update accuracy test data
2. **Quarterly**: Update performance baselines
3. **Semi-annually**: Review test coverage and add missing tests
4. **As needed**: Update tests when adding new features

### Known Issues and Limitations

1. **Historical Dates**: Some tests may fail for dates before 1900
2. **Timezone Changes**: Russian timezone definitions may change
3. **Kerykeion Updates**: New versions may change calculation results
4. **Performance Variations**: System load affects performance tests

### Contributing to the Test Framework

When adding new features:

1. Write tests first (TDD approach)
2. Ensure ≥95% coverage for new code
3. Add both positive and negative test cases
4. Include performance tests for critical paths
5. Update this documentation

For questions or issues with the testing framework, refer to the project's issue tracker or contact the development team.