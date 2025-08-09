"""
Comprehensive tests for astro_time_utils module.
Tests all aspects of time handling including edge cases, security, and performance.
"""

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

        astro_dt = AstroDateTime(dt=dt, timezone_name="Europe/Moscow", coordinates=coords)
        precision = utils.calculate_birth_time_precision(astro_dt)

        assert precision["has_seconds"] is True
        assert precision["has_coordinates"] is True
        assert precision["timezone_source"] in ["coordinates", "explicit"]
        if precision["solar_time_available"]:
            assert "local_solar_time" in precision
            assert "solar_time_offset_minutes" in precision

    def test_batch_convert_timezones(self, utils):
        """Test batch timezone conversion."""
        dt1 = AstroDateTime(dt=datetime(1990, 8, 15, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")), timezone_name="Europe/Moscow")
        dt2 = AstroDateTime(dt=datetime(1991, 5, 10, 9, 15, tzinfo=ZoneInfo("America/New_York")), timezone_name="America/New_York")

        results = utils.batch_convert_timezones([dt1, dt2], "UTC")

        assert all(r.timezone_name == "UTC" for r in results)
        assert results[0].dt.tzinfo == ZoneInfo("UTC")
        assert results[1].dt.tzinfo == ZoneInfo("UTC")

    def test_invalid_input_type(self, utils):
        """Test invalid input type handling."""
        with pytest.raises(InvalidDateTimeError):
            utils.parse_birth_datetime(12345)  # Invalid type


class TestBuilder:
    """Test AstroDateTimeBuilder functionality."""

    def test_builder_from_strings(self):
        builder = astro_time.create_astro_datetime_builder()
        astro_dt = (
            builder
            .date("1990-08-15")
            .time("14:30:00")
            .timezone("Europe/Moscow")
            .coordinates(55.7558, 37.6176)
            .build()
        )

        assert astro_dt.timezone_name == "Europe/Moscow"

    def test_builder_from_datetime(self):
        builder = astro_time.create_astro_datetime_builder()
        astro_dt = (
            builder
            .from_datetime(datetime(1990, 8, 15, 14, 30))
            .timezone("Europe/Moscow")
            .coordinates(55.7558, 37.6176)
            .build()
        )

        assert astro_dt.dt.tzinfo is not None


class TestGlobalInstance:
    """Test global astro_time instance."""

    def test_global_instance_available(self):
        assert isinstance(astro_time, AstroTimeUtils)
