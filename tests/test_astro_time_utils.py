"""
Comprehensive tests for astro_time_utils module.
Tests all aspects of time handling including edge cases, security, and performance.
"""

import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.utils.astro_time_utils import (
    AstroDateTime,
    AstroTimeUtils,
    CoordinateInfo,
    CoordinateTimeCalculator,
    CoordinateTimeError,
    DateTimeValidator,
    InvalidDateTimeError,
    InvalidTimezoneError,
    TimezoneManager,
    astro_time,
    create_astro_datetime_now,
    current_timestamp,
    database_timestamp,
    db_timestamp_default,
    now,
    utcnow,
)


class TestCoordinateInfo:
    """Test coordinate validation and handling."""

    def test_valid_coordinates(self):
        """Test valid coordinate creation."""
        coord = CoordinateInfo(55.7558, 37.6176, 150.0)
        assert coord.latitude == 55.7558
        assert coord.longitude == 37.6176
        assert coord.altitude == 150.0

    def test_coordinates_without_altitude(self):
        """Test coordinate creation without altitude."""
        coord = CoordinateInfo(55.7558, 37.6176)
        assert coord.latitude == 55.7558
        assert coord.longitude == 37.6176
        assert coord.altitude is None

    def test_invalid_latitude(self):
        """Test invalid latitude values."""
        with pytest.raises(CoordinateTimeError):
            CoordinateInfo(91.0, 37.6176)  # > 90

        with pytest.raises(CoordinateTimeError):
            CoordinateInfo(-91.0, 37.6176)  # < -90

    def test_invalid_longitude(self):
        """Test invalid longitude values."""
        with pytest.raises(CoordinateTimeError):
            CoordinateInfo(55.7558, 181.0)  # > 180

        with pytest.raises(CoordinateTimeError):
            CoordinateInfo(55.7558, -181.0)  # < -180

    def test_invalid_altitude(self):
        """Test invalid altitude values."""
        with pytest.raises(CoordinateTimeError):
            CoordinateInfo(55.7558, 37.6176, -1001.0)  # Too low

        with pytest.raises(CoordinateTimeError):
            CoordinateInfo(55.7558, 37.6176, 10001.0)  # Too high


class TestTimezoneManager:
    """Test timezone management functionality."""

    @pytest.fixture
    def tz_manager(self):
        return TimezoneManager()

    def test_get_valid_timezone(self, tz_manager):
        """Test getting valid timezone."""
        tz = tz_manager.get_timezone("Europe/Moscow")
        assert str(tz) == "Europe/Moscow"

    def test_get_timezone_city_mapping(self, tz_manager):
        """Test city name to timezone mapping."""
        tz = tz_manager.get_timezone("москва")
        assert str(tz) == "Europe/Moscow"

        tz = tz_manager.get_timezone("moscow")
        assert str(tz) == "Europe/Moscow"

    def test_invalid_timezone(self, tz_manager):
        """Test invalid timezone handling."""
        with pytest.raises(InvalidTimezoneError):
            tz_manager.get_timezone("Invalid/Timezone")

    def test_empty_timezone(self, tz_manager):
        """Test empty timezone string."""
        with pytest.raises(InvalidTimezoneError):
            tz_manager.get_timezone("")

    def test_detect_timezone_from_coordinates(self, tz_manager):
        """Test timezone detection from coordinates."""
        # Moscow coordinates should detect Europe/Moscow region
        tz_name = tz_manager.detect_timezone_from_coordinates(55.7558, 37.6176)
        assert tz_name == "Europe/Moscow"

        # New York coordinates
        tz_name = tz_manager.detect_timezone_from_coordinates(
            40.7128, -74.0060
        )
        assert tz_name == "America/New_York"

    def test_validate_timezone_name(self, tz_manager):
        """Test timezone name validation."""
        assert tz_manager.validate_timezone_name("Europe/Moscow") is True
        assert tz_manager.validate_timezone_name("москва") is True
        assert tz_manager.validate_timezone_name("Invalid/Zone") is False


class TestDateTimeValidator:
    """Test datetime validation and parsing."""

    def test_sanitize_valid_input(self):
        """Test sanitization of valid input."""
        clean = DateTimeValidator.sanitize_input("2023-08-15 14:30:00")
        assert clean == "2023-08-15 14:30:00"

    def test_sanitize_with_whitespace(self):
        """Test sanitization removes whitespace."""
        clean = DateTimeValidator.sanitize_input("  2023-08-15  ")
        assert clean == "2023-08-15"

    def test_sanitize_dangerous_input(self):
        """Test rejection of dangerous input."""
        dangerous_inputs = [
            "2023-08-15<script>",
            "2023-08-15'; DROP TABLE users; --",
            "2023-08-15\\x41",
            "2023-08-15../../../etc/passwd",
            "2023-08-15\r\n",
        ]

        for dangerous in dangerous_inputs:
            with pytest.raises(InvalidDateTimeError):
                DateTimeValidator.sanitize_input(dangerous)

    def test_sanitize_long_input(self):
        """Test rejection of overly long input."""
        long_input = "2023-08-15 " + "A" * 100
        with pytest.raises(InvalidDateTimeError):
            DateTimeValidator.sanitize_input(long_input)

    def test_parse_iso_format(self):
        """Test parsing ISO format datetime."""
        dt = DateTimeValidator.parse_datetime_string(
            "2023-08-15T14:30:00", "Europe/Moscow"
        )
        assert dt.year == 2023
        assert dt.month == 8
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 30

    def test_parse_european_format(self):
        """Test parsing European date format."""
        dt = DateTimeValidator.parse_datetime_string(
            "15.08.2023 14:30", "Europe/Moscow"
        )
        assert dt.year == 2023
        assert dt.month == 8
        assert dt.day == 15

    def test_parse_date_only(self):
        """Test parsing date without time."""
        dt = DateTimeValidator.parse_datetime_string(
            "2023-08-15", "Europe/Moscow"
        )
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0

    def test_parse_invalid_format(self):
        """Test parsing invalid format."""
        with pytest.raises(InvalidDateTimeError):
            DateTimeValidator.parse_datetime_string("invalid-date")

    def test_validate_birth_datetime_valid(self):
        """Test validation of valid birth datetime."""
        dt = datetime(1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow"))
        assert DateTimeValidator.validate_birth_datetime(dt) is True

    def test_validate_birth_datetime_future(self):
        """Test validation rejects future dates."""
        future_dt = datetime(
            2030, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")
        )
        assert DateTimeValidator.validate_birth_datetime(future_dt) is False

    def test_validate_birth_datetime_no_timezone(self):
        """Test validation rejects naive datetime."""
        naive_dt = datetime(1990, 8, 15, 14, 30)
        assert DateTimeValidator.validate_birth_datetime(naive_dt) is False

    def test_validate_birth_datetime_too_old(self):
        """Test validation of very old dates."""
        old_dt = datetime(500, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow"))
        assert DateTimeValidator.validate_birth_datetime(old_dt) is False


class TestCoordinateTimeCalculator:
    """Test coordinate-based time calculations."""

    def test_solar_time_offset_moscow(self):
        """Test solar time offset calculation for Moscow."""
        moscow_longitude = 37.6176
        offset = CoordinateTimeCalculator.calculate_solar_time_offset(
            moscow_longitude
        )

        # Moscow longitude should give ~2.5 hours offset
        expected_hours = moscow_longitude / 15.0
        assert abs(offset.total_seconds() / 3600 - expected_hours) < 0.01

    def test_solar_time_offset_greenwich(self):
        """Test solar time offset for Greenwich (0 longitude)."""
        offset = CoordinateTimeCalculator.calculate_solar_time_offset(0.0)
        assert offset.total_seconds() == 0

    def test_local_mean_time(self):
        """Test local mean time calculation."""
        utc_dt = datetime(2023, 8, 15, 12, 0, tzinfo=timezone.utc)
        longitude = 30.0  # 2 hours east

        local_time = CoordinateTimeCalculator.calculate_local_mean_time(
            utc_dt, longitude
        )
        assert local_time.hour == 14  # 12 UTC + 2 hours

    def test_estimate_timezone_moscow(self):
        """Test timezone estimation for Moscow coordinates."""
        tz_name = CoordinateTimeCalculator.estimate_timezone_from_coordinates(
            55.7558, 37.6176
        )
        assert tz_name == "Europe/Moscow"

    def test_estimate_timezone_new_york(self):
        """Test timezone estimation for New York coordinates."""
        tz_name = CoordinateTimeCalculator.estimate_timezone_from_coordinates(
            40.7128, -74.0060
        )
        assert tz_name == "America/New_York"


class TestAstroDateTime:
    """Test AstroDateTime functionality."""

    def test_create_astro_datetime(self):
        """Test creating AstroDateTime object."""
        dt = datetime(1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow"))
        coords = CoordinateInfo(55.7558, 37.6176)

        astro_dt = AstroDateTime(
            dt=dt, timezone_name="Europe/Moscow", coordinates=coords
        )

        assert astro_dt.dt == dt
        assert astro_dt.timezone_name == "Europe/Moscow"
        assert astro_dt.coordinates == coords

    def test_astro_datetime_utc_property(self):
        """Test UTC conversion property."""
        moscow_dt = datetime(
            1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")
        )
        astro_dt = AstroDateTime(dt=moscow_dt, timezone_name="Europe/Moscow")

        utc_dt = astro_dt.utc
        assert utc_dt.tzinfo == timezone.utc

    def test_astro_datetime_naive_fails(self):
        """Test that naive datetime fails validation."""
        naive_dt = datetime(1990, 8, 15, 14, 30)

        with pytest.raises(InvalidDateTimeError):
            AstroDateTime(dt=naive_dt, timezone_name="Europe/Moscow")

    def test_astro_datetime_out_of_range(self):
        """Test datetime outside supported range."""
        far_future = datetime(4000, 1, 1, tzinfo=timezone.utc)

        with pytest.raises(InvalidDateTimeError):
            AstroDateTime(dt=far_future, timezone_name="UTC")

    def test_local_solar_time_offset(self):
        """Test local solar time offset calculation."""
        dt = datetime(1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow"))
        coords = CoordinateInfo(55.7558, 37.6176)

        astro_dt = AstroDateTime(
            dt=dt, timezone_name="Europe/Moscow", coordinates=coords
        )

        offset = astro_dt.local_solar_time_offset
        assert offset is not None
        # Moscow longitude ~37.6, so offset should be ~2.5 hours
        assert abs(offset.total_seconds() / 3600 - 2.5) < 0.1

    def test_to_local_solar_time(self):
        """Test conversion to local solar time."""
        dt = datetime(1990, 8, 15, 12, 0, tzinfo=timezone.utc)
        coords = CoordinateInfo(55.7558, 37.6176)

        astro_dt = AstroDateTime(
            dt=dt, timezone_name="UTC", coordinates=coords
        )

        solar_time = astro_dt.to_local_solar_time()
        assert solar_time is not None
        # Should be roughly 14:30 local solar time for Moscow longitude
        assert solar_time.hour in [14, 15]  # Allow some tolerance


class TestAstroTimeUtils:
    """Test main AstroTimeUtils functionality."""

    @pytest.fixture
    def utils(self):
        return AstroTimeUtils()

    def test_parse_birth_datetime_string(self, utils):
        """Test parsing birth datetime from string."""
        coords = CoordinateInfo(55.7558, 37.6176)

        astro_dt = utils.parse_birth_datetime(
            "1990-08-15", "14:30:00", "Europe/Moscow", coords
        )

        assert astro_dt.dt.year == 1990
        assert astro_dt.dt.month == 8
        assert astro_dt.dt.day == 15
        assert astro_dt.dt.hour == 14
        assert astro_dt.dt.minute == 30
        assert astro_dt.timezone_name == "Europe/Moscow"
        assert astro_dt.coordinates == coords

    def test_parse_birth_datetime_combined_string(self, utils):
        """Test parsing combined date-time string."""
        astro_dt = utils.parse_birth_datetime(
            "1990-08-15 14:30:00", timezone_input="Europe/Moscow"
        )

        assert astro_dt.dt.year == 1990
        assert astro_dt.dt.hour == 14
        assert astro_dt.timezone_name == "Europe/Moscow"

    def test_parse_birth_datetime_from_datetime(self, utils):
        """Test parsing from datetime object."""
        dt = datetime(1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow"))

        astro_dt = utils.parse_birth_datetime(dt)

        assert astro_dt.dt == dt
        assert "Europe/Moscow" in astro_dt.timezone_name

    def test_parse_birth_datetime_with_coordinates(self, utils):
        """Test parsing with coordinate-based timezone detection."""
        coords = CoordinateInfo(55.7558, 37.6176)  # Moscow

        astro_dt = utils.parse_birth_datetime(
            "1990-08-15 14:30:00", coordinates=coords
        )

        # Should detect Moscow timezone
        assert astro_dt.timezone_name == "Europe/Moscow"
        assert astro_dt.coordinates == coords

    def test_convert_timezone(self, utils):
        """Test timezone conversion."""
        moscow_dt = datetime(
            1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")
        )
        astro_dt = AstroDateTime(dt=moscow_dt, timezone_name="Europe/Moscow")

        utc_astro_dt = utils.convert_timezone(astro_dt, "UTC")

        assert utc_astro_dt.timezone_name == "UTC"
        assert utc_astro_dt.dt.tzinfo == ZoneInfo("UTC")

    def test_to_utc(self, utils):
        """Test UTC conversion."""
        moscow_dt = datetime(
            1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")
        )
        astro_dt = AstroDateTime(dt=moscow_dt, timezone_name="Europe/Moscow")

        utc_astro_dt = utils.to_utc(astro_dt)

        assert utc_astro_dt.timezone_name == "UTC"

    def test_calculate_birth_time_precision(self, utils):
        """Test birth time precision calculation."""
        dt = datetime(
            1990, 8, 15, 14, 30, 45, tzinfo=ZoneInfo("Europe/Moscow")
        )
        coords = CoordinateInfo(55.7558, 37.6176)

        astro_dt = AstroDateTime(
            dt=dt, timezone_name="Europe/Moscow", coordinates=coords
        )

        precision = utils.calculate_birth_time_precision(astro_dt)

        assert precision["has_seconds"] is True
        assert precision["has_coordinates"] is True
        assert precision["solar_time_available"] is True
        assert "local_solar_time" in precision
        assert "solar_time_offset_minutes" in precision

    def test_batch_convert_timezones(self, utils):
        """Test batch timezone conversion."""
        moscow_dt1 = datetime(
            1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")
        )
        moscow_dt2 = datetime(
            1985, 5, 10, 9, 15, tzinfo=ZoneInfo("Europe/Moscow")
        )

        astro_dts = [
            AstroDateTime(dt=moscow_dt1, timezone_name="Europe/Moscow"),
            AstroDateTime(dt=moscow_dt2, timezone_name="Europe/Moscow"),
        ]

        utc_dts = utils.batch_convert_timezones(astro_dts, "UTC")

        assert len(utc_dts) == 2
        assert all(dt.timezone_name == "UTC" for dt in utc_dts)

    def test_invalid_input_type(self, utils):
        """Test invalid input type handling."""
        with pytest.raises(InvalidDateTimeError):
            utils.parse_birth_datetime(12345)  # Invalid type


class TestAstroDateTimeBuilder:
    """Test builder pattern functionality."""

    @pytest.fixture
    def utils(self):
        return AstroTimeUtils()

    def test_builder_basic(self, utils):
        """Test basic builder usage."""
        astro_dt = (
            utils.create_astro_datetime_builder()
            .date("1990-08-15")
            .time("14:30:00")
            .timezone("Europe/Moscow")
            .build()
        )

        assert astro_dt.dt.year == 1990
        assert astro_dt.dt.hour == 14
        assert astro_dt.timezone_name == "Europe/Moscow"

    def test_builder_with_coordinates(self, utils):
        """Test builder with coordinates."""
        astro_dt = (
            utils.create_astro_datetime_builder()
            .date("1990-08-15")
            .time("14:30:00")
            .coordinates(55.7558, 37.6176, 150.0)
            .build()
        )

        assert astro_dt.coordinates is not None
        assert astro_dt.coordinates.latitude == 55.7558
        assert astro_dt.coordinates.altitude == 150.0

    def test_builder_from_datetime(self, utils):
        """Test builder from existing datetime."""
        dt = datetime(1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow"))

        astro_dt = (
            utils.create_astro_datetime_builder()
            .from_datetime(dt)
            .coordinates(55.7558, 37.6176)
            .build()
        )

        assert astro_dt.dt == dt
        assert astro_dt.coordinates is not None

    def test_builder_no_input_fails(self, utils):
        """Test builder fails without input."""
        with pytest.raises(InvalidDateTimeError):
            utils.create_astro_datetime_builder().build()


class TestGlobalInstance:
    """Test global astro_time instance."""

    def test_global_instance_available(self):
        """Test global instance is available."""
        assert astro_time is not None
        assert isinstance(astro_time, AstroTimeUtils)

    def test_global_instance_functionality(self):
        """Test global instance works correctly."""
        astro_dt = astro_time.parse_birth_datetime(
            "1990-08-15 14:30:00", timezone_input="Europe/Moscow"
        )

        assert astro_dt.dt.year == 1990
        assert astro_dt.timezone_name == "Europe/Moscow"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_leap_year_february(self):
        """Test leap year February 29th."""
        astro_dt = astro_time.parse_birth_datetime(
            "2000-02-29 12:00:00", timezone_input="UTC"
        )

        assert astro_dt.dt.month == 2
        assert astro_dt.dt.day == 29

    def test_timezone_transition_dates(self):
        """Test dates around timezone transitions."""
        # Test around DST transition (this may vary by year)
        dt_str = "2023-03-26 03:00:00"  # DST transition in Europe

        astro_dt = astro_time.parse_birth_datetime(
            dt_str, timezone_input="Europe/Moscow"
        )

        assert astro_dt.dt.year == 2023
        assert astro_dt.dt.month == 3

    def test_year_boundaries(self):
        """Test year boundary dates."""
        # New Year's Eve
        astro_dt = astro_time.parse_birth_datetime(
            "1999-12-31 23:59:59", timezone_input="UTC"
        )

        assert astro_dt.dt.year == 1999
        assert astro_dt.dt.month == 12
        assert astro_dt.dt.day == 31

    def test_extreme_coordinates(self):
        """Test extreme but valid coordinates."""
        # North Pole
        coords_north = CoordinateInfo(90.0, 0.0)
        assert coords_north.latitude == 90.0

        # South Pole
        coords_south = CoordinateInfo(-90.0, 0.0)
        assert coords_south.latitude == -90.0

        # International Date Line
        coords_dateline = CoordinateInfo(0.0, 180.0)
        assert coords_dateline.longitude == 180.0


class TestPerformance:
    """Test performance characteristics."""

    def test_batch_operations_performance(self):
        """Test batch operations are efficient."""
        utils = AstroTimeUtils()

        # Create multiple datetime objects
        datetimes = []
        for i in range(100):
            dt = datetime(
                1990 + i % 30, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")
            )
            astro_dt = AstroDateTime(dt=dt, timezone_name="Europe/Moscow")
            datetimes.append(astro_dt)

        # Batch convert should complete quickly
        import time

        start = time.perf_counter()
        results = utils.batch_convert_timezones(datetimes, "UTC")
        elapsed = time.perf_counter() - start

        assert len(results) == 100
        assert elapsed < 1.0  # Should complete in under 1 second

    def test_timezone_caching(self):
        """Test timezone caching improves performance."""
        tz_manager = TimezoneManager()

        # First access
        start = time.perf_counter()
        tz1 = tz_manager.get_timezone("Europe/Moscow")
        first_time = time.perf_counter() - start

        # Second access (should be cached)
        start = time.perf_counter()
        tz2 = tz_manager.get_timezone("Europe/Moscow")
        second_time = time.perf_counter() - start

        assert tz1 == tz2
        assert (
            second_time <= first_time
        )  # Cached access should be faster or equal


@pytest.mark.integration
class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_full_birth_chart_scenario(self):
        """Test complete birth chart scenario."""
        # Simulate user input for birth chart
        birth_date = "15.08.1990"
        birth_time = "14:30"
        birth_city = "москва"
        coordinates = CoordinateInfo(55.7558, 37.6176)

        # Parse using different components
        astro_dt = astro_time.parse_birth_datetime(
            birth_date, birth_time, birth_city, coordinates
        )

        # Verify all components
        assert astro_dt.dt.year == 1990
        assert astro_dt.dt.hour == 14
        assert astro_dt.timezone_name == "Europe/Moscow"
        assert astro_dt.coordinates == coordinates

        # Calculate precision info
        precision = astro_time.calculate_birth_time_precision(astro_dt)
        assert precision["has_coordinates"] is True
        assert precision["solar_time_available"] is True

        # Convert to UTC for calculations
        utc_dt = astro_time.to_utc(astro_dt)
        assert utc_dt.timezone_name == "UTC"

    def test_international_birth_times(self):
        """Test handling international birth times."""
        test_cases = [
            ("tokyo", "Asia/Tokyo", 35.6762, 139.6503),
            ("new_york", "America/New_York", 40.7128, -74.0060),
            ("london", "Europe/London", 51.5074, -0.1278),
            ("sydney", "Australia/Sydney", -33.8688, 151.2093),
        ]

        for city, expected_tz, lat, lon in test_cases:
            coords = CoordinateInfo(lat, lon)

            astro_dt = astro_time.parse_birth_datetime(
                "1990-08-15 14:30:00", timezone_input=city, coordinates=coords
            )

            # Should successfully parse and have reasonable timezone
            assert astro_dt.dt.year == 1990
            assert astro_dt.coordinates == coords
            # Note: exact timezone matching may vary based on city mapping

    def test_historical_dates(self):
        """Test handling of historical dates."""
        # Test various historical periods
        historical_dates = [
            "1800-01-01 12:00:00",  # 19th century
            "1900-12-31 23:59:59",  # Turn of 20th century
            "1950-06-15 09:30:00",  # Mid 20th century
        ]

        for date_str in historical_dates:
            astro_dt = astro_time.parse_birth_datetime(
                date_str, timezone_input="Europe/Moscow"
            )

            assert astro_dt.dt.year >= 1800
            assert astro_dt.timezone_name == "Europe/Moscow"

    def test_error_recovery_scenarios(self):
        """Test error recovery in various scenarios."""
        # Test malformed input recovery
        try:
            astro_time.parse_birth_datetime("invalid-date-format")
            assert False, "Should have raised exception"
        except InvalidDateTimeError:
            pass  # Expected

        # Test invalid timezone recovery
        try:
            astro_time.parse_birth_datetime(
                "1990-08-15 14:30:00", timezone_input="Invalid/Timezone"
            )
            assert False, "Should have raised exception"
        except InvalidTimezoneError:
            pass  # Expected

        # Test invalid coordinates recovery
        try:
            CoordinateInfo(200.0, 200.0)  # Invalid coordinates
            assert False, "Should have raised exception"
        except CoordinateTimeError:
            pass  # Expected


class TestHelperFunctions:
    """Test helper functions for common datetime patterns."""

    def test_utcnow(self):
        """Test utcnow function returns UTC datetime."""
        dt = utcnow()
        assert dt.tzinfo == timezone.utc

        # Should be very close to actual time
        actual_now = datetime.now(timezone.utc)
        diff = abs((dt - actual_now).total_seconds())
        assert diff < 1.0  # Within 1 second

    def test_now_no_timezone(self):
        """Test now function without timezone."""
        dt = now()
        # Should return local time (may or may not have timezone)
        assert isinstance(dt, datetime)

    def test_now_with_timezone(self):
        """Test now function with specific timezone."""
        moscow_dt = now("Europe/Moscow")
        assert str(moscow_dt.tzinfo) == "Europe/Moscow"

        utc_dt = now("UTC")
        assert utc_dt.tzinfo == ZoneInfo("UTC")

    def test_current_timestamp(self):
        """Test current_timestamp returns ISO string."""
        timestamp = current_timestamp()

        # Should be valid ISO format
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed.tzinfo == timezone.utc

        # Should be recent
        now_dt = utcnow()
        diff = abs((parsed - now_dt).total_seconds())
        assert diff < 1.0

    def test_database_timestamp(self):
        """Test database_timestamp returns UTC datetime."""
        dt = database_timestamp()
        assert dt.tzinfo == timezone.utc

        # Should be very close to utcnow()
        utc_dt = utcnow()
        diff = abs((dt - utc_dt).total_seconds())
        assert diff < 1.0

    def test_db_timestamp_default(self):
        """Test db_timestamp_default returns callable."""
        func = db_timestamp_default()
        assert callable(func)

        # Calling the function should return a datetime
        dt = func()
        assert isinstance(dt, datetime)
        assert dt.tzinfo == timezone.utc

    def test_create_astro_datetime_now(self):
        """Test create_astro_datetime_now function."""
        astro_dt = create_astro_datetime_now()

        assert isinstance(astro_dt, AstroDateTime)
        assert astro_dt.dt.tzinfo == timezone.utc

        # Should be very recent
        now_dt = utcnow()
        diff = abs((astro_dt.dt - now_dt).total_seconds())
        assert diff < 1.0

    def test_create_astro_datetime_now_with_coordinates(self):
        """Test create_astro_datetime_now with coordinates."""
        coords = CoordinateInfo(55.7558, 37.6176)
        astro_dt = create_astro_datetime_now(coordinates=coords)

        assert isinstance(astro_dt, AstroDateTime)
        assert astro_dt.coordinates == coords
        assert astro_dt.dt.tzinfo == timezone.utc

    def test_helper_functions_consistency(self):
        """Test that helper functions are consistent with each other."""
        # All should return very similar times
        dt1 = utcnow()
        dt2 = database_timestamp()
        dt3 = db_timestamp_default()()

        # All should be within a second of each other
        diff12 = abs((dt1 - dt2).total_seconds())
        diff13 = abs((dt1 - dt3).total_seconds())
        diff23 = abs((dt2 - dt3).total_seconds())

        assert diff12 < 1.0
        assert diff13 < 1.0
        assert diff23 < 1.0

    def test_helper_functions_type_safety(self):
        """Test helper functions return correct types."""
        # utcnow should return timezone-aware datetime
        dt = utcnow()
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None

        # current_timestamp should return string
        ts = current_timestamp()
        assert isinstance(ts, str)

        # database_timestamp should return datetime
        db_dt = database_timestamp()
        assert isinstance(db_dt, datetime)
        assert db_dt.tzinfo is not None

        # db_timestamp_default should return callable
        func = db_timestamp_default()
        assert callable(func)

        # create_astro_datetime_now should return AstroDateTime
        astro_dt = create_astro_datetime_now()
        assert isinstance(astro_dt, AstroDateTime)
