# Kerykeion Integration Guide

## Overview

This document provides a comprehensive guide to the Kerykeion library integration in the Astroloh project. Kerykeion is a powerful Python library for astrological calculations that provides advanced features for natal charts, progressions, returns, and chart visualization.

## Features Implemented

### ✅ Core Features
- **Natal Chart Calculations**: Complete natal chart data with 13 planets and 12 houses
- **Multiple House Systems**: Placidus, Koch, Equal, Whole Sign, and more
- **Zodiac Types**: Tropical and Sidereal zodiac support
- **Aspect Calculations**: 66+ aspects with strength and color coding
- **Chart Shapes**: Stellium, Grand Trine, T-Square detection

### ✅ Advanced Features
- **Arabic Parts**: Extended Arabic parts calculation (5+ parts)
- **Secondary Progressions**: Day-for-year progressions (5 progressed planets)
- **Solar Returns**: Annual solar return charts
- **Lunar Returns**: Monthly lunar return charts
- **SVG Chart Generation**: High-quality vector chart images (156KB+)
- **Element & Quality Analysis**: Detailed astrological analysis

### ✅ Technical Features
- **Async Support**: Full asynchronous processing capabilities
- **Caching**: Redis-based caching for performance optimization
- **Error Handling**: Comprehensive error handling and logging
- **Performance Monitoring**: Built-in performance statistics
- **Multiple Backends**: Kerykeion, SwissEph, and fallback support

## Services Architecture

### KerykeionService
Main synchronous service for astrological calculations.

```python
from app.services.kerykeion_service import KerykeionService, HouseSystem, ZodiacType
from datetime import datetime
import pytz

service = KerykeionService()

# Basic natal chart
result = service.get_full_natal_chart_data(
    name='John Doe',
    birth_datetime=datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC),
    latitude=55.7558,
    longitude=37.6176,
    timezone='Europe/Moscow',
    house_system=HouseSystem.PLACIDUS,
    zodiac_type=ZodiacType.TROPICAL
)
```

### AsyncKerykeionService
Asynchronous service for high-performance applications.

```python
from app.services.async_kerykeion_service import AsyncKerykeionService

service = AsyncKerykeionService()

# Async natal chart
result = await service.get_full_natal_chart_data(
    name='Jane Doe',
    birth_datetime=datetime(1985, 6, 15, 14, 30, tzinfo=pytz.UTC),
    latitude=40.7128,
    longitude=-74.0060,
    timezone='America/New_York'
)

# Don't forget to shutdown
await service.shutdown()
```

## Configuration Options

### House Systems
```python
from app.services.kerykeion_service import HouseSystem

# Available house systems
HouseSystem.PLACIDUS      # Default, most common
HouseSystem.KOCH          # Koch houses
HouseSystem.EQUAL         # Equal houses
HouseSystem.WHOLE_SIGN    # Whole sign houses
HouseSystem.CAMPANUS      # Campanus houses
HouseSystem.REGIOMONTANUS # Regiomontanus houses
```

### Zodiac Types
```python
from app.services.kerykeion_service import ZodiacType

ZodiacType.TROPICAL   # Western tropical zodiac (default)
ZodiacType.SIDEREAL   # Vedic sidereal zodiac
```

## Data Structures

### Natal Chart Response
```python
{
    "name": "John Doe",
    "birth_datetime": "1990-01-01T12:00:00+00:00",
    "timezone": "Europe/Moscow",
    "latitude": 55.7558,
    "longitude": 37.6176,
    "house_system": "Placidus",
    "zodiac_type": "Tropical",
    
    "planets": {
        "Sun": {
            "longitude": 280.123,
            "latitude": 0.0,
            "sign": "Capricorn",
            "sign_num": 10,
            "degree_in_sign": 10.123,
            "house": 4,
            "element": "Earth",
            "quality": "Cardinal",
            "retrograde": false
        },
        # ... 12 more planets
    },
    
    "houses": {
        1: {
            "cusp_longitude": 95.456,
            "sign": "Cancer",
            "sign_num": 4,
            "degree_in_sign": 5.456,
            "element": "Water",
            "quality": "Cardinal"
        },
        # ... 11 more houses
    },
    
    "aspects": [
        {
            "planet1": "Sun",
            "planet2": "Moon",
            "aspect": "Conjunction",
            "orb": 2.5,
            "strength": "Very Strong",
            "color": "#FF0000",
            "applying": true
        },
        # ... 65+ more aspects
    ],
    
    "chart_shape": "Stellium",
    "element_distribution": {
        "Fire": 3,
        "Earth": 4,
        "Air": 2,
        "Water": 4
    },
    "quality_distribution": {
        "Cardinal": 4,
        "Fixed": 5,
        "Mutable": 4
    }
}
```

### Arabic Parts Response
```python
{
    "parts": [
        {
            "name": "Часть Фортуны",
            "longitude": 123.456,
            "sign": "Leo",
            "degree_in_sign": 3.456,
            "house": 7,
            "formula": "ASC + Moon - Sun"
        },
        # ... more parts
    ]
}
```

## Advanced Features

### Secondary Progressions
```python
# Calculate progressions for current date
prog_result = service.calculate_secondary_progressions(
    name='John Doe',
    birth_datetime=datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC),
    current_date=datetime(2024, 1, 1, tzinfo=pytz.UTC),
    latitude=55.7558,
    longitude=37.6176,
    timezone='Europe/Moscow'
)

# Returns progressed positions for Sun, Moon, Mercury, Venus, Mars
```

### Solar Returns
```python
# Calculate solar return for specific year
solar_result = service.calculate_solar_return(
    name='John Doe',
    birth_datetime=datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC),
    return_year=2024,
    latitude=55.7558,
    longitude=37.6176,
    timezone='Europe/Moscow'
)
```

### SVG Chart Generation
```python
# Generate high-quality SVG chart
svg_result = service.generate_chart_svg(
    name='John Doe',
    birth_datetime=datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC),
    latitude=55.7558,
    longitude=37.6176,
    timezone='Europe/Moscow',
    theme='classic'  # or 'modern', 'dark'
)

# SVG file is created at: "/root/John Doe - Natal Chart.svg"
```

## Performance Optimization

### Caching
The system uses Redis-based caching to optimize performance:

```python
# Cache keys are automatically generated based on:
# - Birth datetime
# - Location (latitude/longitude)
# - House system
# - Timezone
# - Zodiac type

# Cache TTL: 24 hours for natal charts
# Cache TTL: 1 hour for progressions/returns
```

### Async Processing
```python
# Use async service for high-throughput applications
service = AsyncKerykeionService()

# Process multiple charts concurrently
tasks = [
    service.get_full_natal_chart_data(name, dt, lat, lng, tz)
    for name, dt, lat, lng, tz in chart_requests
]

results = await asyncio.gather(*tasks)
```

## Error Handling

### Common Errors
```python
# Invalid coordinates
{
    "error": "Invalid coordinates: latitude must be between -90 and 90"
}

# Invalid timezone
{
    "error": "Invalid timezone: 'Invalid/Timezone'"
}

# Kerykeion not available
{
    "error": "Kerykeion not available"
}

# Calculation failed
{
    "error": "Chart calculation failed: [specific error message]"
}
```

### Error Logging
All errors are logged with the Loguru library:

```python
# Error logs include:
# - Service name
# - Operation type
# - Input parameters
# - Full error traceback
# - Timestamp and severity level
```

## Testing

### Running Tests
```bash
# Run comprehensive test suite
python test_kerykeion_comprehensive.py

# Run integration tests
python test_kerykeion_integration.py
```

### Test Coverage
- ✅ Basic natal chart calculations
- ✅ Multiple house systems
- ✅ Sidereal zodiac
- ✅ Arabic parts
- ✅ Secondary progressions
- ✅ Solar returns
- ✅ SVG generation
- ✅ Async operations
- ✅ Error handling
- ✅ Performance monitoring

## Dependencies

### Required Packages
```txt
kerykeion>=4.0.0          # Main astrological library
loguru>=0.7.2             # Logging
redis>=4.0.0              # Caching
pytz                      # Timezone handling
```

### Indirect Dependencies
```txt
swisseph                  # Swiss Ephemeris (via kerykeion)
requests                  # HTTP requests for city lookup
```

## Troubleshooting

### Common Issues

1. **Kerykeion Import Error**
   ```bash
   pip install kerykeion>=4.0.0
   ```

2. **Swiss Ephemeris Missing**
   ```bash
   pip install swisseph
   ```

3. **Redis Connection Error**
   - Ensure Redis server is running
   - Check Redis configuration in environment variables

4. **Timezone Errors**
   - Use pytz timezone names
   - Validate timezone strings before processing

5. **SVG Generation Returns None**
   - This is expected behavior
   - SVG file is created in the specified path
   - Check file system for generated SVG files

### Performance Tips

1. **Use Caching**: Enable Redis caching for repeated calculations
2. **Async Processing**: Use AsyncKerykeionService for concurrent operations
3. **Batch Operations**: Process multiple charts in batches
4. **Error Handling**: Implement proper error handling to avoid crashes

## Future Enhancements

### Planned Features
- [ ] Composite chart calculations
- [ ] Harmonic charts
- [ ] Fixed stars integration
- [ ] Asteroid calculations
- [ ] Chart comparison tools
- [ ] PDF chart generation
- [ ] Interactive web charts

### API Improvements
- [ ] RESTful API endpoints
- [ ] GraphQL support
- [ ] WebSocket real-time updates
- [ ] Batch processing endpoints
- [ ] Chart sharing functionality

## Support

For issues and questions:
1. Check the error logs for detailed information
2. Verify all dependencies are installed correctly
3. Test with the provided examples
4. Review the comprehensive test suite for usage patterns

## Version History

- **v1.0.0**: Initial Kerykeion 4.x integration
- **v1.1.0**: Added async support and caching
- **v1.2.0**: Enhanced error handling and logging
- **v1.3.0**: Comprehensive testing and documentation

---

*This integration provides a robust foundation for advanced astrological calculations in the Astroloh project, offering both synchronous and asynchronous processing capabilities with comprehensive error handling and performance optimization.*

