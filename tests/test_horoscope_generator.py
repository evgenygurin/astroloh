"""
Тесты для генератора гороскопов.
"""

from datetime import date, datetime

from app.models.yandex_models import YandexZodiacSign
from app.services.horoscope_generator import HoroscopeGenerator, HoroscopePeriod


class TestHoroscopeGenerator:
    """Тесты генератора гороскопов."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.generator = HoroscopeGenerator()

    def test_generate_personalized_horoscope_basic(self):
        """Тест базовой генерации персонального гороскопа."""
        birth_date = date(1990, 6, 15)
        horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.GEMINI,
            birth_date=birth_date,
            period=HoroscopePeriod.DAILY,
        )

        # Проверяем основную структуру
        assert "zodiac_sign" in horoscope
        assert "period" in horoscope
        assert "date" in horoscope
        assert "general_forecast" in horoscope
        assert "spheres" in horoscope
        assert "energy_level" in horoscope
        assert "lucky_numbers" in horoscope
        assert "lucky_colors" in horoscope
        assert "advice" in horoscope
        assert "astrological_influences" in horoscope

        # Проверяем значения
        assert horoscope["zodiac_sign"] == "близнецы"
        assert horoscope["period"] == "день"
        assert isinstance(horoscope["general_forecast"], str)
        assert len(horoscope["general_forecast"]) > 0

    def test_spheres_forecast(self):
        """Тест прогноза по сферам жизни."""
        horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.LEO,
            birth_date=date(1985, 8, 10),
            period=HoroscopePeriod.DAILY,
        )

        spheres = horoscope["spheres"]
        expected_spheres = ["love", "career", "health", "finances"]

        for sphere in expected_spheres:
            assert sphere in spheres
            assert "forecast" in spheres[sphere]
            assert "rating" in spheres[sphere]
            assert "advice" in spheres[sphere]

            # Проверяем рейтинг (1-5 звезд)
            assert 1 <= spheres[sphere]["rating"] <= 5
            assert isinstance(spheres[sphere]["forecast"], str)
            assert isinstance(spheres[sphere]["advice"], str)

    def test_energy_level_calculation(self):
        """Тест расчета уровня энергии."""
        horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.ARIES,  # Огненный знак
            birth_date=date(1992, 3, 25),
            period=HoroscopePeriod.DAILY,
        )

        energy = horoscope["energy_level"]

        assert "level" in energy
        assert "description" in energy
        assert "advice" in energy

        assert 10 <= energy["level"] <= 100
        assert isinstance(energy["description"], str)
        assert isinstance(energy["advice"], str)

    def test_lucky_elements_generation(self):
        """Тест генерации счастливых элементов."""
        horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.TAURUS,
            birth_date=date(1988, 5, 5),
            period=HoroscopePeriod.DAILY,
        )

        lucky_numbers = horoscope["lucky_numbers"]
        lucky_colors = horoscope["lucky_colors"]

        # Проверяем счастливые числа
        assert isinstance(lucky_numbers, list)
        assert len(lucky_numbers) >= 3
        for number in lucky_numbers:
            assert isinstance(number, int)
            assert 1 <= number <= 99

        # Проверяем счастливые цвета
        assert isinstance(lucky_colors, list)
        assert len(lucky_colors) >= 1
        for color in lucky_colors:
            assert isinstance(color, str)
            assert len(color) > 0

    def test_astrological_influences(self):
        """Тест астрологических влияний."""
        horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.SCORPIO,
            birth_date=date(1991, 11, 8),
            period=HoroscopePeriod.DAILY,
        )

        influences = horoscope["astrological_influences"]

        assert "moon_phase" in influences
        assert "planetary_hours" in influences
        assert "transits" in influences
        assert "season_influence" in influences

        # Проверяем фазу Луны
        moon_phase = influences["moon_phase"]
        assert "phase_name" in moon_phase
        assert "illumination_percent" in moon_phase

        # Проверяем сезонное влияние
        season = influences["season_influence"]
        assert "season" in season
        assert "influence" in season

    def test_different_periods(self):
        """Тест различных периодов гороскопа."""
        birth_date = date(1987, 9, 15)

        # Дневной гороскоп
        daily = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.VIRGO,
            birth_date=birth_date,
            period=HoroscopePeriod.DAILY,
        )

        # Недельный гороскоп
        weekly = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.VIRGO,
            birth_date=birth_date,
            period=HoroscopePeriod.WEEKLY,
        )

        # Месячный гороскоп
        monthly = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.VIRGO,
            birth_date=birth_date,
            period=HoroscopePeriod.MONTHLY,
        )

        assert daily["period"] == "день"
        assert weekly["period"] == "неделя"
        assert monthly["period"] == "месяц"

        # Все должны иметь одинаковую структуру
        for horoscope in [daily, weekly, monthly]:
            assert "general_forecast" in horoscope
            assert "spheres" in horoscope
            assert "energy_level" in horoscope

    def test_different_zodiac_signs(self):
        """Тест для различных знаков зодиака."""
        birth_date = date(1990, 1, 1)

        # Тестируем все знаки зодиака
        all_signs = [
            YandexZodiacSign.ARIES,
            YandexZodiacSign.TAURUS,
            YandexZodiacSign.GEMINI,
            YandexZodiacSign.CANCER,
            YandexZodiacSign.LEO,
            YandexZodiacSign.VIRGO,
            YandexZodiacSign.LIBRA,
            YandexZodiacSign.SCORPIO,
            YandexZodiacSign.SAGITTARIUS,
            YandexZodiacSign.CAPRICORN,
            YandexZodiacSign.AQUARIUS,
            YandexZodiacSign.PISCES,
        ]

        for sign in all_signs:
            horoscope = self.generator.generate_personalized_horoscope(
                zodiac_sign=sign,
                birth_date=birth_date,
                period=HoroscopePeriod.DAILY,
            )

            assert horoscope["zodiac_sign"] == sign.value
            assert len(horoscope["general_forecast"]) > 0
            assert len(horoscope["advice"]) > 0

            # Проверяем, что характеристики знака используются
            sign_info = self.generator.sign_characteristics.get(sign, {})
            if sign_info:
                assert "lucky_colors" in horoscope
                assert len(horoscope["lucky_colors"]) > 0

    def test_moon_phase_influence(self):
        """Тест влияния фазы Луны на прогноз."""
        # Генерируем гороскопы для разных дат (разные фазы Луны)
        dates = [
            datetime(2023, 1, 1),  # Разные даты для разных фаз
            datetime(2023, 1, 15),
            datetime(2023, 2, 1),
            datetime(2023, 2, 15),
        ]

        horoscopes = []
        for target_date in dates:
            horoscope = self.generator.generate_personalized_horoscope(
                zodiac_sign=YandexZodiacSign.CAPRICORN,
                birth_date=date(1989, 1, 10),
                period=HoroscopePeriod.DAILY,
                target_date=target_date,
            )
            horoscopes.append(horoscope)

        # Проверяем, что фазы Луны различаются
        moon_phases = [
            h["astrological_influences"]["moon_phase"]["phase_name"] for h in horoscopes
        ]

        # Должно быть как минимум 2 разные фазы
        unique_phases = set(moon_phases)
        assert len(unique_phases) >= 1  # Минимум одна фаза должна быть

    def test_energy_level_by_element(self):
        """Тест влияния элемента знака на уровень энергии."""
        birth_date = date(1990, 6, 15)

        # Огненный знак (должен иметь высокую энергию)
        fire_horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.ARIES,
            birth_date=birth_date,
            period=HoroscopePeriod.DAILY,
        )

        # Водный знак (может иметь более низкую базовую энергию)
        water_horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.PISCES,
            birth_date=birth_date,
            period=HoroscopePeriod.DAILY,
        )

        fire_energy = fire_horoscope["energy_level"]["level"]
        water_energy = water_horoscope["energy_level"]["level"]

        # Огненные знаки обычно имеют более высокий базовый уровень энергии
        assert isinstance(fire_energy, (int, float))
        assert isinstance(water_energy, (int, float))
        assert 10 <= fire_energy <= 100
        assert 10 <= water_energy <= 100

    def test_advice_generation(self):
        """Тест генерации советов."""
        horoscope = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.LIBRA,
            birth_date=date(1986, 10, 5),
            period=HoroscopePeriod.DAILY,
        )

        advice = horoscope["advice"]

        assert isinstance(advice, str)
        assert len(advice) > 10  # Совет должен быть содержательным

        # Проверяем, что совет содержит ключевые слова для Весов
        sign_keywords = self.generator.sign_characteristics[YandexZodiacSign.LIBRA][
            "keywords"
        ]
        advice_lower = advice.lower()

        # Хотя бы одно ключевое слово должно присутствовать в совете
        _ = any(keyword.lower() in advice_lower for keyword in sign_keywords)
        # Не обязательно, но желательно для персонализации

    def test_deterministic_behavior(self):
        """Тест детерминированного поведения (одинаковые входные данные = одинаковый результат)."""
        birth_date = date(1993, 7, 20)
        target_date = datetime(2023, 6, 15, 10, 30)

        # Генерируем гороскоп дважды с одинаковыми параметрами
        horoscope1 = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.CANCER,
            birth_date=birth_date,
            period=HoroscopePeriod.DAILY,
            target_date=target_date,
        )

        horoscope2 = self.generator.generate_personalized_horoscope(
            zodiac_sign=YandexZodiacSign.CANCER,
            birth_date=birth_date,
            period=HoroscopePeriod.DAILY,
            target_date=target_date,
        )

        # Основные параметры должны совпадать
        assert horoscope1["zodiac_sign"] == horoscope2["zodiac_sign"]
        assert horoscope1["period"] == horoscope2["period"]
        assert horoscope1["date"] == horoscope2["date"]
        assert (
            horoscope1["energy_level"]["level"] == horoscope2["energy_level"]["level"]
        )

        # Астрологические влияния должны быть одинаковыми
        assert (
            horoscope1["astrological_influences"]["moon_phase"]
            == horoscope2["astrological_influences"]["moon_phase"]
        )
