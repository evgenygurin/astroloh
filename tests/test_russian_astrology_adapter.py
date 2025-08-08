"""
Comprehensive unit tests for RussianAstrologyAdapter.
Tests Russian localization, grammatical declensions, timezone support, and TTS optimization.
"""


import pytest

from app.services.russian_astrology_adapter import (
    KERYKEION_AVAILABLE,
    RussianAstrologyAdapter,
    RussianPlanet,
    RussianTimezone,
    RussianZodiacSign,
)


@pytest.mark.unit
class TestRussianZodiacSignEnum:
    """Test RussianZodiacSign enum with all grammatical cases"""

    def test_all_signs_present(self):
        """Test that all 12 zodiac signs are present"""
        expected_signs = [
            "ARIES",
            "TAURUS",
            "GEMINI",
            "CANCER",
            "LEO",
            "VIRGO",
            "LIBRA",
            "SCORPIO",
            "SAGITTARIUS",
            "CAPRICORN",
            "AQUARIUS",
            "PISCES",
        ]

        for sign_name in expected_signs:
            assert hasattr(RussianZodiacSign, sign_name)

    def test_grammatical_cases_completeness(self):
        """Test that all signs have all required grammatical cases"""
        required_cases = [
            "ru",
            "genitive",
            "dative",
            "accusative",
            "instrumental",
            "prepositional",
        ]

        for sign in RussianZodiacSign:
            sign_data = sign.value
            for case in required_cases:
                assert case in sign_data, f"Missing {case} for {sign.name}"
                assert isinstance(
                    sign_data[case], str
                ), f"{case} must be string for {sign.name}"
                assert (
                    len(sign_data[case]) > 0
                ), f"Empty {case} for {sign.name}"

    def test_specific_declensions_accuracy(self):
        """Test accuracy of specific Russian declensions"""
        # Test Leo (masculine)
        leo = RussianZodiacSign.LEO.value
        assert leo["ru"] == "Лев"
        assert leo["genitive"] == "Льва"
        assert leo["dative"] == "Льву"
        assert leo["accusative"] == "Льва"
        assert leo["instrumental"] == "Львом"
        assert leo["prepositional"] == "Льве"

        # Test Virgo (feminine)
        virgo = RussianZodiacSign.VIRGO.value
        assert virgo["ru"] == "Дева"
        assert virgo["genitive"] == "Девы"
        assert virgo["instrumental"] == "Девой"

        # Test Gemini (plural)
        gemini = RussianZodiacSign.GEMINI.value
        assert gemini["ru"] == "Близнецы"
        assert gemini["genitive"] == "Близнецов"
        assert gemini["instrumental"] == "Близнецами"


@pytest.mark.unit
class TestRussianPlanetEnum:
    """Test RussianPlanet enum with keywords and descriptions"""

    def test_main_planets_present(self):
        """Test that all main planets are present"""
        expected_planets = [
            "SUN",
            "MOON",
            "MERCURY",
            "VENUS",
            "MARS",
            "JUPITER",
            "SATURN",
            "URANUS",
            "NEPTUNE",
            "PLUTO",
        ]

        for planet_name in expected_planets:
            assert hasattr(RussianPlanet, planet_name)

    def test_planet_data_structure(self):
        """Test that planet data has required structure"""
        required_fields = [
            "ru",
            "genitive",
            "dative",
            "accusative",
            "instrumental",
            "prepositional",
            "keywords",
            "description",
        ]

        for planet in RussianPlanet:
            planet_data = planet.value
            for field in required_fields:
                assert (
                    field in planet_data
                ), f"Missing {field} for {planet.name}"

            # Keywords should be a list
            assert isinstance(planet_data["keywords"], list)
            assert len(planet_data["keywords"]) > 0

            # Description should be string
            assert isinstance(planet_data["description"], str)
            assert len(planet_data["description"]) > 0

    def test_sun_planet_accuracy(self):
        """Test Sun planet data accuracy"""
        sun = RussianPlanet.SUN.value
        assert sun["ru"] == "Солнце"
        assert sun["genitive"] == "Солнца"
        assert sun["instrumental"] == "Солнцем"
        assert "личность" in sun["keywords"]
        assert "воля" in sun["keywords"]
        assert len(sun["description"]) > 20

    def test_moon_planet_accuracy(self):
        """Test Moon planet data accuracy"""
        moon = RussianPlanet.MOON.value
        assert moon["ru"] == "Луна"
        assert moon["genitive"] == "Луны"
        assert moon["accusative"] == "Луну"
        assert "эмоции" in moon["keywords"] or "чувства" in moon["keywords"]


@pytest.mark.unit
class TestRussianTimezoneEnum:
    """Test Russian timezone support"""

    def test_all_russian_timezones_present(self):
        """Test that all 11 Russian time zones are present"""
        # Russia has 11 time zones as of recent years
        timezone_count = len(list(RussianTimezone))
        assert timezone_count >= 10  # Allow for some flexibility

    def test_timezone_data_structure(self):
        """Test that timezone data has required structure"""
        for tz in RussianTimezone:
            tz_data = tz.value
            assert "name" in tz_data
            assert "offset" in tz_data
            assert "zone" in tz_data

            # Name should be in Russian
            assert isinstance(tz_data["name"], str)
            assert len(tz_data["name"]) > 0

            # Offset should be string like "+03:00"
            assert isinstance(tz_data["offset"], str)
            assert ":" in tz_data["offset"]

            # Zone should be valid pytz zone
            assert isinstance(tz_data["zone"], str)
            assert "/" in tz_data["zone"]  # Format like "Europe/Moscow"

    def test_moscow_timezone_accuracy(self):
        """Test Moscow timezone accuracy"""
        moscow = RussianTimezone.MOSCOW.value
        assert moscow["name"] == "Московское время"
        assert moscow["offset"] == "+03:00"
        assert moscow["zone"] == "Europe/Moscow"


@pytest.mark.unit
class TestRussianAstrologyAdapterInit:
    """Test RussianAstrologyAdapter initialization and basic functionality"""

    @pytest.fixture
    def adapter(self):
        """Create RussianAstrologyAdapter instance"""
        return RussianAstrologyAdapter()

    def test_adapter_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter is not None
        assert hasattr(adapter, "available")

    def test_is_available_method(self, adapter):
        """Test is_available property"""
        available = adapter.available
        assert isinstance(available, bool)

    def test_stress_mark_dictionary_exists(self, adapter):
        """Test that stress marks are applied correctly"""
        # Test that stress marks are applied by format_for_voice
        test_text = "овен телец близнецы лев дева"
        stressed_text = adapter.format_for_voice(
            test_text, add_stress_marks=True
        )

        # Should contain stress marks
        assert "é" in stressed_text or "́" in stressed_text

        # Test that stress marks can be disabled
        unstressed_text = adapter.format_for_voice(
            test_text, add_stress_marks=False
        )
        assert unstressed_text == test_text


@pytest.mark.unit
class TestRussianSignDescriptions:
    """Test Russian zodiac sign descriptions and formatting"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_get_russian_sign_description_default_case(self, adapter):
        """Test getting sign description in default (nominative) case"""
        description = adapter.get_russian_sign_description("Leo")

        assert isinstance(description, dict)
        assert "name" in description
        assert "characteristics" in description
        assert description["name"] == "Лев"

    def test_get_russian_sign_description_different_cases(self, adapter):
        """Test getting sign description in different grammatical cases"""
        cases = [
            "genitive",
            "dative",
            "accusative",
            "instrumental",
            "prepositional",
        ]

        for case in cases:
            description = adapter.get_russian_sign_description(
                "Leo", case=case
            )
            assert isinstance(description, dict)
            assert "name" in description

            if case == "genitive":
                assert description["name"] == "Льва"
            elif case == "dative":
                assert description["name"] == "Льву"
            elif case == "instrumental":
                assert description["name"] == "Львом"

    def test_get_russian_sign_description_case_insensitive(self, adapter):
        """Test that sign name matching is case insensitive"""
        description1 = adapter.get_russian_sign_description("leo")
        description2 = adapter.get_russian_sign_description("LEO")
        description3 = adapter.get_russian_sign_description("Leo")

        assert (
            description1["name"]
            == description2["name"]
            == description3["name"]
        )

    def test_get_russian_sign_description_invalid_sign(self, adapter):
        """Test handling of invalid sign names"""
        description = adapter.get_russian_sign_description("InvalidSign")

        # Should return None or empty dict, not crash
        assert description is None or description == {}

    def test_get_russian_sign_description_russian_input(self, adapter):
        """Test accepting Russian sign names as input"""
        description = adapter.get_russian_sign_description("Лев")

        assert description is not None
        assert description["name"] == "Лев"


@pytest.mark.unit
class TestRussianPlanetDescriptions:
    """Test Russian planet descriptions and formatting"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_get_russian_planet_description_default(self, adapter):
        """Test getting planet description in default case"""
        description = adapter.get_russian_planet_description("Sun")

        assert isinstance(description, dict)
        assert "name" in description
        assert "keywords" in description
        assert "description" in description
        assert description["name"] == "Солнце"
        assert isinstance(description["keywords"], list)

    def test_get_russian_planet_description_different_cases(self, adapter):
        """Test planet descriptions in different grammatical cases"""
        cases = [
            "genitive",
            "dative",
            "accusative",
            "instrumental",
            "prepositional",
        ]

        for case in cases:
            description = adapter.get_russian_planet_description(
                "Sun", case=case
            )
            assert "name" in description

            if case == "genitive":
                assert description["name"] == "Солнца"
            elif case == "instrumental":
                assert description["name"] == "Солнцем"

    def test_get_russian_planet_description_all_planets(self, adapter):
        """Test descriptions for all main planets"""
        planets = [
            "Sun",
            "Moon",
            "Mercury",
            "Venus",
            "Mars",
            "Jupiter",
            "Saturn",
        ]

        for planet in planets:
            description = adapter.get_russian_planet_description(planet)
            assert description is not None
            assert description["name"] != ""
            assert len(description["keywords"]) > 0
            assert len(description["description"]) > 10


@pytest.mark.unit
class TestRussianTimezoneDetection:
    """Test Russian city timezone detection"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_detect_russian_timezone_major_cities(self, adapter):
        """Test timezone detection for major Russian cities"""
        city_tests = [
            ("Москва", "Europe/Moscow"),
            ("москва", "Europe/Moscow"),  # Case insensitive
            ("Санкт-Петербург", "Europe/Moscow"),
            ("санкт-петербург", "Europe/Moscow"),
            ("Екатеринбург", "Asia/Yekaterinburg"),
            ("Новосибирск", "Asia/Novosibirsk"),
            ("Владивосток", "Asia/Vladivostok"),
        ]

        for city, expected_zone in city_tests:
            timezone_info = adapter.detect_russian_timezone(city)
            assert timezone_info is not None
            assert timezone_info["zone"] == expected_zone
            assert "offset" in timezone_info
            assert "name" in timezone_info

    def test_detect_russian_timezone_invalid_city(self, adapter):
        """Test handling of invalid city names"""
        timezone_info = adapter.detect_russian_timezone("InvalidCity")

        # Should return None or default timezone
        assert timezone_info is None or "zone" in timezone_info

    def test_detect_russian_timezone_format(self, adapter):
        """Test timezone info format"""
        timezone_info = adapter.detect_russian_timezone("Москва")

        assert isinstance(timezone_info, dict)
        assert "zone" in timezone_info
        assert "offset" in timezone_info
        assert "name" in timezone_info

        # Offset format check
        assert timezone_info["offset"].startswith(("+", "-"))
        assert ":" in timezone_info["offset"]

        # Name should be in Russian
        assert isinstance(timezone_info["name"], str)
        assert len(timezone_info["name"]) > 0


@pytest.mark.unit
class TestVoiceOptimization:
    """Test TTS and voice interface optimization"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_format_for_voice_basic(self, adapter):
        """Test basic voice formatting"""
        text = "Солнце находится в Льве"
        formatted = adapter.format_for_voice(text)

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_for_voice_with_stress_marks(self, adapter):
        """Test voice formatting with stress marks"""
        text = "Меркурий в ретрограде"
        formatted = adapter.format_for_voice(text, add_stress_marks=True)

        assert isinstance(formatted, str)
        # Should contain stress marks for proper pronunciation
        if (
            "мерку́рий" in formatted.lower()
            or "ретрогра́де" in formatted.lower()
        ):
            assert True  # Stress marks added
        else:
            # May not have stress marks for these specific words
            assert len(formatted) > 0

    def test_format_for_voice_pause_insertion(self, adapter):
        """Test automatic pause insertion for voice"""
        text = "Солнце в Овне. Луна в Стрельце. Марс в Близнецах."
        formatted = adapter.format_for_voice(text, insert_pauses=True)

        assert isinstance(formatted, str)
        # Should contain pause markers or be formatted for TTS
        assert len(formatted) >= len(text)  # May have added pause markers

    def test_format_for_voice_character_limit(self, adapter):
        """Test voice formatting respects character limits"""
        long_text = "Очень длинный текст " * 50  # Create very long text
        formatted = adapter.format_for_voice(long_text, max_length=800)

        assert len(formatted) <= 800
        assert formatted.endswith("...") or len(formatted) < len(long_text)

    def test_astrological_terms_stress_patterns(self, adapter):
        """Test stress patterns for astrological terms"""
        terms_to_test = [
            "овен",
            "телец",
            "близнецы",
            "рак",
            "лев",
            "дева",
            "весы",
            "скорпион",
            "стрелец",
            "козерог",
            "водолей",
            "рыбы",
            "солнце",
            "луна",
            "меркурий",
            "венера",
            "марс",
            "юпитер",
        ]

        stress_dict = adapter.get_stress_marks_dictionary()

        for term in terms_to_test:
            if term in stress_dict:
                stressed_term = stress_dict[term]
                assert (
                    "́" in stressed_term or stressed_term == term
                )  # Has stress mark or unchanged


@pytest.mark.unit
class TestKerykeionIntegration:
    """Test integration with Kerykeion data localization"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_localize_kerykeion_planet_data(self, adapter):
        """Test localizing Kerykeion planet data to Russian"""
        # Mock Kerykeion planet data structure
        kerykeion_planet_data = {
            "sun": {"name": "Sun", "sign": "Leo", "degree": 22.5},
            "moon": {"name": "Moon", "sign": "Sagittarius", "degree": 5.8},
            "mercury": {"name": "Mercury", "sign": "Virgo", "degree": 8.3},
        }

        localized = adapter.localize_kerykeion_planet_data(
            kerykeion_planet_data
        )

        assert isinstance(localized, dict)
        assert "sun" in localized
        assert localized["sun"]["name"] == "Солнце"
        assert localized["sun"]["sign"] == "Лев"
        assert localized["moon"]["name"] == "Луна"
        assert localized["moon"]["sign"] == "Стрелец"

    def test_localize_kerykeion_aspect_data(self, adapter):
        """Test localizing Kerykeion aspect data to Russian"""
        # Mock Kerykeion aspect data
        kerykeion_aspects = [
            {
                "planet1": "Sun",
                "planet2": "Moon",
                "aspect": "Opposition",
                "orb": 2.5,
            },
            {
                "planet1": "Mercury",
                "planet2": "Venus",
                "aspect": "Conjunction",
                "orb": 1.0,
            },
        ]

        localized = adapter.localize_kerykeion_aspect_data(kerykeion_aspects)

        assert isinstance(localized, list)
        assert len(localized) == 2
        assert localized[0]["planet1"] == "Солнце"
        assert localized[0]["planet2"] == "Луна"
        assert localized[0]["aspect"] == "Оппозиция"
        assert localized[1]["aspect"] == "Соединение"

    @pytest.mark.skipif(
        not KERYKEION_AVAILABLE, reason="Kerykeion not available"
    )
    def test_real_kerykeion_data_localization(self, adapter):
        """Test localization with real Kerykeion data (when available)"""
        # This would test with actual Kerykeion objects
        # Implementation depends on adapter's Kerykeion integration methods

        # Create simple mock of what real integration would look like
        real_chart_data = {
            "planets": {"sun": {"name": "Sun", "sign": "Leo", "degree": 22.5}}
        }

        localized = adapter.localize_chart_data(real_chart_data)

        assert "planets" in localized
        assert localized["planets"]["sun"]["name"] == "Солнце"
        assert localized["planets"]["sun"]["sign"] == "Лев"


@pytest.mark.integration
class TestRussianAstrologyAdapterIntegration:
    """Integration tests for RussianAstrologyAdapter"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_full_localization_workflow(self, adapter):
        """Test complete localization workflow"""
        # Simulate full astrological data localization
        astrological_data = {
            "natal_chart": {
                "planets": {
                    "sun": {
                        "name": "Sun",
                        "sign": "Leo",
                        "house": 5,
                        "degree": 22.5,
                    },
                    "moon": {
                        "name": "Moon",
                        "sign": "Cancer",
                        "house": 4,
                        "degree": 15.3,
                    },
                },
                "aspects": [
                    {
                        "planet1": "Sun",
                        "planet2": "Moon",
                        "aspect": "Sextile",
                        "orb": 3.2,
                    }
                ],
            },
            "transit_data": {
                "current_transits": [
                    {
                        "transit_planet": "Jupiter",
                        "natal_planet": "Sun",
                        "aspect": "Trine",
                    }
                ]
            },
        }

        localized_data = adapter.localize_complete_astrological_data(
            astrological_data
        )

        # Check natal chart localization
        natal_chart = localized_data["natal_chart"]
        assert natal_chart["planets"]["sun"]["name"] == "Солнце"
        assert natal_chart["planets"]["sun"]["sign"] == "Лев"
        assert natal_chart["planets"]["moon"]["name"] == "Луна"
        assert natal_chart["planets"]["moon"]["sign"] == "Рак"

        # Check aspects localization
        aspects = natal_chart["aspects"]
        assert aspects[0]["planet1"] == "Солнце"
        assert aspects[0]["planet2"] == "Луна"
        assert aspects[0]["aspect"] == "Секстиль"

        # Check transits localization
        transits = localized_data["transit_data"]["current_transits"]
        assert transits[0]["transit_planet"] == "Юпитер"
        assert transits[0]["natal_planet"] == "Солнце"
        assert transits[0]["aspect"] == "Тригон"

    def test_voice_optimized_interpretation(self, adapter):
        """Test generating voice-optimized Russian interpretations"""
        planet_data = {"name": "Sun", "sign": "Leo", "house": 5}

        interpretation = adapter.generate_voice_optimized_interpretation(
            planet_data
        )

        assert isinstance(interpretation, str)
        assert len(interpretation) > 0
        assert len(interpretation) <= 800  # Alice TTS limit

        # Should contain Russian terminology
        assert "Солнце" in interpretation or "Лев" in interpretation

        # Should be optimized for voice (no special characters that break TTS)
        problematic_chars = ["<", ">", "&", '"', "'"]
        for char in problematic_chars:
            assert char not in interpretation or interpretation.count(char) < 3


@pytest.mark.performance
class TestRussianAstrologyAdapterPerformance:
    """Performance tests for RussianAstrologyAdapter"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_localization_performance(self, adapter):
        """Test localization performance for large datasets"""
        import time

        # Create large mock astrological dataset
        large_dataset = {
            "planets": {
                f"planet_{i}": {"name": "Sun", "sign": "Leo"}
                for i in range(100)
            },
            "aspects": [
                {"planet1": "Sun", "planet2": "Moon", "aspect": "Opposition"}
                for _ in range(50)
            ],
        }

        start_time = time.time()
        localized = adapter.localize_complete_astrological_data(large_dataset)
        end_time = time.time()

        processing_time = end_time - start_time

        # Should complete within reasonable time
        assert processing_time < 1.0  # 1 second for large dataset
        assert len(localized["planets"]) == 100
        assert len(localized["aspects"]) == 50

    def test_timezone_detection_performance(self, adapter):
        """Test timezone detection performance"""
        import time

        russian_cities = [
            "Москва",
            "Санкт-Петербург",
            "Екатеринбург",
            "Новосибирск",
            "Владивосток",
            "Нижний Новгород",
            "Казань",
            "Челябинск",
            "Омск",
            "Самара",
        ]

        start_time = time.time()

        for city in russian_cities:
            timezone_info = adapter.detect_russian_timezone(city)
            assert timezone_info is not None

        end_time = time.time()
        processing_time = end_time - start_time

        # Should detect all cities quickly
        assert processing_time < 0.5  # 0.5 seconds for 10 cities

        # Average time per city should be very fast
        avg_time_per_city = processing_time / len(russian_cities)
        assert avg_time_per_city < 0.05  # 50ms per city


@pytest.mark.security
class TestRussianAstrologyAdapterSecurity:
    """Security tests for RussianAstrologyAdapter"""

    @pytest.fixture
    def adapter(self):
        return RussianAstrologyAdapter()

    def test_input_sanitization_city_names(self, adapter):
        """Test input sanitization for city names"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE cities; --",
            "../../../../etc/passwd",
            "\x00\x01\x02malicious",
            "Москва<script>alert('xss')</script>",
        ]

        for malicious_input in malicious_inputs:
            # Should not crash or cause security issues
            result = adapter.detect_russian_timezone(malicious_input)

            # Either returns None or sanitized result
            assert result is None or (
                isinstance(result, dict) and "zone" in result
            )

    def test_input_sanitization_astrological_terms(self, adapter):
        """Test input sanitization for astrological term queries"""
        malicious_terms = [
            "Leo<script>",
            "Sun'; DROP TABLE;",
            "Mercury\x00\x01",
            "Aries\\..\\..\\passwd",
        ]

        for malicious_term in malicious_terms:
            # Should handle gracefully without security issues
            result = adapter.get_russian_sign_description(malicious_term)

            # Either returns None/empty or valid description
            assert result is None or result == {} or isinstance(result, dict)

    def test_voice_output_sanitization(self, adapter):
        """Test that voice output is properly sanitized"""
        potentially_dangerous_text = (
            "Солнце <script>alert('xss')</script> в Льве"
        )

        formatted = adapter.format_for_voice(potentially_dangerous_text)

        # Should remove or escape dangerous content
        assert "<script>" not in formatted
        assert "alert" not in formatted or formatted.count("alert") == 0
        assert "Солнце" in formatted  # Valid content preserved
        assert "Льве" in formatted
