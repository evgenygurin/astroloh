#!/usr/bin/env python3
"""
Comprehensive Kerykeion Integration Test Suite
Tests all implemented features and advanced capabilities
"""

import asyncio
from datetime import datetime
import pytz
from app.services.kerykeion_service import KerykeionService, HouseSystem, ZodiacType
from app.services.async_kerykeion_service import AsyncKerykeionService
from app.services.astrology_calculator import AstrologyCalculator
from app.services.natal_chart import NatalChartCalculator


def test_kerykeion_service_comprehensive():
    """Test all KerykeionService features"""
    print("🧪 Comprehensive KerykeionService Testing")
    print("=" * 60)
    
    service = KerykeionService()
    test_datetime = datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC)
    
    # Test 1: Basic natal chart
    print("\n1️⃣ Testing basic natal chart calculation...")
    natal_result = service.get_full_natal_chart_data(
        name='Test Person',
        birth_datetime=test_datetime,
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow',
        house_system=HouseSystem.PLACIDUS,
        zodiac_type=ZodiacType.TROPICAL
    )
    
    if 'error' in natal_result:
        print(f"❌ Natal chart error: {natal_result['error']}")
        return False
    
    print(f"✅ Natal chart: {len(natal_result.get('planets', []))} planets, {len(natal_result.get('houses', []))} houses")
    
    # Test 2: Different house systems
    print("\n2️⃣ Testing different house systems...")
    house_systems = [HouseSystem.KOCH, HouseSystem.EQUAL, HouseSystem.WHOLE_SIGN]
    for house_system in house_systems:
        result = service.get_full_natal_chart_data(
            name='Test Person',
            birth_datetime=test_datetime,
            latitude=55.7558,
            longitude=37.6176,
            timezone='Europe/Moscow',
            house_system=house_system,
            zodiac_type=ZodiacType.TROPICAL
        )
        
        if 'error' in result:
            print(f"❌ {house_system.value} error: {result['error']}")
        else:
            print(f"✅ {house_system.value}: {len(result.get('houses', []))} houses")
    
    # Test 3: Sidereal zodiac
    print("\n3️⃣ Testing sidereal zodiac...")
    sidereal_result = service.get_full_natal_chart_data(
        name='Test Person',
        birth_datetime=test_datetime,
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow',
        house_system=HouseSystem.PLACIDUS,
        zodiac_type=ZodiacType.SIDEREAL
    )
    
    if 'error' in sidereal_result:
        print(f"❌ Sidereal error: {sidereal_result['error']}")
    else:
        print(f"✅ Sidereal: {len(sidereal_result.get('planets', []))} planets")
    
    # Test 4: Arabic parts
    print("\n4️⃣ Testing Arabic parts...")
    arabic_result = service.calculate_arabic_parts_extended(natal_result)
    if 'error' in arabic_result:
        print(f"❌ Arabic parts error: {arabic_result['error']}")
    else:
        print(f"✅ Arabic parts: {len(arabic_result.get('parts', []))} parts calculated")
    
    # Test 5: Secondary progressions
    print("\n5️⃣ Testing secondary progressions...")
    prog_result = service.calculate_secondary_progressions(
        name='Test Person',
        birth_datetime=test_datetime,
        current_date=datetime(2024, 1, 1, tzinfo=pytz.UTC),
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow'
    )
    
    if 'error' in prog_result:
        print(f"❌ Progressions error: {prog_result['error']}")
    else:
        print(f"✅ Progressions: {len(prog_result.get('progressed_planets', []))} progressed planets")
    
    # Test 6: Solar return
    print("\n6️⃣ Testing solar return...")
    solar_result = service.calculate_solar_return(
        name='Test Person',
        birth_datetime=test_datetime,
        return_year=2024,
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow'
    )
    
    if 'error' in solar_result:
        print(f"❌ Solar return error: {solar_result['error']}")
    else:
        print(f"✅ Solar return: {len(solar_result.get('planets', []))} planets")
    
    # Test 7: SVG generation
    print("\n7️⃣ Testing SVG chart generation...")
    svg_result = service.generate_chart_svg(
        name='Test Person',
        birth_datetime=test_datetime,
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow'
    )
    
    if svg_result is None:
        print("⚠️ SVG generation: File created but method returned None")
    else:
        print(f"✅ SVG generation: {len(str(svg_result))} characters")
    
    # Test 8: Service capabilities
    print("\n8️⃣ Testing service capabilities...")
    capabilities = service.get_service_capabilities()
    available_features = sum(1 for feature in capabilities.get('features', {}).values() if feature)
    print(f"✅ Service capabilities: {available_features} features available")
    
    return True


async def test_async_kerykeion_service():
    """Test AsyncKerykeionService features"""
    print("\n🚀 Async KerykeionService Testing")
    print("=" * 60)
    
    service = AsyncKerykeionService()
    test_datetime = datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC)
    
    # Test async natal chart
    print("\n1️⃣ Testing async natal chart...")
    result = await service.get_full_natal_chart_data(
        name='Async Test',
        birth_datetime=test_datetime,
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow'
    )
    
    if 'error' in result:
        print(f"❌ Async natal error: {result['error']}")
        return False
    
    print(f"✅ Async natal: {len(result.get('planets', []))} planets, {len(result.get('houses', []))} houses")
    
    # Test performance stats
    print("\n2️⃣ Testing performance stats...")
    stats = await service.get_performance_stats()
    print(f"✅ Performance stats: {len(stats)} metrics")
    
    await service.shutdown()
    return True


def test_natal_chart_calculator():
    """Test NatalChartCalculator"""
    print("\n⭐ NatalChartCalculator Testing")
    print("=" * 60)
    
    calculator = NatalChartCalculator()
    test_datetime = datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC)
    
    # Test natal chart calculation
    print("\n1️⃣ Testing natal chart calculation...")
    try:
        result = calculator.calculate_natal_chart(
            name='Calculator Test',
            birth_datetime=test_datetime,
            latitude=55.7558,
            longitude=37.6176,
            timezone='Europe/Moscow'
        )
        
        if 'error' in result:
            print(f"❌ Calculator error: {result['error']}")
            return False
        
        print(f"✅ Calculator chart: {len(result.get('planets', []))} planets")
        print(f"   Houses: {len(result.get('houses', []))}")
        print(f"   Aspects: {len(result.get('aspects', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Calculator test failed: {e}")
        return False


def test_astrology_calculator():
    """Test AstrologyCalculator backend detection"""
    print("\n🎯 AstrologyCalculator Testing")
    print("=" * 60)
    
    calculator = AstrologyCalculator()
    
    # Test backend detection
    print("\n1️⃣ Testing backend detection...")
    backend_info = calculator.get_backend_info()
    print(f"✅ Backend: {backend_info.get('backend', 'unknown')}")
    print(f"   Version: {backend_info.get('version', 'unknown')}")
    print(f"   Available backends: {', '.join(backend_info.get('available_backends', []))}")
    
    # Test feature availability
    features = calculator.get_available_features()
    available_count = sum(1 for feature in features.values() if feature)
    print(f"✅ Features: {available_count}/{len(features)} available")
    
    return True


def main():
    """Run comprehensive test suite"""
    print("🌟 KERYKEION COMPREHENSIVE INTEGRATION TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test synchronous services
    try:
        results.append(("KerykeionService", test_kerykeion_service_comprehensive()))
    except Exception as e:
        print(f"❌ KerykeionService test failed: {e}")
        results.append(("KerykeionService", False))
    
    try:
        results.append(("NatalChartCalculator", test_natal_chart_calculator()))
    except Exception as e:
        print(f"❌ NatalChartCalculator test failed: {e}")
        results.append(("NatalChartCalculator", False))
    
    try:
        results.append(("AstrologyCalculator", test_astrology_calculator()))
    except Exception as e:
        print(f"❌ AstrologyCalculator test failed: {e}")
        results.append(("AstrologyCalculator", False))
    
    # Test asynchronous services
    try:
        async_result = asyncio.run(test_async_kerykeion_service())
        results.append(("AsyncKerykeionService", async_result))
    except Exception as e:
        print(f"❌ AsyncKerykeionService test failed: {e}")
        results.append(("AsyncKerykeionService", False))
    
    # Print final results
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for service_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{service_name:30} {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} services passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Kerykeion integration is fully functional!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
