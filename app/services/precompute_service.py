"""
Pre-computation service for popular astrological data.
Generates and caches frequently requested calculations in the background.
"""

import asyncio
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from app.services.async_kerykeion_service import async_kerykeion
from app.services.astro_cache_service import astro_cache
from app.services.performance_monitor import performance_monitor


class PrecomputeService:
    """Service for pre-computing and caching popular astrological data."""
    
    def __init__(self):
        self.is_running = False
        self._precompute_task: Optional[asyncio.Task] = None
        self.precompute_schedule = {
            "daily_ephemeris": {"interval_hours": 6, "last_run": None},
            "popular_charts": {"interval_hours": 24, "last_run": None},
            "lunar_phases": {"interval_hours": 12, "last_run": None},
            "zodiac_compatibility": {"interval_hours": 48, "last_run": None},
            "transit_forecasts": {"interval_hours": 8, "last_run": None},
        }
        
        # Popular zodiac signs based on common requests
        self.popular_signs = ["Leo", "Scorpio", "Aries", "Gemini", "Cancer", "Virgo", "Libra", "Sagittarius"]
        
        # Popular locations for chart calculations
        self.popular_locations = [
            {"name": "Moscow", "lat": 55.7558, "lng": 37.6176, "tz": "Europe/Moscow"},
            {"name": "Saint_Petersburg", "lat": 59.9311, "lng": 30.3609, "tz": "Europe/Moscow"},
            {"name": "Novosibirsk", "lat": 55.0084, "lng": 82.9357, "tz": "Asia/Novosibirsk"},
            {"name": "Yekaterinburg", "lat": 56.8431, "lng": 60.6454, "tz": "Asia/Yekaterinburg"},
            {"name": "Sochi", "lat": 43.6028, "lng": 39.7342, "tz": "Europe/Moscow"},
        ]
        
        logger.info("PRECOMPUTE_SERVICE_INIT: Pre-computation service initialized")

    async def start_background_precomputation(self):
        """Start background pre-computation tasks."""
        if self.is_running:
            logger.warning("PRECOMPUTE_SERVICE_ALREADY_RUNNING")
            return
        
        self.is_running = True
        self._precompute_task = asyncio.create_task(self._precompute_loop())
        logger.info("PRECOMPUTE_SERVICE_START: Background pre-computation started")

    async def stop_background_precomputation(self):
        """Stop background pre-computation tasks."""
        self.is_running = False
        if self._precompute_task:
            self._precompute_task.cancel()
            try:
                await self._precompute_task
            except asyncio.CancelledError:
                pass
        logger.info("PRECOMPUTE_SERVICE_STOP: Background pre-computation stopped")

    async def _precompute_loop(self):
        """Main background loop for pre-computation tasks."""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check each scheduled task
                for task_name, schedule in self.precompute_schedule.items():
                    if self._should_run_task(task_name, schedule, current_time):
                        op_id = performance_monitor.start_operation("PrecomputeService", task_name)
                        
                        try:
                            await self._run_precompute_task(task_name)
                            schedule["last_run"] = current_time
                            performance_monitor.end_operation(op_id, success=True)
                            logger.info(f"PRECOMPUTE_SERVICE_TASK_SUCCESS: {task_name}")
                        except Exception as e:
                            performance_monitor.end_operation(op_id, success=False, error_message=str(e))
                            logger.error(f"PRECOMPUTE_SERVICE_TASK_ERROR: {task_name} - {e}")
                
                # Sleep for 30 minutes before next check
                await asyncio.sleep(1800)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"PRECOMPUTE_SERVICE_LOOP_ERROR: {e}")
                await asyncio.sleep(3600)  # Sleep for 1 hour on error

    def _should_run_task(self, task_name: str, schedule: Dict[str, Any], current_time: datetime) -> bool:
        """Check if a task should be run based on its schedule."""
        if schedule["last_run"] is None:
            return True
        
        time_since_last_run = current_time - schedule["last_run"]
        interval = timedelta(hours=schedule["interval_hours"])
        
        return time_since_last_run >= interval

    async def _run_precompute_task(self, task_name: str):
        """Run a specific pre-computation task."""
        if task_name == "daily_ephemeris":
            await self._precompute_daily_ephemeris()
        elif task_name == "popular_charts":
            await self._precompute_popular_charts()
        elif task_name == "lunar_phases":
            await self._precompute_lunar_phases()
        elif task_name == "zodiac_compatibility":
            await self._precompute_zodiac_compatibility()
        elif task_name == "transit_forecasts":
            await self._precompute_transit_forecasts()
        else:
            logger.warning(f"PRECOMPUTE_SERVICE_UNKNOWN_TASK: {task_name}")

    async def _precompute_daily_ephemeris(self):
        """Pre-compute ephemeris data for the next 7 days."""
        logger.info("PRECOMPUTE_EPHEMERIS_START")
        
        today = date.today()
        precomputed_count = 0
        
        for i in range(7):  # Next 7 days
            target_date = today + timedelta(days=i)
            
            # Check if already cached
            cached_ephemeris = await astro_cache.get_daily_ephemeris(target_date)
            if cached_ephemeris:
                continue
            
            # Generate ephemeris data (placeholder - would use actual calculation)
            ephemeris_data = {
                "date": target_date.isoformat(),
                "planets": {
                    "sun": {"longitude": 0.0, "speed": 0.98},  # Placeholder data
                    "moon": {"longitude": 0.0, "speed": 13.2},
                    "mercury": {"longitude": 0.0, "speed": 1.4},
                    "venus": {"longitude": 0.0, "speed": 1.2},
                    "mars": {"longitude": 0.0, "speed": 0.5},
                    "jupiter": {"longitude": 0.0, "speed": 0.08},
                    "saturn": {"longitude": 0.0, "speed": 0.03},
                    "uranus": {"longitude": 0.0, "speed": 0.01},
                    "neptune": {"longitude": 0.0, "speed": 0.006},
                    "pluto": {"longitude": 0.0, "speed": 0.004},
                },
                "computed_at": datetime.now().isoformat(),
                "source": "precomputed"
            }
            
            await astro_cache.set_daily_ephemeris(target_date, ephemeris_data)
            precomputed_count += 1
        
        logger.info(f"PRECOMPUTE_EPHEMERIS_SUCCESS: {precomputed_count} days precomputed")

    async def _precompute_popular_charts(self):
        """Pre-compute natal charts for popular birth dates and locations."""
        logger.info("PRECOMPUTE_CHARTS_START")
        
        precomputed_count = 0
        
        # Generate popular birth date combinations
        popular_dates = []
        current_year = datetime.now().year
        
        # Create representative birth dates for each zodiac sign
        zodiac_dates = [
            datetime(1990, 3, 25, 12, 0),  # Aries
            datetime(1985, 5, 15, 12, 0),  # Taurus
            datetime(1992, 6, 10, 12, 0),  # Gemini
            datetime(1988, 7, 8, 12, 0),   # Cancer
            datetime(1991, 8, 15, 12, 0),  # Leo
            datetime(1987, 9, 20, 12, 0),  # Virgo
            datetime(1993, 10, 12, 12, 0), # Libra
            datetime(1989, 11, 8, 12, 0),  # Scorpio
            datetime(1994, 12, 5, 12, 0),  # Sagittarius
            datetime(1986, 1, 15, 12, 0),  # Capricorn
            datetime(1995, 2, 10, 12, 0),  # Aquarius
            datetime(1990, 3, 5, 12, 0),   # Pisces
        ]
        
        # Combine with popular locations
        chart_requests = []
        for birth_date in zodiac_dates:
            for location in self.popular_locations[:3]:  # Top 3 locations
                chart_requests.append({
                    "name": f"Popular_{birth_date.month:02d}{birth_date.day:02d}_{location['name']}",
                    "birth_datetime": birth_date,
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "timezone": location["tz"]
                })
        
        # Pre-compute charts in batches to avoid overwhelming the system
        batch_size = 5
        for i in range(0, len(chart_requests), batch_size):
            batch = chart_requests[i:i + batch_size]
            
            # Check if charts are already cached
            uncached_requests = []
            for request in batch:
                cached_chart = await astro_cache.get_natal_chart(
                    birth_datetime=request["birth_datetime"],
                    latitude=request["latitude"],
                    longitude=request["longitude"],
                    timezone=request["timezone"]
                )
                if not cached_chart:
                    uncached_requests.append(request)
            
            if uncached_requests:
                results = await async_kerykeion.batch_calculate_charts(uncached_requests, use_cache=True)
                precomputed_count += len([r for r in results if not r.get("error")])
                
                # Small delay between batches to avoid overloading
                await asyncio.sleep(2)
        
        logger.info(f"PRECOMPUTE_CHARTS_SUCCESS: {precomputed_count} charts precomputed")

    async def _precompute_lunar_phases(self):
        """Pre-compute lunar phases for the next 30 days."""
        logger.info("PRECOMPUTE_LUNAR_START")
        
        today = date.today()
        lunar_data = []
        
        # Generate lunar phase data for next 30 days
        for i in range(30):
            target_date = today + timedelta(days=i)
            
            # Simplified lunar phase calculation (placeholder)
            # In reality, this would use proper astronomical calculations
            days_since_new_moon = (target_date - date(2024, 1, 1)).days % 29.53
            
            if days_since_new_moon < 1:
                phase = "New Moon"
                illumination = 0.0
            elif days_since_new_moon < 7:
                phase = "Waxing Crescent"
                illumination = days_since_new_moon / 14.0
            elif days_since_new_moon < 8:
                phase = "First Quarter"
                illumination = 0.5
            elif days_since_new_moon < 15:
                phase = "Waxing Gibbous"
                illumination = 0.5 + (days_since_new_moon - 7) / 14.0
            elif days_since_new_moon < 16:
                phase = "Full Moon"
                illumination = 1.0
            elif days_since_new_moon < 22:
                phase = "Waning Gibbous"
                illumination = 1.0 - (days_since_new_moon - 15) / 14.0
            elif days_since_new_moon < 23:
                phase = "Last Quarter"
                illumination = 0.5
            else:
                phase = "Waning Crescent"
                illumination = 0.5 - (days_since_new_moon - 22) / 14.0
            
            lunar_data.append({
                "date": target_date.isoformat(),
                "phase": phase,
                "illumination": round(illumination, 3),
                "days_since_new_moon": round(days_since_new_moon, 1)
            })
        
        # Cache the lunar phases data
        await astro_cache.set("lunar_phases_30days", lunar_data, 86400 * 7)  # Cache for 7 days
        
        logger.info(f"PRECOMPUTE_LUNAR_SUCCESS: 30 days of lunar phases precomputed")

    async def _precompute_zodiac_compatibility(self):
        """Pre-compute compatibility for popular zodiac sign combinations."""
        logger.info("PRECOMPUTE_COMPATIBILITY_START")
        
        precomputed_count = 0
        
        # Generate all popular sign combinations
        popular_combinations = []
        for i, sign1 in enumerate(self.popular_signs):
            for sign2 in self.popular_signs[i:]:  # Avoid duplicate combinations
                popular_combinations.append((sign1, sign2))
        
        # Create representative birth data for each sign
        sign_birth_data = {}
        for i, sign in enumerate(self.popular_signs):
            # Create a representative birth date for each sign
            month = (i % 12) + 1
            day = 15
            sign_birth_data[sign] = {
                "birth_datetime": datetime(1990, month, day, 12, 0),
                "latitude": 55.7558,  # Moscow coordinates
                "longitude": 37.6176,
                "timezone": "Europe/Moscow"
            }
        
        # Pre-compute compatibility for popular combinations
        for sign1, sign2 in popular_combinations[:20]:  # Limit to top 20 combinations
            # Check if already cached
            person1_id = f"{sign1}_representative"
            person2_id = f"{sign2}_representative"
            
            cached_compatibility = await astro_cache.get_compatibility_analysis(
                person1_birth=person1_id,
                person2_birth=person2_id,
                analysis_type="romantic"
            )
            
            if cached_compatibility:
                continue
            
            # Generate natal charts if not cached
            chart1_data = await async_kerykeion.get_full_natal_chart_data(
                name=f"Representative_{sign1}",
                **sign_birth_data[sign1],
                use_cache=True
            )
            
            chart2_data = await async_kerykeion.get_full_natal_chart_data(
                name=f"Representative_{sign2}",
                **sign_birth_data[sign2],
                use_cache=True
            )
            
            if not chart1_data.get("error") and not chart2_data.get("error"):
                # Calculate compatibility
                compatibility = await async_kerykeion.calculate_compatibility_detailed(
                    person1_data=chart1_data,
                    person2_data=chart2_data,
                    analysis_type="romantic",
                    use_cache=True
                )
                
                if not compatibility.get("error"):
                    precomputed_count += 1
            
            # Small delay to avoid overloading
            await asyncio.sleep(1)
        
        logger.info(f"PRECOMPUTE_COMPATIBILITY_SUCCESS: {precomputed_count} combinations precomputed")

    async def _precompute_transit_forecasts(self):
        """Pre-compute transit forecasts for popular chart configurations."""
        logger.info("PRECOMPUTE_TRANSITS_START")
        
        # This would pre-compute transit forecasts for popular chart configurations
        # For now, we'll create placeholder data
        
        today = date.today()
        forecast_data = {
            "date_range": f"{today.isoformat()} to {(today + timedelta(days=7)).isoformat()}",
            "popular_transits": [
                {
                    "transit_planet": "Jupiter",
                    "natal_planet": "Sun", 
                    "aspect": "Trine",
                    "influence": "Expansion and growth opportunities"
                },
                {
                    "transit_planet": "Saturn",
                    "natal_planet": "Moon",
                    "aspect": "Square", 
                    "influence": "Emotional discipline and structure"
                }
            ],
            "precomputed_at": datetime.now().isoformat(),
            "source": "precomputed"
        }
        
        await astro_cache.set("popular_transits_forecast", forecast_data, 28800)  # 8 hours
        
        logger.info("PRECOMPUTE_TRANSITS_SUCCESS: Transit forecasts precomputed")

    async def manual_precompute_all(self) -> Dict[str, Any]:
        """Manually trigger pre-computation of all popular data."""
        logger.info("PRECOMPUTE_MANUAL_ALL_START")
        
        start_time = datetime.now()
        results = {}
        
        tasks = [
            ("daily_ephemeris", self._precompute_daily_ephemeris),
            ("popular_charts", self._precompute_popular_charts), 
            ("lunar_phases", self._precompute_lunar_phases),
            ("zodiac_compatibility", self._precompute_zodiac_compatibility),
            ("transit_forecasts", self._precompute_transit_forecasts),
        ]
        
        for task_name, task_func in tasks:
            op_id = performance_monitor.start_operation("PrecomputeService", f"manual_{task_name}")
            
            try:
                await task_func()
                results[task_name] = "success"
                performance_monitor.end_operation(op_id, success=True)
            except Exception as e:
                results[task_name] = f"error: {str(e)}"
                performance_monitor.end_operation(op_id, success=False, error_message=str(e))
                logger.error(f"PRECOMPUTE_MANUAL_ERROR: {task_name} - {e}")
        
        elapsed_time = datetime.now() - start_time
        
        logger.info(f"PRECOMPUTE_MANUAL_ALL_COMPLETE: {elapsed_time}")
        
        return {
            "results": results,
            "elapsed_time_seconds": elapsed_time.total_seconds(),
            "completed_at": datetime.now().isoformat()
        }

    async def get_precompute_status(self) -> Dict[str, Any]:
        """Get status of pre-computation service and scheduled tasks."""
        return {
            "service_running": self.is_running,
            "scheduled_tasks": {
                name: {
                    "interval_hours": schedule["interval_hours"],
                    "last_run": schedule["last_run"].isoformat() if schedule["last_run"] else None,
                    "next_run_due": self._get_next_run_time(name, schedule).isoformat() if schedule["last_run"] else "Now"
                }
                for name, schedule in self.precompute_schedule.items()
            },
            "popular_data_counts": {
                "zodiac_signs": len(self.popular_signs),
                "locations": len(self.popular_locations),
                "chart_combinations": len(self.popular_signs) * len(self.popular_locations)
            }
        }

    def _get_next_run_time(self, task_name: str, schedule: Dict[str, Any]) -> datetime:
        """Calculate when a task should run next."""
        if schedule["last_run"] is None:
            return datetime.now()
        
        return schedule["last_run"] + timedelta(hours=schedule["interval_hours"])


# Global pre-computation service instance
precompute_service = PrecomputeService()