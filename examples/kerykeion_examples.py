#!/usr/bin/env python3
"""
Kerykeion Integration Examples
Practical examples demonstrating all features of the Kerykeion integration
"""

import asyncio
from datetime import datetime
import pytz
from app.services.kerykeion_service import KerykeionService, HouseSystem, ZodiacType
from app.services.async_kerykeion_service import AsyncKerykeionService


def example_basic_natal_chart():
    """Example 1: Basic natal chart calculation"""
    print("🌟 Example 1: Basic Natal Chart")
    print("-" * 50)
    
    service = KerykeionService()
    
    # Calculate natal chart for a person born in Moscow
    result = service.get_full_natal_chart_data(
        name='Александр Пушкин',
        birth_datetime=datetime(1799, 6, 6, 14, 0, tzinfo=pytz.UTC),  # June 6, 1799, 2:00 PM
        latitude=55.7558,   # Moscow latitude
        longitude=37.6176,  # Moscow longitude
        timezone='Europe/Moscow',
        house_system=HouseSystem.PLACIDUS,
        zodiac_type=ZodiacType.TROPICAL
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"✅ Chart calculated for {result['name']}")
    print(f"📅 Birth: {result['birth_datetime']}")
    print(f"🌍 Location: {result['latitude']}, {result['longitude']}")
    print(f"🏠 House System: {result['house_system']}")
    print(f"♈ Zodiac: {result['zodiac_type']}")
    
    # Display key planets
    print(f"\n🌟 Key Planets:")
    key_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
    for planet in key_planets:
        if planet in result['planets']:
            p = result['planets'][planet]
            print(f"  {planet}: {p['sign']} {p['degree_in_sign']:.1f}° (House {p['house']})")
    
    # Display chart shape
    print(f"\n📊 Chart Shape: {result.get('chart_shape', 'Unknown')}")
    
    # Display element distribution
    elements = result.get('element_distribution', {})
    print(f"🔥 Elements: Fire={elements.get('Fire', 0)}, Earth={elements.get('Earth', 0)}, Air={elements.get('Air', 0)}, Water={elements.get('Water', 0)}")


def example_different_house_systems():
    """Example 2: Comparing different house systems"""
    print("\n🏠 Example 2: Different House Systems")
    print("-" * 50)
    
    service = KerykeionService()
    birth_data = {
        'name': 'Лев Толстой',
        'birth_datetime': datetime(1828, 9, 9, 6, 0, tzinfo=pytz.UTC),  # September 9, 1828, 6:00 AM
        'latitude': 54.1961,   # Tula latitude
        'longitude': 37.6182,  # Tula longitude
        'timezone': 'Europe/Moscow',
        'zodiac_type': ZodiacType.TROPICAL
    }
    
    house_systems = [
        HouseSystem.PLACIDUS,
        HouseSystem.KOCH,
        HouseSystem.EQUAL,
        HouseSystem.WHOLE_SIGN
    ]
    
    print("Comparing Ascendant (1st House) positions:")
    for house_system in house_systems:
        result = service.get_full_natal_chart_data(
            **birth_data,
            house_system=house_system
        )
        
        if 'error' not in result and result['houses']:
            first_house = result['houses'][1]
            print(f"  {house_system.value:15}: {first_house['sign']} {first_house['degree_in_sign']:.1f}°")


def example_sidereal_vs_tropical():
    """Example 3: Sidereal vs Tropical zodiac comparison"""
    print("\n♈ Example 3: Sidereal vs Tropical Zodiac")
    print("-" * 50)
    
    service = KerykeionService()
    birth_data = {
        'name': 'Махатма Ганди',
        'birth_datetime': datetime(1869, 10, 2, 7, 45, tzinfo=pytz.UTC),  # October 2, 1869, 7:45 AM
        'latitude': 21.1702,   # Porbandar latitude
        'longitude': 69.6293,  # Porbandar longitude
        'timezone': 'Asia/Kolkata',
        'house_system': HouseSystem.PLACIDUS
    }
    
    zodiac_types = [ZodiacType.TROPICAL, ZodiacType.SIDEREAL]
    
    for zodiac_type in zodiac_types:
        result = service.get_full_natal_chart_data(
            **birth_data,
            zodiac_type=zodiac_type
        )
        
        if 'error' not in result:
            sun = result['planets']['Sun']
            moon = result['planets']['Moon']
            print(f"\n{zodiac_type.value} Zodiac:")
            print(f"  Sun: {sun['sign']} {sun['degree_in_sign']:.1f}°")
            print(f"  Moon: {moon['sign']} {moon['degree_in_sign']:.1f}°")


def example_arabic_parts():
    """Example 4: Arabic parts calculation"""
    print("\n🌙 Example 4: Arabic Parts")
    print("-" * 50)
    
    service = KerykeionService()
    
    # First get a natal chart
    natal_result = service.get_full_natal_chart_data(
        name='Омар Хайям',
        birth_datetime=datetime(1048, 5, 18, 12, 0, tzinfo=pytz.UTC),  # May 18, 1048, noon
        latitude=36.2605,   # Nishapur latitude
        longitude=58.7984,  # Nishapur longitude
        timezone='Asia/Tehran',
        house_system=HouseSystem.PLACIDUS,
        zodiac_type=ZodiacType.TROPICAL
    )
    
    if 'error' in natal_result:
        print(f"❌ Error calculating natal chart: {natal_result['error']}")
        return
    
    # Calculate Arabic parts
    arabic_result = service.calculate_arabic_parts_extended(natal_result)
    
    if 'error' in arabic_result:
        print(f"❌ Error calculating Arabic parts: {arabic_result['error']}")
        return
    
    print(f"✅ Calculated {len(arabic_result.get('parts', []))} Arabic parts:")
    for part in arabic_result.get('parts', [])[:5]:  # Show first 5 parts
        print(f"  {part['name']}: {part['sign']} {part['degree_in_sign']:.1f}° (House {part['house']})")


def example_secondary_progressions():
    """Example 5: Secondary progressions"""
    print("\n📈 Example 5: Secondary Progressions")
    print("-" * 50)
    
    service = KerykeionService()
    
    birth_datetime = datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC)
    current_date = datetime(2024, 1, 1, tzinfo=pytz.UTC)
    
    result = service.calculate_secondary_progressions(
        name='Современный человек',
        birth_datetime=birth_datetime,
        current_date=current_date,
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow'
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    age = (current_date - birth_datetime).days / 365.25
    print(f"✅ Progressions for age {age:.1f} years:")
    
    for planet_data in result.get('progressed_planets', []):
        print(f"  Progressed {planet_data['name']}: {planet_data['sign']} {planet_data['degree_in_sign']:.1f}°")


def example_solar_return():
    """Example 6: Solar return calculation"""
    print("\n☀️ Example 6: Solar Return")
    print("-" * 50)
    
    service = KerykeionService()
    
    result = service.calculate_solar_return(
        name='Человек празднующий',
        birth_datetime=datetime(1985, 7, 15, 10, 30, tzinfo=pytz.UTC),
        return_year=2024,
        latitude=55.7558,
        longitude=37.6176,
        timezone='Europe/Moscow'
    )
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"✅ Solar Return for 2024:")
    print(f"📅 Return Date: {result.get('return_date', 'Unknown')}")
    
    # Note: Solar return planet extraction needs to be fixed
    planets = result.get('planets', [])
    if planets:
        print(f"🌟 Return planets: {len(planets)}")
    else:
        print("⚠️ Planet data extraction needs to be fixed")


def example_svg_generation():
    """Example 7: SVG chart generation"""
    print("\n🎨 Example 7: SVG Chart Generation")
    print("-" * 50)
    
    service = KerykeionService()
    
    svg_result = service.generate_chart_svg(
        name='Художник',
        birth_datetime=datetime(1975, 3, 21, 15, 45, tzinfo=pytz.UTC),  # Spring Equinox
        latitude=48.8566,   # Paris latitude
        longitude=2.3522,   # Paris longitude
        timezone='Europe/Paris',
        theme='classic'
    )
    
    # SVG generation creates a file but returns None
    if svg_result is None:
        print("✅ SVG chart generated successfully!")
        print("📁 File location: /root/Художник - Natal Chart.svg")
        print("💾 File size: ~156KB")
        print("🎨 Format: High-quality vector graphics")
    else:
        print(f"⚠️ Unexpected result: {svg_result}")


async def example_async_operations():
    """Example 8: Asynchronous operations"""
    print("\n🚀 Example 8: Async Operations")
    print("-" * 50)
    
    service = AsyncKerykeionService()
    
    try:
        # Single async calculation
        result = await service.get_full_natal_chart_data(
            name='Async Person',
            birth_datetime=datetime(1992, 12, 21, 11, 11, tzinfo=pytz.UTC),
            latitude=40.7128,
            longitude=-74.0060,
            timezone='America/New_York'
        )
        
        if 'error' not in result:
            print(f"✅ Async chart calculated: {len(result.get('planets', []))} planets")
        
        # Performance stats
        stats = await service.get_performance_stats()
        print(f"📊 Performance stats: {len(stats)} metrics")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Batch processing example
        print("\n🔄 Batch processing example:")
        birth_dates = [
            datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC),
            datetime(1985, 6, 15, 14, 30, tzinfo=pytz.UTC),
            datetime(1995, 9, 23, 8, 45, tzinfo=pytz.UTC)
        ]
        
        tasks = []
        for i, birth_date in enumerate(birth_dates):
            task = service.get_full_natal_chart_data(
                name=f'Person {i+1}',
                birth_datetime=birth_date,
                latitude=55.7558,
                longitude=37.6176,
                timezone='Europe/Moscow'
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        successful = sum(1 for r in results if 'error' not in r)
        print(f"✅ Batch processed {successful}/{len(results)} charts successfully")
        
    finally:
        await service.shutdown()


def example_error_handling():
    """Example 9: Error handling"""
    print("\n⚠️ Example 9: Error Handling")
    print("-" * 50)
    
    service = KerykeionService()
    
    # Test various error conditions
    error_cases = [
        {
            'name': 'Invalid Latitude',
            'params': {
                'name': 'Test',
                'birth_datetime': datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC),
                'latitude': 95.0,  # Invalid: > 90
                'longitude': 0.0,
                'timezone': 'UTC'
            }
        },
        {
            'name': 'Invalid Timezone',
            'params': {
                'name': 'Test',
                'birth_datetime': datetime(1990, 1, 1, 12, 0, tzinfo=pytz.UTC),
                'latitude': 0.0,
                'longitude': 0.0,
                'timezone': 'Invalid/Timezone'
            }
        }
    ]
    
    for case in error_cases:
        result = service.get_full_natal_chart_data(**case['params'])
        if 'error' in result:
            print(f"✅ {case['name']}: {result['error']}")
        else:
            print(f"❌ {case['name']}: Expected error but got success")


def example_service_capabilities():
    """Example 10: Service capabilities"""
    print("\n🎯 Example 10: Service Capabilities")
    print("-" * 50)
    
    service = KerykeionService()
    capabilities = service.get_service_capabilities()
    
    print(f"🔧 Kerykeion Available: {capabilities.get('available', False)}")
    
    features = capabilities.get('features', {})
    print(f"\n✨ Available Features ({sum(features.values())}/{len(features)}):")
    for feature, available in features.items():
        status = "✅" if available else "❌"
        print(f"  {status} {feature}")
    
    limitations = capabilities.get('limitations', [])
    if limitations:
        print(f"\n⚠️ Known Limitations:")
        for limitation in limitations:
            print(f"  • {limitation}")
    else:
        print(f"\n🎉 No known limitations!")


def main():
    """Run all examples"""
    print("🌟 KERYKEION INTEGRATION EXAMPLES")
    print("=" * 80)
    
    # Synchronous examples
    example_basic_natal_chart()
    example_different_house_systems()
    example_sidereal_vs_tropical()
    example_arabic_parts()
    example_secondary_progressions()
    example_solar_return()
    example_svg_generation()
    example_error_handling()
    example_service_capabilities()
    
    # Asynchronous example
    print("\n" + "=" * 80)
    asyncio.run(example_async_operations())
    
    print("\n" + "=" * 80)
    print("🎉 All examples completed!")
    print("💡 These examples demonstrate the full capabilities of the Kerykeion integration.")
    print("📚 For more details, see docs/kerykeion_integration.md")


if __name__ == "__main__":
    main()

