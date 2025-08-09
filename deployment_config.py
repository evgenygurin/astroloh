"""
Production deployment configuration for Kerykeion rollout.
Configures deployment monitoring, feature flags, and rollback automation.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from loguru import logger

from app.services.deployment_monitor import deployment_monitor
from app.services.feature_flag_service import feature_flags, FeatureRolloutPhase, KerykeionFeatureFlags
from app.services.rollback_system import rollback_system
from app.services.startup_manager import startup_manager
from app.services.performance_monitor import performance_monitor


class ProductionDeploymentConfig:
    """Configuration and orchestration for production Kerykeion deployment."""
    
    def __init__(self):
        self.deployment_id = f"kerykeion_deploy_{int(datetime.now().timestamp())}"
        self.deployment_start_time = datetime.now()
        self.current_phase = "preparation"
        self.phase_progress = {}
        
        # Deployment phases configuration
        self.deployment_phases = {
            "preparation": {
                "description": "System preparation and health checks",
                "duration_minutes": 10,
                "required_health_score": 80,
            },
            "phase_1": {
                "description": "5% user rollout - Basic Kerykeion features",
                "features": [
                    KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS,
                    KerykeionFeatureFlags.KERYKEION_SYNASTRY,
                    KerykeionFeatureFlags.PERFORMANCE_OPTIMIZATION,
                ],
                "target_percentage": 5.0,
                "duration_minutes": 120,  # 2 hours monitoring
                "success_criteria": {
                    "error_rate_max": 3.0,
                    "response_time_max": 2500,
                    "fallback_rate_max": 15.0,
                    "user_satisfaction_min": 8.0,
                },
            },
            "phase_2": {
                "description": "20% user rollout - Extended astrology features", 
                "features": [
                    KerykeionFeatureFlags.KERYKEION_TRANSITS,
                    KerykeionFeatureFlags.KERYKEION_PROGRESSIONS,
                ],
                "target_percentage": 20.0,
                "duration_minutes": 240,  # 4 hours monitoring
                "success_criteria": {
                    "error_rate_max": 4.0,
                    "response_time_max": 3000,
                    "fallback_rate_max": 20.0,
                    "user_satisfaction_min": 7.5,
                },
            },
            "phase_3": {
                "description": "50% user rollout - AI and enhanced features",
                "features": [
                    KerykeionFeatureFlags.ENHANCED_COMPATIBILITY,
                    KerykeionFeatureFlags.AI_CONSULTATION,
                ],
                "target_percentage": 50.0,
                "duration_minutes": 480,  # 8 hours monitoring
                "success_criteria": {
                    "error_rate_max": 5.0,
                    "response_time_max": 3500,
                    "fallback_rate_max": 25.0,
                    "user_satisfaction_min": 7.0,
                },
            },
            "full": {
                "description": "100% user rollout - Full feature deployment",
                "features": [
                    KerykeionFeatureFlags.RUSSIAN_LOCALIZATION,
                ],
                "target_percentage": 100.0,
                "duration_minutes": 720,  # 12 hours monitoring
                "success_criteria": {
                    "error_rate_max": 6.0,
                    "response_time_max": 4000,
                    "fallback_rate_max": 30.0,
                    "user_satisfaction_min": 6.5,
                },
            },
        }
        
        logger.info(f"DEPLOYMENT_CONFIG_INIT: Production deployment {self.deployment_id} configured")
    
    async def initialize_deployment_systems(self) -> Dict[str, Any]:
        """Initialize all deployment and monitoring systems."""
        logger.info(f"DEPLOYMENT_INIT: Initializing deployment systems for {self.deployment_id}")
        
        initialization_results = {
            "deployment_id": self.deployment_id,
            "initialization_time": datetime.now().isoformat(),
            "systems_initialized": [],
            "errors": [],
        }
        
        try:
            # 1. Initialize startup manager with performance optimizations
            logger.info("DEPLOYMENT_INIT_STARTUP: Initializing startup manager")
            startup_result = await startup_manager.initialize_performance_systems(
                enable_cache_warmup=True,
                enable_background_monitoring=True,
                enable_precomputation=True,
                redis_url=os.getenv("REDIS_URL")
            )
            
            if startup_result["success"]:
                initialization_results["systems_initialized"].append("startup_manager")
                logger.info("DEPLOYMENT_INIT_STARTUP_SUCCESS")
            else:
                initialization_results["errors"].extend(startup_result.get("errors", []))
                logger.warning("DEPLOYMENT_INIT_STARTUP_PARTIAL")
            
            # 2. Load feature flag state from cache
            logger.info("DEPLOYMENT_INIT_FEATURES: Loading feature flags")
            feature_loaded = await feature_flags.load_state_from_cache()
            if feature_loaded:
                initialization_results["systems_initialized"].append("feature_flags")
                logger.info("DEPLOYMENT_INIT_FEATURES_SUCCESS")
            else:
                logger.info("DEPLOYMENT_INIT_FEATURES_DEFAULT: Using default feature configuration")
                initialization_results["systems_initialized"].append("feature_flags_default")
            
            # 3. Initialize deployment monitoring
            logger.info("DEPLOYMENT_INIT_MONITOR: Starting deployment monitoring")
            await deployment_monitor.start_monitoring()
            initialization_results["systems_initialized"].append("deployment_monitor")
            
            # 4. Initialize performance monitoring
            logger.info("DEPLOYMENT_INIT_PERFORMANCE: Starting performance monitoring")
            await performance_monitor.start_monitoring()
            initialization_results["systems_initialized"].append("performance_monitor")
            
            # 5. Backup system state before deployment
            logger.info("DEPLOYMENT_INIT_BACKUP: Creating system state backup")
            backup_success = await rollback_system.backup_current_state()
            if backup_success:
                initialization_results["systems_initialized"].append("system_backup")
                logger.info("DEPLOYMENT_INIT_BACKUP_SUCCESS")
            else:
                initialization_results["errors"].append("Failed to create system backup")
                logger.warning("DEPLOYMENT_INIT_BACKUP_FAILED")
            
            # 6. Perform initial health check
            logger.info("DEPLOYMENT_INIT_HEALTH: Performing initial health check")
            health_checks = await deployment_monitor.perform_health_checks()
            
            health_scores = []
            for check in health_checks.values():
                if check.status.value == "excellent":
                    health_scores.append(100)
                elif check.status.value == "good":
                    health_scores.append(80)
                elif check.status.value == "warning":
                    health_scores.append(60)
                elif check.status.value == "critical":
                    health_scores.append(30)
                else:
                    health_scores.append(0)
            
            overall_health_score = sum(health_scores) / len(health_scores) if health_scores else 0
            
            initialization_results["initial_health_score"] = overall_health_score
            initialization_results["health_checks"] = len(health_checks)
            
            if overall_health_score >= 70:
                initialization_results["ready_for_deployment"] = True
                logger.info(f"DEPLOYMENT_INIT_READY: System ready for deployment (health: {overall_health_score:.1f}%)")
            else:
                initialization_results["ready_for_deployment"] = False
                initialization_results["errors"].append(f"System health too low for deployment: {overall_health_score:.1f}%")
                logger.warning(f"DEPLOYMENT_INIT_NOT_READY: System not ready (health: {overall_health_score:.1f}%)")
            
            self.current_phase = "initialized"
            initialization_results["success"] = len(initialization_results["errors"]) == 0
            
            return initialization_results
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_INIT_ERROR: {e}")
            initialization_results["errors"].append(str(e))
            initialization_results["success"] = False
            return initialization_results
    
    async def execute_phased_deployment(self) -> Dict[str, Any]:
        """Execute the complete phased deployment process."""
        logger.info(f"DEPLOYMENT_EXECUTE: Starting phased deployment {self.deployment_id}")
        
        deployment_result = {
            "deployment_id": self.deployment_id,
            "start_time": self.deployment_start_time.isoformat(),
            "phases_completed": [],
            "phases_failed": [],
            "current_phase": None,
            "success": False,
            "error_message": None,
        }
        
        try:
            # Execute each deployment phase
            for phase_name, phase_config in self.deployment_phases.items():
                if phase_name == "preparation":
                    continue  # Skip preparation phase, handled in initialization
                
                logger.info(f"DEPLOYMENT_PHASE_START: Starting {phase_name}")
                deployment_result["current_phase"] = phase_name
                
                phase_result = await self._execute_deployment_phase(phase_name, phase_config)
                
                if phase_result["success"]:
                    deployment_result["phases_completed"].append(phase_name)
                    logger.info(f"DEPLOYMENT_PHASE_SUCCESS: {phase_name} completed successfully")
                else:
                    deployment_result["phases_failed"].append(phase_name)
                    deployment_result["error_message"] = phase_result.get("error_message")
                    logger.error(f"DEPLOYMENT_PHASE_FAILED: {phase_name} failed: {phase_result.get('error_message')}")
                    
                    # Execute rollback on failure
                    await self._handle_deployment_failure(phase_name, phase_result)
                    break
            
            # Check if all phases completed successfully
            expected_phases = [p for p in self.deployment_phases.keys() if p != "preparation"]
            deployment_result["success"] = len(deployment_result["phases_completed"]) == len(expected_phases)
            
            if deployment_result["success"]:
                logger.info(f"DEPLOYMENT_EXECUTE_SUCCESS: All phases completed for {self.deployment_id}")
                await self._finalize_successful_deployment()
            else:
                logger.error(f"DEPLOYMENT_EXECUTE_FAILED: Deployment {self.deployment_id} failed")
            
            deployment_result["end_time"] = datetime.now().isoformat()
            deployment_result["total_duration_minutes"] = (
                datetime.now() - self.deployment_start_time
            ).total_seconds() / 60
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_EXECUTE_ERROR: {e}")
            deployment_result["error_message"] = str(e)
            deployment_result["success"] = False
            
            # Emergency rollback
            await rollback_system.emergency_rollback_all()
            
            return deployment_result
    
    async def _execute_deployment_phase(self, phase_name: str, phase_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single deployment phase."""
        phase_start_time = datetime.now()
        
        phase_result = {
            "phase": phase_name,
            "start_time": phase_start_time.isoformat(),
            "success": False,
            "metrics": {},
            "error_message": None,
        }
        
        try:
            logger.info(f"DEPLOYMENT_PHASE_EXEC: Executing {phase_name} - {phase_config['description']}")
            
            # 1. Update feature flags for this phase
            if "features" in phase_config:
                for feature in phase_config["features"]:
                    # Determine rollout phase based on percentage
                    if phase_config["target_percentage"] <= 5.0:
                        rollout_phase = FeatureRolloutPhase.PHASE_1
                    elif phase_config["target_percentage"] <= 20.0:
                        rollout_phase = FeatureRolloutPhase.PHASE_2
                    elif phase_config["target_percentage"] <= 50.0:
                        rollout_phase = FeatureRolloutPhase.PHASE_3
                    else:
                        rollout_phase = FeatureRolloutPhase.FULL
                    
                    success = feature_flags.update_feature_flag(
                        feature_name=feature,
                        enabled=True,
                        rollout_phase=rollout_phase,
                        rollout_percentage=phase_config["target_percentage"]
                    )
                    
                    if not success:
                        raise Exception(f"Failed to update feature flag: {feature}")
                    
                    logger.info(f"DEPLOYMENT_PHASE_FEATURE: {feature} -> {rollout_phase.value} ({phase_config['target_percentage']}%)")
            
            # Save feature flag state
            await feature_flags.save_state_to_cache()
            
            # 2. Monitor phase for specified duration
            monitoring_duration = phase_config["duration_minutes"]
            success_criteria = phase_config.get("success_criteria", {})
            
            logger.info(f"DEPLOYMENT_PHASE_MONITOR: Monitoring {phase_name} for {monitoring_duration} minutes")
            
            # Monitor in smaller intervals to allow early detection of issues
            monitoring_intervals = max(1, monitoring_duration // 10)  # 10 check points
            interval_minutes = monitoring_duration / monitoring_intervals
            
            metrics_history = []
            
            for i in range(monitoring_intervals):
                await asyncio.sleep(interval_minutes * 60)  # Convert to seconds
                
                # Collect metrics
                dashboard = await deployment_monitor.get_deployment_dashboard()
                health_checks = dashboard.get("health_checks", {})
                
                interval_metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "interval": i + 1,
                    "health_score": dashboard.get("overall_health", {}).get("score", 0),
                    "error_rate": health_checks.get("error_rate", {}).get("value", 0),
                    "response_time": health_checks.get("response_time", {}).get("value", 0),
                    "fallback_rate": health_checks.get("kerykeion_fallback", {}).get("value", 0),
                    "user_satisfaction": health_checks.get("user_satisfaction", {}).get("value", 10),
                }
                
                metrics_history.append(interval_metrics)
                
                # Check success criteria
                criteria_violations = []
                
                if "error_rate_max" in success_criteria and interval_metrics["error_rate"] > success_criteria["error_rate_max"]:
                    criteria_violations.append(f"Error rate too high: {interval_metrics['error_rate']:.1f}% > {success_criteria['error_rate_max']}%")
                
                if "response_time_max" in success_criteria and interval_metrics["response_time"] > success_criteria["response_time_max"]:
                    criteria_violations.append(f"Response time too high: {interval_metrics['response_time']:.1f}ms > {success_criteria['response_time_max']}ms")
                
                if "fallback_rate_max" in success_criteria and interval_metrics["fallback_rate"] > success_criteria["fallback_rate_max"]:
                    criteria_violations.append(f"Fallback rate too high: {interval_metrics['fallback_rate']:.1f}% > {success_criteria['fallback_rate_max']}%")
                
                if "user_satisfaction_min" in success_criteria and interval_metrics["user_satisfaction"] < success_criteria["user_satisfaction_min"]:
                    criteria_violations.append(f"User satisfaction too low: {interval_metrics['user_satisfaction']:.1f} < {success_criteria['user_satisfaction_min']}")
                
                if criteria_violations:
                    logger.warning(f"DEPLOYMENT_PHASE_CRITERIA_VIOLATION: {phase_name} interval {i+1}: {criteria_violations}")
                    
                    # If violations persist for 2+ intervals, fail the phase
                    if i >= 1:  # Allow one interval for metrics to stabilize
                        phase_result["error_message"] = f"Success criteria violations: {'; '.join(criteria_violations)}"
                        phase_result["metrics"] = metrics_history
                        return phase_result
                
                logger.debug(f"DEPLOYMENT_PHASE_INTERVAL: {phase_name} interval {i+1}/{monitoring_intervals} - Health: {interval_metrics['health_score']:.1f}%")
            
            # 3. Final evaluation
            phase_result["metrics"] = metrics_history
            
            if metrics_history:
                # Average metrics over the monitoring period
                avg_metrics = {
                    "avg_health_score": sum(m["health_score"] for m in metrics_history) / len(metrics_history),
                    "avg_error_rate": sum(m["error_rate"] for m in metrics_history) / len(metrics_history),
                    "avg_response_time": sum(m["response_time"] for m in metrics_history) / len(metrics_history),
                    "avg_fallback_rate": sum(m["fallback_rate"] for m in metrics_history) / len(metrics_history),
                    "avg_user_satisfaction": sum(m["user_satisfaction"] for m in metrics_history) / len(metrics_history),
                }
                
                phase_result["average_metrics"] = avg_metrics
                
                # Final success evaluation
                if avg_metrics["avg_health_score"] >= 70:  # Minimum acceptable health
                    phase_result["success"] = True
                    logger.info(f"DEPLOYMENT_PHASE_SUCCESS: {phase_name} completed successfully")
                else:
                    phase_result["error_message"] = f"Average health score too low: {avg_metrics['avg_health_score']:.1f}%"
            else:
                phase_result["error_message"] = "No metrics collected during monitoring period"
            
            phase_result["end_time"] = datetime.now().isoformat()
            phase_result["duration_minutes"] = (datetime.now() - phase_start_time).total_seconds() / 60
            
            return phase_result
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_PHASE_ERROR: {phase_name}: {e}")
            phase_result["error_message"] = str(e)
            phase_result["end_time"] = datetime.now().isoformat()
            return phase_result
    
    async def _handle_deployment_failure(self, failed_phase: str, phase_result: Dict[str, Any]):
        """Handle deployment phase failure with appropriate rollback."""
        logger.critical(f"DEPLOYMENT_FAILURE: Handling failure in {failed_phase}")
        
        try:
            # Determine rollback strategy based on failed phase
            if failed_phase in ["phase_1"]:
                # Early phase failure - rollback specific features
                rollback_features = self.deployment_phases[failed_phase].get("features", [])
                await rollback_system.manual_rollback(
                    features=rollback_features,
                    strategy="immediate",
                    reason=f"Phase {failed_phase} failure: {phase_result.get('error_message')}"
                )
            else:
                # Later phase failure - full system rollback
                await rollback_system.emergency_rollback_all()
            
            # Record failure metrics
            await deployment_monitor.record_metric(
                "deployment", 
                "phase_failure", 
                1.0, 
                phase=failed_phase, 
                error=phase_result.get("error_message")
            )
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_FAILURE_HANDLING_ERROR: {e}")
    
    async def _finalize_successful_deployment(self):
        """Finalize successful deployment."""
        logger.info(f"DEPLOYMENT_FINALIZE: Finalizing successful deployment {self.deployment_id}")
        
        try:
            # Save final feature flag state
            await feature_flags.save_state_to_cache()
            
            # Record successful deployment metrics
            await deployment_monitor.record_metric(
                "deployment", 
                "successful_completion", 
                1.0, 
                deployment_id=self.deployment_id
            )
            
            # Generate final deployment report
            final_report = deployment_monitor.generate_deployment_report(24)
            logger.info(f"DEPLOYMENT_FINAL_REPORT:\n{final_report}")
            
        except Exception as e:
            logger.error(f"DEPLOYMENT_FINALIZE_ERROR: {e}")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        return {
            "deployment_id": self.deployment_id,
            "start_time": self.deployment_start_time.isoformat(),
            "current_phase": self.current_phase,
            "phase_progress": self.phase_progress,
            "elapsed_time_minutes": (datetime.now() - self.deployment_start_time).total_seconds() / 60,
            "deployment_phases": {
                name: {
                    "description": config["description"],
                    "target_percentage": config.get("target_percentage", 0),
                    "duration_minutes": config["duration_minutes"],
                }
                for name, config in self.deployment_phases.items()
            }
        }


async def main():
    """Main deployment orchestration function."""
    logger.info("PRODUCTION_DEPLOYMENT: Starting Kerykeion production deployment")
    
    # Create deployment configuration
    deployment_config = ProductionDeploymentConfig()
    
    try:
        # 1. Initialize all deployment systems
        init_result = await deployment_config.initialize_deployment_systems()
        
        if not init_result["success"]:
            logger.error("DEPLOYMENT_INIT_FAILED: Cannot proceed with deployment")
            return init_result
        
        # 2. Execute phased deployment
        deployment_result = await deployment_config.execute_phased_deployment()
        
        # 3. Return final results
        final_result = {
            "deployment_successful": deployment_result["success"],
            "initialization": init_result,
            "deployment": deployment_result,
            "final_status": deployment_config.get_deployment_status(),
        }
        
        if deployment_result["success"]:
            logger.info("PRODUCTION_DEPLOYMENT_SUCCESS: Kerykeion deployment completed successfully")
        else:
            logger.error("PRODUCTION_DEPLOYMENT_FAILED: Kerykeion deployment failed")
        
        return final_result
        
    except Exception as e:
        logger.error(f"PRODUCTION_DEPLOYMENT_ERROR: {e}")
        
        # Emergency cleanup
        try:
            await rollback_system.emergency_rollback_all()
            await deployment_monitor.stop_monitoring()
            await performance_monitor.stop_monitoring()
        except:
            pass
        
        return {
            "deployment_successful": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    # Run deployment if executed directly
    asyncio.run(main())