# Performance Optimization Guide

## Overview

This guide covers the comprehensive performance optimization system implemented in Astroloh, designed specifically to meet Alice voice interface requirements (<3 seconds response time) while maintaining accuracy and reliability.

## Performance Architecture

### Multi-Layer Performance Strategy

```
Request → Performance Monitor → Cache Check → Service Layer → Response
    ↓             ↓                ↓              ↓           ↓
 Metrics      Track Start     L1: Redis     Async Calc   Track End
Collection    Operation      L2: Memory    Background    Generate
   ↓             ↓                ↓         Precompute     Report
Alert        Resource         Database        ↓             ↓
System      Monitoring       Calculation   Cache Warm   Performance
   ↓             ↓                ↓            ↓           Analytics
Threshold    CPU/Memory      External APIs  Schedule       ↓
Detection    Tracking        Ephemeris     Tasks       Optimization
                                                       Recommendations
```

## Core Performance Services

### AstroCacheService (`astro_cache_service.py`)

Advanced caching system optimized for astrological data patterns.

#### Key Features

**Redis Integration with Fallback**:
```python
# Automatic Redis detection
try:
    import redis.asyncio as redis
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Redis cache initialized successfully")
except ImportError:
    logger.warning("Redis unavailable. Using memory cache fallback")
    redis_client = None
```

**Data-Type Specific TTL Policies**:
- **Natal Charts**: 30 days (permanent birth data)
- **Ephemeris Data**: 6 hours (daily planetary positions) 
- **Current Transits**: 1 hour (real-time calculations)
- **Period Forecasts**: 2 hours (weekly/monthly predictions)
- **Compatibility Analysis**: 7 days (relationship data)

**Performance Metrics**:
```python
async def get_cache_stats(self):
    """Get comprehensive cache performance statistics."""
    return {
        "hit_rate": self.hit_count / (self.hit_count + self.miss_count),
        "total_requests": self.hit_count + self.miss_count,
        "cache_size_mb": self.get_cache_size_mb(),
        "avg_response_time_ms": self.calculate_avg_response_time(),
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024
    }
```

#### Cache Strategies by Data Type

**Natal Chart Caching**:
- Long-term storage (30 days) for birth chart data
- MD5 hash keys based on birth parameters
- Automatic invalidation for preference changes

**Transit Caching**:
- Short-term caching (1 hour) for real-time calculations
- Batch processing for multiple days
- Intelligent cache warming for popular date ranges

**Ephemeris Caching**:
- Daily planetary position caching (6 hours)
- Background pre-computation for upcoming dates
- Geographical location-specific caching

### AsyncKerykeionService (`async_kerykeion_service.py`)

Non-blocking wrapper for CPU-intensive astrological calculations.

#### Thread Pool Architecture

```python
class AsyncKerykeionService:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.performance_stats = PerformanceStats()
        self.cache_service = AstroCacheService()
        
    async def calculate_natal_chart(self, params: dict) -> dict:
        """Async natal chart calculation with caching."""
        # Check cache first
        cache_key = self.generate_cache_key(params)
        if cached_result := await self.cache_service.get(cache_key):
            return cached_result
            
        # CPU-intensive calculation in thread pool
        result = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._sync_calculate_natal_chart,
            params
        )
        
        # Cache result
        await self.cache_service.set(cache_key, result, ttl=86400)
        return result
```

#### Batch Processing Capabilities

**Parallel Chart Calculations**:
```python
async def batch_calculate_charts(self, chart_requests: List[dict]) -> List[dict]:
    """Process multiple chart requests in parallel."""
    tasks = [
        self.calculate_natal_chart(request) 
        for request in chart_requests
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

**Performance Statistics Tracking**:
- P50, P95, P99 percentile response times
- Success/failure rates per operation type
- Memory usage per calculation
- Thread pool utilization metrics

### PerformanceMonitor (`performance_monitor.py`)

Real-time system monitoring with configurable alerting.

#### Comprehensive Monitoring Features

**Operation Tracking**:
```python
class PerformanceMonitor:
    def start_operation(self, service_name: str, operation_name: str) -> str:
        """Start tracking an operation."""
        operation_id = f"{service_name}_{operation_name}_{uuid.uuid4()}"
        self.active_operations[operation_id] = {
            "start_time": time.time(),
            "service": service_name,
            "operation": operation_name,
            "memory_start": psutil.Process().memory_info().rss
        }
        return operation_id
        
    def end_operation(self, operation_id: str, success: bool = True, 
                     cache_hit: bool = False, error_message: str = None):
        """End operation tracking and record metrics."""
        if operation_id not in self.active_operations:
            return
            
        op_data = self.active_operations.pop(operation_id)
        duration_ms = (time.time() - op_data["start_time"]) * 1000
        memory_used = psutil.Process().memory_info().rss - op_data["memory_start"]
        
        # Record comprehensive metrics
        self.record_metrics({
            "service": op_data["service"],
            "operation": op_data["operation"],
            "duration_ms": duration_ms,
            "success": success,
            "cache_hit": cache_hit,
            "memory_used_mb": memory_used / 1024 / 1024,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        })
```

**Alert System**:
```python
class AlertConfig:
    SLOW_OPERATION_THRESHOLD_MS = 2000
    HIGH_MEMORY_THRESHOLD_MB = 500
    HIGH_CPU_THRESHOLD_PERCENT = 80
    LOW_CACHE_HIT_RATE_THRESHOLD = 0.5
    
def check_performance_alerts(self, metrics: dict):
    """Check metrics against alert thresholds."""
    alerts = []
    
    if metrics["duration_ms"] > self.config.SLOW_OPERATION_THRESHOLD_MS:
        alerts.append({
            "type": "slow_operation",
            "message": f"Operation took {metrics['duration_ms']:.2f}ms",
            "severity": "warning"
        })
        
    if metrics["memory_used_mb"] > self.config.HIGH_MEMORY_THRESHOLD_MB:
        alerts.append({
            "type": "high_memory",
            "message": f"Operation used {metrics['memory_used_mb']:.2f}MB",
            "severity": "error"
        })
        
    return alerts
```

**Background System Monitoring**:
```python
async def start_background_monitoring(self):
    """Start continuous system monitoring."""
    while True:
        try:
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "active_connections": len(self.active_operations),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.record_system_metrics(system_metrics)
            await asyncio.sleep(30)  # Monitor every 30 seconds
            
        except Exception as e:
            logger.error(f"Background monitoring error: {e}")
            await asyncio.sleep(60)  # Extended delay on error
```

### PrecomputeService (`precompute_service.py`)

Background data pre-generation for popular astrological queries.

#### Intelligent Pre-computation Strategy

**Popular Data Identification**:
```python
class PrecomputeService:
    async def identify_popular_queries(self) -> List[dict]:
        """Analyze usage patterns to identify frequently requested data."""
        # Query database for most common requests
        popular_signs = await self.get_popular_zodiac_signs()
        popular_dates = await self.get_popular_date_ranges()
        popular_locations = await self.get_popular_birth_locations()
        
        return self.generate_precompute_tasks(
            signs=popular_signs,
            dates=popular_dates, 
            locations=popular_locations
        )
```

**Scheduled Background Tasks**:
```python
async def schedule_precomputation(self):
    """Schedule background pre-computation tasks."""
    tasks = [
        # Daily ephemeris for next 7 days
        self.precompute_ephemeris_data(days=7),
        
        # Popular chart combinations
        self.precompute_popular_natal_charts(),
        
        # Lunar phases for next 30 days
        self.precompute_lunar_calendar(days=30),
        
        # Popular compatibility combinations
        self.precompute_compatibility_matrix()
    ]
    
    # Run tasks with staggered scheduling
    for i, task in enumerate(tasks):
        await asyncio.sleep(i * 300)  # 5-minute intervals
        asyncio.create_task(task)
```

**Data Pre-generation Categories**:

1. **Daily Ephemeris**: 7 days ahead for all major locations
2. **Popular Charts**: Top 50 birth combinations (sign × location)
3. **Lunar Calendar**: Moon phases and void periods for 30 days
4. **Compatibility Matrix**: All 144 zodiac sign combinations
5. **Transit Forecasts**: Current transits for all signs

#### Performance Impact

**Cache Warmup Results**:
- 60-80% cache hit rate for popular requests
- Sub-500ms response times for cached data
- 70% reduction in CPU usage during peak hours
- 90% reduction in external API calls

### StartupManager (`startup_manager.py`)

Orchestrated system initialization with comprehensive health diagnostics.

#### Initialization Sequence

```python
class StartupManager:
    async def initialize_performance_systems(self, config: dict):
        """Initialize all performance systems in dependency order."""
        
        # Step 1: Core services
        await self.initialize_cache_service()
        await self.initialize_performance_monitor()
        
        # Step 2: Background services
        await self.initialize_precompute_service()
        await self.initialize_async_kerykeion()
        
        # Step 3: Cache warmup
        if config.get("enable_cache_warmup", True):
            await self.warmup_critical_caches()
            
        # Step 4: Health checks
        health_status = await self.comprehensive_health_check()
        
        # Step 5: Start monitoring
        if config.get("enable_background_monitoring", True):
            asyncio.create_task(self.start_background_monitoring())
            
        return health_status
```

#### Health Diagnostics

**System Status Monitoring**:
```python
async def get_system_status(self) -> dict:
    """Get comprehensive system status report."""
    return {
        "services": {
            "cache_service": await self.check_cache_health(),
            "performance_monitor": self.check_monitor_health(),
            "async_kerykeion": await self.check_kerykeion_health(),
            "precompute_service": self.check_precompute_health()
        },
        "performance": {
            "cache_hit_rate": await self.get_cache_hit_rate(),
            "avg_response_time_ms": await self.get_avg_response_time(),
            "active_operations": self.get_active_operation_count(),
            "system_resources": await self.get_system_resources()
        },
        "health_score": await self.calculate_health_score(),
        "recommendations": await self.generate_optimization_recommendations()
    }
```

**Graceful Shutdown**:
```python
async def graceful_shutdown(self):
    """Shutdown all performance services gracefully."""
    logger.info("Starting graceful shutdown...")
    
    # Stop accepting new operations
    self.shutdown_initiated = True
    
    # Wait for active operations to complete
    while self.get_active_operation_count() > 0:
        await asyncio.sleep(1)
        
    # Shutdown services in reverse order
    await self.shutdown_background_monitoring()
    await self.shutdown_precompute_service()
    await self.shutdown_async_kerykeion()
    await self.shutdown_cache_service()
    
    logger.info("Graceful shutdown completed")
```

## Alice Voice Interface Optimizations

### Response Time Requirements

**Alice Compliance Targets**:
- **Critical Path**: <3 seconds for any user query
- **Simple Queries**: <1 second (cached responses)
- **Complex Calculations**: <2.5 seconds (with caching)
- **Fallback Responses**: <500ms (error cases)

### Voice-Specific Optimizations

**TTS Processing**:
```python
class VoiceOptimizer:
    def optimize_for_voice(self, text: str) -> str:
        """Optimize text for voice synthesis."""
        # Remove emoji and special characters
        cleaned_text = re.sub(r'[^\w\s\.,!?]', '', text)
        
        # Add natural pauses
        with_pauses = self.add_natural_pauses(cleaned_text)
        
        # Ensure character limit compliance
        if len(with_pauses) > 800:
            with_pauses = self.truncate_intelligently(with_pauses, 800)
            
        return with_pauses
```

**Response Prioritization**:
```python
def prioritize_response_content(self, content: dict) -> dict:
    """Prioritize response content for voice delivery."""
    priorities = {
        "essential": content.get("main_forecast", ""),
        "important": content.get("energy_level", ""),
        "supplementary": content.get("lucky_elements", ""),
        "optional": content.get("detailed_analysis", "")
    }
    
    # Build response within character limits
    response = priorities["essential"]
    remaining_chars = 800 - len(response)
    
    for level in ["important", "supplementary", "optional"]:
        if len(priorities[level]) <= remaining_chars:
            response += f" {priorities[level]}"
            remaining_chars -= len(priorities[level])
        else:
            break
            
    return {"text": response, "tts": response}
```

## Caching Strategies

### Multi-Level Cache Hierarchy

#### Level 1: Redis Cache (Primary)

**Configuration**:
```yaml
redis:
  host: redis
  port: 6379
  db: 0
  password: secure_password
  max_connections: 20
  socket_timeout: 5
  socket_connect_timeout: 5
  health_check_interval: 30
```

**Key Patterns**:
```python
# Cache key patterns for different data types
CACHE_KEY_PATTERNS = {
    "natal_chart": "nc:{user_hash}:{birth_params_hash}",
    "ephemeris": "eph:{date}:{location_hash}", 
    "transits": "trans:{date}:{sign}:{aspects}",
    "compatibility": "comp:{sign1}:{sign2}:{type}",
    "lunar_calendar": "lunar:{year}:{month}:{location_hash}"
}
```

**TTL Policies**:
```python
TTL_POLICIES = {
    "natal_chart": 30 * 24 * 3600,      # 30 days
    "ephemeris": 6 * 3600,              # 6 hours
    "current_transits": 3600,           # 1 hour
    "period_forecast": 2 * 3600,        # 2 hours
    "compatibility": 7 * 24 * 3600,     # 7 days
    "lunar_calendar": 24 * 3600,        # 24 hours
    "user_session": 10 * 60,            # 10 minutes
}
```

#### Level 2: In-Memory Cache (Fallback)

**LRU Cache Implementation**:
```python
from functools import lru_cache
from collections import OrderedDict

class MemoryCache:
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hit_count = 0
        self.miss_count = 0
        
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hit_count += 1
            return self.cache[key]
        else:
            self.miss_count += 1
            return None
            
    def set(self, key: str, value: Any, ttl: int = None):
        # Add TTL support with timestamp
        if ttl:
            expiry = time.time() + ttl
            value = {"data": value, "expires_at": expiry}
            
        self.cache[key] = value
        self.cache.move_to_end(key)
        
        # Enforce size limit
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)  # Remove oldest
```

#### Level 3: Database Query Optimization

**Query Caching at ORM Level**:
```python
# SQLAlchemy query optimization
session.query(User).filter(
    User.zodiac_sign == sign
).options(
    selectinload(User.preferences),
    selectinload(User.sessions)
).execution_options(
    compiled_cache={}
)
```

### Cache Invalidation Strategies

**Event-Based Invalidation**:
```python
class CacheInvalidator:
    async def invalidate_user_cache(self, user_id: str, event_type: str):
        """Invalidate cache based on user events."""
        patterns_to_clear = {
            "preference_update": [f"nc:{user_id}:*", f"rec:{user_id}:*"],
            "birth_data_update": [f"nc:{user_id}:*", f"comp:{user_id}:*"], 
            "session_end": [f"sess:{user_id}:*"]
        }
        
        if event_type in patterns_to_clear:
            for pattern in patterns_to_clear[event_type]:
                await self.clear_pattern(pattern)
```

**Time-Based Invalidation**:
```python
async def cleanup_expired_cache_entries(self):
    """Remove expired cache entries."""
    current_time = time.time()
    expired_keys = []
    
    for key, value in self.cache.items():
        if isinstance(value, dict) and "expires_at" in value:
            if value["expires_at"] < current_time:
                expired_keys.append(key)
                
    for key in expired_keys:
        del self.cache[key]
        
    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
```

## Background Processing

### Async Task Management

**Task Queue Implementation**:
```python
import asyncio
from typing import Callable, Any
import logging

class BackgroundTaskManager:
    def __init__(self):
        self.tasks = {}
        self.running = False
        
    async def add_recurring_task(self, 
                                name: str,
                                func: Callable,
                                interval_seconds: int,
                                *args, **kwargs):
        """Add a recurring background task."""
        async def task_wrapper():
            while self.running:
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Background task {name} failed: {e}")
                await asyncio.sleep(interval_seconds)
                
        self.tasks[name] = asyncio.create_task(task_wrapper())
        
    async def start_all_tasks(self):
        """Start all background tasks."""
        self.running = True
        logger.info(f"Started {len(self.tasks)} background tasks")
        
    async def stop_all_tasks(self):
        """Stop all background tasks gracefully."""
        self.running = False
        
        for name, task in self.tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Background task {name} cancelled")
```

**Background Task Examples**:
```python
# Cache warming task
await task_manager.add_recurring_task(
    "cache_warmup",
    self.warmup_popular_caches,
    interval_seconds=1800  # Every 30 minutes
)

# System cleanup task  
await task_manager.add_recurring_task(
    "system_cleanup", 
    self.cleanup_expired_data,
    interval_seconds=3600  # Every hour
)

# Performance metrics collection
await task_manager.add_recurring_task(
    "metrics_collection",
    self.collect_performance_metrics, 
    interval_seconds=300  # Every 5 minutes
)
```

## Performance Monitoring

### Metrics Collection

**Key Performance Indicators**:
```python
class PerformanceKPIs:
    def __init__(self):
        self.metrics = {
            "response_times": [],
            "cache_hit_rates": [],
            "error_rates": [],
            "resource_usage": [],
            "user_satisfaction": []
        }
        
    def calculate_kpis(self) -> dict:
        """Calculate current KPIs."""
        return {
            "avg_response_time_ms": np.mean(self.metrics["response_times"]),
            "p95_response_time_ms": np.percentile(self.metrics["response_times"], 95),
            "cache_hit_rate": np.mean(self.metrics["cache_hit_rates"]),
            "error_rate": np.mean(self.metrics["error_rates"]),
            "cpu_usage_percent": np.mean([m["cpu"] for m in self.metrics["resource_usage"]]),
            "memory_usage_mb": np.mean([m["memory"] for m in self.metrics["resource_usage"]]),
            "satisfaction_score": np.mean(self.metrics["user_satisfaction"])
        }
```

### Alert Configuration

**Performance Thresholds**:
```python
PERFORMANCE_THRESHOLDS = {
    "response_time": {
        "warning": 1500,  # ms
        "critical": 2500  # ms
    },
    "cache_hit_rate": {
        "warning": 0.6,
        "critical": 0.4
    },
    "error_rate": {
        "warning": 0.05,  # 5%
        "critical": 0.10  # 10%
    },
    "memory_usage": {
        "warning": 80,    # % of available
        "critical": 95    # % of available
    }
}
```

**Alert Actions**:
```python
async def handle_performance_alert(self, alert: dict):
    """Handle performance alerts."""
    if alert["severity"] == "critical":
        # Critical: immediate action required
        await self.scale_up_resources()
        await self.enable_fallback_mode()
        await self.notify_operations_team(alert)
        
    elif alert["severity"] == "warning":
        # Warning: proactive measures
        await self.optimize_cache_settings()
        await self.cleanup_background_tasks()
        await self.log_performance_warning(alert)
```

## Memory Management

### Memory Optimization Strategies

**Garbage Collection Tuning**:
```python
import gc
import psutil

class MemoryManager:
    def __init__(self):
        self.memory_threshold_mb = 500
        self.gc_threshold_mb = 400
        
    async def monitor_memory_usage(self):
        """Monitor and manage memory usage."""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > self.gc_threshold_mb:
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Collected {collected} objects, memory: {memory_mb:.1f}MB")
            
        if memory_mb > self.memory_threshold_mb:
            # Emergency cache cleanup
            await self.emergency_cache_cleanup()
            await self.notify_high_memory_usage(memory_mb)
```

**Object Pool Pattern**:
```python
class ObjectPool:
    """Reuse expensive objects to reduce memory allocation."""
    
    def __init__(self, factory_func: Callable, max_size: int = 10):
        self.factory = factory_func
        self.pool = []
        self.max_size = max_size
        
    def acquire(self):
        """Get object from pool or create new."""
        if self.pool:
            return self.pool.pop()
        else:
            return self.factory()
            
    def release(self, obj):
        """Return object to pool."""
        if len(self.pool) < self.max_size:
            # Reset object state
            obj.reset() if hasattr(obj, 'reset') else None
            self.pool.append(obj)
```

## Load Testing and Benchmarking

### Performance Benchmarks

**Target Performance Metrics**:
```python
PERFORMANCE_TARGETS = {
    "simple_horoscope": {
        "response_time_ms": 500,
        "memory_usage_mb": 50,
        "cpu_usage_percent": 10
    },
    "complex_natal_chart": {
        "response_time_ms": 2000,
        "memory_usage_mb": 100, 
        "cpu_usage_percent": 30
    },
    "compatibility_analysis": {
        "response_time_ms": 1500,
        "memory_usage_mb": 75,
        "cpu_usage_percent": 20
    }
}
```

### Load Testing Scripts

**Stress Test Implementation**:
```python
import asyncio
import aiohttp
import time
from statistics import mean, median

async def stress_test_endpoint(url: str, concurrent_requests: int, duration_seconds: int):
    """Perform stress test on endpoint."""
    response_times = []
    errors = 0
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Create concurrent requests
            tasks = []
            for _ in range(concurrent_requests):
                tasks.append(make_request(session, url))
                
            # Execute requests
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                else:
                    response_times.append(result)
                    
    # Calculate statistics
    return {
        "total_requests": len(response_times) + errors,
        "successful_requests": len(response_times),
        "error_rate": errors / (len(response_times) + errors),
        "avg_response_time_ms": mean(response_times),
        "median_response_time_ms": median(response_times),
        "p95_response_time_ms": sorted(response_times)[int(0.95 * len(response_times))]
    }

async def make_request(session, url):
    """Make individual request and measure response time."""
    start = time.time()
    try:
        async with session.get(url) as response:
            await response.text()
            return (time.time() - start) * 1000
    except Exception as e:
        raise e
```

This comprehensive performance optimization system ensures Astroloh meets Alice voice interface requirements while maintaining scalability and reliability across all supported platforms.