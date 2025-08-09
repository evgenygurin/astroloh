"""
Advanced caching service for astrological calculations with performance optimization.
Extends the basic cache service with specific methods for Kerykeion data.
"""

import hashlib
import importlib.util
import json
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from app.services.cache_service import CacheService

# Check Redis availability without importing it
REDIS_AVAILABLE = importlib.util.find_spec("redis.asyncio") is not None


class AstroCacheService(CacheService):
    """Enhanced caching service for astrological data with performance monitoring."""

    def __init__(self, redis_url: Optional[str] = None):
        super().__init__(redis_url)
        self.performance_metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "average_response_time": 0,
            "slow_operations": 0,
        }

        # Astrological data specific TTL (Time To Live) settings
        self.astro_ttl = {
            "natal_chart": 86400 * 30,  # 30 days (natal charts don't change)
            "daily_ephemeris": 3600 * 6,  # 6 hours (ephemeris data)
            "current_transits": 3600,  # 1 hour (current transits)
            "period_forecasts": 3600 * 2,  # 2 hours (weekly/monthly forecasts)
            "compatibility": 86400 * 7,  # 7 days (compatibility analysis)
            "arabic_parts": 86400 * 30,  # 30 days (Arabic parts)
            "chart_analysis": 86400 * 7,  # 7 days (chart pattern analysis)
            "popular_calculations": 1800,  # 30 minutes (pre-computed popular data)
        }

        logger.info(
            "ASTRO_CACHE_SERVICE_INIT: Enhanced astrological caching initialized"
        )

    async def cache_data(
        self, key: str, data: Any, ttl_hours: int = 24
    ) -> bool:
        """
        Cache data with TTL in hours.
        Compatibility method for tests and general caching.
        """
        try:
            ttl_seconds = ttl_hours * 3600
            await self.set(key, data, ttl=ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"ASTRO_CACHE_ERROR: Failed to cache data: {e}")
            return False

    async def get_cached_data(self, key: str) -> Optional[Any]:
        """
        Retrieve cached data.
        Compatibility method for tests and general caching.
        """
        try:
            return await self.get(key)
        except Exception as e:
            logger.error(f"ASTRO_CACHE_ERROR: Failed to get cached data: {e}")
            return None

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate deterministic cache key for astrological data."""
        # Sort kwargs for consistent keys
        sorted_kwargs = sorted(kwargs.items())
        key_data = f"{prefix}:" + ":".join(
            [f"{k}={v}" for k, v in sorted_kwargs]
        )

        # Use hash for very long keys
        if len(key_data) > 200:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"

        return key_data

    async def get_natal_chart(
        self,
        birth_datetime: Union[datetime, str],
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Moscow",
        house_system: str = "Placidus",
    ) -> Optional[Dict[str, Any]]:
        """Get cached natal chart data."""
        start_time = time.time()

        # Convert datetime to string for consistent caching
        birth_dt_str = (
            birth_datetime.isoformat()
            if isinstance(birth_datetime, datetime)
            else birth_datetime
        )

        cache_key = self._generate_cache_key(
            "natal_chart",
            birth_dt=birth_dt_str,
            lat=round(latitude, 6),
            lng=round(longitude, 6),
            tz=timezone,
            house_system=house_system,
        )

        result = await self.get(cache_key)
        self._update_performance_metrics(start_time, result is not None)

        if result:
            logger.debug(f"ASTRO_CACHE_HIT: Natal chart {cache_key}")
        else:
            logger.debug(f"ASTRO_CACHE_MISS: Natal chart {cache_key}")

        return result

    async def set_natal_chart(
        self,
        birth_datetime: Union[datetime, str],
        latitude: float,
        longitude: float,
        chart_data: Dict[str, Any],
        timezone: str = "Europe/Moscow",
        house_system: str = "Placidus",
    ) -> bool:
        """Cache natal chart data."""
        birth_dt_str = (
            birth_datetime.isoformat()
            if isinstance(birth_datetime, datetime)
            else birth_datetime
        )

        cache_key = self._generate_cache_key(
            "natal_chart",
            birth_dt=birth_dt_str,
            lat=round(latitude, 6),
            lng=round(longitude, 6),
            tz=timezone,
            house_system=house_system,
        )

        success = await self.set(
            cache_key, chart_data, self.astro_ttl["natal_chart"]
        )

        if success:
            logger.info(f"ASTRO_CACHE_SET: Natal chart cached {cache_key}")
        else:
            logger.error(
                f"ASTRO_CACHE_SET_ERROR: Failed to cache natal chart {cache_key}"
            )

        return success

    async def get_daily_ephemeris(
        self, date: Union[date, str]
    ) -> Optional[Dict[str, Any]]:
        """Get cached daily ephemeris data."""
        start_time = time.time()

        date_str = date.isoformat() if isinstance(date, date) else date
        cache_key = f"ephemeris:daily:{date_str}"

        result = await self.get(cache_key)
        self._update_performance_metrics(start_time, result is not None)

        if result:
            logger.debug(f"ASTRO_CACHE_HIT: Daily ephemeris {date_str}")
        else:
            logger.debug(f"ASTRO_CACHE_MISS: Daily ephemeris {date_str}")

        return result

    async def set_daily_ephemeris(
        self, date: Union[date, str], ephemeris_data: Dict[str, Any]
    ) -> bool:
        """Cache daily ephemeris data."""
        date_str = date.isoformat() if isinstance(date, date) else date
        cache_key = f"ephemeris:daily:{date_str}"

        return await self.set(
            cache_key, ephemeris_data, self.astro_ttl["daily_ephemeris"]
        )

    async def get_current_transits(
        self,
        natal_chart_id: str,
        transit_date: Union[datetime, str],
        include_minor: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Get cached current transits."""
        start_time = time.time()

        transit_dt_str = (
            transit_date.isoformat()
            if isinstance(transit_date, datetime)
            else transit_date
        )
        cache_key = self._generate_cache_key(
            "transits_current",
            chart_id=natal_chart_id,
            date=transit_dt_str,
            minor=include_minor,
        )

        result = await self.get(cache_key)
        self._update_performance_metrics(start_time, result is not None)

        if result:
            logger.debug(f"ASTRO_CACHE_HIT: Current transits {cache_key}")
        else:
            logger.debug(f"ASTRO_CACHE_MISS: Current transits {cache_key}")

        return result

    async def set_current_transits(
        self,
        natal_chart_id: str,
        transit_date: Union[datetime, str],
        transit_data: Dict[str, Any],
        include_minor: bool = True,
    ) -> bool:
        """Cache current transits."""
        transit_dt_str = (
            transit_date.isoformat()
            if isinstance(transit_date, datetime)
            else transit_date
        )
        cache_key = self._generate_cache_key(
            "transits_current",
            chart_id=natal_chart_id,
            date=transit_dt_str,
            minor=include_minor,
        )

        return await self.set(
            cache_key, transit_data, self.astro_ttl["current_transits"]
        )

    async def get_period_forecast(
        self, natal_chart_id: str, start_date: Union[date, str], days: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached period forecast."""
        start_time = time.time()

        start_dt_str = (
            start_date.isoformat()
            if isinstance(start_date, date)
            else start_date
        )
        cache_key = self._generate_cache_key(
            "forecast_period",
            chart_id=natal_chart_id,
            start=start_dt_str,
            days=days,
        )

        result = await self.get(cache_key)
        self._update_performance_metrics(start_time, result is not None)

        return result

    async def set_period_forecast(
        self,
        natal_chart_id: str,
        start_date: Union[date, str],
        days: int,
        forecast_data: Dict[str, Any],
    ) -> bool:
        """Cache period forecast."""
        start_dt_str = (
            start_date.isoformat()
            if isinstance(start_date, date)
            else start_date
        )
        cache_key = self._generate_cache_key(
            "forecast_period",
            chart_id=natal_chart_id,
            start=start_dt_str,
            days=days,
        )

        return await self.set(
            cache_key, forecast_data, self.astro_ttl["period_forecasts"]
        )

    async def get_compatibility_analysis(
        self,
        person1_birth: str,
        person2_birth: str,
        analysis_type: str = "romantic",
    ) -> Optional[Dict[str, Any]]:
        """Get cached compatibility analysis."""
        start_time = time.time()

        # Create consistent ordering for cache key
        births = sorted([person1_birth, person2_birth])
        cache_key = self._generate_cache_key(
            "compatibility",
            person1=births[0],
            person2=births[1],
            type=analysis_type,
        )

        result = await self.get(cache_key)
        self._update_performance_metrics(start_time, result is not None)

        return result

    async def set_compatibility_analysis(
        self,
        person1_birth: str,
        person2_birth: str,
        compatibility_data: Dict[str, Any],
        analysis_type: str = "romantic",
    ) -> bool:
        """Cache compatibility analysis."""
        births = sorted([person1_birth, person2_birth])
        cache_key = self._generate_cache_key(
            "compatibility",
            person1=births[0],
            person2=births[1],
            type=analysis_type,
        )

        return await self.set(
            cache_key, compatibility_data, self.astro_ttl["compatibility"]
        )

    async def get_arabic_parts(
        self, natal_chart_id: str, include_extended: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get cached Arabic Parts calculation."""
        start_time = time.time()

        cache_key = self._generate_cache_key(
            "arabic_parts", chart_id=natal_chart_id, extended=include_extended
        )

        result = await self.get(cache_key)
        self._update_performance_metrics(start_time, result is not None)

        return result

    async def set_arabic_parts(
        self,
        natal_chart_id: str,
        parts_data: Dict[str, Any],
        include_extended: bool = True,
    ) -> bool:
        """Cache Arabic Parts calculation."""
        cache_key = self._generate_cache_key(
            "arabic_parts", chart_id=natal_chart_id, extended=include_extended
        )

        return await self.set(
            cache_key, parts_data, self.astro_ttl["arabic_parts"]
        )

    async def get_chart_analysis(
        self, natal_chart_id: str, analysis_types: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Get cached chart pattern analysis."""
        start_time = time.time()

        cache_key = self._generate_cache_key(
            "chart_analysis",
            chart_id=natal_chart_id,
            types=",".join(sorted(analysis_types)),
        )

        result = await self.get(cache_key)
        self._update_performance_metrics(start_time, result is not None)

        return result

    async def set_chart_analysis(
        self,
        natal_chart_id: str,
        analysis_data: Dict[str, Any],
        analysis_types: List[str],
    ) -> bool:
        """Cache chart pattern analysis."""
        cache_key = self._generate_cache_key(
            "chart_analysis",
            chart_id=natal_chart_id,
            types=",".join(sorted(analysis_types)),
        )

        return await self.set(
            cache_key, analysis_data, self.astro_ttl["chart_analysis"]
        )

    async def precompute_popular_data(self) -> Dict[str, Any]:
        """Pre-compute and cache popular astrological data."""
        logger.info(
            "ASTRO_CACHE_PRECOMPUTE_START: Starting popular data pre-computation"
        )

        start_time = time.time()
        precomputed_data = {}

        try:
            # Pre-compute today's ephemeris for all zodiac signs
            today = datetime.now().date()
            ephemeris_key = f"ephemeris:popular:{today.isoformat()}"

            # This would call the actual calculation service
            # For now, we'll create placeholder data
            popular_ephemeris = {
                "date": today.isoformat(),
                "planets": {},
                "computed_at": datetime.now().isoformat(),
            }

            await self.set(
                ephemeris_key,
                popular_ephemeris,
                self.astro_ttl["popular_calculations"],
            )
            precomputed_data["ephemeris"] = True

            # Pre-compute popular zodiac sign combinations
            popular_combinations = [
                ("Leo", "Aries"),
                ("Scorpio", "Cancer"),
                ("Gemini", "Libra"),
                ("Virgo", "Capricorn"),
                ("Sagittarius", "Leo"),
                ("Aquarius", "Gemini"),
            ]

            for sign1, sign2 in popular_combinations:
                compat_key = f"compatibility:popular:{sign1}:{sign2}"
                popular_compatibility = {
                    "sign1": sign1,
                    "sign2": sign2,
                    "basic_compatibility": 75,  # Placeholder
                    "computed_at": datetime.now().isoformat(),
                }
                await self.set(
                    compat_key,
                    popular_compatibility,
                    self.astro_ttl["popular_calculations"],
                )

            precomputed_data["compatibility_combinations"] = len(
                popular_combinations
            )

            # Pre-compute lunar phases for next 30 days
            lunar_phases = []
            current_date = today
            for i in range(30):
                phase_date = current_date + timedelta(days=i)
                lunar_phases.append(
                    {
                        "date": phase_date.isoformat(),
                        "phase": "placeholder",  # Would be calculated
                        "illumination": 0.5,  # Placeholder
                    }
                )

            lunar_key = "lunar:phases:30days"
            await self.set(
                lunar_key, lunar_phases, self.astro_ttl["popular_calculations"]
            )
            precomputed_data["lunar_phases"] = True

            elapsed_time = time.time() - start_time
            logger.info(
                f"ASTRO_CACHE_PRECOMPUTE_SUCCESS: Completed in {elapsed_time:.2f}s"
            )

            return precomputed_data

        except Exception as e:
            logger.error(f"ASTRO_CACHE_PRECOMPUTE_ERROR: {e}")
            return {"error": str(e)}

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics."""
        total_requests = self.performance_metrics["total_requests"]
        cache_hits = self.performance_metrics["cache_hits"]

        hit_rate = (
            (cache_hits / total_requests * 100) if total_requests > 0 else 0
        )

        stats = {
            "performance": {
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "cache_misses": self.performance_metrics["cache_misses"],
                "hit_rate_percentage": round(hit_rate, 2),
                "average_response_time_ms": round(
                    self.performance_metrics["average_response_time"] * 1000, 2
                ),
                "slow_operations": self.performance_metrics["slow_operations"],
            },
            "cache_info": {
                "redis_available": REDIS_AVAILABLE,
                "redis_connected": self.redis_client is not None,
                "memory_cache_size": len(self.memory_cache),
                "memory_cache_limit": self.max_memory_items,
            },
            "ttl_settings": self.astro_ttl,
        }

        # Add Redis-specific stats if available
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
                stats["redis_info"] = {
                    "used_memory": redis_info.get(
                        "used_memory_human", "Unknown"
                    ),
                    "used_memory_peak": redis_info.get(
                        "used_memory_peak_human", "Unknown"
                    ),
                    "connected_clients": redis_info.get(
                        "connected_clients", 0
                    ),
                }
            except Exception as e:
                logger.warning(f"ASTRO_CACHE_REDIS_INFO_ERROR: {e}")

        return stats

    def _update_performance_metrics(self, start_time: float, cache_hit: bool):
        """Update internal performance metrics."""
        elapsed_time = time.time() - start_time

        self.performance_metrics["total_requests"] += 1

        if cache_hit:
            self.performance_metrics["cache_hits"] += 1
        else:
            self.performance_metrics["cache_misses"] += 1

        # Update average response time (rolling average)
        current_avg = self.performance_metrics["average_response_time"]
        total_requests = self.performance_metrics["total_requests"]

        new_avg = (
            (current_avg * (total_requests - 1)) + elapsed_time
        ) / total_requests
        self.performance_metrics["average_response_time"] = new_avg

        # Track slow operations (> 100ms)
        if elapsed_time > 0.1:
            self.performance_metrics["slow_operations"] += 1
            logger.warning(f"ASTRO_CACHE_SLOW_OPERATION: {elapsed_time:.3f}s")

    async def invalidate_user_data(self, user_identifier: str) -> int:
        """Invalidate all cached data for a specific user."""
        logger.info(f"ASTRO_CACHE_INVALIDATE_USER: {user_identifier}")

        invalidated_count = 0

        # Pattern to match user-specific cache keys
        patterns = [
            f"natal_chart:*{user_identifier}*",
            f"transits_current:*{user_identifier}*",
            f"forecast_period:*{user_identifier}*",
            f"compatibility:*{user_identifier}*",
            f"arabic_parts:*{user_identifier}*",
            f"chart_analysis:*{user_identifier}*",
        ]

        if self.redis_client:
            # Redis pattern matching
            for pattern in patterns:
                try:
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                        invalidated_count += len(keys)
                except Exception as e:
                    logger.error(f"ASTRO_CACHE_INVALIDATE_REDIS_ERROR: {e}")
        else:
            # Memory cache pattern matching
            keys_to_delete = []
            for key in self.memory_cache.keys():
                if any(
                    pattern.replace("*", "") in key for pattern in patterns
                ):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                await self.delete(key)
                invalidated_count += 1

        logger.info(
            f"ASTRO_CACHE_INVALIDATE_COMPLETE: {invalidated_count} keys invalidated"
        )
        return invalidated_count

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            # Check Redis cache
            if self.redis_client:
                redis_data = await self.redis_client.get(key)
                if redis_data:
                    return json.loads(redis_data)

            # Check memory cache fallback
            if key in self.memory_cache:
                data, timestamp, ttl = self.memory_cache[key]

                # Check if expired
                if ttl is not None and (time.time() - timestamp) > ttl:
                    del self.memory_cache[key]
                    return None

                return data

            return None
        except Exception as e:
            logger.error(f"ASTRO_CACHE_GET_ERROR: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache."""
        try:
            # Set in Redis cache
            if self.redis_client:
                json_data = json.dumps(value, default=str)
                if ttl:
                    await self.redis_client.setex(key, ttl, json_data)
                else:
                    await self.redis_client.set(key, json_data)

            # Set in memory cache as fallback
            timestamp = time.time()
            self.memory_cache[key] = (value, timestamp, ttl)

            # Enforce memory cache size limit
            if len(self.memory_cache) > self.max_memory_items:
                # Remove oldest item
                oldest_key = min(
                    self.memory_cache.keys(),
                    key=lambda k: self.memory_cache[k][1],  # timestamp
                )
                del self.memory_cache[oldest_key]

            return True
        except Exception as e:
            logger.error(f"ASTRO_CACHE_SET_ERROR: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]

            # Remove from Redis cache
            if self.redis_client:
                await self.redis_client.delete(key)

            return True
        except Exception as e:
            logger.error(f"ASTRO_CACHE_DELETE_ERROR: {e}")
            return False

    async def clear_expired_cache(self) -> int:
        """Manually clear expired cache entries."""
        logger.info("ASTRO_CACHE_CLEANUP_START: Clearing expired entries")

        cleared_count = 0

        if not self.redis_client:
            # Only needed for memory cache - Redis handles TTL automatically
            now = datetime.utcnow()
            expired_keys = [
                key
                for key, expiry in self.cache_expiry.items()
                if now > expiry
            ]

            for key in expired_keys:
                await self.delete(key)
                cleared_count += 1

        logger.info(
            f"ASTRO_CACHE_CLEANUP_COMPLETE: {cleared_count} expired entries cleared"
        )
        return cleared_count


# Global astro cache service instance
astro_cache = AstroCacheService()
