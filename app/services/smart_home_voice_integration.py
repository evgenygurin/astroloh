"""Smart home voice integration for multiple assistants."""

from datetime import datetime
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot_models import DeviceType
from app.services.horoscope_generator import HoroscopeGenerator
from app.services.iot_manager import IoTDeviceManager
from app.services.lunar_calendar import LunarCalendar
from app.services.smart_lighting_service import SmartLightingService


class SmartHomeVoiceIntegration:
    """Integrates astrology features with voice assistants for smart home control."""

    def __init__(
        self,
        db: AsyncSession,
        iot_manager: IoTDeviceManager,
        lighting_service: SmartLightingService,
        horoscope_generator: HoroscopeGenerator,
        lunar_service: LunarCalendar,
    ):
        self.db = db
        self.iot_manager = iot_manager
        self.lighting_service = lighting_service
        self.horoscope_generator = horoscope_generator
        self.lunar_service = lunar_service

    async def handle_yandex_station_command(
        self, user_id: int, command: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Yandex.Station voice commands."""
        try:
            command_lower = command.lower()

            # Lighting commands
            if "свет" in command_lower and (
                "луна" in command_lower or "лунн" in command_lower
            ):
                return await self._handle_lunar_lighting_command(
                    user_id, parameters
                )

            # Horoscope commands
            elif "гороскоп" in command_lower:
                return await self._handle_horoscope_command(
                    user_id, parameters
                )

            # Mood lighting
            elif "настроение" in command_lower and "свет" in command_lower:
                return await self._handle_mood_lighting_command(
                    user_id, parameters
                )

            # Device status
            elif "статус" in command_lower and "дом" in command_lower:
                return await self._handle_home_status_command(user_id)

            # Meditation/practice reminders
            elif "медитация" in command_lower or "практика" in command_lower:
                return await self._handle_meditation_command(
                    user_id, parameters
                )

            else:
                return {
                    "success": False,
                    "message": "Команда не распознана",
                    "suggestions": [
                        "Включи лунное освещение",
                        "Расскажи гороскоп на сегодня",
                        "Создай романтичное настроение",
                        "Покажи статус умного дома",
                        "Напомни о медитации",
                    ],
                }

        except Exception as e:
            logger.error(f"Failed to handle Yandex.Station command: {e}")
            return {"success": False, "error": str(e)}

    async def handle_google_assistant_command(
        self, user_id: int, intent: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Google Assistant smart home commands."""
        try:
            intent_handlers = {
                "astro.lighting.lunar": self._handle_lunar_lighting_command,
                "astro.horoscope.daily": self._handle_horoscope_command,
                "astro.mood.lighting": self._handle_mood_lighting_command,
                "astro.home.status": lambda uid, _: self._handle_home_status_command(
                    uid
                ),
                "astro.meditation.reminder": self._handle_meditation_command,
                "astro.transit.alert": self._handle_transit_alert_command,
            }

            handler = intent_handlers.get(intent)
            if not handler:
                return {
                    "success": False,
                    "message": "Intent not supported",
                    "supported_intents": list(intent_handlers.keys()),
                }

            return await handler(user_id, parameters)

        except Exception as e:
            logger.error(f"Failed to handle Google Assistant command: {e}")
            return {"success": False, "error": str(e)}

    async def handle_alexa_command(
        self, user_id: int, intent_name: str, slots: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Amazon Alexa smart home commands."""
        try:
            intent_handlers = {
                "ApplyLunarLightingIntent": self._handle_lunar_lighting_command,
                "GetHoroscopeIntent": self._handle_horoscope_command,
                "SetMoodLightingIntent": self._handle_mood_lighting_command,
                "HomeStatusIntent": lambda uid, _: self._handle_home_status_command(
                    uid
                ),
                "MeditationReminderIntent": self._handle_meditation_command,
                "TransitAlertIntent": self._handle_transit_alert_command,
            }

            handler = intent_handlers.get(intent_name)
            if not handler:
                return {
                    "success": False,
                    "message": "Intent not supported",
                    "supported_intents": list(intent_handlers.keys()),
                }

            return await handler(user_id, slots)

        except Exception as e:
            logger.error(f"Failed to handle Alexa command: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_lunar_lighting_command(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle lunar lighting commands."""
        room = parameters.get("room")
        result = await self.lighting_service.apply_lunar_lighting(
            user_id, room
        )

        if result.get("success"):
            phase = result.get("phase", "unknown")
            devices_updated = result.get("devices_updated", 0)

            # Translate phase to Russian
            phase_translations = {
                "full_moon": "полная луна",
                "new_moon": "новая луна",
                "waxing_crescent": "растущая луна",
                "waning_crescent": "убывающая луна",
                "first_quarter": "первая четверть луны",
                "last_quarter": "последняя четверть луны",
            }
            russian_phase = phase_translations.get(
                phase, f"лунное освещение ({phase})"
            )

            response_message = f"Настроил освещение под {russian_phase}. "
            response_message += f"Обновлено устройств: {devices_updated}"

            if room:
                response_message += f" в комнате {room}"
        else:
            response_message = f"Не удалось настроить лунное освещение: {result.get('message', 'неизвестная ошибка')}"

        return {
            "success": result.get("success", False),
            "message": response_message,
            "data": result,
        }

    async def _handle_horoscope_command(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle horoscope requests."""
        try:
            parameters.get("date", "today")
            parameters.get("type", "daily")

            # Generate horoscope based on user's profile
            horoscope_result = (
                await self.horoscope_generator.generate_daily_horoscope(
                    user_id, datetime.now()
                )
            )

            if horoscope_result.get("success"):
                horoscope = horoscope_result.get("horoscope", {})
                message = f"Ваш гороскоп на сегодня: {horoscope.get('general', 'Информация недоступна')}"

                # Add smart home recommendations
                if horoscope.get("energy_level"):
                    energy = horoscope["energy_level"]
                    if energy > 7:
                        message += " Рекомендую включить энергичное освещение."
                    elif energy < 4:
                        message += (
                            " Предлагаю создать расслабляющую атмосферу."
                        )

            else:
                message = "Не удалось получить гороскоп. Попробуйте позже."

            return {
                "success": horoscope_result.get("success", False),
                "message": message,
                "data": horoscope_result,
            }

        except Exception as e:
            logger.error(f"Failed to handle horoscope command: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_mood_lighting_command(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle mood lighting commands."""
        mood = parameters.get("mood", "relaxing")
        zodiac_sign = parameters.get("zodiac_sign")

        result = await self.lighting_service.create_mood_lighting(
            user_id, mood, zodiac_sign
        )

        if result.get("success"):
            devices_updated = result.get("devices_updated", 0)
            message = f"Создал освещение для настроения '{mood}'. "
            message += f"Обновлено устройств: {devices_updated}"
        else:
            message = f"Не удалось создать освещение настроения: {result.get('error', 'неизвестная ошибка')}"

        return {
            "success": result.get("success", False),
            "message": message,
            "data": result,
        }

    async def _handle_home_status_command(
        self, user_id: int
    ) -> Dict[str, Any]:
        """Handle home status requests."""
        try:
            # Get all user devices
            devices = await self.iot_manager.get_user_devices(user_id)

            online_count = sum(1 for d in devices if d.status == "online")
            offline_count = len(devices) - online_count

            # Get lighting status
            lighting_status = (
                await self.lighting_service.get_current_lighting_state(user_id)
            )
            light_count = lighting_status.get("device_count", 0)

            # Get current lunar phase
            lunar_info = await self.lunar_service.get_lunar_calendar_info(
                datetime.now()
            )
            current_phase = lunar_info.get("phase", "неизвестна")

            message = f"Статус умного дома: {online_count} устройств онлайн, "
            message += (
                f"{offline_count} офлайн. Освещение: {light_count} ламп. "
            )
            message += f"Текущая лунная фаза: {current_phase}."

            return {
                "success": True,
                "message": message,
                "data": {
                    "total_devices": len(devices),
                    "online_devices": online_count,
                    "offline_devices": offline_count,
                    "lighting_devices": light_count,
                    "lunar_phase": current_phase,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get home status: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_meditation_command(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle meditation/practice reminders."""
        try:
            practice_type = parameters.get("type", "медитация")
            duration = parameters.get("duration", 20)  # minutes

            # Get optimal time based on lunar phase and transits
            lunar_info = await self.lunar_service.get_lunar_calendar_info(
                datetime.now()
            )
            current_phase = lunar_info.get("phase", "")

            # Recommend timing based on lunar phase
            timing_recommendations = {
                "new_moon": "Отличное время для намерений и планирования",
                "waxing_crescent": "Подходит для роста и развития",
                "first_quarter": "Время действий и преодоления препятствий",
                "waxing_gibbous": "Период доработки и совершенствования",
                "full_moon": "Пик энергии, идеально для завершения дел",
                "waning_gibbous": "Время благодарности и отдачи",
                "last_quarter": "Освобождение от ненужного",
                "waning_crescent": "Отдых и восстановление",
            }

            recommendation = timing_recommendations.get(
                current_phase, "Подходящее время для практики"
            )

            # Set up meditation lighting
            lighting_result = await self.lighting_service.create_mood_lighting(
                user_id, "meditative"
            )

            message = (
                f"Настроил атмосферу для {practice_type} на {duration} минут. "
            )
            message += f"{recommendation}. "

            if lighting_result.get("success"):
                message += "Освещение настроено для медитации."

            return {
                "success": True,
                "message": message,
                "data": {
                    "practice_type": practice_type,
                    "duration": duration,
                    "lunar_phase": current_phase,
                    "recommendation": recommendation,
                    "lighting_applied": lighting_result.get("success", False),
                },
            }

        except Exception as e:
            logger.error(f"Failed to handle meditation command: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_transit_alert_command(
        self, user_id: int, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle astrological transit alerts."""
        try:
            # This would integrate with transit calculator
            transit_type = parameters.get("transit", "mercury_retrograde")

            # Create appropriate lighting for transit
            lighting_result = (
                await self.lighting_service.create_transit_lighting(
                    user_id, transit_type, parameters
                )
            )

            transit_messages = {
                "mercury_retrograde": "Меркурий в ретроградном движении. Будьте осторожны с коммуникациями.",
                "full_moon": "Полнолуние сегодня. Время завершения проектов.",
                "new_moon": "Новолуние. Отличное время для новых начинаний.",
                "mars_transit": "Транзит Марса активизирует вашу энергию.",
                "venus_transit": "Транзит Венеры благоприятен для отношений.",
            }

            message = transit_messages.get(
                transit_type, f"Астрологическое событие: {transit_type}"
            )

            if lighting_result.get("success"):
                message += " Освещение настроено под это событие."

            return {
                "success": True,
                "message": message,
                "data": {
                    "transit_type": transit_type,
                    "lighting_applied": lighting_result.get("success", False),
                    "parameters": parameters,
                },
            }

        except Exception as e:
            logger.error(f"Failed to handle transit alert: {e}")
            return {"success": False, "error": str(e)}

    async def create_voice_routine(
        self,
        user_id: int,
        routine_name: str,
        triggers: List[str],
        actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create a voice-activated routine."""
        try:
            routine = {
                "name": routine_name,
                "user_id": user_id,
                "triggers": triggers,
                "actions": actions,
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True,
            }

            # Store routine configuration
            # In a real implementation, this would be saved to database
            logger.info(
                f"Created voice routine '{routine_name}' for user {user_id}"
            )

            return {
                "success": True,
                "message": f"Создана голосовая команда '{routine_name}'",
                "routine": routine,
            }

        except Exception as e:
            logger.error(f"Failed to create voice routine: {e}")
            return {"success": False, "error": str(e)}

    async def get_suggested_commands(
        self, user_id: int, context: str = ""
    ) -> List[str]:
        """Get context-aware voice command suggestions."""
        try:
            # Get user's devices to customize suggestions
            devices = await self.iot_manager.get_user_devices(user_id)
            has_lights = any(
                d.device_type == DeviceType.SMART_LIGHT.value for d in devices
            )

            # Get current lunar phase for contextual suggestions
            lunar_info = await self.lunar_service.get_lunar_calendar_info(
                datetime.now()
            )
            current_phase = lunar_info.get("phase", "")

            base_commands = [
                "Расскажи гороскоп на сегодня",
                "Покажи статус умного дома",
                "Напомни о медитации",
            ]

            if has_lights:
                base_commands.extend(
                    [
                        "Включи лунное освещение",
                        "Создай романтичное настроение",
                        "Настрой освещение для медитации",
                    ]
                )

            # Add phase-specific suggestions
            phase_commands = {
                "full_moon": [
                    "Создай атмосферу полнолуния",
                    "Включи яркое освещение",
                ],
                "new_moon": [
                    "Создай тихую атмосферу",
                    "Включи тусклое освещение",
                ],
                "mercury_retrograde": [
                    "Напомни о осторожности",
                    "Включи спокойное освещение",
                ],
            }

            if current_phase in phase_commands:
                base_commands.extend(phase_commands[current_phase])

            return base_commands

        except Exception as e:
            logger.error(f"Failed to get suggested commands: {e}")
            return []
