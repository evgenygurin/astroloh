"""
Startup manager for initializing performance optimizations and background services.
Coordinates the startup of caching, monitoring, and pre-computation services.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger

from app.services.async_kerykeion_service import async_kerykeion
from app.services.astro_cache_service import astro_cache
from app.services.performance_monitor import performance_monitor
from app.services.precompute_service import precompute_service


class StartupManager:
    """Manager for coordinating startup of performance optimization services."""
    
    def __init__(self):
        self.startup_completed = False
        self.startup_errors = []
        self.startup_stats = {
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "services_initialized": 0,
            "services_failed": 0,
            "cache_warmed": False,
            "monitoring_active": False,
            "precompute_active": False,
        }
        
        logger.info("STARTUP_MANAGER_INIT: Startup manager initialized")

    async def initialize_performance_systems(
        self, 
        enable_cache_warmup: bool = True,
        enable_background_monitoring: bool = True,
        enable_precomputation: bool = True,
        redis_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize all performance optimization systems."""
        self.startup_stats["start_time"] = datetime.now()
        logger.info("STARTUP_MANAGER_BEGIN: Initializing performance systems")
        
        initialization_results = {
            "async_kerykeion": {"status": "pending"},
            "cache_service": {"status": "pending"},
            "performance_monitor": {"status": "pending"},
            "precompute_service": {"status": "pending"},
            "cache_warmup": {"status": "pending"},
        }
        
        try:
            # 1. Initialize async Kerykeion service
            await self._initialize_async_kerykeion(initialization_results)
            
            # 2. Initialize cache service with Redis if available
            await self._initialize_cache_service(initialization_results, redis_url)
            
            # 3. Initialize performance monitoring
            await self._initialize_performance_monitor(initialization_results, enable_background_monitoring)
            
            # 4. Initialize pre-computation service
            await self._initialize_precompute_service(initialization_results, enable_precomputation)
            
            # 5. Warm up cache with popular data
            if enable_cache_warmup:
                await self._warm_up_cache(initialization_results)
            
            # 6. Run initial diagnostics
            diagnostics = await self._run_startup_diagnostics()
            
            self.startup_completed = True
            self.startup_stats["end_time"] = datetime.now()
            self.startup_stats["duration_seconds"] = (
                self.startup_stats["end_time"] - self.startup_stats["start_time"]
            ).total_seconds()
            
            logger.info(f"STARTUP_MANAGER_COMPLETE: All systems initialized in {self.startup_stats['duration_seconds']:.2f}s")
            
            return {
                "success": True,
                "initialization_results": initialization_results,
                "startup_stats": self.startup_stats,
                "diagnostics": diagnostics,
                "message": "Performance optimization systems successfully initialized"
            }
            
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_ERROR: {e}")
            self.startup_errors.append(str(e))
            
            return {
                "success": False,
                "initialization_results": initialization_results,
                "startup_stats": self.startup_stats,
                "errors": self.startup_errors,
                "message": f"Startup failed: {str(e)}"
            }

    async def _initialize_async_kerykeion(self, results: Dict[str, Any]):
        """Initialize async Kerykeion service."""
        try:
            logger.info("STARTUP_MANAGER_KERYKEION: Initializing async Kerykeion service")
            
            # Check if Kerykeion is available
            kerykeion_available = async_kerykeion.is_available()
            
            if kerykeion_available:
                # Test a simple operation to ensure it works
                test_stats = await async_kerykeion.get_performance_stats()
                
                results["async_kerykeion"] = {
                    "status": "success",
                    "available": True,
                    "stats": test_stats,
                }
                self.startup_stats["services_initialized"] += 1
                logger.info("STARTUP_MANAGER_KERYKEION_SUCCESS")
            else:
                results["async_kerykeion"] = {
                    "status": "warning", 
                    "available": False,
                    "message": "Kerykeion not available, using fallback calculations"
                }
                logger.warning("STARTUP_MANAGER_KERYKEION_FALLBACK")
                
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_KERYKEION_ERROR: {e}")
            results["async_kerykeion"] = {
                "status": "error",
                "error": str(e)
            }
            self.startup_stats["services_failed"] += 1
            self.startup_errors.append(f"Async Kerykeion: {str(e)}")

    async def _initialize_cache_service(self, results: Dict[str, Any], redis_url: Optional[str]):
        """Initialize caching service with Redis support."""
        try:
            logger.info("STARTUP_MANAGER_CACHE: Initializing cache service")
            
            # Initialize astro cache with Redis URL if provided
            if redis_url:
                # Reinitialize with Redis URL
                astro_cache.__init__(redis_url)
                logger.info(f"STARTUP_MANAGER_CACHE_REDIS: Redis configured at {redis_url}")
            
            # Test cache operations
            test_key = "startup_test"
            test_value = {"test": True, "timestamp": datetime.now().isoformat()}
            
            await astro_cache.set(test_key, test_value, 60)  # 1 minute TTL
            cached_value = await astro_cache.get(test_key)
            
            if cached_value and cached_value.get("test"):
                cache_stats = await astro_cache.get_cache_stats()
                results["cache_service"] = {
                    "status": "success",
                    "redis_available": astro_cache.redis_client is not None,
                    "stats": cache_stats
                }
                self.startup_stats["services_initialized"] += 1
                logger.info("STARTUP_MANAGER_CACHE_SUCCESS")
            else:
                raise Exception("Cache test failed")
                
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_CACHE_ERROR: {e}")
            results["cache_service"] = {
                "status": "error",
                "error": str(e)
            }
            self.startup_stats["services_failed"] += 1
            self.startup_errors.append(f"Cache Service: {str(e)}")

    async def _initialize_performance_monitor(self, results: Dict[str, Any], enable_background: bool):
        """Initialize performance monitoring."""
        try:
            logger.info("STARTUP_MANAGER_MONITOR: Initializing performance monitor")
            
            if enable_background:
                await performance_monitor.start_monitoring()
                self.startup_stats["monitoring_active"] = True
            
            # Test performance monitoring
            op_id = performance_monitor.start_operation("StartupManager", "test_operation")
            await asyncio.sleep(0.1)  # Simulate some work
            performance_monitor.end_operation(op_id, success=True)
            
            monitor_stats = performance_monitor.get_service_statistics("StartupManager")
            
            results["performance_monitor"] = {
                "status": "success",
                "background_monitoring": enable_background,
                "stats": monitor_stats
            }
            self.startup_stats["services_initialized"] += 1
            logger.info("STARTUP_MANAGER_MONITOR_SUCCESS")
            
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_MONITOR_ERROR: {e}")
            results["performance_monitor"] = {
                "status": "error",
                "error": str(e)
            }
            self.startup_stats["services_failed"] += 1
            self.startup_errors.append(f"Performance Monitor: {str(e)}")

    async def _initialize_precompute_service(self, results: Dict[str, Any], enable_precomputation: bool):
        """Initialize pre-computation service."""
        try:
            logger.info("STARTUP_MANAGER_PRECOMPUTE: Initializing pre-computation service")
            
            if enable_precomputation:
                await precompute_service.start_background_precomputation()
                self.startup_stats["precompute_active"] = True
            
            precompute_status = await precompute_service.get_precompute_status()
            
            results["precompute_service"] = {
                "status": "success",
                "background_active": enable_precomputation,
                "status_info": precompute_status
            }
            self.startup_stats["services_initialized"] += 1
            logger.info("STARTUP_MANAGER_PRECOMPUTE_SUCCESS")
            
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_PRECOMPUTE_ERROR: {e}")
            results["precompute_service"] = {
                "status": "error",
                "error": str(e)
            }
            self.startup_stats["services_failed"] += 1
            self.startup_errors.append(f"Precompute Service: {str(e)}")

    async def _warm_up_cache(self, results: Dict[str, Any]):
        """Warm up cache with popular astrological data."""
        try:
            logger.info("STARTUP_MANAGER_WARMUP: Starting cache warmup")
            
            # Pre-compute popular charts
            warmup_results = await async_kerykeion.precompute_popular_charts()
            
            # Pre-compute other popular data
            cache_precompute = await astro_cache.precompute_popular_data()
            
            # Manual pre-computation of critical data
            manual_precompute = await precompute_service.manual_precompute_all()
            
            results["cache_warmup"] = {
                "status": "success",
                "kerykeion_precompute": warmup_results,
                "cache_precompute": cache_precompute,
                "manual_precompute": manual_precompute
            }
            self.startup_stats["cache_warmed"] = True
            logger.info("STARTUP_MANAGER_WARMUP_SUCCESS")
            
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_WARMUP_ERROR: {e}")
            results["cache_warmup"] = {
                "status": "error",
                "error": str(e)
            }
            self.startup_errors.append(f"Cache Warmup: {str(e)}")

    async def _run_startup_diagnostics(self) -> Dict[str, Any]:
        """Run diagnostic tests to verify system health."""
        logger.info("STARTUP_MANAGER_DIAGNOSTICS: Running startup diagnostics")
        
        diagnostics = {
            "system_health": "unknown",
            "response_times": {},
            "cache_efficiency": {},
            "service_availability": {},
        }
        
        try:
            # Test response times for key operations
            import time
            
            # Test cache response time
            start_time = time.time()
            await astro_cache.get("nonexistent_key")
            cache_response_time = (time.time() - start_time) * 1000
            
            diagnostics["response_times"]["cache_ms"] = round(cache_response_time, 2)
            
            # Test async kerykeion availability
            start_time = time.time()
            kerykeion_stats = await async_kerykeion.get_performance_stats()
            kerykeion_response_time = (time.time() - start_time) * 1000
            
            diagnostics["response_times"]["kerykeion_ms"] = round(kerykeion_response_time, 2)
            
            # Check service availability
            diagnostics["service_availability"] = {
                "async_kerykeion": async_kerykeion.is_available(),
                "cache_service": True,  # If we got here, cache works
                "performance_monitor": performance_monitor.monitoring_active,
                "precompute_service": precompute_service.is_running,
            }
            
            # Determine overall health
            all_services_ok = all(diagnostics["service_availability"].values())
            fast_response_times = all(
                t < 100 for t in diagnostics["response_times"].values()  # Less than 100ms
            )
            
            if all_services_ok and fast_response_times:
                diagnostics["system_health"] = "excellent"
            elif all_services_ok:
                diagnostics["system_health"] = "good"
            else:
                diagnostics["system_health"] = "degraded"
                
            logger.info(f"STARTUP_MANAGER_DIAGNOSTICS_SUCCESS: System health: {diagnostics['system_health']}")
            
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_DIAGNOSTICS_ERROR: {e}")
            diagnostics["system_health"] = "error"
            diagnostics["error"] = str(e)
        
        return diagnostics

    async def shutdown_performance_systems(self) -> Dict[str, Any]:
        """Gracefully shutdown all performance optimization systems."""
        logger.info("STARTUP_MANAGER_SHUTDOWN: Shutting down performance systems")
        
        shutdown_results = {
            "performance_monitor": {"status": "pending"},
            "precompute_service": {"status": "pending"},
            "async_kerykeion": {"status": "pending"},
            "cache_service": {"status": "pending"},
        }
        
        try:
            # Stop performance monitoring
            try:
                await performance_monitor.stop_monitoring()
                shutdown_results["performance_monitor"]["status"] = "success"
                logger.info("STARTUP_MANAGER_SHUTDOWN_MONITOR_SUCCESS")
            except Exception as e:
                shutdown_results["performance_monitor"]["status"] = "error"
                shutdown_results["performance_monitor"]["error"] = str(e)
                logger.error(f"STARTUP_MANAGER_SHUTDOWN_MONITOR_ERROR: {e}")
            
            # Stop pre-computation service
            try:
                await precompute_service.stop_background_precomputation()
                shutdown_results["precompute_service"]["status"] = "success"
                logger.info("STARTUP_MANAGER_SHUTDOWN_PRECOMPUTE_SUCCESS")
            except Exception as e:
                shutdown_results["precompute_service"]["status"] = "error"
                shutdown_results["precompute_service"]["error"] = str(e)
                logger.error(f"STARTUP_MANAGER_SHUTDOWN_PRECOMPUTE_ERROR: {e}")
            
            # Shutdown async kerykeion
            try:
                await async_kerykeion.shutdown()
                shutdown_results["async_kerykeion"]["status"] = "success"
                logger.info("STARTUP_MANAGER_SHUTDOWN_KERYKEION_SUCCESS")
            except Exception as e:
                shutdown_results["async_kerykeion"]["status"] = "error"
                shutdown_results["async_kerykeion"]["error"] = str(e)
                logger.error(f"STARTUP_MANAGER_SHUTDOWN_KERYKEION_ERROR: {e}")
            
            # Shutdown cache service
            try:
                await astro_cache.shutdown()
                shutdown_results["cache_service"]["status"] = "success"
                logger.info("STARTUP_MANAGER_SHUTDOWN_CACHE_SUCCESS")
            except Exception as e:
                shutdown_results["cache_service"]["status"] = "error"
                shutdown_results["cache_service"]["error"] = str(e)
                logger.error(f"STARTUP_MANAGER_SHUTDOWN_CACHE_ERROR: {e}")
            
            self.startup_completed = False
            logger.info("STARTUP_MANAGER_SHUTDOWN_COMPLETE")
            
            return {
                "success": True,
                "shutdown_results": shutdown_results,
                "message": "Performance systems gracefully shutdown"
            }
            
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_SHUTDOWN_ERROR: {e}")
            return {
                "success": False,
                "shutdown_results": shutdown_results,
                "error": str(e),
                "message": "Shutdown completed with errors"
            }

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all performance systems."""
        try:
            status = {
                "startup_completed": self.startup_completed,
                "startup_stats": self.startup_stats,
                "startup_errors": self.startup_errors,
                "current_time": datetime.now().isoformat(),
            }
            
            # Get individual service statuses
            if self.startup_completed:
                status["services"] = {
                    "async_kerykeion": await async_kerykeion.get_performance_stats(),
                    "cache_service": await astro_cache.get_cache_stats(),
                    "performance_monitor": performance_monitor.get_overall_statistics(),
                    "precompute_service": await precompute_service.get_precompute_status(),
                }
                
                # Generate performance report
                status["performance_report"] = performance_monitor.get_performance_report(24)
            
            return status
            
        except Exception as e:
            logger.error(f"STARTUP_MANAGER_STATUS_ERROR: {e}")
            return {
                "error": str(e),
                "startup_completed": self.startup_completed,
                "current_time": datetime.now().isoformat(),
            }


# Global startup manager instance
startup_manager = StartupManager()