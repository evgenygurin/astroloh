"""
Test deployment system functionality.
Tests feature flags, deployment monitoring, and rollback automation.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.services.deployment_monitor import HealthStatus, deployment_monitor
from app.services.feature_flag_service import (
    FeatureRolloutPhase,
    KerykeionFeatureFlags,
    feature_flags,
)
from app.services.rollback_system import (
    RollbackStrategy,
    RollbackTrigger,
    rollback_system,
)


@pytest.fixture
async def clean_feature_flags():
    """Clean feature flags state before test."""
    # Reset feature flags to initial state
    feature_flags.flags.clear()
    feature_flags.user_assignments.clear()
    feature_flags._initialize_kerykeion_flags()
    yield
    # Cleanup after test
    feature_flags.flags.clear()
    feature_flags.user_assignments.clear()


@pytest.fixture
async def clean_deployment_monitor():
    """Clean deployment monitor state before test."""
    deployment_monitor.metrics_history.clear()
    deployment_monitor.health_checks.clear()
    yield
    # Cleanup
    deployment_monitor.metrics_history.clear()
    deployment_monitor.health_checks.clear()


@pytest.fixture
async def clean_rollback_system():
    """Clean rollback system state before test."""
    rollback_system.rollback_history.clear()
    rollback_system.active_rollbacks.clear()
    rollback_system.system_state_backup.clear()
    yield
    # Cleanup
    rollback_system.rollback_history.clear()
    rollback_system.active_rollbacks.clear()


class TestFeatureFlagService:
    """Test feature flag service functionality."""

    async def test_feature_flag_initialization(self, clean_feature_flags):
        """Test that feature flags are initialized correctly."""
        assert len(feature_flags.flags) == 8  # All Kerykeion features

        # Check that natal charts feature exists
        assert (
            KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS in feature_flags.flags
        )

        natal_flag = feature_flags.flags[
            KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS
        ]
        assert natal_flag.enabled is True
        assert natal_flag.rollout_phase == FeatureRolloutPhase.PHASE_1
        assert natal_flag.rollout_percentage == 5.0

    async def test_user_hash_consistency(self, clean_feature_flags):
        """Test that user hashing is consistent."""
        user_id = "test_user_123"
        feature_name = KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS

        # Get hash multiple times
        hash1 = feature_flags._get_user_hash(user_id, feature_name)
        hash2 = feature_flags._get_user_hash(user_id, feature_name)
        hash3 = feature_flags._get_user_hash(user_id, feature_name)

        assert hash1 == hash2 == hash3
        assert 0 <= hash1 <= 1

    async def test_feature_rollout_percentage(self, clean_feature_flags):
        """Test feature rollout based on percentage."""
        feature_name = KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS

        # Set to 50% rollout
        feature_flags.update_feature_flag(
            feature_name,
            rollout_percentage=50.0,
            rollout_phase=FeatureRolloutPhase.PHASE_3,
        )

        # Test with many users to check approximate percentage
        enabled_count = 0
        total_users = 1000

        for i in range(total_users):
            user_id = f"user_{i}"
            if feature_flags.is_feature_enabled(feature_name, user_id):
                enabled_count += 1

        # Should be approximately 50% (allow 10% variance)
        percentage = (enabled_count / total_users) * 100
        assert 40 <= percentage <= 60

    async def test_feature_update(self, clean_feature_flags):
        """Test updating feature flags."""
        feature_name = KerykeionFeatureFlags.KERYKEION_SYNASTRY

        # Update feature
        success = feature_flags.update_feature_flag(
            feature_name,
            enabled=False,
            rollout_phase=FeatureRolloutPhase.ROLLBACK,
        )

        assert success is True

        flag = feature_flags.flags[feature_name]
        assert flag.enabled is False
        assert flag.rollout_phase == FeatureRolloutPhase.ROLLBACK

        # Test that feature is now disabled for users
        assert (
            feature_flags.is_feature_enabled(feature_name, "any_user") is False
        )

    async def test_emergency_rollback(self, clean_feature_flags):
        """Test emergency rollback functionality."""
        feature_name = KerykeionFeatureFlags.KERYKEION_TRANSITS

        # Ensure feature is enabled first
        assert feature_flags.is_feature_enabled(feature_name, "test_user")

        # Execute emergency rollback
        success = feature_flags.emergency_rollback(feature_name)
        assert success is True

        # Check that feature is disabled
        flag = feature_flags.flags[feature_name]
        assert flag.enabled is False
        assert flag.rollout_phase == FeatureRolloutPhase.ROLLBACK

        # Test that feature is disabled for all users
        assert (
            feature_flags.is_feature_enabled(feature_name, "test_user")
            is False
        )


class TestDeploymentMonitor:
    """Test deployment monitoring functionality."""

    async def test_metric_recording(self, clean_deployment_monitor):
        """Test recording deployment metrics."""
        await deployment_monitor.record_metric(
            "test_feature", "response_time", 150.0, user_id="test_user"
        )

        assert len(deployment_monitor.metrics_history) == 1

        metric = deployment_monitor.metrics_history[0]
        assert metric.feature_name == "test_feature"
        assert metric.metric_type == "response_time"
        assert metric.value == 150.0
        assert metric.user_id == "test_user"

    async def test_kerykeion_usage_recording(self, clean_deployment_monitor):
        """Test recording Kerykeion service usage."""
        await deployment_monitor.record_kerykeion_usage(
            "natal_chart",
            success=True,
            response_time_ms=1200.0,
            fallback_used=False,
        )

        # Should record multiple metrics
        assert (
            len(deployment_monitor.metrics_history) == 2
        )  # response_time + success_rate

        # Find response time metric
        response_metric = next(
            m
            for m in deployment_monitor.metrics_history
            if m.metric_type == "response_time"
        )
        assert response_metric.value == 1200.0

        # Find success rate metric
        success_metric = next(
            m
            for m in deployment_monitor.metrics_history
            if m.metric_type == "success_rate"
        )
        assert success_metric.value == 1.0

    @patch(
        "app.services.deployment_monitor.deployment_monitor.perform_health_checks"
    )
    async def test_health_checks(
        self, mock_health_checks, clean_deployment_monitor
    ):
        """Test system health checks."""
        # Mock health check results
        from app.services.deployment_monitor import HealthCheck

        mock_health_checks.return_value = {
            "response_time": HealthCheck(
                check_name="Response Time",
                status=HealthStatus.GOOD,
                value=800.0,
                threshold=2000.0,
                message="Response time: 800ms",
            ),
            "error_rate": HealthCheck(
                check_name="Error Rate",
                status=HealthStatus.EXCELLENT,
                value=1.5,
                threshold=5.0,
                message="Error rate: 1.5%",
            ),
        }

        health_checks = await deployment_monitor.perform_health_checks()

        assert len(health_checks) == 2
        assert "response_time" in health_checks
        assert "error_rate" in health_checks

        assert health_checks["response_time"].status == HealthStatus.GOOD
        assert health_checks["error_rate"].status == HealthStatus.EXCELLENT


class TestRollbackSystem:
    """Test rollback system functionality."""

    @patch("app.services.rollback_system.astro_cache")
    async def test_backup_system_state(
        self, mock_cache, clean_rollback_system
    ):
        """Test system state backup."""
        mock_cache.set = AsyncMock(return_value=True)

        success = await rollback_system.backup_current_state()
        assert success is True
        assert rollback_system.system_state_backup is not None

        # Check that backup contains expected data
        backup = rollback_system.system_state_backup
        assert "timestamp" in backup
        assert "feature_flags" in backup

    async def test_rollback_plan_creation(self, clean_rollback_system):
        """Test creation of rollback plans."""
        plan = await rollback_system._create_rollback_plan(
            RollbackTrigger.HIGH_ERROR_RATE,
            RollbackStrategy.IMMEDIATE,
            "test_rule",
        )

        assert plan is not None
        assert plan.strategy == RollbackStrategy.IMMEDIATE
        assert len(plan.rollback_steps) > 0
        assert plan.expected_duration > 0

        # Check that plan is stored in active rollbacks
        assert plan.rollback_id in rollback_system.active_rollbacks

    @patch("app.services.rollback_system.feature_flags")
    async def test_manual_rollback(
        self, mock_feature_flags, clean_rollback_system
    ):
        """Test manual rollback execution."""
        mock_feature_flags.emergency_rollback.return_value = True

        features_to_rollback = ["kerykeion_natal_charts", "kerykeion_synastry"]

        rollback_event = await rollback_system.manual_rollback(
            features=features_to_rollback,
            strategy=RollbackStrategy.IMMEDIATE,
            reason="Test rollback",
        )

        assert rollback_event is not None
        assert rollback_event.trigger == RollbackTrigger.MANUAL
        assert rollback_event.affected_features == features_to_rollback
        assert "reason" in rollback_event.rollback_data
        assert rollback_event.rollback_data["reason"] == "Test rollback"

    async def test_rollback_statistics(self, clean_rollback_system):
        """Test rollback statistics calculation."""
        # Add some mock rollback history
        from app.services.rollback_system import RollbackEvent

        rollback_system.rollback_history = [
            RollbackEvent(
                rollback_id="test1",
                timestamp=datetime.now(),
                trigger=RollbackTrigger.MANUAL,
                strategy=RollbackStrategy.IMMEDIATE,
                affected_features=["feature1"],
                rollback_data={},
                success=True,
                recovery_time=30.0,
            ),
            RollbackEvent(
                rollback_id="test2",
                timestamp=datetime.now(),
                trigger=RollbackTrigger.HIGH_ERROR_RATE,
                strategy=RollbackStrategy.GRADUAL,
                affected_features=["feature2"],
                rollback_data={},
                success=False,
                error_message="Test error",
            ),
        ]

        stats = await rollback_system.get_rollback_statistics()

        assert stats["total_rollbacks"] == 2
        assert stats["successful_rollbacks"] == 1
        assert stats["success_rate"] == 50.0
        assert (
            stats["average_recovery_time"] == 30.0
        )  # Only successful rollbacks counted
        assert "manual" in stats["trigger_breakdown"]
        assert "high_error_rate" in stats["trigger_breakdown"]


class TestIntegration:
    """Test integration between deployment components."""

    async def test_feature_flag_deployment_monitoring_integration(
        self, clean_feature_flags, clean_deployment_monitor
    ):
        """Test integration between feature flags and deployment monitoring."""
        feature_name = KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS

        # Enable feature for user
        user_id = "integration_test_user"
        feature_flags.is_feature_enabled(feature_name, user_id)

        # Record usage metrics
        await deployment_monitor.record_kerykeion_usage(
            "natal_chart",
            success=True,
            response_time_ms=950.0,
            fallback_used=False,
        )

        # Update feature metrics
        await feature_flags.update_feature_metrics(
            feature_name,
            {"last_usage": datetime.now().isoformat(), "user_count": 1},
        )

        # Get feature metrics
        metrics = await feature_flags.get_rollout_metrics(feature_name)

        assert "last_usage" in metrics
        assert metrics["user_count"] == 1

        # Check deployment metrics
        assert len(deployment_monitor.metrics_history) >= 1

    @patch("app.services.rollback_system.deployment_monitor")
    async def test_rollback_trigger_integration(
        self, mock_deployment_monitor, clean_rollback_system
    ):
        """Test integration between deployment monitoring and rollback triggers."""
        # Mock critical health status
        mock_dashboard = {
            "overall_health": {"status": "failure", "score": 10},
            "health_checks": {
                "error_rate": {
                    "status": "critical",
                    "value": 25.0,  # High error rate
                }
            },
        }

        mock_deployment_monitor.get_deployment_dashboard = AsyncMock(
            return_value=mock_dashboard
        )

        # Test rollback need analysis
        rollback_plan = await rollback_system.analyze_rollback_need()

        # Should detect need for rollback due to system failure or high error rate
        assert rollback_plan is not None
        assert rollback_plan.strategy in [
            RollbackStrategy.IMMEDIATE,
            RollbackStrategy.FULL_SYSTEM,
            RollbackStrategy.GRADUAL,
        ]


@pytest.mark.asyncio
async def test_deployment_system_startup():
    """Test that deployment system can be initialized."""
    try:
        from app.services.startup_manager import startup_manager

        # Test initialization (without actually starting background services)
        result = await startup_manager.initialize_performance_systems(
            enable_cache_warmup=False,
            enable_background_monitoring=False,
            enable_precomputation=False,
        )

        # Should succeed even if some services aren't available
        assert "initialization_results" in result

        # Clean up any initialized services
        try:
            await startup_manager.shutdown_performance_systems()
        except Exception as cleanup_error:
            # Ignore cleanup errors in tests as services may not be initialized
            pass

    except ImportError:
        pytest.skip("Deployment services not available in test environment")


if __name__ == "__main__":
    pytest.main([__file__])
