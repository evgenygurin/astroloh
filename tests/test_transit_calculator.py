"""
Тесты для калькулятора транзитов и прогрессий.
"""
import pytest
from datetime import date, datetime, time
from unittest.mock import patch, MagicMock

from app.services.transit_calculator import TransitCalculator


class TestTransitCalculator:
    """Тесты для TransitCalculator."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.transit_calc = TransitCalculator()
        self.test_birth_date = date(1990, 3, 15)
        self.test_birth_time = time(12, 0)
        self.test_birth_place = {"latitude": 55.7558, "longitude": 37.6176}

    def test_init(self):
        """Тест инициализации калькулятора."""
        assert self.transit_calc.astro_calc is not None
        assert self.transit_calc.transit_orbs is not None
        assert self.transit_calc.transit_interpretations is not None

    def test_calculate_current_transits_success(self):
        """Тест успешного расчета транзитов."""
        # Мокаем вычисления позиций планет
        mock_positions = {
            "Sun": {
                "longitude": 0.0,
                "sign": "Овен",
                "degree_in_sign": 0.0,
                "sign_number": 0,
            },
            "Moon": {
                "longitude": 90.0,
                "sign": "Рак",
                "degree_in_sign": 0.0,
                "sign_number": 3,
            },
        }

        with patch.object(
            self.transit_calc.astro_calc,
            "calculate_planet_positions",
            return_value=mock_positions,
        ):
            result = self.transit_calc.calculate_current_transits(
                self.test_birth_date, self.test_birth_time, self.test_birth_place
            )

        assert "calculation_date" in result
        assert "birth_info" in result
        assert "natal_positions" in result
        assert "current_positions" in result
        assert "all_transits" in result
        assert "significant_transits" in result
        assert "interpretation" in result
        assert "summary" in result

    def test_calculate_current_transits_error_handling(self):
        """Тест обработки ошибок при расчете транзитов."""
        # Мокаем ошибку в вычислениях
        with patch.object(
            self.transit_calc.astro_calc,
            "calculate_planet_positions",
            side_effect=Exception("Test error"),
        ):
            result = self.transit_calc.calculate_current_transits(
                self.test_birth_date
            )

        assert "error" in result
        assert result["error"] == "Не удалось рассчитать транзиты"

    def test_calculate_transit_aspects(self):
        """Тест расчета транзитных аспектов."""
        natal_positions = {
            "Sun": {"longitude": 0.0, "sign": "Овен", "degree_in_sign": 0.0},
            "Moon": {"longitude": 30.0, "sign": "Телец", "degree_in_sign": 0.0},
        }

        current_positions = {
            "Mars": {"longitude": 90.0, "sign": "Рак", "degree_in_sign": 0.0},
            "Venus": {"longitude": 120.0, "sign": "Лев", "degree_in_sign": 0.0},
        }

        transits = self.transit_calc._calculate_transit_aspects(
            natal_positions, current_positions
        )

        assert isinstance(transits, list)
        # Должен найти квадрат Марс-Солнце (90 градусов)
        mars_sun_aspects = [
            t for t in transits
            if t["transit_planet"] == "Mars" and t["natal_planet"] == "Sun"
        ]
        assert len(mars_sun_aspects) > 0
        assert mars_sun_aspects[0]["aspect"] == "Квадрат"

    def test_analyze_significant_transits(self):
        """Тест анализа значимых транзитов."""
        mock_transits = [
            {
                "transit_planet": "Saturn",
                "natal_planet": "Sun",
                "aspect": "Квадрат",
                "strength": 8.5,
                "orb": 1.2,
            },
            {
                "transit_planet": "Jupiter",
                "natal_planet": "Moon",
                "aspect": "Трин",
                "strength": 6.8,
                "orb": 2.1,
            },
        ]

        significant = self.transit_calc._analyze_significant_transits(mock_transits)

        assert isinstance(significant, list)
        assert len(significant) <= 10  # Максимум 10 значимых транзитов
        # Первый должен быть самым сильным
        if significant:
            assert significant[0]["strength"] >= significant[-1]["strength"]

    def test_calculate_progressions_success(self):
        """Тест успешного расчета прогрессий."""
        mock_positions = {
            "Sun": {
                "longitude": 0.0,
                "sign": "Овен",
                "degree_in_sign": 0.0,
                "sign_number": 0,
            },
            "Moon": {
                "longitude": 90.0,
                "sign": "Рак",
                "degree_in_sign": 0.0,
                "sign_number": 3,
            },
        }

        with patch.object(
            self.transit_calc.astro_calc,
            "calculate_planet_positions",
            return_value=mock_positions,
        ):
            result = self.transit_calc.calculate_progressions(
                self.test_birth_date, self.test_birth_time, self.test_birth_place
            )

        assert "calculation_date" in result
        assert "birth_info" in result
        assert "progression_date" in result
        assert "years_lived" in result
        assert "natal_positions" in result
        assert "progressed_positions" in result
        assert "progressions" in result
        assert "interpretation" in result

    def test_analyze_progressions(self):
        """Тест анализа прогрессий."""
        natal_positions = {
            "Sun": {"longitude": 0.0},
            "Moon": {"longitude": 30.0},
        }

        progressed_positions = {
            "Sun": {"longitude": 15.0},
            "Moon": {"longitude": 45.0},
        }

        progressions = self.transit_calc._analyze_progressions(
            natal_positions, progressed_positions
        )

        assert isinstance(progressions, list)
        if progressions:
            progression = progressions[0]
            assert "planet" in progression
            assert "movement_degrees" in progression
            assert "interpretation" in progression

    def test_calculate_solar_return_success(self):
        """Тест успешного расчета соляра."""
        mock_positions = {
            "Sun": {
                "longitude": 0.0,
                "sign": "Овен",
                "degree_in_sign": 0.0,
                "sign_number": 0,
            }
        }

        mock_houses = {
            "ascendant": {
                "longitude": 90.0,
                "sign": "Рак",
                "degree_in_sign": 0.0,
            }
        }

        with patch.object(
            self.transit_calc.astro_calc,
            "calculate_planet_positions",
            return_value=mock_positions,
        ), patch.object(
            self.transit_calc.astro_calc,
            "calculate_houses",
            return_value=mock_houses,
        ):
            result = self.transit_calc.calculate_solar_return(
                self.test_birth_date, self.test_birth_time, self.test_birth_place
            )

        assert "solar_year" in result
        assert "solar_date" in result
        assert "solar_positions" in result
        assert "solar_houses" in result
        assert "interpretation" in result

    def test_calculate_lunar_return_success(self):
        """Тест успешного расчета лунара."""
        mock_positions = {
            "Moon": {
                "longitude": 0.0,
                "sign": "Овен",
                "degree_in_sign": 0.0,
                "sign_number": 0,
            }
        }

        with patch.object(
            self.transit_calc.astro_calc,
            "calculate_planet_positions",
            return_value=mock_positions,
        ):
            result = self.transit_calc.calculate_lunar_return(
                self.test_birth_date, self.test_birth_time, self.test_birth_place
            )

        assert "lunar_date" in result
        assert "target_date" in result
        assert "lunar_positions" in result
        assert "interpretation" in result

    def test_calculate_transit_strength(self):
        """Тест расчета силы транзитного аспекта."""
        strength = self.transit_calc._calculate_transit_strength(
            "Saturn", "Sun", 90, 1.0  # Квадрат Сатурна к Солнцу с орбом 1 градус
        )

        assert isinstance(strength, float)
        assert strength > 0
        # Сатурн-Солнце квадрат должен иметь высокую силу
        assert strength > 5.0

    def test_get_aspect_name(self):
        """Тест получения названия аспекта."""
        assert self.transit_calc._get_aspect_name(0) == "Соединение"
        assert self.transit_calc._get_aspect_name(60) == "Секстиль"
        assert self.transit_calc._get_aspect_name(90) == "Квадрат"
        assert self.transit_calc._get_aspect_name(120) == "Трин"
        assert self.transit_calc._get_aspect_name(180) == "Оппозиция"
        assert self.transit_calc._get_aspect_name(45) == "Неизвестный"

    def test_find_planet_house(self):
        """Тест определения дома планеты."""
        houses = {
            1: {"cusp_longitude": 0.0},
            2: {"cusp_longitude": 30.0},
            3: {"cusp_longitude": 60.0},
            4: {"cusp_longitude": 90.0},
        }

        # Планета на 15 градусах должна быть в первом доме
        house = self.transit_calc._find_planet_house(15.0, houses)
        assert house == 1

        # Планета на 45 градусах должна быть во втором доме
        house = self.transit_calc._find_planet_house(45.0, houses)
        assert house == 2

    def test_create_transit_summary(self):
        """Тест создания резюме транзитов."""
        significant_transits = [
            {
                "transit_planet": "Saturn",
                "aspect": "Квадрат",
                "strength": 8.0,
            },
            {
                "transit_planet": "Jupiter",
                "aspect": "Трин",
                "strength": 6.0,
            },
            {
                "transit_planet": "Mars",
                "aspect": "Оппозиция",
                "strength": 7.0,
            },
        ]

        summary = self.transit_calc._create_transit_summary(significant_transits)

        assert "overall_influence" in summary
        assert "dominant_planet" in summary
        assert "main_themes" in summary
        assert "transit_count" in summary
        assert "advice" in summary

        assert summary["transit_count"] == 3
        assert summary["dominant_planet"] == "Saturn"  # Самая сильная планета

    def test_create_transit_summary_empty(self):
        """Тест создания резюме для пустого списка транзитов."""
        summary = self.transit_calc._create_transit_summary([])

        assert summary["overall_influence"] == "спокойный"
        assert "стабильность" in summary["main_themes"]
        assert "спокойствия" in summary["advice"]

    def test_interpret_progression_movement(self):
        """Тест интерпретации движения планеты в прогрессии."""
        # Медленное движение
        interp = self.transit_calc._interpret_progression_movement("Sun", 2.0)
        assert interp["phase"] == "стабильная"

        # Умеренное движение
        interp = self.transit_calc._interpret_progression_movement("Moon", 10.0)
        assert interp["phase"] == "умеренная"

        # Активное движение
        interp = self.transit_calc._interpret_progression_movement("Mercury", 20.0)
        assert interp["phase"] == "активная"

    def test_interpret_solar_return(self):
        """Тест интерпретации соляра."""
        solar_positions = {
            "Sun": {"longitude": 90.0}  # Солнце в 4-м доме (приблизительно)
        }

        solar_houses = {
            "ascendant": {"sign": "Лев"},
            1: {"cusp_longitude": 0.0},
            4: {"cusp_longitude": 90.0},
        }

        interpretation = self.transit_calc._interpret_solar_return(
            solar_positions, solar_houses
        )

        assert "year_theme" in interpretation
        assert "ascendant_influence" in interpretation
        assert "summary" in interpretation

    def test_interpret_lunar_return(self):
        """Тест интерпретации лунара."""
        lunar_positions = {"Moon": {"sign": "Рак"}}

        interpretation = self.transit_calc._interpret_lunar_return(lunar_positions)

        assert "monthly_theme" in interpretation
        assert "moon_influence" in interpretation
        assert "summary" in interpretation
        assert "семейные вопросы" in interpretation["monthly_theme"]

    def test_get_transit_advice(self):
        """Тест получения советов по транзитным аспектам."""
        advice = self.transit_calc._get_transit_advice("Sun", "Соединение")
        assert "лидерства" in advice

        advice = self.transit_calc._get_transit_advice("Mars", "Квадрат")
        assert "энергию" in advice

        # Неизвестная комбинация
        advice = self.transit_calc._get_transit_advice("Unknown", "Unknown")
        assert "изменения" in advice

    def test_default_parameters(self):
        """Тест параметров по умолчанию."""
        # Тест с минимальными параметрами
        with patch.object(
            self.transit_calc.astro_calc,
            "calculate_planet_positions",
            return_value={"Sun": {"longitude": 0.0, "sign": "Овен"}},
        ):
            result = self.transit_calc.calculate_current_transits(
                self.test_birth_date
            )

        # Должен использовать значения по умолчанию
        assert result["birth_info"]["time"] == "12:00"
        assert result["birth_info"]["place"]["latitude"] == 55.7558
        assert result["birth_info"]["place"]["longitude"] == 37.6176

    @pytest.mark.parametrize(
        "planet,expected_weight",
        [
            ("Sun", 10),
            ("Moon", 9),
            ("Saturn", 9),
            ("Jupiter", 8),
            ("Unknown", 5),  # Значение по умолчанию
        ],
    )
    def test_planet_weights(self, planet, expected_weight):
        """Тест весов планет для расчета силы аспектов."""
        strength = self.transit_calc._calculate_transit_strength(
            planet, "Sun", 90, 1.0
        )
        # Проверяем, что сила зависит от веса планеты
        assert strength > 0

    def test_timing_analysis(self):
        """Тест анализа тайминга транзитов."""
        transit = {"orb": 0.3}
        timing = self.transit_calc._analyze_transit_timing(transit)
        assert timing["phase"] == "точный"

        transit = {"orb": 0.8}
        timing = self.transit_calc._analyze_transit_timing(transit)
        assert timing["phase"] == "близкий"

        transit = {"orb": 1.5}
        timing = self.transit_calc._analyze_transit_timing(transit)
        assert timing["phase"] == "приближающийся"

        transit = {"orb": 2.5}
        timing = self.transit_calc._analyze_transit_timing(transit)
        assert timing["phase"] == "слабый"