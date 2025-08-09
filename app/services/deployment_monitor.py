"""
Production deployment monitoring service.
Tracks deployment health, performance metrics, and user satisfaction.
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from loguru import logger

from app.services.astro_cache_service import astro_cache
from app.services.feature_flag_service import feature_flags, KerykeionFeatureFlags
from app.services.performance_monitor import performance_monitor


class HealthStatus(Enum):
    """System health status levels."""
    
    EXCELLENT = "excellent"
    GOOD = "good" 
    WARNING = "warning"
    CRITICAL = "critical"
    FAILURE = "failure"


class AlertLevel(Enum):
    """Alert severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class DeploymentMetric:
    """Single deployment metric measurement."""
    
    timestamp: datetime
    feature_name: str
    metric_type: str  # response_time, error_rate, user_satisfaction, etc.
    value: float
    user_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """System health check result."""
    
    check_name: str
    status: HealthStatus
    value: float
    threshold: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class DeploymentMonitor:
    """Monitor production deployment health and metrics."""
    
    def __init__(self):
        self.metrics_history: List[DeploymentMetric] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_thresholds = {
            "response_time_ms": 3000,      # Alice voice interface limit
            "error_rate_percent": 5.0,     # Maximum error rate
            "kerykeion_fallback_rate": 20.0,  # Fallback usage threshold  
            "user_satisfaction_min": 7.0,  # Minimum satisfaction score (1-10)
            "memory_usage_mb": 800,        # Memory usage threshold
            "cpu_usage_percent": 85,       # CPU usage threshold
            "cache_hit_rate_min": 60.0,    # Minimum cache efficiency
        }
        
        self.monitoring_active = True
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info("DEPLOYMENT_MONITOR_INIT: Deployment monitor initialized")
    
    async def start_monitoring(self):
        """Start background deployment monitoring."""
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            logger.info("DEPLOYMENT_MONITOR_START: Background monitoring started")
    
    async def stop_monitoring(self):
        """Stop background deployment monitoring."""
        self.monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            logger.info("DEPLOYMENT_MONITOR_STOP: Background monitoring stopped")
    
    async def record_metric(
        self,
        feature_name: str,
        metric_type: str,
        value: float,
        user_id: Optional[str] = None,
        **additional_data
    ):
        """Record a deployment metric."""
        metric = DeploymentMetric(
            timestamp=datetime.now(),
            feature_name=feature_name,
            metric_type=metric_type,
            value=value,
            user_id=user_id,
            additional_data=additional_data
        )
        
        self.metrics_history.append(metric)
        
        # Keep only last 10000 metrics to prevent memory issues
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-5000:]
        
        logger.debug(f"DEPLOYMENT_METRIC_RECORDED: {feature_name}.{metric_type} = {value}")
        
        # Update feature flag metrics
        await feature_flags.update_feature_metrics(feature_name, {
            f"last_{metric_type}": value,
            f"last_{metric_type}_timestamp": datetime.now().isoformat(),
        })
    
    async def record_kerykeion_usage(self, service_name: str, success: bool, response_time_ms: float, fallback_used: bool = False):
        """Record Kerykeion service usage metrics."""
        feature_name = self._map_service_to_feature(service_name)
        
        # Record response time
        await self.record_metric(feature_name, "response_time", response_time_ms)
        
        # Record success/failure
        await self.record_metric(feature_name, "success_rate", 1.0 if success else 0.0)
        
        # Record fallback usage
        if fallback_used:
            await self.record_metric(feature_name, "fallback_usage", 1.0)
        
        logger.debug(f"DEPLOYMENT_KERYKEION_USAGE: {service_name} success={success} time={response_time_ms}ms fallback={fallback_used}")
    
    def _map_service_to_feature(self, service_name: str) -> str:
        """Map service name to feature flag name."""
        service_mapping = {
            "natal_chart": KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS,
            "synastry": KerykeionFeatureFlags.KERYKEION_SYNASTRY,
            "transit": KerykeionFeatureFlags.KERYKEION_TRANSITS,
            "progression": KerykeionFeatureFlags.KERYKEION_PROGRESSIONS,
            "compatibility": KerykeionFeatureFlags.ENHANCED_COMPATIBILITY,
            "ai_consultation": KerykeionFeatureFlags.AI_CONSULTATION,
        }
        return service_mapping.get(service_name, service_name)
    
    async def record_user_satisfaction(self, user_id: str, rating: float, feedback: Optional[str] = None):
        """Record user satisfaction rating (1-10 scale)."""
        await self.record_metric(
            "user_experience", 
            "satisfaction_rating", 
            rating,
            user_id=user_id,
            feedback=feedback
        )
        
        logger.info(f"DEPLOYMENT_USER_SATISFACTION: {user_id} rated {rating}/10")
    
    async def perform_health_checks(self) -> Dict[str, HealthCheck]:
        """Perform comprehensive system health checks."""
        health_checks = {}
        
        try:
            # 1. Response Time Health Check
            response_times = [
                m.value for m in self.metrics_history[-100:]  # Last 100 metrics
                if m.metric_type == "response_time" and m.timestamp > datetime.now() - timedelta(minutes=5)
            ]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                threshold = self.alert_thresholds["response_time_ms"]
                
                if avg_response_time <= threshold * 0.5:
                    status = HealthStatus.EXCELLENT
                elif avg_response_time <= threshold * 0.8:
                    status = HealthStatus.GOOD
                elif avg_response_time <= threshold:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                health_checks["response_time"] = HealthCheck(
                    check_name="Average Response Time",
                    status=status,
                    value=avg_response_time,
                    threshold=threshold,
                    message=f"Average response time: {avg_response_time:.1f}ms (threshold: {threshold}ms)"
                )
            
            # 2. Error Rate Health Check
            recent_operations = [
                m for m in self.metrics_history[-200:]
                if m.metric_type == "success_rate" and m.timestamp > datetime.now() - timedelta(minutes=10)
            ]
            
            if recent_operations:
                error_rate = (1.0 - sum(m.value for m in recent_operations) / len(recent_operations)) * 100
                threshold = self.alert_thresholds["error_rate_percent"]
                
                if error_rate <= 1.0:
                    status = HealthStatus.EXCELLENT
                elif error_rate <= threshold * 0.5:
                    status = HealthStatus.GOOD
                elif error_rate <= threshold:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                health_checks["error_rate"] = HealthCheck(
                    check_name="System Error Rate",
                    status=status,
                    value=error_rate,
                    threshold=threshold,
                    message=f"Error rate: {error_rate:.1f}% (threshold: {threshold}%)"
                )
            
            # 3. Kerykeion Fallback Rate
            fallback_metrics = [
                m for m in self.metrics_history[-100:]
                if m.metric_type == "fallback_usage" and m.timestamp > datetime.now() - timedelta(minutes=15)
            ]
            
            if fallback_metrics:
                fallback_rate = (len(fallback_metrics) / 100) * 100  # Percentage of last 100 operations
                threshold = self.alert_thresholds["kerykeion_fallback_rate"]
                
                if fallback_rate <= 5.0:
                    status = HealthStatus.EXCELLENT
                elif fallback_rate <= 10.0:
                    status = HealthStatus.GOOD
                elif fallback_rate <= threshold:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                health_checks["kerykeion_fallback"] = HealthCheck(
                    check_name="Kerykeion Fallback Rate",
                    status=status,
                    value=fallback_rate,
                    threshold=threshold,
                    message=f"Fallback rate: {fallback_rate:.1f}% (threshold: {threshold}%)"
                )
            
            # 4. User Satisfaction Check
            satisfaction_ratings = [
                m.value for m in self.metrics_history[-50:]
                if m.metric_type == "satisfaction_rating" and m.timestamp > datetime.now() - timedelta(hours=1)
            ]
            
            if satisfaction_ratings:
                avg_satisfaction = sum(satisfaction_ratings) / len(satisfaction_ratings)
                threshold = self.alert_thresholds["user_satisfaction_min"]
                
                if avg_satisfaction >= 9.0:
                    status = HealthStatus.EXCELLENT
                elif avg_satisfaction >= 8.0:
                    status = HealthStatus.GOOD
                elif avg_satisfaction >= threshold:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                health_checks["user_satisfaction"] = HealthCheck(
                    check_name="User Satisfaction",
                    status=status,
                    value=avg_satisfaction,
                    threshold=threshold,
                    message=f"Average satisfaction: {avg_satisfaction:.1f}/10 (threshold: {threshold}/10)"
                )
            
            # 5. Performance Monitor Integration
            perf_stats = performance_monitor.get_overall_statistics()
            summary = perf_stats.get("summary", {})
            
            if summary:
                overall_error_rate = summary.get("overall_error_rate_percent", 0)
                
                if overall_error_rate <= 1.0:
                    status = HealthStatus.EXCELLENT
                elif overall_error_rate <= 3.0:
                    status = HealthStatus.GOOD
                elif overall_error_rate <= 5.0:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                health_checks["system_performance"] = HealthCheck(
                    check_name="Overall System Performance",
                    status=status,
                    value=overall_error_rate,
                    threshold=5.0,
                    message=f"System error rate: {overall_error_rate:.1f}% from {summary.get('total_operations', 0)} operations"
                )
            
            # 6. Feature Flag Health
            all_features = feature_flags.get_all_features_status()
            enabled_features = sum(1 for f in all_features["features"].values() if f["enabled"])
            total_features = len(all_features["features"])
            
            if total_features > 0:
                enabled_rate = (enabled_features / total_features) * 100
                
                if enabled_rate >= 90.0:
                    status = HealthStatus.EXCELLENT
                elif enabled_rate >= 70.0:
                    status = HealthStatus.GOOD
                elif enabled_rate >= 50.0:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                health_checks["feature_flags"] = HealthCheck(
                    check_name="Feature Flag Health",
                    status=status,
                    value=enabled_rate,
                    threshold=50.0,
                    message=f"{enabled_features}/{total_features} features enabled ({enabled_rate:.1f}%)"
                )
            
            self.health_checks.update(health_checks)
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_HEALTH_CHECK_ERROR: {e}")
            health_checks["system_error"] = HealthCheck(
                check_name="System Error Check",
                status=HealthStatus.FAILURE,
                value=1.0,
                threshold=0.0,
                message=f"Health check failed: {str(e)}"
            )
        
        return health_checks
    
    async def check_auto_rollback_conditions(self) -> Tuple[bool, List[str]]:
        """Check if automatic rollback conditions are met."""
        rollback_triggers = []
        should_rollback = False
        
        try:
            health_checks = await self.perform_health_checks()
            
            # Critical conditions that trigger rollback
            critical_checks = [
                health_checks.get("error_rate"),
                health_checks.get("response_time"),
                health_checks.get("kerykeion_fallback"),
            ]
            
            for check in critical_checks:
                if check and check.status == HealthStatus.CRITICAL:
                    rollback_triggers.append(f"{check.check_name}: {check.message}")
                    should_rollback = True
            
            # Emergency conditions
            if health_checks.get("system_error") and health_checks["system_error"].status == HealthStatus.FAILURE:
                rollback_triggers.append("System failure detected")
                should_rollback = True
            
            # Multiple warnings also trigger rollback
            warning_count = sum(1 for check in health_checks.values() if check.status == HealthStatus.WARNING)
            if warning_count >= 3:
                rollback_triggers.append(f"Multiple system warnings detected ({warning_count})")
                should_rollback = True
            
            if should_rollback:
                logger.warning(f"DEPLOYMENT_ROLLBACK_CONDITIONS_MET: {len(rollback_triggers)} triggers")
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_ROLLBACK_CHECK_ERROR: {e}")
            rollback_triggers.append(f"Rollback check failed: {str(e)}")
            should_rollback = True
        
        return should_rollback, rollback_triggers
    
    async def execute_automatic_rollback(self, triggers: List[str]) -> Dict[str, Any]:
        """Execute automatic rollback of all features."""
        logger.critical(f"DEPLOYMENT_AUTO_ROLLBACK_EXECUTING: Triggers: {triggers}")
        
        rollback_result = {
            "timestamp": datetime.now().isoformat(),
            "triggers": triggers,
            "rolled_back_features": [],
            "errors": [],
            "success": False,
        }
        
        try:
            # Emergency rollback all features
            rolled_back_features = feature_flags.emergency_rollback_all()
            rollback_result["rolled_back_features"] = rolled_back_features
            
            # Record rollback metric
            await self.record_metric("system", "auto_rollback", 1.0, triggers=triggers)
            
            # Save rollback event to cache
            await astro_cache.set(
                f"rollback_event_{int(datetime.now().timestamp())}", 
                rollback_result, 
                ttl=86400 * 7  # Keep for 7 days
            )
            
            rollback_result["success"] = True
            logger.critical(f"DEPLOYMENT_AUTO_ROLLBACK_SUCCESS: {len(rolled_back_features)} features rolled back")
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_AUTO_ROLLBACK_ERROR: {e}")
            rollback_result["errors"].append(str(e))
        
        return rollback_result
    
    async def get_deployment_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive deployment status dashboard."""
        try:
            # Perform health checks
            health_checks = await self.perform_health_checks()
            
            # Get feature status
            feature_status = feature_flags.get_all_features_status()
            
            # Calculate overall health score
            health_scores = []
            for check in health_checks.values():
                if check.status == HealthStatus.EXCELLENT:
                    health_scores.append(100)
                elif check.status == HealthStatus.GOOD:
                    health_scores.append(80)
                elif check.status == HealthStatus.WARNING:
                    health_scores.append(60)
                elif check.status == HealthStatus.CRITICAL:
                    health_scores.append(30)
                else:  # FAILURE
                    health_scores.append(0)
            
            overall_health_score = sum(health_scores) / len(health_scores) if health_scores else 0
            
            # Determine overall status
            if overall_health_score >= 90:
                overall_status = HealthStatus.EXCELLENT
            elif overall_health_score >= 75:
                overall_status = HealthStatus.GOOD
            elif overall_health_score >= 60:
                overall_status = HealthStatus.WARNING
            elif overall_health_score >= 30:
                overall_status = HealthStatus.CRITICAL
            else:
                overall_status = HealthStatus.FAILURE
            
            # Recent metrics summary
            recent_metrics = [
                m for m in self.metrics_history
                if m.timestamp > datetime.now() - timedelta(hours=1)
            ]
            
            # Performance summary from performance monitor
            perf_stats = performance_monitor.get_overall_statistics()
            
            dashboard = {
                "timestamp": datetime.now().isoformat(),
                "overall_health": {
                    "status": overall_status.value,
                    "score": round(overall_health_score, 1),
                    "message": f"System health at {overall_health_score:.1f}%"
                },
                "health_checks": {
                    name: {
                        "status": check.status.value,
                        "value": check.value,
                        "threshold": check.threshold,
                        "message": check.message,
                        "timestamp": check.timestamp.isoformat(),
                    }
                    for name, check in health_checks.items()
                },
                "feature_rollout": feature_status,
                "recent_activity": {
                    "total_metrics": len(recent_metrics),
                    "unique_features": len(set(m.feature_name for m in recent_metrics)),
                    "unique_users": len(set(m.user_id for m in recent_metrics if m.user_id)),
                },
                "performance": perf_stats.get("summary", {}),
                "alert_thresholds": self.alert_thresholds,
                "monitoring_active": self.monitoring_active,
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_DASHBOARD_ERROR: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "overall_health": {"status": "failure", "message": "Dashboard generation failed"}
            }
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # Check for auto-rollback conditions every 2 minutes
                should_rollback, triggers = await self.check_auto_rollback_conditions()
                
                if should_rollback:
                    await self.execute_automatic_rollback(triggers)
                    
                    # Stop monitoring after rollback to prevent loops
                    logger.critical("DEPLOYMENT_MONITOR_STOPPING: Auto-rollback executed, stopping monitoring")
                    self.monitoring_active = False
                    break
                
                # Update health checks every monitoring cycle
                await self.perform_health_checks()
                
                # Sleep for 2 minutes between checks
                await asyncio.sleep(120)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"DEPLOYMENT_MONITORING_LOOP_ERROR: {e}")
                await asyncio.sleep(300)  # 5 minute delay on error
    
    def generate_deployment_report(self, hours: int = 24) -> str:
        """Generate human-readable deployment report."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
            
            # Calculate key statistics
            total_operations = len(recent_metrics)
            unique_features = len(set(m.feature_name for m in recent_metrics))
            unique_users = len(set(m.user_id for m in recent_metrics if m.user_id))
            
            # Response time statistics
            response_times = [m.value for m in recent_metrics if m.metric_type == "response_time"]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Error rate statistics
            success_metrics = [m.value for m in recent_metrics if m.metric_type == "success_rate"]
            success_rate = (sum(success_metrics) / len(success_metrics)) * 100 if success_metrics else 0
            
            # Feature status
            feature_status = feature_flags.get_all_features_status()
            
            report = f"""
🚀 ASTROLOH DEPLOYMENT REPORT (Last {hours} hours)
{'='*60}

📊 OVERVIEW:
• Total Operations: {total_operations:,}
• Features Monitored: {unique_features}
• Active Users: {unique_users}
• Success Rate: {success_rate:.1f}%
• Avg Response Time: {avg_response_time:.1f}ms

🎛️ FEATURE ROLLOUT STATUS:
"""
            
            for feature_name, feature_info in feature_status["features"].items():
                phase = feature_info["rollout_phase"]
                percentage = feature_info["rollout_percentage"]
                enabled = "✅" if feature_info["enabled"] else "❌"
                
                report += f"• {enabled} {feature_name}: {phase} ({percentage}%)\n"
            
            # Health status
            report += f"""

🔍 HEALTH CHECKS:
"""
            for check_name, check in self.health_checks.items():
                status_emoji = {
                    HealthStatus.EXCELLENT: "🟢",
                    HealthStatus.GOOD: "🟡", 
                    HealthStatus.WARNING: "🟠",
                    HealthStatus.CRITICAL: "🔴",
                    HealthStatus.FAILURE: "💀"
                }.get(check.status, "❓")
                
                report += f"• {status_emoji} {check.check_name}: {check.message}\n"
            
            report += f"""

⚠️ ALERT THRESHOLDS:
• Response Time: <{self.alert_thresholds['response_time_ms']}ms
• Error Rate: <{self.alert_thresholds['error_rate_percent']}%
• Fallback Rate: <{self.alert_thresholds['kerykeion_fallback_rate']}%
• User Satisfaction: >{self.alert_thresholds['user_satisfaction_min']}/10

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return report
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_REPORT_ERROR: {e}")
            return f"Error generating deployment report: {str(e)}"


# Global deployment monitor instance
deployment_monitor = DeploymentMonitor()