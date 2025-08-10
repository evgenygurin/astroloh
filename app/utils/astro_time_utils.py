"""
Centralized time, date, and timezone handling for Astroloh application.

This module provides a unified interface for all time-related operations,
replacing direct usage of datetime, pytz, and other time libraries throughout
the application. It includes comprehensive Russian timezone support, security
measures, and performance optimizations.

Key Features:
- Immutable AstroDateTime objects for thread safety
- Russian city timezone detection and mapping
- LRU caching for timezone operations (256 entries)
- Input validation with injection protection
- Local solar time calculations for astrology
- Database-optimized timestamp functions
- Performance monitoring and batch operations

Usage Examples:
    from app.utils.astro_time_utils import utcnow, now, create_astro_datetime
    
    # Current time operations
    current_utc = utcnow()
    moscow_time = now("Europe/Moscow")
    
    # Database operations
    from app.utils.astro_time_utils import db_timestamp_default
    created_at = Column(DateTime, default=db_timestamp_default())
    
    # Astrology-specific operations
    birth_time = create_astro_datetime("1990-01-01T12:00:00", "Москва")
"""

import re
import logging
from datetime import datetime, timezone, timedelta, date, time
from functools import lru_cache
from typing import Optional, Union, Dict, Any, List, Tuple, Callable
from zoneinfo import ZoneInfo
import calendar

# Configure logging
logger = logging.getLogger(__name__)

# Security patterns for input validation
DANGEROUS_PATTERNS = [
    r'[<>"\']',  # HTML/XML injection
    r'[\x00-\x1f\x7f-\x9f]',  # Control characters
    r'(union|select|insert|update|delete|drop|create|alter)',  # SQL injection
    r'(script|javascript|vbscript)',  # Script injection
]

# Compile patterns for performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]


class AstroDateTime:
    """
    Immutable datetime wrapper for astronomical calculations.
    
    Provides thread-safe datetime operations with timezone awareness,
    coordinate support, and astronomical context preservation.
    """
    
    def __init__(
        self,
        dt: datetime,
        timezone_name: Optional[str] = None,
        city_name: Optional[str] = None,
        coordinates: Optional[Tuple[float, float]] = None,
        is_solar_time: bool = False
    ):
        """
        Initialize AstroDateTime with comprehensive context.
        
        Args:
            dt: Base datetime object (must be timezone-aware)
            timezone_name: IANA timezone identifier
            city_name: City name for context
            coordinates: (latitude, longitude) tuple
            is_solar_time: Whether this represents local solar time
        """
        if dt.tzinfo is None:
            raise ValueError("AstroDateTime requires timezone-aware datetime")
        
        self._dt = dt
        self._timezone_name = timezone_name
        self._city_name = city_name
        self._coordinates = coordinates
        self._is_solar_time = is_solar_time
    
    @property
    def datetime(self) -> datetime:
        """Get the underlying datetime object."""
        return self._dt
    
    @property
    def timezone_name(self) -> Optional[str]:
        """Get the timezone name."""
        return self._timezone_name
    
    @property
    def city_name(self) -> Optional[str]:
        """Get the city name."""
        return self._city_name
    
    @property
    def coordinates(self) -> Optional[Tuple[float, float]]:
        """Get the coordinates as (latitude, longitude)."""
        return self._coordinates
    
    @property
    def is_solar_time(self) -> bool:
        """Check if this represents local solar time."""
        return self._is_solar_time
    
    def to_timezone(self, tz_name: str) -> 'AstroDateTime':
        """Convert to another timezone while preserving context."""
        try:
            new_tz = ZoneInfo(tz_name)
            new_dt = self._dt.astimezone(new_tz)
            return AstroDateTime(
                new_dt,
                tz_name,
                self._city_name,
                self._coordinates,
                self._is_solar_time
            )
        except Exception as e:
            logger.warning(f"Timezone conversion failed for {tz_name}: {e}")
            return self
    
    def to_utc(self) -> 'AstroDateTime':
        """Convert to UTC timezone."""
        return self.to_timezone("UTC")
    
    def isoformat(self) -> str:
        """Get ISO format string."""
        return self._dt.isoformat()
    
    def __str__(self) -> str:
        """String representation."""
        context = []
        if self._city_name:
            context.append(f"city={self._city_name}")
        if self._timezone_name:
            context.append(f"tz={self._timezone_name}")
        if self._is_solar_time:
            context.append("solar_time")
        
        context_str = f" ({', '.join(context)})" if context else ""
        return f"{self._dt.isoformat()}{context_str}"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"AstroDateTime({self._dt!r}, timezone_name={self._timezone_name!r}, "
                f"city_name={self._city_name!r}, coordinates={self._coordinates!r}, "
                f"is_solar_time={self._is_solar_time})")


# Russian timezone mapping with comprehensive city support
RUSSIAN_TIMEZONE_MAP = {
    # Калининградское время (UTC+2)
    "калининград": "Europe/Kaliningrad",
    
    # Московское время (UTC+3)
    "москва": "Europe/Moscow",
    "санкт-петербург": "Europe/Moscow",
    "спб": "Europe/Moscow",
    "питер": "Europe/Moscow",
    "воронеж": "Europe/Moscow",
    "нижний новгород": "Europe/Moscow",
    "ростов-на-дону": "Europe/Moscow",
    "краснодар": "Europe/Moscow",
    "сочи": "Europe/Moscow",
    "архангельск": "Europe/Moscow",
    "мурманск": "Europe/Moscow",
    "псков": "Europe/Moscow",
    "смоленск": "Europe/Moscow",
    "тула": "Europe/Moscow",
    "рязань": "Europe/Moscow",
    "владимир": "Europe/Moscow",
    "иваново": "Europe/Moscow",
    "ярославль": "Europe/Moscow",
    "кострома": "Europe/Moscow",
    "вологда": "Europe/Moscow",
    "череповец": "Europe/Moscow",
    "петрозаводск": "Europe/Moscow",
    "сыктывкар": "Europe/Moscow",
    
    # Самарское время (UTC+4)
    "самара": "Europe/Samara",
    "тольятти": "Europe/Samara",
    "ульяновск": "Europe/Samara",
    "саратов": "Europe/Samara",
    "волгоград": "Europe/Samara",
    "астрахань": "Europe/Samara",
    "оренбург": "Europe/Samara",
    "пенза": "Europe/Samara",
    
    # Екатеринбургское время (UTC+5)
    "екатеринбург": "Asia/Yekaterinburg",
    "челябинск": "Asia/Yekaterinburg",
    "уфа": "Asia/Yekaterinburg",
    "пермь": "Asia/Yekaterinburg",
    "тюмень": "Asia/Yekaterinburg",
    "курган": "Asia/Yekaterinburg",
    "ижевск": "Asia/Yekaterinburg",
    
    # Омское время (UTC+6)
    "омск": "Asia/Omsk",
    
    # Красноярское время (UTC+7)
    "красноярск": "Asia/Krasnoyarsk",
    "новосибирск": "Asia/Novosibirsk",
    "кемерово": "Asia/Krasnoyarsk",
    "барнаул": "Asia/Krasnoyarsk",
    "томск": "Asia/Krasnoyarsk",
    "абакан": "Asia/Krasnoyarsk",
    "кызыл": "Asia/Krasnoyarsk",
    
    # Иркутское время (UTC+8)
    "иркутск": "Asia/Irkutsk",
    "улан-удэ": "Asia/Irkutsk",
    "чита": "Asia/Irkutsk",
    
    # Якутское время (UTC+9)
    "якутск": "Asia/Yakutsk",
    "благовещенск": "Asia/Yakutsk",
    "комсомольск-на-амуре": "Asia/Yakutsk",
    
    # Владивостокское время (UTC+10)
    "владивосток": "Asia/Vladivostok",
    "хабаровск": "Asia/Vladivostok",
    "уссурийск": "Asia/Vladivostok",
    "находка": "Asia/Vladivostok",
    "биробиджан": "Asia/Vladivostok",
    
    # Магаданское время (UTC+11)
    "магадан": "Asia/Magadan",
    "южно-сахалинск": "Asia/Magadan",
    
    # Камчатское время (UTC+12)
    "петропавловск-камчатский": "Asia/Kamchatka",
    "анадырь": "Asia/Kamchatka",
}


@lru_cache(maxsize=256)
def get_timezone_info(tz_identifier: str) -> Dict[str, Any]:
    """
    Get comprehensive timezone information with caching.
    
    Args:
        tz_identifier: IANA timezone identifier or Russian city name
        
    Returns:
        Dictionary with timezone information
    """
    try:
        # Check if it's a Russian city name
        city_lower = tz_identifier.lower().strip()
        if city_lower in RUSSIAN_TIMEZONE_MAP:
            tz_name = RUSSIAN_TIMEZONE_MAP[city_lower]
            logger.info(f"ASTRO_TIME_UTILS: Russian city {tz_identifier} -> {tz_name}")
        else:
            tz_name = tz_identifier
        
        # Get timezone object
        tz = ZoneInfo(tz_name)
        now_dt = datetime.now(tz)
        
        return {
            "zone": tz_name,
            "name": tz_name,
            "offset": now_dt.strftime("%z"),
            "offset_seconds": now_dt.utcoffset().total_seconds(),
            "dst": now_dt.dst() is not None and now_dt.dst().total_seconds() > 0,
            "city_name": tz_identifier if city_lower in RUSSIAN_TIMEZONE_MAP else None
        }
    except Exception as e:
        logger.warning(f"ASTRO_TIME_UTILS: Timezone error for {tz_identifier}: {e}")
        # Fallback to Moscow time
        return {
            "zone": "Europe/Moscow",
            "name": "Europe/Moscow",
            "offset": "+0300",
            "offset_seconds": 10800,
            "dst": False,
            "city_name": None
        }


def validate_input(value: str, max_length: int = 100) -> str:
    """
    Validate and sanitize input strings for security.
    
    Args:
        value: Input string to validate
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValueError: If input contains dangerous patterns
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")
    
    if len(value) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")
    
    # Check for dangerous patterns
    for pattern in COMPILED_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Input contains potentially dangerous content")
    
    return value.strip()


def utcnow() -> datetime:
    """
    Get current UTC time.
    
    Replacement for datetime.utcnow() with timezone awareness.
    
    Returns:
        Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def now(tz: Optional[str] = None) -> datetime:
    """
    Get current time in specified timezone.
    
    Args:
        tz: Timezone identifier (IANA or Russian city name)
        
    Returns:
        Current datetime in specified timezone
    """
    if tz is None:
        return datetime.now(timezone.utc)
    
    try:
        tz_info = get_timezone_info(tz)
        zone = ZoneInfo(tz_info["zone"])
        return datetime.now(zone)
    except Exception as e:
        logger.warning(f"ASTRO_TIME_UTILS: Error getting time for {tz}: {e}")
        return datetime.now(timezone.utc)


def current_timestamp() -> str:
    """
    Get current timestamp as ISO string.
    
    Returns:
        ISO format timestamp string
    """
    return utcnow().isoformat()


def database_timestamp() -> datetime:
    """
    Get UTC datetime optimized for database storage.
    
    Returns:
        UTC datetime for database operations
    """
    return utcnow()


def db_timestamp_default() -> Callable[[], datetime]:
    """
    Factory function for SQLAlchemy default timestamps.
    
    Returns:
        Lambda function for SQLAlchemy default parameter
    """
    return lambda: database_timestamp()


def create_astro_datetime(
    dt_input: Union[str, datetime],
    timezone_or_city: Optional[str] = None,
    coordinates: Optional[Tuple[float, float]] = None
) -> AstroDateTime:
    """
    Create AstroDateTime from various input formats.
    
    Args:
        dt_input: Datetime string or datetime object
        timezone_or_city: Timezone identifier or Russian city name
        coordinates: Optional (latitude, longitude) tuple
        
    Returns:
        AstroDateTime object with full context
    """
    # Parse datetime input
    if isinstance(dt_input, str):
        dt_input = validate_input(dt_input, 50)
        try:
            if 'T' in dt_input:
                dt = datetime.fromisoformat(dt_input.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(dt_input)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {dt_input}") from e
    else:
        dt = dt_input
    
    # Handle timezone
    tz_name = None
    city_name = None
    
    if timezone_or_city:
        timezone_or_city = validate_input(timezone_or_city, 50)
        tz_info = get_timezone_info(timezone_or_city)
        tz_name = tz_info["zone"]
        city_name = tz_info.get("city_name")
        
        # Apply timezone if datetime is naive
        if dt.tzinfo is None:
            zone = ZoneInfo(tz_name)
            dt = dt.replace(tzinfo=zone)
        else:
            # Convert to specified timezone
            zone = ZoneInfo(tz_name)
            dt = dt.astimezone(zone)
    elif dt.tzinfo is None:
        # Default to UTC for naive datetimes
        dt = dt.replace(tzinfo=timezone.utc)
        tz_name = "UTC"
    
    return AstroDateTime(
        dt=dt,
        timezone_name=tz_name,
        city_name=city_name,
        coordinates=coordinates
    )


def create_astro_datetime_now(
    timezone_or_city: Optional[str] = None,
    coordinates: Optional[Tuple[float, float]] = None
) -> AstroDateTime:
    """
    Create AstroDateTime for current time.
    
    Args:
        timezone_or_city: Timezone identifier or Russian city name
        coordinates: Optional (latitude, longitude) tuple
        
    Returns:
        AstroDateTime for current time
    """
    current_dt = now(timezone_or_city)
    
    tz_name = None
    city_name = None
    
    if timezone_or_city:
        tz_info = get_timezone_info(timezone_or_city)
        tz_name = tz_info["zone"]
        city_name = tz_info.get("city_name")
    
    return AstroDateTime(
        dt=current_dt,
        timezone_name=tz_name,
        city_name=city_name,
        coordinates=coordinates
    )


def parse_datetime_safe(
    dt_string: str,
    default_tz: str = "UTC"
) -> datetime:
    """
    Safely parse datetime string with validation.
    
    Args:
        dt_string: Datetime string to parse
        default_tz: Default timezone if none specified
        
    Returns:
        Parsed datetime object
    """
    dt_string = validate_input(dt_string, 50)
    
    try:
        # Handle various formats
        if 'T' in dt_string:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(dt_string)
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            tz_info = get_timezone_info(default_tz)
            zone = ZoneInfo(tz_info["zone"])
            dt = dt.replace(tzinfo=zone)
        
        return dt
    except Exception as e:
        logger.error(f"ASTRO_TIME_UTILS: Parse error for '{dt_string}': {e}")
        raise ValueError(f"Invalid datetime format: {dt_string}") from e


def calculate_local_solar_time(
    dt: datetime,
    longitude: float,
    timezone_name: Optional[str] = None
) -> AstroDateTime:
    """
    Calculate local solar time for astronomical calculations.
    
    Args:
        dt: Base datetime
        longitude: Longitude in degrees
        timezone_name: Optional timezone name for context
        
    Returns:
        AstroDateTime representing local solar time
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to UTC for calculation
    utc_dt = dt.astimezone(timezone.utc)
    
    # Calculate solar time offset (4 minutes per degree of longitude)
    solar_offset_minutes = longitude * 4
    solar_offset = timedelta(minutes=solar_offset_minutes)
    
    # Apply solar time correction
    solar_dt = utc_dt + solar_offset
    
    return AstroDateTime(
        dt=solar_dt,
        timezone_name=timezone_name,
        coordinates=(None, longitude),
        is_solar_time=True
    )


def get_timezone_for_coordinates(
    latitude: float,
    longitude: float
) -> str:
    """
    Get approximate timezone for coordinates.
    
    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees
        
    Returns:
        IANA timezone identifier
    """
    # Simple longitude-based timezone estimation
    # This is a basic implementation - for production use a proper timezone library
    
    # Rough timezone calculation (15 degrees per hour)
    tz_offset_hours = round(longitude / 15)
    
    # Clamp to valid range
    tz_offset_hours = max(-12, min(14, tz_offset_hours))
    
    # Map to common timezones
    timezone_map = {
        -12: "Pacific/Kwajalein",
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
        0: "UTC",
        1: "Europe/London",
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
        13: "Pacific/Tongatapu",
        14: "Pacific/Kiritimati"
    }
    
    return timezone_map.get(tz_offset_hours, "UTC")


def batch_create_astro_datetimes(
    datetime_data: List[Dict[str, Any]]
) -> List[AstroDateTime]:
    """
    Create multiple AstroDateTime objects efficiently.
    
    Args:
        datetime_data: List of dictionaries with datetime creation parameters
        
    Returns:
        List of AstroDateTime objects
    """
    results = []
    
    for data in datetime_data:
        try:
            astro_dt = create_astro_datetime(
                dt_input=data.get("datetime"),
                timezone_or_city=data.get("timezone"),
                coordinates=data.get("coordinates")
            )
            results.append(astro_dt)
        except Exception as e:
            logger.warning(f"ASTRO_TIME_UTILS: Batch creation error: {e}")
            # Add fallback UTC datetime
            fallback_dt = AstroDateTime(
                dt=utcnow(),
                timezone_name="UTC"
            )
            results.append(fallback_dt)
    
    return results


def format_for_display(
    dt: Union[datetime, AstroDateTime],
    format_type: str = "iso",
    locale: str = "ru"
) -> str:
    """
    Format datetime for display with localization support.
    
    Args:
        dt: Datetime or AstroDateTime object
        format_type: Format type ("iso", "human", "short")
        locale: Locale for formatting ("ru", "en")
        
    Returns:
        Formatted datetime string
    """
    if isinstance(dt, AstroDateTime):
        dt = dt.datetime
    
    if format_type == "iso":
        return dt.isoformat()
    elif format_type == "human":
        if locale == "ru":
            months_ru = [
                "января", "февраля", "марта", "апреля", "мая", "июня",
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            return f"{dt.day} {months_ru[dt.month-1]} {dt.year} г., {dt.strftime('%H:%M')}"
        else:
            return dt.strftime("%B %d, %Y at %H:%M")
    elif format_type == "short":
        return dt.strftime("%Y-%m-%d %H:%M")
    else:
        return dt.isoformat()


# Performance monitoring utilities
def measure_time_operation(operation_name: str):
    """
    Decorator for measuring time operation performance.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = utcnow()
            try:
                result = func(*args, **kwargs)
                end_time = utcnow()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"ASTRO_TIME_UTILS_PERF: {operation_name} took {duration:.3f}s")
                return result
            except Exception as e:
                end_time = utcnow()
                duration = (end_time - start_time).total_seconds()
                logger.error(f"ASTRO_TIME_UTILS_PERF: {operation_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator


# Cache statistics
def get_cache_stats() -> Dict[str, Any]:
    """
    Get timezone cache statistics.
    
    Returns:
        Dictionary with cache performance metrics
    """
    cache_info = get_timezone_info.cache_info()
    return {
        "hits": cache_info.hits,
        "misses": cache_info.misses,
        "maxsize": cache_info.maxsize,
        "currsize": cache_info.currsize,
        "hit_rate": cache_info.hits / (cache_info.hits + cache_info.misses) if (cache_info.hits + cache_info.misses) > 0 else 0.0
    }


def clear_timezone_cache():
    """Clear the timezone information cache."""
    get_timezone_info.cache_clear()
    logger.info("ASTRO_TIME_UTILS: Timezone cache cleared")


# Module initialization
logger.info("ASTRO_TIME_UTILS: Module initialized with Russian timezone support")
logger.info(f"ASTRO_TIME_UTILS: Loaded {len(RUSSIAN_TIMEZONE_MAP)} Russian cities")

