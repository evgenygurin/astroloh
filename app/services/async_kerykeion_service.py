"""
Asynchronous wrapper for Kerykeion service with performance optimizations.
Provides non-blocking astrological calculations with intelligent caching.
"""

import asyncio
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from app.services.kerykeion_service import (
    KerykeionService, 
    HouseSystem, 
    ZodiacType, 
    KERYKEION_AVAILABLE
)
from app.services.astro_cache_service import astro_cache


class AsyncKerykeionService:
    """Asynchronous wrapper for KerykeionService with performance optimizations."""
    
    def __init__(self, max_workers: int = 4):
        self.kerykeion_service = KerykeionService()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.performance_stats = {
            "total_operations": 0,
            "cached_operations": 0,
            "async_operations": 0,
            "average_calculation_time": 0.0,
            "slow_calculations": 0,
        }
        
        logger.info(f"ASYNC_KERYKEION_INIT: Service initialized with {max_workers} workers")
        
    def is_available(self) -> bool:
        """Check if Kerykeion is available."""
        return self.kerykeion_service.is_available()

    def _generate_chart_id(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Moscow"
    ) -> str:
        """Generate unique ID for natal chart."""
        data = f"{birth_datetime.isoformat()}_{latitude}_{longitude}_{timezone}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def get_full_natal_chart_data(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Moscow",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        zodiac_type: ZodiacType = ZodiacType.TROPICAL,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive natal chart data asynchronously with caching."""
        start_time = time.time()
        self.performance_stats["total_operations"] += 1
        
        logger.info(f"ASYNC_KERYKEION_NATAL_START: {name}")
        
        # Check cache first
        if use_cache:
            cached_result = await astro_cache.get_natal_chart(
                birth_datetime=birth_datetime,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                house_system=house_system.value
            )
            
            if cached_result:
                self.performance_stats["cached_operations"] += 1
                elapsed = time.time() - start_time
                self._update_average_time(elapsed)
                logger.info(f"ASYNC_KERYKEION_NATAL_CACHED: {name} in {elapsed:.3f}s")
                return cached_result
        
        # If not available, return error immediately
        if not self.is_available():
            return {"error": "Kerykeion not available"}
        
        # Calculate asynchronously
        try:
            self.performance_stats["async_operations"] += 1
            
            # Run in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._calculate_natal_chart_sync,
                name, birth_datetime, latitude, longitude, timezone, house_system, zodiac_type
            )
            
            elapsed = time.time() - start_time
            self._update_average_time(elapsed)
            
            if elapsed > 2.0:  # Slow calculation threshold
                self.performance_stats["slow_calculations"] += 1
                logger.warning(f"ASYNC_KERYKEION_SLOW_CALCULATION: {elapsed:.3f}s for {name}")
            
            # Cache successful results
            if use_cache and not result.get("error"):
                await astro_cache.set_natal_chart(
                    birth_datetime=birth_datetime,
                    latitude=latitude,
                    longitude=longitude,
                    chart_data=result,
                    timezone=timezone,
                    house_system=house_system.value
                )
            
            logger.info(f"ASYNC_KERYKEION_NATAL_SUCCESS: {name} in {elapsed:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"ASYNC_KERYKEION_NATAL_ERROR: {e}")
            return {"error": f"Async calculation failed: {str(e)}"}

    def _calculate_natal_chart_sync(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str,
        house_system: HouseSystem,
        zodiac_type: ZodiacType
    ) -> Dict[str, Any]:
        """Synchronous natal chart calculation for thread pool execution."""
        return self.kerykeion_service.get_full_natal_chart_data(
            name=name,
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            house_system=house_system,
            zodiac_type=zodiac_type
        )

    async def calculate_compatibility_detailed(
        self,
        person1_data: Dict[str, Any],
        person2_data: Dict[str, Any],
        analysis_type: str = "romantic",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Calculate detailed compatibility asynchronously with caching."""
        start_time = time.time()
        self.performance_stats["total_operations"] += 1
        
        logger.info("ASYNC_KERYKEION_COMPATIBILITY_START")
        
        # Generate cache key based on chart data
        person1_id = person1_data.get("subject_info", {}).get("birth_datetime", "unknown1")
        person2_id = person2_data.get("subject_info", {}).get("birth_datetime", "unknown2")
        
        # Check cache first
        if use_cache:
            cached_result = await astro_cache.get_compatibility_analysis(
                person1_birth=person1_id,
                person2_birth=person2_id,
                analysis_type=analysis_type
            )
            
            if cached_result:
                self.performance_stats["cached_operations"] += 1
                elapsed = time.time() - start_time
                self._update_average_time(elapsed)
                logger.info(f"ASYNC_KERYKEION_COMPATIBILITY_CACHED: {elapsed:.3f}s")
                return cached_result
        
        if not self.is_available():
            return {"error": "Kerykeion not available"}
        
        # Calculate asynchronously
        try:
            self.performance_stats["async_operations"] += 1
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.kerykeion_service.calculate_compatibility_detailed,
                person1_data,
                person2_data
            )
            
            elapsed = time.time() - start_time
            self._update_average_time(elapsed)
            
            if elapsed > 3.0:  # Compatibility calculations can be slower
                self.performance_stats["slow_calculations"] += 1
                logger.warning(f"ASYNC_KERYKEION_COMPATIBILITY_SLOW: {elapsed:.3f}s")
            
            # Cache successful results
            if use_cache and not result.get("error"):
                await astro_cache.set_compatibility_analysis(
                    person1_birth=person1_id,
                    person2_birth=person2_id,
                    compatibility_data=result,
                    analysis_type=analysis_type
                )
            
            logger.info(f"ASYNC_KERYKEION_COMPATIBILITY_SUCCESS: {elapsed:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"ASYNC_KERYKEION_COMPATIBILITY_ERROR: {e}")
            return {"error": f"Async compatibility calculation failed: {str(e)}"}

    async def calculate_arabic_parts_extended(
        self,
        natal_chart_data: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Calculate extended Arabic Parts asynchronously with caching."""
        start_time = time.time()
        self.performance_stats["total_operations"] += 1
        
        logger.info("ASYNC_KERYKEION_ARABIC_PARTS_START")
        
        # Generate chart ID for caching
        chart_id = self._generate_chart_id(
            birth_datetime=datetime.fromisoformat(
                natal_chart_data.get("subject_info", {}).get("birth_datetime", "2000-01-01T00:00:00")
            ),
            latitude=natal_chart_data.get("subject_info", {}).get("coordinates", {}).get("latitude", 0),
            longitude=natal_chart_data.get("subject_info", {}).get("coordinates", {}).get("longitude", 0)
        )
        
        # Check cache first
        if use_cache:
            cached_result = await astro_cache.get_arabic_parts(
                natal_chart_id=chart_id,
                include_extended=True
            )
            
            if cached_result:
                self.performance_stats["cached_operations"] += 1
                elapsed = time.time() - start_time
                self._update_average_time(elapsed)
                logger.info(f"ASYNC_KERYKEION_ARABIC_PARTS_CACHED: {elapsed:.3f}s")
                return cached_result
        
        if not self.is_available():
            return {"error": "Kerykeion not available"}
        
        # Calculate asynchronously
        try:
            self.performance_stats["async_operations"] += 1
            
            # Create astrological subject from chart data
            subject = await self._create_subject_from_chart_data(natal_chart_data)
            
            if not subject:
                return {"error": "Failed to create astrological subject"}
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.kerykeion_service.calculate_arabic_parts_extended,
                subject
            )
            
            elapsed = time.time() - start_time
            self._update_average_time(elapsed)
            
            # Cache successful results
            if use_cache and result:
                await astro_cache.set_arabic_parts(
                    natal_chart_id=chart_id,
                    parts_data=result,
                    include_extended=True
                )
            
            logger.info(f"ASYNC_KERYKEION_ARABIC_PARTS_SUCCESS: {elapsed:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"ASYNC_KERYKEION_ARABIC_PARTS_ERROR: {e}")
            return {"error": f"Async Arabic parts calculation failed: {str(e)}"}

    async def generate_chart_svg(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Moscow",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        theme: str = "classic"
    ) -> Optional[str]:
        """Generate SVG chart asynchronously."""
        start_time = time.time()
        self.performance_stats["total_operations"] += 1
        
        logger.info(f"ASYNC_KERYKEION_SVG_START: {name}")
        
        if not self.is_available():
            return None
        
        try:
            self.performance_stats["async_operations"] += 1
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._generate_svg_sync,
                name, birth_datetime, latitude, longitude, timezone, house_system, theme
            )
            
            elapsed = time.time() - start_time
            self._update_average_time(elapsed)
            
            if elapsed > 5.0:  # SVG generation can be slow
                self.performance_stats["slow_calculations"] += 1
                logger.warning(f"ASYNC_KERYKEION_SVG_SLOW: {elapsed:.3f}s")
            
            logger.info(f"ASYNC_KERYKEION_SVG_SUCCESS: {name} in {elapsed:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"ASYNC_KERYKEION_SVG_ERROR: {e}")
            return None

    def _generate_svg_sync(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str,
        house_system: HouseSystem,
        theme: str
    ) -> Optional[str]:
        """Synchronous SVG generation for thread pool execution."""
        return self.kerykeion_service.generate_chart_svg(
            name=name,
            birth_datetime=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            house_system=house_system,
            theme=theme
        )

    async def batch_calculate_charts(
        self,
        chart_requests: List[Dict[str, Any]],
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Calculate multiple natal charts in parallel."""
        logger.info(f"ASYNC_KERYKEION_BATCH_START: {len(chart_requests)} charts")
        
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = []
        for request in chart_requests:
            task = self.get_full_natal_chart_data(
                name=request.get("name", "Unknown"),
                birth_datetime=request["birth_datetime"],
                latitude=request["latitude"],
                longitude=request["longitude"],
                timezone=request.get("timezone", "Europe/Moscow"),
                house_system=HouseSystem(request.get("house_system", "Placidus")),
                zodiac_type=ZodiacType(request.get("zodiac_type", "Tropical")),
                use_cache=use_cache
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"ASYNC_KERYKEION_BATCH_ERROR: Chart {i} failed: {result}")
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)
        
        elapsed = time.time() - start_time
        logger.info(f"ASYNC_KERYKEION_BATCH_SUCCESS: {len(chart_requests)} charts in {elapsed:.3f}s")
        
        return processed_results

    async def _create_subject_from_chart_data(self, chart_data: Dict[str, Any]) -> Optional[Any]:
        """Create astrological subject from existing chart data."""
        try:
            subject_info = chart_data.get("subject_info", {})
            birth_datetime = datetime.fromisoformat(subject_info.get("birth_datetime", "2000-01-01T00:00:00"))
            coordinates = subject_info.get("coordinates", {})
            
            return await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.kerykeion_service.create_astrological_subject,
                "SubjectFromData",
                birth_datetime,
                coordinates.get("latitude", 0),
                coordinates.get("longitude", 0),
                subject_info.get("timezone", "Europe/Moscow")
            )
        except Exception as e:
            logger.error(f"ASYNC_KERYKEION_CREATE_SUBJECT_ERROR: {e}")
            return None

    def _update_average_time(self, elapsed_time: float):
        """Update rolling average calculation time."""
        current_avg = self.performance_stats["average_calculation_time"]
        total_ops = self.performance_stats["total_operations"]
        
        new_avg = ((current_avg * (total_ops - 1)) + elapsed_time) / total_ops
        self.performance_stats["average_calculation_time"] = new_avg

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        cache_stats = await astro_cache.get_cache_stats()
        
        total_ops = self.performance_stats["total_operations"]
        cached_ops = self.performance_stats["cached_operations"]
        
        cache_efficiency = (cached_ops / total_ops * 100) if total_ops > 0 else 0
        
        return {
            "async_kerykeion_stats": {
                "total_operations": total_ops,
                "cached_operations": cached_ops,
                "async_operations": self.performance_stats["async_operations"],
                "cache_efficiency_percentage": round(cache_efficiency, 2),
                "average_calculation_time_ms": round(self.performance_stats["average_calculation_time"] * 1000, 2),
                "slow_calculations": self.performance_stats["slow_calculations"],
                "kerykeion_available": self.is_available()
            },
            "cache_stats": cache_stats,
            "thread_pool_info": {
                "max_workers": self.executor._max_workers,
                "active_threads": len(self.executor._threads) if hasattr(self.executor, '_threads') else 0
            }
        }

    async def precompute_popular_charts(self) -> Dict[str, Any]:
        """Pre-compute popular astrological charts and cache them."""
        logger.info("ASYNC_KERYKEION_PRECOMPUTE_START: Popular charts pre-computation")
        
        start_time = time.time()
        
        # Define popular birth dates and locations for pre-computation
        popular_requests = [
            # Famous personalities (placeholder dates)
            {
                "name": "Popular_Leo_Moscow",
                "birth_datetime": datetime(1990, 8, 15, 12, 0),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow"
            },
            {
                "name": "Popular_Scorpio_SPB",
                "birth_datetime": datetime(1985, 11, 8, 15, 30),
                "latitude": 59.9311,
                "longitude": 30.3609,
                "timezone": "Europe/Moscow"
            },
            {
                "name": "Popular_Gemini_Sochi",
                "birth_datetime": datetime(1992, 6, 10, 9, 45),
                "latitude": 43.6028,
                "longitude": 39.7342,
                "timezone": "Europe/Moscow"
            }
        ]
        
        try:
            # Pre-compute charts in parallel
            results = await self.batch_calculate_charts(popular_requests, use_cache=True)
            
            # Pre-compute popular ephemeris data
            await astro_cache.precompute_popular_data()
            
            elapsed_time = time.time() - start_time
            
            success_count = sum(1 for result in results if not result.get("error"))
            
            logger.info(f"ASYNC_KERYKEION_PRECOMPUTE_SUCCESS: {success_count}/{len(popular_requests)} charts in {elapsed_time:.3f}s")
            
            return {
                "precomputed_charts": success_count,
                "total_requests": len(popular_requests),
                "elapsed_time_seconds": elapsed_time,
                "success_rate_percentage": (success_count / len(popular_requests) * 100) if popular_requests else 0
            }
            
        except Exception as e:
            logger.error(f"ASYNC_KERYKEION_PRECOMPUTE_ERROR: {e}")
            return {"error": str(e)}

    async def shutdown(self):
        """Gracefully shutdown the service."""
        logger.info("ASYNC_KERYKEION_SHUTDOWN: Shutting down service")
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        # Shutdown cache service
        await astro_cache.shutdown()
        
        logger.info("ASYNC_KERYKEION_SHUTDOWN_COMPLETE")


# Global async kerykeion service instance
async_kerykeion = AsyncKerykeionService(max_workers=4)