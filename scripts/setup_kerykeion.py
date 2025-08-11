#!/usr/bin/env python3
"""
Kerykeion installation and configuration setup script.
Ensures proper installation of Kerykeion and its dependencies for Astroloh.

Usage:
    python scripts/setup_kerykeion.py [--force] [--docker] [--validate]
    
Options:
    --force     Force reinstallation of Kerykeion
    --docker    Setup for Docker environment
    --validate  Validate installation after setup
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from loguru import logger


class KerykeionSetup:
    """Handles Kerykeion installation and configuration."""

    def __init__(self, force: bool = False, docker: bool = False):
        self.force = force
        self.docker = docker
        self.setup_results = {
            "kerykeion_installed": False,
            "swisseph_installed": False,
            "dependencies_installed": False,
            "configuration_ok": False,
            "errors": [],
            "warnings": []
        }

    def install_kerykeion(self) -> bool:
        """Install Kerykeion and its dependencies."""
        print("📦 INSTALLING KERYKEION")
        print("=" * 40)

        try:
            # Check if uv is available
            try:
                subprocess.run(["uv", "--version"], check=True, capture_output=True)
                package_manager = "uv"
                print("✅ Using uv package manager")
            except (subprocess.CalledProcessError, FileNotFoundError):
                package_manager = "pip"
                print("⚠️  uv not found, using pip")

            # Install Kerykeion with full dependencies
            if package_manager == "uv":
                cmd = ["uv", "pip", "install", "kerykeion>=4.26.0", "pyswisseph==2.10.3.2"]
            else:
                cmd = [sys.executable, "-m", "pip", "install", "kerykeion>=4.26.0", "pyswisseph==2.10.3.2"]

            if self.force:
                cmd.append("--force-reinstall")

            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Kerykeion installation successful")
                self.setup_results["kerykeion_installed"] = True
                self.setup_results["swisseph_installed"] = True
                return True
            else:
                error_msg = f"Kerykeion installation failed: {result.stderr}"
                self.setup_results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                return False

        except Exception as e:
            error_msg = f"Installation process failed: {e}"
            self.setup_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def install_system_dependencies(self) -> bool:
        """Install system dependencies for Kerykeion."""
        if not self.docker:
            print("⚠️  System dependencies should be installed manually on non-Docker systems")
            print("   Required packages: gcc, g++, pkg-config, libffi-dev, libc6-dev, libswe-dev")
            return True

        print("🔧 INSTALLING SYSTEM DEPENDENCIES (Docker)")
        print("=" * 50)

        try:
            # Docker-specific dependencies
            dependencies = [
                "gcc", "g++", "pkg-config", "libffi-dev", 
                "libc6-dev", "libsqlite3-dev", "libswe-dev"
            ]

            for dep in dependencies:
                print(f"Installing {dep}...")
                cmd = ["apt-get", "update", "&&", "apt-get", "install", "-y", dep]
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    warning_msg = f"Failed to install {dep}: {result.stderr}"
                    self.setup_results["warnings"].append(warning_msg)
                    print(f"⚠️  {warning_msg}")

            print("✅ System dependencies installation completed")
            return True

        except Exception as e:
            error_msg = f"System dependencies installation failed: {e}"
            self.setup_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def configure_kerykeion(self) -> bool:
        """Configure Kerykeion settings."""
        print("⚙️  CONFIGURING KERYKEION")
        print("=" * 30)

        try:
            # Create necessary directories
            directories = ["/app/swisseph", "/app/logs", "/app/tmp"]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {directory}")

            # Set environment variables
            env_vars = {
                "KERYKEION_ENABLED": "true",
                "SWISSEPH_ENABLED": "true",
                "SWISS_EPHEMERIS_PATH": "/app/swisseph"
            }

            print("Environment variables to set:")
            for key, value in env_vars.items():
                print(f"   {key}={value}")

            self.setup_results["configuration_ok"] = True
            print("✅ Kerykeion configuration completed")
            return True

        except Exception as e:
            error_msg = f"Configuration failed: {e}"
            self.setup_results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def validate_installation(self) -> Dict[str, Any]:
        """Validate Kerykeion installation."""
        print("🔍 VALIDATING KERYKEION INSTALLATION")
        print("=" * 40)

        validation_results = {
            "kerykeion_available": False,
            "swisseph_available": False,
            "test_calculation_ok": False,
            "overall_success": False,
            "errors": [],
            "warnings": []
        }

        try:
            # Test Kerykeion import
            print("📦 Testing Kerykeion import...")
            try:
                from kerykeion import AstrologicalSubject, KerykeionChartSVG
                from kerykeion import Report as NatalChart
                validation_results["kerykeion_available"] = True
                print("✅ Kerykeion import successful")
            except ImportError as e:
                validation_results["errors"].append(f"Kerykeion import failed: {e}")
                print(f"❌ Kerykeion import failed: {e}")

            # Test Swiss Ephemeris
            print("📦 Testing Swiss Ephemeris...")
            try:
                import swisseph
                validation_results["swisseph_available"] = True
                print("✅ Swiss Ephemeris import successful")
            except ImportError as e:
                validation_results["warnings"].append(f"Swiss Ephemeris import failed: {e}")
                print(f"⚠️  Swiss Ephemeris import failed: {e}")

            # Test basic calculation
            if validation_results["kerykeion_available"]:
                print("🧮 Testing basic Kerykeion calculation...")
                try:
                    from datetime import datetime
                    import pytz
                    
                    # Create a test subject
                    test_subject = AstrologicalSubject(
                        name="Test User",
                        year=1990,
                        month=1,
                        day=1,
                        hour=12,
                        minute=0,
                        lat=55.7558,
                        lng=37.6176,
                        tz_str="Europe/Moscow",
                        city="Moscow",
                        nation="Russia"
                    )
                    
                    # Test basic properties
                    if hasattr(test_subject, 'sun') and test_subject.sun:
                        validation_results["test_calculation_ok"] = True
                        print("✅ Basic Kerykeion calculation successful")
                    else:
                        validation_results["errors"].append("Basic Kerykeion calculation failed")
                        print("❌ Basic Kerykeion calculation failed")
                        
                except Exception as e:
                    validation_results["errors"].append(f"Kerykeion calculation test failed: {e}")
                    print(f"❌ Kerykeion calculation test failed: {e}")

            # Overall validation result
            validation_results["overall_success"] = (
                validation_results["kerykeion_available"] and 
                validation_results["test_calculation_ok"]
            )

            # Print summary
            print("\n📊 VALIDATION SUMMARY:")
            print(f"   Kerykeion Available: {'✅' if validation_results['kerykeion_available'] else '❌'}")
            print(f"   Swiss Ephemeris: {'✅' if validation_results['swisseph_available'] else '⚠️'}")
            print(f"   Test Calculation: {'✅' if validation_results['test_calculation_ok'] else '❌'}")
            print(f"   Overall Status: {'✅ PASSED' if validation_results['overall_success'] else '❌ FAILED'}")

            return validation_results

        except Exception as e:
            logger.error(f"KERYKEION_VALIDATION_ERROR: {e}")
            validation_results["errors"].append(f"Validation process failed: {e}")
            return validation_results

    def run_setup(self) -> Dict[str, Any]:
        """Run complete Kerykeion setup process."""
        print("🚀 KERYKEION SETUP PROCESS")
        print("=" * 50)

        # Install system dependencies (if Docker)
        if self.docker:
            if not self.install_system_dependencies():
                print("⚠️  System dependencies installation had issues")

        # Install Kerykeion
        if not self.install_kerykeion():
            print("❌ Kerykeion installation failed")
            return self.setup_results

        # Configure Kerykeion
        if not self.configure_kerykeion():
            print("❌ Kerykeion configuration failed")
            return self.setup_results

        # Validate installation
        validation_results = self.validate_installation()
        
        # Update setup results
        self.setup_results.update(validation_results)

        # Print final summary
        print("\n🎉 SETUP COMPLETE")
        print("=" * 30)
        print(f"   Installation: {'✅' if self.setup_results['kerykeion_installed'] else '❌'}")
        print(f"   Configuration: {'✅' if self.setup_results['configuration_ok'] else '❌'}")
        print(f"   Validation: {'✅' if validation_results['overall_success'] else '❌'}")

        if self.setup_results["errors"]:
            print("\n❌ ERRORS:")
            for error in self.setup_results["errors"]:
                print(f"   - {error}")

        if self.setup_results["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in self.setup_results["warnings"]:
                print(f"   - {warning}")

        return self.setup_results


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup Kerykeion for Astroloh"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force reinstallation"
    )
    parser.add_argument(
        "--docker", action="store_true", help="Setup for Docker environment"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate installation only"
    )

    args = parser.parse_args()

    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        level="INFO",
        format="<level>{level: <8}</level> | {message}",
    )

    setup = KerykeionSetup(force=args.force, docker=args.docker)

    try:
        if args.validate:
            # Only validate
            validation_results = setup.validate_installation()
            sys.exit(0 if validation_results["overall_success"] else 1)
        else:
            # Run complete setup
            results = setup.run_setup()
            success = (
                results["kerykeion_installed"] and 
                results["configuration_ok"] and 
                results.get("overall_success", False)
            )
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"SETUP_ERROR: {e}")
        print(f"💥 Setup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()