"""Caching service for IoT device data and analytics."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set
from loguru import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Using in-memory cache fallback.")


class CacheService:
    """Service for caching IoT device data and analytics results."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.max_memory_items = 1000
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Try to initialize Redis if available and configured
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using memory cache.")
                self.redis_client = None
        
        # Start cleanup task for memory cache
        if not self.redis_client:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            else:
                # Use memory cache
                if key in self.cache_expiry:
                    if datetime.utcnow() > self.cache_expiry[key]:
                        # Expired
                        await self.delete(key)
                        return None
                
                return self.memory_cache.get(key, {}).get('value')
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expiry_seconds: int = 3600
    ) -> bool:
        """Set value in cache with expiry."""
        try:
            if self.redis_client:
                serialized_value = json.dumps(value, default=str)
                await self.redis_client.setex(key, expiry_seconds, serialized_value)
                return True
            else:
                # Use memory cache
                if len(self.memory_cache) >= self.max_memory_items:
                    # Remove oldest entries
                    await self._cleanup_oldest_entries()
                
                self.memory_cache[key] = {
                    'value': value,
                    'created_at': datetime.utcnow()
                }
                self.cache_expiry[key] = datetime.utcnow() + timedelta(seconds=expiry_seconds)
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
                return True
            else:
                # Use memory cache
                self.memory_cache.pop(key, None)
                self.cache_expiry.pop(key, None)
                return True
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def get_device_capabilities(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get cached device capabilities."""
        cache_key = f"device_capabilities:{device_id}"
        return await self.get(cache_key)
    
    async def set_device_capabilities(
        self, 
        device_id: str, 
        capabilities: Dict[str, Any],
        expiry_minutes: int = 60
    ) -> bool:
        """Cache device capabilities."""
        cache_key = f"device_capabilities:{device_id}"
        return await self.set(cache_key, capabilities, expiry_minutes * 60)
    
    async def get_user_devices(self, user_id: int) -> Optional[list]:
        """Get cached user devices list."""
        cache_key = f"user_devices:{user_id}"
        return await self.get(cache_key)
    
    async def set_user_devices(
        self, 
        user_id: int, 
        devices: list,
        expiry_minutes: int = 30
    ) -> bool:
        """Cache user devices list."""
        cache_key = f"user_devices:{user_id}"
        return await self.set(cache_key, devices, expiry_minutes * 60)
    
    async def invalidate_user_devices(self, user_id: int) -> bool:
        """Invalidate cached user devices."""
        cache_key = f"user_devices:{user_id}"
        return await self.delete(cache_key)
    
    async def get_analytics_result(
        self, 
        user_id: int, 
        analysis_type: str,
        period_days: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached analytics result."""
        cache_key = f"analytics:{user_id}:{analysis_type}:{period_days}"
        return await self.get(cache_key)
    
    async def set_analytics_result(
        self, 
        user_id: int, 
        analysis_type: str,
        period_days: int,
        result: Dict[str, Any],
        expiry_hours: int = 4
    ) -> bool:
        """Cache analytics result."""
        cache_key = f"analytics:{user_id}:{analysis_type}:{period_days}"
        return await self.set(cache_key, result, expiry_hours * 3600)
    
    async def get_automation_insights(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached automation insights."""
        cache_key = f"automation_insights:{user_id}"
        return await self.get(cache_key)
    
    async def set_automation_insights(
        self, 
        user_id: int, 
        insights: Dict[str, Any],
        expiry_hours: int = 6
    ) -> bool:
        """Cache automation insights."""
        cache_key = f"automation_insights:{user_id}"
        return await self.set(cache_key, insights, expiry_hours * 3600)
    
    async def _cleanup_expired_entries(self):
        """Background task to cleanup expired memory cache entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                now = datetime.utcnow()
                expired_keys = [
                    key for key, expiry in self.cache_expiry.items()
                    if now > expiry
                ]
                
                for key in expired_keys:
                    await self.delete(key)
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_oldest_entries(self):
        """Remove oldest entries when memory cache is full."""
        if not self.memory_cache:
            return
        
        # Sort by creation time and remove oldest 10%
        entries_by_age = sorted(
            [(key, data['created_at']) for key, data in self.memory_cache.items()],
            key=lambda x: x[1]
        )
        
        remove_count = max(1, len(entries_by_age) // 10)
        for key, _ in entries_by_age[:remove_count]:
            await self.delete(key)
    
    async def shutdown(self):
        """Shutdown cache service."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.aclose()
        
        logger.info("Cache service shut down")


# Global cache service instance
cache_service = CacheService()