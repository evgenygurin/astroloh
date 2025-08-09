"""
Advanced time handling utilities for astrological calculations.
Provides secure, performant, and timezone-aware datetime operations.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union
from zoneinfo import ZoneInfo, available_timezones

from loguru import logger

# Optional TimezoneFinder for accurate coordinate-based timezone detection
try:
    from timezonefinder import TimezoneFinder
    TIMEZONEFINDER_AVAILABLE = True
except ImportError:
    TIMEZONEFINDER_AVAILABLE = False
    TimezoneFinder = None


class AstroTimeError(Exception):
    pass


class InvalidTimezoneError(AstroTimeError):
    pass


class InvalidDateTimeError(AstroTimeError):
    pass


class CoordinateTimeError(AstroTimeError):
    pass


@dataclass(frozen=True)
class CoordinateInfo:
    latitude: float
    longitude: float
    altitude: Optional[float] = None

    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise CoordinateTimeError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise CoordinateTimeError(f"Invalid longitude: {self.longitude}")
        if self.altitude is not None and not (-1000 <= self.altitude <= 10000):
            raise CoordinateTimeError(f"Invalid altitude: {self.altitude}")


@dataclass(frozen=True)
class AstroDateTime:
    dt: datetime
    timezone_name: str
    coordinates: Optional[CoordinateInfo] = None
    source_format: Optional[str] = None

    def __post_init__(self):
        if self.dt.tzinfo is None:
            raise InvalidDateTimeError("Datetime must be timezone-aware")

        min_date = datetime(1, 1, 1, tzinfo=timezone.utc)
        max_date = datetime(3000, 12, 31, tzinfo=timezone.utc)

        if not (min_date <= self.dt.replace(tzinfo=timezone.utc) <= max_date):
            raise InvalidDateTimeError(f"Date {self.dt} is outside supported range")

    @property
    def utc(self) -> datetime:
        return self.dt.astimezone(timezone.utc)

    @property
    def local_solar_time_offset(self) -> Optional[timedelta]:
        if not self.coordinates:
            return None
        return timedelta(hours=self.coordinates.longitude / 15.0)

    def to_local_solar_time(self) -> Optional[datetime]:
        if not self.coordinates:
            return None
        offset = self.local_solar_time_offset
        return self.utc + offset if offset else None


class TimezoneManager:
    """Timezone manager with caching and validation."""

    def __init__(self):
        self._timezone_cache: Dict[str, ZoneInfo] = {}
        self._city_timezone_mapping: Dict[str, str] = {}
        self._load_city_mappings()

    def _load_city_mappings(self):
        city_mappings = {
            # Russia
            "москва": "Europe/Moscow",
            "moscow": "Europe/Moscow",
            "санкт-петербург": "Europe/Moscow",
            "petersburg": "Europe/Moscow",
            "spb": "Europe/Moscow",
            "новосибирск": "Asia/Novosibirsk",
            "novosibirsk": "Asia/Novosibirsk",
            "екатеринбург": "Asia/Yekaterinburg",
            "yekaterinburg": "Asia/Yekaterinburg",
            "сочи": "Europe/Moscow",
            "sochi": "Europe/Moscow",
            # Major world cities
            "london": "Europe/London",
            "лондон": "Europe/London",
            "paris": "Europe/Paris",
            "париж": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "берлин": "Europe/Berlin",
            "new_york": "America/New_York",
            "нью-йорк": "America/New_York",
            "los_angeles": "America/Los_Angeles",
            "лос-анджелес": "America/Los_Angeles",
            "tokyo": "Asia/Tokyo",
            "токио": "Asia/Tokyo",
            "beijing": "Asia/Shanghai",
            "пекин": "Asia/Shanghai",
            "sydney": "Australia/Sydney",
            "сидней": "Australia/Sydney",
            "mumbai": "Asia/Kolkata",
            "мумбаи": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "дели": "Asia/Kolkata",
        }

        self._city_timezone_mapping.update(city_mappings)

    @lru_cache(maxsize=256)
    def get_timezone(self, tz_identifier: str) -> ZoneInfo:
        if not tz_identifier:
            raise InvalidTimezoneError("Timezone identifier cannot be empty")

        tz_id_normalized = tz_identifier.strip().lower()

        if tz_id_normalized in self._city_timezone_mapping:
            tz_id = self._city_timezone_mapping[tz_id_normalized]
        else:
            tz_id = tz_identifier.strip()

        if tz_id not in available_timezones():
            raise InvalidTimezoneError(f"Timezone '{tz_identifier}' is not available")

        try:
            return ZoneInfo(tz_id)
        except Exception as e:
            raise InvalidTimezoneError(f"Failed to load timezone '{tz_id}': {e}")

    def detect_timezone_from_coordinates(self, latitude: float, longitude: float) -> str:
        """Detect timezone from coordinates using TimezoneFinder when available, else fallback to longitude-based estimation."""
        if TIMEZONEFINDER_AVAILABLE and TimezoneFinder is not None:
            try:
                tf = TimezoneFinder()
                tz_id = tf.timezone_at(lng=longitude, lat=latitude)
                if tz_id and tz_id in available_timezones():
                    return tz_id
            except Exception as exc:  # pragma: no cover
                logger.debug(f"TimezoneFinder failed, fallback to estimate: {exc}")

        utc_offset = round(longitude / 15.0)
        timezone_map = {
            -12: "Pacific/Auckland",
            -11: "Pacific/Midway",
            -10: "Pacific/Honolulu",
            -9: "America/Anchorage",
            -8: "America/Los_Angeles",
            -7: "America/Denver",
            -6: "America/Chicago",
            -5: "America/New_York",
            -4: "America/Halifax",
            -3: "America/Sao_Paulo",
            -2: "Atlantic/South_Georgia",
            -1: "Atlantic/Azores",
            0: "Europe/London",
            1: "Europe/Paris",
            2: "Europe/Berlin",
            3: "Europe/Moscow",
            4: "Asia/Dubai",
            5: "Asia/Karachi",
            6: "Asia/Dhaka",
            7: "Asia/Bangkok",
            8: "Asia/Shanghai",
            9: "Asia/Tokyo",
            10: "Australia/Sydney",
            11: "Pacific/Norfolk",
            12: "Pacific/Auckland",
        }

        return timezone_map.get(utc_offset, "UTC")

    def validate_timezone_name(self, tz_name: str) -> bool:
        try:
            self.get_timezone(tz_name)
            return True
        except InvalidTimezoneError:
            return False


class DateTimeValidator:
    """Datetime validation and parsing."""

    SUPPORTED_FORMATS = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]

    DANGEROUS_PATTERNS = [
        r"[<>\"'`]",
        r"\\x[0-9a-fA-F]{2}",
        r"\\[0-7]{3}",
        r"\.\./",
        r"[\r\n\0]",
    ]

    @classmethod
    def sanitize_input(cls, input_str: str) -> str:
        if len(input_str) > 50:
            raise InvalidDateTimeError("Input string too long")
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, input_str):
                raise InvalidDateTimeError(f"Invalid characters in input: {input_str}")
        return input_str.strip()

    @classmethod
    def parse_datetime_string(cls, dt_string: str, default_timezone: str = "UTC") -> datetime:
        sanitized = cls.sanitize_input(dt_string)
        for fmt in cls.SUPPORTED_FORMATS:
            try:
                parsed_dt = datetime.strptime(sanitized, fmt)
                if parsed_dt.tzinfo is None:
                    tz = ZoneInfo(default_timezone)
                    parsed_dt = parsed_dt.replace(tzinfo=tz)
                return parsed_dt
            except ValueError:
                continue
        raise InvalidDateTimeError(f"Could not parse datetime: {dt_string}")

    @classmethod
    def validate_birth_datetime(
        cls, dt: datetime, coordinates: Optional[CoordinateInfo] = None
    ) -> bool:
        if dt.tzinfo is None:
            return False
        if dt > datetime.now(timezone.utc):
            return False
        min_year = 1000
        max_year = datetime.now().year + 1
        if not (min_year <= dt.year <= max_year):
            return False
        if coordinates:
            expected_tz = TimezoneManager().detect_timezone_from_coordinates(
                coordinates.latitude, coordinates.longitude
            )
            if expected_tz:
                logger.debug(f"Expected timezone {expected_tz} for coordinates")
        return True


class CoordinateTimeCalculator:
    """Calculate time-related values based on geographical coordinates."""

    @staticmethod
    def calculate_solar_time_offset(longitude: float) -> timedelta:
        hours_offset = longitude / 15.0
        return timedelta(hours=hours_offset)

    @staticmethod
    def calculate_local_mean_time(dt_utc: datetime, longitude: float) -> datetime:
        solar_offset = CoordinateTimeCalculator.calculate_solar_time_offset(longitude)
        return dt_utc + solar_offset

    @staticmethod
    def estimate_timezone_from_coordinates(latitude: float, longitude: float) -> str:
        """Estimate timezone identifier from coordinates. Uses TimezoneFinder if available, else longitude-based fallback."""
        if TIMEZONEFINDER_AVAILABLE and TimezoneFinder is not None:
            try:
                tf = TimezoneFinder()
                tz_id = tf.timezone_at(lng=longitude, lat=latitude)
                if tz_id and tz_id in available_timezones():
                    return tz_id
            except Exception as exc:  # pragma: no cover
                logger.debug(f"TimezoneFinder failed, fallback to estimate: {exc}")

        utc_offset_hours = round(longitude / 15.0)
        offset_to_tz = {
            -12: "Pacific/Majuro",
            -11: "Pacific/Midway",
            -10: "Pacific/Honolulu",
            -9: "America/Anchorage",
            -8: "America/Los_Angeles",
            -7: "America/Denver",
            -6: "America/Chicago",
            -5: "America/New_York",
            -4: "America/Halifax",
            -3: "America/Sao_Paulo",
            -2: "Atlantic/South_Georgia",
            -1: "Atlantic/Azores",
            0: "Europe/London",
            1: "Europe/Paris",
            2: "Europe/Berlin",
            3: "Europe/Moscow",
            4: "Asia/Dubai",
            5: "Asia/Karachi",
            6: "Asia/Dhaka",
            7: "Asia/Bangkok",
            8: "Asia/Shanghai",
            9: "Asia/Tokyo",
            10: "Australia/Sydney",
            11: "Pacific/Norfolk",
            12: "Pacific/Auckland",
        }
        return offset_to_tz.get(utc_offset_hours, "UTC")


class AstroTimeUtils:
    """Main utils for time operations."""

    def __init__(self):
        self.timezone_manager = TimezoneManager()
        self.validator = DateTimeValidator()
        self.coord_calculator = CoordinateTimeCalculator()

    def parse_birth_datetime(
        self,
        date_input: Union[str, datetime],
        time_input: Optional[str] = None,
        timezone_input: Optional[str] = None,
        coordinates: Optional[CoordinateInfo] = None,
    ) -> AstroDateTime:
        # Handle string input
        if isinstance(date_input, str):
            combined = f"{date_input} {time_input}".strip() if time_input else date_input.strip()

            if timezone_input:
                # Resolve to IANA via manager (supports city names)
                tz = self.timezone_manager.get_timezone(timezone_input)
                tz_name = str(tz)
            elif coordinates:
                tz_name = self.coord_calculator.estimate_timezone_from_coordinates(
                    coordinates.latitude, coordinates.longitude
                )
            else:
                tz_name = "UTC"

            parsed_dt = self.validator.parse_datetime_string(combined, tz_name)

        elif isinstance(date_input, datetime):
            parsed_dt = date_input
            tz_name = str(parsed_dt.tzinfo) if parsed_dt.tzinfo else "UTC"

            if parsed_dt.tzinfo is None:
                if timezone_input:
                    tz = self.timezone_manager.get_timezone(timezone_input)
                    parsed_dt = parsed_dt.replace(tzinfo=tz)
                    tz_name = str(tz)
                else:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                    tz_name = "UTC"
        else:
            raise InvalidDateTimeError(f"Unsupported date input type: {type(date_input)}")

        if not self.validator.validate_birth_datetime(parsed_dt, coordinates):
            raise InvalidDateTimeError("Invalid birth datetime")

        return AstroDateTime(
            dt=parsed_dt,
            timezone_name=tz_name,
            coordinates=coordinates,
            source_format=f"{type(date_input).__name__}_input",
        )

    def convert_timezone(self, astro_dt: AstroDateTime, target_timezone: str) -> AstroDateTime:
        target_tz = self.timezone_manager.get_timezone(target_timezone)
        converted_dt = astro_dt.dt.astimezone(target_tz)
        return AstroDateTime(
            dt=converted_dt,
            timezone_name=target_timezone,
            coordinates=astro_dt.coordinates,
            source_format=astro_dt.source_format,
        )

    def to_utc(self, astro_dt: AstroDateTime) -> AstroDateTime:
        return self.convert_timezone(astro_dt, "UTC")

    def calculate_birth_time_precision(self, astro_dt: AstroDateTime) -> Dict[str, Any]:
        precision_info: Dict[str, Any] = {
            "has_seconds": astro_dt.dt.second > 0,
            "has_coordinates": astro_dt.coordinates is not None,
            "timezone_source": "coordinates" if astro_dt.coordinates else "explicit",
            "solar_time_available": astro_dt.coordinates is not None,
        }
        if astro_dt.coordinates:
            solar_time = astro_dt.to_local_solar_time()
            if solar_time:
                precision_info["local_solar_time"] = solar_time.isoformat()
                offset = astro_dt.local_solar_time_offset
                if offset:
                    precision_info["solar_time_offset_minutes"] = offset.total_seconds() / 60
        return precision_info

    def batch_convert_timezones(
        self, astro_datetimes: List[AstroDateTime], target_timezone: str
    ) -> List[AstroDateTime]:
        target_tz = self.timezone_manager.get_timezone(target_timezone)
        results: List[AstroDateTime] = []
        for astro_dt in astro_datetimes:
            converted_dt = astro_dt.dt.astimezone(target_tz)
            results.append(
                AstroDateTime(
                    dt=converted_dt,
                    timezone_name=target_timezone,
                    coordinates=astro_dt.coordinates,
                    source_format=astro_dt.source_format,
                )
            )
        return results

    def create_astro_datetime_builder(self):
        return AstroDateTimeBuilder(self)


class AstroDateTimeBuilder:
    def __init__(self, utils: AstroTimeUtils):
        self.utils = utils
        self._date: Optional[str] = None
        self._time: Optional[str] = None
        self._timezone: Optional[str] = None
        self._coordinates: Optional[CoordinateInfo] = None
        self._datetime_obj: Optional[datetime] = None

    def date(self, date_str: str) -> "AstroDateTimeBuilder":
        self._date = date_str
        return self

    def time(self, time_str: str) -> "AstroDateTimeBuilder":
        self._time = time_str
        return self

    def timezone(self, tz_str: str) -> "AstroDateTimeBuilder":
        self._timezone = tz_str
        return self

    def coordinates(
        self, latitude: float, longitude: float, altitude: Optional[float] = None
    ) -> "AstroDateTimeBuilder":
        self._coordinates = CoordinateInfo(latitude, longitude, altitude)
        return self

    def from_datetime(self, dt: datetime) -> "AstroDateTimeBuilder":
        self._datetime_obj = dt
        return self

    def build(self) -> AstroDateTime:
        if self._datetime_obj:
            return self.utils.parse_birth_datetime(
                self._datetime_obj,
                timezone_input=self._timezone,
                coordinates=self._coordinates,
            )
        elif self._date:
            return self.utils.parse_birth_datetime(
                self._date,
                time_input=self._time,
                timezone_input=self._timezone,
                coordinates=self._coordinates,
            )
        else:
            raise InvalidDateTimeError("Must provide either date or datetime object")


astro_time = AstroTimeUtils()
