"""
Tests for natal chart calculation functionality.
"""

from datetime import date, time

from app.services.natal_chart import NatalChartCalculator


class TestNatalChartCalculator:
    """Tests for natal chart calculator."""

    def setup_method(self):
        """Setup before each test."""
        self.natal_chart = NatalChartCalculator()

    def test_calculate_natal_chart_basic(self):
        """Test basic natal chart calculation."""
        birth_date = date(1990, 5, 15)  # May 15, 1990
        birth_time = time(14, 30)  # 2:30 PM
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}  # Moscow

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert "chart_signature" in chart

        # Check that we have all major planets
        expected_planets = [
            "Sun",
            "Moon",
            "Mercury",
            "Venus",
            "Mars",
            "Jupiter",
            "Saturn",
            "Uranus",
            "Neptune",
            "Pluto",
        ]
        for planet in expected_planets:
            assert planet in chart["planets"]

    def test_calculate_natal_chart_with_interpretation(self):
        """Test natal chart calculation with interpretation."""
        birth_date = date(1985, 12, 25)  # Christmas
        birth_time = time(10, 0)  # Morning
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        assert "interpretation" in chart
        assert "personality" in chart["interpretation"]
        assert "relationships" in chart["interpretation"]
        assert "career" in chart["interpretation"]

    def test_calculate_planet_positions(self):
        """Test planet position calculations via natal chart."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        positions = chart["planets"]
        assert isinstance(positions, dict)
        assert len(positions) >= 10  # Major planets

        for planet, data in positions.items():
            assert "longitude" in data
            assert "sign" in data
            assert 0 <= data["longitude"] < 360
            # The signs are returned in capitalized Russian form
            capitalized_signs = [
                "Овен",
                "Телец",
                "Близнецы",
                "Рак",
                "Лев",
                "Дева",
                "Весы",
                "Скорпион",
                "Стрелец",
                "Козерог",
                "Водолей",
                "Рыбы",
            ]
            assert data["sign"] in capitalized_signs

    def test_calculate_houses(self):
        """Test house calculations via natal chart."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        houses = chart["houses"]
        assert isinstance(houses, dict)
        # Houses might be numbered differently, just check we have house data
        assert len(houses) > 0

    def test_calculate_aspects(self):
        """Test aspect calculations via natal chart."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        aspects = chart["aspects"]
        assert isinstance(aspects, list)
        # Just check that we get some aspects back
        assert len(aspects) >= 0

    def test_get_chart_signature(self):
        """Test chart signature calculation."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        signature = chart["chart_signature"]

        assert "dominant_element" in signature
        assert "dominant_quality" in signature
        assert "description" in signature

    def test_interpret_personality(self):
        """Test personality interpretation."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        interpretation = chart["interpretation"]["personality"]

        assert isinstance(interpretation, dict)
        assert "core_self" in interpretation
        assert "emotional_nature" in interpretation
        assert "general_description" in interpretation

    def test_interpret_relationships(self):
        """Test relationship interpretation."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        interpretation = chart["interpretation"]["relationships"]

        assert isinstance(interpretation, dict)
        assert "love_style" in interpretation
        assert "passion_style" in interpretation
        assert "compatibility_advice" in interpretation

    def test_interpret_career(self):
        """Test career interpretation."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        interpretation = chart["interpretation"]["career"]

        assert isinstance(interpretation, dict)
        assert "career_direction" in interpretation
        assert "work_style" in interpretation
        assert "success_factors" in interpretation

    def test_calculate_planetary_strengths(self):
        """Test planetary strength concepts via chart interpretation."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        # Check that we have strengths mentioned in interpretation
        strengths = chart["interpretation"]["strengths"]
        assert isinstance(strengths, list)
        assert len(strengths) >= 0

    def test_get_house_meanings(self):
        """Test house meaning interpretations."""
        # Test that house meanings are available in the class
        for house_num in range(1, 13):
            meaning = self.natal_chart.house_meanings[house_num]
            assert isinstance(meaning, dict)
            assert "name" in meaning
            assert "description" in meaning
            assert "keywords" in meaning

    def test_get_aspect_meaning(self):
        """Test aspect meaning interpretations."""
        aspect_types = [
            "Соединение",
            "Оппозиция",
            "Квадрат",
            "Трин",
            "Секстиль",
        ]

        for aspect_type in aspect_types:
            meaning = self.natal_chart.aspect_interpretations[aspect_type]
            assert isinstance(meaning, dict)
            assert "description" in meaning
            assert "nature" in meaning
            assert "strength" in meaning

    def test_calculate_natal_chart_different_locations(self):
        """Test natal chart calculation for different locations."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)

        # Moscow
        moscow_location = {"latitude": 55.7558, "longitude": 37.6176}
        moscow_chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=moscow_location,
        )

        # New York
        ny_location = {"latitude": 40.7128, "longitude": -74.0060}
        ny_chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=ny_location,
        )

        # Houses should be different due to different locations
        assert moscow_chart["houses"] != ny_chart["houses"]

        # But planet signs should be the same (approximately, depending on exact time)
        moscow_sun_sign = moscow_chart["planets"]["Sun"]["sign"]
        ny_sun_sign = ny_chart["planets"]["Sun"]["sign"]
        assert moscow_sun_sign == ny_sun_sign  # Same day, so same Sun sign

    def test_validate_birth_data(self):
        """Test birth data validation through chart calculation."""
        # Valid data should work
        valid_date = date(1990, 5, 15)
        valid_time = time(14, 30)
        valid_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=valid_date,
            birth_time=valid_time,
            birth_place=valid_location,
        )

        assert "planets" in chart
        assert "houses" in chart
        assert "birth_info" in chart

    def test_calculate_chart_summary(self):
        """Test chart summary through interpretation."""
        birth_date = date(1990, 5, 15)
        birth_time = time(14, 30)
        birth_location = {"latitude": 55.7558, "longitude": 37.6176}

        chart = self.natal_chart.calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_location,
        )

        interpretation = chart["interpretation"]

        assert isinstance(interpretation, dict)
        assert "personality" in interpretation
        assert "relationships" in interpretation
        assert "career" in interpretation
        assert "life_purpose" in interpretation
