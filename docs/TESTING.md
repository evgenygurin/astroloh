# Testing Documentation

This document describes the comprehensive testing strategy for the Astroloh Yandex Alice skill.

## Test Structure

### Test Categories

#### 1. Unit Tests
- **Location**: `tests/test_*.py`
- **Purpose**: Test individual components and functions in isolation
- **Coverage**: All service modules, utilities, and core functionality

#### 2. Integration Tests
- **Location**: `tests/test_integration_*.py`
- **Purpose**: Test component interactions and API endpoints
- **Coverage**: API endpoints, database operations, service integrations

#### 3. Performance Tests
- **Location**: `tests/test_performance.py`
- **Purpose**: Ensure optimal performance for critical operations
- **Coverage**: Astrological calculations, API response times, concurrent operations

#### 4. Workflow Tests
- **Location**: `tests/test_workflow_scenarios.py`
- **Purpose**: Test complete user interaction scenarios
- **Coverage**: End-to-end dialog flows, multi-turn conversations

## Test Files Overview

### Core Service Tests
- `test_astrology_calculator.py` - Astronomical calculations and zodiac operations
- `test_horoscope_generator.py` - Horoscope generation and personalization
- `test_natal_chart.py` - Natal chart calculations and interpretations
- `test_lunar_calendar.py` - Lunar calendar and moon phase calculations

### Dialog System Tests
- `test_dialog_handler.py` - Main dialog orchestration
- `test_dialog_flow_manager.py` - Dialog state management
- `test_conversation_manager.py` - Conversation context and personalization
- `test_intent_recognition.py` - Intent recognition and entity extraction
- `test_error_recovery.py` - Error handling and recovery strategies

### Security and Data Tests
- `test_security.py` - Encryption, user management, and GDPR compliance
- `test_validators.py` - Input validation and sanitization

### Integration and Performance Tests
- `test_integration_api.py` - API endpoint testing
- `test_performance.py` - Performance benchmarks
- `test_workflow_scenarios.py` - Complete user journeys

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_astrology_calculator.py

# Run specific test
pytest tests/test_astrology_calculator.py::TestAstrologyCalculator::test_get_zodiac_sign_by_date
```

### Test Categories
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only performance tests
pytest -m performance

# Exclude slow tests
pytest -m "not slow"
```

### Coverage Reports
```bash
# Run tests with coverage
pytest --cov=app

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Generate XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Performance Testing
```bash
# Run performance tests only
pytest tests/test_performance.py -v

# Run with timing information
pytest --durations=10
```

## Test Configuration

### Environment Variables
Tests use the following environment variables:
- `ENVIRONMENT=testing` - Enables test mode
- `DATABASE_URL=sqlite:///:memory:` - In-memory database for tests
- `SECRET_KEY=test-secret-key-32-characters!!` - Test encryption key
- `ENCRYPTION_KEY=test-encryption-key-32-characters` - Test encryption key

### Pytest Configuration
Configuration is defined in `pytest.ini`:
- Async test support
- Coverage thresholds (80% minimum)
- Test markers for categorization
- Warning filters

### Fixtures
Common test fixtures are defined in `tests/conftest.py`:
- `mock_database` - Mock database session
- `mock_yandex_request` - Mock Yandex Alice request
- `mock_user_context` - Mock user conversation context
- `sample_birth_data` - Sample astrological data
- `mock_encryption_service` - Mock encryption operations

## Performance Benchmarks

### Target Performance Metrics

#### Astrological Calculations
- Zodiac sign calculation: > 10,000 ops/sec
- Planetary positions: < 40ms per calculation
- Compatibility analysis: < 4ms per calculation
- Horoscope generation: < 10ms per generation

#### API Response Times
- Simple requests (greeting): < 100ms
- Horoscope requests: < 500ms
- Complex calculations (natal chart): < 2000ms

#### Concurrent Operations
- Support for 50+ concurrent users
- No memory leaks during extended operation
- Graceful degradation under load

## Continuous Integration

### GitHub Actions Workflow
The test workflow (`.github/workflows/test.yml`) includes:

1. **Linting and Code Quality**
   - Black code formatting
   - isort import sorting
   - flake8 style checking
   - mypy type checking

2. **Unit and Integration Tests**
   - Full test suite execution
   - Coverage reporting
   - Artifact generation

3. **Security Checks**
   - Bandit security analysis
   - Safety vulnerability scanning

4. **Performance Testing**
   - Dedicated performance test job
   - Benchmark validation

### Coverage Requirements
- Minimum 80% code coverage
- All new code must include tests
- Critical paths require 100% coverage

## Test Data and Mocking

### Mock Strategy
- External services (Swiss Ephemeris) are mocked for unit tests
- Database operations use in-memory SQLite
- API calls use TestClient for integration tests

### Test Data
- Sample birth data for various scenarios
- Predefined horoscope templates
- Mock user interaction patterns
- Error condition simulations

## Best Practices

### Writing Tests
1. **Descriptive Names**: Test names should clearly describe what is being tested
2. **Single Responsibility**: Each test should verify one specific behavior
3. **Isolation**: Tests should not depend on each other
4. **Readable Assertions**: Use clear, specific assertions

### Test Organization
1. **Logical Grouping**: Group related tests in the same file
2. **Setup/Teardown**: Use fixtures for common setup
3. **Error Testing**: Include negative test cases
4. **Edge Cases**: Test boundary conditions

### Performance Considerations
1. **Realistic Data**: Use representative data sizes
2. **Timing Measurements**: Include specific performance targets
3. **Resource Cleanup**: Ensure tests don't leak resources
4. **Concurrent Testing**: Verify thread safety

## Troubleshooting

### Common Issues

#### Test Database Issues
```bash
# Reset test database
rm -f test.db
alembic upgrade head
```

#### Coverage Issues
```bash
# Check which lines are not covered
pytest --cov=app --cov-report=term-missing
```

#### Performance Test Failures
- Check system load during testing
- Verify no background processes affecting timing
- Review performance targets for relevance

### Debugging Tests
```bash
# Run with debugging output
pytest -s -vv

# Drop into debugger on failure
pytest --pdb

# Run specific failing test
pytest tests/test_file.py::test_function -vv
```

## Future Enhancements

### Planned Improvements
1. **Load Testing**: Add comprehensive load testing scenarios
2. **Chaos Engineering**: Introduce fault injection testing
3. **Security Testing**: Expand security vulnerability testing
4. **User Journey Testing**: Add more complex user interaction scenarios

### Monitoring Integration
1. **Test Metrics**: Track test execution times and success rates
2. **Coverage Trends**: Monitor coverage changes over time
3. **Performance Trends**: Track performance benchmark evolution
4. **Quality Gates**: Automated quality gates in CI/CD pipeline