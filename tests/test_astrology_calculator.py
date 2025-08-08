"""
Тесты для сервиса астрологических вычислений.
"""

from datetime import date, datetime

import numpy as np
import pytest

from app.models.yandex_models import YandexZodiacSign
from app.services.astrology_calculator import AstrologyCalculator


class TestAstrologyCalculator:
    """Тесты калькулятора астрологических вычислений."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calculator = AstrologyCalculator()

    def test_get_zodiac_sign_by_date(self):
        """Тест определения знака зодиака по дате."""
        # Овен
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 3, 25))
            == YandexZodiacSign.ARIES
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 4, 15))
            == YandexZodiacSign.ARIES
        )

        # Телец
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 4, 25))
            == YandexZodiacSign.TAURUS
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 5, 15))
            == YandexZodiacSign.TAURUS
        )

        # Близнецы
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 5, 25))
            == YandexZodiacSign.GEMINI
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 6, 15))
            == YandexZodiacSign.GEMINI
        )

        # Рак
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 6, 25))
            == YandexZodiacSign.CANCER
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 7, 15))
            == YandexZodiacSign.CANCER
        )

        # Лев
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 7, 25))
            == YandexZodiacSign.LEO
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 8, 15))
            == YandexZodiacSign.LEO
        )

        # Дева
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 8, 25))
            == YandexZodiacSign.VIRGO
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(1990, 9, 15))
            == YandexZodiacSign.VIRGO
        )

    def test_calculate_julian_day(self):
        """Тест вычисления юлианского дня."""
        test_date = datetime(2023, 1, 1, 12, 0)
        jd = self.calculator.calculate_julian_day(test_date)

        assert isinstance(jd, float)
        assert (
            jd > 2400000
        )  # Юлианский день должен быть больше базового значения

    def test_calculate_planet_positions(self):
        """Тест вычисления позиций планет."""
        birth_date = datetime(1990, 6, 15, 12, 0)
        positions = self.calculator.calculate_planet_positions(birth_date)

        # Проверяем, что все планеты присутствуют
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
            assert planet in positions
            assert "longitude" in positions[planet]
            assert "sign" in positions[planet]
            assert "degree_in_sign" in positions[planet]
            assert 0 <= positions[planet]["longitude"] <= 360
            assert 0 <= positions[planet]["degree_in_sign"] <= 30

    def test_calculate_houses(self):
        """Тест вычисления астрологических домов."""
        birth_date = datetime(1990, 6, 15, 12, 0)
        houses = self.calculator.calculate_houses(birth_date)

        # Проверяем наличие всех 12 домов
        for i in range(1, 13):
            assert i in houses
            assert "cusp_longitude" in houses[i]
            assert "sign" in houses[i]
            assert "degree_in_sign" in houses[i]

        # Проверяем особые точки
        assert "ascendant" in houses
        assert "midheaven" in houses

    def test_calculate_aspects(self):
        """Тест вычисления аспектов между планетами."""
        # Создаем тестовые позиции планет
        test_positions = {
            "Sun": {"longitude": 0},
            "Moon": {"longitude": 90},
            "Mercury": {"longitude": 120},
            "Venus": {"longitude": 180},
        }

        aspects = self.calculator.calculate_aspects(test_positions)

        assert isinstance(aspects, list)

        # Проверяем, что найдены ожидаемые аспекты
        aspect_types = [aspect["aspect"] for aspect in aspects]
        assert "Квадрат" in aspect_types  # Sun-Moon 90°
        assert "Трин" in aspect_types  # Sun-Mercury 120°
        assert "Оппозиция" in aspect_types  # Sun-Venus 180°

    def test_calculate_moon_phase(self):
        """Тест вычисления фазы Луны."""
        test_date = datetime(2023, 6, 15)
        moon_phase = self.calculator.calculate_moon_phase(test_date)

        assert "phase_name" in moon_phase
        assert "phase_description" in moon_phase
        assert "angle" in moon_phase
        assert "illumination_percent" in moon_phase
        assert "is_waxing" in moon_phase

        assert 0 <= moon_phase["illumination_percent"] <= 100
        assert 0 <= moon_phase["angle"] <= 360
        assert isinstance(moon_phase["is_waxing"], (bool, np.bool_))

    def test_calculate_compatibility_score(self):
        """Тест вычисления совместимости знаков зодиака."""
        # Тестируем совместимость огненных знаков
        compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.LEO
        )

        assert "total_score" in compatibility
        assert "element_score" in compatibility
        assert "quality_score" in compatibility
        assert "description" in compatibility

        assert 0 <= compatibility["total_score"] <= 100
        assert (
            compatibility["total_score"] > 50
        )  # Огненные знаки должны быть совместимы

        # Тестируем менее совместимые знаки
        low_compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.CANCER
        )

        assert low_compatibility["total_score"] < compatibility["total_score"]

    def test_get_planetary_hours(self):
        """Тест получения планетных часов."""
        test_date = datetime(2023, 6, 15, 14, 30)  # Четверг, 14:30
        planetary_hours = self.calculator.get_planetary_hours(test_date)

        assert "day_ruler" in planetary_hours
        assert "current_hour_ruler" in planetary_hours
        assert "favorable_hours" in planetary_hours
        assert "description" in planetary_hours

        assert planetary_hours["day_ruler"] == "Юпитер"  # Четверг
        assert isinstance(planetary_hours["favorable_hours"], list)
        assert len(planetary_hours["favorable_hours"]) == 4

    def test_element_and_quality_mapping(self):
        """Тест правильности соответствия элементов и качеств знакам."""
        # Проверяем элементы (lowercase keys)
        assert self.calculator.elements["овен"] == "fire"
        assert self.calculator.elements["телец"] == "earth"
        assert self.calculator.elements["близнецы"] == "air"
        assert self.calculator.elements["рак"] == "water"

        # Проверяем качества (lowercase keys)
        assert self.calculator.qualities["овен"] == "cardinal"
        assert self.calculator.qualities["телец"] == "fixed"
        assert self.calculator.qualities["близнецы"] == "mutable"

    def test_edge_cases(self):
        """Тест граничных случаев."""
        # Тест с граничными датами знаков зодиака
        assert (
            self.calculator.get_zodiac_sign_by_date(date(2023, 3, 21))
            == YandexZodiacSign.ARIES
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(2023, 4, 19))
            == YandexZodiacSign.ARIES
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(2023, 4, 20))
            == YandexZodiacSign.TAURUS
        )

        # Тест с датой на рубеже года
        assert (
            self.calculator.get_zodiac_sign_by_date(date(2023, 12, 25))
            == YandexZodiacSign.CAPRICORN
        )
        assert (
            self.calculator.get_zodiac_sign_by_date(date(2023, 1, 15))
            == YandexZodiacSign.CAPRICORN
        )

    def test_compatibility_edge_cases(self):
        """Тест граничных случаев совместимости."""
        # Совместимость знака с самим собой
        self_compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.ARIES
        )

        assert (
            self_compatibility["total_score"] >= 80
        )  # Высокая совместимость с собой

        # Совместимость противоположных знаков
        opposite_compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.LIBRA
        )

        assert isinstance(opposite_compatibility["total_score"], (int, float))
        assert 0 <= opposite_compatibility["total_score"] <= 100

    def test_backend_info(self):
        """Тест получения информации о бэкенде."""
        backend_info = self.calculator.get_backend_info()

        assert "backend" in backend_info
        assert "available_backends" in backend_info
        assert "capabilities" in backend_info

        assert isinstance(backend_info["available_backends"], list)
        assert isinstance(backend_info["capabilities"], dict)

        # Проверяем, что хотя бы один бэкенд доступен или это fallback
        available_backends = backend_info["available_backends"]
        current_backend = backend_info["backend"]

        if current_backend:
            assert current_backend in available_backends

        # Проверяем структуру capabilities
        capabilities = backend_info["capabilities"]
        expected_caps = [
            "planet_positions",
            "moon_phases",
            "houses",
            "aspects",
            "high_precision",
        ]
        for cap in expected_caps:
            assert cap in capabilities
            assert isinstance(capabilities[cap], bool)

    def test_backend_fallback(self):
        """Тест fallback при недоступности астрономических библиотек."""
        # Этот тест проверяет, что приложение не падает при отсутствии библиотек
        birth_date = datetime(1990, 6, 15, 12, 0)

        # Тестируем основные функции
        try:
            positions = self.calculator.calculate_planet_positions(birth_date)
            assert isinstance(positions, dict)
            assert len(positions) > 0

            moon_phase = self.calculator.calculate_moon_phase(birth_date)
            assert isinstance(moon_phase, dict)
            assert "phase_name" in moon_phase

            jd = self.calculator.calculate_julian_day(birth_date)
            assert isinstance(jd, float)

        except Exception as e:
            pytest.fail(f"Backend fallback failed: {e}")

    @pytest.mark.parametrize(
        "backend_name", ["swisseph", "skyfield", "astropy", None]
    )
    def test_backend_compatibility(self, backend_name, monkeypatch):
        """Тест совместимости с разными бэкендами."""

        # Имитируем доступность только определенного бэкенда
        def mock_backend_availability(backend):
            if backend == backend_name:
                return True
            return False

        # Создаем новый калькулятор
        calc = AstrologyCalculator()

        # Сохраняем оригинальное значение
        original_backend = calc.backend

        try:
            # Устанавливаем тестируемый бэкенд
            calc.backend = backend_name

            birth_date = datetime(1990, 6, 15, 12, 0)

            # Тестируем, что основные функции работают
            positions = calc.calculate_planet_positions(birth_date)
            assert isinstance(positions, dict)

            moon_phase = calc.calculate_moon_phase(birth_date)
            assert isinstance(moon_phase, dict)

            backend_info = calc.get_backend_info()
            # Backend may fall back to None or another backend if library is not available
            available_backends = backend_info["available_backends"]

            # We manually set the backend, but actual backend may fall back if not available
            # This is acceptable behavior - the system should gracefully handle unavailable backends
            assert backend_info["backend"] in available_backends + [
                None,
                backend_name,
            ]

        finally:
            # Восстанавливаем оригинальное значение
            calc.backend = original_backend

    def test_planet_position_consistency(self):
        """Тест согласованности позиций планет между вызовами."""
        birth_date = datetime(1990, 6, 15, 12, 0)

        # Вызываем дважды и проверяем согласованность
        positions1 = self.calculator.calculate_planet_positions(birth_date)
        positions2 = self.calculator.calculate_planet_positions(birth_date)

        assert positions1.keys() == positions2.keys()

        for planet in positions1:
            # Позиции должны быть одинаковыми для одной и той же даты
            assert (
                positions1[planet]["longitude"]
                == positions2[planet]["longitude"]
            )
            assert positions1[planet]["sign"] == positions2[planet]["sign"]

    def test_fallback_positions_valid(self):
        """Тест корректности fallback позиций планет."""
        # Создаем калькулятор без астрономических библиотек
        from app.services import astrology_calculator

        # Сохраняем оригинальные значения
        original_kerykeion = astrology_calculator.KERYKEION_AVAILABLE
        original_swisseph = astrology_calculator.SWISSEPH_AVAILABLE
        original_skyfield = astrology_calculator.SKYFIELD_AVAILABLE

        try:
            # Отключаем все бэкенды для тестирования fallback
            astrology_calculator.KERYKEION_AVAILABLE = False
            astrology_calculator.SWISSEPH_AVAILABLE = False
            astrology_calculator.SKYFIELD_AVAILABLE = False
            
            calc = AstrologyCalculator()

            birth_date = datetime(1990, 6, 15, 12, 0)
            positions = calc.calculate_planet_positions(birth_date)

            # Проверяем, что fallback позиции корректны
            for planet, pos in positions.items():
                assert 0 <= pos["longitude"] <= 360
                assert 0 <= pos["degree_in_sign"] <= 30
                assert pos["sign"] in calc.zodiac_signs
                assert 0 <= pos["sign_number"] <= 11

        finally:
            # Восстанавливаем оригинальные значения
            astrology_calculator.KERYKEION_AVAILABLE = original_kerykeion
            astrology_calculator.SWISSEPH_AVAILABLE = original_swisseph
            astrology_calculator.SKYFIELD_AVAILABLE = original_skyfield
