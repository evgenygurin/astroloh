#!/usr/bin/env python3
"""
Test script for the new Kerykeion integration.
Tests the KerykeionService and enhanced NatalChartCalculator.
"""

import logging
import os
import sys
from datetime import date, datetime, time

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from app.services.astrology_calculator import AstrologyCalculator
    from app.services.kerykeion_service import HouseSystem, KerykeionService, ZodiacType
    from app.services.natal_chart import NatalChartCalculator
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(
        "Make sure you're running from the correct directory and dependencies are installed"
    )
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def test_kerykeion_service():
    """Test the KerykeionService directly"""
    print("\n" + "=" * 60)
    print("🧪 Testing KerykeionService")
    print("=" * 60)

    service = KerykeionService()

    print("✅ KerykeionService created")
    print(f"🔍 Kerykeion available: {service.is_available()}")

    if not service.is_available():
        print("⚠️  Kerykeion not available - testing fallback behavior")
        capabilities = service.get_service_capabilities()
        print(f"🔧 Service capabilities: {capabilities}")
        return False

    # Test creating an astrological subject
    print("\n📊 Testing astrological subject creation...")
    birth_datetime = datetime(1990, 8, 15, 14, 30)
    subject = service.create_astrological_subject(
        name="Test User",
        birth_datetime=birth_datetime,
        latitude=55.7558,  # Moscow
        longitude=37.6176,
        timezone="Europe/Moscow",
    )

    if subject:
        print("✅ Astrological subject created successfully")
    else:
        print("❌ Failed to create astrological subject")
        return False

    # Test full natal chart calculation
    print("\n🗺️  Testing full natal chart calculation...")
    chart_data = service.get_full_natal_chart_data(
        name="Test User",
        birth_datetime=birth_datetime,
        latitude=55.7558,
        longitude=37.6176,
        timezone="Europe/Moscow",
        house_system=HouseSystem.PLACIDUS,
        zodiac_type=ZodiacType.TROPICAL,
    )

    if "error" in chart_data:
        print(f"❌ Chart calculation failed: {chart_data['error']}")
        return False

    print("✅ Chart calculation successful")
    print(f"🌟 Planets found: {len(chart_data.get('planets', {}))}")
    print(f"🏠 Houses calculated: {len(chart_data.get('houses', {}))}")
    print(f"⭐ Aspects found: {len(chart_data.get('aspects', []))}")
    print(
        f"📊 Chart shape: {chart_data.get('chart_shape', {}).get('shape', 'Unknown')}"
    )

    # Show some planet positions
    print("\n🌍 Planet positions:")
    planets = chart_data.get("planets", {})
    for planet_name in ["sun", "moon", "mercury", "venus", "mars"]:
        if planet_name in planets:
            planet = planets[planet_name]
            print(
                f"  {planet.get('name', planet_name)}: {planet.get('sign', 'Unknown')} "
                f"{planet.get('degree_in_sign', 0):.2f}°"
            )

    # Test Arabic parts
    print("\n📿 Testing Arabic parts calculation...")
    arabic_parts = service.calculate_arabic_parts_extended(subject)
    if arabic_parts:
        print(f"✅ Arabic parts calculated: {len(arabic_parts)}")
        for part_name, part_data in list(arabic_parts.items())[:3]:
            print(
                f"  {part_data.get('name', part_name)}: {part_data.get('sign', 'Unknown')} "
                f"{part_data.get('degree_in_sign', 0):.2f}°"
            )
    else:
        print("⚠️  No Arabic parts calculated")

    return True


def test_enhanced_natal_chart():
    """Test the enhanced NatalChartCalculator"""
    print("\n" + "=" * 60)
    print("🧪 Testing Enhanced NatalChartCalculator")
    print("=" * 60)

    calculator = NatalChartCalculator()
    print("✅ NatalChartCalculator created")

    # Test enhanced natal chart calculation
    print("\n🎂 Testing enhanced natal chart calculation...")

    enhanced_chart = calculator.calculate_enhanced_natal_chart(
        name="Test User Enhanced",
        birth_date=date(1990, 8, 15),
        birth_time=time(14, 30),
        birth_place={"latitude": 55.7558, "longitude": 37.6176},
        timezone_str="Europe/Moscow",
        house_system="Placidus",
        zodiac_type="Tropical",
        include_arabic_parts=True,
        include_fixed_stars=True,
        generate_svg=False,  # Don't generate SVG for this test
    )

    print("✅ Enhanced chart calculated")
    print(
        f"🔧 Backend used: {enhanced_chart.get('calculation_backend', 'unknown')}"
    )
    print(
        f"🌟 Enhanced features available: {enhanced_chart.get('enhanced_features_available', False)}"
    )

    if enhanced_chart.get("enhanced_features_available"):
        print(f"🌍 Planets: {len(enhanced_chart.get('planets', {}))}")
        print(f"🏠 Houses: {len(enhanced_chart.get('houses', {}))}")
        print(f"⭐ Aspects: {len(enhanced_chart.get('aspects', []))}")

        # Show element distribution
        element_dist = enhanced_chart.get("element_distribution", {})
        if element_dist:
            print(f"🔥 Element distribution: {element_dist}")

        # Show some aspects with colors
        aspects = enhanced_chart.get("aspects", [])[:3]  # First 3 aspects
        if aspects:
            print("\n⭐ Sample aspects:")
            for aspect in aspects:
                print(
                    f"  {aspect.get('planet1', '?')} {aspect.get('symbol', '?')} "
                    f"{aspect.get('planet2', '?')} - {aspect.get('strength', '?')} "
                    f"(color: {aspect.get('color', 'none')})"
                )

        # Show enhanced interpretation if available
        interpretation = enhanced_chart.get("enhanced_interpretation", {})
        if interpretation:
            spiritual_path = interpretation.get("spiritual_path", {})
            if spiritual_path:
                print(
                    f"\n🕯️  Spiritual path: {spiritual_path.get('path', 'Unknown')}"
                )
    else:
        print("📋 Using fallback calculations")
        print(f"🌟 Basic planets: {len(enhanced_chart.get('planets', {}))}")
        print(f"🏠 Basic houses: {len(enhanced_chart.get('houses', {}))}")

    return True


def test_astrology_calculator_backend():
    """Test the backend detection in AstrologyCalculator"""
    print("\n" + "=" * 60)
    print("🧪 Testing AstrologyCalculator Backend Detection")
    print("=" * 60)

    calc = AstrologyCalculator()
    backend_info = calc.get_backend_info()

    print("✅ AstrologyCalculator created")
    print(f"🔧 Backend: {backend_info.get('backend', 'unknown')}")
    print(f"📦 Version: {backend_info.get('version', 'unknown')}")
    print(
        f"🌟 Available backends: {', '.join(backend_info.get('available_backends', []))}"
    )

    features = backend_info.get("features", {})
    print("\n🎯 Available features:")
    for feature, available in features.items():
        status = "✅" if available else "❌"
        print(f"  {status} {feature}")

    return True


def main():
    """Run all tests"""
    print("🚀 Starting Kerykeion Integration Tests")

    success_count = 0
    total_tests = 3

    try:
        # Test 1: KerykeionService
        if test_kerykeion_service():
            success_count += 1

        # Test 2: Enhanced NatalChartCalculator
        if test_enhanced_natal_chart():
            success_count += 1

        # Test 3: AstrologyCalculator backend detection
        if test_astrology_calculator_backend():
            success_count += 1

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        logging.exception("Test suite error")
        return False

    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")

    if success_count == total_tests:
        print(
            "🎉 All tests passed! Kerykeion integration is working correctly."
        )
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
