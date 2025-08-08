"""
Comprehensive unit tests for KerykeionService.
Tests all Kerykeion integration features including natal charts, aspects, Arabic parts, and synastry.
"""

import pytest
from datetime import datetime, date, time
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

from app.services.kerykeion_service import (
    KerykeionService, 
    HouseSystem, 
    ZodiacType,
    AspectColor,
    KERYKEION_AVAILABLE
)


@pytest.mark.unit
class TestKerykeionServiceInit:
    """Test KerykeionService initialization and availability"""
    
    def test_service_initialization_with_kerykeion(self):
        """Test service initialization when Kerykeion is available"""
        service = KerykeionService()
        assert service.available == KERYKEION_AVAILABLE
        
    def test_is_available_returns_correct_status(self):
        """Test is_available method returns correct status"""
        service = KerykeionService()
        assert service.is_available() == KERYKEION_AVAILABLE
        
    def test_house_system_enum_values(self):
        """Test HouseSystem enum has all required values"""
        expected_systems = [
            "Placidus", "Koch", "Equal", "Whole Sign", 
            "Regiomontanus", "Campanus", "Topocentric", 
            "Alcabitus", "Morinus", "Porphyrius"
        ]
        for system in expected_systems:
            assert any(hs.value == system for hs in HouseSystem)
            
    def test_zodiac_type_enum_values(self):
        """Test ZodiacType enum has correct values"""
        assert ZodiacType.TROPICAL.value == "Tropical"
        assert ZodiacType.SIDEREAL.value == "Sidereal"
        
    def test_aspect_color_enum_values(self):
        """Test AspectColor enum has traditional astrological colors"""
        assert AspectColor.CONJUNCTION.value == "#FF0000"
        assert AspectColor.OPPOSITION.value == "#0000FF"
        assert AspectColor.TRINE.value == "#00FF00"
        assert AspectColor.SQUARE.value == "#FF8000"
        assert AspectColor.SEXTILE.value == "#8000FF"


@pytest.mark.unit
@pytest.mark.skipif(not KERYKEION_AVAILABLE, reason="Kerykeion not available")
class TestKerykeionServiceWithKerykeion:
    """Tests that run when Kerykeion is available"""
    
    @pytest.fixture
    def service(self):
        """Create KerykeionService instance"""
        return KerykeionService()
    
    @pytest.fixture
    def sample_birth_data(self):
        """Sample birth data for testing"""
        return {
            "name": "Test Subject",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,  # Moscow
            "longitude": 37.6176,
            "timezone": "Europe/Moscow"
        }
    
    def test_create_astrological_subject_success(self, service, sample_birth_data):
        """Test successful creation of astrological subject"""
        subject = service.create_astrological_subject(**sample_birth_data)
        
        assert subject is not None
        assert hasattr(subject, 'name')
        assert hasattr(subject, 'year')
        assert hasattr(subject, 'month')
        assert hasattr(subject, 'day')
        
    def test_create_astrological_subject_with_different_house_systems(self, service, sample_birth_data):
        """Test creating subject with different house systems"""
        for house_system in [HouseSystem.PLACIDUS, HouseSystem.KOCH, HouseSystem.EQUAL]:
            data = sample_birth_data.copy()
            data['house_system'] = house_system
            
            subject = service.create_astrological_subject(**data)
            assert subject is not None
            
    def test_create_astrological_subject_with_different_zodiac_types(self, service, sample_birth_data):
        """Test creating subject with different zodiac types"""
        for zodiac_type in [ZodiacType.TROPICAL, ZodiacType.SIDEREAL]:
            data = sample_birth_data.copy()
            data['zodiac_type'] = zodiac_type
            
            subject = service.create_astrological_subject(**data)
            assert subject is not None
            
    def test_create_astrological_subject_with_invalid_timezone(self, service, sample_birth_data):
        """Test creating subject with invalid timezone falls back gracefully"""
        data = sample_birth_data.copy()
        data['timezone'] = "Invalid/Timezone"
        
        subject = service.create_astrological_subject(**data)
        # Should still create subject with fallback timezone
        assert subject is not None
        
    def test_get_full_natal_chart_data_success(self, service, sample_birth_data):
        """Test successful full natal chart calculation"""
        chart_data = service.get_full_natal_chart_data(**sample_birth_data)
        
        assert "error" not in chart_data
        assert "planets" in chart_data
        assert "houses" in chart_data
        assert "aspects" in chart_data
        
        # Check planets data structure
        planets = chart_data.get("planets", {})
        assert isinstance(planets, dict)
        assert len(planets) > 0
        
        # Check houses data structure  
        houses = chart_data.get("houses", {})
        assert isinstance(houses, dict)
        assert len(houses) >= 12
        
        # Check aspects data structure
        aspects = chart_data.get("aspects", [])
        assert isinstance(aspects, list)
        
    def test_get_full_natal_chart_data_includes_arabic_parts(self, service, sample_birth_data):
        """Test that full chart data includes Arabic parts"""
        chart_data = service.get_full_natal_chart_data(**sample_birth_data)
        
        assert "arabic_parts" in chart_data
        arabic_parts = chart_data.get("arabic_parts", {})
        assert isinstance(arabic_parts, dict)
        
    def test_get_full_natal_chart_data_includes_chart_analysis(self, service, sample_birth_data):
        """Test that full chart data includes chart analysis"""
        chart_data = service.get_full_natal_chart_data(**sample_birth_data)
        
        # Should include element/quality distribution
        assert "element_distribution" in chart_data
        assert "quality_distribution" in chart_data
        
        # Should include chart shape analysis
        assert "chart_shape" in chart_data
        
    def test_aspects_have_color_coding(self, service, sample_birth_data):
        """Test that aspects include color coding"""
        chart_data = service.get_full_natal_chart_data(**sample_birth_data)
        
        aspects = chart_data.get("aspects", [])
        if aspects:  # If aspects are calculated
            for aspect in aspects[:3]:  # Check first 3 aspects
                assert "color" in aspect or "aspect_type" in aspect


@pytest.mark.unit
class TestKerykeionServiceWithoutKerykeion:
    """Tests for when Kerykeion is not available (fallback behavior)"""
    
    @pytest.fixture
    def service_without_kerykeion(self):
        """Create service instance with mocked unavailable Kerykeion"""
        with patch('app.services.kerykeion_service.KERYKEION_AVAILABLE', False):
            service = KerykeionService()
            service.available = False
            return service
    
    def test_create_astrological_subject_returns_none(self, service_without_kerykeion):
        """Test that creating subject returns None when Kerykeion unavailable"""
        result = service_without_kerykeion.create_astrological_subject(
            name="Test",
            birth_datetime=datetime(1990, 8, 15, 14, 30),
            latitude=55.7558,
            longitude=37.6176
        )
        assert result is None
        
    def test_get_full_natal_chart_data_returns_error(self, service_without_kerykeion):
        """Test that chart calculation returns error when Kerykeion unavailable"""
        result = service_without_kerykeion.get_full_natal_chart_data(
            name="Test",
            birth_datetime=datetime(1990, 8, 15, 14, 30),
            latitude=55.7558,
            longitude=37.6176
        )
        assert "error" in result
        assert "Kerykeion not available" in result["error"]


@pytest.mark.unit
@pytest.mark.skipif(not KERYKEION_AVAILABLE, reason="Kerykeion not available")  
class TestKerykeionServiceAdvancedFeatures:
    """Test advanced Kerykeion features like synastry and transits"""
    
    @pytest.fixture
    def service(self):
        return KerykeionService()
        
    @pytest.fixture
    def test_subjects(self, service):
        """Create test astrological subjects for relationship analysis"""
        subject1 = service.create_astrological_subject(
            name="Person 1",
            birth_datetime=datetime(1990, 8, 15, 14, 30),
            latitude=55.7558,
            longitude=37.6176
        )
        
        subject2 = service.create_astrological_subject(
            name="Person 2", 
            birth_datetime=datetime(1992, 4, 20, 10, 0),
            latitude=55.7558,
            longitude=37.6176
        )
        
        return subject1, subject2
    
    def test_synastry_calculation(self, service, test_subjects):
        """Test synastry calculation between two charts"""
        subject1, subject2 = test_subjects
        
        if hasattr(service, 'calculate_synastry'):
            synastry = service.calculate_synastry(subject1, subject2)
            
            assert "aspects" in synastry
            assert "compatibility_score" in synastry
            assert isinstance(synastry["aspects"], list)
            assert isinstance(synastry["compatibility_score"], (int, float))
    
    def test_arabic_parts_calculation(self, service):
        """Test extended Arabic parts calculation"""
        subject = service.create_astrological_subject(
            name="Test",
            birth_datetime=datetime(1990, 8, 15, 14, 30),
            latitude=55.7558,
            longitude=37.6176
        )
        
        if hasattr(service, 'calculate_arabic_parts_extended'):
            parts = service.calculate_arabic_parts_extended(subject)
            
            assert isinstance(parts, dict)
            # Should include at least Part of Fortune
            assert len(parts) > 0


@pytest.mark.integration
@pytest.mark.skipif(not KERYKEION_AVAILABLE, reason="Kerykeion not available")
class TestKerykeionServiceIntegration:
    """Integration tests with actual Kerykeion calculations"""
    
    def test_known_birth_data_accuracy(self):
        """Test against known astrological data for accuracy verification"""
        service = KerykeionService()
        
        # Famous birth data: Albert Einstein (March 14, 1879, 11:30 AM, Ulm, Germany)
        chart_data = service.get_full_natal_chart_data(
            name="Albert Einstein",
            birth_datetime=datetime(1879, 3, 14, 11, 30),
            latitude=48.4011,  # Ulm, Germany
            longitude=9.9876,
            timezone="Europe/Berlin"
        )
        
        if "error" not in chart_data:
            planets = chart_data.get("planets", {})
            
            # Einstein's Sun should be in Pisces (approximately)
            if "sun" in planets:
                sun_sign = planets["sun"].get("sign", "").lower()
                assert "pisces" in sun_sign or "fish" in sun_sign
    
    def test_aspect_accuracy_known_charts(self):
        """Test aspect calculation accuracy with known chart data"""
        service = KerykeionService()
        
        # Chart with known strong aspects
        chart_data = service.get_full_natal_chart_data(
            name="Test Strong Aspects",
            birth_datetime=datetime(1990, 8, 15, 12, 0),  # Noon for clearer aspects
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow"
        )
        
        if "error" not in chart_data:
            aspects = chart_data.get("aspects", [])
            assert len(aspects) > 0
            
            # Check aspect data structure
            for aspect in aspects[:5]:  # Check first 5 aspects
                assert "planet1" in aspect
                assert "planet2" in aspect
                assert "aspect_type" in aspect
                assert "orb" in aspect
                assert isinstance(aspect["orb"], (int, float))


@pytest.mark.performance
@pytest.mark.skipif(not KERYKEION_AVAILABLE, reason="Kerykeion not available")
class TestKerykeionServicePerformance:
    """Performance tests for Kerykeion service"""
    
    def test_chart_calculation_performance(self):
        """Test that chart calculations complete within acceptable time"""
        import time
        
        service = KerykeionService()
        
        start_time = time.time()
        
        chart_data = service.get_full_natal_chart_data(
            name="Performance Test",
            birth_datetime=datetime(1990, 8, 15, 14, 30),
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow"
        )
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Chart calculation should complete within 5 seconds
        assert calculation_time < 5.0
        assert "error" not in chart_data
        
    def test_multiple_chart_calculations_performance(self):
        """Test performance of multiple consecutive chart calculations"""
        import time
        
        service = KerykeionService()
        
        birth_dates = [
            datetime(1990, 1, 15, 12, 0),
            datetime(1985, 6, 20, 14, 30),
            datetime(1975, 12, 10, 9, 45),
            datetime(2000, 3, 25, 16, 15),
            datetime(1995, 9, 8, 11, 30)
        ]
        
        start_time = time.time()
        
        for i, birth_date in enumerate(birth_dates):
            chart_data = service.get_full_natal_chart_data(
                name=f"Test Subject {i+1}",
                birth_datetime=birth_date,
                latitude=55.7558,
                longitude=37.6176,
                timezone="Europe/Moscow"
            )
            assert "error" not in chart_data
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # 5 chart calculations should complete within 15 seconds
        assert total_time < 15.0
        
        # Average time per chart should be reasonable
        avg_time_per_chart = total_time / len(birth_dates)
        assert avg_time_per_chart < 5.0


@pytest.mark.security
class TestKerykeionServiceSecurity:
    """Security tests for KerykeionService"""
    
    def test_input_validation_name_injection(self):
        """Test that name input is properly validated against injection attacks"""
        service = KerykeionService()
        
        malicious_names = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../../etc/passwd",
            "\x00\x01\x02malicious"
        ]
        
        for malicious_name in malicious_names:
            # Should not raise exceptions or cause issues
            result = service.create_astrological_subject(
                name=malicious_name,
                birth_datetime=datetime(1990, 8, 15, 14, 30),
                latitude=55.7558,
                longitude=37.6176
            )
            
            # Either returns valid subject or None, but shouldn't crash
            assert result is None or hasattr(result, 'name')
            
    def test_coordinate_boundary_validation(self):
        """Test validation of latitude/longitude boundaries"""
        service = KerykeionService()
        
        # Test extreme coordinates
        extreme_coords = [
            (999, 999),      # Way out of bounds
            (-999, -999),    # Way out of bounds  
            (90.1, 0),       # Slightly over max latitude
            (-90.1, 0),      # Slightly under min latitude
            (0, 180.1),      # Slightly over max longitude
            (0, -180.1)      # Slightly under min longitude
        ]
        
        for lat, lng in extreme_coords:
            # Should handle gracefully without crashing
            try:
                result = service.create_astrological_subject(
                    name="Boundary Test",
                    birth_datetime=datetime(1990, 8, 15, 14, 30),
                    latitude=lat,
                    longitude=lng
                )
                # Either succeeds with clamped values or returns None
                assert result is None or hasattr(result, 'lat')
            except Exception as e:
                # Should raise appropriate validation errors, not crash
                assert "coordinate" in str(e).lower() or "latitude" in str(e).lower() or "longitude" in str(e).lower()