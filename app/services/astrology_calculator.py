"""
Сервис астрологических вычислений с использованием Swiss Ephemeris.
"""
import swisseph as swe
from datetime import datetime, date, time
from typing import Dict, List, Tuple, Optional, Any
import pytz
import math
from enum import Enum

from app.models.yandex_models import YandexZodiacSign


class AstrologyCalculator:
    """Класс для астрологических вычислений."""
    
    def __init__(self):
        # Настройка Swiss Ephemeris
        swe.set_ephe_path('/usr/share/swisseph')  # Путь к эфемеридам
        
        # Планеты для расчетов
        self.planets = {
            'Sun': swe.SUN,
            'Moon': swe.MOON,
            'Mercury': swe.MERCURY,
            'Venus': swe.VENUS,
            'Mars': swe.MARS,
            'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN,
            'Uranus': swe.URANUS,
            'Neptune': swe.NEPTUNE,
            'Pluto': swe.PLUTO
        }
        
        # Знаки зодиака
        self.zodiac_signs = [
            "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
            "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
        ]
        
        # Элементы знаков
        self.elements = {
            "Овен": "fire", "Лев": "fire", "Стрелец": "fire",
            "Телец": "earth", "Дева": "earth", "Козерог": "earth", 
            "Близнецы": "air", "Весы": "air", "Водолей": "air",
            "Рак": "water", "Скорпион": "water", "Рыбы": "water"
        }
        
        # Качества знаков
        self.qualities = {
            "Овен": "cardinal", "Рак": "cardinal", "Весы": "cardinal", "Козерог": "cardinal",
            "Телец": "fixed", "Лев": "fixed", "Скорпион": "fixed", "Водолей": "fixed",
            "Близнецы": "mutable", "Дева": "mutable", "Стрелец": "mutable", "Рыбы": "mutable"
        }

    def calculate_julian_day(self, birth_datetime: datetime) -> float:
        """Вычисляет юлианский день для заданной даты и времени."""
        year = birth_datetime.year
        month = birth_datetime.month
        day = birth_datetime.day
        hour = birth_datetime.hour + birth_datetime.minute / 60.0
        
        return swe.julday(year, month, day, hour)

    def get_zodiac_sign_by_date(self, birth_date: date) -> YandexZodiacSign:
        """Определяет знак зодиака по дате рождения."""
        month = birth_date.month
        day = birth_date.day
        
        # Границы знаков зодиака
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return YandexZodiacSign.ARIES
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return YandexZodiacSign.TAURUS
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return YandexZodiacSign.GEMINI
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return YandexZodiacSign.CANCER
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return YandexZodiacSign.LEO
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return YandexZodiacSign.VIRGO
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return YandexZodiacSign.LIBRA
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return YandexZodiacSign.SCORPIO
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return YandexZodiacSign.SAGITTARIUS
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return YandexZodiacSign.CAPRICORN
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return YandexZodiacSign.AQUARIUS
        else:  # (month == 2 and day >= 19) or (month == 3 and day <= 20)
            return YandexZodiacSign.PISCES

    def calculate_planet_positions(
        self, 
        birth_datetime: datetime,
        latitude: float = 55.7558,  # Москва по умолчанию
        longitude: float = 37.6176
    ) -> Dict[str, Dict[str, Any]]:
        """Вычисляет позиции планет на момент рождения."""
        jd = self.calculate_julian_day(birth_datetime)
        positions = {}
        
        for planet_name, planet_id in self.planets.items():
            try:
                # Получаем координаты планеты
                pos, ret = swe.calc_ut(jd, planet_id)
                longitude_deg = pos[0]
                
                # Определяем знак зодиака
                sign_num = int(longitude_deg / 30)
                sign_name = self.zodiac_signs[sign_num]
                
                # Позиция в знаке
                degree_in_sign = longitude_deg % 30
                
                positions[planet_name] = {
                    'longitude': longitude_deg,
                    'sign': sign_name,
                    'degree_in_sign': degree_in_sign,
                    'sign_number': sign_num
                }
                
            except Exception as e:
                # В случае ошибки используем приблизительные значения
                positions[planet_name] = {
                    'longitude': 0,
                    'sign': self.zodiac_signs[0],
                    'degree_in_sign': 0,
                    'sign_number': 0
                }
        
        return positions

    def calculate_houses(
        self,
        birth_datetime: datetime,
        latitude: float = 55.7558,
        longitude: float = 37.6176
    ) -> Dict[int, Dict[str, Any]]:
        """Вычисляет астрологические дома."""
        jd = self.calculate_julian_day(birth_datetime)
        houses = {}
        
        try:
            # Используем систему домов Placidus
            cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
            
            for i in range(12):
                house_num = i + 1
                cusp_longitude = cusps[i]
                
                # Определяем знак зодиака куспида дома
                sign_num = int(cusp_longitude / 30)
                sign_name = self.zodiac_signs[sign_num]
                degree_in_sign = cusp_longitude % 30
                
                houses[house_num] = {
                    'cusp_longitude': cusp_longitude,
                    'sign': sign_name,
                    'degree_in_sign': degree_in_sign
                }
            
            # Добавляем важные точки
            houses['ascendant'] = {
                'longitude': ascmc[0],
                'sign': self.zodiac_signs[int(ascmc[0] / 30)],
                'degree_in_sign': ascmc[0] % 30
            }
            
            houses['midheaven'] = {
                'longitude': ascmc[1],
                'sign': self.zodiac_signs[int(ascmc[1] / 30)],
                'degree_in_sign': ascmc[1] % 30
            }
            
        except Exception as e:
            # В случае ошибки создаем упрощенную систему домов
            for i in range(12):
                houses[i + 1] = {
                    'cusp_longitude': i * 30,
                    'sign': self.zodiac_signs[i],
                    'degree_in_sign': 0
                }
        
        return houses

    def calculate_aspects(
        self, 
        planet_positions: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Вычисляет аспекты между планетами."""
        aspects = []
        aspect_orbs = {
            0: 8,    # Соединение
            60: 6,   # Секстиль
            90: 8,   # Квадрат
            120: 8,  # Трин
            180: 8   # Оппозиция
        }
        
        planets = list(planet_positions.keys())
        
        for i, planet1 in enumerate(planets):
            for planet2 in planets[i+1:]:
                pos1 = planet_positions[planet1]['longitude']
                pos2 = planet_positions[planet2]['longitude']
                
                # Вычисляем угол между планетами
                angle = abs(pos1 - pos2)
                if angle > 180:
                    angle = 360 - angle
                
                # Проверяем аспекты
                for aspect_angle, orb in aspect_orbs.items():
                    if abs(angle - aspect_angle) <= orb:
                        aspect_name = self._get_aspect_name(aspect_angle)
                        aspects.append({
                            'planet1': planet1,
                            'planet2': planet2,
                            'aspect': aspect_name,
                            'angle': aspect_angle,
                            'orb': abs(angle - aspect_angle),
                            'exact_angle': angle
                        })
                        break
        
        return aspects

    def _get_aspect_name(self, angle: float) -> str:
        """Возвращает название аспекта по углу."""
        aspect_names = {
            0: "Соединение",
            60: "Секстиль", 
            90: "Квадрат",
            120: "Трин",
            180: "Оппозиция"
        }
        return aspect_names.get(angle, "Неизвестный")

    def calculate_moon_phase(self, target_date: datetime) -> Dict[str, Any]:
        """Вычисляет фазу Луны на заданную дату."""
        jd = self.calculate_julian_day(target_date)
        
        try:
            # Получаем позиции Солнца и Луны
            sun_pos, _ = swe.calc_ut(jd, swe.SUN)
            moon_pos, _ = swe.calc_ut(jd, swe.MOON)
            
            # Вычисляем угол между Солнцем и Луной
            angle = moon_pos[0] - sun_pos[0]
            if angle < 0:
                angle += 360
            
            # Определяем фазу
            phase_info = self._get_moon_phase_info(angle)
            
            # Вычисляем освещенность
            illumination = (1 - math.cos(math.radians(angle))) / 2 * 100
            
            return {
                'phase_name': phase_info['name'],
                'phase_description': phase_info['description'],
                'angle': angle,
                'illumination_percent': round(illumination, 1),
                'is_waxing': angle < 180
            }
            
        except Exception:
            # Упрощенный расчет в случае ошибки
            day_of_month = target_date.day
            phase_angle = (day_of_month / 29.5) * 360
            phase_info = self._get_moon_phase_info(phase_angle)
            
            return {
                'phase_name': phase_info['name'],
                'phase_description': phase_info['description'],
                'angle': phase_angle,
                'illumination_percent': 50,
                'is_waxing': True
            }

    def _get_moon_phase_info(self, angle: float) -> Dict[str, str]:
        """Возвращает информацию о фазе Луны по углу."""
        if 0 <= angle < 45:
            return {'name': 'Новолуние', 'description': 'Время новых начинаний'}
        elif 45 <= angle < 90:
            return {'name': 'Растущая Луна', 'description': 'Время роста и развития'}
        elif 90 <= angle < 135:
            return {'name': 'Первая четверть', 'description': 'Время действий и решений'}
        elif 135 <= angle < 180:
            return {'name': 'Растущая Луна', 'description': 'Время накопления энергии'}
        elif 180 <= angle < 225:
            return {'name': 'Полнолуние', 'description': 'Пик энергии и эмоций'}
        elif 225 <= angle < 270:
            return {'name': 'Убывающая Луна', 'description': 'Время освобождения'}
        elif 270 <= angle < 315:
            return {'name': 'Последняя четверть', 'description': 'Время анализа и выводов'}
        else:
            return {'name': 'Убывающая Луна', 'description': 'Время подготовки к новому'}

    def calculate_compatibility_score(
        self, 
        sign1: YandexZodiacSign, 
        sign2: YandexZodiacSign
    ) -> Dict[str, Any]:
        """Вычисляет совместимость знаков зодиака."""
        sign1_name = sign1.value
        sign2_name = sign2.value
        
        # Получаем элементы и качества знаков
        element1 = self.elements.get(sign1_name, "earth")
        element2 = self.elements.get(sign2_name, "earth")
        quality1 = self.qualities.get(sign1_name, "mutable")
        quality2 = self.qualities.get(sign2_name, "mutable")
        
        # Базовая совместимость по элементам
        element_compatibility = self._calculate_element_compatibility(element1, element2)
        
        # Совместимость по качествам
        quality_compatibility = self._calculate_quality_compatibility(quality1, quality2)
        
        # Общий счет
        total_score = (element_compatibility + quality_compatibility) / 2
        
        return {
            'total_score': round(total_score, 1),
            'element_score': element_compatibility,
            'quality_score': quality_compatibility,
            'element1': element1,
            'element2': element2,
            'quality1': quality1,
            'quality2': quality2,
            'description': self._get_compatibility_description(total_score)
        }

    def _calculate_element_compatibility(self, element1: str, element2: str) -> float:
        """Вычисляет совместимость по элементам."""
        # Совместимость элементов (0-100)
        compatibility_matrix = {
            ('fire', 'fire'): 85,
            ('fire', 'earth'): 40,
            ('fire', 'air'): 90,
            ('fire', 'water'): 35,
            ('earth', 'earth'): 80,
            ('earth', 'air'): 45,
            ('earth', 'water'): 85,
            ('air', 'air'): 88,
            ('air', 'water'): 50,
            ('water', 'water'): 90
        }
        
        # Проверяем прямую и обратную совместимость
        score = compatibility_matrix.get((element1, element2))
        if score is None:
            score = compatibility_matrix.get((element2, element1), 50)
        
        return score

    def _calculate_quality_compatibility(self, quality1: str, quality2: str) -> float:
        """Вычисляет совместимость по качествам."""
        compatibility_matrix = {
            ('cardinal', 'cardinal'): 75,
            ('cardinal', 'fixed'): 60,
            ('cardinal', 'mutable'): 80,
            ('fixed', 'fixed'): 70,
            ('fixed', 'mutable'): 65,
            ('mutable', 'mutable'): 85
        }
        
        score = compatibility_matrix.get((quality1, quality2))
        if score is None:
            score = compatibility_matrix.get((quality2, quality1), 60)
        
        return score

    def _get_compatibility_description(self, score: float) -> str:
        """Возвращает описание совместимости по баллам."""
        if score >= 85:
            return "Отличная совместимость"
        elif score >= 70:
            return "Хорошая совместимость"
        elif score >= 55:
            return "Умеренная совместимость"
        elif score >= 40:
            return "Сложная, но возможная совместимость"
        else:
            return "Низкая совместимость"

    def get_planetary_hours(self, target_date: datetime) -> Dict[str, Any]:
        """Вычисляет планетные часы для заданной даты."""
        # Упрощенный расчет планетных часов
        weekday = target_date.weekday()  # 0 = понедельник
        
        # Правящие планеты дней недели
        day_rulers = [
            "Луна",      # Понедельник
            "Марс",      # Вторник
            "Меркурий",  # Среда
            "Юпитер",    # Четверг
            "Венера",    # Пятница
            "Сатурн",    # Суббота
            "Солнце"     # Воскресенье
        ]
        
        ruler = day_rulers[weekday]
        hour = target_date.hour
        
        return {
            'day_ruler': ruler,
            'current_hour_ruler': self._get_hour_ruler(weekday, hour),
            'favorable_hours': self._get_favorable_hours(weekday),
            'description': f"День управляется {ruler}"
        }

    def _get_hour_ruler(self, weekday: int, hour: int) -> str:
        """Возвращает планету-управителя текущего часа."""
        # Упрощенная система планетных часов
        planets_order = [
            "Солнце", "Венера", "Меркурий", "Луна", 
            "Сатурн", "Юпитер", "Марс"
        ]
        
        # Начинаем с правящей планеты дня
        day_rulers = ["Луна", "Марс", "Меркурий", "Юпитер", "Венера", "Сатурн", "Солнце"]
        start_planet = day_rulers[weekday]
        start_index = planets_order.index(start_planet)
        
        # Рассчитываем планету часа
        hour_index = (start_index + hour) % 7
        return planets_order[hour_index]

    def _get_favorable_hours(self, weekday: int) -> List[int]:
        """Возвращает благоприятные часы для дня."""
        # Упрощенная логика благоприятных часов
        favorable_patterns = [
            [1, 8, 15, 22],  # Понедельник
            [2, 9, 16, 23],  # Вторник
            [3, 10, 17, 0],  # Среда
            [4, 11, 18, 1],  # Четверг
            [5, 12, 19, 2],  # Пятница
            [6, 13, 20, 3],  # Суббота
            [7, 14, 21, 4]   # Воскресенье
        ]
        
        return favorable_patterns[weekday]