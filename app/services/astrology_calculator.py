"""
Сервис астрологических вычислений на базе kerykeion.
Полная реализация всех возможностей современной астрологии.
"""

import logging
import math
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import pytz

from app.models.yandex_models import YandexZodiacSign

# Попытка импорта kerykeion и связанных библиотек
try:
    from kerykeion import AstrologicalSubject

    KERYKEION_AVAILABLE = True
    logging.info("Kerykeion library available for advanced calculations")
except ImportError as e:
    logging.warning(f"Kerykeion not fully available: {e}")
    KERYKEION_AVAILABLE = False
    AstrologicalSubject = None

# Попытка импорта pyswisseph напрямую для дополнительных функций
try:
    import swisseph as swe

    SWISSEPH_AVAILABLE = True
    logging.info("Swiss Ephemeris available for high-precision calculations")
except ImportError:
    SWISSEPH_AVAILABLE = False
    swe = None

# Попытка импорта альтернативных библиотек
try:
    from skyfield.api import load

    SKYFIELD_AVAILABLE = True
    ts = load.timescale()
    eph = load("de421.bsp")
    logging.info("Skyfield available as fallback")
except ImportError:
    SKYFIELD_AVAILABLE = False
    ts = None
    eph = None


class HouseSystem(Enum):
    """Системы домов"""

    PLACIDUS = "P"
    KOCH = "K"
    REGIOMONTANUS = "R"
    CAMPANUS = "C"
    EQUAL = "E"
    WHOLE_SIGN = "W"
    MERIDIAN = "X"
    MORINUS = "M"
    PORPHYRY = "O"
    ALCABITUS = "B"
    AZIMUTHAL = "H"
    POLICH_PAGE = "T"
    VEHLOW = "V"


class AspectType(Enum):
    """Типы аспектов"""

    CONJUNCTION = (0, 10, "Соединение", "☌")
    OPPOSITION = (180, 10, "Оппозиция", "☍")
    TRINE = (120, 9, "Трин", "△")
    SQUARE = (90, 8, "Квадрат", "□")
    SEXTILE = (60, 6, "Секстиль", "⚹")
    QUINCUNX = (150, 3, "Квинконс", "⚻")
    SEMISQUARE = (45, 2, "Полуквадрат", "∠")
    SESQUISQUARE = (135, 2, "Полутораквадрат", "⚼")
    SEMISEXTILE = (30, 2, "Полусекстиль", "⚺")
    QUINTILE = (72, 2, "Квинтиль", "Q")
    BIQUINTILE = (144, 2, "Биквинтиль", "bQ")

    def __init__(self, angle: float, orb: float, name_ru: str, symbol: str):
        self.angle = angle
        self.orb = orb
        self.name_ru = name_ru
        self.symbol = symbol


class CelestialBody(Enum):
    """Небесные тела"""

    SUN = ("Солнце", "☉", 0)
    MOON = ("Луна", "☽", 1)
    MERCURY = ("Меркурий", "☿", 2)
    VENUS = ("Венера", "♀", 3)
    MARS = ("Марс", "♂", 4)
    JUPITER = ("Юпитер", "♃", 5)
    SATURN = ("Сатурн", "♄", 6)
    URANUS = ("Уран", "♅", 7)
    NEPTUNE = ("Нептун", "♆", 8)
    PLUTO = ("Плутон", "♇", 9)
    TRUE_NODE = ("Северный узел", "☊", 11)
    SOUTH_NODE = ("Южный узел", "☋", 12)
    CHIRON = ("Хирон", "⚷", 15)
    LILITH = ("Лилит", "⚸", 13)
    CERES = ("Церера", "⚳", 17)
    PALLAS = ("Паллада", "⚴", 18)
    JUNO = ("Юнона", "⚵", 19)
    VESTA = ("Веста", "⚶", 20)

    def __init__(self, name_ru: str, symbol: str, swiss_id: int):
        self.name_ru = name_ru
        self.symbol = symbol
        self.swiss_id = swiss_id


class ZodiacSign(Enum):
    """Знаки зодиака с полной информацией"""

    ARIES = ("Овен", "♈", "fire", "cardinal", "Mars", 0)
    TAURUS = ("Телец", "♉", "earth", "fixed", "Venus", 30)
    GEMINI = ("Близнецы", "♊", "air", "mutable", "Mercury", 60)
    CANCER = ("Рак", "♋", "water", "cardinal", "Moon", 90)
    LEO = ("Лев", "♌", "fire", "fixed", "Sun", 120)
    VIRGO = ("Дева", "♍", "earth", "mutable", "Mercury", 150)
    LIBRA = ("Весы", "♎", "air", "cardinal", "Venus", 180)
    SCORPIO = ("Скорпион", "♏", "water", "fixed", "Mars/Pluto", 210)
    SAGITTARIUS = ("Стрелец", "♐", "fire", "mutable", "Jupiter", 240)
    CAPRICORN = ("Козерог", "♑", "earth", "cardinal", "Saturn", 270)
    AQUARIUS = ("Водолей", "♒", "air", "fixed", "Saturn/Uranus", 300)
    PISCES = ("Рыбы", "♓", "water", "mutable", "Jupiter/Neptune", 330)

    def __init__(
        self,
        name_ru: str,
        symbol: str,
        element: str,
        quality: str,
        ruler: str,
        start_degree: int,
    ):
        self.name_ru = name_ru
        self.symbol = symbol
        self.element = element
        self.quality = quality
        self.ruler = ruler
        self.start_degree = start_degree


class ArabicPart(Enum):
    """Арабские части/жребии"""

    FORTUNE = ("Колесо Фортуны", "ASC + Moon - Sun")
    SPIRIT = ("Часть Духа", "ASC + Sun - Moon")
    LOVE = ("Часть Любви", "ASC + Venus - Sun")
    MARRIAGE = ("Часть Брака", "ASC + 7th_cusp - Venus")
    CHILDREN = ("Часть Детей", "ASC + Jupiter - Moon")
    DEATH = ("Часть Смерти", "ASC + 8th_cusp - Moon")
    DISEASE = ("Часть Болезни", "ASC + Mars - Saturn")
    CAREER = ("Часть Карьеры", "ASC + MC - Sun")
    WEALTH = ("Часть Богатства", "ASC + 2nd_cusp - 2nd_ruler")

    def __init__(self, name_ru: str, formula: str):
        self.name_ru = name_ru
        self.formula = formula


class ProgressionType(Enum):
    """Типы прогрессий"""

    SECONDARY = "Вторичная прогрессия"
    SOLAR_ARC = "Солнечная дуга"
    PRIMARY = "Первичная дирекция"
    TERTIARY = "Третичная прогрессия"


class TransitPeriod(Enum):
    """Периоды транзитов"""

    TODAY = "Сегодня"
    WEEK = "Неделя"
    MONTH = "Месяц"
    YEAR = "Год"
    CUSTOM = "Произвольный период"


class ChartPoint:
    """Точка на астрологической карте"""

    def __init__(
        self,
        name: str,
        longitude: float,
        latitude: float = 0,
        speed: float = 0,
        retrograde: bool = False,
        sign: Optional[ZodiacSign] = None,
        house: Optional[int] = None,
    ):
        self.name = name
        self.longitude = longitude
        self.latitude = latitude
        self.speed = speed
        self.retrograde = retrograde
        self.sign = sign or self._calculate_sign(longitude)
        self.house = house
        self.degree_in_sign = longitude % 30

    def _calculate_sign(self, longitude: float) -> ZodiacSign:
        """Определяет знак по долготе"""
        signs = list(ZodiacSign)
        sign_index = int(longitude / 30) % 12
        return signs[sign_index]

    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь"""
        return {
            "name": self.name,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "speed": self.speed,
            "retrograde": self.retrograde,
            "sign": self.sign.name_ru if self.sign else None,
            "sign_symbol": self.sign.symbol if self.sign else None,
            "degree_in_sign": self.degree_in_sign,
            "house": self.house,
        }


class NatalChart:
    """Натальная карта"""

    def __init__(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "UTC",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
    ):
        self.name = name
        self.birth_datetime = birth_datetime
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.house_system = house_system
        self.planets: Dict[str, ChartPoint] = {}
        self.houses: Dict[int, Dict[str, Any]] = {}
        self.aspects: List[Dict[str, Any]] = []
        self.arabic_parts: Dict[str, float] = {}
        self.fixed_stars: List[Dict[str, Any]] = []

        # Kerykeion subject if available
        self.kerykeion_subject = None
        if KERYKEION_AVAILABLE and AstrologicalSubject:
            try:
                self.kerykeion_subject = AstrologicalSubject(
                    name=name,
                    year=birth_datetime.year,
                    month=birth_datetime.month,
                    day=birth_datetime.day,
                    hour=birth_datetime.hour,
                    minute=birth_datetime.minute,
                    lat=latitude,
                    lng=longitude,
                    tz_str=timezone,
                    city="Unknown",
                    nation="Unknown",
                )
            except Exception as e:
                logging.warning(f"Failed to create Kerykeion subject: {e}")


class AstrologyCalculator:
    """Класс для астрологических вычислений с полным функционалом kerykeion"""

    def __init__(self):
        self.backend = self._detect_backend()
        self._init_astronomical_data()
        logging.info(
            f"AstrologyCalculator initialized with backend: {self.backend}"
        )

    def _detect_backend(self) -> str:
        """Определяет доступный бэкенд"""
        if KERYKEION_AVAILABLE:
            return "kerykeion"
        elif SWISSEPH_AVAILABLE:
            return "swisseph"
        elif SKYFIELD_AVAILABLE:
            return "skyfield"
        else:
            return "fallback"

    def _init_astronomical_data(self):
        """Инициализирует астрономические данные"""
        # Базовые данные для всех бэкендов
        self.zodiac_signs = list(ZodiacSign)
        self.celestial_bodies = list(CelestialBody)
        self.aspect_types = list(AspectType)
        self.arabic_parts = list(ArabicPart)

        # Элементы и качества для совместимости
        self.elements = {
            sign.name_ru.lower(): sign.element for sign in ZodiacSign
        }
        self.qualities = {
            sign.name_ru.lower(): sign.quality for sign in ZodiacSign
        }

        # Инициализация Swiss Ephemeris если доступен
        if SWISSEPH_AVAILABLE and swe:
            try:
                swe.set_ephe_path("/usr/share/swisseph")
            except Exception:
                pass

    def get_zodiac_sign_by_date(self, birth_date: date) -> YandexZodiacSign:
        """Определяет знак зодиака по дате рождения"""
        logging.getLogger(__name__)
        month = birth_date.month
        day = birth_date.day

        # Точные границы знаков зодиака
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
        else:
            return YandexZodiacSign.PISCES

    def create_natal_chart(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float = 55.7558,
        longitude: float = 37.6176,
        timezone: str = "Europe/Moscow",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
    ) -> NatalChart:
        """Создает полную натальную карту"""
        chart = NatalChart(
            name, birth_datetime, latitude, longitude, timezone, house_system
        )

        # Вычисляем позиции планет
        chart.planets = self.calculate_planet_positions(
            birth_datetime, latitude, longitude
        )

        # Вычисляем дома
        chart.houses = self.calculate_houses(
            birth_datetime, latitude, longitude, house_system
        )

        # Вычисляем аспекты
        chart.aspects = self.calculate_aspects(chart.planets)

        # Вычисляем арабские части
        chart.arabic_parts = self.calculate_arabic_parts(chart)

        # Добавляем фиксированные звезды
        chart.fixed_stars = self.calculate_fixed_stars(
            birth_datetime, latitude, longitude
        )

        return chart

    def calculate_planet_positions(
        self,
        birth_datetime: datetime,
        latitude: float = 55.7558,
        longitude: float = 37.6176,
    ) -> Dict[str, Dict[str, Any]]:
        """Вычисляет позиции планет и других небесных тел"""
        positions = {}

        if self.backend == "kerykeion" and KERYKEION_AVAILABLE:
            try:
                subject = AstrologicalSubject(
                    name="Temp",
                    year=birth_datetime.year,
                    month=birth_datetime.month,
                    day=birth_datetime.day,
                    hour=birth_datetime.hour,
                    minute=birth_datetime.minute,
                    lat=latitude,
                    lng=longitude,
                    tz_str="UTC",
                )

                # Основные планеты
                planet_mapping = {
                    "Sun": "sun",
                    "Moon": "moon",
                    "Mercury": "mercury",
                    "Venus": "venus",
                    "Mars": "mars",
                    "Jupiter": "jupiter",
                    "Saturn": "saturn",
                    "Uranus": "uranus",
                    "Neptune": "neptune",
                    "Pluto": "pluto",
                }

                for planet_name, attr_name in planet_mapping.items():
                    planet_data = getattr(subject, attr_name, None)
                    if planet_data:
                        positions[planet_name] = {
                            "longitude": planet_data.get("lon", 0),
                            "latitude": planet_data.get("lat", 0),
                            "speed": planet_data.get("speed", 0),
                            "retrograde": planet_data.get("retrograde", False),
                            "sign": planet_data.get("sign", ""),
                            "degree_in_sign": planet_data.get("lon", 0) % 30,
                            "house": planet_data.get("house", None),
                        }

                # Лунные узлы
                if hasattr(subject, "true_node"):
                    node_data = subject.true_node
                    positions["TrueNode"] = {
                        "longitude": node_data.get("lon", 0),
                        "sign": node_data.get("sign", ""),
                        "degree_in_sign": node_data.get("lon", 0) % 30,
                    }

                # Хирон
                if hasattr(subject, "chiron"):
                    chiron_data = subject.chiron
                    positions["Chiron"] = {
                        "longitude": chiron_data.get("lon", 0),
                        "sign": chiron_data.get("sign", ""),
                        "degree_in_sign": chiron_data.get("lon", 0) % 30,
                    }

                # Лилит
                if hasattr(subject, "mean_lilith"):
                    lilith_data = subject.mean_lilith
                    positions["Lilith"] = {
                        "longitude": lilith_data.get("lon", 0),
                        "sign": lilith_data.get("sign", ""),
                        "degree_in_sign": lilith_data.get("lon", 0) % 30,
                    }

            except Exception as e:
                logging.error(f"Kerykeion calculation failed: {e}")
                positions = self._calculate_positions_fallback(
                    birth_datetime, latitude, longitude
                )

        elif self.backend == "swisseph" and SWISSEPH_AVAILABLE:
            positions = self._calculate_positions_swisseph(
                birth_datetime, latitude, longitude
            )

        elif self.backend == "skyfield" and SKYFIELD_AVAILABLE:
            positions = self._calculate_positions_skyfield(
                birth_datetime, latitude, longitude
            )

        else:
            positions = self._calculate_positions_fallback(
                birth_datetime, latitude, longitude
            )

        return positions

    def _calculate_positions_swisseph(
        self, birth_datetime: datetime, latitude: float, longitude: float
    ) -> Dict[str, Dict[str, Any]]:
        """Вычисляет позиции с помощью Swiss Ephemeris"""
        positions = {}
        jd = swe.julday(
            birth_datetime.year,
            birth_datetime.month,
            birth_datetime.day,
            birth_datetime.hour + birth_datetime.minute / 60.0,
        )

        planet_ids = {
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
            "TrueNode": swe.TRUE_NODE,
            "Chiron": swe.CHIRON,
        }

        for planet_name, planet_id in planet_ids.items():
            try:
                pos, ret = swe.calc_ut(jd, planet_id)
                longitude_deg = pos[0]
                latitude_deg = pos[1]
                speed = pos[3]

                sign_num = int(longitude_deg / 30)
                sign = self.zodiac_signs[sign_num]

                positions[planet_name] = {
                    "longitude": longitude_deg,
                    "latitude": latitude_deg,
                    "speed": speed,
                    "retrograde": speed < 0,
                    "sign": sign.name_ru,
                    "degree_in_sign": longitude_deg % 30,
                }
            except Exception as e:
                logging.warning(f"Failed to calculate {planet_name}: {e}")

        return positions

    def _calculate_positions_skyfield(
        self, birth_datetime: datetime, latitude: float, longitude: float
    ) -> Dict[str, Dict[str, Any]]:
        """Вычисляет позиции с помощью Skyfield"""
        positions = {}

        if not ts or not eph:
            return self._calculate_positions_fallback(
                birth_datetime, latitude, longitude
            )

        t = ts.from_datetime(birth_datetime.replace(tzinfo=pytz.UTC))

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

        earth = eph["earth"]

        for planet_name, skyfield_name in planet_mapping.items():
            try:
                planet = eph[skyfield_name]
                astrometric = earth.at(t).observe(planet)
                lat, lon, distance = astrometric.ecliptic_latlon()

                longitude_deg = lon.degrees
                latitude_deg = lat.degrees

                sign_num = int(longitude_deg / 30) % 12
                sign = self.zodiac_signs[sign_num]

                positions[planet_name] = {
                    "longitude": longitude_deg,
                    "latitude": latitude_deg,
                    "speed": 0,  # Skyfield не дает скорость напрямую
                    "retrograde": False,  # Требует дополнительных вычислений
                    "sign": sign.name_ru,
                    "degree_in_sign": longitude_deg % 30,
                }
            except Exception as e:
                logging.warning(f"Failed to calculate {planet_name}: {e}")

        return positions

    def _calculate_positions_fallback(
        self, birth_datetime: datetime, latitude: float, longitude: float
    ) -> Dict[str, Dict[str, Any]]:
        """Упрощенный расчет позиций для fallback режима"""
        positions = {}

        # Простая аппроксимация позиций основных планет
        day_of_year = birth_datetime.timetuple().tm_yday
        year_fraction = day_of_year / 365.25

        # Средние угловые скорости планет (градусов в год)
        speeds = {
            "Sun": 360,
            "Moon": 4680,  # ~13 оборотов в год
            "Mercury": 1480,
            "Venus": 585,
            "Mars": 191,
            "Jupiter": 30.3,
            "Saturn": 12.2,
            "Uranus": 4.3,
            "Neptune": 2.2,
            "Pluto": 1.5,
        }

        # Начальные позиции на эпоху J2000
        j2000_positions = {
            "Sun": 280.5,
            "Moon": 218.3,
            "Mercury": 252.3,
            "Venus": 181.9,
            "Mars": 355.4,
            "Jupiter": 34.4,
            "Saturn": 50.1,
            "Uranus": 314.1,
            "Neptune": 304.9,
            "Pluto": 250.1,
        }

        years_since_2000 = birth_datetime.year - 2000 + year_fraction

        for planet_name in speeds:
            # Вычисляем приблизительную позицию
            base_position = j2000_positions[planet_name]
            yearly_motion = speeds[planet_name]
            current_position = (
                base_position + yearly_motion * years_since_2000
            ) % 360

            sign_num = int(current_position / 30) % 12
            sign = self.zodiac_signs[sign_num]

            positions[planet_name] = {
                "longitude": current_position,
                "latitude": 0,
                "speed": yearly_motion / 365.25,
                "retrograde": False,
                "sign": sign.name_ru,
                "degree_in_sign": current_position % 30,
            }

        return positions

    def calculate_houses(
        self,
        birth_datetime: datetime,
        latitude: float = 55.7558,
        longitude: float = 37.6176,
        house_system: HouseSystem = HouseSystem.PLACIDUS,
    ) -> Dict[int, Dict[str, Any]]:
        """Вычисляет астрологические дома"""
        houses = {}

        if self.backend == "kerykeion" and KERYKEION_AVAILABLE:
            try:
                subject = AstrologicalSubject(
                    name="Temp",
                    year=birth_datetime.year,
                    month=birth_datetime.month,
                    day=birth_datetime.day,
                    hour=birth_datetime.hour,
                    minute=birth_datetime.minute,
                    lat=latitude,
                    lng=longitude,
                    tz_str="UTC",
                )

                # Kerykeion автоматически вычисляет дома
                for i in range(1, 13):
                    house_name = f"house{i}"
                    if hasattr(subject, house_name):
                        house_data = getattr(subject, house_name)
                        cusp_longitude = house_data.get("position", i * 30)
                        sign_num = int(cusp_longitude / 30) % 12
                        sign = self.zodiac_signs[sign_num]

                        houses[i] = {
                            "cusp_longitude": cusp_longitude,
                            "sign": sign.name_ru,
                            "degree_in_sign": cusp_longitude % 30,
                        }

                # Добавляем углы
                if hasattr(subject, "first_house"):
                    asc_data = subject.first_house
                    houses["ascendant"] = {
                        "longitude": asc_data.get("position", 0),
                        "sign": asc_data.get("sign", ""),
                        "degree_in_sign": asc_data.get("position", 0) % 30,
                    }

                if hasattr(subject, "tenth_house"):
                    mc_data = subject.tenth_house
                    houses["midheaven"] = {
                        "longitude": mc_data.get("position", 270),
                        "sign": mc_data.get("sign", ""),
                        "degree_in_sign": mc_data.get("position", 270) % 30,
                    }

            except Exception as e:
                logging.error(f"Kerykeion houses calculation failed: {e}")
                houses = self._calculate_houses_fallback(
                    birth_datetime, latitude, longitude
                )

        elif self.backend == "swisseph" and SWISSEPH_AVAILABLE:
            jd = swe.julday(
                birth_datetime.year,
                birth_datetime.month,
                birth_datetime.day,
                birth_datetime.hour + birth_datetime.minute / 60.0,
            )

            try:
                cusps, ascmc = swe.houses(
                    jd, latitude, longitude, house_system.value.encode()
                )

                for i in range(12):
                    house_num = i + 1
                    cusp_longitude = cusps[i]
                    sign_num = int(cusp_longitude / 30) % 12
                    sign = self.zodiac_signs[sign_num]

                    houses[house_num] = {
                        "cusp_longitude": cusp_longitude,
                        "sign": sign.name_ru,
                        "degree_in_sign": cusp_longitude % 30,
                    }

                # Углы
                houses["ascendant"] = {
                    "longitude": ascmc[0],
                    "sign": self.zodiac_signs[int(ascmc[0] / 30) % 12].name_ru,
                    "degree_in_sign": ascmc[0] % 30,
                }

                houses["midheaven"] = {
                    "longitude": ascmc[1],
                    "sign": self.zodiac_signs[int(ascmc[1] / 30) % 12].name_ru,
                    "degree_in_sign": ascmc[1] % 30,
                }

            except Exception as e:
                logging.error(
                    f"Swiss Ephemeris houses calculation failed: {e}"
                )
                houses = self._calculate_houses_fallback(
                    birth_datetime, latitude, longitude
                )

        else:
            houses = self._calculate_houses_fallback(
                birth_datetime, latitude, longitude
            )

        return houses

    def _calculate_houses_fallback(
        self, birth_datetime: datetime, latitude: float, longitude: float
    ) -> Dict[int, Dict[str, Any]]:
        """Упрощенный расчет домов для fallback режима"""
        houses = {}

        # Вычисляем приблизительный асцендент
        hour_angle = (birth_datetime.hour + birth_datetime.minute / 60) * 15
        asc_longitude = (hour_angle + longitude) % 360

        # Равнодомная система
        for i in range(12):
            house_num = i + 1
            cusp_longitude = (asc_longitude + i * 30) % 360
            sign_num = int(cusp_longitude / 30) % 12
            sign = self.zodiac_signs[sign_num]

            houses[house_num] = {
                "cusp_longitude": cusp_longitude,
                "sign": sign.name_ru,
                "degree_in_sign": cusp_longitude % 30,
            }

        # Углы
        houses["ascendant"] = {
            "longitude": asc_longitude,
            "sign": self.zodiac_signs[int(asc_longitude / 30) % 12].name_ru,
            "degree_in_sign": asc_longitude % 30,
        }

        mc_longitude = (asc_longitude + 270) % 360
        houses["midheaven"] = {
            "longitude": mc_longitude,
            "sign": self.zodiac_signs[int(mc_longitude / 30) % 12].name_ru,
            "degree_in_sign": mc_longitude % 30,
        }

        return houses

    def calculate_aspects(
        self,
        planet_positions: Dict[str, Dict[str, Any]],
        orb_factor: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Вычисляет аспекты между планетами с учетом орбисов"""
        aspects = []
        planets = list(planet_positions.keys())

        for i, planet1 in enumerate(planets):
            for planet2 in planets[i + 1 :]:
                pos1 = planet_positions[planet1].get("longitude", 0)
                pos2 = planet_positions[planet2].get("longitude", 0)

                # Вычисляем угол между планетами
                angle = abs(pos1 - pos2)
                if angle > 180:
                    angle = 360 - angle

                # Проверяем все типы аспектов
                for aspect_type in AspectType:
                    orb = aspect_type.orb * orb_factor
                    if abs(angle - aspect_type.angle) <= orb:
                        aspects.append(
                            {
                                "planet1": planet1,
                                "planet2": planet2,
                                "aspect": aspect_type.name_ru,
                                "aspect_symbol": aspect_type.symbol,
                                "angle": aspect_type.angle,
                                "actual_angle": angle,
                                "orb": abs(angle - aspect_type.angle),
                                "applying": self._is_aspect_applying(
                                    planet_positions[planet1],
                                    planet_positions[planet2],
                                    angle,
                                    aspect_type.angle,
                                ),
                            }
                        )
                        break

        return aspects

    def _is_aspect_applying(
        self,
        planet1_data: Dict,
        planet2_data: Dict,
        current_angle: float,
        exact_angle: float,
    ) -> bool:
        """Определяет, является ли аспект сходящимся"""
        speed1 = planet1_data.get("speed", 0)
        speed2 = planet2_data.get("speed", 0)

        # Если угол уменьшается к точному значению - аспект сходящийся
        if current_angle > exact_angle:
            return speed1 > speed2
        else:
            return speed1 < speed2

    def calculate_arabic_parts(self, chart: NatalChart) -> Dict[str, float]:
        """Вычисляет арабские части/жребии"""
        parts = {}

        if not chart.planets or not chart.houses:
            return parts

        # Получаем необходимые точки
        asc = chart.houses.get("ascendant", {}).get("longitude", 0)
        mc = chart.houses.get("midheaven", {}).get("longitude", 0)
        sun = chart.planets.get("Sun", {}).get("longitude", 0)
        moon = chart.planets.get("Moon", {}).get("longitude", 0)
        venus = chart.planets.get("Venus", {}).get("longitude", 0)
        mars = chart.planets.get("Mars", {}).get("longitude", 0)
        jupiter = chart.planets.get("Jupiter", {}).get("longitude", 0)
        saturn = chart.planets.get("Saturn", {}).get("longitude", 0)

        # Колесо Фортуны (дневная/ночная формула)
        is_day_chart = sun > asc or sun < (asc + 180) % 360
        if is_day_chart:
            parts["Fortune"] = (asc + moon - sun) % 360
        else:
            parts["Fortune"] = (asc + sun - moon) % 360

        # Часть Духа
        if is_day_chart:
            parts["Spirit"] = (asc + sun - moon) % 360
        else:
            parts["Spirit"] = (asc + moon - sun) % 360

        # Часть Любви
        parts["Love"] = (asc + venus - sun) % 360

        # Часть Брака
        seventh_cusp = chart.houses.get(7, {}).get(
            "cusp_longitude", (asc + 180) % 360
        )
        parts["Marriage"] = (asc + seventh_cusp - venus) % 360

        # Часть Детей
        parts["Children"] = (asc + jupiter - moon) % 360

        # Часть Карьеры
        parts["Career"] = (asc + mc - sun) % 360

        # Часть Болезни
        parts["Disease"] = (asc + mars - saturn) % 360

        # Часть Богатства
        second_cusp = chart.houses.get(2, {}).get(
            "cusp_longitude", (asc + 30) % 360
        )
        parts["Wealth"] = (asc + second_cusp - jupiter) % 360

        return parts

    def calculate_fixed_stars(
        self, birth_datetime: datetime, latitude: float, longitude: float
    ) -> List[Dict[str, Any]]:
        """Вычисляет позиции важных фиксированных звезд"""
        fixed_stars = []

        # Основные фиксированные звезды с их эклиптическими координатами (приблизительно на 2000 год)
        stars_data = [
            {
                "name": "Регул",
                "longitude": 150.0,
                "magnitude": 1.35,
                "nature": "Mars-Jupiter",
            },
            {
                "name": "Спика",
                "longitude": 203.8,
                "magnitude": 0.97,
                "nature": "Venus-Mars",
            },
            {
                "name": "Альдебаран",
                "longitude": 69.9,
                "magnitude": 0.85,
                "nature": "Mars",
            },
            {
                "name": "Антарес",
                "longitude": 249.7,
                "magnitude": 1.09,
                "nature": "Mars-Jupiter",
            },
            {
                "name": "Фомальгаут",
                "longitude": 333.9,
                "magnitude": 1.16,
                "nature": "Venus-Mercury",
            },
            {
                "name": "Сириус",
                "longitude": 104.0,
                "magnitude": -1.46,
                "nature": "Jupiter-Mars",
            },
            {
                "name": "Канопус",
                "longitude": 105.0,
                "magnitude": -0.74,
                "nature": "Saturn-Jupiter",
            },
            {
                "name": "Арктур",
                "longitude": 204.0,
                "magnitude": -0.05,
                "nature": "Mars-Jupiter",
            },
            {
                "name": "Вега",
                "longitude": 285.2,
                "magnitude": 0.03,
                "nature": "Venus-Mercury",
            },
            {
                "name": "Капелла",
                "longitude": 81.9,
                "magnitude": 0.08,
                "nature": "Mars-Mercury",
            },
            {
                "name": "Ригель",
                "longitude": 77.0,
                "magnitude": 0.13,
                "nature": "Jupiter-Mars",
            },
            {
                "name": "Процион",
                "longitude": 115.9,
                "magnitude": 0.37,
                "nature": "Mercury-Mars",
            },
            {
                "name": "Бетельгейзе",
                "longitude": 89.0,
                "magnitude": 0.50,
                "nature": "Mars-Mercury",
            },
            {
                "name": "Альтаир",
                "longitude": 301.7,
                "magnitude": 0.76,
                "nature": "Mars-Jupiter",
            },
            {
                "name": "Поллукс",
                "longitude": 113.1,
                "magnitude": 1.14,
                "nature": "Mars",
            },
        ]

        # Прецессия: ~50.3" в год или 0.014 градуса в год
        years_since_2000 = (
            birth_datetime.year - 2000 + birth_datetime.month / 12
        )
        precession = years_since_2000 * 0.014

        for star in stars_data:
            current_longitude = (star["longitude"] + precession) % 360
            sign_num = int(current_longitude / 30) % 12
            sign = self.zodiac_signs[sign_num]

            fixed_stars.append(
                {
                    "name": star["name"],
                    "longitude": current_longitude,
                    "sign": sign.name_ru,
                    "degree_in_sign": current_longitude % 30,
                    "magnitude": star["magnitude"],
                    "nature": star["nature"],
                }
            )

        return fixed_stars

    def calculate_synastry(
        self, chart1: NatalChart, chart2: NatalChart, orb_factor: float = 1.2
    ) -> Dict[str, Any]:
        """Вычисляет синастрию между двумя картами"""
        synastry_data = {
            "aspects": [],
            "compatibility_score": 0,
            "element_compatibility": {},
            "quality_compatibility": {},
            "house_overlays": {},
            "composite_midpoints": {},
        }

        # Вычисляем межкартовые аспекты
        for planet1_name, planet1_data in chart1.planets.items():
            for planet2_name, planet2_data in chart2.planets.items():
                pos1 = planet1_data.get("longitude", 0)
                pos2 = planet2_data.get("longitude", 0)

                angle = abs(pos1 - pos2)
                if angle > 180:
                    angle = 360 - angle

                for aspect_type in AspectType:
                    orb = aspect_type.orb * orb_factor
                    if abs(angle - aspect_type.angle) <= orb:
                        synastry_data["aspects"].append(
                            {
                                "planet1": f"{chart1.name}_{planet1_name}",
                                "planet2": f"{chart2.name}_{planet2_name}",
                                "aspect": aspect_type.name_ru,
                                "aspect_symbol": aspect_type.symbol,
                                "angle": aspect_type.angle,
                                "actual_angle": angle,
                                "orb": abs(angle - aspect_type.angle),
                            }
                        )
                        break

        # Вычисляем совместимость по элементам
        sun1_sign = self._get_sign_from_longitude(
            chart1.planets.get("Sun", {}).get("longitude", 0)
        )
        sun2_sign = self._get_sign_from_longitude(
            chart2.planets.get("Sun", {}).get("longitude", 0)
        )
        moon1_sign = self._get_sign_from_longitude(
            chart1.planets.get("Moon", {}).get("longitude", 0)
        )
        moon2_sign = self._get_sign_from_longitude(
            chart2.planets.get("Moon", {}).get("longitude", 0)
        )

        synastry_data["element_compatibility"] = {
            "sun_sun": self._calculate_element_compatibility(
                sun1_sign.element, sun2_sign.element
            ),
            "sun_moon": self._calculate_element_compatibility(
                sun1_sign.element, moon2_sign.element
            ),
            "moon_sun": self._calculate_element_compatibility(
                moon1_sign.element, sun2_sign.element
            ),
            "moon_moon": self._calculate_element_compatibility(
                moon1_sign.element, moon2_sign.element
            ),
        }

        # Вычисляем наложения домов
        for planet_name, planet_data in chart2.planets.items():
            planet_long = planet_data.get("longitude", 0)
            house = self._find_house_for_longitude(planet_long, chart1.houses)
            if house:
                if house not in synastry_data["house_overlays"]:
                    synastry_data["house_overlays"][house] = []
                synastry_data["house_overlays"][house].append(planet_name)

        # Вычисляем композитные средние точки
        for planet_name in ["Sun", "Moon", "Mercury", "Venus", "Mars"]:
            if planet_name in chart1.planets and planet_name in chart2.planets:
                pos1 = chart1.planets[planet_name].get("longitude", 0)
                pos2 = chart2.planets[planet_name].get("longitude", 0)
                midpoint = self._calculate_midpoint(pos1, pos2)
                synastry_data["composite_midpoints"][planet_name] = midpoint

        # Вычисляем общий балл совместимости
        synastry_data["compatibility_score"] = self._calculate_synastry_score(
            synastry_data
        )

        return synastry_data

    def _get_sign_from_longitude(self, longitude: float) -> ZodiacSign:
        """Получает знак зодиака по долготе"""
        sign_index = int(longitude / 30) % 12
        return self.zodiac_signs[sign_index]

    def _find_house_for_longitude(
        self, longitude: float, houses: Dict
    ) -> Optional[int]:
        """Находит дом для заданной долготы"""
        for i in range(1, 13):
            if i not in houses:
                continue

            current_cusp = houses[i].get("cusp_longitude", 0)
            next_house = (i % 12) + 1
            next_cusp = houses.get(next_house, {}).get(
                "cusp_longitude", (current_cusp + 30) % 360
            )

            if current_cusp <= longitude < next_cusp:
                return i
            elif current_cusp > next_cusp:  # Переход через 0°
                if longitude >= current_cusp or longitude < next_cusp:
                    return i

        return None

    def _calculate_midpoint(self, pos1: float, pos2: float) -> float:
        """Вычисляет среднюю точку между двумя позициями"""
        diff = abs(pos1 - pos2)
        if diff > 180:
            # Короткая дуга
            if pos1 > pos2:
                midpoint = (pos1 + (360 - diff) / 2) % 360
            else:
                midpoint = (pos2 + (360 - diff) / 2) % 360
        else:
            midpoint = (pos1 + pos2) / 2

        return midpoint

    def _calculate_synastry_score(self, synastry_data: Dict) -> float:
        """Вычисляет общий балл синастрии"""
        score = 50.0  # Базовый балл

        # Учитываем аспекты
        for aspect in synastry_data["aspects"]:
            aspect_name = aspect["aspect"]
            if aspect_name in ["Трин", "Секстиль"]:
                score += 5
            elif aspect_name == "Соединение":
                score += 3
            elif aspect_name in ["Квадрат", "Оппозиция"]:
                score -= 2

        # Учитываем совместимость элементов
        for compatibility in synastry_data["element_compatibility"].values():
            score += compatibility / 20

        # Ограничиваем диапазон
        return max(0, min(100, score))

    def calculate_transits(
        self,
        natal_chart: NatalChart,
        transit_date: datetime = None,
        period: TransitPeriod = TransitPeriod.TODAY,
    ) -> Dict[str, Any]:
        """Вычисляет транзиты к натальной карте"""
        if transit_date is None:
            transit_date = datetime.now(pytz.UTC)

        # Получаем текущие позиции планет
        transit_positions = self.calculate_planet_positions(transit_date)

        transits = {
            "date": transit_date.isoformat(),
            "period": period.value,
            "aspects": [],
            "ingresses": [],
            "retrogrades": [],
        }

        # Вычисляем аспекты транзитных планет к натальным
        for transit_planet, transit_data in transit_positions.items():
            transit_pos = transit_data.get("longitude", 0)

            for natal_planet, natal_data in natal_chart.planets.items():
                natal_pos = natal_data.get("longitude", 0)

                angle = abs(transit_pos - natal_pos)
                if angle > 180:
                    angle = 360 - angle

                for aspect_type in AspectType:
                    # Используем более узкие орбисы для транзитов
                    orb = aspect_type.orb * 0.5
                    if abs(angle - aspect_type.angle) <= orb:
                        transits["aspects"].append(
                            {
                                "transit_planet": transit_planet,
                                "natal_planet": natal_planet,
                                "aspect": aspect_type.name_ru,
                                "aspect_symbol": aspect_type.symbol,
                                "exact_date": self._calculate_exact_aspect_date(
                                    transit_planet,
                                    natal_pos,
                                    aspect_type.angle,
                                    transit_date,
                                ),
                                "orb": abs(angle - aspect_type.angle),
                            }
                        )
                        break

            # Проверяем ингрессии (вход в новый знак)
            transit_sign = self._get_sign_from_longitude(transit_pos)
            if transit_data.get("degree_in_sign", 30) < 1:
                transits["ingresses"].append(
                    {
                        "planet": transit_planet,
                        "sign": transit_sign.name_ru,
                        "date": transit_date.isoformat(),
                    }
                )

            # Проверяем ретроградность
            if transit_data.get("retrograde", False):
                transits["retrogrades"].append(
                    {"planet": transit_planet, "status": "ретроградный"}
                )

        return transits

    def _calculate_exact_aspect_date(
        self,
        transit_planet: str,
        natal_pos: float,
        aspect_angle: float,
        current_date: datetime,
    ) -> Optional[str]:
        """Вычисляет точную дату аспекта (упрощенно)"""
        # Это упрощенная версия - в реальности нужен более сложный расчет
        return current_date.isoformat()

    def calculate_progressions(
        self,
        natal_chart: NatalChart,
        target_date: datetime = None,
        progression_type: ProgressionType = ProgressionType.SECONDARY,
    ) -> Dict[str, Any]:
        """Вычисляет прогрессии"""
        if target_date is None:
            target_date = datetime.now(pytz.UTC)

        age_days = (target_date - natal_chart.birth_datetime).days

        progressions = {
            "type": progression_type.value,
            "target_date": target_date.isoformat(),
            "progressed_planets": {},
            "progressed_angles": {},
        }

        if progression_type == ProgressionType.SECONDARY:
            # Вторичная прогрессия: 1 день = 1 год
            prog_days = age_days / 365.25
            prog_date = natal_chart.birth_datetime + timedelta(days=prog_days)

            # Получаем прогрессивные позиции
            prog_positions = self.calculate_planet_positions(
                prog_date, natal_chart.latitude, natal_chart.longitude
            )
            progressions["progressed_planets"] = prog_positions

            # Прогрессивные углы
            prog_houses = self.calculate_houses(
                prog_date,
                natal_chart.latitude,
                natal_chart.longitude,
                natal_chart.house_system,
            )
            progressions["progressed_angles"] = {
                "ascendant": prog_houses.get("ascendant"),
                "midheaven": prog_houses.get("midheaven"),
            }

        elif progression_type == ProgressionType.SOLAR_ARC:
            # Солнечная дуга: все планеты движутся с той же скоростью, что и Солнце
            years = age_days / 365.25
            solar_arc = years * 0.9856  # Среднее движение Солнца в день * годы

            for planet_name, planet_data in natal_chart.planets.items():
                natal_pos = planet_data.get("longitude", 0)
                prog_pos = (natal_pos + solar_arc) % 360

                progressions["progressed_planets"][planet_name] = {
                    "longitude": prog_pos,
                    "sign": self._get_sign_from_longitude(prog_pos).name_ru,
                    "degree_in_sign": prog_pos % 30,
                }

        return progressions

    def calculate_solar_return(
        self, natal_chart: NatalChart, year: int = None
    ) -> NatalChart:
        """Вычисляет солнечное возвращение (соляр)"""
        if year is None:
            year = datetime.now().year

        # Находим момент, когда Солнце возвращается в натальное положение
        natal_sun = natal_chart.planets.get("Sun", {}).get("longitude", 0)

        # Приблизительная дата солнечного возвращения
        solar_return_date = natal_chart.birth_datetime.replace(year=year)

        # Уточняем дату (упрощенно - в реальности нужен итеративный поиск)
        for day_offset in range(-2, 3):
            check_date = solar_return_date + timedelta(days=day_offset)
            sun_pos = (
                self.calculate_planet_positions(check_date)
                .get("Sun", {})
                .get("longitude", 0)
            )

            if abs(sun_pos - natal_sun) < 0.5:
                solar_return_date = check_date
                break

        # Создаем карту солнечного возвращения
        solar_return = self.create_natal_chart(
            f"Solar Return {year}",
            solar_return_date,
            natal_chart.latitude,
            natal_chart.longitude,
            natal_chart.timezone,
            natal_chart.house_system,
        )

        return solar_return

    def calculate_lunar_return(
        self, natal_chart: NatalChart, target_date: datetime = None
    ) -> NatalChart:
        """Вычисляет лунное возвращение (лунар)"""
        if target_date is None:
            target_date = datetime.now(pytz.UTC)

        # Находим момент, когда Луна возвращается в натальное положение
        natal_moon = natal_chart.planets.get("Moon", {}).get("longitude", 0)

        # Луна проходит зодиак примерно за 27.3 дня

        # Ищем ближайшее лунное возвращение
        for day_offset in range(-14, 15):
            check_date = target_date + timedelta(days=day_offset)
            moon_pos = (
                self.calculate_planet_positions(check_date)
                .get("Moon", {})
                .get("longitude", 0)
            )

            if abs(moon_pos - natal_moon) < 1:
                lunar_return_date = check_date
                break
        else:
            lunar_return_date = target_date

        # Создаем карту лунного возвращения
        lunar_return = self.create_natal_chart(
            f"Lunar Return {lunar_return_date.strftime('%Y-%m')}",
            lunar_return_date,
            natal_chart.latitude,
            natal_chart.longitude,
            natal_chart.timezone,
            natal_chart.house_system,
        )

        return lunar_return

    def calculate_compatibility_score(
        self, sign1: YandexZodiacSign, sign2: YandexZodiacSign
    ) -> Dict[str, Any]:
        """Вычисляет совместимость знаков зодиака"""
        logger = logging.getLogger(__name__)
        logger.info(
            f"COMPATIBILITY_CALCULATION_START: sign1={sign1.value}, sign2={sign2.value}"
        )

        sign1_name = sign1.value
        sign2_name = sign2.value

        # Получаем элементы и качества знаков
        element1 = self.elements.get(sign1_name, "earth")
        element2 = self.elements.get(sign2_name, "earth")
        quality1 = self.qualities.get(sign1_name, "mutable")
        quality2 = self.qualities.get(sign2_name, "mutable")

        # Базовая совместимость по элементам
        element_compatibility = self._calculate_element_compatibility(
            element1, element2
        )

        # Совместимость по качествам
        quality_compatibility = self._calculate_quality_compatibility(
            quality1, quality2
        )

        # Общий счет
        total_score = (element_compatibility + quality_compatibility) / 2

        # Дополнительные факторы для kerykeion
        additional_factors = {}
        if self.backend == "kerykeion":
            # Можем добавить более сложные расчеты
            additional_factors[
                "karmic_connection"
            ] = self._calculate_karmic_connection(sign1_name, sign2_name)
            additional_factors[
                "growth_potential"
            ] = self._calculate_growth_potential(
                element1, element2, quality1, quality2
            )

        result = {
            "score": round(total_score, 1),
            "total_score": round(total_score, 1),
            "element_score": element_compatibility,
            "quality_score": quality_compatibility,
            "element1": element1,
            "element2": element2,
            "quality1": quality1,
            "quality2": quality2,
            "description": self._get_compatibility_description(total_score),
            "additional_factors": additional_factors,
        }

        logger.info(
            f"COMPATIBILITY_CALCULATION_SUCCESS: {sign1.value}+{sign2.value}={result['total_score']}"
        )
        return result

    def _calculate_element_compatibility(
        self, element1: str, element2: str
    ) -> float:
        """Вычисляет совместимость по элементам"""
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

        score = compatibility_matrix.get((element1, element2))
        if score is None:
            score = compatibility_matrix.get((element2, element1), 50)

        return score

    def _calculate_quality_compatibility(
        self, quality1: str, quality2: str
    ) -> float:
        """Вычисляет совместимость по качествам"""
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

    def _calculate_karmic_connection(self, sign1: str, sign2: str) -> float:
        """Вычисляет кармическую связь между знаками"""
        # Знаки в оппозиции часто имеют кармическую связь
        sign_order = [
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
        ]

        try:
            idx1 = sign_order.index(sign1)
            idx2 = sign_order.index(sign2)

            diff = abs(idx1 - idx2)
            if diff == 6:  # Оппозиция
                return 90
            elif diff in [4, 8]:  # Трин
                return 80
            elif diff in [3, 9]:  # Квадрат
                return 60
            else:
                return 50
        except ValueError:
            return 50

    def _calculate_growth_potential(
        self, element1: str, element2: str, quality1: str, quality2: str
    ) -> float:
        """Вычисляет потенциал роста в отношениях"""
        score = 50

        # Разные элементы могут дать больше роста
        if element1 != element2:
            score += 10

        # Разные качества тоже способствуют росту
        if quality1 != quality2:
            score += 10

        # Но слишком большие различия могут мешать
        if element1 == "fire" and element2 == "water":
            score -= 15
        elif element1 == "earth" and element2 == "air":
            score -= 15

        return max(0, min(100, score))

    def _get_compatibility_description(self, score: float) -> str:
        """Возвращает описание совместимости по баллам"""
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

    def calculate_moon_phase(self, target_date: datetime) -> Dict[str, Any]:
        """Вычисляет фазу Луны на заданную дату"""
        logger = logging.getLogger(__name__)
        logger.info(
            f"MOON_PHASE_CALCULATION_START: date={target_date.strftime('%Y-%m-%d')}"
        )

        try:
            # Получаем позиции Солнца и Луны
            positions = self.calculate_planet_positions(target_date)
            sun_pos = positions.get("Sun", {}).get("longitude", 0)
            moon_pos = positions.get("Moon", {}).get("longitude", 0)

            # Вычисляем угол между Солнцем и Луной
            angle = (moon_pos - sun_pos) % 360

            # Определяем фазу
            phase_info = self._get_moon_phase_info(angle)

            # Вычисляем освещенность
            illumination = (1 - math.cos(math.radians(angle))) / 2 * 100

            # Добавляем эмодзи фазы если доступен kerykeion
            moon_emoji = ""
            if KERYKEION_AVAILABLE:
                try:
                    from kerykeion.utilities import get_moon_emoji

                    moon_emoji = get_moon_emoji(angle)
                except ImportError:
                    moon_emoji = self._get_moon_emoji_fallback(angle)
            else:
                moon_emoji = self._get_moon_emoji_fallback(angle)

            result = {
                "phase_name": phase_info["name"],
                "phase_description": phase_info["description"],
                "angle": angle,
                "illumination_percent": round(illumination, 1),
                "is_waxing": angle < 180,
                "moon_emoji": moon_emoji,
                "days_since_new_moon": round(
                    angle / 12.19
                ),  # Средняя скорость Луны ~12.19°/день
                "days_until_full_moon": round((180 - angle) / 12.19)
                if angle < 180
                else round((540 - angle) / 12.19),
            }

            logger.info(
                f"MOON_PHASE_CALCULATION_SUCCESS: phase='{result['phase_name']}'"
            )
            return result

        except Exception as e:
            logger.error(f"MOON_PHASE_CALCULATION_ERROR: {e}")
            return self._get_moon_phase_fallback(target_date)

    def _get_moon_phase_info(self, angle: float) -> Dict[str, str]:
        """Возвращает информацию о фазе Луны по углу"""
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

    def _get_moon_emoji_fallback(self, angle: float) -> str:
        """Возвращает эмодзи фазы Луны"""
        if angle < 45:
            return "🌑"  # Новолуние
        elif angle < 90:
            return "🌒"  # Растущий серп
        elif angle < 135:
            return "🌓"  # Первая четверть
        elif angle < 180:
            return "🌔"  # Растущая выпуклая
        elif angle < 225:
            return "🌕"  # Полнолуние
        elif angle < 270:
            return "🌖"  # Убывающая выпуклая
        elif angle < 315:
            return "🌗"  # Последняя четверть
        else:
            return "🌘"  # Убывающий серп

    def _get_moon_phase_fallback(
        self, target_date: datetime
    ) -> Dict[str, Any]:
        """Упрощенный расчет фазы Луны"""
        day_of_month = target_date.day
        phase_angle = (day_of_month / 29.5) * 360
        phase_info = self._get_moon_phase_info(phase_angle)

        return {
            "phase_name": phase_info["name"],
            "phase_description": phase_info["description"],
            "angle": phase_angle,
            "illumination_percent": 50,
            "is_waxing": day_of_month <= 14,
            "moon_emoji": self._get_moon_emoji_fallback(phase_angle),
        }

    def get_planetary_hours(self, target_date: datetime) -> Dict[str, Any]:
        """Вычисляет планетные часы для заданной даты"""
        logger = logging.getLogger(__name__)
        logger.debug(
            f"PLANETARY_HOURS_CALCULATION_START: date={target_date.strftime('%Y-%m-%d %H:%M')}"
        )

        weekday = target_date.weekday()
        hour = target_date.hour

        # Правящие планеты дней недели
        day_rulers = [
            "Луна",
            "Марс",
            "Меркурий",
            "Юпитер",
            "Венера",
            "Сатурн",
            "Солнце",
        ]

        ruler = day_rulers[weekday]
        hour_ruler = self._get_hour_ruler(weekday, hour)
        favorable_hours = self._get_favorable_hours(weekday)

        result = {
            "day_ruler": ruler,
            "current_hour_ruler": hour_ruler,
            "favorable_hours": favorable_hours,
            "description": f"День управляется {ruler}",
            "hour_meanings": self._get_planetary_hour_meanings(hour_ruler),
        }

        logger.info(f"PLANETARY_HOURS_CALCULATION_SUCCESS: day_ruler={ruler}")
        return result

    def _get_hour_ruler(self, weekday: int, hour: int) -> str:
        """Возвращает планету-управителя текущего часа"""
        planets_order = [
            "Солнце",
            "Венера",
            "Меркурий",
            "Луна",
            "Сатурн",
            "Юпитер",
            "Марс",
        ]
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
        hour_index = (start_index + hour) % 7

        return planets_order[hour_index]

    def _get_favorable_hours(self, weekday: int) -> List[int]:
        """Возвращает благоприятные часы для дня"""
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

    def _get_planetary_hour_meanings(self, planet: str) -> Dict[str, str]:
        """Возвращает значения планетного часа"""
        meanings = {
            "Солнце": "Успех, слава, продвижение",
            "Луна": "Эмоции, семья, путешествия",
            "Меркурий": "Общение, учеба, торговля",
            "Венера": "Любовь, искусство, удовольствия",
            "Марс": "Действие, конфликты, спорт",
            "Юпитер": "Удача, расширение, философия",
            "Сатурн": "Дисциплина, ограничения, планирование",
        }

        return {
            "planet": planet,
            "meaning": meanings.get(planet, "Неизвестно"),
        }

    def calculate_dignities(
        self, planet_positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """Вычисляет достоинства и слабости планет"""
        dignities = {}

        # Таблица управителей знаков
        sign_rulers = {
            "Овен": "Mars",
            "Телец": "Venus",
            "Близнецы": "Mercury",
            "Рак": "Moon",
            "Лев": "Sun",
            "Дева": "Mercury",
            "Весы": "Venus",
            "Скорпион": ["Mars", "Pluto"],
            "Стрелец": "Jupiter",
            "Козерог": "Saturn",
            "Водолей": ["Saturn", "Uranus"],
            "Рыбы": ["Jupiter", "Neptune"],
        }

        # Таблица экзальтаций
        exaltations = {
            "Sun": "Овен",
            "Moon": "Телец",
            "Mercury": "Дева",
            "Venus": "Рыбы",
            "Mars": "Козерог",
            "Jupiter": "Рак",
            "Saturn": "Весы",
        }

        # Таблица падений (противоположны экзальтациям)
        falls = {
            "Sun": "Весы",
            "Moon": "Скорпион",
            "Mercury": "Рыбы",
            "Venus": "Дева",
            "Mars": "Рак",
            "Jupiter": "Козерог",
            "Saturn": "Овен",
        }

        for planet_name, planet_data in planet_positions.items():
            sign = planet_data.get("sign", "")
            dignity_status = "Перегрин"  # По умолчанию

            # Проверяем управление
            ruler = sign_rulers.get(sign)
            if isinstance(ruler, list):
                if planet_name in ruler:
                    dignity_status = "В обители"
            elif planet_name == ruler:
                dignity_status = "В обители"

            # Проверяем экзальтацию
            if exaltations.get(planet_name) == sign:
                dignity_status = "В экзальтации"

            # Проверяем падение
            if falls.get(planet_name) == sign:
                dignity_status = "В падении"

            # Проверяем изгнание (противоположно обители)
            # Упрощенная проверка
            opposite_signs = {
                "Овен": "Весы",
                "Весы": "Овен",
                "Телец": "Скорпион",
                "Скорпион": "Телец",
                "Близнецы": "Стрелец",
                "Стрелец": "Близнецы",
                "Рак": "Козерог",
                "Козерог": "Рак",
                "Лев": "Водолей",
                "Водолей": "Лев",
                "Дева": "Рыбы",
                "Рыбы": "Дева",
            }

            opposite_sign = opposite_signs.get(sign)
            if opposite_sign:
                opposite_ruler = sign_rulers.get(opposite_sign)
                if isinstance(opposite_ruler, list):
                    if planet_name in opposite_ruler:
                        dignity_status = "В изгнании"
                elif planet_name == opposite_ruler:
                    dignity_status = "В изгнании"

            dignities[planet_name] = {"sign": sign, "dignity": dignity_status}

        return dignities

    def get_backend_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущем астрономическом бэкенде"""
        capabilities = {
            "kerykeion": {
                "planet_positions": True,
                "moon_phases": True,
                "houses": True,
                "aspects": True,
                "synastry": True,
                "transits": True,
                "progressions": True,
                "solar_return": True,
                "lunar_return": True,
                "arabic_parts": True,
                "fixed_stars": True,
                "dignities": True,
                "high_precision": True,
            },
            "swisseph": {
                "planet_positions": True,
                "moon_phases": True,
                "houses": True,
                "aspects": True,
                "synastry": False,
                "transits": True,
                "progressions": True,
                "solar_return": True,
                "lunar_return": True,
                "arabic_parts": True,
                "fixed_stars": False,
                "dignities": False,
                "high_precision": True,
            },
            "skyfield": {
                "planet_positions": True,
                "moon_phases": True,
                "houses": False,
                "aspects": True,
                "synastry": False,
                "transits": True,
                "progressions": False,
                "solar_return": False,
                "lunar_return": False,
                "arabic_parts": False,
                "fixed_stars": False,
                "dignities": False,
                "high_precision": True,
            },
            "fallback": {
                "planet_positions": True,
                "moon_phases": True,
                "houses": True,
                "aspects": True,
                "synastry": False,
                "transits": False,
                "progressions": False,
                "solar_return": False,
                "lunar_return": False,
                "arabic_parts": False,
                "fixed_stars": False,
                "dignities": False,
                "high_precision": False,
            },
        }

        return {
            "backend": self.backend,
            "capabilities": capabilities.get(self.backend, {}),
            "available_backends": self._get_available_backends(),
            "version": "2.0.0",
            "features": {
                "natal_charts": True,
                "synastry": self.backend == "kerykeion",
                "transits": self.backend
                in ["kerykeion", "swisseph", "skyfield"],
                "progressions": self.backend in ["kerykeion", "swisseph"],
                "returns": self.backend in ["kerykeion", "swisseph"],
                "arabic_parts": self.backend in ["kerykeion", "swisseph"],
                "fixed_stars": self.backend == "kerykeion",
                "chart_drawing": self.backend == "kerykeion"
                and KERYKEION_AVAILABLE,
            },
        }

    def _get_available_backends(self) -> List[str]:
        """Проверяет доступные астрономические бэкенды"""
        available = []

        if KERYKEION_AVAILABLE:
            available.append("kerykeion")

        if SWISSEPH_AVAILABLE:
            available.append("swisseph")

        if SKYFIELD_AVAILABLE:
            available.append("skyfield")

        available.append("fallback")  # Всегда доступен

        return available

    def calculate_julian_day(self, birth_datetime: datetime) -> float:
        """Вычисляет юлианский день для заданной даты и времени"""
        year = birth_datetime.year
        month = birth_datetime.month
        day = birth_datetime.day
        hour = birth_datetime.hour + birth_datetime.minute / 60.0

        if SWISSEPH_AVAILABLE and swe:
            return swe.julday(year, month, day, hour)
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
