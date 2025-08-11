#!/usr/bin/env python3
"""
Simple test script to verify Kerykeion functionality.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
import pytz

def test_kerykeion_import():
    """Test Kerykeion import."""
    print("🔍 Testing Kerykeion import...")
    try:
        from kerykeion import AstrologicalSubject, KerykeionChartSVG
        from kerykeion import Report as NatalChart
        print("✅ Kerykeion import successful")
        return True
    except ImportError as e:
        print(f"❌ Kerykeion import failed: {e}")
        return False

def test_swisseph_import():
    """Test Swiss Ephemeris import."""
    print("🔍 Testing Swiss Ephemeris import...")
    try:
        import swisseph
        print("✅ Swiss Ephemeris import successful")
        return True
    except ImportError as e:
        print(f"❌ Swiss Ephemeris import failed: {e}")
        return False

def test_basic_calculation():
    """Test basic Kerykeion calculation."""
    print("🧮 Testing basic Kerykeion calculation...")
    try:
        from kerykeion import AstrologicalSubject
        
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
            print("✅ Basic Kerykeion calculation successful")
            print(f"   Sun position: {test_subject.sun}")
            return True
        else:
            print("❌ Basic Kerykeion calculation failed")
            return False
            
    except Exception as e:
        print(f"❌ Kerykeion calculation test failed: {e}")
        return False

def test_astroloh_integration():
    """Test Astroloh Kerykeion service integration."""
    print("🔗 Testing Astroloh Kerykeion service integration...")
    try:
        from app.services.kerykeion_service import KerykeionService
        
        service = KerykeionService()
        
        if service.is_available():
            print("✅ Astroloh Kerykeion service available")
            
            # Test service capabilities
            capabilities = service.get_service_capabilities()
            print(f"   Features: {list(capabilities['features'].keys())}")
            
            return True
        else:
            print("❌ Astroloh Kerykeion service not available")
            return False
            
    except Exception as e:
        print(f"❌ Astroloh integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 KERYKEION FUNCTIONALITY TEST")
    print("=" * 50)
    
    tests = [
        ("Kerykeion Import", test_kerykeion_import),
        ("Swiss Ephemeris Import", test_swisseph_import),
        ("Basic Calculation", test_basic_calculation),
        ("Astroloh Integration", test_astroloh_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # Print summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Kerykeion is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())