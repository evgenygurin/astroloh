"""
Deployment management API endpoints.
Provides control interface for production deployment monitoring and rollbacks.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from loguru import logger
from pydantic import BaseModel

from app.services.deployment_monitor import deployment_monitor
from app.services.feature_flag_service import feature_flags, FeatureRolloutPhase, KerykeionFeatureFlags
from app.services.rollback_system import rollback_system, RollbackStrategy
from app.services.startup_manager import startup_manager
from app.services.performance_monitor import performance_monitor


router = APIRouter(prefix="/api/v1/deployment", tags=["deployment"])


class FeatureFlagUpdate(BaseModel):
    """Request model for updating feature flags."""
    
    enabled: Optional[bool] = None
    rollout_phase: Optional[str] = None
    rollout_percentage: Optional[float] = None
    target_users: Optional[List[str]] = None
    excluded_users: Optional[List[str]] = None


class ManualRollbackRequest(BaseModel):
    """Request model for manual rollback."""
    
    features: List[str]
    strategy: str = "immediate"
    reason: str = "Manual intervention"


class DeploymentStatusResponse(BaseModel):
    """Response model for deployment status."""
    
    timestamp: str
    overall_health: Dict[str, Any]
    feature_rollout: Dict[str, Any]
    recent_activity: Dict[str, Any]
    performance: Dict[str, Any]


@router.get("/status", response_model=DeploymentStatusResponse)
async def get_deployment_status():
    """Get comprehensive deployment status dashboard."""
    try:
        logger.info("DEPLOYMENT_API_STATUS: Getting deployment status")
        dashboard = await deployment_monitor.get_deployment_dashboard()
        
        return DeploymentStatusResponse(
            timestamp=dashboard["timestamp"],
            overall_health=dashboard["overall_health"],
            feature_rollout=dashboard["feature_rollout"],
            recent_activity=dashboard["recent_activity"],
            performance=dashboard["performance"]
        )
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_STATUS_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")


@router.get("/features")
async def get_feature_flags():
    """Get all feature flags and their current status."""
    try:
        logger.info("DEPLOYMENT_API_FEATURES: Getting feature flag status")
        return feature_flags.get_all_features_status()
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_FEATURES_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feature flags: {str(e)}")


@router.get("/features/{feature_name}/metrics")
async def get_feature_metrics(feature_name: str):
    """Get detailed metrics for a specific feature."""
    try:
        logger.info(f"DEPLOYMENT_API_FEATURE_METRICS: Getting metrics for {feature_name}")
        metrics = await feature_flags.get_rollout_metrics(feature_name)
        
        if "error" in metrics:
            raise HTTPException(status_code=404, detail=metrics["error"])
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_FEATURE_METRICS_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feature metrics: {str(e)}")


@router.put("/features/{feature_name}")
async def update_feature_flag(feature_name: str, update_data: FeatureFlagUpdate):
    """Update a feature flag configuration."""
    try:
        logger.info(f"DEPLOYMENT_API_UPDATE_FEATURE: Updating {feature_name}")
        
        # Convert rollout phase string to enum if provided
        rollout_phase = None
        if update_data.rollout_phase:
            try:
                rollout_phase = FeatureRolloutPhase(update_data.rollout_phase)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid rollout phase: {update_data.rollout_phase}"
                )
        
        success = feature_flags.update_feature_flag(
            feature_name=feature_name,
            enabled=update_data.enabled,
            rollout_phase=rollout_phase,
            rollout_percentage=update_data.rollout_percentage,
            target_users=set(update_data.target_users) if update_data.target_users else None,
            excluded_users=set(update_data.excluded_users) if update_data.excluded_users else None,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Feature {feature_name} not found")
        
        # Save updated state
        await feature_flags.save_state_to_cache()
        
        return {"success": True, "message": f"Feature {feature_name} updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_UPDATE_FEATURE_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update feature: {str(e)}")


@router.post("/features/{feature_name}/advance-phase")
async def advance_feature_phase(feature_name: str):
    """Advance feature to the next rollout phase."""
    try:
        logger.info(f"DEPLOYMENT_API_ADVANCE_PHASE: Advancing {feature_name}")
        
        success = feature_flags.advance_rollout_phase(feature_name)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot advance phase for {feature_name} (already at max or disabled)"
            )
        
        # Save updated state
        await feature_flags.save_state_to_cache()
        
        # Get updated metrics
        metrics = await feature_flags.get_rollout_metrics(feature_name)
        
        return {
            "success": True,
            "message": f"Feature {feature_name} advanced to next phase",
            "current_phase": metrics.get("rollout_phase"),
            "current_percentage": metrics.get("rollout_percentage")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_ADVANCE_PHASE_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to advance phase: {str(e)}")


@router.post("/features/{feature_name}/emergency-rollback")
async def emergency_feature_rollback(feature_name: str):
    """Immediately disable a feature (emergency rollback)."""
    try:
        logger.warning(f"DEPLOYMENT_API_EMERGENCY_ROLLBACK: Emergency rollback for {feature_name}")
        
        success = feature_flags.emergency_rollback(feature_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Feature {feature_name} not found")
        
        # Save updated state
        await feature_flags.save_state_to_cache()
        
        # Record rollback event
        await deployment_monitor.record_metric(
            feature_name, 
            "emergency_rollback", 
            1.0, 
            reason="API emergency rollback"
        )
        
        return {"success": True, "message": f"Feature {feature_name} emergency rollback completed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_EMERGENCY_ROLLBACK_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute emergency rollback: {str(e)}")


@router.post("/rollback/manual")
async def manual_rollback(rollback_request: ManualRollbackRequest, background_tasks: BackgroundTasks):
    """Execute manual rollback of specified features."""
    try:
        logger.warning(f"DEPLOYMENT_API_MANUAL_ROLLBACK: Manual rollback requested for {len(rollback_request.features)} features")
        
        # Validate rollback strategy
        try:
            strategy = RollbackStrategy(rollback_request.strategy)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid rollback strategy: {rollback_request.strategy}"
            )
        
        # Validate features exist
        for feature in rollback_request.features:
            if feature not in feature_flags.flags:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Feature not found: {feature}"
                )
        
        # Execute rollback in background
        def execute_rollback():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                rollback_event = loop.run_until_complete(
                    rollback_system.manual_rollback(
                        features=rollback_request.features,
                        strategy=strategy,
                        reason=rollback_request.reason
                    )
                )
                logger.info(f"DEPLOYMENT_API_MANUAL_ROLLBACK_COMPLETE: {rollback_event.rollback_id}")
            except Exception as e:
                logger.error(f"DEPLOYMENT_API_MANUAL_ROLLBACK_BG_ERROR: {e}")
            finally:
                loop.close()
        
        background_tasks.add_task(execute_rollback)
        
        return {
            "success": True,
            "message": f"Manual rollback initiated for {len(rollback_request.features)} features",
            "features": rollback_request.features,
            "strategy": rollback_request.strategy,
            "reason": rollback_request.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_MANUAL_ROLLBACK_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate manual rollback: {str(e)}")


@router.get("/rollback/history")
async def get_rollback_history(limit: int = Query(10, ge=1, le=100)):
    """Get recent rollback history."""
    try:
        logger.info(f"DEPLOYMENT_API_ROLLBACK_HISTORY: Getting last {limit} rollbacks")
        return rollback_system.get_rollback_history(limit)
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_ROLLBACK_HISTORY_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rollback history: {str(e)}")


@router.get("/rollback/statistics")
async def get_rollback_statistics():
    """Get rollback system statistics."""
    try:
        logger.info("DEPLOYMENT_API_ROLLBACK_STATS: Getting rollback statistics")
        return await rollback_system.get_rollback_statistics()
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_ROLLBACK_STATS_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rollback statistics: {str(e)}")


@router.get("/health-checks")
async def get_health_checks():
    """Get detailed system health checks."""
    try:
        logger.info("DEPLOYMENT_API_HEALTH_CHECKS: Getting health checks")
        health_checks = await deployment_monitor.perform_health_checks()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_checks": {
                name: {
                    "status": check.status.value,
                    "value": check.value,
                    "threshold": check.threshold,
                    "message": check.message,
                    "timestamp": check.timestamp.isoformat(),
                }
                for name, check in health_checks.items()
            }
        }
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_HEALTH_CHECKS_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health checks: {str(e)}")


@router.get("/performance-report")
async def get_performance_report(hours: int = Query(24, ge=1, le=168)):
    """Get human-readable performance report."""
    try:
        logger.info(f"DEPLOYMENT_API_PERFORMANCE_REPORT: Getting {hours}h report")
        
        # Get performance report from performance monitor
        perf_report = performance_monitor.get_performance_report(hours)
        
        # Get deployment report from deployment monitor
        deploy_report = deployment_monitor.generate_deployment_report(hours)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "hours_covered": hours,
            "performance_report": perf_report,
            "deployment_report": deploy_report,
        }
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_PERFORMANCE_REPORT_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate performance report: {str(e)}")


@router.get("/system-status")
async def get_system_status():
    """Get comprehensive system status including all services."""
    try:
        logger.info("DEPLOYMENT_API_SYSTEM_STATUS: Getting comprehensive system status")
        return await startup_manager.get_system_status()
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_SYSTEM_STATUS_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.post("/monitoring/start")
async def start_deployment_monitoring():
    """Start deployment monitoring services."""
    try:
        logger.info("DEPLOYMENT_API_START_MONITORING: Starting deployment monitoring")
        await deployment_monitor.start_monitoring()
        
        return {"success": True, "message": "Deployment monitoring started"}
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_START_MONITORING_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/monitoring/stop")
async def stop_deployment_monitoring():
    """Stop deployment monitoring services."""
    try:
        logger.info("DEPLOYMENT_API_STOP_MONITORING: Stopping deployment monitoring")
        await deployment_monitor.stop_monitoring()
        
        return {"success": True, "message": "Deployment monitoring stopped"}
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_STOP_MONITORING_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@router.post("/user-feedback")
async def submit_user_feedback(
    user_id: str,
    rating: float = Query(..., ge=1.0, le=10.0),
    feedback: Optional[str] = None
):
    """Submit user satisfaction feedback."""
    try:
        logger.info(f"DEPLOYMENT_API_USER_FEEDBACK: User {user_id} rated {rating}/10")
        
        await deployment_monitor.record_user_satisfaction(
            user_id=user_id,
            rating=rating,
            feedback=feedback
        )
        
        return {
            "success": True,
            "message": "User feedback recorded",
            "user_id": user_id,
            "rating": rating
        }
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_USER_FEEDBACK_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record user feedback: {str(e)}")


@router.get("/features/kerykeion/usage")
async def get_kerykeion_feature_usage():
    """Get usage statistics for all Kerykeion features."""
    try:
        logger.info("DEPLOYMENT_API_KERYKEION_USAGE: Getting Kerykeion feature usage")
        
        kerykeion_features = [
            KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS,
            KerykeionFeatureFlags.KERYKEION_SYNASTRY,
            KerykeionFeatureFlags.KERYKEION_TRANSITS,
            KerykeionFeatureFlags.KERYKEION_PROGRESSIONS,
            KerykeionFeatureFlags.ENHANCED_COMPATIBILITY,
            KerykeionFeatureFlags.AI_CONSULTATION,
        ]
        
        usage_stats = {}
        for feature in kerykeion_features:
            metrics = await feature_flags.get_rollout_metrics(feature)
            usage_stats[feature] = metrics
        
        return {
            "timestamp": datetime.now().isoformat(),
            "kerykeion_features": usage_stats,
            "summary": {
                "total_features": len(kerykeion_features),
                "enabled_features": sum(1 for f in usage_stats.values() if f.get("enabled", False)),
                "total_estimated_users": sum(f.get("estimated_enabled_users", 0) for f in usage_stats.values()),
            }
        }
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_KERYKEION_USAGE_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Kerykeion usage: {str(e)}")


@router.get("/alerts/check")
async def check_deployment_alerts():
    """Check for deployment alerts and conditions."""
    try:
        logger.info("DEPLOYMENT_API_ALERTS_CHECK: Checking for deployment alerts")
        
        # Check if rollback conditions are met
        should_rollback, triggers = await rollback_system.analyze_rollback_need()
        
        # Get current health status
        health_checks = await deployment_monitor.perform_health_checks()
        
        # Identify any critical issues
        critical_issues = [
            {"check": name, "status": check.status.value, "message": check.message}
            for name, check in health_checks.items()
            if check.status.value in ["critical", "failure"]
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "rollback_needed": should_rollback is not None,
            "rollback_triggers": triggers if should_rollback else [],
            "critical_issues": critical_issues,
            "health_summary": {
                "total_checks": len(health_checks),
                "critical_count": len(critical_issues),
                "status": "critical" if critical_issues else "normal"
            }
        }
        
    except Exception as e:
        logger.error(f"DEPLOYMENT_API_ALERTS_CHECK_ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check alerts: {str(e)}")