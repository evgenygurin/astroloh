#!/usr/bin/env python3
"""
Production deployment script for Kerykeion features.
Executes the complete phased rollout process with monitoring and rollback capabilities.

Usage:
    python scripts/deploy_kerykeion.py [--dry-run] [--phase PHASE] [--auto-advance]
    
Options:
    --dry-run       Simulate deployment without making actual changes
    --phase PHASE   Start from specific phase (phase_1, phase_2, phase_3, full)
    --auto-advance  Automatically advance through phases without manual confirmation
    --rollback      Execute emergency rollback of all features
    --status        Show current deployment status
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger
from deployment_config import ProductionDeploymentConfig
from app.services.deployment_monitor import deployment_monitor
from app.services.feature_flag_service import feature_flags, FeatureRolloutPhase
from app.services.rollback_system import rollback_system
from app.services.startup_manager import startup_manager


class DeploymentOrchestrator:
    """Orchestrates the production deployment process."""
    
    def __init__(self, dry_run: bool = False, auto_advance: bool = False):
        self.dry_run = dry_run
        self.auto_advance = auto_advance
        self.deployment_config = ProductionDeploymentConfig()
        
        if dry_run:
            logger.warning("DRY RUN MODE: No actual changes will be made")
    
    async def execute_deployment(self, start_phase: str = None) -> Dict[str, Any]:
        """Execute the complete deployment process."""
        logger.info("🚀 STARTING KERYKEION PRODUCTION DEPLOYMENT")
        
        try:
            # Initialize deployment systems
            print("📋 Initializing deployment systems...")
            init_result = await self.deployment_config.initialize_deployment_systems()
            
            if not init_result["success"]:
                print(f"❌ Initialization failed: {init_result['errors']}")
                return init_result
            
            print(f"✅ Systems initialized successfully")
            print(f"   - Health score: {init_result['initial_health_score']:.1f}%")
            print(f"   - Systems ready: {len(init_result['systems_initialized'])}")
            
            if not init_result["ready_for_deployment"]:
                print("⚠️  System not ready for deployment")
                if not self._confirm_action("Continue anyway?"):
                    return {"success": False, "message": "Deployment cancelled by user"}
            
            # Show deployment plan
            self._show_deployment_plan(start_phase)
            
            if not self.auto_advance and not self._confirm_action("Proceed with deployment?"):
                return {"success": False, "message": "Deployment cancelled by user"}
            
            # Execute phased deployment
            print("\n🎯 Starting phased deployment...")
            
            if self.dry_run:
                return self._simulate_deployment(start_phase)
            else:
                return await self.deployment_config.execute_phased_deployment()
                
        except KeyboardInterrupt:
            print("\n⚠️  Deployment interrupted by user")
            return await self._handle_interruption()
        except Exception as e:
            logger.error(f"DEPLOYMENT_ORCHESTRATOR_ERROR: {e}")
            print(f"💥 Deployment failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _show_deployment_plan(self, start_phase: str = None):
        """Display the deployment plan to user."""
        print("\n📊 DEPLOYMENT PLAN:")
        print("=" * 60)
        
        phases = self.deployment_config.deployment_phases
        for phase_name, config in phases.items():
            if phase_name == "preparation":
                continue
                
            status = "⏭️ " if start_phase and phase_name != start_phase else "📋"
            print(f"{status} {phase_name.upper()}: {config['description']}")
            
            if "target_percentage" in config:
                print(f"     Target: {config['target_percentage']}% of users")
            if "features" in config:
                print(f"     Features: {', '.join(config['features'])}")
            print(f"     Duration: {config['duration_minutes']} minutes")
            
            if "success_criteria" in config:
                criteria = config["success_criteria"]
                print(f"     Success criteria:")
                for criterion, value in criteria.items():
                    print(f"       - {criterion}: {value}")
            print()
    
    def _simulate_deployment(self, start_phase: str = None) -> Dict[str, Any]:
        """Simulate deployment for dry run."""
        print("🎭 DRY RUN: Simulating deployment phases...")
        
        simulation_result = {
            "deployment_id": f"dry_run_{int(datetime.now().timestamp())}",
            "dry_run": True,
            "simulated_phases": [],
            "success": True,
        }
        
        phases = list(self.deployment_config.deployment_phases.keys())
        if "preparation" in phases:
            phases.remove("preparation")
        
        # Skip to start phase if specified
        if start_phase:
            try:
                start_index = phases.index(start_phase)
                phases = phases[start_index:]
            except ValueError:
                print(f"⚠️  Invalid start phase: {start_phase}")
        
        for phase in phases:
            print(f"📋 Simulating {phase}...")
            simulation_result["simulated_phases"].append({
                "phase": phase,
                "status": "simulated",
                "timestamp": datetime.now().isoformat(),
            })
        
        print("✅ Dry run completed successfully")
        return simulation_result
    
    async def _handle_interruption(self) -> Dict[str, Any]:
        """Handle deployment interruption."""
        print("🛑 Handling deployment interruption...")
        
        try:
            # Check if rollback is needed
            dashboard = await deployment_monitor.get_deployment_dashboard()
            health_score = dashboard.get("overall_health", {}).get("score", 0)
            
            if health_score < 70:
                print(f"⚠️  System health low ({health_score:.1f}%), initiating rollback...")
                rollback_result = await rollback_system.emergency_rollback_all()
                return {
                    "success": False,
                    "interrupted": True,
                    "rollback_executed": True,
                    "rollback_result": rollback_result,
                }
            else:
                print(f"✅ System health acceptable ({health_score:.1f}%), no rollback needed")
                return {
                    "success": False,
                    "interrupted": True,
                    "rollback_executed": False,
                }
                
        except Exception as e:
            logger.error(f"INTERRUPTION_HANDLING_ERROR: {e}")
            return {
                "success": False,
                "interrupted": True,
                "error": str(e),
            }
    
    def _confirm_action(self, message: str) -> bool:
        """Get user confirmation for action."""
        if self.auto_advance:
            return True
            
        response = input(f"\n{message} (y/N): ").strip().lower()
        return response in ['y', 'yes']
    
    async def show_current_status(self):
        """Show current deployment and system status."""
        print("📊 CURRENT DEPLOYMENT STATUS")
        print("=" * 50)
        
        try:
            # System status
            system_status = await startup_manager.get_system_status()
            print(f"🖥️  System Status: {'✅ Running' if system_status.get('startup_completed') else '⚠️ Initializing'}")
            
            # Feature flags status
            features_status = feature_flags.get_all_features_status()
            print(f"🎛️  Total Features: {features_status['total_features']}")
            
            enabled_count = sum(1 for f in features_status['features'].values() if f['enabled'])
            print(f"✅ Enabled Features: {enabled_count}/{features_status['total_features']}")
            
            print("\n📋 FEATURE DETAILS:")
            for name, info in features_status['features'].items():
                status = "✅" if info['enabled'] else "❌"
                phase = info['rollout_phase']
                percentage = info['rollout_percentage']
                print(f"   {status} {name}: {phase} ({percentage}%)")
            
            # Health checks
            dashboard = await deployment_monitor.get_deployment_dashboard()
            health = dashboard.get("overall_health", {})
            print(f"\n🏥 System Health: {health.get('score', 0):.1f}% ({health.get('status', 'unknown')})")
            
            # Rollback history
            rollback_stats = await rollback_system.get_rollback_statistics()
            print(f"🔄 Rollback History: {rollback_stats['total_rollbacks']} total")
            if rollback_stats['total_rollbacks'] > 0:
                print(f"   Success Rate: {rollback_stats['success_rate']}%")
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
    
    async def execute_rollback(self, features: list = None):
        """Execute rollback of specified features or all features."""
        print("🔄 EXECUTING ROLLBACK")
        print("=" * 30)
        
        try:
            if features:
                print(f"Rolling back features: {', '.join(features)}")
                rollback_result = await rollback_system.manual_rollback(
                    features=features,
                    reason="Manual rollback via script"
                )
            else:
                print("Rolling back ALL features...")
                rollback_features = rollback_system.emergency_rollback_all()
                rollback_result = {
                    "success": True,
                    "rolled_back_features": rollback_features,
                    "message": f"Emergency rollback of {len(rollback_features)} features"
                }
            
            if rollback_result.get("success"):
                print("✅ Rollback completed successfully")
                if "recovery_time" in rollback_result:
                    print(f"   Recovery time: {rollback_result['recovery_time']:.1f}s")
            else:
                print(f"❌ Rollback failed: {rollback_result.get('error_message', 'Unknown error')}")
            
            return rollback_result
            
        except Exception as e:
            print(f"💥 Rollback error: {e}")
            return {"success": False, "error": str(e)}


async def main():
    """Main deployment script function."""
    parser = argparse.ArgumentParser(description="Deploy Kerykeion features to production")
    parser.add_argument("--dry-run", action="store_true", help="Simulate deployment without making changes")
    parser.add_argument("--phase", choices=["phase_1", "phase_2", "phase_3", "full"], help="Start from specific phase")
    parser.add_argument("--auto-advance", action="store_true", help="Automatically advance without confirmations")
    parser.add_argument("--rollback", action="store_true", help="Execute emergency rollback")
    parser.add_argument("--status", action="store_true", help="Show current deployment status")
    parser.add_argument("--features", nargs="+", help="Specific features to rollback")
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(sys.stdout, level="INFO", format="<level>{level: <8}</level> | {message}")
    
    orchestrator = DeploymentOrchestrator(
        dry_run=args.dry_run,
        auto_advance=args.auto_advance
    )
    
    try:
        if args.status:
            await orchestrator.show_current_status()
            
        elif args.rollback:
            result = await orchestrator.execute_rollback(args.features)
            sys.exit(0 if result.get("success") else 1)
            
        else:
            # Execute deployment
            result = await orchestrator.execute_deployment(args.phase)
            
            # Print results
            print("\n" + "=" * 60)
            if result.get("success") or result.get("dry_run"):
                print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
                
                if result.get("deployment"):
                    deployment = result["deployment"]
                    print(f"   Deployment ID: {deployment.get('deployment_id')}")
                    print(f"   Phases completed: {len(deployment.get('phases_completed', []))}")
                    if "total_duration_minutes" in deployment:
                        print(f"   Total duration: {deployment['total_duration_minutes']:.1f} minutes")
            else:
                print("💥 DEPLOYMENT FAILED!")
                if "error_message" in result:
                    print(f"   Error: {result['error_message']}")
                
                # Show rollback information if applicable
                if result.get("phases_failed"):
                    print(f"   Failed phases: {', '.join(result['phases_failed'])}")
            
            # Save deployment results
            results_file = Path("deployment_results.json")
            with open(results_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"📄 Results saved to: {results_file}")
            
            sys.exit(0 if result.get("success") or result.get("dry_run") else 1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"DEPLOYMENT_SCRIPT_ERROR: {e}")
        print(f"💥 Script error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())