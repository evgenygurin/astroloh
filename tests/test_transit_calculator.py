"""
Тесты для сервиса расчета транзитов.
"""

import pytest
from datetime import date, datetime
from unittest.mock import patch

from app.services.transit_calculator import TransitCalculator


class TestTransitCalculator:
    """Тесты для калькулятора транзитов."""

    def setup_method(self):
        """Настройка для каждого теста."""
        self.transit_calc = TransitCalculator()

        # Мок натальных планет для тестирования
        self.mock_natal_planets = {
            "Sun": {"longitude": 120.5, "sign": "Лев", "degree_in_sign": 0.5},
            "Moon": {"longitude": 45.2, "sign": "Телец", "degree_in_sign": 15.2},
            "Mercury": {"longitude": 95.8, "sign": "Рак", "degree_in_sign": 5.8},
            "Venus": {"longitude": 200.1, "sign": "Весы", "degree_in_sign": 20.1},
            "Mars": {"longitude": 310.7, "sign": "Водолей", "degree_in_sign": 10.7},
        }

    @pytest.mark.unit
    def test_init(self):
        """Тест инициализации."""
        assert self.transit_calc.astro_calc is not None
        assert isinstance(self.transit_calc.transit_orbs, dict)
        assert isinstance(self.transit_calc.planet_speeds, dict)
        assert len(self.transit_calc.transit_orbs) == 5  # 5 main aspects

    @pytest.mark.unit
    def test_calculate_current_transits_basic(self):
        """Тест базового расчета транзитов."""
        with patch.object(
            self.transit_calc.astro_calc, "calculate_planet_positions"
        ) as mock_positions:
            # Мок текущих позиций планет
            mock_positions.return_value = {
                "Sun": {"longitude": 125.0, "sign": "Лев", "degree_in_sign": 5.0},
                "Jupiter": {"longitude": 120.0, "sign": "Лев", "degree_in_sign": 0.0},
                "Saturn": {"longitude": 45.0, "sign": "Телец", "degree_in_sign": 15.0},
            }

            result = self.transit_calc.calculate_current_transits(
                self.mock_natal_planets
            )

            assert "date" in result
            assert "active_transits" in result
            assert "approaching_transits" in result
            assert "summary" in result
            assert "daily_influences" in result
            assert isinstance(result["active_transits"], list)
            assert isinstance(result["approaching_transits"], list)

    @pytest.mark.unit
    def test_calculate_transit_aspects(self):
        """Тест расчета транзитных аспектов."""
        transit_data = {"longitude": 120.0, "sign": "Лев"}
        natal_data = {"longitude": 120.5, "sign": "Лев"}

        aspects = self.transit_calc._calculate_transit_aspects(
            transit_data, natal_data, "Jupiter", "Sun"
        )

        assert isinstance(aspects, list)
        if aspects:  # Если найдены аспекты
            aspect = aspects[0]
            assert "transit_planet" in aspect
            assert "natal_planet" in aspect
            assert "aspect" in aspect
            assert "orb" in aspect
            assert "influence" in aspect
            assert "strength" in aspect
            assert "nature" in aspect

    @pytest.mark.unit
    def test_get_aspect_name(self):
        """Тест получения названия аспекта."""
        assert self.transit_calc._get_aspect_name(0) == "Соединение"
        assert self.transit_calc._get_aspect_name(60) == "Секстиль"
        assert self.transit_calc._get_aspect_name(90) == "Квадрат"
        assert self.transit_calc._get_aspect_name(120) == "Трин"
        assert self.transit_calc._get_aspect_name(180) == "Оппозиция"
        assert self.transit_calc._get_aspect_name(999) == "Неизвестный"

    @pytest.mark.unit
    def test_get_aspect_nature(self):
        """Тест определения природы аспекта."""
        assert self.transit_calc._get_aspect_nature("Соединение") == "усиление"
        assert self.transit_calc._get_aspect_nature("Трин") == "поток"
        assert self.transit_calc._get_aspect_nature("Квадрат") == "напряжение"
        assert self.transit_calc._get_aspect_nature("Оппозиция") == "противостояние"
        assert self.transit_calc._get_aspect_nature("Неизвестный") == "нейтральный"

    @pytest.mark.unit
    def test_calculate_aspect_strength(self):
        """Тест расчета силы аспекта."""
        assert self.transit_calc._calculate_aspect_strength(0.5, 0) == "очень сильный"
        assert self.transit_calc._calculate_aspect_strength(2.0, 90) == "сильный"
        assert self.transit_calc._calculate_aspect_strength(4.0, 120) == "умеренный"
        assert self.transit_calc._calculate_aspect_strength(7.0, 60) == "слабый"

    @pytest.mark.unit
    def test_get_transit_influence(self):
        """Тест получения влияния транзита."""
        # Тест прямого сочетания
        influence = self.transit_calc._get_transit_influence("Sun", "Sun", "Соединение")
        assert isinstance(influence, str)
        assert len(influence) > 0

        # Тест общих влияний
        influence = self.transit_calc._get_transit_influence("Jupiter", "Mars", "Трин")
        assert isinstance(influence, str)
        assert "Возможность:" in influence or "Расширение" in influence

    @pytest.mark.unit
    def test_create_transit_summary(self):
        """Тест создания резюме транзитов."""
        # Пустой список транзитов
        empty_summary = self.transit_calc._create_transit_summary([])
        assert "Спокойный период" in empty_summary

        # Транзиты со слабыми аспектами
        weak_transits = [
            {"strength": "слабый", "nature": "гармония"},
            {"strength": "слабый", "nature": "напряжение"},
        ]
        weak_summary = self.transit_calc._create_transit_summary(weak_transits)
        assert "слабых транзитных влияний" in weak_summary

        # Сильные гармоничные транзиты
        harmonious_transits = [
            {"strength": "сильный", "nature": "гармония"},
            {"strength": "очень сильный", "nature": "поток"},
        ]
        harmonious_summary = self.transit_calc._create_transit_summary(
            harmonious_transits
        )
        assert "Благоприятный период" in harmonious_summary

    @pytest.mark.unit
    def test_calculate_solar_return_basic(self):
        """Тест базового расчета соляра."""
        birth_date = date(1990, 3, 15)
        year = 2024

        with (
            patch.object(
                self.transit_calc.astro_calc, "calculate_planet_positions"
            ) as mock_positions,
            patch.object(
                self.transit_calc.astro_calc, "calculate_houses"
            ) as mock_houses,
            patch.object(
                self.transit_calc.astro_calc, "calculate_aspects"
            ) as mock_aspects,
        ):
            mock_positions.return_value = self.mock_natal_planets
            mock_houses.return_value = {1: {"cusp_longitude": 0, "sign": "Овен"}}
            mock_aspects.return_value = [
                {"aspect": "Трин", "orb": 3, "planet1": "Sun", "planet2": "Jupiter"}
            ]

            result = self.transit_calc.calculate_solar_return(birth_date, year)

            assert "year" in result
            assert "date" in result
            assert "planets" in result
            assert "houses" in result
            assert "interpretation" in result
            assert "themes" in result
            assert result["year"] == year

    @pytest.mark.unit
    def test_get_year_theme(self):
        """Тест определения темы года."""
        themes = [
            ("Овен", "новых начинаний"),
            ("Телец", "стабилизации"),
            ("Близнецы", "обучения"),
            ("Рак", "семьи"),
            ("Лев", "творчества"),
            ("Дева", "совершенствования"),
            ("Весы", "отношений"),
            ("Скорпион", "трансформации"),
            ("Стрелец", "расширения"),
            ("Козерог", "достижений"),
            ("Водолей", "инноваций"),
            ("Рыбы", "духовного развития"),
        ]

        for sign, expected_keyword in themes:
            theme = self.transit_calc._get_year_theme(sign)
            assert isinstance(theme, str)
            assert expected_keyword in theme.lower()

    @pytest.mark.unit
    def test_calculate_lunar_return_basic(self):
        """Тест базового расчета лунара."""
        birth_date = date(1990, 3, 15)
        month = 12
        year = 2024

        with (
            patch.object(
                self.transit_calc.astro_calc, "calculate_planet_positions"
            ) as mock_positions,
            patch.object(
                self.transit_calc.astro_calc, "calculate_houses"
            ) as mock_houses,
            patch.object(self.transit_calc, "_find_new_moon") as mock_new_moon,
        ):
            mock_positions.return_value = self.mock_natal_planets
            mock_houses.return_value = {1: {"cusp_longitude": 0, "sign": "Рак"}}
            mock_new_moon.return_value = datetime(2024, 12, 15)

            result = self.transit_calc.calculate_lunar_return(birth_date, month, year)

            assert "month" in result
            assert "year" in result
            assert "new_moon_date" in result
            assert "planets" in result
            assert "houses" in result
            assert "interpretation" in result
            assert "monthly_themes" in result
            assert result["month"] == month
            assert result["year"] == year

    @pytest.mark.unit
    def test_find_new_moon(self):
        """Тест поиска новолуния."""
        with patch.object(
            self.transit_calc.astro_calc, "calculate_moon_phase"
        ) as mock_phase:
            # Тест новолуния
            mock_phase.return_value = {"angle": 15}
            result = self.transit_calc._find_new_moon(2024, 12)
            assert result is not None
            assert isinstance(result, datetime)

            # Тест случая когда не новолуние
            mock_phase.return_value = {"angle": 180}
            result = self.transit_calc._find_new_moon(2024, 12)
            assert result is not None

    @pytest.mark.unit
    def test_get_monthly_themes(self):
        """Тест получения тем месяца."""
        positions = {"Moon": {"sign": "Рак"}, "Mercury": {"sign": "Близнецы"}}

        themes = self.transit_calc._get_monthly_themes(positions)
        assert isinstance(themes, list)
        assert len(themes) > 0
        assert "забота" in themes[0].lower() or "семейные" in themes[0].lower()

    @pytest.mark.integration
    def test_transit_calculation_integration(self):
        """Интеграционный тест расчета транзитов."""
        # Используем реальные данные для более полного тестирования
        natal_planets = {
            "Sun": {"longitude": 100.0, "sign": "Рак", "degree_in_sign": 10.0},
            "Moon": {"longitude": 200.0, "sign": "Весы", "degree_in_sign": 20.0},
        }

        # Не мочим astro_calc для интеграционного теста
        result = self.transit_calc.calculate_current_transits(natal_planets)

        # Проверяем структуру результата
        assert isinstance(result, dict)
        required_keys = [
            "date",
            "active_transits",
            "approaching_transits",
            "summary",
            "daily_influences",
        ]
        for key in required_keys:
            assert key in result

    @pytest.mark.performance
    def test_transit_calculation_performance(self):
        """Тест производительности расчета транзитов."""
        import time

        start_time = time.time()

        # Выполняем несколько расчетов
        for _ in range(10):
            self.transit_calc.calculate_current_transits(self.mock_natal_planets)

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем, что расчеты выполняются достаточно быстро
        assert execution_time < 5.0  # Менее 5 секунд для 10 расчетов
