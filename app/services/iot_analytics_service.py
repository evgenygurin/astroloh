"""IoT analytics and monitoring service for smart home data analysis."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import statistics
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.iot_models import (
    IoTDevice,
    DeviceData,
    WearableData,
    HomeAutomation,
    DeviceType,
)
from app.services.lunar_calendar import LunarCalendarService


class IoTAnalyticsService:
    """Analytics service for IoT and smart home data analysis."""

    def __init__(self, db: AsyncSession, lunar_service: LunarCalendarService):
        self.db = db
        self.lunar_service = lunar_service

    async def analyze_energy_consumption(
        self, user_id: int, period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze energy consumption patterns and correlations with lunar cycles."""
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Get energy consumption data
            query = (
                select(DeviceData)
                .join(IoTDevice)
                .where(
                    and_(
                        IoTDevice.user_id == user_id,
                        DeviceData.data_type == "energy_consumption",
                        DeviceData.timestamp >= start_date,
                    )
                )
                .order_by(DeviceData.timestamp)
            )
            
            result = await self.db.execute(query)
            energy_data = result.scalars().all()

            if not energy_data:
                return {"success": False, "message": "No energy consumption data available"}

            # Group by device
            device_consumption = defaultdict(list)
            daily_consumption = defaultdict(float)
            
            for data_point in energy_data:
                device_consumption[data_point.device_id].append(data_point.value)
                day_key = data_point.timestamp.date()
                daily_consumption[day_key] += data_point.value or 0

            # Calculate statistics
            total_consumption = sum(daily_consumption.values())
            avg_daily_consumption = total_consumption / len(daily_consumption) if daily_consumption else 0
            
            # Analyze lunar correlations
            lunar_correlation = await self._calculate_energy_lunar_correlation(
                daily_consumption, period_days
            )
            
            # Find peak consumption times
            peak_hours = await self._analyze_peak_consumption_hours(energy_data)
            
            # Device efficiency analysis
            device_efficiency = await self._analyze_device_efficiency(device_consumption)

            return {
                "success": True,
                "period_days": period_days,
                "total_consumption": round(total_consumption, 2),
                "average_daily": round(avg_daily_consumption, 2),
                "lunar_correlation": lunar_correlation,
                "peak_hours": peak_hours,
                "device_efficiency": device_efficiency,
                "recommendations": await self._generate_energy_recommendations(
                    lunar_correlation, peak_hours, device_efficiency
                ),
            }

        except Exception as e:
            logger.error(f"Failed to analyze energy consumption: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_energy_lunar_correlation(
        self, daily_consumption: Dict[Any, float], period_days: int
    ) -> Dict[str, Any]:
        """Calculate correlation between energy consumption and lunar phases."""
        try:
            phase_consumption = defaultdict(list)
            
            for date, consumption in daily_consumption.items():
                # Get lunar phase for this date
                lunar_info = await self.lunar_service.get_lunar_calendar_info(
                    datetime.combine(date, datetime.min.time())
                )
                phase = lunar_info.get("phase", "unknown")
                phase_consumption[phase].append(consumption)
            
            # Calculate average consumption per phase
            phase_averages = {}
            for phase, consumptions in phase_consumption.items():
                if consumptions:
                    phase_averages[phase] = {
                        "average": statistics.mean(consumptions),
                        "median": statistics.median(consumptions),
                        "data_points": len(consumptions),
                    }
            
            # Find highest and lowest consumption phases
            if phase_averages:
                highest_phase = max(phase_averages.keys(), key=lambda x: phase_averages[x]["average"])
                lowest_phase = min(phase_averages.keys(), key=lambda x: phase_averages[x]["average"])
                
                return {
                    "phase_averages": phase_averages,
                    "highest_consumption_phase": highest_phase,
                    "lowest_consumption_phase": lowest_phase,
                    "variation": round(
                        phase_averages[highest_phase]["average"] - phase_averages[lowest_phase]["average"], 2
                    ),
                }
            
            return {"phase_averages": {}, "message": "Insufficient data for correlation"}

        except Exception as e:
            logger.error(f"Failed to calculate lunar correlation: {e}")
            return {"error": str(e)}

    async def _analyze_peak_consumption_hours(
        self, energy_data: List[DeviceData]
    ) -> Dict[str, Any]:
        """Analyze peak consumption hours."""
        hour_consumption = defaultdict(list)
        
        for data_point in energy_data:
            hour = data_point.timestamp.hour
            hour_consumption[hour].append(data_point.value or 0)
        
        # Calculate averages per hour
        hour_averages = {}
        for hour, values in hour_consumption.items():
            if values:
                hour_averages[hour] = statistics.mean(values)
        
        if not hour_averages:
            return {"hours": {}, "message": "No consumption data available"}
        
        # Find peak hours
        peak_hour = max(hour_averages.keys(), key=lambda x: hour_averages[x])
        low_hour = min(hour_averages.keys(), key=lambda x: hour_averages[x])
        
        return {
            "hours": hour_averages,
            "peak_hour": peak_hour,
            "peak_consumption": round(hour_averages[peak_hour], 2),
            "low_hour": low_hour,
            "low_consumption": round(hour_averages[low_hour], 2),
        }

    async def _analyze_device_efficiency(
        self, device_consumption: Dict[int, List[float]]
    ) -> Dict[str, Any]:
        """Analyze individual device efficiency."""
        efficiency_scores = {}
        
        for device_id, consumptions in device_consumption.items():
            if not consumptions:
                continue
                
            avg_consumption = statistics.mean(consumptions)
            consistency = 1 / (statistics.stdev(consumptions) + 1) if len(consumptions) > 1 else 1
            
            # Simple efficiency score (lower consumption + higher consistency = better)
            efficiency_score = consistency / (avg_consumption + 1)
            
            efficiency_scores[str(device_id)] = {
                "average_consumption": round(avg_consumption, 2),
                "consistency": round(consistency, 2),
                "efficiency_score": round(efficiency_score, 2),
                "data_points": len(consumptions),
            }
        
        return efficiency_scores

    async def _generate_energy_recommendations(
        self, lunar_correlation: Dict[str, Any], peak_hours: Dict[str, Any], 
        device_efficiency: Dict[str, Any]
    ) -> List[str]:
        """Generate energy optimization recommendations."""
        recommendations = []
        
        # Lunar-based recommendations
        if "highest_consumption_phase" in lunar_correlation:
            highest_phase = lunar_correlation["highest_consumption_phase"]
            lowest_phase = lunar_correlation["lowest_consumption_phase"]
            
            recommendations.append(
                f"Энергопотребление выше всего во время {highest_phase}. "
                f"Планируйте энергоемкие задачи на {lowest_phase}."
            )
        
        # Time-based recommendations
        if "peak_hour" in peak_hours:
            peak_hour = peak_hours["peak_hour"]
            low_hour = peak_hours["low_hour"]
            
            recommendations.append(
                f"Пиковое потребление в {peak_hour}:00. "
                f"Используйте энергоемкие приборы в {low_hour}:00 для экономии."
            )
        
        # Device-specific recommendations
        if device_efficiency:
            inefficient_devices = [
                device_id for device_id, data in device_efficiency.items()
                if data["efficiency_score"] < 0.3
            ]
            
            if inefficient_devices:
                recommendations.append(
                    f"Устройства {', '.join(inefficient_devices)} работают неэффективно. "
                    "Рассмотрите замену или обслуживание."
                )
        
        return recommendations

    async def analyze_wellness_correlations(
        self, user_id: int, period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze correlations between wellness data and astrological cycles."""
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Get wearable data
            query = select(WearableData).where(
                and_(
                    WearableData.user_id == user_id,
                    WearableData.timestamp >= start_date,
                )
            ).order_by(WearableData.timestamp)
            
            result = await self.db.execute(query)
            wellness_data = result.scalars().all()

            if not wellness_data:
                return {"success": False, "message": "No wellness data available"}

            # Analyze different metrics
            sleep_analysis = await self._analyze_sleep_patterns(wellness_data)
            mood_analysis = await self._analyze_mood_patterns(wellness_data)
            activity_analysis = await self._analyze_activity_patterns(wellness_data)
            lunar_sync_analysis = await self._analyze_lunar_synchronization(wellness_data)

            return {
                "success": True,
                "period_days": period_days,
                "data_points": len(wellness_data),
                "sleep_analysis": sleep_analysis,
                "mood_analysis": mood_analysis,
                "activity_analysis": activity_analysis,
                "lunar_synchronization": lunar_sync_analysis,
                "overall_wellness_score": await self._calculate_wellness_score(wellness_data),
            }

        except Exception as e:
            logger.error(f"Failed to analyze wellness correlations: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_sleep_patterns(self, wellness_data: List[WearableData]) -> Dict[str, Any]:
        """Analyze sleep quality patterns."""
        sleep_scores = [d.sleep_quality for d in wellness_data if d.sleep_quality is not None]
        
        if not sleep_scores:
            return {"message": "No sleep data available"}
        
        return {
            "average_quality": round(statistics.mean(sleep_scores), 2),
            "best_quality": max(sleep_scores),
            "worst_quality": min(sleep_scores),
            "consistency": round(1 / (statistics.stdev(sleep_scores) + 0.01), 2) if len(sleep_scores) > 1 else 1,
            "trend": "improving" if sleep_scores[-5:] > sleep_scores[:5] else "stable",
        }

    async def _analyze_mood_patterns(self, wellness_data: List[WearableData]) -> Dict[str, Any]:
        """Analyze mood score patterns."""
        mood_scores = [d.mood_score for d in wellness_data if d.mood_score is not None]
        
        if not mood_scores:
            return {"message": "No mood data available"}
        
        return {
            "average_mood": round(statistics.mean(mood_scores), 2),
            "highest_mood": max(mood_scores),
            "lowest_mood": min(mood_scores),
            "volatility": round(statistics.stdev(mood_scores), 2) if len(mood_scores) > 1 else 0,
            "positive_days": len([s for s in mood_scores if s > 0.6]),
            "total_days": len(mood_scores),
        }

    async def _analyze_activity_patterns(self, wellness_data: List[WearableData]) -> Dict[str, Any]:
        """Analyze activity level patterns."""
        activity_scores = [d.activity_level for d in wellness_data if d.activity_level is not None]
        
        if not activity_scores:
            return {"message": "No activity data available"}
        
        return {
            "average_activity": round(statistics.mean(activity_scores), 2),
            "peak_activity": max(activity_scores),
            "lowest_activity": min(activity_scores),
            "active_days": len([s for s in activity_scores if s > 0.6]),
            "total_days": len(activity_scores),
        }

    async def _analyze_lunar_synchronization(self, wellness_data: List[WearableData]) -> Dict[str, Any]:
        """Analyze synchronization with lunar cycles."""
        lunar_correlations = [d.lunar_correlation for d in wellness_data if d.lunar_correlation is not None]
        
        if not lunar_correlations:
            return {"message": "No lunar correlation data available"}
        
        avg_correlation = statistics.mean(lunar_correlations)
        sync_level = "high" if avg_correlation > 0.6 else "medium" if avg_correlation > 0.3 else "low"
        
        return {
            "average_correlation": round(avg_correlation, 2),
            "synchronization_level": sync_level,
            "highly_synchronized_days": len([c for c in lunar_correlations if c > 0.7]),
            "total_days": len(lunar_correlations),
        }

    async def _calculate_wellness_score(self, wellness_data: List[WearableData]) -> float:
        """Calculate overall wellness score."""
        if not wellness_data:
            return 0.0
        
        scores = []
        for data in wellness_data:
            day_score = 0
            weight_sum = 0
            
            if data.sleep_quality is not None:
                scores.append(data.sleep_quality * 0.3)
                weight_sum += 0.3
            
            if data.mood_score is not None:
                scores.append(data.mood_score * 0.25)
                weight_sum += 0.25
            
            if data.activity_level is not None:
                scores.append(data.activity_level * 0.2)
                weight_sum += 0.2
            
            if data.stress_level is not None:
                scores.append((1 - data.stress_level) * 0.15)  # Lower stress is better
                weight_sum += 0.15
            
            if data.lunar_correlation is not None:
                scores.append(abs(data.lunar_correlation) * 0.1)  # Any correlation is good
                weight_sum += 0.1
        
        return round(statistics.mean(scores), 2) if scores else 0.0

    async def generate_automation_insights(self, user_id: int) -> Dict[str, Any]:
        """Generate insights about home automation effectiveness."""
        try:
            # Get automation executions from last 30 days
            start_date = datetime.utcnow() - timedelta(days=30)
            
            query = select(HomeAutomation).where(
                and_(
                    HomeAutomation.user_id == user_id,
                    HomeAutomation.last_executed >= start_date,
                )
            )
            
            result = await self.db.execute(query)
            automations = result.scalars().all()

            if not automations:
                return {"success": False, "message": "No automation data available"}

            # Analyze automation performance
            total_executions = sum(a.execution_count for a in automations)
            successful_automations = len([a for a in automations if a.execution_count > 0])
            
            # Most and least used automations
            most_used = max(automations, key=lambda x: x.execution_count) if automations else None
            least_used = min(automations, key=lambda x: x.execution_count) if automations else None
            
            # Trigger type analysis
            trigger_stats = defaultdict(int)
            for automation in automations:
                trigger_stats[automation.trigger_type] += automation.execution_count
            
            return {
                "success": True,
                "total_automations": len(automations),
                "total_executions": total_executions,
                "active_automations": successful_automations,
                "most_used": {
                    "name": most_used.name if most_used else None,
                    "executions": most_used.execution_count if most_used else 0,
                } if most_used else None,
                "least_used": {
                    "name": least_used.name if least_used else None,
                    "executions": least_used.execution_count if least_used else 0,
                } if least_used else None,
                "trigger_statistics": dict(trigger_stats),
                "recommendations": await self._generate_automation_recommendations(
                    automations, trigger_stats
                ),
            }

        except Exception as e:
            logger.error(f"Failed to generate automation insights: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_automation_recommendations(
        self, automations: List[HomeAutomation], trigger_stats: Dict[str, int]
    ) -> List[str]:
        """Generate recommendations for automation optimization."""
        recommendations = []
        
        # Unused automations
        unused = [a for a in automations if a.execution_count == 0]
        if unused:
            recommendations.append(
                f"У вас есть {len(unused)} неиспользуемых автоматизаций. "
                "Рассмотрите их настройку или удаление."
            )
        
        # Most popular trigger types
        if trigger_stats:
            most_popular_trigger = max(trigger_stats.keys(), key=lambda x: trigger_stats[x])
            recommendations.append(
                f"Триггер '{most_popular_trigger}' используется чаще всего. "
                "Рассмотрите создание дополнительных правил этого типа."
            )
        
        # Lunar phase automations
        lunar_automations = [a for a in automations if "lunar" in a.trigger_type.lower()]
        if not lunar_automations:
            recommendations.append(
                "Рассмотрите создание автоматизаций на основе лунных фаз "
                "для оптимизации энергопотребления и комфорта."
            )
        
        return recommendations

    async def generate_monthly_report(self, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive monthly IoT report."""
        try:
            # Collect all analyses
            energy_analysis = await self.analyze_energy_consumption(user_id, 30)
            wellness_analysis = await self.analyze_wellness_correlations(user_id, 30)
            automation_insights = await self.generate_automation_insights(user_id)
            
            # Device status summary
            device_query = select(IoTDevice).where(IoTDevice.user_id == user_id)
            result = await self.db.execute(device_query)
            devices = result.scalars().all()
            
            device_summary = {
                "total_devices": len(devices),
                "online_devices": len([d for d in devices if d.status == "online"]),
                "device_types": {},
            }
            
            for device in devices:
                device_type = device.device_type
                device_summary["device_types"][device_type] = device_summary["device_types"].get(device_type, 0) + 1
            
            return {
                "success": True,
                "report_date": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "device_summary": device_summary,
                "energy_analysis": energy_analysis,
                "wellness_analysis": wellness_analysis,
                "automation_insights": automation_insights,
                "overall_score": await self._calculate_overall_smart_home_score(
                    energy_analysis, wellness_analysis, automation_insights
                ),
            }

        except Exception as e:
            logger.error(f"Failed to generate monthly report: {e}")
            return {"success": False, "error": str(e)}

    async def _calculate_overall_smart_home_score(
        self, energy: Dict[str, Any], wellness: Dict[str, Any], automation: Dict[str, Any]
    ) -> float:
        """Calculate overall smart home optimization score."""
        score = 0.0
        factors = 0
        
        # Energy efficiency score
        if energy.get("success"):
            lunar_correlation = energy.get("lunar_correlation", {})
            if "variation" in lunar_correlation:
                # Lower variation is better (more optimized)
                energy_score = max(0, 1 - (lunar_correlation["variation"] / 100))
                score += energy_score * 0.4
                factors += 0.4
        
        # Wellness score
        if wellness.get("success"):
            wellness_score = wellness.get("overall_wellness_score", 0)
            score += wellness_score * 0.4
            factors += 0.4
        
        # Automation effectiveness score
        if automation.get("success"):
            total_automations = automation.get("total_automations", 0)
            active_automations = automation.get("active_automations", 0)
            automation_score = active_automations / max(total_automations, 1)
            score += automation_score * 0.2
            factors += 0.2
        
        return round(score / factors if factors > 0 else 0, 2)