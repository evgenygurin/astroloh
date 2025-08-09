"""
Performance monitoring service for astrological calculations.
Tracks response times, memory usage, and system metrics.
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

import psutil
from loguru import logger


@dataclass
class PerformanceMetric:
    """Individual performance metric data."""

    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    cache_hit: bool = False
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0


@dataclass
class ServiceStats:
    """Statistics for a specific service."""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    cache_hits: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    avg_duration: float = 0.0
    recent_operations: Deque[PerformanceMetric] = field(
        default_factory=lambda: deque(maxlen=100)
    )
    error_counts: Dict[str, int] = field(default_factory=dict)


class PerformanceMonitor:
    """Comprehensive performance monitoring for astrological services."""

    def __init__(self, max_metrics_history: int = 1000):
        self.max_metrics_history = max_metrics_history
        self.service_stats: Dict[str, ServiceStats] = defaultdict(ServiceStats)
        self.system_metrics: Deque[Dict[str, Any]] = deque(maxlen=100)
        self.alert_thresholds = {
            "slow_operation_ms": 2000,  # Operations slower than 2 seconds
            "high_memory_mb": 1000,  # Memory usage above 1000MB (1GB)
            "high_cpu_percent": 80,  # CPU usage above 80%
            "error_rate_percent": 10,  # Error rate above 10%
        }
        self.monitoring_active = True
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info(
            "PERFORMANCE_MONITOR_INIT: Performance monitoring initialized"
        )

    async def start_monitoring(self):
        """Start background monitoring tasks."""
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(
                self._system_monitor_loop()
            )
            logger.info(
                "PERFORMANCE_MONITOR_START: Background monitoring started"
            )

    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        self.monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            logger.info(
                "PERFORMANCE_MONITOR_STOP: Background monitoring stopped"
            )

    def start_operation(self, service_name: str, operation_name: str) -> str:
        """Start timing an operation and return a unique operation ID."""
        operation_id = (
            f"{service_name}_{operation_name}_{int(time.time() * 1000000)}"
        )

        # Store operation start time
        if not hasattr(self, "_active_operations"):
            self._active_operations = {}

        self._active_operations[operation_id] = {
            "service": service_name,
            "operation": operation_name,
            "start_time": time.time(),
            "start_memory": self._get_memory_usage(),
            "start_cpu": self._get_cpu_usage(),
        }

        logger.debug(f"PERFORMANCE_MONITOR_START_OP: {operation_id}")
        return operation_id

    def end_operation(
        self,
        operation_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        cache_hit: bool = False,
        additional_metrics: Optional[Dict[str, Any]] = None,
    ):
        """End timing an operation and record the metric."""
        if not hasattr(self, "_active_operations"):
            logger.warning(
                f"PERFORMANCE_MONITOR_NO_ACTIVE_OPS: {operation_id}"
            )
            return

        if operation_id not in self._active_operations:
            logger.warning(f"PERFORMANCE_MONITOR_UNKNOWN_OP: {operation_id}")
            return

        start_data = self._active_operations.pop(operation_id)
        end_time = time.time()
        duration = end_time - start_data["start_time"]

        # Calculate resource usage
        end_memory = self._get_memory_usage()
        end_cpu = self._get_cpu_usage()
        memory_delta = end_memory - start_data["start_memory"]
        cpu_avg = (start_data["start_cpu"] + end_cpu) / 2

        # Create performance metric
        metric = PerformanceMetric(
            operation=start_data["operation"],
            start_time=start_data["start_time"],
            end_time=end_time,
            duration=duration,
            success=success,
            error_message=error_message,
            cache_hit=cache_hit,
            memory_usage_mb=memory_delta,
            cpu_percent=cpu_avg,
        )

        # Update service statistics
        service_name = start_data["service"]
        stats = self.service_stats[service_name]

        stats.total_operations += 1
        stats.recent_operations.append(metric)

        if success:
            stats.successful_operations += 1
        else:
            stats.failed_operations += 1
            if error_message:
                stats.error_counts[error_message] = (
                    stats.error_counts.get(error_message, 0) + 1
                )

        if cache_hit:
            stats.cache_hits += 1

        # Update duration statistics
        stats.total_duration += duration
        stats.min_duration = min(stats.min_duration, duration)
        stats.max_duration = max(stats.max_duration, duration)
        stats.avg_duration = stats.total_duration / stats.total_operations

        # Check for alerts
        self._check_performance_alerts(service_name, metric)

        logger.debug(
            f"PERFORMANCE_MONITOR_END_OP: {operation_id} in {duration:.3f}s"
        )

    def _check_performance_alerts(
        self, service_name: str, metric: PerformanceMetric
    ):
        """Check if metric exceeds alert thresholds."""
        duration_ms = metric.duration * 1000

        # Slow operation alert
        if duration_ms > self.alert_thresholds["slow_operation_ms"]:
            logger.warning(
                f"PERFORMANCE_ALERT_SLOW: {service_name}.{metric.operation} "
                f"took {duration_ms:.1f}ms (threshold: {self.alert_thresholds['slow_operation_ms']}ms)"
            )

        # High memory usage alert
        if metric.memory_usage_mb > self.alert_thresholds["high_memory_mb"]:
            logger.warning(
                f"PERFORMANCE_ALERT_MEMORY: {service_name}.{metric.operation} "
                f"used {metric.memory_usage_mb:.1f}MB (threshold: {self.alert_thresholds['high_memory_mb']}MB)"
            )

        # High CPU usage alert
        if metric.cpu_percent > self.alert_thresholds["high_cpu_percent"]:
            logger.warning(
                f"PERFORMANCE_ALERT_CPU: {service_name}.{metric.operation} "
                f"used {metric.cpu_percent:.1f}% CPU (threshold: {self.alert_thresholds['high_cpu_percent']}%)"
            )

    def get_service_statistics(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a service."""
        stats = self.service_stats[service_name]

        if stats.total_operations == 0:
            return {
                "service": service_name,
                "status": "No operations recorded",
            }

        # Calculate error rate
        error_rate = (stats.failed_operations / stats.total_operations) * 100
        cache_hit_rate = (stats.cache_hits / stats.total_operations) * 100

        # Calculate percentiles from recent operations
        recent_durations = [op.duration for op in stats.recent_operations]
        percentiles = {}

        if recent_durations:
            sorted_durations = sorted(recent_durations)
            percentiles = {
                "p50": self._percentile(sorted_durations, 50),
                "p95": self._percentile(sorted_durations, 95),
                "p99": self._percentile(sorted_durations, 99),
            }

        # Top errors
        top_errors = sorted(
            stats.error_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "service": service_name,
            "operations": {
                "total": stats.total_operations,
                "successful": stats.successful_operations,
                "failed": stats.failed_operations,
                "error_rate_percent": round(error_rate, 2),
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
            },
            "performance": {
                "avg_duration_ms": round(stats.avg_duration * 1000, 2),
                "min_duration_ms": round(stats.min_duration * 1000, 2),
                "max_duration_ms": round(stats.max_duration * 1000, 2),
                "percentiles_ms": {
                    k: round(v * 1000, 2) for k, v in percentiles.items()
                },
            },
            "top_errors": top_errors,
        }

    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall performance statistics across all services."""
        overall_stats = {
            "monitoring_period": self._get_monitoring_period(),
            "services": {},
            "system_performance": self._get_system_performance_summary(),
            "alerts": {
                "thresholds": self.alert_thresholds,
                "recent_alerts": self._get_recent_alerts(),
            },
        }

        # Aggregate service statistics
        total_operations = 0
        total_successful = 0
        total_failed = 0
        total_cache_hits = 0

        for service_name in self.service_stats:
            service_stats = self.get_service_statistics(service_name)
            overall_stats["services"][service_name] = service_stats

            ops = service_stats.get("operations", {})
            total_operations += ops.get("total", 0)
            total_successful += ops.get("successful", 0)
            total_failed += ops.get("failed", 0)
            total_cache_hits += ops.get("cache_hits", 0)

        # Overall metrics
        overall_error_rate = (
            (total_failed / total_operations * 100)
            if total_operations > 0
            else 0
        )
        overall_cache_rate = (
            (total_cache_hits / total_operations * 100)
            if total_operations > 0
            else 0
        )

        overall_stats["summary"] = {
            "total_operations": total_operations,
            "successful_operations": total_successful,
            "failed_operations": total_failed,
            "overall_error_rate_percent": round(overall_error_rate, 2),
            "overall_cache_hit_rate_percent": round(overall_cache_rate, 2),
            "active_services": len(self.service_stats),
        }

        return overall_stats

    def get_performance_report(self, hours: int = 24) -> str:
        """Generate a human-readable performance report."""
        stats = self.get_overall_statistics()

        report = f"""
🚀 ASTROLOH PERFORMANCE REPORT (Last {hours} hours)
{'='*60}

📊 SUMMARY:
• Total Operations: {stats['summary']['total_operations']:,}
• Success Rate: {100 - stats['summary']['overall_error_rate_percent']:.1f}%
• Cache Hit Rate: {stats['summary']['overall_cache_hit_rate_percent']:.1f}%
• Active Services: {stats['summary']['active_services']}

🔧 SERVICE PERFORMANCE:
"""

        for service_name, service_stats in stats["services"].items():
            if service_stats.get("status") == "No operations recorded":
                continue

            ops = service_stats["operations"]
            perf = service_stats["performance"]

            report += f"""
• {service_name.upper()}:
  - Operations: {ops['total']:,} (Success: {100 - ops['error_rate_percent']:.1f}%)
  - Avg Response: {perf['avg_duration_ms']:.0f}ms
  - P95 Response: {perf.get('percentiles_ms', {}).get('p95', 0):.0f}ms
  - Cache Hit Rate: {ops['cache_hit_rate_percent']:.1f}%
"""

        # System performance
        system = stats["system_performance"]
        report += f"""
🖥️ SYSTEM PERFORMANCE:
• CPU Usage: {system.get('avg_cpu_percent', 0):.1f}%
• Memory Usage: {system.get('avg_memory_mb', 0):.0f}MB
• Peak Memory: {system.get('peak_memory_mb', 0):.0f}MB

⚠️ ALERT THRESHOLDS:
• Slow Operation: >{stats['alerts']['thresholds']['slow_operation_ms']}ms
• High Memory: >{stats['alerts']['thresholds']['high_memory_mb']}MB
• High CPU: >{stats['alerts']['thresholds']['high_cpu_percent']}%
• Error Rate: >{stats['alerts']['thresholds']['error_rate_percent']}%

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    async def _system_monitor_loop(self):
        """Background task to collect system metrics."""
        while self.monitoring_active:
            try:
                system_metric = {
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage_percent": psutil.disk_usage("/").percent,
                    "active_connections": len(psutil.net_connections()),
                }

                self.system_metrics.append(system_metric)

                # Check for system-level alerts
                if (
                    system_metric["cpu_percent"]
                    > self.alert_thresholds["high_cpu_percent"]
                ):
                    logger.warning(
                        f"PERFORMANCE_ALERT_SYSTEM_CPU: {system_metric['cpu_percent']:.1f}%"
                    )

                if (
                    system_metric["memory_mb"]
                    > self.alert_thresholds["high_memory_mb"]
                ):
                    logger.warning(
                        f"PERFORMANCE_ALERT_SYSTEM_MEMORY: {system_metric['memory_mb']:.1f}MB"
                    )

                await asyncio.sleep(
                    30
                )  # Collect system metrics every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"PERFORMANCE_MONITOR_SYSTEM_ERROR: {e}")
                await asyncio.sleep(60)  # Retry after error

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            return psutil.Process().memory_info().rss / 1024 / 1024
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent()
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            return 0.0

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from a list of values."""
        if not data:
            return 0.0

        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = k - f

        if f == len(data) - 1:
            return data[f]

        return data[f] * (1 - c) + data[f + 1] * c

    def _get_monitoring_period(self) -> str:
        """Get the monitoring period description."""
        if not self.system_metrics:
            return "No monitoring data available"

        oldest_timestamp = self.system_metrics[0]["timestamp"]
        newest_timestamp = self.system_metrics[-1]["timestamp"]

        period_hours = (newest_timestamp - oldest_timestamp) / 3600
        return f"{period_hours:.1f} hours"

    def _get_system_performance_summary(self) -> Dict[str, Any]:
        """Get system performance summary from collected metrics."""
        if not self.system_metrics:
            return {"status": "No system metrics available"}

        cpu_values = [m["cpu_percent"] for m in self.system_metrics]
        memory_values = [m["memory_mb"] for m in self.system_metrics]

        return {
            "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
            "peak_cpu_percent": max(cpu_values),
            "avg_memory_mb": sum(memory_values) / len(memory_values),
            "peak_memory_mb": max(memory_values),
            "samples_collected": len(self.system_metrics),
        }

    def _get_recent_alerts(self) -> List[str]:
        """Get recent performance alerts."""
        # This would typically be implemented with a proper alert storage system
        # For now, return placeholder
        return ["System monitoring active"]

    def reset_statistics(self, service_name: Optional[str] = None):
        """Reset statistics for a service or all services."""
        if service_name:
            if service_name in self.service_stats:
                del self.service_stats[service_name]
                logger.info(
                    f"PERFORMANCE_MONITOR_RESET: Statistics reset for {service_name}"
                )
        else:
            self.service_stats.clear()
            self.system_metrics.clear()
            logger.info("PERFORMANCE_MONITOR_RESET: All statistics reset")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
