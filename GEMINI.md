# Gemini AI Development Guidelines

This file contains guidelines and instructions for Gemini AI when working with the Astroloh project.

## Project Overview

Astroloh is a sophisticated voice skill for Yandex Alice providing personalized astrological forecasts and consultations. The project leverages advanced astrological libraries including Kerykeion for professional-grade astronomical calculations.

## Enhanced Astrological Capabilities (2025-01-08)

### Kerykeion Integration

The project now features comprehensive integration with Kerykeion >=4.11.0, providing:

**Core Features:**
- Complete natal chart calculation with all traditional and modern planets
- Advanced aspect analysis with color coding and orb configuration
- Multiple house systems (Placidus, Koch, Equal, Whole Sign, Regiomontanus, Campanus, etc.)
- Support for both Tropical and Sidereal zodiac calculations
- Arabic Parts (Lots) calculation for deeper astrological analysis
- Professional chart shape analysis and planetary strength assessment
- SVG chart generation for visual representation
- Comprehensive synastry (compatibility) analysis

### Service Architecture

**Primary Services:**
1. `KerykeionService` - New professional astrological computation service
2. `AstrologyCalculator` - Multi-backend coordinator with automatic fallbacks
3. `NatalChartCalculator` - Enhanced natal chart service with Kerykeion integration
4. `HoroscopeGenerator` - AI-powered and traditional horoscope generation

**Backend Priority System:**
1. Kerykeion (primary) - Full professional features
2. Swiss Ephemeris (fallback) - High precision
3. Skyfield (fallback) - Pure Python
4. Built-in algorithms (fallback) - Basic functionality

### Development Approach for Gemini

**Code Analysis Best Practices:**
1. Understand the multi-backend architecture and fallback system
2. Recognize the comprehensive logging patterns (`KERYKEION_SERVICE_*`)
3. Appreciate the graceful degradation when libraries are unavailable
4. Consider the Russian language context and Yandex Alice voice interface requirements

**When Reviewing or Extending Code:**

1. **Astrological Accuracy**: Ensure calculations respect traditional and modern astrological principles
2. **Multi-Backend Support**: Maintain compatibility across all supported astronomical libraries
3. **Error Handling**: Always implement graceful fallbacks and proper error reporting
4. **Performance**: Consider computational complexity for real-time voice responses
5. **Russian Localization**: Maintain proper Russian language support throughout

### Key Technical Concepts

**Astronomical Calculations:**
- Julian Day calculations for precise timing
- Ecliptic coordinate systems for planetary positions
- House division systems and their mathematical foundations
- Aspect theory with configurable orbs and strength calculations
- Precession corrections for accurate star positions

**Astrological Concepts:**
- Tropical vs Sidereal zodiac systems
- Arabic Parts formulas and their meanings
- Synastry aspect interpretation
- Chart pattern recognition (Bowl, Bundle, Locomotive, etc.)
- Element and quality distribution analysis

### Integration Patterns

**Service Integration:**
```python
# Example of proper Kerykeion service usage
kerykeion_service = KerykeionService()

if kerykeion_service.is_available():
    chart_data = kerykeion_service.get_full_natal_chart_data(
        name=name,
        birth_datetime=datetime,
        latitude=lat,
        longitude=lon,
        house_system=HouseSystem.PLACIDUS,
        zodiac_type=ZodiacType.TROPICAL
    )
    
    if "error" not in chart_data:
        # Use enhanced features
        process_kerykeion_data(chart_data)
    else:
        # Fallback to basic calculator
        fallback_calculation()
else:
    # Graceful degradation
    basic_astrology_calculation()
```

**Error Handling Pattern:**
```python
try:
    result = advanced_astrological_calculation()
    logger.info(f"OPERATION_SUCCESS: {correlation_id}")
except Exception as e:
    logger.error(f"OPERATION_ERROR: {correlation_id} - {e}")
    result = fallback_calculation()
```

### Voice Interface Considerations

**For Yandex Alice Integration:**
- Response time critical: max 2-3 seconds for horoscope generation
- Character limits: 800 chars for horoscopes, 600 for compatibility
- Button limits: maximum 5 buttons per response
- TTS optimization: automatic emoji removal and pause insertion
- Multi-turn conversation support with session management

**Russian Language Processing:**
- Zodiac sign declension handling
- Voice recognition error correction patterns
- Proper date and time format parsing
- Cultural astrological terminology usage

### Testing Strategy

**When Writing or Reviewing Tests:**
1. Test both Kerykeion-available and fallback scenarios
2. Verify astronomical calculation accuracy against known values
3. Test multi-backend fallback mechanisms
4. Validate Russian text processing and voice interface constraints
5. Performance test for Alice response time requirements

### Data Privacy and Security

**Astrological Data Handling:**
- Personal birth data encryption at rest
- GDPR compliance for EU users
- Session-based temporary data storage
- Secure astrological calculation parameter handling

### Deployment Considerations

**Docker Environment:**
- Multi-stage builds for different library combinations
- Environment variable mapping for Kerykeion availability
- Graceful container startup with library detection
- Resource allocation for complex astrological calculations

**Production Monitoring:**
- Library availability detection at startup
- Calculation backend usage tracking
- Performance metrics for astrological computations
- Error rate monitoring for fallback scenarios

### Contributing Guidelines

**When Extending Astrological Features:**
1. Maintain backward compatibility with existing API
2. Implement proper fallback mechanisms
3. Add comprehensive logging with correlation IDs
4. Include both unit and integration tests
5. Document new astrological concepts and calculations
6. Consider computational performance impact
7. Validate against traditional astrological principles

**Code Review Focus:**
- Astronomical calculation accuracy
- Multi-backend compatibility
- Russian language processing
- Voice interface optimization
- Error handling and logging
- Performance implications
- Test coverage adequacy

### Resources

**Astrological References:**
- Traditional planetary aspects and their meanings
- House system mathematical foundations
- Arabic Parts formulas and interpretations
- Synastry analysis principles
- Chart pattern recognition techniques

**Technical References:**
- Kerykeion documentation and examples
- Swiss Ephemeris precision standards
- Astronomical coordinate system conversions
- Julian Day calculation methods
- Timezone handling best practices

This document should guide AI assistants in understanding the sophisticated astrological computing architecture and contributing effectively to the Astroloh project's continued development.