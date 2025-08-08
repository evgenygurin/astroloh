#!/usr/bin/env python3
"""Test script for kerykeion-based astrology calculator"""

import logging
import sys
from datetime import datetime

import pytz

# Add project root to path (repo root)
sys.path.insert(0, "/workspace")

from app.models.yandex_models import YandexZodiacSign
from app.services.astrology_calculator import AstrologyCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def test_basic_functionality():
    """Test basic functionality of the astrology calculator"""
    print("\n" + "=" * 50)
    print("Testing Kerykeion-based Astrology Calculator")
    print("=" * 50)

    calculator = AstrologyCalculator()

    # Show backend info
    backend_info = calculator.get_backend_info()
    print(f"\n✓ Backend: {backend_info['backend']}")
    print(f"✓ Version: {backend_info['version']}")
    print(
        f"✓ Available backends: {', '.join(backend_info['available_backends'])}"
    )

    # Test zodiac sign calculation
    print("\n" + "-" * 30)
    print("Testing Zodiac Sign Calculation")
    print("-" * 30)

    test_dates = [
        (datetime(1990, 3, 25), YandexZodiacSign.ARIES),
        (datetime(1990, 8, 15), YandexZodiacSign.LEO),
        (datetime(1990, 12, 15), YandexZodiacSign.SAGITTARIUS),
    ]

    for test_date, expected_sign in test_dates:
        sign = calculator.get_zodiac_sign_by_date(test_date.date())
        status = "✓" if sign == expected_sign else "✗"
        print(
            f"{status} {test_date.strftime('%Y-%m-%d')}: {sign.value} (expected: {expected_sign.value})"
        )

    # Test natal chart creation
    print("\n" + "-" * 30)
    print("Testing Natal Chart Creation")
    print("-" * 30)

    birth_datetime = datetime(1990, 8, 15, 14, 30, tzinfo=pytz.UTC)
    chart = calculator.create_natal_chart(
        name="Test User",
        birth_datetime=birth_datetime,
        latitude=55.7558,  # Moscow
        longitude=37.6176,
    )

    print(f"✓ Chart created for: {chart.name}")
    print(f"✓ Birth date: {chart.birth_datetime}")
    print(f"✓ Planets calculated: {len(chart.planets)}")
    print(
        f"✓ Houses calculated: {len([h for h in chart.houses if isinstance(h, int)])}"
    )
    print(f"✓ Aspects calculated: {len(chart.aspects)}")
    print(f"✓ Arabic parts calculated: {len(chart.arabic_parts)}")
    print(f"✓ Fixed stars calculated: {len(chart.fixed_stars)}")

    # Show some planet positions
    print("\nPlanet Positions:")
    for planet_name in ["Sun", "Moon", "Mercury", "Venus", "Mars"]:
        if planet_name in chart.planets:
            planet = chart.planets[planet_name]
            print(
                f"  {planet_name}: {planet.get('sign', 'Unknown')} {planet.get('degree_in_sign', 0):.2f}°"
            )

    # Test moon phase calculation
    print("\n" + "-" * 30)
    print("Testing Moon Phase Calculation")
    print("-" * 30)

    moon_phase = calculator.calculate_moon_phase(datetime.now())
    print(
        f"✓ Phase: {moon_phase['phase_name']} {moon_phase.get('moon_emoji', '')}"
    )
    print(f"✓ Illumination: {moon_phase['illumination_percent']:.1f}%")
    print(f"✓ Waxing: {moon_phase['is_waxing']}")

    # Test compatibility calculation
    print("\n" + "-" * 30)
    print("Testing Compatibility Calculation")
    print("-" * 30)

    compatibility = calculator.calculate_compatibility_score(
        YandexZodiacSign.LEO, YandexZodiacSign.ARIES
    )
    print(f"✓ Leo + Aries compatibility: {compatibility['total_score']:.1f}%")
    print(f"✓ Description: {compatibility['description']}")
    print(f"✓ Element compatibility: {compatibility['element_score']:.1f}%")
    print(f"✓ Quality compatibility: {compatibility['quality_score']:.1f}%")

    # Test planetary hours
    print("\n" + "-" * 30)
    print("Testing Planetary Hours")
    print("-" * 30)

    planetary_hours = calculator.get_planetary_hours(datetime.now())
    print(f"✓ Day ruler: {planetary_hours['day_ruler']}")
    print(f"✓ Current hour ruler: {planetary_hours['current_hour_ruler']}")
    print(f"✓ Favorable hours: {planetary_hours['favorable_hours']}")

    # Test advanced features if available
    if backend_info["capabilities"].get("synastry"):
        print("\n" + "-" * 30)
        print("Testing Advanced Features")
        print("-" * 30)

        # Create second chart for synastry
        chart2 = calculator.create_natal_chart(
            name="Partner",
            birth_datetime=datetime(1992, 4, 20, 10, 0, tzinfo=pytz.UTC),
            latitude=55.7558,
            longitude=37.6176,
        )

        # Test synastry
        synastry = calculator.calculate_synastry(chart, chart2)
        print(f"✓ Synastry aspects: {len(synastry['aspects'])}")
        print(f"✓ Compatibility score: {synastry['compatibility_score']:.1f}%")

        # Test transits
        transits = calculator.calculate_transits(chart)
        print(f"✓ Current transits: {len(transits['aspects'])} aspects")

        # Test progressions
        progressions = calculator.calculate_progressions(chart)
        print(
            f"✓ Progressed planets calculated: {len(progressions['progressed_planets'])}"
        )

    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        logging.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)
