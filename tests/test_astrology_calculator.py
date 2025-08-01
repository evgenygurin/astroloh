"""
Тесты для сервиса астрологических вычислений.
"""
import pytest
from datetime import datetime, date
from app.services.astrology_calculator import AstrologyCalculator
from app.models.yandex_models import YandexZodiacSign


class TestAstrologyCalculator:
    """Тесты калькулятора астрологических вычислений."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.calculator = AstrologyCalculator()
    
    def test_get_zodiac_sign_by_date(self):
        """Тест определения знака зодиака по дате."""
        # Овен
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 3, 25)) == YandexZodiacSign.ARIES
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 4, 15)) == YandexZodiacSign.ARIES
        
        # Телец
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 4, 25)) == YandexZodiacSign.TAURUS
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 5, 15)) == YandexZodiacSign.TAURUS
        
        # Близнецы
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 5, 25)) == YandexZodiacSign.GEMINI
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 6, 15)) == YandexZodiacSign.GEMINI
        
        # Рак
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 6, 25)) == YandexZodiacSign.CANCER
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 7, 15)) == YandexZodiacSign.CANCER
        
        # Лев
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 7, 25)) == YandexZodiacSign.LEO
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 8, 15)) == YandexZodiacSign.LEO
        
        # Дева
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 8, 25)) == YandexZodiacSign.VIRGO
        assert self.calculator.get_zodiac_sign_by_date(date(1990, 9, 15)) == YandexZodiacSign.VIRGO
    
    def test_calculate_julian_day(self):
        """Тест вычисления юлианского дня."""
        test_date = datetime(2023, 1, 1, 12, 0)
        jd = self.calculator.calculate_julian_day(test_date)
        
        assert isinstance(jd, float)
        assert jd > 2400000  # Юлианский день должен быть больше базового значения
    
    def test_calculate_planet_positions(self):
        """Тест вычисления позиций планет."""
        birth_date = datetime(1990, 6, 15, 12, 0)
        positions = self.calculator.calculate_planet_positions(birth_date)
        
        # Проверяем, что все планеты присутствуют
        expected_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                           'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
        
        for planet in expected_planets:
            assert planet in positions
            assert 'longitude' in positions[planet]
            assert 'sign' in positions[planet]
            assert 'degree_in_sign' in positions[planet]
            assert 0 <= positions[planet]['longitude'] <= 360
            assert 0 <= positions[planet]['degree_in_sign'] <= 30
    
    def test_calculate_houses(self):
        """Тест вычисления астрологических домов."""
        birth_date = datetime(1990, 6, 15, 12, 0)
        houses = self.calculator.calculate_houses(birth_date)
        
        # Проверяем наличие всех 12 домов
        for i in range(1, 13):
            assert i in houses
            assert 'cusp_longitude' in houses[i]
            assert 'sign' in houses[i]
            assert 'degree_in_sign' in houses[i]
        
        # Проверяем особые точки
        assert 'ascendant' in houses
        assert 'midheaven' in houses
    
    def test_calculate_aspects(self):
        """Тест вычисления аспектов между планетами."""
        # Создаем тестовые позиции планет
        test_positions = {
            'Sun': {'longitude': 0},
            'Moon': {'longitude': 90},
            'Mercury': {'longitude': 120},
            'Venus': {'longitude': 180}
        }
        
        aspects = self.calculator.calculate_aspects(test_positions)
        
        assert isinstance(aspects, list)
        
        # Проверяем, что найдены ожидаемые аспекты
        aspect_types = [aspect['aspect'] for aspect in aspects]
        assert 'Квадрат' in aspect_types  # Sun-Moon 90°
        assert 'Трин' in aspect_types    # Sun-Mercury 120°
        assert 'Оппозиция' in aspect_types  # Sun-Venus 180°
    
    def test_calculate_moon_phase(self):
        """Тест вычисления фазы Луны."""
        test_date = datetime(2023, 6, 15)
        moon_phase = self.calculator.calculate_moon_phase(test_date)
        
        assert 'phase_name' in moon_phase
        assert 'phase_description' in moon_phase
        assert 'angle' in moon_phase
        assert 'illumination_percent' in moon_phase
        assert 'is_waxing' in moon_phase
        
        assert 0 <= moon_phase['illumination_percent'] <= 100
        assert 0 <= moon_phase['angle'] <= 360
        assert isinstance(moon_phase['is_waxing'], bool)
    
    def test_calculate_compatibility_score(self):
        """Тест вычисления совместимости знаков зодиака."""
        # Тестируем совместимость огненных знаков
        compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.LEO
        )
        
        assert 'total_score' in compatibility
        assert 'element_score' in compatibility
        assert 'quality_score' in compatibility
        assert 'description' in compatibility
        
        assert 0 <= compatibility['total_score'] <= 100
        assert compatibility['total_score'] > 50  # Огненные знаки должны быть совместимы
        
        # Тестируем менее совместимые знаки
        low_compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.CANCER
        )
        
        assert low_compatibility['total_score'] < compatibility['total_score']
    
    def test_get_planetary_hours(self):
        """Тест получения планетных часов."""
        test_date = datetime(2023, 6, 15, 14, 30)  # Четверг, 14:30
        planetary_hours = self.calculator.get_planetary_hours(test_date)
        
        assert 'day_ruler' in planetary_hours
        assert 'current_hour_ruler' in planetary_hours
        assert 'favorable_hours' in planetary_hours
        assert 'description' in planetary_hours
        
        assert planetary_hours['day_ruler'] == "Юпитер"  # Четверг
        assert isinstance(planetary_hours['favorable_hours'], list)
        assert len(planetary_hours['favorable_hours']) == 4
    
    def test_element_and_quality_mapping(self):
        """Тест правильности соответствия элементов и качеств знакам."""
        # Проверяем элементы
        assert self.calculator.elements["Овен"] == "fire"
        assert self.calculator.elements["Телец"] == "earth"
        assert self.calculator.elements["Близнецы"] == "air"
        assert self.calculator.elements["Рак"] == "water"
        
        # Проверяем качества
        assert self.calculator.qualities["Овен"] == "cardinal"
        assert self.calculator.qualities["Телец"] == "fixed"
        assert self.calculator.qualities["Близнецы"] == "mutable"
    
    def test_edge_cases(self):
        """Тест граничных случаев."""
        # Тест с граничными датами знаков зодиака
        assert self.calculator.get_zodiac_sign_by_date(date(2023, 3, 21)) == YandexZodiacSign.ARIES
        assert self.calculator.get_zodiac_sign_by_date(date(2023, 4, 19)) == YandexZodiacSign.ARIES
        assert self.calculator.get_zodiac_sign_by_date(date(2023, 4, 20)) == YandexZodiacSign.TAURUS
        
        # Тест с датой на рубеже года
        assert self.calculator.get_zodiac_sign_by_date(date(2023, 12, 25)) == YandexZodiacSign.CAPRICORN
        assert self.calculator.get_zodiac_sign_by_date(date(2023, 1, 15)) == YandexZodiacSign.CAPRICORN
    
    def test_compatibility_edge_cases(self):
        """Тест граничных случаев совместимости."""
        # Совместимость знака с самим собой
        self_compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.ARIES
        )
        
        assert self_compatibility['total_score'] >= 80  # Высокая совместимость с собой
        
        # Совместимость противоположных знаков
        opposite_compatibility = self.calculator.calculate_compatibility_score(
            YandexZodiacSign.ARIES, YandexZodiacSign.LIBRA
        )
        
        assert isinstance(opposite_compatibility['total_score'], (int, float))
        assert 0 <= opposite_compatibility['total_score'] <= 100