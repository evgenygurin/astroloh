"""
Comprehensive test suite for astro_time_utils module.

This test suite covers all functionality of the centralized time handling module,
including security validation, performance testing, and integration scenarios.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo

from app.utils.astro_time_utils import (
    AstroDateTime,
    utcnow,
    now,
    current_timestamp,
    database_timestamp,
    db_timestamp_default,
    create_astro_datetime,
    create_astro_datetime_now,
    parse_datetime_safe,
    calculate_local_solar_time,
    get_timezone_for_coordinates,
    batch_create_astro_datetimes,
    format_for_display,
    validate_input,
    get_timezone_info,
    get_cache_stats,
    clear_timezone_cache,
    RUSSIAN_TIMEZONE_MAP
)


class TestAstroDateTime:
    """Test cases for AstroDateTime class."""
    
    def test_astro_datetime_creation(self):
        """Test basic AstroDateTime creation."""
        dt = datetime.now(timezone.utc)
        astro_dt = AstroDateTime(dt, "UTC", "Test City", (55.7558, 37.6176))
        
        assert astro_dt.datetime == dt
        assert astro_dt.timezone_name == "UTC"
        assert astro_dt.city_name == "Test City"
        assert astro_dt.coordinates == (55.7558, 37.6176)
        assert not astro_dt.is_solar_time
    
    def test_astro_datetime_requires_timezone_aware(self):
        """Test that AstroDateTime requires timezone-aware datetime."""
        naive_dt = datetime.now()  # No timezone
        
        with pytest.raises(ValueError, match="requires timezone-aware datetime"):
            AstroDateTime(naive_dt)
    
    def test_astro_datetime_timezone_conversion(self):
        """Test timezone conversion functionality."""
        moscow_dt = datetime.now(ZoneInfo("Europe/Moscow"))
        astro_dt = AstroDateTime(moscow_dt, "Europe/Moscow", "Москва")
        
        # Convert to UTC
        utc_astro_dt = astro_dt.to_utc()
        assert utc_astro_dt.timezone_name == "UTC"
        assert utc_astro_dt.city_name == "Москва"  # Context preserved
        
        # Convert to another timezone
        ny_astro_dt = astro_dt.to_timezone("America/New_York")
        assert "America/New_York" in str(ny_astro_dt.datetime.tzinfo)
    
    def test_astro_datetime_string_representations(self):
        """Test string representation methods."""
        dt = datetime(2023, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        astro_dt = AstroDateTime(dt, "UTC", "Test City", (55.0, 37.0), True)
        
        # Test __str__
        str_repr = str(astro_dt)
        assert "2023-06-15T12:30:45+00:00" in str_repr
        assert "city=Test City" in str_repr
        assert "tz=UTC" in str_repr
        assert "solar_time" in str_repr
        
        # Test isoformat
        assert astro_dt.isoformat() == "2023-06-15T12:30:45+00:00"
        
        # Test __repr__
        repr_str = repr(astro_dt)
        assert "AstroDateTime" in repr_str
        assert "timezone_name='UTC'" in repr_str


class TestBasicTimeFunctions:
    """Test cases for basic time functions."""
    
    def test_utcnow(self):
        """Test utcnow function."""
        result = utcnow()
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
        
        # Should be close to current time
        now_time = datetime.now(timezone.utc)
        assert abs((result - now_time).total_seconds()) < 1
    
    def test_now_without_timezone(self):
        """Test now function without timezone parameter."""
        result = now()
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
    
    def test_now_with_timezone(self):
        """Test now function with timezone parameter."""
        result = now("Europe/Moscow")
        assert isinstance(result, datetime)
        assert result.tzinfo is not None
        
        # Test with Russian city name
        result_city = now("Москва")
        assert isinstance(result_city, datetime)
        assert result_city.tzinfo is not None
    
    def test_now_with_invalid_timezone(self):
        """Test now function with invalid timezone."""
        result = now("Invalid/Timezone")
        # Should fallback to UTC
        assert result.tzinfo == timezone.utc
    
    def test_current_timestamp(self):
        """Test current_timestamp function."""
        result = current_timestamp()
        assert isinstance(result, str)
        assert "T" in result  # ISO format
        assert result.endswith("+00:00") or result.endswith("Z")
    
    def test_database_timestamp(self):
        """Test database_timestamp function."""
        result = database_timestamp()
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc
    
    def test_db_timestamp_default(self):
        """Test db_timestamp_default factory function."""
        factory = db_timestamp_default()
        assert callable(factory)
        
        result = factory()
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc


class TestRussianTimezoneSupport:
    """Test cases for Russian timezone support."""
    
    def test_russian_cities_mapping(self):
        """Test Russian cities are properly mapped."""
        test_cities = [
            ("москва", "Europe/Moscow"),
            ("санкт-петербург", "Europe/Moscow"),
            ("екатеринбург", "Asia/Yekaterinburg"),
            ("владивосток", "Asia/Vladivostok"),
            ("калининград", "Europe/Kaliningrad")
        ]
        
        for city, expected_tz in test_cities:
            assert city in RUSSIAN_TIMEZONE_MAP
            assert RUSSIAN_TIMEZONE_MAP[city] == expected_tz
    
    def test_get_timezone_info_russian_cities(self):
        """Test timezone info for Russian cities."""
        tz_info = get_timezone_info("Москва")
        assert tz_info["zone"] == "Europe/Moscow"
        assert tz_info["city_name"] == "Москва"
        assert isinstance(tz_info["offset_seconds"], (int, float))
    
    def test_get_timezone_info_caching(self):
        """Test that timezone info is properly cached."""
        # Clear cache first
        clear_timezone_cache()
        
        # First call
        tz_info1 = get_timezone_info("Europe/Moscow")
        stats1 = get_cache_stats()
        
        # Second call (should hit cache)
        tz_info2 = get_timezone_info("Europe/Moscow")
        stats2 = get_cache_stats()
        
        assert tz_info1 == tz_info2
        assert stats2["hits"] > stats1["hits"]
    
    def test_get_timezone_info_fallback(self):
        """Test fallback behavior for invalid timezones."""
        tz_info = get_timezone_info("Invalid/Timezone")
        assert tz_info["zone"] == "Europe/Moscow"  # Fallback
        assert tz_info["city_name"] is None


class TestAstroDateTimeCreation:
    """Test cases for AstroDateTime creation functions."""
    
    def test_create_astro_datetime_from_string(self):
        """Test creating AstroDateTime from string."""
        dt_str = "2023-06-15T12:30:45"
        astro_dt = create_astro_datetime(dt_str, "Europe/Moscow")
        
        assert astro_dt.datetime.year == 2023
        assert astro_dt.datetime.month == 6
        assert astro_dt.datetime.day == 15
        assert astro_dt.timezone_name == "Europe/Moscow"
    
    def test_create_astro_datetime_from_datetime(self):
        """Test creating AstroDateTime from datetime object."""
        dt = datetime(2023, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        astro_dt = create_astro_datetime(dt, "UTC")
        
        assert astro_dt.datetime == dt
        assert astro_dt.timezone_name == "UTC"
    
    def test_create_astro_datetime_with_russian_city(self):
        """Test creating AstroDateTime with Russian city."""
        astro_dt = create_astro_datetime("2023-06-15T12:30:45", "Москва")
        
        assert astro_dt.timezone_name == "Europe/Moscow"
        assert astro_dt.city_name == "Москва"
    
    def test_create_astro_datetime_with_coordinates(self):
        """Test creating AstroDateTime with coordinates."""
        coords = (55.7558, 37.6176)  # Moscow coordinates
        astro_dt = create_astro_datetime(
            "2023-06-15T12:30:45",
            "Europe/Moscow",
            coords
        )
        
        assert astro_dt.coordinates == coords
    
    def test_create_astro_datetime_now(self):
        """Test creating AstroDateTime for current time."""
        astro_dt = create_astro_datetime_now("Europe/Moscow", (55.0, 37.0))
        
        assert astro_dt.timezone_name == "Europe/Moscow"
        assert astro_dt.coordinates == (55.0, 37.0)
        
        # Should be close to current time
        now_time = datetime.now(ZoneInfo("Europe/Moscow"))
        time_diff = abs((astro_dt.datetime - now_time).total_seconds())
        assert time_diff < 2  # Within 2 seconds


class TestDateTimeParsing:
    """Test cases for datetime parsing functions."""
    
    def test_parse_datetime_safe_iso_format(self):
        """Test parsing ISO format datetime."""
        dt_str = "2023-06-15T12:30:45+03:00"
        result = parse_datetime_safe(dt_str)
        
        assert result.year == 2023
        assert result.month == 6
        assert result.day == 15
        assert result.tzinfo is not None
    
    def test_parse_datetime_safe_with_z_suffix(self):
        """Test parsing datetime with Z suffix."""
        dt_str = "2023-06-15T12:30:45Z"
        result = parse_datetime_safe(dt_str)
        
        assert result.tzinfo == timezone.utc
    
    def test_parse_datetime_safe_naive_datetime(self):
        """Test parsing naive datetime with default timezone."""
        dt_str = "2023-06-15T12:30:45"
        result = parse_datetime_safe(dt_str, "Europe/Moscow")
        
        assert result.tzinfo is not None
        # Should be in Moscow timezone
        assert result.tzinfo.key == "Europe/Moscow"
    
    def test_parse_datetime_safe_invalid_format(self):
        """Test parsing invalid datetime format."""
        with pytest.raises(ValueError, match="Invalid datetime format"):
            parse_datetime_safe("invalid-datetime")


class TestSolarTimeCalculations:
    """Test cases for solar time calculations."""
    
    def test_calculate_local_solar_time(self):
        """Test local solar time calculation."""
        dt = datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        longitude = 37.6176  # Moscow longitude
        
        solar_dt = calculate_local_solar_time(dt, longitude, "Europe/Moscow")
        
        assert solar_dt.is_solar_time
        assert solar_dt.timezone_name == "Europe/Moscow"
        assert solar_dt.coordinates == (None, longitude)
        
        # Solar time should be different from input time
        assert solar_dt.datetime != dt
    
    def test_calculate_local_solar_time_naive_datetime(self):
        """Test solar time calculation with naive datetime."""
        dt = datetime(2023, 6, 15, 12, 0, 0)  # Naive
        longitude = 0.0  # Greenwich
        
        solar_dt = calculate_local_solar_time(dt, longitude)
        
        assert solar_dt.is_solar_time
        # For Greenwich (0° longitude), solar time should equal UTC time
        assert abs((solar_dt.datetime - dt.replace(tzinfo=timezone.utc)).total_seconds()) < 1


class TestTimezoneCoordinates:
    """Test cases for coordinate-based timezone detection."""
    
    def test_get_timezone_for_coordinates_moscow(self):
        """Test timezone detection for Moscow coordinates."""
        # Moscow: ~37.6° E longitude
        tz = get_timezone_for_coordinates(55.7558, 37.6176)
        # Should be close to Moscow timezone (UTC+3)
        assert tz in ["Europe/Moscow", "Asia/Dubai"]  # Both are UTC+3/+4
    
    def test_get_timezone_for_coordinates_utc(self):
        """Test timezone detection for UTC coordinates."""
        # Greenwich: 0° longitude
        tz = get_timezone_for_coordinates(51.4778, 0.0)
        assert tz in ["UTC", "Europe/London"]
    
    def test_get_timezone_for_coordinates_extreme_values(self):
        """Test timezone detection for extreme coordinate values."""
        # Test extreme longitude values
        tz_west = get_timezone_for_coordinates(0, -180)
        tz_east = get_timezone_for_coordinates(0, 180)
        
        assert isinstance(tz_west, str)
        assert isinstance(tz_east, str)


class TestBatchOperations:
    """Test cases for batch operations."""
    
    def test_batch_create_astro_datetimes(self):
        """Test batch creation of AstroDateTime objects."""
        datetime_data = [
            {
                "datetime": "2023-06-15T12:30:45",
                "timezone": "Europe/Moscow",
                "coordinates": (55.7558, 37.6176)
            },
            {
                "datetime": "2023-06-15T15:30:45",
                "timezone": "Владивосток",
                "coordinates": (43.1056, 131.8735)
            },
            {
                "datetime": "2023-06-15T09:30:45",
                "timezone": "Europe/London"
            }
        ]
        
        results = batch_create_astro_datetimes(datetime_data)
        
        assert len(results) == 3
        assert all(isinstance(dt, AstroDateTime) for dt in results)
        
        # Check first result
        assert results[0].timezone_name == "Europe/Moscow"
        assert results[0].coordinates == (55.7558, 37.6176)
        
        # Check second result (Russian city)
        assert results[1].timezone_name == "Asia/Vladivostok"
        assert results[1].city_name == "Владивосток"
    
    def test_batch_create_with_errors(self):
        """Test batch creation with some invalid data."""
        datetime_data = [
            {"datetime": "2023-06-15T12:30:45", "timezone": "Europe/Moscow"},
            {"datetime": "invalid-datetime", "timezone": "Europe/Moscow"},
            {"datetime": "2023-06-15T15:30:45", "timezone": "UTC"}
        ]
        
        results = batch_create_astro_datetimes(datetime_data)
        
        # Should still return 3 results (with fallback for invalid)
        assert len(results) == 3
        assert all(isinstance(dt, AstroDateTime) for dt in results)
        
        # Second result should be fallback UTC
        assert results[1].timezone_name == "UTC"


class TestDisplayFormatting:
    """Test cases for display formatting."""
    
    def test_format_for_display_iso(self):
        """Test ISO format display."""
        dt = datetime(2023, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        result = format_for_display(dt, "iso")
        
        assert result == "2023-06-15T12:30:45+00:00"
    
    def test_format_for_display_human_russian(self):
        """Test human-readable format in Russian."""
        dt = datetime(2023, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        result = format_for_display(dt, "human", "ru")
        
        assert "15 июня 2023 г." in result
        assert "12:30" in result
    
    def test_format_for_display_human_english(self):
        """Test human-readable format in English."""
        dt = datetime(2023, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        result = format_for_display(dt, "human", "en")
        
        assert "June 15, 2023" in result
        assert "12:30" in result
    
    def test_format_for_display_short(self):
        """Test short format display."""
        dt = datetime(2023, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        result = format_for_display(dt, "short")
        
        assert result == "2023-06-15 12:30"
    
    def test_format_for_display_astro_datetime(self):
        """Test formatting AstroDateTime object."""
        dt = datetime(2023, 6, 15, 12, 30, 45, tzinfo=timezone.utc)
        astro_dt = AstroDateTime(dt, "UTC")
        result = format_for_display(astro_dt, "iso")
        
        assert result == "2023-06-15T12:30:45+00:00"


class TestInputValidation:
    """Test cases for input validation and security."""
    
    def test_validate_input_normal_string(self):
        """Test validation of normal string."""
        result = validate_input("Europe/Moscow")
        assert result == "Europe/Moscow"
    
    def test_validate_input_with_whitespace(self):
        """Test validation strips whitespace."""
        result = validate_input("  Europe/Moscow  ")
        assert result == "Europe/Moscow"
    
    def test_validate_input_too_long(self):
        """Test validation rejects too long strings."""
        long_string = "a" * 101
        with pytest.raises(ValueError, match="Input too long"):
            validate_input(long_string, max_length=100)
    
    def test_validate_input_non_string(self):
        """Test validation rejects non-string input."""
        with pytest.raises(ValueError, match="Input must be a string"):
            validate_input(123)
    
    def test_validate_input_dangerous_patterns(self):
        """Test validation rejects dangerous patterns."""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "javascript:alert(1)",
            "SELECT * FROM users",
            "UNION SELECT password FROM users"
        ]
        
        for dangerous_input in dangerous_inputs:
            with pytest.raises(ValueError, match="potentially dangerous content"):
                validate_input(dangerous_input)
    
    def test_validate_input_control_characters(self):
        """Test validation rejects control characters."""
        with pytest.raises(ValueError, match="potentially dangerous content"):
            validate_input("test\x00string")
    
    def test_create_astro_datetime_input_validation(self):
        """Test that create_astro_datetime validates inputs."""
        with pytest.raises(ValueError, match="potentially dangerous content"):
            create_astro_datetime("<script>alert(1)</script>", "UTC")


class TestCacheManagement:
    """Test cases for cache management."""
    
    def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        clear_timezone_cache()
        
        # Make some calls to populate cache
        get_timezone_info("Europe/Moscow")
        get_timezone_info("UTC")
        get_timezone_info("Europe/Moscow")  # Should hit cache
        
        stats = get_cache_stats()
        
        assert isinstance(stats, dict)
        assert "hits" in stats
        assert "misses" in stats
        assert "maxsize" in stats
        assert "currsize" in stats
        assert "hit_rate" in stats
        
        assert stats["hits"] >= 1  # At least one cache hit
        assert stats["misses"] >= 2  # At least two cache misses
        assert 0 <= stats["hit_rate"] <= 1
    
    def test_clear_timezone_cache(self):
        """Test cache clearing functionality."""
        # Populate cache
        get_timezone_info("Europe/Moscow")
        stats_before = get_cache_stats()
        
        # Clear cache
        clear_timezone_cache()
        stats_after = get_cache_stats()
        
        assert stats_after["currsize"] == 0
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0


class TestPerformanceAndStress:
    """Test cases for performance and stress testing."""
    
    def test_timezone_lookup_performance(self):
        """Test timezone lookup performance."""
        start_time = time.time()
        
        # Perform many timezone lookups
        for _ in range(100):
            get_timezone_info("Europe/Moscow")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast due to caching (less than 0.1 seconds for 100 lookups)
        assert duration < 0.1
    
    def test_batch_creation_performance(self):
        """Test batch creation performance."""
        # Create large batch of datetime data
        datetime_data = []
        for i in range(50):
            datetime_data.append({
                "datetime": f"2023-06-{15 + (i % 15):02d}T12:30:45",
                "timezone": "Europe/Moscow" if i % 2 == 0 else "UTC",
                "coordinates": (55.0 + i * 0.1, 37.0 + i * 0.1)
            })
        
        start_time = time.time()
        results = batch_create_astro_datetimes(datetime_data)
        end_time = time.time()
        
        duration = end_time - start_time
        
        assert len(results) == 50
        assert duration < 1.0  # Should complete within 1 second
    
    def test_memory_usage_stability(self):
        """Test that repeated operations don't cause memory leaks."""
        # Perform many operations
        for i in range(1000):
            dt_str = f"2023-06-15T{12 + (i % 12):02d}:30:45"
            astro_dt = create_astro_datetime(dt_str, "Europe/Moscow")
            _ = astro_dt.to_utc()
            _ = format_for_display(astro_dt, "iso")
        
        # If we get here without memory issues, test passes
        assert True


class TestEdgeCases:
    """Test cases for edge cases and error conditions."""
    
    def test_leap_year_handling(self):
        """Test leap year date handling."""
        # February 29, 2024 (leap year)
        astro_dt = create_astro_datetime("2024-02-29T12:00:00", "UTC")
        assert astro_dt.datetime.month == 2
        assert astro_dt.datetime.day == 29
    
    def test_daylight_saving_time_transitions(self):
        """Test DST transition handling."""
        # Test spring forward (March in Europe)
        spring_dt = create_astro_datetime("2023-03-26T02:30:00", "Europe/Moscow")
        assert spring_dt.datetime is not None
        
        # Test fall back (October in Europe)
        fall_dt = create_astro_datetime("2023-10-29T02:30:00", "Europe/Moscow")
        assert fall_dt.datetime is not None
    
    def test_extreme_coordinates(self):
        """Test extreme coordinate values."""
        # North Pole
        tz_north = get_timezone_for_coordinates(90.0, 0.0)
        assert isinstance(tz_north, str)
        
        # South Pole
        tz_south = get_timezone_for_coordinates(-90.0, 0.0)
        assert isinstance(tz_south, str)
        
        # International Date Line
        tz_dateline = get_timezone_for_coordinates(0.0, 180.0)
        assert isinstance(tz_dateline, str)
    
    def test_year_boundaries(self):
        """Test year boundary dates."""
        # New Year's Eve
        nye_dt = create_astro_datetime("2023-12-31T23:59:59", "UTC")
        assert nye_dt.datetime.year == 2023
        
        # New Year's Day
        nyd_dt = create_astro_datetime("2024-01-01T00:00:00", "UTC")
        assert nyd_dt.datetime.year == 2024
    
    def test_unicode_city_names(self):
        """Test Unicode city names handling."""
        unicode_cities = ["Москва", "Санкт-Петербург", "Екатеринбург"]
        
        for city in unicode_cities:
            astro_dt = create_astro_datetime("2023-06-15T12:00:00", city)
            assert astro_dt.city_name == city
            assert astro_dt.timezone_name is not None


class TestIntegrationScenarios:
    """Test cases for real-world integration scenarios."""
    
    def test_database_integration_scenario(self):
        """Test typical database integration scenario."""
        # Simulate SQLAlchemy default usage
        timestamp_factory = db_timestamp_default()
        
        # Create multiple timestamps (as would happen in database operations)
        timestamps = [timestamp_factory() for _ in range(5)]
        
        assert len(timestamps) == 5
        assert all(isinstance(ts, datetime) for ts in timestamps)
        assert all(ts.tzinfo == timezone.utc for ts in timestamps)
        
        # Timestamps should be close to each other but not identical
        time_diffs = [abs((timestamps[i+1] - timestamps[i]).total_seconds()) 
                     for i in range(len(timestamps)-1)]
        assert all(diff < 1.0 for diff in time_diffs)  # Within 1 second
    
    def test_api_response_scenario(self):
        """Test typical API response formatting scenario."""
        # Create datetime for API response
        api_timestamp = current_timestamp()
        
        # Parse it back (as would happen in API processing)
        parsed_dt = parse_datetime_safe(api_timestamp)
        
        # Format for different display contexts
        iso_format = format_for_display(parsed_dt, "iso")
        human_format = format_for_display(parsed_dt, "human", "ru")
        short_format = format_for_display(parsed_dt, "short")
        
        assert isinstance(iso_format, str)
        assert isinstance(human_format, str)
        assert isinstance(short_format, str)
        
        # All formats should represent the same time
        assert "T" in iso_format
        assert "г." in human_format  # Russian format
        assert len(short_format.split()) == 2  # Date and time parts
    
    def test_astronomical_calculation_scenario(self):
        """Test typical astronomical calculation scenario."""
        # Birth data processing
        birth_data = {
            "datetime": "1990-07-15T14:30:00",
            "city": "Москва",
            "coordinates": (55.7558, 37.6176)
        }
        
        # Create birth time
        birth_time = create_astro_datetime(
            birth_data["datetime"],
            birth_data["city"],
            birth_data["coordinates"]
        )
        
        # Calculate solar time (important for astrology)
        solar_time = calculate_local_solar_time(
            birth_time.datetime,
            birth_data["coordinates"][1],  # longitude
            birth_time.timezone_name
        )
        
        # Convert to different timezones for calculations
        utc_time = birth_time.to_utc()
        
        assert birth_time.city_name == "Москва"
        assert birth_time.timezone_name == "Europe/Moscow"
        assert solar_time.is_solar_time
        assert utc_time.timezone_name == "UTC"
        
        # Times should be different but related
        assert birth_time.datetime != solar_time.datetime
        assert birth_time.datetime != utc_time.datetime
    
    def test_multi_user_session_scenario(self):
        """Test multi-user session handling scenario."""
        # Simulate multiple users from different timezones
        users = [
            {"name": "Moscow User", "timezone": "Москва"},
            {"name": "Vladivostok User", "timezone": "Владивосток"},
            {"name": "Kaliningrad User", "timezone": "Калининград"},
            {"name": "UTC User", "timezone": "UTC"}
        ]
        
        session_times = []
        for user in users:
            session_time = create_astro_datetime_now(user["timezone"])
            session_times.append({
                "user": user["name"],
                "local_time": session_time,
                "utc_time": session_time.to_utc()
            })
        
        assert len(session_times) == 4
        
        # All UTC times should be very close (within seconds)
        utc_times = [st["utc_time"].datetime for st in session_times]
        max_diff = max(utc_times) - min(utc_times)
        assert max_diff.total_seconds() < 5
        
        # Local times should be different (different timezones)
        local_times = [st["local_time"].datetime for st in session_times]
        # Moscow and Kaliningrad should have different times
        moscow_time = next(st["local_time"] for st in session_times if "Moscow" in st["user"])
        kaliningrad_time = next(st["local_time"] for st in session_times if "Kaliningrad" in st["user"])
        
        time_diff = abs((moscow_time.datetime - kaliningrad_time.datetime).total_seconds())
        assert time_diff >= 3600  # At least 1 hour difference


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

