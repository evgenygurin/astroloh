"""IoT integration API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.core.database import get_db_session as get_db
from app.models.iot_models import (
    AutomationCreate,
    DeviceCommand,
    IoTDeviceCreate,
    IoTDeviceResponse,
    IoTDeviceUpdate,
    WearableAlert,
)
from app.services.encryption import EncryptionService
from app.services.home_automation_service import HomeAutomationService
from app.services.horoscope_generator import HoroscopeGenerator
from app.services.iot_analytics_service import IoTAnalyticsService
from app.services.iot_manager import IoTDeviceManager
from app.services.lunar_calendar import LunarCalendar
from app.services.smart_home_voice_integration import SmartHomeVoiceIntegration
from app.services.smart_lighting_service import SmartLightingService
from app.services.transit_calculator import TransitCalculator
from app.services.wearable_integration import WearableIntegrationService

router = APIRouter(prefix="/api/v1/iot", tags=["IoT Integration"])


# Dependencies
async def get_iot_manager(
    db: AsyncSession = Depends(get_db),
) -> IoTDeviceManager:
    """Get IoT device manager instance."""
    encryption_service = EncryptionService()
    return IoTDeviceManager(db, encryption_service)


async def get_lighting_service(
    db: AsyncSession = Depends(get_db),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
) -> SmartLightingService:
    """Get smart lighting service instance."""
    lunar_service = LunarCalendar()
    return SmartLightingService(db, iot_manager, lunar_service)


async def get_voice_integration(
    db: AsyncSession = Depends(get_db),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
    lighting_service: SmartLightingService = Depends(get_lighting_service),
) -> SmartHomeVoiceIntegration:
    """Get voice integration service instance."""
    lunar_service = LunarCalendar()
    TransitCalculator()
    horoscope_generator = HoroscopeGenerator()

    return SmartHomeVoiceIntegration(
        db, iot_manager, lighting_service, horoscope_generator, lunar_service
    )


async def get_wearable_service(
    db: AsyncSession = Depends(get_db),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
) -> WearableIntegrationService:
    """Get wearable integration service instance."""
    lunar_service = LunarCalendar()
    transit_calculator = TransitCalculator()
    return WearableIntegrationService(
        db, iot_manager, lunar_service, transit_calculator
    )


async def get_automation_service(
    db: AsyncSession = Depends(get_db),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
    lighting_service: SmartLightingService = Depends(get_lighting_service),
) -> HomeAutomationService:
    """Get home automation service instance."""
    lunar_service = LunarCalendar()
    transit_calculator = TransitCalculator()
    horoscope_generator = HoroscopeGenerator()

    return HomeAutomationService(
        db,
        iot_manager,
        lighting_service,
        lunar_service,
        transit_calculator,
        horoscope_generator,
    )


async def get_analytics_service(
    db: AsyncSession = Depends(get_db),
) -> IoTAnalyticsService:
    """Get IoT analytics service instance."""
    lunar_service = LunarCalendar()
    return IoTAnalyticsService(db, lunar_service)


# Device Management Endpoints
@router.post("/devices", response_model=Dict[str, Any])
async def register_device(
    device_data: IoTDeviceCreate,
    user_id: int = Depends(get_current_user_id),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
):
    """Register a new IoT device."""
    try:
        device = await iot_manager.register_device(user_id, device_data)
        return {
            "success": True,
            "message": "Device registered successfully",
            "device": {
                "id": device.id,
                "device_id": device.device_id,
                "name": device.name,
                "device_type": device.device_type,
                "status": device.status,
            },
        }
    except ValidationError as e:
        logger.warning(f"Invalid device data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device data provided",
        )
    except ValueError as e:
        logger.warning(f"Invalid device configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device configuration",
        )
    except Exception as e:
        logger.error(f"Failed to register device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred",
        )


@router.get("/devices", response_model=List[IoTDeviceResponse])
async def get_user_devices(
    user_id: int = Depends(get_current_user_id),
    device_type: Optional[str] = Query(
        None, description="Filter by device type"
    ),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
):
    """Get all devices for a user."""
    try:
        from app.models.iot_models import DeviceType

        type_filter = None
        if device_type:
            try:
                type_filter = DeviceType(device_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid device type: {device_type}",
                )

        devices = await iot_manager.get_user_devices(user_id, type_filter)

        return [
            IoTDeviceResponse(
                id=device.id,
                device_id=device.device_id,
                name=device.name,
                device_type=device.device_type,
                protocol=device.protocol,
                manufacturer=device.manufacturer,
                model=device.model,
                status=device.status,
                capabilities=device.capabilities,
                configuration=device.configuration,
                location=device.location,
                room=device.room,
                last_seen=device.last_seen,
                created_at=device.created_at,
            )
            for device in devices
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user devices",
        )


@router.put("/devices/{device_id}", response_model=Dict[str, Any])
async def update_device(
    device_id: int = Path(..., description="Device ID"),
    update_data: IoTDeviceUpdate = ...,
    user_id: int = Depends(get_current_user_id),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
):
    """Update device information."""
    try:
        device = await iot_manager.update_device(
            device_id, user_id, update_data
        )
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found or access denied",
            )

        return {
            "success": True,
            "message": "Device updated successfully",
            "device": {
                "id": device.id,
                "name": device.name,
                "status": device.status,
            },
        }
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Invalid update data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid update data provided",
        )
    except Exception as e:
        logger.error(f"Failed to update device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device",
        )


@router.post("/devices/{device_id}/command", response_model=Dict[str, Any])
async def send_device_command(
    device_id: str = Path(..., description="Device ID"),
    command: DeviceCommand = ...,
    user_id: int = Depends(get_current_user_id),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
):
    """Send command to IoT device."""
    try:
        # Verify user owns the device before sending command
        result = await iot_manager.send_command(device_id, command, user_id)
        return result
    except ValueError as e:
        logger.warning(f"Invalid command for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device command",
        )
    except PermissionError as e:
        logger.warning(f"Access denied for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to device",
        )
    except Exception as e:
        logger.error(f"Failed to send device command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send device command",
        )


@router.get("/devices/{device_id}/capabilities", response_model=Dict[str, Any])
async def get_device_capabilities(
    device_id: str = Path(..., description="Device ID"),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
):
    """Get device capabilities and current state."""
    try:
        capabilities = await iot_manager.get_device_capabilities(device_id)
        return {"success": True, "capabilities": capabilities}
    except Exception as e:
        logger.error(f"Failed to get device capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover/{protocol}", response_model=Dict[str, Any])
async def discover_devices(
    protocol: str = Path(
        ..., description="Protocol to discover (matter, homekit, mqtt)"
    ),
    timeout: int = Query(30, description="Discovery timeout in seconds"),
    iot_manager: IoTDeviceManager = Depends(get_iot_manager),
):
    """Discover available devices on the network."""
    try:
        devices = await iot_manager.discover_devices(protocol, timeout)
        return {
            "success": True,
            "protocol": protocol,
            "discovered_devices": devices,
            "count": len(devices),
        }
    except Exception as e:
        logger.error(f"Failed to discover devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Smart Lighting Endpoints
@router.post("/lighting/lunar", response_model=Dict[str, Any])
async def apply_lunar_lighting(
    user_id: int = Depends(get_current_user_id),
    room: Optional[str] = Query(None, description="Room name"),
    lighting_service: SmartLightingService = Depends(get_lighting_service),
):
    """Apply lighting based on current lunar phase."""
    try:
        result = await lighting_service.apply_lunar_lighting(user_id, room)
        return result
    except ValueError as e:
        logger.warning(f"Invalid lighting configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid lighting configuration",
        )
    except Exception as e:
        logger.error(f"Failed to apply lunar lighting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply lunar lighting",
        )


@router.post("/lighting/mood", response_model=Dict[str, Any])
async def create_mood_lighting(
    mood: str = Query(..., description="Mood type"),
    user_id: int = Depends(get_current_user_id),
    zodiac_sign: Optional[str] = Query(
        None, description="Zodiac sign for personalization"
    ),
    lighting_service: SmartLightingService = Depends(get_lighting_service),
):
    """Create mood lighting based on astrological profile."""
    try:
        # Validate mood parameter
        valid_moods = [
            "relaxed",
            "energetic",
            "romantic",
            "focused",
            "meditative",
        ]
        if mood not in valid_moods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mood. Must be one of: {', '.join(valid_moods)}",
            )

        result = await lighting_service.create_mood_lighting(
            user_id, mood, zodiac_sign
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create mood lighting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create mood lighting",
        )


@router.post("/lighting/sunrise-sunset", response_model=Dict[str, Any])
async def schedule_sunrise_sunset_lighting(
    user_id: int = Query(..., description="User ID"),
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    lighting_service: SmartLightingService = Depends(get_lighting_service),
):
    """Schedule automatic lighting based on sunrise/sunset times."""
    try:
        result = await lighting_service.schedule_sunrise_sunset_lighting(
            user_id, latitude, longitude
        )
        return result
    except Exception as e:
        logger.error(f"Failed to schedule sunrise/sunset lighting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lighting/state", response_model=Dict[str, Any])
async def get_lighting_state(
    user_id: int = Query(..., description="User ID"),
    lighting_service: SmartLightingService = Depends(get_lighting_service),
):
    """Get current state of all user's smart lights."""
    try:
        result = await lighting_service.get_current_lighting_state(user_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get lighting state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Voice Integration Endpoints
@router.post("/voice/yandex", response_model=Dict[str, Any])
async def handle_yandex_command(
    command: str = Query(
        ..., description="Voice command", min_length=1, max_length=500
    ),
    user_id: int = Depends(get_current_user_id),
    parameters: Optional[Dict[str, Any]] = None,
    voice_service: SmartHomeVoiceIntegration = Depends(get_voice_integration),
):
    """Handle Yandex.Station voice commands."""
    try:
        result = await voice_service.handle_yandex_station_command(
            user_id, command, parameters or {}
        )
        return result
    except ValueError as e:
        logger.warning(f"Invalid voice command: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid voice command format",
        )
    except Exception as e:
        logger.error(f"Failed to handle Yandex command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice command",
        )


@router.post("/voice/google", response_model=Dict[str, Any])
async def handle_google_command(
    intent: str = Query(..., description="Google Assistant intent"),
    user_id: int = Query(..., description="User ID"),
    parameters: Optional[Dict[str, Any]] = None,
    voice_service: SmartHomeVoiceIntegration = Depends(get_voice_integration),
):
    """Handle Google Assistant smart home commands."""
    try:
        result = await voice_service.handle_google_assistant_command(
            user_id, intent, parameters or {}
        )
        return result
    except Exception as e:
        logger.error(f"Failed to handle Google command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/alexa", response_model=Dict[str, Any])
async def handle_alexa_command(
    intent_name: str = Query(..., description="Alexa intent name"),
    user_id: int = Query(..., description="User ID"),
    slots: Optional[Dict[str, Any]] = None,
    voice_service: SmartHomeVoiceIntegration = Depends(get_voice_integration),
):
    """Handle Amazon Alexa smart home commands."""
    try:
        result = await voice_service.handle_alexa_command(
            user_id, intent_name, slots or {}
        )
        return result
    except Exception as e:
        logger.error(f"Failed to handle Alexa command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/suggestions", response_model=List[str])
async def get_voice_suggestions(
    user_id: int = Query(..., description="User ID"),
    context: str = Query("", description="Context for suggestions"),
    voice_service: SmartHomeVoiceIntegration = Depends(get_voice_integration),
):
    """Get context-aware voice command suggestions."""
    try:
        suggestions = await voice_service.get_suggested_commands(
            user_id, context
        )
        return suggestions
    except Exception as e:
        logger.error(f"Failed to get voice suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Wearable Integration Endpoints
@router.post("/wearable/sync", response_model=Dict[str, Any])
async def sync_wearable_data(
    device_id: str = Query(..., description="Wearable device ID"),
    user_id: int = Query(..., description="User ID"),
    data: Dict[str, Any] = ...,
    wearable_service: WearableIntegrationService = Depends(
        get_wearable_service
    ),
):
    """Sync data from wearable device."""
    try:
        result = await wearable_service.sync_wearable_data(
            user_id, device_id, data
        )
        return result
    except Exception as e:
        logger.error(f"Failed to sync wearable data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wearable/notification", response_model=Dict[str, Any])
async def send_wearable_notification(
    user_id: int = Query(..., description="User ID"),
    alert: WearableAlert = ...,
    wearable_service: WearableIntegrationService = Depends(
        get_wearable_service
    ),
):
    """Send notification to user's wearable devices."""
    try:
        result = await wearable_service.send_wearable_notification(
            user_id, alert
        )
        return result
    except Exception as e:
        logger.error(f"Failed to send wearable notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wearable/sleep-recommendations", response_model=Dict[str, Any])
async def get_sleep_recommendations(
    user_id: int = Query(..., description="User ID"),
    recent_days: int = Query(
        7, description="Number of recent days to analyze"
    ),
    wearable_service: WearableIntegrationService = Depends(
        get_wearable_service
    ),
):
    """Get sleep recommendations based on lunar cycle and wearable data."""
    try:
        result = await wearable_service.get_sleep_recommendations(
            user_id, recent_days
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get sleep recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Home Automation Endpoints
@router.post("/automation", response_model=Dict[str, Any])
async def create_automation(
    user_id: int = Depends(get_current_user_id),
    automation_data: AutomationCreate = ...,
    automation_service: HomeAutomationService = Depends(
        get_automation_service
    ),
):
    """Create a new home automation rule."""
    try:
        result = await automation_service.create_automation(
            user_id, automation_data
        )
        return result
    except ValidationError as e:
        logger.warning(f"Invalid automation data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid automation configuration",
        )
    except Exception as e:
        logger.error(f"Failed to create automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create automation rule",
        )


@router.get("/automation", response_model=List[Dict[str, Any]])
async def get_user_automations(
    user_id: int = Depends(get_current_user_id),
    automation_service: HomeAutomationService = Depends(
        get_automation_service
    ),
):
    """Get all automation rules for a user."""
    try:
        automations = await automation_service.get_user_automations(user_id)
        return [
            {
                "id": automation.id,
                "name": automation.name,
                "description": automation.description,
                "trigger_type": automation.trigger_type,
                "is_enabled": automation.is_enabled,
                "execution_count": automation.execution_count,
                "last_executed": automation.last_executed,
            }
            for automation in automations
        ]
    except Exception as e:
        logger.error(f"Failed to get user automations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve automation rules",
        )


@router.post("/automation/morning-ritual", response_model=Dict[str, Any])
async def create_morning_ritual(
    user_id: int = Query(..., description="User ID"),
    wake_time: str = Query(..., description="Wake up time (HH:MM)"),
    preferences: Dict[str, Any] = ...,
    automation_service: HomeAutomationService = Depends(
        get_automation_service
    ),
):
    """Create morning ritual automation based on daily horoscope."""
    try:
        result = await automation_service.create_morning_ritual_automation(
            user_id, wake_time, preferences
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create morning ritual: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/lunar-phase", response_model=Dict[str, Any])
async def create_lunar_phase_automation(
    user_id: int = Query(..., description="User ID"),
    room: Optional[str] = Query(None, description="Room name"),
    automation_service: HomeAutomationService = Depends(
        get_automation_service
    ),
):
    """Create automation for lunar phase changes."""
    try:
        result = await automation_service.create_lunar_phase_automation(
            user_id, room
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create lunar phase automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints
@router.get("/analytics/energy", response_model=Dict[str, Any])
async def analyze_energy_consumption(
    user_id: int = Depends(get_current_user_id),
    period_days: int = Query(
        30, description="Analysis period in days", ge=1, le=365
    ),
    analytics_service: IoTAnalyticsService = Depends(get_analytics_service),
):
    """Analyze energy consumption patterns and correlations with lunar cycles."""
    try:
        result = await analytics_service.analyze_energy_consumption(
            user_id, period_days
        )
        return result
    except Exception as e:
        logger.error(f"Failed to analyze energy consumption: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze energy consumption",
        )


@router.get("/analytics/wellness", response_model=Dict[str, Any])
async def analyze_wellness_correlations(
    user_id: int = Query(..., description="User ID"),
    period_days: int = Query(30, description="Analysis period in days"),
    analytics_service: IoTAnalyticsService = Depends(get_analytics_service),
):
    """Analyze correlations between wellness data and astrological cycles."""
    try:
        result = await analytics_service.analyze_wellness_correlations(
            user_id, period_days
        )
        return result
    except Exception as e:
        logger.error(f"Failed to analyze wellness correlations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/automation", response_model=Dict[str, Any])
async def get_automation_insights(
    user_id: int = Query(..., description="User ID"),
    analytics_service: IoTAnalyticsService = Depends(get_analytics_service),
):
    """Generate insights about home automation effectiveness."""
    try:
        result = await analytics_service.generate_automation_insights(user_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get automation insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/report", response_model=Dict[str, Any])
async def get_monthly_report(
    user_id: int = Query(..., description="User ID"),
    analytics_service: IoTAnalyticsService = Depends(get_analytics_service),
):
    """Generate comprehensive monthly IoT report."""
    try:
        result = await analytics_service.generate_monthly_report(user_id)
        return result
    except Exception as e:
        logger.error(f"Failed to generate monthly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
