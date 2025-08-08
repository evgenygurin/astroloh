"""IoT integration models for Astroloh."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, relationship

from app.models.database import GUID
from app.models.database import Base as SQLBaseModel


class DeviceType(str, Enum):
    """Types of IoT devices."""

    SMART_LIGHT = "smart_light"
    SMART_SPEAKER = "smart_speaker"
    SMART_DISPLAY = "smart_display"
    WEARABLE = "wearable"
    SENSOR = "sensor"
    THERMOSTAT = "thermostat"
    SECURITY_CAMERA = "security_camera"
    SMART_PLUG = "smart_plug"
    SMART_LOCK = "smart_lock"


class DeviceProtocol(str, Enum):
    """IoT protocols supported."""

    MATTER = "matter"
    HOMEKIT = "homekit"
    GOOGLE_ASSISTANT = "google_assistant"
    ALEXA = "alexa"
    MQTT = "mqtt"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"


class AutomationTrigger(str, Enum):
    """Automation trigger types."""

    LUNAR_PHASE = "lunar_phase"
    PLANETARY_TRANSIT = "planetary_transit"
    DAILY_HOROSCOPE = "daily_horoscope"
    TIME_BASED = "time_based"
    SENSOR_DATA = "sensor_data"
    USER_PRESENCE = "user_presence"
    ASTROLOGICAL_EVENT = "astrological_event"


class DeviceStatus(str, Enum):
    """Device status enum."""

    ONLINE = "online"
    OFFLINE = "offline"
    PAIRING = "pairing"
    ERROR = "error"


# SQLAlchemy Models
class IoTDevice(SQLBaseModel):
    """IoT device database model."""

    __tablename__ = "iot_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    device_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)
    protocol = Column(String(50), nullable=False)
    manufacturer = Column(String(255))
    model = Column(String(255))
    firmware_version = Column(String(100))
    status = Column(String(50), default=DeviceStatus.OFFLINE)
    capabilities = Column(JSON)
    configuration = Column(JSON)
    location = Column(String(255))
    room = Column(String(255))
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    automations: Mapped[list["HomeAutomation"]] = relationship("HomeAutomation", back_populates="device")
    device_data: Mapped[list["DeviceData"]] = relationship("DeviceData", back_populates="device")


class HomeAutomation(SQLBaseModel):
    """Home automation rules database model."""

    __tablename__ = "home_automations"

    id = Column(Integer, primary_key=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("iot_devices.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(50), nullable=False)
    trigger_conditions = Column(JSON)
    actions = Column(JSON)
    is_enabled = Column(Boolean, default=True)
    last_executed = Column(DateTime)
    execution_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    device: Mapped["IoTDevice"] = relationship("IoTDevice", back_populates="automations")


class DeviceData(SQLBaseModel):
    """Device sensor data and telemetry."""

    __tablename__ = "device_data"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("iot_devices.id"), nullable=False)
    data_type = Column(String(100), nullable=False)
    value = Column(Float)
    unit = Column(String(50))
    device_metadata = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    device: Mapped["IoTDevice"] = relationship("IoTDevice", back_populates="device_data")


class WearableData(SQLBaseModel):
    """Wearable device specific data."""

    __tablename__ = "wearable_data"

    id = Column(Integer, primary_key=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("iot_devices.id"), nullable=False)
    heart_rate = Column(Integer)
    sleep_quality = Column(Float)
    activity_level = Column(Float)
    stress_level = Column(Float)
    mood_score = Column(Float)
    lunar_correlation = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Pydantic Models for API
class IoTDeviceCreate(BaseModel):
    """Create IoT device request."""

    device_id: str
    name: str
    device_type: DeviceType
    protocol: DeviceProtocol
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    room: Optional[str] = None


class IoTDeviceUpdate(BaseModel):
    """Update IoT device request."""

    name: Optional[str] = None
    status: Optional[DeviceStatus] = None
    configuration: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    room: Optional[str] = None


class IoTDeviceResponse(BaseModel):
    """IoT device response."""

    id: int
    device_id: str
    name: str
    device_type: str
    protocol: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    status: str
    capabilities: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    room: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime


class AutomationCreate(BaseModel):
    """Create automation rule request."""

    device_id: int
    name: str
    description: Optional[str] = None
    trigger_type: AutomationTrigger
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]


class AutomationUpdate(BaseModel):
    """Update automation rule request."""

    name: Optional[str] = None
    description: Optional[str] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    is_enabled: Optional[bool] = None


class AutomationResponse(BaseModel):
    """Automation rule response."""

    id: int
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_enabled: bool
    last_executed: Optional[datetime] = None
    execution_count: int
    created_at: datetime


class DeviceCommand(BaseModel):
    """Device command request."""

    command: str
    parameters: Optional[Dict[str, Any]] = None
    priority: int = Field(default=5, ge=1, le=10)


class LunarLightingConfig(BaseModel):
    """Configuration for lunar phase lighting."""

    new_moon: Dict[str, Any] = Field(
        default={"brightness": 10, "color": "#0F0F23", "temperature": 2700}
    )
    waxing_crescent: Dict[str, Any] = Field(
        default={"brightness": 25, "color": "#1A1A3A", "temperature": 3000}
    )
    first_quarter: Dict[str, Any] = Field(
        default={"brightness": 50, "color": "#2D2D5A", "temperature": 3500}
    )
    waxing_gibbous: Dict[str, Any] = Field(
        default={"brightness": 75, "color": "#4A4A7A", "temperature": 4000}
    )
    full_moon: Dict[str, Any] = Field(
        default={"brightness": 100, "color": "#6A6A9A", "temperature": 4500}
    )
    waning_gibbous: Dict[str, Any] = Field(
        default={"brightness": 75, "color": "#4A4A7A", "temperature": 4000}
    )
    last_quarter: Dict[str, Any] = Field(
        default={"brightness": 50, "color": "#2D2D5A", "temperature": 3500}
    )
    waning_crescent: Dict[str, Any] = Field(
        default={"brightness": 25, "color": "#1A1A3A", "temperature": 3000}
    )


class WearableAlert(BaseModel):
    """Wearable device alert/notification."""

    title: str
    message: str
    alert_type: str = "info"  # info, warning, reminder, transit
    vibration_pattern: Optional[List[int]] = None
    priority: int = Field(default=5, ge=1, le=10)
    expires_at: Optional[datetime] = None
