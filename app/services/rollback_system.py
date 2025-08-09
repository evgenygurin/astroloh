"""
Automated rollback system for production deployments.
Handles emergency rollbacks, feature disabling, and system recovery.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.astro_cache_service import astro_cache
from app.services.deployment_monitor import deployment_monitor
from app.services.feature_flag_service import feature_flags
from app.services.performance_monitor import performance_monitor


class RollbackTrigger(Enum):
    """Types of rollback triggers."""

    MANUAL = "manual"
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_RESPONSE = "slow_response"
    HIGH_FALLBACK_RATE = "high_fallback_rate"
    USER_COMPLAINTS = "user_complaints"
    SYSTEM_FAILURE = "system_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    AUTOMATIC = "automatic"


class RollbackStrategy(Enum):
    """Rollback execution strategies."""

    IMMEDIATE = "immediate"  # Instant rollback
    GRADUAL = "gradual"  # Gradual percentage reduction
    FEATURE_SPECIFIC = "feature_specific"  # Rollback specific features
    FULL_SYSTEM = "full_system"  # Complete system rollback


@dataclass
class RollbackEvent:
    """Record of a rollback event."""

    rollback_id: str
    timestamp: datetime
    trigger: RollbackTrigger
    strategy: RollbackStrategy
    affected_features: List[str]
    rollback_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    recovery_time: Optional[float] = None
    user_impact: Optional[Dict[str, Any]] = None


@dataclass
class RollbackPlan:
    """Plan for executing a rollback."""

    rollback_id: str
    strategy: RollbackStrategy
    target_features: List[str]
    rollback_steps: List[Dict[str, Any]]
    expected_duration: float
    user_notification_required: bool
    backup_data: Dict[str, Any] = field(default_factory=dict)


class RollbackSystem:
    """Automated system for handling production rollbacks."""

    def __init__(self):
        self.rollback_history: List[RollbackEvent] = []
        self.active_rollbacks: Dict[str, RollbackPlan] = {}
        self.rollback_rules = self._initialize_rollback_rules()
        self.system_state_backup: Dict[str, Any] = {}

        # Circuit breaker for preventing rollback loops
        self.circuit_breaker = {
            "max_rollbacks_per_hour": 3,
            "cooldown_minutes": 30,
            "last_rollback_time": None,
            "rollback_count": 0,
        }

        logger.info("ROLLBACK_SYSTEM_INIT: Rollback system initialized")

    def _initialize_rollback_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rollback decision rules."""
        return {
            "error_rate_threshold": {
                "trigger": RollbackTrigger.HIGH_ERROR_RATE,
                "condition": "error_rate > 10.0",
                "strategy": RollbackStrategy.GRADUAL,
                "severity": "high",
                "auto_execute": True,
            },
            "response_time_threshold": {
                "trigger": RollbackTrigger.SLOW_RESPONSE,
                "condition": "avg_response_time > 5000",
                "strategy": RollbackStrategy.FEATURE_SPECIFIC,
                "severity": "medium",
                "auto_execute": True,
            },
            "fallback_rate_threshold": {
                "trigger": RollbackTrigger.HIGH_FALLBACK_RATE,
                "condition": "kerykeion_fallback_rate > 50.0",
                "strategy": RollbackStrategy.FEATURE_SPECIFIC,
                "severity": "high",
                "auto_execute": True,
            },
            "system_failure": {
                "trigger": RollbackTrigger.SYSTEM_FAILURE,
                "condition": "health_status == 'failure'",
                "strategy": RollbackStrategy.IMMEDIATE,
                "severity": "critical",
                "auto_execute": True,
            },
            "user_satisfaction": {
                "trigger": RollbackTrigger.USER_COMPLAINTS,
                "condition": "avg_satisfaction < 5.0",
                "strategy": RollbackStrategy.GRADUAL,
                "severity": "medium",
                "auto_execute": False,
            },
        }

    async def backup_current_state(self) -> bool:
        """Backup current system state before rollback."""
        try:
            logger.info("ROLLBACK_BACKUP_STATE: Creating system state backup")

            # Backup feature flag states
            feature_status = feature_flags.get_all_features_status()

            # Backup performance metrics
            perf_stats = performance_monitor.get_overall_statistics()

            # Backup deployment metrics
            dashboard = await deployment_monitor.get_deployment_dashboard()

            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "feature_flags": feature_status,
                "performance_stats": perf_stats,
                "deployment_dashboard": dashboard,
                "system_health": dashboard.get("overall_health", {}),
            }

            self.system_state_backup = backup_data

            # Store backup in cache for persistence
            cache_result = astro_cache.set(
                f"system_backup_{int(datetime.now().timestamp())}",
                backup_data,
                ttl=86400 * 7,  # Keep for 7 days
            )
            logger.debug(
                f"ROLLBACK_CACHE_SET_RESULT_TYPE: {type(cache_result)}"
            )
            await cache_result

            logger.info("ROLLBACK_BACKUP_SUCCESS: System state backed up")
            return True

        except Exception as e:
            logger.error(f"ROLLBACK_BACKUP_ERROR: {e}")
            return False

    async def analyze_rollback_need(self) -> Optional[RollbackPlan]:
        """Analyze current system state and determine if rollback is needed."""
        try:
            logger.debug(
                "ROLLBACK_ANALYSIS: Analyzing system for rollback need"
            )

            # Check circuit breaker
            if await self._is_circuit_breaker_active():
                logger.warning(
                    "ROLLBACK_CIRCUIT_BREAKER: Circuit breaker active, skipping analysis"
                )
                return None

            # Get current system health
            dashboard = await deployment_monitor.get_deployment_dashboard()
            health_checks = dashboard.get("health_checks", {})

            # Evaluate rollback rules
            for rule_name, rule in self.rollback_rules.items():
                if await self._evaluate_rollback_condition(
                    rule, health_checks, dashboard
                ):
                    logger.warning(
                        f"ROLLBACK_CONDITION_MET: Rule '{rule_name}' triggered"
                    )

                    rollback_plan = await self._create_rollback_plan(
                        rule["trigger"], rule["strategy"], rule_name
                    )

                    if rollback_plan and rule.get("auto_execute", False):
                        logger.critical(
                            f"ROLLBACK_AUTO_TRIGGER: Automatic rollback planned for rule '{rule_name}'"
                        )
                        return rollback_plan

            return None

        except Exception as e:
            logger.error(f"ROLLBACK_ANALYSIS_ERROR: {e}")
            return None

    async def _evaluate_rollback_condition(
        self,
        rule: Dict[str, Any],
        health_checks: Dict[str, Any],
        dashboard: Dict[str, Any],
    ) -> bool:
        """Evaluate if a specific rollback condition is met."""
        try:
            trigger = rule["trigger"]

            if trigger == RollbackTrigger.HIGH_ERROR_RATE:
                error_check = health_checks.get("error_rate", {})
                if error_check.get("status") in ["critical", "failure"]:
                    return error_check.get("value", 0) > 10.0

            elif trigger == RollbackTrigger.SLOW_RESPONSE:
                response_check = health_checks.get("response_time", {})
                if response_check.get("status") in ["critical", "failure"]:
                    return response_check.get("value", 0) > 5000

            elif trigger == RollbackTrigger.HIGH_FALLBACK_RATE:
                fallback_check = health_checks.get("kerykeion_fallback", {})
                if fallback_check.get("status") in ["critical", "failure"]:
                    return fallback_check.get("value", 0) > 50.0

            elif trigger == RollbackTrigger.SYSTEM_FAILURE:
                overall_health = dashboard.get("overall_health", {})
                return overall_health.get("status") == "failure"

            elif trigger == RollbackTrigger.USER_COMPLAINTS:
                satisfaction_check = health_checks.get("user_satisfaction", {})
                if satisfaction_check.get("status") in ["critical", "warning"]:
                    return satisfaction_check.get("value", 10) < 5.0

            return False

        except Exception as e:
            logger.error(f"ROLLBACK_CONDITION_EVAL_ERROR: {e}")
            return False

    async def _create_rollback_plan(
        self,
        trigger: RollbackTrigger,
        strategy: RollbackStrategy,
        rule_name: str,
    ) -> Optional[RollbackPlan]:
        """Create a rollback plan based on trigger and strategy."""
        try:
            rollback_id = f"rollback_{int(datetime.now().timestamp())}"

            # Determine affected features based on trigger
            affected_features = await self._identify_affected_features(
                trigger, rule_name
            )

            # Create rollback steps
            rollback_steps = []
            expected_duration = 0

            if strategy == RollbackStrategy.IMMEDIATE:
                rollback_steps = [
                    {
                        "action": "disable_all_features",
                        "features": affected_features,
                        "duration": 10,
                    },
                    {"action": "clear_cache", "duration": 5},
                    {"action": "restart_monitoring", "duration": 15},
                ]
                expected_duration = 30

            elif strategy == RollbackStrategy.GRADUAL:
                rollback_steps = [
                    {
                        "action": "reduce_rollout_percentage",
                        "features": affected_features,
                        "target_percentage": 50,
                        "duration": 60,
                    },
                    {
                        "action": "reduce_rollout_percentage",
                        "features": affected_features,
                        "target_percentage": 20,
                        "duration": 60,
                    },
                    {
                        "action": "reduce_rollout_percentage",
                        "features": affected_features,
                        "target_percentage": 5,
                        "duration": 60,
                    },
                    {
                        "action": "disable_features_if_needed",
                        "features": affected_features,
                        "duration": 30,
                    },
                ]
                expected_duration = 210

            elif strategy == RollbackStrategy.FEATURE_SPECIFIC:
                rollback_steps = [
                    {
                        "action": "disable_specific_features",
                        "features": affected_features,
                        "duration": 20,
                    },
                    {
                        "action": "enable_fallbacks",
                        "features": affected_features,
                        "duration": 10,
                    },
                    {"action": "monitor_recovery", "duration": 60},
                ]
                expected_duration = 90

            elif strategy == RollbackStrategy.FULL_SYSTEM:
                rollback_steps = [
                    {"action": "backup_state", "duration": 30},
                    {
                        "action": "disable_all_kerykeion_features",
                        "duration": 20,
                    },
                    {"action": "clear_all_caches", "duration": 15},
                    {"action": "restart_all_services", "duration": 120},
                    {"action": "verify_recovery", "duration": 60},
                ]
                expected_duration = 245

            plan = RollbackPlan(
                rollback_id=rollback_id,
                strategy=strategy,
                target_features=affected_features,
                rollback_steps=rollback_steps,
                expected_duration=expected_duration,
                user_notification_required=(
                    strategy
                    in [
                        RollbackStrategy.FULL_SYSTEM,
                        RollbackStrategy.IMMEDIATE,
                    ]
                ),
                backup_data=self.system_state_backup,
            )

            self.active_rollbacks[rollback_id] = plan

            logger.info(
                f"ROLLBACK_PLAN_CREATED: {rollback_id} with {len(rollback_steps)} steps"
            )
            return plan

        except Exception as e:
            logger.error(f"ROLLBACK_PLAN_ERROR: {e}")
            return None

    async def _identify_affected_features(
        self, trigger: RollbackTrigger, rule_name: str
    ) -> List[str]:
        """Identify which features should be affected by rollback."""
        all_features = list(feature_flags.flags.keys())

        if trigger == RollbackTrigger.HIGH_FALLBACK_RATE:
            # Focus on Kerykeion-dependent features
            return [
                "kerykeion_natal_charts",
                "kerykeion_synastry",
                "kerykeion_transits",
                "kerykeion_progressions",
            ]

        elif trigger == RollbackTrigger.SLOW_RESPONSE:
            # Focus on performance-heavy features
            return [
                "kerykeion_transits",
                "kerykeion_progressions",
                "enhanced_compatibility",
                "ai_consultation",
            ]

        elif trigger == RollbackTrigger.SYSTEM_FAILURE:
            # All features for system failure
            return all_features

        elif trigger == RollbackTrigger.USER_COMPLAINTS:
            # User-facing features
            return [
                "enhanced_compatibility",
                "ai_consultation",
                "russian_localization",
            ]

        else:
            # Default to all Kerykeion features
            return [
                f
                for f in all_features
                if "kerykeion" in f or "enhanced" in f or "ai" in f
            ]

    async def execute_rollback(self, plan: RollbackPlan) -> RollbackEvent:
        """Execute a rollback plan."""
        start_time = datetime.now()
        rollback_event = RollbackEvent(
            rollback_id=plan.rollback_id,
            timestamp=start_time,
            trigger=RollbackTrigger.AUTOMATIC,  # Will be updated with actual trigger
            strategy=plan.strategy,
            affected_features=plan.target_features,
            rollback_data={},
            success=False,
        )

        try:
            logger.critical(
                f"ROLLBACK_EXECUTION_START: Executing rollback {plan.rollback_id}"
            )

            # Update circuit breaker
            await self._update_circuit_breaker()

            # Execute rollback steps
            for i, step in enumerate(plan.rollback_steps):
                try:
                    logger.info(
                        f"ROLLBACK_STEP: {i+1}/{len(plan.rollback_steps)} - {step['action']}"
                    )
                    await self._execute_rollback_step(step, rollback_event)

                    # Brief pause between steps
                    await asyncio.sleep(2)

                except Exception as step_error:
                    logger.error(
                        f"ROLLBACK_STEP_ERROR: Step {i+1} failed: {step_error}"
                    )
                    rollback_event.rollback_data[f"step_{i+1}_error"] = str(
                        step_error
                    )
                    # Continue with other steps

            # Verify rollback success
            success = await self._verify_rollback_success(plan, rollback_event)
            rollback_event.success = success

            # Calculate recovery time
            recovery_time = (datetime.now() - start_time).total_seconds()
            rollback_event.recovery_time = recovery_time

            # Record rollback event
            self.rollback_history.append(rollback_event)

            # Clean up active rollback
            if plan.rollback_id in self.active_rollbacks:
                del self.active_rollbacks[plan.rollback_id]

            # Store rollback event in cache
            await astro_cache.set(
                f"rollback_event_{plan.rollback_id}",
                {
                    "rollback_id": rollback_event.rollback_id,
                    "timestamp": rollback_event.timestamp.isoformat(),
                    "success": rollback_event.success,
                    "recovery_time": rollback_event.recovery_time,
                    "affected_features": rollback_event.affected_features,
                    "rollback_data": rollback_event.rollback_data,
                },
                ttl=86400 * 30,  # Keep for 30 days
            )

            if success:
                logger.info(
                    f"ROLLBACK_EXECUTION_SUCCESS: Rollback {plan.rollback_id} completed in {recovery_time:.1f}s"
                )
            else:
                logger.error(
                    f"ROLLBACK_EXECUTION_PARTIAL: Rollback {plan.rollback_id} partially successful"
                )

            return rollback_event

        except Exception as e:
            logger.error(f"ROLLBACK_EXECUTION_ERROR: {e}")
            rollback_event.error_message = str(e)
            rollback_event.recovery_time = (
                datetime.now() - start_time
            ).total_seconds()
            self.rollback_history.append(rollback_event)
            return rollback_event

    async def _execute_rollback_step(
        self, step: Dict[str, Any], rollback_event: RollbackEvent
    ):
        """Execute a single rollback step."""
        action = step["action"]

        if action == "disable_all_features":
            for feature in step["features"]:
                feature_flags.emergency_rollback(feature)
            rollback_event.rollback_data["disabled_features"] = step[
                "features"
            ]

        elif action == "disable_specific_features":
            for feature in step["features"]:
                feature_flags.emergency_rollback(feature)
            rollback_event.rollback_data["disabled_specific"] = step[
                "features"
            ]

        elif action == "reduce_rollout_percentage":
            target_percentage = step["target_percentage"]
            for feature in step["features"]:
                feature_flags.update_feature_flag(
                    feature, rollout_percentage=target_percentage
                )
            rollback_event.rollback_data[
                "reduced_to_percentage"
            ] = target_percentage

        elif action == "clear_cache":
            # Clear astrology cache
            cleared = await astro_cache.clear_all_caches()
            rollback_event.rollback_data["cache_cleared"] = cleared

        elif action == "clear_all_caches":
            cleared = await astro_cache.clear_all_caches()
            rollback_event.rollback_data["all_caches_cleared"] = cleared

        elif action == "enable_fallbacks":
            # This would typically involve configuration changes
            rollback_event.rollback_data["fallbacks_enabled"] = step[
                "features"
            ]

        elif action == "restart_monitoring":
            await deployment_monitor.stop_monitoring()
            await deployment_monitor.start_monitoring()
            rollback_event.rollback_data["monitoring_restarted"] = True

        elif action == "restart_all_services":
            # This would typically require coordinating with container orchestration
            rollback_event.rollback_data["services_restart_requested"] = True

        elif action == "backup_state":
            backed_up = await self.backup_current_state()
            rollback_event.rollback_data["state_backed_up"] = backed_up

        elif action == "monitor_recovery":
            # Wait and monitor system recovery
            await asyncio.sleep(30)
            dashboard = await deployment_monitor.get_deployment_dashboard()
            rollback_event.rollback_data["recovery_status"] = dashboard.get(
                "overall_health", {}
            )

        elif action == "verify_recovery":
            success = await self._verify_system_health()
            rollback_event.rollback_data["recovery_verified"] = success

    async def _verify_rollback_success(
        self, plan: RollbackPlan, rollback_event: RollbackEvent
    ) -> bool:
        """Verify that rollback was successful."""
        try:
            # Wait for system to stabilize
            await asyncio.sleep(30)

            # Check system health
            dashboard = await deployment_monitor.get_deployment_dashboard()
            overall_health = dashboard.get("overall_health", {})

            # Consider rollback successful if health improved
            health_score = overall_health.get("score", 0)

            if health_score >= 70:  # Good enough health score
                return True

            # Check if critical issues are resolved
            health_checks = dashboard.get("health_checks", {})
            critical_issues = [
                check
                for check in health_checks.values()
                if check.get("status") in ["critical", "failure"]
            ]

            # Rollback successful if no critical issues remain
            return len(critical_issues) == 0

        except Exception as e:
            logger.error(f"ROLLBACK_VERIFICATION_ERROR: {e}")
            return False

    async def _verify_system_health(self) -> bool:
        """Verify overall system health."""
        try:
            dashboard = await deployment_monitor.get_deployment_dashboard()
            overall_health = dashboard.get("overall_health", {})
            return overall_health.get("score", 0) >= 60
        except Exception as e:
            logger.error(f"ROLLBACK_HEALTH_CHECK_ERROR: {e}")
            return False

    async def _is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is preventing rollbacks."""
        now = datetime.now()

        # Reset counter if more than an hour has passed
        if self.circuit_breaker[
            "last_rollback_time"
        ] and now - self.circuit_breaker["last_rollback_time"] > timedelta(
            hours=1
        ):
            self.circuit_breaker["rollback_count"] = 0

        # Check if we've exceeded the limit
        if (
            self.circuit_breaker["rollback_count"]
            >= self.circuit_breaker["max_rollbacks_per_hour"]
        ):
            # Check cooldown period
            if self.circuit_breaker[
                "last_rollback_time"
            ] and now - self.circuit_breaker["last_rollback_time"] < timedelta(
                minutes=self.circuit_breaker["cooldown_minutes"]
            ):
                return True

        return False

    async def _update_circuit_breaker(self):
        """Update circuit breaker state after rollback."""
        now = datetime.now()
        self.circuit_breaker["last_rollback_time"] = now
        self.circuit_breaker["rollback_count"] += 1

    async def manual_rollback(
        self,
        features: List[str],
        strategy: RollbackStrategy = RollbackStrategy.IMMEDIATE,
        reason: str = "Manual intervention",
    ) -> RollbackEvent:
        """Execute manual rollback of specific features."""
        logger.warning(
            f"ROLLBACK_MANUAL: Manual rollback requested for {len(features)} features"
        )

        # Create manual rollback plan
        rollback_id = f"manual_rollback_{int(datetime.now().timestamp())}"

        rollback_steps = [
            {"action": "backup_state", "duration": 10},
            {
                "action": "disable_specific_features",
                "features": features,
                "duration": 20,
            },
            {"action": "clear_cache", "duration": 5},
            {"action": "verify_recovery", "duration": 30},
        ]

        plan = RollbackPlan(
            rollback_id=rollback_id,
            strategy=strategy,
            target_features=features,
            rollback_steps=rollback_steps,
            expected_duration=65,
            user_notification_required=True,
            backup_data={"manual_reason": reason},
        )

        # Execute the rollback
        rollback_event = await self.execute_rollback(plan)
        rollback_event.trigger = RollbackTrigger.MANUAL
        rollback_event.rollback_data["reason"] = reason

        return rollback_event

    def get_rollback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent rollback history."""
        recent_rollbacks = sorted(
            self.rollback_history, key=lambda x: x.timestamp, reverse=True
        )[:limit]

        return [
            {
                "rollback_id": rb.rollback_id,
                "timestamp": rb.timestamp.isoformat(),
                "trigger": rb.trigger.value,
                "strategy": rb.strategy.value,
                "affected_features": rb.affected_features,
                "success": rb.success,
                "recovery_time": rb.recovery_time,
                "error_message": rb.error_message,
            }
            for rb in recent_rollbacks
        ]

    async def get_rollback_statistics(self) -> Dict[str, Any]:
        """Get rollback system statistics."""
        total_rollbacks = len(self.rollback_history)

        if total_rollbacks == 0:
            return {
                "total_rollbacks": 0,
                "success_rate": 100.0,
                "average_recovery_time": 0,
                "circuit_breaker_status": "inactive",
            }

        successful_rollbacks = sum(
            1 for rb in self.rollback_history if rb.success
        )
        success_rate = (successful_rollbacks / total_rollbacks) * 100

        recovery_times = [
            rb.recovery_time
            for rb in self.rollback_history
            if rb.recovery_time
        ]
        avg_recovery_time = (
            sum(recovery_times) / len(recovery_times) if recovery_times else 0
        )

        # Trigger statistics
        trigger_counts = {}
        for rb in self.rollback_history:
            trigger = rb.trigger.value
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

        return {
            "total_rollbacks": total_rollbacks,
            "successful_rollbacks": successful_rollbacks,
            "success_rate": round(success_rate, 1),
            "average_recovery_time": round(avg_recovery_time, 1),
            "trigger_breakdown": trigger_counts,
            "circuit_breaker_status": "active"
            if await self._is_circuit_breaker_active()
            else "inactive",
            "active_rollbacks": len(self.active_rollbacks),
        }


# Global rollback system instance
rollback_system = RollbackSystem()
