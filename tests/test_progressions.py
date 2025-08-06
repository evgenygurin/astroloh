"""
Тесты для прогрессий в натальной карте.
"""

import pytest
from datetime import date, time
from unittest.mock import patch

from app.services.natal_chart import NatalChartCalculator


class TestProgressions:
    """Тесты для прогрессий."""

    def setup_method(self):
        """Настройка для каждого теста."""
        self.natal_calc = NatalChartCalculator()

    @pytest.mark.unit
    def test_calculate_progressions_basic(self):
        """Тест базового расчета прогрессий."""
        birth_date = date(1990, 3, 15)
        progression_date = date(2024, 3, 15)  # 34 года спустя

        with (
            patch.object(
                self.natal_calc.astro_calc, "calculate_planet_positions"
            ) as mock_positions,
            patch.object(self.natal_calc.astro_calc, "calculate_houses") as mock_houses,
        ):
            mock_positions.return_value = {
                "Sun": {"longitude": 130.0, "sign": "Лев", "degree_in_sign": 10.0},
                "Moon": {"longitude": 45.0, "sign": "Телец", "degree_in_sign": 15.0},
            }
            mock_houses.return_value = {1: {"cusp_longitude": 0, "sign": "Овен"}}

            result = self.natal_calc.calculate_progressions(
                birth_date=birth_date, progression_date=progression_date
            )

            assert "birth_date" in result
            assert "progression_date" in result
            assert "days_progressed" in result
            assert "progressed_planets" in result
            assert "progressed_houses" in result
            assert "interpretation" in result
            assert "key_changes" in result

            # Проверяем количество дней
            expected_days = (progression_date - birth_date).days
            assert result["days_progressed"] == expected_days

    @pytest.mark.unit
    def test_interpret_progressions(self):
        """Тест интерпретации прогрессий."""
        progressed_positions = {
            "Sun": {"sign": "Дева", "longitude": 150.0},
            "Moon": {"sign": "Близнецы", "longitude": 75.0},
        }
        progression_date = date(2024, 3, 15)
        birth_date = date(1990, 3, 15)

        interpretation = self.natal_calc._interpret_progressions(
            progressed_positions, progression_date, birth_date
        )

        assert "current_age" in interpretation
        assert "life_stage" in interpretation
        assert "progressed_sun" in interpretation
        assert "progressed_moon" in interpretation
        assert "general_trends" in interpretation

        # Проверяем возраст
        expected_age = (progression_date - birth_date).days // 365
        assert interpretation["current_age"] == expected_age

    @pytest.mark.unit
    def test_get_life_stage_description(self):
        """Тест описания жизненного этапа."""
        test_cases = [
            (5, "детство"),
            (12, "детство"),
            (18, "юность"),
            (25, "молодость"),
            (35, "зрелость"),
            (45, "средний возраст"),
            (60, "зрелый возраст"),
            (75, "старшие годы"),
        ]

        for age, expected_keyword in test_cases:
            description = self.natal_calc._get_life_stage_description(age)
            assert isinstance(description, str)
            assert expected_keyword.lower() in description.lower()

    @pytest.mark.unit
    def test_get_progressed_sun_meaning(self):
        """Тест значения прогрессированного Солнца."""
        test_signs = [
            ("Овен", "активности"),
            ("Телец", "стабилизации"),
            ("Близнецы", "общении"),
            ("Рак", "семье"),
            ("Лев", "творческое"),
            ("Дева", "совершенствование"),
            ("Весы", "отношений"),
            ("Скорпион", "трансформация"),
            ("Стрелец", "расширение"),
            ("Козерог", "структуры"),
            ("Водолей", "инновации"),
            ("Рыбы", "духовное"),
        ]

        for sign, expected_keyword in test_signs:
            meaning = self.natal_calc._get_progressed_sun_meaning(sign)
            assert isinstance(meaning, str)
            assert expected_keyword.lower() in meaning.lower()

    @pytest.mark.unit
    def test_get_progressed_moon_meaning(self):
        """Тест значения прогрессированной Луны."""
        test_signs = [
            ("Овен", "независимость"),
            ("Телец", "стабильности"),
            ("Близнецы", "любознательность"),
            ("Рак", "эмоциональная"),
            ("Лев", "признании"),
            ("Дева", "аналитический"),
            ("Весы", "гармонии"),
            ("Скорпион", "интенсивные"),
            ("Стрелец", "оптимизм"),
            ("Козерог", "серьезный"),
            ("Водолей", "необычный"),
            ("Рыбы", "чувствительность"),
        ]

        for sign, expected_keyword in test_signs:
            meaning = self.natal_calc._get_progressed_moon_meaning(sign)
            assert isinstance(meaning, str)
            assert expected_keyword.lower() in meaning.lower()

    @pytest.mark.unit
    def test_get_progression_trends(self):
        """Тест определения тенденций прогрессий."""
        progressed_positions = {
            "Sun": {"longitude": 120.0},
            "Moon": {"longitude": 125.0},  # Близко к Солнцу - соединение
        }

        # Тест возрастного периода Сатурна
        trends_29 = self.natal_calc._get_progression_trends(29, progressed_positions)
        assert isinstance(trends_29, list)
        assert any("Сатурна" in trend for trend in trends_29)

        # Тест кризиса среднего возраста
        trends_40 = self.natal_calc._get_progression_trends(40, progressed_positions)
        assert isinstance(trends_40, list)
        assert any("кризис" in trend.lower() for trend in trends_40)

        # Тест гармонии Солнце-Луна
        assert any("гармония" in trend.lower() for trend in trends_29 + trends_40)

    @pytest.mark.unit
    def test_analyze_progression_changes(self):
        """Тест анализа изменений в прогрессиях."""
        progressed_positions = {
            "Sun": {"sign": "Дева"},
            "Moon": {"sign": "Близнецы"},
            "Mercury": {"sign": "Весы"},
            "Venus": {"sign": "Скорпион"},
            "Mars": {"sign": "Стрелец"},
            "Jupiter": {"sign": "Козерог"},  # Не должен попасть в быстрые планеты
        }

        changes = self.natal_calc._analyze_progression_changes(progressed_positions)

        assert isinstance(changes, list)
        assert len(changes) <= 3  # Ограничено тремя основными

        # Проверяем, что включены только быстрые планеты
        fast_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
        for change in changes:
            assert any(planet in change for planet in fast_planets)
            assert "Jupiter" not in change

    @pytest.mark.unit
    def test_progressions_with_different_dates(self):
        """Тест прогрессий с различными датами."""
        birth_date = date(1985, 7, 20)

        # Тест с различными датами прогрессии
        test_dates = [
            date(2000, 7, 20),  # 15 лет
            date(2010, 7, 20),  # 25 лет
            date(2020, 7, 20),  # 35 лет
            date(2024, 7, 20),  # 39 лет
        ]

        with (
            patch.object(
                self.natal_calc.astro_calc, "calculate_planet_positions"
            ) as mock_positions,
            patch.object(self.natal_calc.astro_calc, "calculate_houses") as mock_houses,
        ):
            mock_positions.return_value = {
                "Sun": {"sign": "Лев", "longitude": 120.0},
                "Moon": {"sign": "Дева", "longitude": 150.0},
            }
            mock_houses.return_value = {1: {"cusp_longitude": 0}}

            for progression_date in test_dates:
                result = self.natal_calc.calculate_progressions(
                    birth_date=birth_date, progression_date=progression_date
                )

                expected_age = (progression_date - birth_date).days // 365
                actual_age = result["interpretation"]["current_age"]

                assert actual_age == expected_age

    @pytest.mark.unit
    def test_progressions_with_custom_time_and_place(self):
        """Тест прогрессий с пользовательским временем и местом."""
        birth_date = date(1990, 6, 10)
        birth_time = time(14, 30)  # 14:30
        birth_place = {"latitude": 59.9311, "longitude": 30.3609}  # Санкт-Петербург

        with (
            patch.object(
                self.natal_calc.astro_calc, "calculate_planet_positions"
            ) as mock_positions,
            patch.object(self.natal_calc.astro_calc, "calculate_houses") as mock_houses,
        ):
            mock_positions.return_value = {
                "Sun": {"sign": "Близнецы", "longitude": 80.0}
            }
            mock_houses.return_value = {1: {"cusp_longitude": 15.0}}

            result = self.natal_calc.calculate_progressions(
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                timezone_str="Europe/Moscow",
            )

            assert result is not None
            assert "progressed_planets" in result
            assert "progressed_houses" in result

    @pytest.mark.integration
    def test_progressions_integration(self):
        """Интеграционный тест прогрессий."""
        birth_date = date(1992, 12, 25)
        progression_date = date(2024, 12, 25)

        # Не мочим astro_calc для более реального тестирования
        result = self.natal_calc.calculate_progressions(
            birth_date=birth_date, progression_date=progression_date
        )

        # Проверяем структуру результата
        assert isinstance(result, dict)
        required_keys = [
            "birth_date",
            "progression_date",
            "days_progressed",
            "progressed_planets",
            "progressed_houses",
            "interpretation",
            "key_changes",
        ]
        for key in required_keys:
            assert key in result

        # Проверяем интерпретацию
        interpretation = result["interpretation"]
        assert interpretation["current_age"] == 32  # 2024 - 1992
        assert isinstance(interpretation["life_stage"], str)
        assert "progressed_sun" in interpretation
        assert "progressed_moon" in interpretation

    @pytest.mark.performance
    def test_progressions_performance(self):
        """Тест производительности расчета прогрессий."""
        import time

        birth_date = date(1988, 4, 12)

        start_time = time.time()

        # Выполняем несколько расчетов
        for i in range(5):
            progression_date = date(2020 + i, 4, 12)
            self.natal_calc.calculate_progressions(
                birth_date, progression_date=progression_date
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # Проверяем производительность
        assert execution_time < 3.0  # Менее 3 секунд для 5 расчетов

    @pytest.mark.security
    def test_progressions_input_validation(self):
        """Тест валидации входных данных прогрессий."""
        # Тест с экстремальными датами
        birth_date = date(1900, 1, 1)
        progression_date = date(2100, 12, 31)

        # Не должно падать даже с экстремальными датами
        result = self.natal_calc.calculate_progressions(
            birth_date=birth_date, progression_date=progression_date
        )

        assert result is not None
        assert result["days_progressed"] > 0

        # Тест с датой прогрессии раньше рождения
        early_progression = date(1899, 1, 1)
        result_early = self.natal_calc.calculate_progressions(
            birth_date=birth_date, progression_date=early_progression
        )

        # Должно обработать корректно (отрицательные дни)
        assert result_early is not None
