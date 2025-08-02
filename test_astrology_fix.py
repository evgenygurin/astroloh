#!/usr/bin/env python3
"""
Test script to verify astrology calculator works with all backends.
"""
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.astrology_calculator import AstrologyCalculator
from models.yandex_models import YandexZodiacSign

def test_backend_availability():
    """Test which astronomy backends are available."""
    print("=== Testing Backend Availability ===")
    
    # Test pyswisseph
    try:
        import swisseph
        print("✓ pyswisseph is available")
    except ImportError as e:
        print(f"✗ pyswisseph not available: {e}")
    
    # Test skyfield
    try:
        from skyfield.api import load
        print("✓ skyfield is available")
    except ImportError as e:
        print(f"✗ skyfield not available: {e}")
    
    # Test astropy
    try:
        from astropy.time import Time
        print("✓ astropy is available")
    except ImportError as e:
        print(f"✗ astropy not available: {e}")
    
    print()

def test_calculator_functionality():
    """Test basic astrology calculator functionality."""
    print("=== Testing Calculator Functionality ===")
    
    calc = AstrologyCalculator()
    backend_info = calc.get_backend_info()
    
    print(f"Current backend: {backend_info['backend']}")
    print(f"Available backends: {backend_info['available_backends']}")
    print(f"Capabilities: {backend_info['capabilities']}")
    print()
    
    # Test date: June 15, 1990, 12:00 PM
    test_date = datetime(1990, 6, 15, 12, 0)
    
    print("Testing basic functions:")
    
    # Test zodiac sign calculation
    try:
        sign = calc.get_zodiac_sign_by_date(test_date.date())
        print(f"✓ Zodiac sign calculation: {sign.value}")
    except Exception as e:
        print(f"✗ Zodiac sign calculation failed: {e}")
    
    # Test Julian day calculation
    try:
        jd = calc.calculate_julian_day(test_date)
        print(f"✓ Julian day calculation: {jd}")
    except Exception as e:
        print(f"✗ Julian day calculation failed: {e}")
    
    # Test planet positions
    try:
        positions = calc.calculate_planet_positions(test_date)
        print(f"✓ Planet positions calculated for {len(positions)} planets")
        for planet, pos in list(positions.items())[:3]:  # Show first 3
            print(f"  {planet}: {pos['sign']} {pos['degree_in_sign']:.1f}°")
    except Exception as e:
        print(f"✗ Planet positions calculation failed: {e}")
    
    # Test houses calculation
    try:
        houses = calc.calculate_houses(test_date)
        print(f"✓ Houses calculation: {len([k for k in houses.keys() if isinstance(k, int)])} houses")
        if 'ascendant' in houses:
            asc = houses['ascendant']
            print(f"  Ascendant: {asc['sign']} {asc['degree_in_sign']:.1f}°")
    except Exception as e:
        print(f"✗ Houses calculation failed: {e}")
    
    # Test aspects calculation
    try:
        positions = calc.calculate_planet_positions(test_date)
        aspects = calc.calculate_aspects(positions)
        print(f"✓ Aspects calculation: {len(aspects)} aspects found")
    except Exception as e:
        print(f"✗ Aspects calculation failed: {e}")
    
    # Test moon phase
    try:
        moon_phase = calc.calculate_moon_phase(test_date)
        print(f"✓ Moon phase: {moon_phase['phase_name']}")
    except Exception as e:
        print(f"✗ Moon phase calculation failed: {e}")
    
    # Test compatibility
    try:
        compatibility = calc.calculate_compatibility_score(
            YandexZodiacSign.GEMINI, YandexZodiacSign.LEO
        )
        print(f"✓ Compatibility: {compatibility['total_score']}/100 ({compatibility['description']})")
    except Exception as e:
        print(f"✗ Compatibility calculation failed: {e}")
    
    print()

def test_fallback_behavior():
    """Test fallback behavior when libraries are missing."""
    print("=== Testing Fallback Behavior ===")
    
    # Simulate different backend scenarios
    from services import astrology_calculator
    original_backend = astrology_calculator._astronomy_backend
    
    backends_to_test = ["swisseph", "skyfield", "astropy", None]
    
    for backend in backends_to_test:
        print(f"Testing with backend: {backend or 'None (fallback)'}")
        
        # Temporarily set the backend
        astrology_calculator._astronomy_backend = backend
        
        try:
            calc = AstrologyCalculator()
            test_date = datetime(1990, 6, 15, 12, 0)
            
            # Test critical functions
            positions = calc.calculate_planet_positions(test_date)
            houses = calc.calculate_houses(test_date)
            moon_phase = calc.calculate_moon_phase(test_date)
            
            print(f"  ✓ All functions work with {backend or 'fallback'}")
            print(f"    Planets: {len(positions)}, Houses: {len([k for k in houses.keys() if isinstance(k, int)])}")
            
        except Exception as e:
            print(f"  ✗ Failed with {backend}: {e}")
        
        finally:
            # Restore original backend
            astrology_calculator._astronomy_backend = original_backend
    
    print()

if __name__ == "__main__":
    print("Astrology Calculator Test Suite")
    print("=" * 40)
    print()
    
    test_backend_availability()
    test_calculator_functionality()
    test_fallback_behavior()
    
    print("Test completed!")