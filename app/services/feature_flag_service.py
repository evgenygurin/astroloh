"""
Feature flag service for phased rollout of Kerykeion features.
Enables gradual deployment with user-based rollout percentages.
"""

import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from pydantic import BaseModel

from app.services.astro_cache_service import astro_cache
from app.services.performance_monitor import performance_monitor


class FeatureRolloutPhase(Enum):
    """Rollout phases for feature deployment."""

    DISABLED = "disabled"
    PHASE_1 = "phase_1"  # 5% of users
    PHASE_2 = "phase_2"  # 20% of users
    PHASE_3 = "phase_3"  # 50% of users
    FULL = "full"  # 100% of users
    ROLLBACK = "rollback"  # Emergency rollback


class FeatureFlag(BaseModel):
    """Feature flag configuration."""

    name: str
    description: str
    enabled: bool = False
    rollout_phase: FeatureRolloutPhase = FeatureRolloutPhase.DISABLED
    rollout_percentage: float = 0.0
    target_users: Set[str] = set()
    excluded_users: Set[str] = set()
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: Dict[str, Any] = {}
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class KerykeionFeatureFlags:
    """Specific feature flags for Kerykeion integration."""

    KERYKEION_NATAL_CHARTS = "kerykeion_natal_charts"
    KERYKEION_SYNASTRY = "kerykeion_synastry"
    KERYKEION_TRANSITS = "kerykeion_transits"
    KERYKEION_PROGRESSIONS = "kerykeion_progressions"
    ENHANCED_COMPATIBILITY = "enhanced_compatibility"
    AI_CONSULTATION = "ai_consultation"
    RUSSIAN_LOCALIZATION = "russian_localization"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class FeatureFlagService:
    """Service for managing feature flags and phased rollouts."""

    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self.user_assignments: Dict[
            str, Set[str]
        ] = {}  # user_id -> set of enabled features
        self.rollout_phases = {
            FeatureRolloutPhase.PHASE_1: 5.0,  # 5%
            FeatureRolloutPhase.PHASE_2: 20.0,  # 20%
            FeatureRolloutPhase.PHASE_3: 50.0,  # 50%
            FeatureRolloutPhase.FULL: 100.0,  # 100%
        }

        # Initialize default Kerykeion feature flags
        self._initialize_kerykeion_flags()

        logger.info(
            "FEATURE_FLAG_SERVICE_INIT: Feature flag service initialized"
        )

    def _initialize_kerykeion_flags(self):
        """Initialize default feature flags for Kerykeion integration."""
        default_flags = [
            {
                "name": KerykeionFeatureFlags.KERYKEION_NATAL_CHARTS,
                "description": "Enhanced natal chart calculations with Kerykeion",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.PHASE_1,
                "rollout_percentage": 5.0,
            },
            {
                "name": KerykeionFeatureFlags.KERYKEION_SYNASTRY,
                "description": "Professional synastry analysis using Kerykeion",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.PHASE_1,
                "rollout_percentage": 5.0,
            },
            {
                "name": KerykeionFeatureFlags.KERYKEION_TRANSITS,
                "description": "Advanced transit calculations with Kerykeion",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.PHASE_2,
                "rollout_percentage": 20.0,
            },
            {
                "name": KerykeionFeatureFlags.KERYKEION_PROGRESSIONS,
                "description": "Secondary progressions and returns",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.PHASE_2,
                "rollout_percentage": 20.0,
            },
            {
                "name": KerykeionFeatureFlags.ENHANCED_COMPATIBILITY,
                "description": "AI-enhanced compatibility analysis",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.PHASE_3,
                "rollout_percentage": 50.0,
            },
            {
                "name": KerykeionFeatureFlags.AI_CONSULTATION,
                "description": "AI-powered astrological consultations",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.PHASE_3,
                "rollout_percentage": 50.0,
            },
            {
                "name": KerykeionFeatureFlags.RUSSIAN_LOCALIZATION,
                "description": "Complete Russian localization system",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.FULL,
                "rollout_percentage": 100.0,
            },
            {
                "name": KerykeionFeatureFlags.PERFORMANCE_OPTIMIZATION,
                "description": "Async processing and caching optimizations",
                "enabled": True,
                "rollout_phase": FeatureRolloutPhase.FULL,
                "rollout_percentage": 100.0,
            },
        ]

        for flag_data in default_flags:
            flag = FeatureFlag(**flag_data)
            self.flags[flag.name] = flag

        logger.info(
            f"FEATURE_FLAG_SERVICE_INIT_FLAGS: Initialized {len(default_flags)} Kerykeion feature flags"
        )

    def is_feature_enabled(self, feature_name: str, user_id: str) -> bool:
        """Check if a feature is enabled for a specific user."""
        try:
            op_id = performance_monitor.start_operation(
                "FeatureFlagService", "is_feature_enabled"
            )

            if feature_name not in self.flags:
                logger.warning(f"FEATURE_FLAG_UNKNOWN: {feature_name}")
                performance_monitor.end_operation(
                    op_id, success=False, error_message="Unknown feature"
                )
                return False

            flag = self.flags[feature_name]

            # Check if feature is globally disabled
            if not flag.enabled:
                performance_monitor.end_operation(
                    op_id, success=True, cache_hit=True
                )
                return False

            # Check if user is explicitly excluded
            if user_id in flag.excluded_users:
                performance_monitor.end_operation(
                    op_id, success=True, cache_hit=True
                )
                return False

            # Check if user is explicitly included
            if user_id in flag.target_users:
                performance_monitor.end_operation(
                    op_id, success=True, cache_hit=True
                )
                return True

            # Check time-based constraints
            if flag.start_date and datetime.now() < flag.start_date:
                performance_monitor.end_operation(
                    op_id, success=True, cache_hit=True
                )
                return False

            if flag.end_date and datetime.now() > flag.end_date:
                performance_monitor.end_operation(
                    op_id, success=True, cache_hit=True
                )
                return False

            # Emergency rollback check
            if flag.rollout_phase == FeatureRolloutPhase.ROLLBACK:
                performance_monitor.end_operation(
                    op_id, success=True, cache_hit=True
                )
                return False

            # Full rollout
            if flag.rollout_phase == FeatureRolloutPhase.FULL:
                performance_monitor.end_operation(
                    op_id, success=True, cache_hit=True
                )
                return True

            # Percentage-based rollout using consistent hashing
            user_hash = self._get_user_hash(user_id, feature_name)
            rollout_threshold = flag.rollout_percentage / 100.0

            enabled = user_hash < rollout_threshold

            # Cache user assignment for consistency
            if user_id not in self.user_assignments:
                self.user_assignments[user_id] = set()

            if enabled:
                self.user_assignments[user_id].add(feature_name)
            else:
                self.user_assignments[user_id].discard(feature_name)

            performance_monitor.end_operation(op_id, success=True)
            return enabled

        except Exception as e:
            logger.error(
                f"FEATURE_FLAG_ERROR: {feature_name} for {user_id}: {e}"
            )
            performance_monitor.end_operation(
                op_id, success=False, error_message=str(e)
            )
            return False

    def _get_user_hash(self, user_id: str, feature_name: str) -> float:
        """Get consistent hash for user and feature combination."""
        combined = f"{user_id}:{feature_name}"
        hash_object = hashlib.md5(combined.encode())
        hash_hex = hash_object.hexdigest()

        # Convert first 8 characters to integer and normalize to 0-1
        hash_int = int(hash_hex[:8], 16)
        return hash_int / (16**8)

    async def get_user_enabled_features(self, user_id: str) -> Dict[str, bool]:
        """Get all features and their enabled status for a user."""
        enabled_features = {}

        for feature_name in self.flags:
            enabled_features[feature_name] = self.is_feature_enabled(
                feature_name, user_id
            )

        # Update user assignment cache
        self.user_assignments[user_id] = {
            name for name, enabled in enabled_features.items() if enabled
        }

        logger.debug(
            f"FEATURE_FLAG_USER_FEATURES: {user_id} has {len(self.user_assignments[user_id])} features enabled"
        )
        return enabled_features

    def update_feature_flag(
        self,
        feature_name: str,
        enabled: Optional[bool] = None,
        rollout_phase: Optional[FeatureRolloutPhase] = None,
        rollout_percentage: Optional[float] = None,
        target_users: Optional[Set[str]] = None,
        excluded_users: Optional[Set[str]] = None,
    ) -> bool:
        """Update feature flag configuration."""
        try:
            if feature_name not in self.flags:
                logger.error(f"FEATURE_FLAG_UPDATE_UNKNOWN: {feature_name}")
                return False

            flag = self.flags[feature_name]

            if enabled is not None:
                flag.enabled = enabled

            if rollout_phase is not None:
                flag.rollout_phase = rollout_phase
                # Update percentage based on phase
                if rollout_phase in self.rollout_phases:
                    flag.rollout_percentage = self.rollout_phases[
                        rollout_phase
                    ]

            if rollout_percentage is not None:
                flag.rollout_percentage = max(
                    0.0, min(100.0, rollout_percentage)
                )

            if target_users is not None:
                flag.target_users = target_users

            if excluded_users is not None:
                flag.excluded_users = excluded_users

            flag.updated_at = datetime.now()

            logger.info(
                f"FEATURE_FLAG_UPDATED: {feature_name} -> phase={flag.rollout_phase.value}, percentage={flag.rollout_percentage}%"
            )

            # Clear user assignments to force recalculation
            self.user_assignments.clear()

            return True

        except Exception as e:
            logger.error(f"FEATURE_FLAG_UPDATE_ERROR: {feature_name}: {e}")
            return False

    def advance_rollout_phase(self, feature_name: str) -> bool:
        """Advance feature to next rollout phase."""
        if feature_name not in self.flags:
            return False

        flag = self.flags[feature_name]
        current_phase = flag.rollout_phase

        phase_progression = {
            FeatureRolloutPhase.DISABLED: FeatureRolloutPhase.PHASE_1,
            FeatureRolloutPhase.PHASE_1: FeatureRolloutPhase.PHASE_2,
            FeatureRolloutPhase.PHASE_2: FeatureRolloutPhase.PHASE_3,
            FeatureRolloutPhase.PHASE_3: FeatureRolloutPhase.FULL,
        }

        next_phase = phase_progression.get(current_phase)
        if next_phase:
            return self.update_feature_flag(
                feature_name, rollout_phase=next_phase
            )

        return False

    def emergency_rollback(self, feature_name: str) -> bool:
        """Immediately disable feature for all users."""
        logger.warning(f"FEATURE_FLAG_EMERGENCY_ROLLBACK: {feature_name}")
        return self.update_feature_flag(
            feature_name,
            enabled=False,
            rollout_phase=FeatureRolloutPhase.ROLLBACK,
        )

    def emergency_rollback_all(self) -> List[str]:
        """Emergency rollback all features."""
        logger.warning(
            "FEATURE_FLAG_EMERGENCY_ROLLBACK_ALL: Rolling back all features"
        )

        rolled_back = []
        for feature_name in self.flags:
            if self.emergency_rollback(feature_name):
                rolled_back.append(feature_name)

        return rolled_back

    async def get_rollout_metrics(self, feature_name: str) -> Dict[str, Any]:
        """Get metrics for feature rollout."""
        if feature_name not in self.flags:
            return {"error": "Feature not found"}

        flag = self.flags[feature_name]

        # Calculate estimated user coverage
        total_users = max(
            1000, len(self.user_assignments)
        )  # Estimate minimum users
        estimated_enabled_users = int(
            total_users * (flag.rollout_percentage / 100.0)
        )

        # Get actual enabled users from assignments
        actual_enabled_users = sum(
            1
            for user_features in self.user_assignments.values()
            if feature_name in user_features
        )

        metrics = {
            "feature_name": feature_name,
            "enabled": flag.enabled,
            "rollout_phase": flag.rollout_phase.value,
            "rollout_percentage": flag.rollout_percentage,
            "estimated_enabled_users": estimated_enabled_users,
            "actual_enabled_users": actual_enabled_users,
            "total_tracked_users": len(self.user_assignments),
            "target_users_count": len(flag.target_users),
            "excluded_users_count": len(flag.excluded_users),
            "created_at": flag.created_at.isoformat(),
            "updated_at": flag.updated_at.isoformat(),
        }

        # Add cached metrics from flag
        if flag.metrics:
            metrics.update(flag.metrics)

        return metrics

    async def update_feature_metrics(
        self, feature_name: str, metrics: Dict[str, Any]
    ):
        """Update stored metrics for a feature."""
        if feature_name not in self.flags:
            return False

        flag = self.flags[feature_name]
        flag.metrics.update(metrics)
        flag.updated_at = datetime.now()

        logger.debug(f"FEATURE_FLAG_METRICS_UPDATED: {feature_name}")
        return True

    def get_all_features_status(self) -> Dict[str, Any]:
        """Get status of all feature flags."""
        return {
            "features": {
                name: {
                    "enabled": flag.enabled,
                    "rollout_phase": flag.rollout_phase.value,
                    "rollout_percentage": flag.rollout_percentage,
                    "description": flag.description,
                    "updated_at": flag.updated_at.isoformat(),
                }
                for name, flag in self.flags.items()
            },
            "total_features": len(self.flags),
            "total_users_tracked": len(self.user_assignments),
            "rollout_phases": {
                phase.value: percentage
                for phase, percentage in self.rollout_phases.items()
            },
        }

    async def save_state_to_cache(self):
        """Save feature flag state to cache for persistence."""
        try:
            state_data = {
                "flags": {
                    name: {
                        "name": flag.name,
                        "description": flag.description,
                        "enabled": flag.enabled,
                        "rollout_phase": flag.rollout_phase.value,
                        "rollout_percentage": flag.rollout_percentage,
                        "target_users": list(flag.target_users),
                        "excluded_users": list(flag.excluded_users),
                        "start_date": flag.start_date.isoformat()
                        if flag.start_date
                        else None,
                        "end_date": flag.end_date.isoformat()
                        if flag.end_date
                        else None,
                        "metrics": flag.metrics,
                        "created_at": flag.created_at.isoformat(),
                        "updated_at": flag.updated_at.isoformat(),
                    }
                    for name, flag in self.flags.items()
                },
                "user_assignments": {
                    user_id: list(features)
                    for user_id, features in self.user_assignments.items()
                },
                "saved_at": datetime.now().isoformat(),
            }

            await astro_cache.set(
                "feature_flags_state", state_data, ttl=86400
            )  # 24 hours
            logger.info(
                "FEATURE_FLAG_STATE_SAVED: Feature flag state saved to cache"
            )
            return True

        except Exception as e:
            logger.error(f"FEATURE_FLAG_SAVE_ERROR: {e}")
            return False

    async def load_state_from_cache(self):
        """Load feature flag state from cache."""
        try:
            state_data = await astro_cache.get("feature_flags_state")
            if not state_data:
                logger.info(
                    "FEATURE_FLAG_NO_CACHED_STATE: No cached state found"
                )
                return False

            # Restore flags
            for name, flag_data in state_data.get("flags", {}).items():
                try:
                    flag = FeatureFlag(
                        name=flag_data["name"],
                        description=flag_data["description"],
                        enabled=flag_data["enabled"],
                        rollout_phase=FeatureRolloutPhase(
                            flag_data["rollout_phase"]
                        ),
                        rollout_percentage=flag_data["rollout_percentage"],
                        target_users=set(flag_data.get("target_users", [])),
                        excluded_users=set(
                            flag_data.get("excluded_users", [])
                        ),
                        start_date=datetime.fromisoformat(
                            flag_data["start_date"]
                        )
                        if flag_data.get("start_date")
                        else None,
                        end_date=datetime.fromisoformat(flag_data["end_date"])
                        if flag_data.get("end_date")
                        else None,
                        metrics=flag_data.get("metrics", {}),
                        created_at=datetime.fromisoformat(
                            flag_data["created_at"]
                        ),
                        updated_at=datetime.fromisoformat(
                            flag_data["updated_at"]
                        ),
                    )
                    self.flags[name] = flag
                except Exception as e:
                    logger.error(f"FEATURE_FLAG_LOAD_FLAG_ERROR: {name}: {e}")

            # Restore user assignments
            for user_id, features in state_data.get(
                "user_assignments", {}
            ).items():
                self.user_assignments[user_id] = set(features)

            logger.info(
                f"FEATURE_FLAG_STATE_LOADED: Loaded {len(self.flags)} flags and {len(self.user_assignments)} user assignments"
            )
            return True

        except Exception as e:
            logger.error(f"FEATURE_FLAG_LOAD_ERROR: {e}")
            return False


# Global feature flag service instance
feature_flags = FeatureFlagService()
