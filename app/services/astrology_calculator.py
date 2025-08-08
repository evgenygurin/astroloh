"""
Сервис астрологических вычислений с поддержкой множественных астрономических библиотек.
Автоматическое переключение между pyswisseph, skyfield и astropy в зависимости от доступности.
"""

import logging
import math
from datetime import date, datetime
from typing import Any, Dict, List

import pytz

from app.models.yandex_models import YandexZodiacSign

# Попытка импорта астрономических библиотек с graceful fallback
_astronomy_backend = None

try:
    import swisseph as swe

    _astronomy_backend = "swisseph"
    logging.info("Using Swiss Ephemeris backend for astronomical calculations")
except ImportError as e:
    logging.warning(f"Swiss Ephemeris not available: {e}")
    swe = None  # Set swe to None when import fails
    import importlib.util

    if importlib.util.find_spec("skyfield"):
        _astronomy_backend = "skyfield"
        logging.info("Using Skyfield backend for astronomical calculations")
    elif importlib.util.find_spec("astropy"):
        _astronomy_backend = "astropy"
        logging.info("Using Astropy backend for astronomical calculations")
    else:
        logging.error("No astronomy libraries available")
        _astronomy_backend = None


class AstrologyCalculator:
    """Класс для астрологических вычислений с поддержкой множественных бэкендов."""

    def __init__(self):
        self.backend = _astronomy_backend

        if not self.backend:
            logging.error(
                "No astronomy backend available. Some calculations may be limited."
            )

        # Настройка в зависимости от доступного бэкенда
        if self.backend == "swisseph" and swe is not None:
            try:
                swe.set_ephe_path("/usr/share/swisseph")  # Путь к эфемеридам
            except Exception:
                pass  # Игнорируем ошибки пути к эфемеридам

            # Планеты для расчетов Swiss Ephemeris
            self.planets = {
                "Sun": swe.SUN,
                "Moon": swe.MOON,
                "Mercury": swe.MERCURY,
                "Venus": swe.VENUS,
                "Mars": swe.MARS,
                "Jupiter": swe.JUPITER,
                "Saturn": swe.SATURN,
                "Uranus": swe.URANUS,
                "Neptune": swe.NEPTUNE,
                "Pluto": swe.PLUTO,
            }
        elif self.backend == "swisseph" and swe is None:
            # Fallback if swisseph backend was selected but import failed
            import importlib.util

            if importlib.util.find_spec("skyfield"):
                self.backend = "skyfield"
            elif importlib.util.find_spec("astropy"):
                self.backend = "astropy"
            else:
                self.backend = None

        # Initialize the selected backend properly
        if self.backend == "skyfield":
            # Инициализация Skyfield
            try:
                from skyfield.api import load

                self.skyfield_loader = load
                self.skyfield_ts = load.timescale()
                self.skyfield_planets = load("de421.bsp")  # JPL planetary ephemeris
            except (ImportError, Exception):
                # Fallback to astropy or None if skyfield not available
                import importlib.util

                if importlib.util.find_spec("astropy"):
                    self.backend = "astropy"
                else:
                    self.backend = None

        elif self.backend == "astropy":
            # Astropy не требует особой инициализации
            pass
        else:
            # Fallback: no specific backend configuration
            self.planets = {}

        # Универсальные данные для всех бэкендов
        self.planets_universal = [
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

        # Знаки зодиака
        self.zodiac_signs = [
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

        # Элементы знаков
        self.elements = {
            "овен": "fire",
            "лев": "fire",
            "стрелец": "fire",
            "телец": "earth",
            "дева": "earth",
            "козерог": "earth",
            "близнецы": "air",
            "весы": "air",
            "водолей": "air",
            "рак": "water",
            "скорпион": "water",
            "рыбы": "water",
        }

        # Качества знаков
        self.qualities = {
            "овен": "cardinal",
            "рак": "cardinal",
            "весы": "cardinal",
            "козерог": "cardinal",
            "телец": "fixed",
            "лев": "fixed",
            "скорпион": "fixed",
            "водолей": "fixed",
            "близнецы": "mutable",
            "дева": "mutable",
            "стрелец": "mutable",
            "рыбы": "mutable",
        }

    def calculate_julian_day(self, birth_datetime: datetime) -> float:
        """Вычисляет юлианский день для заданной даты и времени."""
        year = birth_datetime.year
        month = birth_datetime.month
        day = birth_datetime.day
        hour = birth_datetime.hour + birth_datetime.minute / 60.0

        if self.backend == "swisseph":
            return swe.julday(year, month, day, hour)
        elif self.backend == "skyfield":
            # Skyfield использует свой объект времени
            t = self.skyfield_ts.ut1(year, month, day, hour)
            return t.ut1
        elif self.backend == "astropy":
            # Astropy Time object для Julian Day
            from astropy.time import Time

            t = Time(birth_datetime)
            return t.jd
        else:
            # Fallback: простое вычисление Julian Day
            a = (14 - month) // 12
            y = year + 4800 - a
            m = month + 12 * a - 3
            jd = (
                day
                + (153 * m + 2) // 5
                + 365 * y
                + y // 4
                - y // 100
                + y // 400
                - 32045
            )
            return jd + (hour - 12) / 24.0

    def get_zodiac_sign_by_date(self, birth_date: date) -> YandexZodiacSign:
        """Определяет знак зодиака по дате рождения."""
        logger = logging.getLogger(__name__)
        logger.debug(f"ZODIAC_SIGN_CALCULATION_START: date={birth_date.strftime('%Y-%m-%d')}")
        
        month = birth_date.month
        day = birth_date.day
        logger.debug(f"ZODIAC_SIGN_DATE_PARSE: month={month}, day={day}")

        # Границы знаков зодиака
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            result = YandexZodiacSign.ARIES
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            result = YandexZodiacSign.TAURUS
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            result = YandexZodiacSign.GEMINI
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            result = YandexZodiacSign.CANCER
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            result = YandexZodiacSign.LEO
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            result = YandexZodiacSign.VIRGO
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            result = YandexZodiacSign.LIBRA
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            result = YandexZodiacSign.SCORPIO
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            result = YandexZodiacSign.SAGITTARIUS
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            result = YandexZodiacSign.CAPRICORN
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            result = YandexZodiacSign.AQUARIUS
        else:  # (month == 2 and day >= 19) or (month == 3 and day <= 20)
            result = YandexZodiacSign.PISCES
            
        logger.info(f"ZODIAC_SIGN_CALCULATED: date={birth_date.strftime('%Y-%m-%d')}, sign={result.value}")
        return result

    def calculate_planet_positions(
        self,
        birth_datetime: datetime,
        latitude: float = 55.7558,  # Москва по умолчанию
        longitude: float = 37.6176,
    ) -> Dict[str, Dict[str, Any]]:
        """Вычисляет позиции планет на момент рождения."""
        positions = {}

        if self.backend == "swisseph":
            jd = self.calculate_julian_day(birth_datetime)
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
                        "longitude": longitude_deg,
                        "sign": sign_name,
                        "degree_in_sign": degree_in_sign,
                        "sign_number": sign_num,
                    }

                except Exception:
                    positions[planet_name] = self._get_fallback_position(planet_name)

        elif self.backend == "skyfield":
            positions = self._calculate_positions_skyfield(
                birth_datetime, latitude, longitude
            )

        elif self.backend == "astropy":
            positions = self._calculate_positions_astropy(
                birth_datetime, latitude, longitude
            )

        else:
            # Fallback: используем упрощенные позиции
            for planet_name in self.planets_universal:
                positions[planet_name] = self._get_fallback_position(planet_name)

        return positions

    def _calculate_positions_skyfield(
        self, birth_datetime: datetime, latitude: float, longitude: float
    ) -> Dict[str, Dict[str, Any]]:
        """Вычисляет позиции планет с использованием Skyfield."""
        positions = {}
        try:
            t = self.skyfield_ts.from_datetime(birth_datetime.replace(tzinfo=pytz.UTC))

            # Получаем позиции планет
            planet_mapping = {
                "Sun": "sun",
                "Moon": "moon",
                "Mercury": "mercury",
                "Venus": "venus",
                "Mars": "mars",
                "Jupiter": "jupiter barycenter",
                "Saturn": "saturn barycenter",
                "Uranus": "uranus barycenter",
                "Neptune": "neptune barycenter",
                "Pluto": "pluto barycenter",
            }

            for planet_name, skyfield_name in planet_mapping.items():
                try:
                    planet = self.skyfield_planets[skyfield_name]
                    position = planet.at(t)
                    lat, lon, distance = position.ecliptic_latlon()
                    longitude_deg = lon.degrees

                    # Определяем знак зодиака
                    sign_num = int(longitude_deg / 30) % 12
                    sign_name = self.zodiac_signs[sign_num]
                    degree_in_sign = longitude_deg % 30

                    positions[planet_name] = {
                        "longitude": longitude_deg,
                        "sign": sign_name,
                        "degree_in_sign": degree_in_sign,
                        "sign_number": sign_num,
                    }
                except Exception:
                    positions[planet_name] = self._get_fallback_position(planet_name)

        except Exception:
            # Fallback для всех планет
            for planet_name in self.planets_universal:
                positions[planet_name] = self._get_fallback_position(planet_name)

        return positions

    def _calculate_positions_astropy(
        self, birth_datetime: datetime, latitude: float, longitude: float
    ) -> Dict[str, Dict[str, Any]]:
        """Вычисляет позиции планет с использованием Astropy."""
        positions = {}
        try:
            from astropy.coordinates import get_moon, get_sun
            from astropy.time import Time

            time_obj = Time(birth_datetime)

            # Солнце
            try:
                sun = get_sun(time_obj)
                sun_lon = sun.geocentrictrueecliptic.lon.degree
                positions["Sun"] = self._position_from_longitude(sun_lon)
            except Exception:
                positions["Sun"] = self._get_fallback_position("Sun")

            # Луна
            try:
                moon = get_moon(time_obj)
                moon_lon = moon.geocentrictrueecliptic.lon.degree
                positions["Moon"] = self._position_from_longitude(moon_lon)
            except Exception:
                positions["Moon"] = self._get_fallback_position("Moon")

            # Для остальных планет используем приблизительные позиции
            for planet_name in [
                "Mercury",
                "Venus",
                "Mars",
                "Jupiter",
                "Saturn",
                "Uranus",
                "Neptune",
                "Pluto",
            ]:
                positions[planet_name] = self._get_fallback_position(planet_name)

        except Exception:
            for planet_name in self.planets_universal:
                positions[planet_name] = self._get_fallback_position(planet_name)

        return positions

    def _position_from_longitude(self, longitude_deg: float) -> Dict[str, Any]:
        """Преобразует долготу в астрологическую позицию."""
        # Нормализуем долготу к диапазону 0-360
        longitude_deg = longitude_deg % 360
        sign_num = int(longitude_deg / 30)
        sign_name = self.zodiac_signs[sign_num]
        degree_in_sign = longitude_deg % 30

        return {
            "longitude": longitude_deg,
            "sign": sign_name,
            "degree_in_sign": degree_in_sign,
            "sign_number": sign_num,
        }

    def _get_fallback_position(self, planet_name: str) -> Dict[str, Any]:
        """Возвращает приблизительную позицию планеты для fallback."""
        # Простые приблизительные позиции планет
        fallback_positions = {
            "Sun": 0,  # Овен
            "Moon": 30,  # Телец
            "Mercury": 60,  # Близнецы
            "Venus": 90,  # Рак
            "Mars": 120,  # Лев
            "Jupiter": 150,  # Дева
            "Saturn": 180,  # Весы
            "Uranus": 210,  # Скорпион
            "Neptune": 240,  # Стрелец
            "Pluto": 270,  # Козерог
        }

        longitude_deg = fallback_positions.get(planet_name, 0)
        return self._position_from_longitude(longitude_deg)

    def calculate_houses(
        self,
        birth_datetime: datetime,
        latitude: float = 55.7558,
        longitude: float = 37.6176,
    ) -> Dict[int, Dict[str, Any]]:
        """Вычисляет астрологические дома."""
        jd = self.calculate_julian_day(birth_datetime)
        houses = {}

        if self.backend == "swisseph":
            try:
                # Используем систему домов Placidus
                cusps, ascmc = swe.houses(jd, latitude, longitude, b"P")

                for i in range(12):
                    house_num = i + 1
                    cusp_longitude = cusps[i]

                    # Определяем знак зодиака куспида дома
                    sign_num = int(cusp_longitude / 30)
                    sign_name = self.zodiac_signs[sign_num]
                    degree_in_sign = cusp_longitude % 30

                    houses[house_num] = {
                        "cusp_longitude": cusp_longitude,
                        "sign": sign_name,
                        "degree_in_sign": degree_in_sign,
                    }

                # Добавляем важные точки
                houses["ascendant"] = {
                    "longitude": ascmc[0],
                    "sign": self.zodiac_signs[int(ascmc[0] / 30)],
                    "degree_in_sign": ascmc[0] % 30,
                }

                houses["midheaven"] = {
                    "longitude": ascmc[1],
                    "sign": self.zodiac_signs[int(ascmc[1] / 30)],
                    "degree_in_sign": ascmc[1] % 30,
                }

            except Exception:
                # В случае ошибки создаем упрощенную систему домов
                for i in range(12):
                    houses[i + 1] = {
                        "cusp_longitude": i * 30,
                        "sign": self.zodiac_signs[i],
                        "degree_in_sign": 0,
                    }
        else:
            # Fallback: создаем упрощенную систему домов для не-swisseph бэкендов
            # Добавляем зависимость от широты для получения разных результатов для разных локаций
            latitude_offset = int(latitude) % 30  # Используем широту для сдвига

            for i in range(12):
                cusp_longitude = (i * 30 + latitude_offset) % 360
                sign_num = int(cusp_longitude / 30)
                houses[i + 1] = {
                    "cusp_longitude": cusp_longitude,
                    "sign": self.zodiac_signs[sign_num],
                    "degree_in_sign": cusp_longitude % 30,
                }

            # Добавляем важные точки для fallback режима (также зависящие от широты)
            asc_longitude = latitude_offset % 360
            asc_sign_num = int(asc_longitude / 30)
            houses["ascendant"] = {
                "longitude": asc_longitude,
                "sign": self.zodiac_signs[asc_sign_num],
                "degree_in_sign": asc_longitude % 30,
            }

            mc_longitude = (270 + latitude_offset) % 360
            mc_sign_num = int(mc_longitude / 30)
            houses["midheaven"] = {
                "longitude": mc_longitude,
                "sign": self.zodiac_signs[mc_sign_num],
                "degree_in_sign": mc_longitude % 30,
            }

        return houses

    def calculate_aspects(
        self, planet_positions: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Вычисляет аспекты между планетами."""
        aspects = []
        aspect_orbs = {
            0: 8,  # Соединение
            60: 6,  # Секстиль
            90: 8,  # Квадрат
            120: 8,  # Трин
            180: 8,  # Оппозиция
        }

        planets = list(planet_positions.keys())

        for i, planet1 in enumerate(planets):
            for planet2 in planets[i + 1 :]:
                pos1 = planet_positions[planet1]["longitude"]
                pos2 = planet_positions[planet2]["longitude"]

                # Вычисляем угол между планетами
                angle = abs(pos1 - pos2)
                if angle > 180:
                    angle = 360 - angle

                # Проверяем аспекты
                for aspect_angle, orb in aspect_orbs.items():
                    if abs(angle - aspect_angle) <= orb:
                        aspect_name = self._get_aspect_name(aspect_angle)
                        aspects.append({
                            "planet1": planet1,
                            "planet2": planet2,
                            "aspect": aspect_name,
                            "angle": aspect_angle,
                            "orb": abs(angle - aspect_angle),
                            "exact_angle": angle,
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
            180: "Оппозиция",
        }
        return aspect_names.get(angle, "Неизвестный")

    def calculate_moon_phase(self, target_date: datetime) -> Dict[str, Any]:
        """Вычисляет фазу Луны на заданную дату."""
        logger = logging.getLogger(__name__)
        logger.info(f"MOON_PHASE_CALCULATION_START: date={target_date.strftime('%Y-%m-%d')}, backend={self.backend}")
        
        try:
            if self.backend == "swisseph":
                logger.debug("MOON_PHASE_SWISSEPH: using_swiss_ephemeris")
                jd = self.calculate_julian_day(target_date)
                # Получаем позиции Солнца и Луны
                sun_pos, _ = swe.calc_ut(jd, swe.SUN)
                moon_pos, _ = swe.calc_ut(jd, swe.MOON)
                logger.debug(f"MOON_PHASE_POSITIONS: sun_lon={sun_pos[0]:.2f}, moon_lon={moon_pos[0]:.2f}")

                # Вычисляем угол между Солнцем и Луной
                angle = moon_pos[0] - sun_pos[0]
                if angle < 0:
                    angle += 360

            elif self.backend == "skyfield":
                logger.debug("MOON_PHASE_SKYFIELD: using_skyfield")
                t = self.skyfield_ts.from_datetime(target_date.replace(tzinfo=pytz.UTC))
                sun = self.skyfield_planets["sun"].at(t)
                moon = self.skyfield_planets["moon"].at(t)

                _, sun_lon, _ = sun.ecliptic_latlon()
                _, moon_lon, _ = moon.ecliptic_latlon()

                angle = (moon_lon.degrees - sun_lon.degrees) % 360
                logger.debug(f"MOON_PHASE_SKYFIELD_POSITIONS: sun_lon={sun_lon.degrees:.2f}, moon_lon={moon_lon.degrees:.2f}")

            elif self.backend == "astropy":
                logger.debug("MOON_PHASE_ASTROPY: using_astropy")
                from astropy.coordinates import get_moon, get_sun
                from astropy.time import Time

                time_obj = Time(target_date)
                sun = get_sun(time_obj)
                moon = get_moon(time_obj)

                sun_lon = sun.geocentrictrueecliptic.lon.degree
                moon_lon = moon.geocentrictrueecliptic.lon.degree

                angle = (moon_lon - sun_lon) % 360
                logger.debug(f"MOON_PHASE_ASTROPY_POSITIONS: sun_lon={sun_lon:.2f}, moon_lon={moon_lon:.2f}")

            else:
                # Fallback: упрощенный расчет
                logger.warning("MOON_PHASE_FALLBACK: using_simplified_calculation")
                day_of_month = target_date.day
                angle = (day_of_month / 29.5) * 360

            logger.debug(f"MOON_PHASE_ANGLE: calculated_angle={angle:.2f}")

            # Определяем фазу
            phase_info = self._get_moon_phase_info(angle)
            logger.debug(f"MOON_PHASE_INFO: phase_name='{phase_info['name']}', description='{phase_info['description']}'")

            # Вычисляем освещенность
            illumination = (1 - math.cos(math.radians(angle))) / 2 * 100
            logger.debug(f"MOON_PHASE_ILLUMINATION: illumination={illumination:.1f}%")

            result = {
                "phase_name": phase_info["name"],
                "phase_description": phase_info["description"],
                "angle": angle,
                "illumination_percent": round(illumination, 1),
                "is_waxing": bool(angle < 180),
            }
            
            logger.info(f"MOON_PHASE_CALCULATION_SUCCESS: phase='{result['phase_name']}', illumination={result['illumination_percent']}%")
            return result

        except Exception as e:
            # Упрощенный расчет в случае ошибки
            logger.error(f"MOON_PHASE_CALCULATION_ERROR: {e}")
            logger.warning("MOON_PHASE_FALLBACK_CALCULATION: using_simplified_approach")
            
            day_of_month = target_date.day
            phase_angle = (day_of_month / 29.5) * 360
            phase_info = self._get_moon_phase_info(phase_angle)

            result = {
                "phase_name": phase_info["name"],
                "phase_description": phase_info["description"],
                "angle": phase_angle,
                "illumination_percent": 50,
                "is_waxing": bool(day_of_month <= 14),
            }
            
            logger.warning(f"MOON_PHASE_FALLBACK_RESULT: phase='{result['phase_name']}', using_simplified_illumination")
            return result

    def _get_moon_phase_info(self, angle: float) -> Dict[str, str]:
        """Возвращает информацию о фазе Луны по углу."""
        if 0 <= angle < 45:
            return {
                "name": "Новолуние",
                "description": "Время новых начинаний",
            }
        elif 45 <= angle < 90:
            return {
                "name": "Растущая Луна",
                "description": "Время роста и развития",
            }
        elif 90 <= angle < 135:
            return {
                "name": "Первая четверть",
                "description": "Время действий и решений",
            }
        elif 135 <= angle < 180:
            return {
                "name": "Растущая Луна",
                "description": "Время накопления энергии",
            }
        elif 180 <= angle < 225:
            return {
                "name": "Полнолуние",
                "description": "Пик энергии и эмоций",
            }
        elif 225 <= angle < 270:
            return {
                "name": "Убывающая Луна",
                "description": "Время освобождения",
            }
        elif 270 <= angle < 315:
            return {
                "name": "Последняя четверть",
                "description": "Время анализа и выводов",
            }
        else:
            return {
                "name": "Убывающая Луна",
                "description": "Время подготовки к новому",
            }

    def calculate_compatibility_score(
        self, sign1: YandexZodiacSign, sign2: YandexZodiacSign
    ) -> Dict[str, Any]:
        """Вычисляет совместимость знаков зодиака."""
        logger = logging.getLogger(__name__)
        logger.info(f"COMPATIBILITY_CALCULATION_START: sign1={sign1.value}, sign2={sign2.value}")
        
        sign1_name = sign1.value
        sign2_name = sign2.value

        # Получаем элементы и качества знаков
        element1 = self.elements.get(sign1_name, "earth")
        element2 = self.elements.get(sign2_name, "earth")
        quality1 = self.qualities.get(sign1_name, "mutable")
        quality2 = self.qualities.get(sign2_name, "mutable")
        
        logger.debug(f"COMPATIBILITY_ELEMENTS: {sign1_name}={element1}, {sign2_name}={element2}")
        logger.debug(f"COMPATIBILITY_QUALITIES: {sign1_name}={quality1}, {sign2_name}={quality2}")

        # Базовая совместимость по элементам
        element_compatibility = self._calculate_element_compatibility(
            element1, element2
        )
        logger.debug(f"COMPATIBILITY_ELEMENT_SCORE: {element_compatibility}")

        # Совместимость по качествам
        quality_compatibility = self._calculate_quality_compatibility(
            quality1, quality2
        )
        logger.debug(f"COMPATIBILITY_QUALITY_SCORE: {quality_compatibility}")

        # Общий счет
        total_score = (element_compatibility + quality_compatibility) / 2
        logger.debug(f"COMPATIBILITY_TOTAL_SCORE: {total_score:.1f}")

        result = {
            "score": round(total_score, 1),  # For backward compatibility with tests
            "total_score": round(total_score, 1),
            "element_score": element_compatibility,
            "quality_score": quality_compatibility,
            "element1": element1,
            "element2": element2,
            "quality1": quality1,
            "quality2": quality2,
            "description": self._get_compatibility_description(total_score),
        }
        
        logger.info(f"COMPATIBILITY_CALCULATION_SUCCESS: {sign1.value}+{sign2.value}={result['total_score']}, description='{result['description']}'")
        return result

    def _calculate_element_compatibility(self, element1: str, element2: str) -> float:
        """Вычисляет совместимость по элементам."""
        # Совместимость элементов (0-100)
        compatibility_matrix = {
            ("fire", "fire"): 85,
            ("fire", "earth"): 40,
            ("fire", "air"): 90,
            ("fire", "water"): 35,
            ("earth", "earth"): 80,
            ("earth", "air"): 45,
            ("earth", "water"): 85,
            ("air", "air"): 88,
            ("air", "water"): 50,
            ("water", "water"): 90,
        }

        # Проверяем прямую и обратную совместимость
        score = compatibility_matrix.get((element1, element2))
        if score is None:
            score = compatibility_matrix.get((element2, element1), 50)

        return score

    def _calculate_quality_compatibility(self, quality1: str, quality2: str) -> float:
        """Вычисляет совместимость по качествам."""
        compatibility_matrix = {
            ("cardinal", "cardinal"): 75,
            ("cardinal", "fixed"): 60,
            ("cardinal", "mutable"): 80,
            ("fixed", "fixed"): 70,
            ("fixed", "mutable"): 65,
            ("mutable", "mutable"): 85,
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
        logger = logging.getLogger(__name__)
        logger.debug(f"PLANETARY_HOURS_CALCULATION_START: date={target_date.strftime('%Y-%m-%d %H:%M')}")
        
        # Упрощенный расчет планетных часов
        weekday = target_date.weekday()  # 0 = понедельник
        hour = target_date.hour
        logger.debug(f"PLANETARY_HOURS_TIME: weekday={weekday}, hour={hour}")

        # Правящие планеты дней недели
        day_rulers = [
            "Луна",  # Понедельник
            "Марс",  # Вторник
            "Меркурий",  # Среда
            "Юпитер",  # Четверг
            "Венера",  # Пятница
            "Сатурн",  # Суббота
            "Солнце",  # Воскресенье
        ]

        ruler = day_rulers[weekday]
        hour_ruler = self._get_hour_ruler(weekday, hour)
        favorable_hours = self._get_favorable_hours(weekday)
        
        logger.debug(f"PLANETARY_HOURS_RULERS: day_ruler={ruler}, hour_ruler={hour_ruler}")
        logger.debug(f"PLANETARY_HOURS_FAVORABLE: hours={favorable_hours}")

        result = {
            "day_ruler": ruler,
            "current_hour_ruler": hour_ruler,
            "favorable_hours": favorable_hours,
            "description": f"День управляется {ruler}",
        }
        
        logger.info(f"PLANETARY_HOURS_CALCULATION_SUCCESS: day_ruler={ruler}, current_hour_ruler={hour_ruler}")
        return result

    def _get_hour_ruler(self, weekday: int, hour: int) -> str:
        """Возвращает планету-управителя текущего часа."""
        # Упрощенная система планетных часов
        planets_order = [
            "Солнце",
            "Венера",
            "Меркурий",
            "Луна",
            "Сатурн",
            "Юпитер",
            "Марс",
        ]

        # Начинаем с правящей планеты дня
        day_rulers = [
            "Луна",
            "Марс",
            "Меркурий",
            "Юпитер",
            "Венера",
            "Сатурн",
            "Солнце",
        ]
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
            [7, 14, 21, 4],  # Воскресенье
        ]

        return favorable_patterns[weekday]

    def get_backend_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущем астрономическом бэкенде."""
        return {
            "backend": self.backend,
            "available_backends": self._get_available_backends(),
            "capabilities": self._get_backend_capabilities(),
        }

    def _get_available_backends(self) -> List[str]:
        """Проверяет доступные астрономические бэкенды."""
        available = []
        import importlib.util

        if importlib.util.find_spec("swisseph"):
            available.append("swisseph")

        if importlib.util.find_spec("skyfield"):
            available.append("skyfield")

        if importlib.util.find_spec("astropy"):
            available.append("astropy")

        return available

    def _get_backend_capabilities(self) -> Dict[str, bool]:
        """Возвращает возможности текущего бэкенда."""
        if self.backend == "swisseph":
            return {
                "planet_positions": True,
                "moon_phases": True,
                "houses": True,
                "aspects": True,
                "high_precision": True,
            }
        elif self.backend == "skyfield":
            return {
                "planet_positions": True,
                "moon_phases": True,
                "houses": False,  # Ограниченная поддержка домов
                "aspects": True,
                "high_precision": True,
            }
        elif self.backend == "astropy":
            return {
                "planet_positions": True,  # Только Солнце и Луна точно
                "moon_phases": True,
                "houses": False,
                "aspects": True,
                "high_precision": False,  # Ограниченная точность для планет
            }
        else:
            return {
                "planet_positions": False,
                "moon_phases": False,
                "houses": False,
                "aspects": False,
                "high_precision": False,
            }
