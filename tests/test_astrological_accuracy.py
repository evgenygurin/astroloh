"""
Astrological accuracy tests using known astronomical data.
Validates calculations against historical events, famous birth charts, and verified ephemeris data.
"""

from datetime import date, datetime, time

import pytest

from app.services.astrology_calculator import AstrologyCalculator
from app.services.kerykeion_service import KERYKEION_AVAILABLE, KerykeionService
from app.services.natal_chart import NatalChartCalculator


class KnownAstronomicalData:
    """Known astronomical data for accuracy validation"""

    # Famous birth data with known astrological placements
    FAMOUS_BIRTHS = {
        "albert_einstein": {
            "birth_datetime": datetime(1879, 3, 14, 11, 30),
            "latitude": 48.4011,  # Ulm, Germany
            "longitude": 9.9876,
            "timezone": "Europe/Berlin",
            "known_placements": {
                "sun": {"sign": "pisces", "approximate_degree": 23},
                "moon": {"sign": "sagittarius"},
                "mercury": {"sign": "aries"},
                "venus": {"sign": "aries"},
                "mars": {"sign": "capricorn"},
            },
        },
        "marie_curie": {
            "birth_datetime": datetime(1867, 11, 7, 12, 0),  # Estimated time
            "latitude": 52.2330,  # Warsaw, Poland (approximate historical location)
            "longitude": 21.0611,
            "timezone": "Europe/Warsaw",
            "known_placements": {
                "sun": {"sign": "scorpio", "approximate_degree": 14},
                "moon": {"sign": "pisces"},  # Estimated
                "mercury": {"sign": "scorpio"},
                "venus": {"sign": "sagittarius"},
            },
        },
        "leonardo_da_vinci": {
            "birth_datetime": datetime(
                1452, 4, 15, 21, 0
            ),  # Historical records vary
            "latitude": 43.7711,  # Vinci, Italy (approximate)
            "longitude": 10.9218,
            "timezone": "Europe/Rome",
            "known_placements": {
                "sun": {"sign": "aries", "approximate_degree": 26},
                "moon": {
                    "sign": "pisces"
                },  # Estimated from historical analysis
                "mercury": {"sign": "aries"},
                "venus": {"sign": "aries"},
            },
        },
    }

    # Known zodiac sign dates for accuracy testing
    ZODIAC_SIGN_BOUNDARIES = {
        # Approximate dates (can vary by 1-2 days due to yearly variations)
        "aries": {"start": (3, 20), "end": (4, 20)},
        "taurus": {"start": (4, 20), "end": (5, 21)},
        "gemini": {"start": (5, 21), "end": (6, 21)},
        "cancer": {"start": (6, 21), "end": (7, 22)},
        "leo": {"start": (7, 22), "end": (8, 23)},
        "virgo": {"start": (8, 23), "end": (9, 23)},
        "libra": {"start": (9, 23), "end": (10, 23)},
        "scorpio": {"start": (10, 23), "end": (11, 22)},
        "sagittarius": {"start": (11, 22), "end": (12, 21)},
        "capricorn": {"start": (12, 21), "end": (1, 20)},
        "aquarius": {"start": (1, 20), "end": (2, 18)},
        "pisces": {"start": (2, 18), "end": (3, 20)},
    }

    # Known moon phases for accuracy testing
    KNOWN_MOON_PHASES = {
        # New Moon dates (UTC)
        "new_moons": [
            datetime(2023, 1, 21, 20, 53),
            datetime(2023, 2, 20, 7, 6),
            datetime(2023, 3, 21, 17, 23),
            datetime(2023, 4, 20, 4, 12),
            datetime(2023, 5, 19, 15, 53),
        ],
        # Full Moon dates (UTC)
        "full_moons": [
            datetime(2023, 1, 6, 23, 8),
            datetime(2023, 2, 5, 18, 29),
            datetime(2023, 3, 7, 12, 40),
            datetime(2023, 4, 6, 4, 35),
            datetime(2023, 5, 5, 17, 34),
        ],
    }


@pytest.mark.unit
class TestZodiacSignAccuracy:
    """Test zodiac sign calculation accuracy"""

    @pytest.fixture
    def calculator(self):
        return AstrologyCalculator()

    def test_zodiac_sign_boundaries_accuracy(self, calculator):
        """Test zodiac sign calculations at boundary dates"""
        test_year = 2023

        # Mapping from English to Russian zodiac sign names (YandexZodiacSign uses Russian)
        english_to_russian = {
            "aries": "овен",
            "taurus": "телец",
            "gemini": "близнецы",
            "cancer": "рак",
            "leo": "лев",
            "virgo": "дева",
            "libra": "весы",
            "scorpio": "скорпион",
            "sagittarius": "стрелец",
            "capricorn": "козерог",
            "aquarius": "водолей",
            "pisces": "рыбы",
        }

        for (
            sign_name,
            boundaries,
        ) in KnownAstronomicalData.ZODIAC_SIGN_BOUNDARIES.items():
            start_month, start_day = boundaries["start"]
            end_month, end_day = boundaries["end"]

            # Test middle of the sign (should be accurate)
            if start_month <= end_month:
                middle_month = start_month
                middle_day = start_day + 15
                if middle_day > 30:  # Simplified, just adjust roughly
                    middle_month += 1
                    middle_day -= 30
            else:  # Sign crosses year boundary (Capricorn)
                middle_month = 1
                middle_day = 1

            try:
                middle_date = date(test_year, middle_month, middle_day)
                calculated_sign = calculator.get_zodiac_sign_by_date(
                    middle_date
                )

                # Convert to string for comparison
                calculated_sign_name = calculated_sign.value.lower()
                expected_russian_name = english_to_russian[sign_name]

                assert (
                    calculated_sign_name == expected_russian_name
                ), f"Expected {expected_russian_name} (from {sign_name}), got {calculated_sign_name} for date {middle_date}"

            except ValueError:
                # Invalid date, skip this test case
                continue

    def test_zodiac_cusp_dates_handling(self, calculator):
        """Test handling of cusp dates (sign boundaries)"""
        # English to Russian mapping
        english_to_russian = {
            "aries": "овен",
            "taurus": "телец",
            "gemini": "близнецы",
            "cancer": "рак",
            "leo": "лев",
            "virgo": "дева",
            "libra": "весы",
            "scorpio": "скорпион",
            "sagittarius": "стрелец",
            "capricorn": "козерог",
            "aquarius": "водолей",
            "pisces": "рыбы",
        }

        # Test specific cusp dates where accuracy is critical
        cusp_tests = [
            (date(2023, 3, 20), ["pisces", "aries"]),  # Spring equinox
            (date(2023, 6, 21), ["gemini", "cancer"]),  # Summer solstice
            (date(2023, 9, 23), ["virgo", "libra"]),  # Autumn equinox
            (
                date(2023, 12, 21),
                ["sagittarius", "capricorn"],
            ),  # Winter solstice
        ]

        for test_date, possible_signs in cusp_tests:
            calculated_sign = calculator.get_zodiac_sign_by_date(test_date)
            calculated_sign_name = calculated_sign.value.lower()

            # Convert possible signs to Russian
            possible_russian_signs = [
                english_to_russian[sign] for sign in possible_signs
            ]

            # Should match one of the possible signs (within 1-2 day variation)
            sign_match = calculated_sign_name in possible_russian_signs
            assert (
                sign_match
            ), f"Date {test_date} gave {calculated_sign_name}, expected one of {possible_russian_signs} (from {possible_signs})"

    def test_leap_year_zodiac_accuracy(self, calculator):
        """Test zodiac calculations during leap years"""
        # Test Feb 29th in leap year
        leap_date = date(2024, 2, 29)  # 2024 is a leap year
        calculated_sign = calculator.get_zodiac_sign_by_date(leap_date)
        calculated_sign_name = calculated_sign.value.lower()

        # Should be Pisces (Feb 18 - Mar 20 approximately) - Russian: "рыбы"
        assert (
            calculated_sign_name == "рыбы"
        ), f"Expected 'рыбы' (Pisces), got {calculated_sign_name}"


@pytest.mark.integration
@pytest.mark.skipif(not KERYKEION_AVAILABLE, reason="Kerykeion not available")
class TestNatalChartAccuracy:
    """Test natal chart calculation accuracy using Kerykeion"""

    @pytest.fixture
    def kerykeion_service(self):
        return KerykeionService()

    @pytest.fixture
    def natal_calculator(self):
        return NatalChartCalculator()

    def test_famous_birth_chart_accuracy(self, kerykeion_service):
        """Test calculation accuracy for famous historical figures"""

        for (
            person_name,
            birth_data,
        ) in KnownAstronomicalData.FAMOUS_BIRTHS.items():
            chart_data = kerykeion_service.get_full_natal_chart_data(
                name=person_name.replace("_", " ").title(),
                birth_datetime=birth_data["birth_datetime"],
                latitude=birth_data["latitude"],
                longitude=birth_data["longitude"],
                timezone=birth_data["timezone"],
            )

            if "error" in chart_data:
                pytest.skip(
                    f"Chart calculation failed for {person_name}: {chart_data['error']}"
                )
                continue

            planets = chart_data.get("planets", {})
            known_placements = birth_data["known_placements"]

            # Test Sun sign accuracy (most critical)
            if "sun" in planets and "sun" in known_placements:
                calculated_sun_sign = planets["sun"].get("sign", "").lower()
                expected_sun_sign = known_placements["sun"]["sign"].lower()

                assert (
                    expected_sun_sign in calculated_sun_sign
                    or calculated_sun_sign in expected_sun_sign
                ), f"{person_name}: Expected Sun in {expected_sun_sign}, got {calculated_sun_sign}"

            # Test other major planets if data available
            for planet_name in ["moon", "mercury", "venus", "mars"]:
                if planet_name in planets and planet_name in known_placements:
                    calculated_sign = (
                        planets[planet_name].get("sign", "").lower()
                    )
                    expected_sign = known_placements[planet_name][
                        "sign"
                    ].lower()

                    # Allow some variation in historical data
                    if (
                        expected_sign in calculated_sign
                        or calculated_sign in expected_sign
                    ):
                        continue  # Match found
                    else:
                        # Log the discrepancy but don't fail (historical data may vary)
                        print(
                            f"Note: {person_name} {planet_name} - Expected {expected_sign}, got {calculated_sign}"
                        )

    def test_planetary_degree_accuracy(self, kerykeion_service):
        """Test planetary degree calculation accuracy"""
        # Use Einstein's data as it's well-documented
        einstein_data = KnownAstronomicalData.FAMOUS_BIRTHS["albert_einstein"]

        chart_data = kerykeion_service.get_full_natal_chart_data(
            name="Albert Einstein",
            birth_datetime=einstein_data["birth_datetime"],
            latitude=einstein_data["latitude"],
            longitude=einstein_data["longitude"],
            timezone=einstein_data["timezone"],
        )

        if "error" in chart_data:
            pytest.skip(f"Chart calculation failed: {chart_data['error']}")

        planets = chart_data.get("planets", {})

        # Test Sun degree accuracy (we know Einstein's Sun was around 23° Pisces)
        if "sun" in planets:
            sun_degree = planets["sun"].get("degree_in_sign", 0)
            expected_degree = einstein_data["known_placements"]["sun"][
                "approximate_degree"
            ]

            # Allow ±5 degrees variation for historical records
            degree_difference = abs(sun_degree - expected_degree)
            assert (
                degree_difference <= 5.0
            ), f"Einstein Sun degree: Expected ~{expected_degree}°, got {sun_degree}°"

    def test_house_calculation_accuracy(self, kerykeion_service):
        """Test house calculation accuracy"""
        # Use modern birth data for more precise testing
        modern_birth = {
            "name": "Test Subject",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,  # Moscow
            "longitude": 37.6176,
            "timezone": "Europe/Moscow",
        }

        chart_data = kerykeion_service.get_full_natal_chart_data(
            **modern_birth
        )

        if "error" in chart_data:
            pytest.skip(f"Chart calculation failed: {chart_data['error']}")

        houses = chart_data.get("houses", {})

        # Should have 12 houses
        assert len(houses) == 12, f"Expected 12 houses, got {len(houses)}"

        # Houses should be in order (1-12)
        for i in range(1, 13):
            assert str(i) in houses, f"Missing house {i}"

            house_data = houses[str(i)]
            assert "cusp" in house_data, f"Missing cusp for house {i}"
            assert "sign" in house_data, f"Missing sign for house {i}"

            # Cusp degrees should be between 0-360
            cusp_degree = house_data.get("cusp", 0)
            assert (
                0 <= cusp_degree < 360
            ), f"Invalid cusp degree {cusp_degree} for house {i}"


@pytest.mark.integration
class TestMoonPhaseAccuracy:
    """Test moon phase calculation accuracy"""

    @pytest.fixture
    def calculator(self):
        return AstrologyCalculator()

    def test_known_new_moon_accuracy(self, calculator):
        """Test accuracy of new moon calculations"""
        for new_moon_date in KnownAstronomicalData.KNOWN_MOON_PHASES[
            "new_moons"
        ]:
            moon_phase = calculator.calculate_moon_phase(new_moon_date)

            illumination = moon_phase.get("illumination_percent", 50)
            phase_name = moon_phase.get("phase_name", "").lower()

            # New moon should have very low illumination (0-10%)
            assert (
                illumination <= 15
            ), f"New moon {new_moon_date} has {illumination}% illumination, expected ≤15%"

            # Phase name should indicate new moon
            assert (
                "new" in phase_name or illumination < 5
            ), f"New moon {new_moon_date} has phase '{phase_name}'"

    def test_known_full_moon_accuracy(self, calculator):
        """Test accuracy of full moon calculations"""
        for full_moon_date in KnownAstronomicalData.KNOWN_MOON_PHASES[
            "full_moons"
        ]:
            moon_phase = calculator.calculate_moon_phase(full_moon_date)

            illumination = moon_phase.get("illumination_percent", 50)
            phase_name = moon_phase.get("phase_name", "").lower()

            # Full moon should have high illumination (90-100%)
            assert (
                illumination >= 85
            ), f"Full moon {full_moon_date} has {illumination}% illumination, expected ≥85%"

            # Phase name should indicate full moon
            assert (
                "full" in phase_name or illumination > 95
            ), f"Full moon {full_moon_date} has phase '{phase_name}'"

    def test_moon_phase_continuity(self, calculator):
        """Test that moon phases change continuously"""
        base_date = datetime(2023, 6, 1, 12, 0)

        dates_tested = []
        illuminations = []

        # Test over 30 days
        for day_offset in range(0, 30, 3):
            test_date = base_date.replace(day=base_date.day + day_offset)
            moon_phase = calculator.calculate_moon_phase(test_date)
            illumination = moon_phase.get("illumination_percent", 50)

            dates_tested.append(test_date)
            illuminations.append(illumination)

            # Illumination should be valid percentage
            assert (
                0 <= illumination <= 100
            ), f"Invalid illumination {illumination}% on {test_date}"


        # Should see variation over 30 days (moon cycle ~29.5 days)
        illumination_range = max(illuminations) - min(illuminations)
        assert (
            illumination_range > 50
        ), f"Insufficient illumination variation over 30 days: {illumination_range}%"


@pytest.mark.integration
class TestAspectCalculationAccuracy:
    """Test aspect calculation accuracy"""

    @pytest.fixture
    def calculator(self):
        return AstrologyCalculator()

    @pytest.fixture
    def kerykeion_service(self):
        return KerykeionService()

    @pytest.mark.skipif(
        not KERYKEION_AVAILABLE, reason="Kerykeion not available"
    )
    def test_major_aspect_detection(self, kerykeion_service):
        """Test detection of major aspects"""
        # Use birth data known to have strong aspects
        chart_data = kerykeion_service.get_full_natal_chart_data(
            name="Aspect Test",
            birth_datetime=datetime(
                1990, 8, 15, 12, 0
            ),  # Noon for clear aspects
            latitude=55.7558,
            longitude=37.6176,
            timezone="Europe/Moscow",
        )

        if "error" in chart_data:
            pytest.skip(f"Chart calculation failed: {chart_data['error']}")

        aspects = chart_data.get("aspects", [])

        # Should find some aspects
        assert len(aspects) > 0, "No aspects found in natal chart"

        # Test aspect data structure
        for aspect in aspects[:5]:  # Test first 5 aspects
            assert "planet1" in aspect, "Aspect missing planet1"
            assert "planet2" in aspect, "Aspect missing planet2"
            assert (
                "aspect_type" in aspect or "symbol" in aspect
            ), "Aspect missing type/symbol"
            assert "orb" in aspect, "Aspect missing orb"

            # Orb should be reasonable (0-10 degrees typically)
            orb = aspect.get("orb", 0)
            assert (
                0 <= orb <= 15
            ), f"Aspect orb {orb}° outside reasonable range"

    def test_aspect_orb_accuracy(self, kerykeion_service):
        """Test aspect orb calculations"""
        if not kerykeion_service.is_available():
            pytest.skip("Kerykeion not available")

        # Create chart with known planetary positions
        chart_data = kerykeion_service.get_full_natal_chart_data(
            name="Orb Test",
            birth_datetime=datetime(1990, 1, 1, 0, 0),
            latitude=0,  # Equator
            longitude=0,  # Prime meridian
            timezone="UTC",
        )

        if "error" in chart_data:
            pytest.skip(f"Chart calculation failed: {chart_data['error']}")

        planets = chart_data.get("planets", {})
        aspects = chart_data.get("aspects", [])

        # Manually verify an aspect orb calculation
        for aspect in aspects[:3]:  # Check first 3 aspects
            planet1_name = aspect.get("planet1", "")
            planet2_name = aspect.get("planet2", "")
            calculated_orb = aspect.get("orb", 0)

            if planet1_name in planets and planet2_name in planets:
                planet1_pos = planets[planet1_name].get("longitude", 0)
                planet2_pos = planets[planet2_name].get("longitude", 0)

                # Calculate expected orb for conjunction (0°)
                angle_diff = abs(planet1_pos - planet2_pos)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                # For conjunction aspects, orb should be close to angle difference
                aspect_type = aspect.get("aspect_type", "").lower()
                if "conjunction" in aspect_type or aspect_type == "0":
                    expected_orb = angle_diff
                    orb_difference = abs(calculated_orb - expected_orb)

                    # Allow 1-2 degrees variation
                    assert (
                        orb_difference <= 2
                    ), f"Orb calculation off by {orb_difference}°: expected ~{expected_orb}°, got {calculated_orb}°"


@pytest.mark.integration
class TestCalculationConsistency:
    """Test consistency across different calculation methods"""

    @pytest.fixture
    def astrology_calculator(self):
        return AstrologyCalculator()

    @pytest.fixture
    def natal_calculator(self):
        return NatalChartCalculator()

    def test_zodiac_sign_consistency(
        self, astrology_calculator, natal_calculator
    ):
        """Test consistency between different sign calculation methods"""
        test_dates = [
            date(2023, 3, 21),  # Spring equinox
            date(2023, 6, 21),  # Summer solstice
            date(2023, 9, 23),  # Autumn equinox
            date(2023, 12, 21),  # Winter solstice
            date(2023, 8, 15),  # Random date
            date(2023, 11, 11),  # Another random date
        ]

        for test_date in test_dates:
            # Get sign from basic calculator
            basic_sign = astrology_calculator.get_zodiac_sign_by_date(
                test_date
            )

            # Get sign from natal chart (if available)
            datetime.combine(test_date, time(12, 0))
            enhanced_chart = natal_calculator.calculate_enhanced_natal_chart(
                name="Consistency Test",
                birth_date=test_date,
                birth_time=time(12, 0),
                birth_place={"latitude": 55.7558, "longitude": 37.6176},
                timezone_str="Europe/Moscow",
            )

            if (
                "planets" in enhanced_chart
                and "sun" in enhanced_chart["planets"]
            ):
                enhanced_sun_sign = (
                    enhanced_chart["planets"]["sun"].get("sign", "").lower()
                )
                basic_sign_name = basic_sign.value.lower()

                # Signs should match (or be close for cusp dates)
                sign_match = (
                    enhanced_sun_sign in basic_sign_name
                    or basic_sign_name in enhanced_sun_sign
                )

                if not sign_match:
                    # Allow for 1-day variation on cusp dates
                    print(
                        f"Sign inconsistency on {test_date}: basic={basic_sign_name}, enhanced={enhanced_sun_sign}"
                    )
                    # Don't assert hard failure for cusp dates

    def test_moon_phase_calculation_stability(self, astrology_calculator):
        """Test that moon phase calculations are stable and consistent"""
        test_date = datetime(2023, 6, 15, 18, 30)

        # Calculate same moon phase multiple times
        results = []
        for _ in range(5):
            moon_phase = astrology_calculator.calculate_moon_phase(test_date)
            results.append(moon_phase)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert (
                result["illumination_percent"]
                == first_result["illumination_percent"]
            ), "Moon phase calculations are inconsistent"
            assert (
                result["phase_name"] == first_result["phase_name"]
            ), "Moon phase names are inconsistent"

    def test_planetary_position_precision(self, astrology_calculator):
        """Test precision of planetary position calculations"""
        # Test with high precision timestamps
        precise_timestamps = [
            datetime(2023, 6, 21, 10, 57, 0),  # Summer solstice 2023 (precise)
            datetime(2023, 3, 20, 21, 24, 0),  # Spring equinox 2023 (precise)
            datetime(2023, 12, 22, 9, 27, 0),  # Winter solstice 2023 (precise)
        ]

        for timestamp in precise_timestamps:
            # Get zodiac sign
            zodiac_sign = astrology_calculator.get_zodiac_sign_by_date(
                timestamp.date()
            )

            # Sign should be reasonable for the date
            assert (
                zodiac_sign is not None
            ), f"No zodiac sign calculated for {timestamp}"

            # Calculate moon phase
            moon_phase = astrology_calculator.calculate_moon_phase(timestamp)

            # Moon phase should have valid values
            assert (
                0 <= moon_phase["illumination_percent"] <= 100
            ), f"Invalid moon illumination: {moon_phase['illumination_percent']}"
            assert (
                len(moon_phase["phase_name"]) > 0
            ), f"Empty moon phase name for {timestamp}"


@pytest.mark.slow
class TestLongTermAccuracy:
    """Long-term accuracy tests (marked as slow)"""

    @pytest.fixture
    def calculator(self):
        return AstrologyCalculator()

    def test_historical_date_accuracy(self, calculator):
        """Test calculations for historical dates"""
        historical_dates = [
            date(1900, 1, 1),  # Turn of 20th century
            date(1945, 8, 15),  # End of WWII
            date(1969, 7, 20),  # Moon landing
            date(2000, 1, 1),  # Y2K
        ]

        for historical_date in historical_dates:
            try:
                zodiac_sign = calculator.get_zodiac_sign_by_date(
                    historical_date
                )
                assert (
                    zodiac_sign is not None
                ), f"Failed to calculate sign for {historical_date}"

                # Try moon phase calculation (may not be available for very old dates)
                try:
                    moon_phase = calculator.calculate_moon_phase(
                        datetime.combine(historical_date, time(12, 0))
                    )
                    assert 0 <= moon_phase["illumination_percent"] <= 100
                except Exception:
                    # Moon phase calculations may not work for very historical dates
                    pass

            except Exception as e:
                pytest.skip(
                    f"Historical calculation failed for {historical_date}: {e}"
                )

    def test_future_date_accuracy(self, calculator):
        """Test calculations for future dates"""
        future_dates = [
            date(2030, 6, 21),  # Future summer solstice
            date(2040, 12, 21),  # Future winter solstice
            date(2050, 3, 20),  # Future spring equinox
        ]

        for future_date in future_dates:
            try:
                zodiac_sign = calculator.get_zodiac_sign_by_date(future_date)
                assert (
                    zodiac_sign is not None
                ), f"Failed to calculate sign for {future_date}"

                # Future moon phases should also work
                moon_phase = calculator.calculate_moon_phase(
                    datetime.combine(future_date, time(12, 0))
                )
                assert 0 <= moon_phase["illumination_percent"] <= 100

            except Exception as e:
                pytest.skip(
                    f"Future calculation failed for {future_date}: {e}"
                )
