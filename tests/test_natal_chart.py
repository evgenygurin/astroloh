"""
Tests for natal chart calculation functionality.
"""
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch

from app.services.natal_chart import NatalChartCalculator
from app.models.yandex_models import YandexZodiacSign


class TestNatalChartCalculator:
    """Tests for natal chart calculator."""
    
    def setup_method(self):
        """Setup before each test."""
        self.natal_chart = NatalChartCalculator()
    
    def test_calculate_natal_chart_basic(self):
        """Test basic natal chart calculation."""
        birth_date = datetime(1990, 5, 15, 14, 30)  # May 15, 1990, 2:30 PM
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}  # Moscow
        
        chart = self.natal_chart.calculate_natal_chart(
            birth_date, birth_location
        )
        
        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert "chart_signature" in chart
        
        # Check that we have all major planets
        expected_planets = ["sun", "moon", "mercury", "venus", "mars", 
                          "jupiter", "saturn", "uranus", "neptune", "pluto"]
        for planet in expected_planets:
            assert planet in chart["planets"]
    
    def test_calculate_natal_chart_with_interpretation(self):
        """Test natal chart calculation with interpretation."""
        birth_date = datetime(1985, 12, 25, 10, 0)  # Christmas, morning
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}
        
        chart = self.natal_chart.calculate_natal_chart(
            birth_date, birth_location, include_interpretation=True
        )
        
        assert "interpretation" in chart
        assert "personality" in chart["interpretation"]
        assert "relationships" in chart["interpretation"]
        assert "career" in chart["interpretation"]
        assert "growth_areas" in chart["interpretation"]
    
    def test_calculate_planet_positions(self):
        """Test planet position calculations."""
        birth_date = datetime(1990, 5, 15, 14, 30)
        
        positions = self.natal_chart.calculate_planet_positions(birth_date)
        
        assert isinstance(positions, dict)
        assert len(positions) >= 10  # Major planets
        
        for planet, data in positions.items():
            assert "longitude" in data
            assert "sign" in data
            assert "house" in data
            assert 0 <= data["longitude"] < 360
            assert data["sign"] in [sign.value for sign in YandexZodiacSign]
            assert 1 <= data["house"] <= 12
    
    def test_calculate_houses(self):
        """Test house calculations."""
        birth_date = datetime(1990, 5, 15, 14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}
        
        houses = self.natal_chart.calculate_houses(birth_date, birth_location)
        
        assert isinstance(houses, dict)
        assert len(houses) == 12
        
        for house_num in range(1, 13):
            assert str(house_num) in houses
            house_data = houses[str(house_num)]
            assert "cusp" in house_data
            assert "sign" in house_data
            assert 0 <= house_data["cusp"] < 360
    
    def test_calculate_aspects(self):
        """Test aspect calculations."""
        planet_positions = {
            "sun": {"longitude": 54.5},      # Taurus
            "moon": {"longitude": 124.5},    # Leo (70° from Sun - sextile)
            "mercury": {"longitude": 64.5},  # Gemini (10° from Sun - conjunction)
            "venus": {"longitude": 234.5},   # Scorpio (180° from Sun - opposition)
            "mars": {"longitude": 144.5}     # Leo (90° from Sun - square)
        }
        
        aspects = self.natal_chart.calculate_aspects(planet_positions)
        
        assert isinstance(aspects, list)
        assert len(aspects) > 0
        
        # Check for expected aspects
        aspect_types = [aspect["type"] for aspect in aspects]
        assert "conjunction" in aspect_types  # Sun-Mercury
        assert "opposition" in aspect_types   # Sun-Venus
        assert "square" in aspect_types       # Sun-Mars
    
    def test_get_chart_signature(self):
        """Test chart signature calculation."""
        planet_positions = {
            "sun": {"sign": "taurus"},      # Earth
            "moon": {"sign": "leo"},       # Fire
            "mercury": {"sign": "gemini"}, # Air
            "venus": {"sign": "taurus"},   # Earth
            "mars": {"sign": "leo"}        # Fire
        }
        
        signature = self.natal_chart.get_chart_signature(planet_positions)
        
        assert "dominant_element" in signature
        assert "dominant_quality" in signature
        assert "element_distribution" in signature
        assert "quality_distribution" in signature
        
        # Should have calculated distributions
        assert isinstance(signature["element_distribution"], dict)
        assert isinstance(signature["quality_distribution"], dict)
    
    def test_interpret_personality(self):
        """Test personality interpretation."""
        chart_data = {
            "planets": {
                "sun": {"sign": "leo", "house": 1},
                "moon": {"sign": "cancer", "house": 12},
                "mercury": {"sign": "virgo", "house": 2}
            },
            "chart_signature": {
                "dominant_element": "fire",
                "dominant_quality": "fixed"
            }
        }
        
        interpretation = self.natal_chart.interpret_personality(chart_data)
        
        assert isinstance(interpretation, str)
        assert len(interpretation) > 50  # Should be a substantial interpretation
        assert "лев" in interpretation.lower() or "leo" in interpretation.lower()
    
    def test_interpret_relationships(self):
        """Test relationship interpretation."""
        chart_data = {
            "planets": {
                "venus": {"sign": "libra", "house": 7},
                "mars": {"sign": "scorpio", "house": 8},
                "moon": {"sign": "pisces", "house": 5}
            }
        }
        
        interpretation = self.natal_chart.interpret_relationships(chart_data)
        
        assert isinstance(interpretation, str)
        assert len(interpretation) > 30
        assert "отношени" in interpretation.lower() or "relationship" in interpretation.lower()
    
    def test_interpret_career(self):
        """Test career interpretation."""
        chart_data = {
            "planets": {
                "sun": {"sign": "capricorn", "house": 10},
                "mercury": {"sign": "capricorn", "house": 10},
                "mars": {"sign": "aries", "house": 6}
            }
        }
        
        interpretation = self.natal_chart.interpret_career(chart_data)
        
        assert isinstance(interpretation, str)
        assert len(interpretation) > 30
        assert "карьер" in interpretation.lower() or "career" in interpretation.lower()
    
    def test_calculate_planetary_strengths(self):
        """Test planetary strength calculations."""
        planet_positions = {
            "sun": {"sign": "leo", "house": 1},      # Domicile + Angular house
            "moon": {"sign": "cancer", "house": 4},  # Domicile + Angular house
            "mercury": {"sign": "pisces", "house": 8}, # Detriment + Succedent house
            "venus": {"sign": "taurus", "house": 2}   # Domicile + Succedent house
        }
        
        strengths = self.natal_chart.calculate_planetary_strengths(planet_positions)
        
        assert isinstance(strengths, dict)
        assert "sun" in strengths
        assert "moon" in strengths
        
        # Sun in Leo (domicile) should be stronger than Mercury in Pisces (detriment)
        assert strengths["sun"] > strengths["mercury"]
    
    def test_get_house_meanings(self):
        """Test house meaning interpretations."""
        for house_num in range(1, 13):
            meaning = self.natal_chart.get_house_meaning(house_num)
            assert isinstance(meaning, str)
            assert len(meaning) > 10
    
    def test_get_aspect_meaning(self):
        """Test aspect meaning interpretations."""
        aspect_types = ["conjunction", "opposition", "square", "trine", "sextile"]
        
        for aspect_type in aspect_types:
            meaning = self.natal_chart.get_aspect_meaning(aspect_type)
            assert isinstance(meaning, str)
            assert len(meaning) > 10
    
    def test_calculate_natal_chart_different_locations(self):
        """Test natal chart calculation for different locations."""
        birth_date = datetime(1990, 5, 15, 14, 30)
        
        # Moscow
        moscow_location = {"latitude": 55.7558, "longitude": 37.6176}
        moscow_chart = self.natal_chart.calculate_natal_chart(birth_date, moscow_location)
        
        # New York
        ny_location = {"latitude": 40.7128, "longitude": -74.0060}
        ny_chart = self.natal_chart.calculate_natal_chart(birth_date, ny_location)
        
        # Houses should be different due to different locations
        assert moscow_chart["houses"] != ny_chart["houses"]
        
        # But planet signs should be the same (approximately, depending on exact time)
        moscow_sun_sign = moscow_chart["planets"]["sun"]["sign"]
        ny_sun_sign = ny_chart["planets"]["sun"]["sign"]
        assert moscow_sun_sign == ny_sun_sign  # Same day, so same Sun sign
    
    def test_validate_birth_data(self):
        """Test birth data validation."""
        # Valid data
        valid_date = datetime(1990, 5, 15, 14, 30)
        valid_location = {"latitude": 55.7558, "longitude": 37.6176}
        
        assert self.natal_chart.validate_birth_data(valid_date, valid_location)
        
        # Invalid latitude
        invalid_location = {"latitude": 95, "longitude": 37.6176}
        assert not self.natal_chart.validate_birth_data(valid_date, invalid_location)
        
        # Invalid longitude
        invalid_location = {"latitude": 55.7558, "longitude": 185}
        assert not self.natal_chart.validate_birth_data(valid_date, invalid_location)
        
        # Future date
        future_date = datetime(2050, 1, 1)
        assert not self.natal_chart.validate_birth_data(future_date, valid_location)
    
    def test_calculate_chart_summary(self):
        """Test chart summary generation."""
        chart = {
            "planets": {
                "sun": {"sign": "taurus", "house": 2},
                "moon": {"sign": "scorpio", "house": 8}
            },
            "chart_signature": {
                "dominant_element": "earth",
                "dominant_quality": "fixed"
            }
        }
        
        summary = self.natal_chart.calculate_chart_summary(chart)
        
        assert isinstance(summary, dict)
        assert "dominant_traits" in summary
        assert "key_strengths" in summary
        assert "potential_challenges" in summary
        assert "life_purpose" in summary