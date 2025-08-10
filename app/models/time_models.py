"""
Pydantic models for time handling and validation.
Integrates with astro_time_utils for type-safe API operations.
"""

import datetime as dt
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.astro_time_utils import (
    AstroDateTime,
    CoordinateInfo,
    CoordinateTimeError,
    InvalidDateTimeError,
    InvalidTimezoneError,
    astro_time,
)


class CoordinateModel(BaseModel):
    """Pydantic model for geographical coordinates with validation."""

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90 to 90)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180 to 180)",
    )
    altitude: Optional[float] = Field(
        None,
        ge=-1000.0,
        le=10000.0,
        description="Altitude in meters (-1000 to 10000)",
    )

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude bounds."""
        if not -90.0 <= v <= 90.0:
            raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude bounds."""
        if not -180.0 <= v <= 180.0:
            raise ValueError(
                f"Longitude must be between -180 and 180, got {v}"
            )
        return v

    def to_coordinate_info(self) -> CoordinateInfo:
        """Convert to CoordinateInfo object."""
        return CoordinateInfo(
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
        )

    @classmethod
    def from_coordinate_info(
        cls, coord_info: CoordinateInfo
    ) -> "CoordinateModel":
        """Create from CoordinateInfo object."""
        return cls(
            latitude=coord_info.latitude,
            longitude=coord_info.longitude,
            altitude=coord_info.altitude,
        )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "latitude": 55.7558,
                    "longitude": 37.6176,
                    "altitude": 150.0,
                    "description": "Moscow coordinates",
                },
                {
                    "latitude": 59.9311,
                    "longitude": 30.3609,
                    "description": "Saint Petersburg coordinates",
                },
            ]
        }


class TimeInputModel(BaseModel):
    """Pydantic model for time input validation and parsing."""

    date_input: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Date string in various formats (ISO, European, etc.)",
    )
    time_input: Optional[str] = Field(
        None, max_length=20, description="Time string (HH:MM or HH:MM:SS)"
    )
    timezone_input: Optional[str] = Field(
        None,
        max_length=50,
        description="Timezone string (IANA name or city name)",
    )
    coordinates: Optional[CoordinateModel] = Field(
        None, description="Coordinates for timezone detection"
    )

    @field_validator("date_input")
    @classmethod
    def validate_date_input(cls, v: str) -> str:
        """Validate and sanitize date input."""
        if not v or not v.strip():
            raise ValueError("Date input cannot be empty")

        # Basic security validation
        dangerous_chars = ["<", ">", '"', "'", "`", "\\", "\n", "\r", "\0"]
        if any(char in v for char in dangerous_chars):
            raise ValueError("Date input contains invalid characters")

        return v.strip()

    @field_validator("time_input")
    @classmethod
    def validate_time_input(cls, v: Optional[str]) -> Optional[str]:
        """Validate time input format."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # Basic format validation
        if not (5 <= len(v) <= 8):  # HH:MM to HH:MM:SS
            raise ValueError("Time format should be HH:MM or HH:MM:SS")

        return v

    @field_validator("timezone_input")
    @classmethod
    def validate_timezone_input(cls, v: Optional[str]) -> Optional[str]:
        """Validate timezone input."""
        if v is None:
            return v

        v = v.strip()
        if not v:
            return None

        # Length validation
        if len(v) > 50:
            raise ValueError("Timezone input too long")

        return v

    def parse_to_astro_datetime(self) -> AstroDateTime:
        """Parse input to AstroDateTime using astro_time_utils."""
        try:
            coordinates = None
            if self.coordinates:
                coordinates = self.coordinates.to_coordinate_info()

            return astro_time.parse_birth_datetime(
                date_input=self.date_input,
                time_input=self.time_input,
                timezone_input=self.timezone_input,
                coordinates=coordinates,
            )
        except (
            InvalidDateTimeError,
            InvalidTimezoneError,
            CoordinateTimeError,
        ) as e:
            raise ValueError(f"Failed to parse datetime: {str(e)}")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "date_input": "15.08.1990",
                    "time_input": "14:30:00",
                    "timezone_input": "Europe/Moscow",
                    "coordinates": {"latitude": 55.7558, "longitude": 37.6176},
                },
                {
                    "date_input": "1990-08-15T14:30:00",
                    "timezone_input": "москва",
                },
                {
                    "date_input": "15/08/1990",
                    "time_input": "14:30",
                    "coordinates": {"latitude": 55.7558, "longitude": 37.6176},
                },
            ]
        }


class TimePrecisionModel(BaseModel):
    """Model for time precision metadata."""

    has_seconds: bool = Field(
        ..., description="Whether the time includes seconds precision"
    )
    has_coordinates: bool = Field(
        ..., description="Whether coordinates are available"
    )
    timezone_source: str = Field(
        ..., description="Source of timezone (coordinates, explicit, default)"
    )
    solar_time_available: bool = Field(
        ..., description="Whether local solar time can be calculated"
    )
    local_solar_time: Optional[str] = Field(
        None, description="Local solar time in ISO format"
    )
    solar_time_offset_minutes: Optional[float] = Field(
        None, description="Solar time offset in minutes from UTC"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "has_seconds": True,
                "has_coordinates": True,
                "timezone_source": "coordinates",
                "solar_time_available": True,
                "local_solar_time": "1990-08-15T16:30:00",
                "solar_time_offset_minutes": 150.0,
            }
        }


class AstroDateTimeModel(BaseModel):
    """Pydantic model for AstroDateTime serialization."""

    datetime: dt.datetime = Field(..., description="Timezone-aware datetime")
    timezone_name: str = Field(..., description="Name of the timezone")
    coordinates: Optional[CoordinateModel] = Field(
        None, description="Associated coordinates"
    )
    source_format: Optional[str] = Field(
        None, description="Original input format identifier"
    )
    precision: Optional[TimePrecisionModel] = Field(
        None, description="Time precision metadata"
    )

    @classmethod
    def from_astro_datetime(
        cls, astro_dt: AstroDateTime, include_precision: bool = True
    ) -> "AstroDateTimeModel":
        """Create from AstroDateTime object."""
        coordinates = None
        if astro_dt.coordinates:
            coordinates = CoordinateModel.from_coordinate_info(
                astro_dt.coordinates
            )

        precision = None
        if include_precision:
            precision_data = astro_time.calculate_birth_time_precision(
                astro_dt
            )
            precision = TimePrecisionModel(**precision_data)

        return cls(
            datetime=astro_dt.dt,
            timezone_name=astro_dt.timezone_name,
            coordinates=coordinates,
            source_format=astro_dt.source_format,
            precision=precision,
        )

    def to_astro_datetime(self) -> AstroDateTime:
        """Convert to AstroDateTime object."""
        coordinates = None
        if self.coordinates:
            coordinates = self.coordinates.to_coordinate_info()

        return AstroDateTime(
            dt=self.datetime,
            timezone_name=self.timezone_name,
            coordinates=coordinates,
            source_format=self.source_format,
        )

    @property
    def utc_datetime(self):
        """Get UTC datetime."""
        return self.datetime.astimezone(dt.timezone.utc)

    class Config:
        """Pydantic configuration."""

        json_encoders = {dt.datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "datetime": "1990-08-15T14:30:00+03:00",
                "timezone_name": "Europe/Moscow",
                "coordinates": {
                    "latitude": 55.7558,
                    "longitude": 37.6176,
                    "altitude": 150.0,
                },
                "source_format": "string_input",
                "precision": {
                    "has_seconds": True,
                    "has_coordinates": True,
                    "timezone_source": "coordinates",
                    "solar_time_available": True,
                },
            }
        }


class TimeValidationResponseModel(BaseModel):
    """Response model for time validation operations."""

    valid: bool = Field(..., description="Whether the time input is valid")
    astro_datetime: Optional[AstroDateTimeModel] = Field(
        None, description="Parsed AstroDateTime if successful"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if validation failed"
    )
    warnings: List[str] = Field(
        default_factory=list, description="List of validation warnings"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="List of suggested corrections"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "valid": True,
                    "astro_datetime": {
                        "datetime": "1990-08-15T14:30:00+03:00",
                        "timezone_name": "Europe/Moscow",
                        "coordinates": {
                            "latitude": 55.7558,
                            "longitude": 37.6176,
                        },
                    },
                    "warnings": [],
                    "suggestions": [],
                },
                {
                    "valid": False,
                    "error_message": "Invalid date format",
                    "warnings": ["Time precision may be low without seconds"],
                    "suggestions": [
                        "Use format: YYYY-MM-DD HH:MM:SS",
                        "Provide coordinates for better accuracy",
                    ],
                },
            ]
        }


class BatchTimeInputModel(BaseModel):
    """Model for batch time processing operations."""

    time_inputs: List[TimeInputModel] = Field(
        ...,
        description="List of time inputs to process",
    )
    target_timezone: Optional[str] = Field(
        None, description="Target timezone for conversion"
    )
    include_precision: bool = Field(
        True, description="Whether to include precision metadata"
    )

    @field_validator("time_inputs")
    @classmethod
    def validate_batch_size(
        cls, v: List[TimeInputModel]
    ) -> List[TimeInputModel]:
        """Validate batch size limits."""
        if len(v) < 1:
            raise ValueError("Batch must contain at least 1 item")
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 items")
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "time_inputs": [
                    {
                        "date_input": "15.08.1990",
                        "time_input": "14:30:00",
                        "timezone_input": "Europe/Moscow",
                    },
                    {
                        "date_input": "10.05.1985",
                        "time_input": "09:15:00",
                        "timezone_input": "Asia/Novosibirsk",
                    },
                ],
                "target_timezone": "UTC",
                "include_precision": True,
            }
        }


class BatchTimeResponseModel(BaseModel):
    """Response model for batch time processing."""

    results: List[TimeValidationResponseModel] = Field(
        ..., description="Processing results for each input"
    )
    summary: Dict[str, Any] = Field(..., description="Summary statistics")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "valid": True,
                        "astro_datetime": {
                            "datetime": "1990-08-15T14:30:00+03:00",
                            "timezone_name": "Europe/Moscow",
                        },
                    }
                ],
                "summary": {
                    "total_inputs": 2,
                    "successful_parses": 2,
                    "failed_parses": 0,
                    "success_rate": 100.0,
                    "processing_time_ms": 45.7,
                },
            }
        }


class TimezoneDetectionModel(BaseModel):
    """Model for timezone detection from coordinates."""

    coordinates: CoordinateModel = Field(
        ..., description="Coordinates for timezone detection"
    )

    def detect_timezone(self) -> str:
        """Detect timezone from coordinates."""
        coord_info = self.coordinates.to_coordinate_info()
        return astro_time.timezone_manager.detect_timezone_from_coordinates(
            coord_info.longitude
        )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "coordinates": {"latitude": 55.7558, "longitude": 37.6176}
            }
        }


class TimezoneDetectionResponseModel(BaseModel):
    """Response model for timezone detection."""

    detected_timezone: str = Field(
        ..., description="Detected timezone identifier"
    )
    confidence: str = Field(
        ..., description="Confidence level (high, medium, low)"
    )
    alternative_timezones: List[str] = Field(
        default_factory=list, description="Alternative timezone options"
    )
    coordinates: CoordinateModel = Field(..., description="Input coordinates")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "detected_timezone": "Europe/Moscow",
                "confidence": "high",
                "alternative_timezones": ["Europe/Volgograd"],
                "coordinates": {"latitude": 55.7558, "longitude": 37.6176},
            }
        }


# Export all models
__all__ = [
    "CoordinateModel",
    "TimeInputModel",
    "TimePrecisionModel",
    "AstroDateTimeModel",
    "TimeValidationResponseModel",
    "BatchTimeInputModel",
    "BatchTimeResponseModel",
    "TimezoneDetectionModel",
    "TimezoneDetectionResponseModel",
]
