"""Wearable devices integration service."""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot_models import DeviceCommand, DeviceType, WearableAlert, WearableData
from app.services.iot_manager import IoTDeviceManager
from app.services.lunar_calendar import LunarCalendar
from app.services.transit_calculator import TransitCalculator


class WearableIntegrationService:
    """Manages wearable devices and astrological correlations."""

    def __init__(
        self,
        db: AsyncSession,
        iot_manager: IoTDeviceManager,
        lunar_service: LunarCalendar,
        transit_calculator: TransitCalculator,
    ):
        self.db = db
        self.iot_manager = iot_manager
        self.lunar_service = lunar_service
        self.transit_calculator = transit_calculator

    async def sync_wearable_data(
        self, user_id: int, device_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync data from wearable device."""
        try:
            # Get device
            devices = await self.iot_manager.get_user_devices(
                user_id, DeviceType.WEARABLE
            )
            device = next(
                (d for d in devices if d.device_id == device_id), None
            )

            if not device:
                return {"success": False, "error": "Wearable device not found"}

            # Calculate lunar correlation
            lunar_correlation = await self._calculate_lunar_correlation(data)

            # Store wearable data
            wearable_data = WearableData(
                user_id=user_id,
                device_id=device.id,
                heart_rate=data.get("heart_rate"),
                sleep_quality=data.get("sleep_quality"),
                activity_level=data.get("activity_level"),
                stress_level=data.get("stress_level"),
                mood_score=data.get("mood_score"),
                lunar_correlation=lunar_correlation,
                timestamp=datetime.utcnow(),
            )

            self.db.add(wearable_data)
            await self.db.commit()

            # Generate insights based on data
            insights = await self._generate_wearable_insights(
                user_id, data, lunar_correlation
            )

            logger.info(f"Synced wearable data for user {user_id}")

            return {
                "success": True,
                "message": "Wearable data synced successfully",
                "lunar_correlation": lunar_correlation,
                "insights": insights,
            }

        except Exception as e:
            logger.error(f"Failed to sync wearable data: {e}")
            await self.db.rollback()
            return {"success": False, "error": str(e)}

    async def _calculate_lunar_correlation(
        self, data: Dict[str, Any]
    ) -> float:
        """Calculate correlation between biometric data and lunar cycle."""
        try:
            # Get current lunar phase info
            lunar_info = await self.lunar_service.get_lunar_calendar_info(
                datetime.now()
            )
            lunar_phase_value = lunar_info.get(
                "phase_percentage", 0.5
            )  # 0-1 value

            # Extract biometric values
            sleep_quality = data.get("sleep_quality", 0.5)
            mood_score = data.get("mood_score", 0.5)
            stress_level = data.get("stress_level", 0.5)
            activity_level = data.get("activity_level", 0.5)

            # Calculate correlations (simplified algorithm)
            # Full moon often correlates with higher energy, less sleep
            # New moon often correlates with introspection, better sleep

            correlations = []

            # Sleep correlation (inverse with lunar brightness)
            sleep_correlation = abs(sleep_quality - (1 - lunar_phase_value))
            correlations.append(sleep_correlation)

            # Mood correlation (positive with lunar energy)
            mood_correlation = 1 - abs(mood_score - lunar_phase_value)
            correlations.append(mood_correlation)

            # Stress correlation (often higher during full moon)
            stress_correlation = 1 - abs(stress_level - lunar_phase_value)
            correlations.append(stress_correlation)

            # Activity correlation (higher during waxing phases)
            activity_correlation = 1 - abs(activity_level - lunar_phase_value)
            correlations.append(activity_correlation)

            # Average correlation
            avg_correlation = sum(correlations) / len(correlations)

            return min(1.0, max(-1.0, avg_correlation))

        except Exception as e:
            logger.error(f"Failed to calculate lunar correlation: {e}")
            return 0.0

    async def _generate_wearable_insights(
        self, user_id: int, data: Dict[str, Any], lunar_correlation: float
    ) -> List[Dict[str, Any]]:
        """Generate insights based on wearable data and astrological factors."""
        insights = []

        try:
            # Get lunar phase info
            lunar_info = await self.lunar_service.get_lunar_calendar_info(
                datetime.now()
            )
            current_phase = lunar_info.get("phase", "unknown")

            # Sleep insights
            sleep_quality = data.get("sleep_quality", 0)
            if sleep_quality < 0.4:
                if current_phase in ["full_moon", "waxing_gibbous"]:
                    insights.append(
                        {
                            "type": "sleep",
                            "severity": "info",
                            "title": "Влияние полнолуния на сон",
                            "message": "Полнолуние может влиять на качество сна. Попробуйте медитацию перед сном.",
                            "recommendations": [
                                "meditation",
                                "dim_lighting",
                                "early_bedtime",
                            ],
                        }
                    )

            # Stress insights
            stress_level = data.get("stress_level", 0)
            if stress_level > 0.7:
                insights.append(
                    {
                        "type": "stress",
                        "severity": "warning",
                        "title": "Повышенный уровень стресса",
                        "message": "Обнаружен высокий уровень стресса. Рекомендуем дыхательные практики.",
                        "recommendations": [
                            "breathing_exercise",
                            "calming_music",
                            "aromatherapy",
                        ],
                    }
                )

            # Activity insights
            activity_level = data.get("activity_level", 0)
            if activity_level < 0.3 and current_phase in [
                "new_moon",
                "waning_crescent",
            ]:
                insights.append(
                    {
                        "type": "activity",
                        "severity": "info",
                        "title": "Низкая активность в новолуние",
                        "message": "Новолуние - время для отдыха и восстановления. Это нормально!",
                        "recommendations": [
                            "gentle_yoga",
                            "journaling",
                            "planning",
                        ],
                    }
                )

            # Lunar correlation insights
            if lunar_correlation > 0.7:
                insights.append(
                    {
                        "type": "lunar_sync",
                        "severity": "positive",
                        "title": "Высокая синхронизация с лунным циклом",
                        "message": f"Ваши биоритмы хорошо синхронизированы с лунным циклом ({lunar_correlation:.1%})",
                        "recommendations": [
                            "continue_tracking",
                            "moon_rituals",
                            "cycle_planning",
                        ],
                    }
                )

            return insights

        except Exception as e:
            logger.error(f"Failed to generate wearable insights: {e}")
            return []

    async def send_wearable_notification(
        self, user_id: int, alert: WearableAlert
    ) -> Dict[str, Any]:
        """Send notification to user's wearable devices."""
        try:
            # Get user's wearable devices
            devices = await self.iot_manager.get_user_devices(
                user_id, DeviceType.WEARABLE
            )

            if not devices:
                return {
                    "success": False,
                    "message": "No wearable devices found",
                }

            results = []
            for device in devices:
                # Create notification command
                command = DeviceCommand(
                    command="send_notification",
                    parameters={
                        "title": alert.title,
                        "message": alert.message,
                        "type": alert.alert_type,
                        "vibration": alert.vibration_pattern,
                        "priority": alert.priority,
                        "expires_at": alert.expires_at.isoformat()
                        if alert.expires_at
                        else None,
                    },
                    priority=alert.priority,
                )

                result = await self.iot_manager.send_command(
                    device.device_id, command
                )
                results.append(
                    {
                        "device": device.name,
                        "success": result.get("success", False),
                        "response": result.get("response", ""),
                    }
                )

            successful = sum(1 for r in results if r["success"])

            return {
                "success": successful > 0,
                "message": f"Notification sent to {successful}/{len(devices)} devices",
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to send wearable notification: {e}")
            return {"success": False, "error": str(e)}

    async def schedule_transit_reminders(
        self, user_id: int, birth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule wearable reminders for important transits."""
        try:
            # Calculate upcoming transits
            upcoming_transits = (
                await self.transit_calculator.get_upcoming_transits(
                    birth_data, days_ahead=7
                )
            )

            if not upcoming_transits:
                return {
                    "success": True,
                    "message": "No upcoming transits",
                    "reminders": [],
                }

            # Filter significant transits
            significant_transits = [
                t
                for t in upcoming_transits
                if t.get("significance", 0)
                >= 7  # Only high-significance transits
            ]

            reminders_scheduled = []
            for transit in significant_transits:
                alert = WearableAlert(
                    title="Астрологическое событие",
                    message=f"{transit['name']}: {transit['description']}",
                    alert_type="transit",
                    priority=transit.get("significance", 5),
                    expires_at=transit["date"] + timedelta(hours=6),
                )

                # Schedule reminder 2 hours before
                reminder_time = transit["date"] - timedelta(hours=2)

                # In a real implementation, this would be scheduled with a task queue
                reminders_scheduled.append(
                    {
                        "transit": transit["name"],
                        "reminder_time": reminder_time.isoformat(),
                        "alert": alert.dict(),
                    }
                )

            logger.info(
                f"Scheduled {len(reminders_scheduled)} transit reminders for user {user_id}"
            )

            return {
                "success": True,
                "message": f"Scheduled {len(reminders_scheduled)} transit reminders",
                "reminders": reminders_scheduled,
            }

        except Exception as e:
            logger.error(f"Failed to schedule transit reminders: {e}")
            return {"success": False, "error": str(e)}

    async def get_sleep_recommendations(
        self, user_id: int, recent_days: int = 7
    ) -> Dict[str, Any]:
        """Get sleep recommendations based on lunar cycle and wearable data."""
        try:
            # Get recent wearable data
            query = (
                select(WearableData)
                .where(
                    and_(
                        WearableData.user_id == user_id,
                        WearableData.timestamp
                        >= datetime.utcnow() - timedelta(days=recent_days),
                    )
                )
                .order_by(WearableData.timestamp.desc())
            )

            result = await self.db.execute(query)
            recent_data = result.scalars().all()

            if not recent_data:
                return {
                    "success": False,
                    "message": "No recent wearable data available",
                }

            # Analyze sleep patterns
            sleep_scores = [
                d.sleep_quality for d in recent_data if d.sleep_quality
            ]
            avg_sleep_quality = (
                sum(sleep_scores) / len(sleep_scores) if sleep_scores else 0
            )

            # Get current and upcoming lunar phases
            lunar_info = await self.lunar_service.get_lunar_calendar_info(
                datetime.now()
            )
            current_phase = lunar_info.get("phase", "")

            recommendations = []

            # Phase-specific sleep recommendations
            phase_recommendations = {
                "new_moon": {
                    "optimal_bedtime": "21:30",
                    "wake_time": "06:00",
                    "tips": [
                        "Perfect time for deep rest",
                        "Set intentions before sleep",
                        "Dark room recommended",
                    ],
                },
                "waxing_crescent": {
                    "optimal_bedtime": "22:00",
                    "wake_time": "06:30",
                    "tips": [
                        "Growing energy",
                        "Light stretching before bed",
                        "Visualization exercises",
                    ],
                },
                "first_quarter": {
                    "optimal_bedtime": "22:30",
                    "wake_time": "06:30",
                    "tips": [
                        "Challenging phase for sleep",
                        "Meditation crucial",
                        "Avoid caffeine after 16:00",
                    ],
                },
                "waxing_gibbous": {
                    "optimal_bedtime": "22:00",
                    "wake_time": "06:00",
                    "tips": [
                        "Refinement phase",
                        "Review day before sleep",
                        "Cool room temperature",
                    ],
                },
                "full_moon": {
                    "optimal_bedtime": "23:00",
                    "wake_time": "05:30",
                    "tips": [
                        "Expect lighter sleep",
                        "Extra meditation needed",
                        "Eye mask recommended",
                    ],
                },
                "waning_gibbous": {
                    "optimal_bedtime": "21:30",
                    "wake_time": "06:00",
                    "tips": [
                        "Gratitude practice",
                        "Releasing meditation",
                        "Warm bath before bed",
                    ],
                },
                "last_quarter": {
                    "optimal_bedtime": "22:00",
                    "wake_time": "06:30",
                    "tips": [
                        "Letting go phase",
                        "Journal worries",
                        "Deep breathing exercises",
                    ],
                },
                "waning_crescent": {
                    "optimal_bedtime": "21:00",
                    "wake_time": "06:30",
                    "tips": [
                        "Maximum rest phase",
                        "Longest sleep duration",
                        "Complete darkness",
                    ],
                },
            }

            phase_rec = phase_recommendations.get(
                current_phase, phase_recommendations["new_moon"]
            )

            # Personalized recommendations based on data
            if avg_sleep_quality < 0.6:
                recommendations.append(
                    {
                        "type": "improvement",
                        "title": "Улучшение качества сна",
                        "message": "Ваше качество сна ниже оптимального",
                        "actions": [
                            "consistent_schedule",
                            "sleep_hygiene",
                            "limit_screens",
                        ],
                    }
                )

            # Lunar correlation recommendations
            lunar_correlations = [
                d.lunar_correlation for d in recent_data if d.lunar_correlation
            ]
            if lunar_correlations:
                avg_correlation = sum(lunar_correlations) / len(
                    lunar_correlations
                )
                if avg_correlation > 0.5:
                    recommendations.append(
                        {
                            "type": "lunar_sync",
                            "title": "Синхронизация с луной",
                            "message": "Ваш сон хорошо коррелирует с лунными фазами",
                            "actions": [
                                "track_phases",
                                "plan_activities",
                                "honor_cycles",
                            ],
                        }
                    )

            return {
                "success": True,
                "average_sleep_quality": avg_sleep_quality,
                "current_phase": current_phase,
                "phase_recommendations": phase_rec,
                "personalized_recommendations": recommendations,
                "data_points": len(recent_data),
            }

        except Exception as e:
            logger.error(f"Failed to get sleep recommendations: {e}")
            return {"success": False, "error": str(e)}

    async def create_wellness_plan(
        self, user_id: int, goals: List[str], duration_days: int = 30
    ) -> Dict[str, Any]:
        """Create a personalized wellness plan based on astrological cycles."""
        try:
            # Get user's recent data for baseline
            query = (
                select(WearableData)
                .where(
                    and_(
                        WearableData.user_id == user_id,
                        WearableData.timestamp
                        >= datetime.utcnow() - timedelta(days=7),
                    )
                )
                .order_by(WearableData.timestamp.desc())
            )

            result = await self.db.execute(query)
            baseline_data = result.scalars().all()

            # Calculate lunar cycles in the plan period
            lunar_cycles = await self._calculate_lunar_cycles(duration_days)

            # Create phase-based plan
            plan_phases = []
            for cycle in lunar_cycles:
                phase_plan = await self._create_phase_plan(
                    cycle, goals, baseline_data
                )
                plan_phases.append(phase_plan)

            wellness_plan = {
                "user_id": user_id,
                "goals": goals,
                "duration_days": duration_days,
                "created_at": datetime.utcnow().isoformat(),
                "lunar_cycles": len(lunar_cycles),
                "phases": plan_phases,
                "tracking_metrics": [
                    "sleep_quality",
                    "mood_score",
                    "stress_level",
                    "activity_level",
                    "lunar_correlation",
                ],
            }

            logger.info(
                f"Created {duration_days}-day wellness plan for user {user_id}"
            )

            return {
                "success": True,
                "message": f"Created {duration_days}-day wellness plan",
                "plan": wellness_plan,
            }

        except Exception as e:
            logger.error(f"Failed to create wellness plan: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_lunar_cycles(
        self, duration_days: int
    ) -> List[Dict[str, Any]]:
        """Calculate lunar cycles within the plan duration."""
        cycles = []
        start_date = datetime.now()

        # Simplified cycle calculation (29.5 days per cycle)
        cycle_length = 29.5
        num_cycles = int(duration_days / cycle_length) + 1

        for i in range(num_cycles):
            cycle_start = start_date + timedelta(days=i * cycle_length)
            cycle_end = cycle_start + timedelta(days=cycle_length)

            if cycle_start < start_date + timedelta(days=duration_days):
                cycles.append(
                    {
                        "cycle_number": i + 1,
                        "start_date": cycle_start.isoformat(),
                        "end_date": cycle_end.isoformat(),
                        "focus": self._get_cycle_focus(i % 4),  # 4 main phases
                    }
                )

        return cycles

    def _get_cycle_focus(self, phase_index: int) -> str:
        """Get focus theme for each lunar cycle phase."""
        focuses = [
            "Новые начинания и планирование",
            "Рост и развитие",
            "Активность и достижения",
            "Отдых и восстановление",
        ]
        return focuses[phase_index]

    async def _create_phase_plan(
        self,
        cycle: Dict[str, Any],
        goals: List[str],
        baseline_data: List[WearableData],
    ) -> Dict[str, Any]:
        """Create plan for specific lunar cycle phase."""
        phase_activities = {
            "Новые начинания и планирование": [
                "Set new wellness intentions",
                "Plan workout schedule",
                "Establish meditation routine",
                "Track baseline metrics",
            ],
            "Рост и развитие": [
                "Increase activity gradually",
                "Try new exercises",
                "Expand meditation practice",
                "Monitor progress",
            ],
            "Активность и достижения": [
                "Peak performance workouts",
                "Challenge yourself",
                "Maintain consistency",
                "Celebrate achievements",
            ],
            "Отдых и восстановление": [
                "Focus on recovery",
                "Gentle movement only",
                "Extra sleep time",
                "Reflect and adjust plan",
            ],
        }

        activities = phase_activities.get(cycle["focus"], [])

        return {
            "cycle": cycle,
            "recommended_activities": activities,
            "sleep_schedule": self._get_sleep_schedule_for_phase(
                cycle["focus"]
            ),
            "activity_targets": self._get_activity_targets(
                cycle["focus"], baseline_data
            ),
            "wellness_reminders": self._get_wellness_reminders(cycle["focus"]),
        }

    def _get_sleep_schedule_for_phase(self, focus: str) -> Dict[str, str]:
        """Get recommended sleep schedule for phase."""
        schedules = {
            "Новые начинания и планирование": {
                "bedtime": "22:00",
                "wake": "06:00",
            },
            "Рост и развитие": {"bedtime": "22:30", "wake": "06:30"},
            "Активность и достижения": {"bedtime": "23:00", "wake": "06:00"},
            "Отдых и восстановление": {"bedtime": "21:30", "wake": "07:00"},
        }
        return schedules.get(focus, {"bedtime": "22:00", "wake": "06:30"})

    def _get_activity_targets(
        self, focus: str, baseline: List[WearableData]
    ) -> Dict[str, float]:
        """Get activity targets based on phase and baseline data."""
        if not baseline:
            return {"activity_level": 0.6, "stress_level": 0.4}

        avg_activity = sum(
            d.activity_level for d in baseline if d.activity_level
        ) / len(baseline)

        multipliers = {
            "Новые начинания и планирование": 0.8,
            "Рост и развитие": 1.1,
            "Активность и достижения": 1.3,
            "Отдых и восстановление": 0.6,
        }

        multiplier = multipliers.get(focus, 1.0)

        return {
            "activity_level": min(1.0, avg_activity * multiplier),
            "stress_level": 0.4,  # Target low stress
        }

    def _get_wellness_reminders(self, focus: str) -> List[str]:
        """Get wellness reminders for phase."""
        reminders = {
            "Новые начинания и планирование": [
                "Set clear intentions",
                "Start slowly",
                "Track everything",
            ],
            "Рост и развитие": [
                "Be consistent",
                "Push comfort zone gradually",
                "Monitor energy levels",
            ],
            "Активность и достижения": [
                "Maintain peak performance",
                "Don't overexert",
                "Stay hydrated",
            ],
            "Отдых и восстановление": [
                "Prioritize rest",
                "Listen to your body",
                "Reflect on progress",
            ],
        }
        return reminders.get(focus, [])
