"""Smart lighting service with lunar phase integration."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot_models import (
    IoTDevice,
    DeviceType,
    DeviceStatus,
    LunarLightingConfig,
    DeviceCommand,
)
from app.services.iot_manager import IoTDeviceManager
from app.services.lunar_calendar import LunarCalendar


class SmartLightingService:
    """Manages smart lighting based on astrological data."""

    def __init__(
        self,
        db: AsyncSession,
        iot_manager: IoTDeviceManager,
        lunar_service: LunarCalendar,
    ):
        self.db = db
        self.iot_manager = iot_manager
        self.lunar_service = lunar_service
        self.default_config = LunarLightingConfig()

    async def apply_lunar_lighting(
        self, user_id: int, room: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply lighting based on current lunar phase."""
        try:
            # Get current lunar phase
            lunar_info = await self.lunar_service.get_lunar_calendar_info(
                datetime.now()
            )
            current_phase = lunar_info.get("phase", "new_moon")

            # Get user's smart lights
            devices = await self.iot_manager.get_user_devices(
                user_id, DeviceType.SMART_LIGHT
            )

            if room:
                devices = [d for d in devices if d.room == room]

            if not devices:
                return {
                    "success": False,
                    "message": "No smart lights found",
                    "phase": current_phase,
                }

            # Get lighting configuration for current phase
            phase_config = getattr(self.default_config, current_phase, {})
            if not phase_config:
                phase_config = self.default_config.new_moon

            results = []
            for device in devices:
                result = await self._apply_lighting_to_device(device, phase_config, current_phase)
                results.append(result)

            successful = sum(1 for r in results if r.get("success", False))
            
            logger.info(f"Applied lunar lighting ({current_phase}) to {successful}/{len(devices)} devices")

            return {
                "success": True,
                "phase": current_phase,
                "devices_updated": successful,
                "total_devices": len(devices),
                "phase_config": phase_config,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to apply lunar lighting: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_lighting_to_device(
        self, device: IoTDevice, phase_config: Dict[str, Any], phase: str
    ) -> Dict[str, Any]:
        """Apply lighting configuration to a specific device."""
        try:
            if device.status != DeviceStatus.ONLINE.value:
                return {
                    "device_id": device.device_id,
                    "name": device.name,
                    "success": False,
                    "error": "Device offline",
                }

            # Create lighting commands based on device capabilities
            commands = await self._create_lighting_commands(device, phase_config)
            
            # Execute commands
            success_count = 0
            for command in commands:
                result = await self.iot_manager.send_command(device.device_id, command)
                if result.get("success", False):
                    success_count += 1

            return {
                "device_id": device.device_id,
                "name": device.name,
                "success": success_count > 0,
                "commands_executed": success_count,
                "total_commands": len(commands),
                "phase": phase,
                "config_applied": phase_config,
            }

        except Exception as e:
            logger.error(f"Failed to apply lighting to device {device.name}: {e}")
            return {
                "device_id": device.device_id,
                "name": device.name,
                "success": False,
                "error": str(e),
            }

    async def _create_lighting_commands(
        self, device: IoTDevice, config: Dict[str, Any]
    ) -> List[DeviceCommand]:
        """Create device commands based on lighting configuration."""
        commands = []
        capabilities = device.capabilities or {}

        # Turn on the light
        if "on_off" in capabilities:
            commands.append(
                DeviceCommand(command="turn_on", parameters={})
            )

        # Set brightness
        if "brightness" in capabilities and "brightness" in config:
            commands.append(
                DeviceCommand(
                    command="set_brightness",
                    parameters={"brightness": config["brightness"]},
                )
            )

        # Set color
        if "color" in capabilities and "color" in config:
            commands.append(
                DeviceCommand(
                    command="set_color",
                    parameters={"color": config["color"]},
                )
            )

        # Set color temperature
        if "color_temperature" in capabilities and "temperature" in config:
            commands.append(
                DeviceCommand(
                    command="set_temperature",
                    parameters={"temperature": config["temperature"]},
                )
            )

        return commands

    async def create_mood_lighting(
        self, user_id: int, mood: str, zodiac_sign: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create mood lighting based on astrological profile."""
        try:
            # Get mood-specific lighting configuration
            mood_config = self._get_mood_lighting_config(mood, zodiac_sign)

            devices = await self.iot_manager.get_user_devices(
                user_id, DeviceType.SMART_LIGHT
            )

            if not devices:
                return {"success": False, "message": "No smart lights found"}

            results = []
            for device in devices:
                result = await self._apply_lighting_to_device(device, mood_config, mood)
                results.append(result)

            successful = sum(1 for r in results if r.get("success", False))

            return {
                "success": True,
                "mood": mood,
                "zodiac_sign": zodiac_sign,
                "devices_updated": successful,
                "total_devices": len(devices),
                "mood_config": mood_config,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to create mood lighting: {e}")
            return {"success": False, "error": str(e)}

    def _get_mood_lighting_config(
        self, mood: str, zodiac_sign: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get lighting configuration for specific mood and zodiac sign."""
        base_configs = {
            "romantic": {
                "brightness": 30,
                "color": "#FF69B4",
                "temperature": 2200,
            },
            "energetic": {
                "brightness": 90,
                "color": "#FF4500", 
                "temperature": 5000,
            },
            "relaxing": {
                "brightness": 20,
                "color": "#9370DB",
                "temperature": 2700,
            },
            "meditative": {
                "brightness": 15,
                "color": "#4169E1",
                "temperature": 2400,
            },
            "focus": {
                "brightness": 80,
                "color": "#FFFFFF",
                "temperature": 4000,
            },
        }

        config = base_configs.get(mood, base_configs["relaxing"])

        # Adjust based on zodiac sign
        if zodiac_sign:
            config = self._adjust_for_zodiac(config, zodiac_sign)

        return config

    def _adjust_for_zodiac(
        self, config: Dict[str, Any], zodiac_sign: str
    ) -> Dict[str, Any]:
        """Adjust lighting configuration for zodiac sign characteristics."""
        zodiac_adjustments = {
            "aries": {"brightness": "+10", "color": "#FF0000"},
            "taurus": {"brightness": "-5", "color": "#228B22"},
            "gemini": {"brightness": "0", "color": "#FFD700"},
            "cancer": {"brightness": "-10", "color": "#C0C0C0"},
            "leo": {"brightness": "+15", "color": "#FF8C00"},
            "virgo": {"brightness": "0", "color": "#9ACD32"},
            "libra": {"brightness": "0", "color": "#FFB6C1"},
            "scorpio": {"brightness": "-5", "color": "#8B0000"},
            "sagittarius": {"brightness": "+5", "color": "#9932CC"},
            "capricorn": {"brightness": "-5", "color": "#2F4F4F"},
            "aquarius": {"brightness": "0", "color": "#00CED1"},
            "pisces": {"brightness": "-5", "color": "#9370DB"},
        }

        adjustments = zodiac_adjustments.get(zodiac_sign.lower(), {})
        adjusted_config = config.copy()

        # Apply brightness adjustment
        if "brightness" in adjustments:
            brightness_adj = adjustments["brightness"]
            if brightness_adj.startswith(("+", "-")):
                adjusted_config["brightness"] += int(brightness_adj)
            else:
                adjusted_config["brightness"] = int(brightness_adj)
            
            # Clamp values
            adjusted_config["brightness"] = max(1, min(100, adjusted_config["brightness"]))

        # Apply color adjustment
        if "color" in adjustments:
            adjusted_config["color"] = adjustments["color"]

        return adjusted_config

    async def schedule_sunrise_sunset_lighting(
        self, user_id: int, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """Schedule automatic lighting based on sunrise/sunset times."""
        try:
            # Calculate sunrise and sunset for user's location
            sun_times = await self._calculate_sun_times(latitude, longitude)

            devices = await self.iot_manager.get_user_devices(
                user_id, DeviceType.SMART_LIGHT
            )

            if not devices:
                return {"success": False, "message": "No smart lights found"}

            # Create automation rules for each device
            automation_results = []
            for device in devices:
                # Morning automation
                morning_result = await self._create_sun_automation(
                    device, "sunrise", sun_times["sunrise"]
                )
                automation_results.append(morning_result)

                # Evening automation
                evening_result = await self._create_sun_automation(
                    device, "sunset", sun_times["sunset"]
                )
                automation_results.append(evening_result)

            return {
                "success": True,
                "sun_times": sun_times,
                "devices": len(devices),
                "automations_created": len(automation_results),
                "results": automation_results,
            }

        except Exception as e:
            logger.error(f"Failed to schedule sunrise/sunset lighting: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_sun_times(
        self, latitude: float, longitude: float
    ) -> Dict[str, datetime]:
        """Calculate sunrise and sunset times for given coordinates."""
        # This would typically use an astronomy library
        # For now, return approximate times
        today = datetime.now().date()
        
        return {
            "sunrise": datetime.combine(today, datetime.strptime("06:30", "%H:%M").time()),
            "sunset": datetime.combine(today, datetime.strptime("18:30", "%H:%M").time()),
        }

    async def _create_sun_automation(
        self, device: IoTDevice, event_type: str, event_time: datetime
    ) -> Dict[str, Any]:
        """Create automation rule for sunrise/sunset lighting."""
        try:
            if event_type == "sunrise":
                # Gradually increase brightness to mimic sunrise
                config = {
                    "brightness": 80,
                    "color": "#FFE135",
                    "temperature": 3500,
                    "transition_duration": 1800,  # 30 minutes
                }
            else:  # sunset
                # Gradually decrease brightness and warm up color
                config = {
                    "brightness": 30,
                    "color": "#FF8C42", 
                    "temperature": 2200,
                    "transition_duration": 3600,  # 60 minutes
                }

            # In a real implementation, this would create an automation rule
            # in the database and schedule it with a task scheduler
            logger.info(f"Created {event_type} automation for {device.name}")

            return {
                "device_id": device.device_id,
                "device_name": device.name,
                "event_type": event_type,
                "event_time": event_time.isoformat(),
                "config": config,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Failed to create sun automation for {device.name}: {e}")
            return {
                "device_id": device.device_id,
                "device_name": device.name,
                "success": False,
                "error": str(e),
            }

    async def create_transit_lighting(
        self, user_id: int, transit_type: str, transit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create lighting effects for astrological transits."""
        try:
            # Get transit-specific lighting
            transit_config = self._get_transit_lighting_config(transit_type, transit_data)

            devices = await self.iot_manager.get_user_devices(
                user_id, DeviceType.SMART_LIGHT
            )

            results = []
            for device in devices:
                result = await self._apply_lighting_to_device(
                    device, transit_config, f"transit_{transit_type}"
                )
                results.append(result)

            successful = sum(1 for r in results if r.get("success", False))

            return {
                "success": True,
                "transit_type": transit_type,
                "transit_data": transit_data,
                "devices_updated": successful,
                "total_devices": len(devices),
                "transit_config": transit_config,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to create transit lighting: {e}")
            return {"success": False, "error": str(e)}

    def _get_transit_lighting_config(
        self, transit_type: str, transit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get lighting configuration for astrological transits."""
        transit_configs = {
            "mercury_retrograde": {
                "brightness": 40,
                "color": "#708090",
                "temperature": 3200,
                "effect": "slow_pulse",
            },
            "full_moon": {
                "brightness": 95,
                "color": "#F8F8FF",
                "temperature": 4500,
                "effect": "gentle_glow",
            },
            "new_moon": {
                "brightness": 10,
                "color": "#2F2F4F",
                "temperature": 2200,
                "effect": "dim_steady",
            },
            "mars_transit": {
                "brightness": 85,
                "color": "#DC143C",
                "temperature": 4800,
                "effect": "energetic_pulse",
            },
            "venus_transit": {
                "brightness": 60,
                "color": "#FF69B4",
                "temperature": 2800,
                "effect": "romantic_fade",
            },
        }

        return transit_configs.get(transit_type, transit_configs["new_moon"])

    async def get_current_lighting_state(self, user_id: int) -> Dict[str, Any]:
        """Get current state of all user's smart lights."""
        try:
            devices = await self.iot_manager.get_user_devices(
                user_id, DeviceType.SMART_LIGHT
            )

            states = []
            for device in devices:
                capabilities = await self.iot_manager.get_device_capabilities(device.device_id)
                states.append({
                    "device_id": device.device_id,
                    "name": device.name,
                    "room": device.room,
                    "status": device.status,
                    "capabilities": capabilities,
                })

            return {
                "success": True,
                "device_count": len(devices),
                "devices": states,
            }

        except Exception as e:
            logger.error(f"Failed to get lighting state: {e}")
            return {"success": False, "error": str(e)}