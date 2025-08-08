"""Home automation service with astrological triggers."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot_models import (
    AutomationCreate,
    AutomationTrigger,
    AutomationUpdate,
    DeviceCommand,
    HomeAutomation,
)
from app.services.horoscope_generator import HoroscopeGenerator
from app.services.iot_manager import IoTDeviceManager
from app.services.lunar_calendar import LunarCalendar
from app.services.smart_lighting_service import SmartLightingService
from app.services.transit_calculator import TransitCalculator


class HomeAutomationService:
    """Manages automated home scenarios based on astrological events."""

    def __init__(
        self,
        db: AsyncSession,
        iot_manager: IoTDeviceManager,
        lighting_service: SmartLightingService,
        lunar_service: LunarCalendar,
        transit_calculator: TransitCalculator,
        horoscope_generator: HoroscopeGenerator,
    ):
        self.db = db
        self.iot_manager = iot_manager
        self.lighting_service = lighting_service
        self.lunar_service = lunar_service
        self.transit_calculator = transit_calculator
        self.horoscope_generator = horoscope_generator

    async def create_automation(
        self, user_id: int, automation_data: AutomationCreate
    ) -> Dict[str, Any]:
        """Create a new home automation rule."""
        try:
            automation = HomeAutomation(
                user_id=user_id,
                device_id=automation_data.device_id,
                name=automation_data.name,
                description=automation_data.description,
                trigger_type=automation_data.trigger_type.value,
                trigger_conditions=automation_data.trigger_conditions,
                actions=automation_data.actions,
                is_enabled=True,
            )

            self.db.add(automation)
            await self.db.commit()
            await self.db.refresh(automation)

            logger.info(f"Created automation rule: {automation.name}")

            return {
                "success": True,
                "message": "Automation rule created successfully",
                "automation_id": automation.id,
                "automation": {
                    "id": automation.id,
                    "name": automation.name,
                    "trigger_type": automation.trigger_type,
                    "is_enabled": automation.is_enabled,
                },
            }

        except Exception as e:
            logger.error(f"Failed to create automation rule: {e}")
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def get_user_automations(self, user_id: int) -> List[HomeAutomation]:
        """Get all automation rules for a user."""
        try:
            query = select(HomeAutomation).where(
                HomeAutomation.user_id == user_id
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get user automations: {e}")
            return []

    async def update_automation(
        self, automation_id: int, user_id: int, update_data: AutomationUpdate
    ) -> Dict[str, Any]:
        """Update an existing automation rule."""
        try:
            query = select(HomeAutomation).where(
                and_(
                    HomeAutomation.id == automation_id,
                    HomeAutomation.user_id == user_id,
                )
            )
            result = await self.db.execute(query)
            automation = result.scalar_one_or_none()

            if not automation:
                return {"success": False, "error": "Automation rule not found"}

            # Update fields
            if update_data.name:
                automation.name = update_data.name
            if update_data.description:
                automation.description = update_data.description
            if update_data.trigger_conditions:
                automation.trigger_conditions = update_data.trigger_conditions
            if update_data.actions:
                automation.actions = update_data.actions
            if update_data.is_enabled is not None:
                automation.is_enabled = update_data.is_enabled

            automation.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(automation)

            return {
                "success": True,
                "message": "Automation rule updated successfully",
                "automation": {
                    "id": automation.id,
                    "name": automation.name,
                    "is_enabled": automation.is_enabled,
                },
            }

        except Exception as e:
            logger.error(f"Failed to update automation rule: {e}")
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def execute_automation(self, automation_id: int) -> Dict[str, Any]:
        """Execute an automation rule."""
        try:
            query = select(HomeAutomation).where(
                HomeAutomation.id == automation_id
            )
            result = await self.db.execute(query)
            automation = result.scalar_one_or_none()

            if not automation:
                return {"success": False, "error": "Automation rule not found"}

            if not automation.is_enabled:
                return {
                    "success": False,
                    "error": "Automation rule is disabled",
                }

            # Execute actions
            action_results = []
            for action in automation.actions:
                result = await self._execute_action(automation.user_id, action)
                action_results.append(result)

            # Update execution tracking
            automation.last_executed = datetime.utcnow()
            automation.execution_count += 1
            await self.db.commit()

            successful_actions = sum(
                1 for r in action_results if r.get("success", False)
            )

            logger.info(
                f"Executed automation {automation.name}: {successful_actions}/{len(action_results)} actions succeeded"
            )

            return {
                "success": successful_actions > 0,
                "automation_name": automation.name,
                "actions_executed": successful_actions,
                "total_actions": len(action_results),
                "results": action_results,
            }

        except Exception as e:
            logger.error(f"Failed to execute automation: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_action(
        self, user_id: int, action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific automation action."""
        try:
            action_type = action.get("type")
            parameters = action.get("parameters", {})

            if action_type == "device_command":
                return await self._execute_device_command(action)
            elif action_type == "lighting_scene":
                return await self._execute_lighting_scene(user_id, parameters)
            elif action_type == "notification":
                return await self._execute_notification(user_id, parameters)
            elif action_type == "music":
                return await self._execute_music_action(user_id, parameters)
            elif action_type == "temperature":
                return await self._execute_temperature_action(
                    user_id, parameters
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                }

        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_device_command(
        self, action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a device command action."""
        device_id = action.get("device_id")
        command_name = action.get("command")
        parameters = action.get("parameters", {})

        command = DeviceCommand(command=command_name, parameters=parameters)
        return await self.iot_manager.send_command(device_id, command)

    async def _execute_lighting_scene(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a lighting scene action."""
        scene_type = parameters.get("scene", "lunar")
        room = parameters.get("room")

        if scene_type == "lunar":
            return await self.lighting_service.apply_lunar_lighting(
                user_id, room
            )
        elif scene_type == "mood":
            mood = parameters.get("mood", "relaxing")
            zodiac = parameters.get("zodiac_sign")
            return await self.lighting_service.create_mood_lighting(
                user_id, mood, zodiac
            )
        elif scene_type == "transit":
            transit_type = parameters.get("transit_type", "full_moon")
            return await self.lighting_service.create_transit_lighting(
                user_id, transit_type, parameters
            )
        else:
            return {
                "success": False,
                "error": f"Unknown lighting scene: {scene_type}",
            }

    async def _execute_notification(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a notification action."""
        # This would integrate with notification services
        message = parameters.get("message", "Астрологическое уведомление")
        notification_type = parameters.get("type", "info")

        logger.info(f"Sending notification to user {user_id}: {message}")

        return {
            "success": True,
            "message": "Notification sent",
            "notification": message,
            "type": notification_type,
        }

    async def _execute_music_action(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a music action."""
        action = parameters.get("action", "play")
        playlist = parameters.get("playlist", "astro_ambient")

        # This would integrate with music services
        logger.info(f"Music action for user {user_id}: {action} - {playlist}")

        return {
            "success": True,
            "message": f"Music {action} executed",
            "playlist": playlist,
        }

    async def _execute_temperature_action(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a temperature control action."""
        target_temp = parameters.get("temperature", 22)
        room = parameters.get("room", "living_room")

        # This would control smart thermostats
        logger.info(
            f"Setting temperature in {room} to {target_temp}°C for user {user_id}"
        )

        return {
            "success": True,
            "message": f"Temperature set to {target_temp}°C in {room}",
            "temperature": target_temp,
            "room": room,
        }

    async def create_morning_ritual_automation(
        self, user_id: int, wake_time: str, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create morning ritual automation based on daily horoscope."""
        try:
            # Parse wake time
            wake_hour, wake_minute = map(int, wake_time.split(":"))

            # Create actions for morning ritual
            actions = []

            # Gradual lighting
            if preferences.get("gradual_lighting", True):
                actions.append(
                    {
                        "type": "lighting_scene",
                        "parameters": {
                            "scene": "sunrise",
                            "duration": 1800,  # 30 minutes
                        },
                    }
                )

            # Horoscope reading
            if preferences.get("horoscope_audio", True):
                actions.append(
                    {
                        "type": "notification",
                        "parameters": {
                            "message": "Доброе утро! Ваш гороскоп на сегодня готов.",
                            "type": "horoscope",
                        },
                    }
                )

            # Ambient music
            if preferences.get("morning_music", True):
                actions.append(
                    {
                        "type": "music",
                        "parameters": {
                            "action": "play",
                            "playlist": "morning_astro",
                            "volume": 30,
                        },
                    }
                )

            # Temperature adjustment
            if preferences.get("temperature_control", True):
                actions.append(
                    {
                        "type": "temperature",
                        "parameters": {
                            "temperature": preferences.get("morning_temp", 23),
                            "room": "bedroom",
                        },
                    }
                )

            # Create the automation rule
            automation_data = AutomationCreate(
                device_id=0,  # General automation, not tied to specific device
                name="Утренний астрологический ритуал",
                description="Ежедневный утренний ритуал с гороскопом и подготовкой атмосферы",
                trigger_type=AutomationTrigger.TIME_BASED,
                trigger_conditions={
                    "time": wake_time,
                    "days": [
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                        "sunday",
                    ],
                    "check_horoscope": True,
                },
                actions=actions,
            )

            return await self.create_automation(user_id, automation_data)

        except Exception as e:
            logger.error(f"Failed to create morning ritual automation: {e}")
            return {"success": False, "error": str(e)}

    async def create_lunar_phase_automation(
        self, user_id: int, room: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create automation for lunar phase changes."""
        try:
            actions = [
                {
                    "type": "lighting_scene",
                    "parameters": {
                        "scene": "lunar",
                        "room": room,
                        "transition_duration": 300,
                    },
                },
                {
                    "type": "notification",
                    "parameters": {
                        "message": "Лунная фаза изменилась. Атмосфера дома обновлена.",
                        "type": "lunar_phase",
                    },
                },
            ]

            automation_data = AutomationCreate(
                device_id=0,
                name="Автоматическая адаптация к лунным фазам",
                description="Автоматическое изменение освещения при смене лунных фаз",
                trigger_type=AutomationTrigger.LUNAR_PHASE,
                trigger_conditions={
                    "phases": [
                        "new_moon",
                        "first_quarter",
                        "full_moon",
                        "last_quarter",
                    ],
                    "room": room,
                },
                actions=actions,
            )

            return await self.create_automation(user_id, automation_data)

        except Exception as e:
            logger.error(f"Failed to create lunar phase automation: {e}")
            return {"success": False, "error": str(e)}

    async def create_meditation_reminder_automation(
        self,
        user_id: int,
        preferred_times: List[str],
        birth_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create meditation reminders based on favorable astrological times."""
        try:
            actions = [
                {
                    "type": "lighting_scene",
                    "parameters": {
                        "scene": "mood",
                        "mood": "meditative",
                        "zodiac_sign": birth_data.get("sun_sign"),
                    },
                },
                {
                    "type": "notification",
                    "parameters": {
                        "message": "Благоприятное время для медитации и духовных практик",
                        "type": "meditation_reminder",
                    },
                },
                {
                    "type": "music",
                    "parameters": {
                        "action": "play",
                        "playlist": "meditation_ambient",
                        "volume": 20,
                    },
                },
            ]

            automation_data = AutomationCreate(
                device_id=0,
                name="Напоминания о медитации",
                description="Напоминания о медитации в астрологически благоприятное время",
                trigger_type=AutomationTrigger.ASTROLOGICAL_EVENT,
                trigger_conditions={
                    "preferred_times": preferred_times,
                    "check_transits": True,
                    "favorable_aspects": True,
                    "birth_data": birth_data,
                },
                actions=actions,
            )

            return await self.create_automation(user_id, automation_data)

        except Exception as e:
            logger.error(
                f"Failed to create meditation reminder automation: {e}"
            )
            return {"success": False, "error": str(e)}

    async def create_romantic_mode_automation(
        self, user_id: int, partner_sign: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create romantic atmosphere automation for compatible signs."""
        try:
            # Get user's astrological profile for compatibility
            compatibility_lighting = "romantic"
            if partner_sign:
                # Adjust lighting based on compatibility
                compatibility_lighting = self._get_compatibility_lighting(
                    partner_sign
                )

            actions = [
                {
                    "type": "lighting_scene",
                    "parameters": {
                        "scene": "mood",
                        "mood": compatibility_lighting,
                        "room": "living_room",
                    },
                },
                {
                    "type": "music",
                    "parameters": {
                        "action": "play",
                        "playlist": "romantic_astro",
                        "volume": 25,
                    },
                },
                {
                    "type": "temperature",
                    "parameters": {
                        "temperature": 24,
                        "room": "living_room",
                    },
                },
            ]

            automation_data = AutomationCreate(
                device_id=0,
                name="Романтический режим",
                description="Создание романтической атмосферы для совместимых знаков",
                trigger_type=AutomationTrigger.ASTROLOGICAL_EVENT,
                trigger_conditions={
                    "venus_aspects": ["trine", "sextile", "conjunction"],
                    "partner_sign": partner_sign,
                    "favorable_timing": True,
                },
                actions=actions,
            )

            return await self.create_automation(user_id, automation_data)

        except Exception as e:
            logger.error(f"Failed to create romantic mode automation: {e}")
            return {"success": False, "error": str(e)}

    def _get_compatibility_lighting(self, partner_sign: str) -> str:
        """Get lighting mood based on partner's zodiac sign."""
        sign_moods = {
            "aries": "energetic",
            "taurus": "romantic",
            "gemini": "playful",
            "cancer": "cozy",
            "leo": "dramatic",
            "virgo": "elegant",
            "libra": "romantic",
            "scorpio": "intimate",
            "sagittarius": "adventurous",
            "capricorn": "sophisticated",
            "aquarius": "unique",
            "pisces": "dreamy",
        }
        return sign_moods.get(partner_sign.lower(), "romantic")

    async def create_energy_cleansing_automation(
        self, user_id: int, cleansing_schedule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create automatic energy cleansing rituals."""
        try:
            frequency = cleansing_schedule.get("frequency", "weekly")
            preferred_day = cleansing_schedule.get("day", "sunday")

            actions = [
                {
                    "type": "lighting_scene",
                    "parameters": {
                        "scene": "mood",
                        "mood": "cleansing",
                        "color": "#FFFFFF",
                        "brightness": 100,
                    },
                },
                {
                    "type": "music",
                    "parameters": {
                        "action": "play",
                        "playlist": "cleansing_frequencies",
                        "volume": 35,
                    },
                },
                {
                    "type": "notification",
                    "parameters": {
                        "message": "Время для очищения энергии пространства",
                        "type": "energy_cleansing",
                    },
                },
            ]

            # Add air purifier if available
            if cleansing_schedule.get("air_purifier", True):
                actions.append(
                    {
                        "type": "device_command",
                        "device_id": "air_purifier_001",
                        "command": "turn_on",
                        "parameters": {"mode": "high", "duration": 3600},
                    }
                )

            trigger_conditions = {
                "frequency": frequency,
                "day": preferred_day,
                "lunar_phase": cleansing_schedule.get(
                    "lunar_phase", "waning_moon"
                ),
            }

            automation_data = AutomationCreate(
                device_id=0,
                name="Автоматическое очищение энергии",
                description="Регулярные ритуалы очищения пространства",
                trigger_type=AutomationTrigger.TIME_BASED,
                trigger_conditions=trigger_conditions,
                actions=actions,
            )

            return await self.create_automation(user_id, automation_data)

        except Exception as e:
            logger.error(f"Failed to create energy cleansing automation: {e}")
            return {"success": False, "error": str(e)}

    async def check_and_execute_automations(self) -> Dict[str, Any]:
        """Check all automation rules and execute those that should trigger."""
        try:
            # Get all enabled automations
            query = select(HomeAutomation).where(HomeAutomation.is_enabled)
            result = await self.db.execute(query)
            automations = result.scalars().all()

            executed_count = 0
            results = []

            for automation in automations:
                should_execute = await self._should_execute_automation(
                    automation
                )

                if should_execute:
                    execution_result = await self.execute_automation(
                        automation.id
                    )
                    results.append(
                        {
                            "automation_id": automation.id,
                            "automation_name": automation.name,
                            "result": execution_result,
                        }
                    )

                    if execution_result.get("success"):
                        executed_count += 1

            return {
                "success": True,
                "checked_automations": len(automations),
                "executed_automations": executed_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to check and execute automations: {e}")
            return {"success": False, "error": str(e)}

    async def _should_execute_automation(
        self, automation: HomeAutomation
    ) -> bool:
        """Check if an automation should be executed based on its trigger conditions."""
        try:
            trigger_type = automation.trigger_type
            conditions = automation.trigger_conditions

            if trigger_type == AutomationTrigger.TIME_BASED.value:
                return await self._check_time_trigger(conditions)
            elif trigger_type == AutomationTrigger.LUNAR_PHASE.value:
                return await self._check_lunar_phase_trigger(conditions)
            elif trigger_type == AutomationTrigger.PLANETARY_TRANSIT.value:
                return await self._check_transit_trigger(conditions)
            elif trigger_type == AutomationTrigger.ASTROLOGICAL_EVENT.value:
                return await self._check_astrological_event_trigger(conditions)

            return False

        except Exception as e:
            logger.error(f"Failed to check automation trigger: {e}")
            return False

    async def _check_time_trigger(self, conditions: Dict[str, Any]) -> bool:
        """Check if time-based trigger should fire."""
        trigger_time = conditions.get("time")
        if not trigger_time:
            return False

        now = datetime.now()
        trigger_hour, trigger_minute = map(int, trigger_time.split(":"))

        # Check if current time matches trigger time (within 1 minute)
        return (
            now.hour == trigger_hour and abs(now.minute - trigger_minute) <= 1
        )

    async def _check_lunar_phase_trigger(
        self, conditions: Dict[str, Any]
    ) -> bool:
        """Check if lunar phase trigger should fire."""
        phases = conditions.get("phases", [])
        if not phases:
            return False

        lunar_info = await self.lunar_service.get_lunar_calendar_info(
            datetime.now()
        )
        current_phase = lunar_info.get("phase")

        return current_phase in phases

    async def _check_transit_trigger(self, conditions: Dict[str, Any]) -> bool:
        """Check if planetary transit trigger should fire."""
        # This would check for specific transits
        # Simplified for this implementation
        return False

    async def _check_astrological_event_trigger(
        self, conditions: Dict[str, Any]
    ) -> bool:
        """Check if astrological event trigger should fire."""
        # This would check for various astrological events
        # Simplified for this implementation
        return False
