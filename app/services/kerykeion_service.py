"""
Specialized Kerykeion service for advanced astrological calculations.
This service extends the basic astrology calculator with Kerykeion-specific features.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import pytz

logger = logging.getLogger(__name__)

# Try to import Kerykeion with detailed error handling
try:
    # Updated imports for Kerykeion 4.x
    from kerykeion import KerykeionSubject as AstrologicalSubject, MakeSvgInstance as KerykeionChartSVG, KrInstance as NatalChart

    KERYKEION_AVAILABLE = True
    logger.info("KERYKEION_SERVICE_INIT: Kerykeion fully available with updated classes")
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"KERYKEION_SERVICE_INIT: Kerykeion not fully available: {e}")
    KERYKEION_AVAILABLE = False
    # Create stub classes to prevent import errors
    AstrologicalSubject = None
    NatalChart = None
    KerykeionChartSVG = None


class HouseSystem(Enum):
    """Extended house systems supported by Kerykeion"""

    PLACIDUS = "Placidus"
    KOCH = "Koch"
    EQUAL = "Equal"
    WHOLE_SIGN = "Whole Sign"
    REGIOMONTANUS = "Regiomontanus"
    CAMPANUS = "Campanus"
    TOPOCENTRIC = "Topocentric"
    ALCABITUS = "Alcabitus"
    MORINUS = "Morinus"
    PORPHYRIUS = "Porphyrius"


class ZodiacType(Enum):
    """Zodiac types"""

    TROPICAL = "Tropical"
    SIDEREAL = "Sidereal"


class AspectColor(Enum):
    """Aspect colors according to traditional astrology"""

    CONJUNCTION = "#FF0000"  # Red
    OPPOSITION = "#0000FF"  # Blue
    TRINE = "#00FF00"  # Green
    SQUARE = "#FF8000"  # Orange
    SEXTILE = "#8000FF"  # Purple
    QUINCUNX = "#808080"  # Gray
    SEMISQUARE = "#FFC0CB"  # Pink
    SESQUISQUARE = "#FFC0CB"  # Pink
    SEMISEXTILE = "#ADD8E6"  # Light Blue
    QUINTILE = "#FFD700"  # Gold
    BIQUINTILE = "#FFD700"  # Gold


class KerykeionService:
    """Advanced astrological service using Kerykeion library"""

    def __init__(self):
        self.available = KERYKEION_AVAILABLE
        if not self.available:
            logger.warning(
                "KERYKEION_SERVICE: Service initialized without Kerykeion"
            )

    def is_available(self) -> bool:
        """Check if Kerykeion is available"""
        return self.available

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "available": self.available,
            "service_name": "KerykeionService",
            "features": {
                "natal_charts": self.available,
                "house_systems": self.available,
                "synastry": self.available,
                "svg_generation": self.available
            },
            "fallback_enabled": not self.available
        }

    def create_astrological_subject(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Moscow",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        zodiac_type: ZodiacType = ZodiacType.TROPICAL,
    ) -> Optional[Any]:
        """Create Kerykeion AstrologicalSubject with full configuration"""
        if not self.available:
            logger.error(
                "KERYKEION_SERVICE_CREATE_SUBJECT: Kerykeion not available"
            )
            return None

        try:
            logger.info(
                f"KERYKEION_SERVICE_CREATE_SUBJECT: Creating subject for {name}"
            )

            # Convert timezone string to pytz timezone
            try:
                tz = pytz.timezone(timezone)
                if birth_datetime.tzinfo is None:
                    birth_datetime = tz.localize(birth_datetime)
                else:
                    birth_datetime = birth_datetime.astimezone(tz)
            except Exception as e:
                logger.warning(
                    f"KERYKEION_SERVICE_CREATE_SUBJECT: Timezone error {e}, using UTC"
                )
                if birth_datetime.tzinfo is None:
                    birth_datetime = pytz.UTC.localize(birth_datetime)

            subject = AstrologicalSubject(
                name=name,
                year=birth_datetime.year,
                month=birth_datetime.month,
                day=birth_datetime.day,
                hour=birth_datetime.hour,
                minute=birth_datetime.minute,
                lat=latitude,
                lng=longitude,
                tz_str=str(birth_datetime.tzinfo),
                city="Unknown",
                nation="Unknown",
                zodiac_type=zodiac_type.value,
                sidereal_mode="FAGAN_BRADLEY",  # Default sidereal mode
                house_system=house_system.value,
            )

            logger.info(f"KERYKEION_SERVICE_CREATE_SUBJECT_SUCCESS: {name}")
            return subject

        except Exception as e:
            logger.error(f"KERYKEION_SERVICE_CREATE_SUBJECT_ERROR: {e}")
            return None

    def get_full_natal_chart_data(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Moscow",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        zodiac_type: ZodiacType = ZodiacType.TROPICAL,
    ) -> Dict[str, Any]:
        """Get comprehensive natal chart data using Kerykeion"""
        if not self.available:
            return {"error": "Kerykeion not available"}

        logger.info(f"KERYKEION_SERVICE_FULL_CHART_START: {name}")

        subject = self.create_astrological_subject(
            name,
            birth_datetime,
            latitude,
            longitude,
            timezone,
            house_system,
            zodiac_type,
        )

        if not subject:
            return {"error": "Failed to create astrological subject"}

        try:
            # Extract all planetary data
            planets_data = {}
            for planet in [
                "sun",
                "moon",
                "mercury",
                "venus",
                "mars",
                "jupiter",
                "saturn",
                "uranus",
                "neptune",
                "pluto",
                "mean_node",
                "true_node",
                "mean_apog",
                "osculating_apog",
                "chiron",
            ]:
                if hasattr(subject, planet):
                    planet_info = getattr(subject, planet)
                    if planet_info:
                        planets_data[planet] = {
                            "name": planet_info.get(
                                "name", planet.capitalize()
                            ),
                            "longitude": planet_info.get("pos", [0, 0, 0])[0],
                            "latitude": planet_info.get("pos", [0, 0, 0])[1],
                            "distance": planet_info.get("pos", [0, 0, 0])[2],
                            "speed": planet_info.get("speed", 0),
                            "retrograde": planet_info.get("retrograde", False),
                            "sign": planet_info.get("sign", "Unknown"),
                            "sign_num": planet_info.get("sign_num", 0),
                            "degree_in_sign": planet_info.get(
                                "deg_in_sign", 0
                            ),
                            "house": planet_info.get("house", None),
                            "emoji": planet_info.get("emoji", ""),
                            "element": planet_info.get("element", ""),
                            "quality": planet_info.get("quality", ""),
                        }

            # Extract houses data
            houses_data = {}
            for i in range(1, 13):
                house_attr = f"house{i}"
                if hasattr(subject, house_attr):
                    house_info = getattr(subject, house_attr)
                    if house_info:
                        houses_data[i] = {
                            "cusp_longitude": house_info.get("pos", [0])[0],
                            "sign": house_info.get("sign", "Unknown"),
                            "sign_num": house_info.get("sign_num", 0),
                            "degree_in_sign": house_info.get("deg_in_sign", 0),
                        }

            # Add angles (ASC, MC, DSC, IC)
            angles = {}
            if hasattr(subject, "first_house") and subject.first_house:
                angles["ascendant"] = {
                    "longitude": subject.first_house.get("pos", [0])[0],
                    "sign": subject.first_house.get("sign", "Unknown"),
                    "degree_in_sign": subject.first_house.get(
                        "deg_in_sign", 0
                    ),
                }

            if hasattr(subject, "tenth_house") and subject.tenth_house:
                angles["midheaven"] = {
                    "longitude": subject.tenth_house.get("pos", [0])[0],
                    "sign": subject.tenth_house.get("sign", "Unknown"),
                    "degree_in_sign": subject.tenth_house.get(
                        "deg_in_sign", 0
                    ),
                }

            # Calculate all aspects with Kerykeion
            aspects_data = self.calculate_kerykeion_aspects(subject)

            # Get additional chart information
            chart_info = {
                "timezone": str(subject.tz),
                "julian_day": getattr(subject, "julian_day", None),
                "house_system": house_system.value,
                "zodiac_type": zodiac_type.value,
                "coordinates": {"latitude": latitude, "longitude": longitude},
                "birth_datetime": birth_datetime.isoformat(),
            }

            result = {
                "subject_info": chart_info,
                "planets": planets_data,
                "houses": houses_data,
                "angles": angles,
                "aspects": aspects_data,
                "chart_shape": self._analyze_chart_shape(planets_data),
                "element_distribution": self._calculate_element_distribution(
                    planets_data
                ),
                "quality_distribution": self._calculate_quality_distribution(
                    planets_data
                ),
                "dominant_planets": self._find_dominant_planets(
                    planets_data, aspects_data
                ),
            }

            logger.info(f"KERYKEION_SERVICE_FULL_CHART_SUCCESS: {name}")
            return result

        except Exception as e:
            logger.error(f"KERYKEION_SERVICE_FULL_CHART_ERROR: {e}")
            return {"error": f"Chart calculation failed: {str(e)}"}

    def calculate_kerykeion_aspects(
        self, subject: Any
    ) -> List[Dict[str, Any]]:
        """Calculate aspects using Kerykeion with full orb and color information"""
        if not subject:
            return []

        aspects = []

        try:
            # Get all celestial bodies for aspect calculation
            celestial_bodies = [
                "sun",
                "moon",
                "mercury",
                "venus",
                "mars",
                "jupiter",
                "saturn",
                "uranus",
                "neptune",
                "pluto",
                "mean_node",
                "chiron",
            ]

            # Standard aspect definitions with orbs
            aspect_definitions = {
                0: {
                    "name": "Conjunction",
                    "symbol": "☌",
                    "orb": 10,
                    "color": AspectColor.CONJUNCTION.value,
                },
                60: {
                    "name": "Sextile",
                    "symbol": "⚹",
                    "orb": 6,
                    "color": AspectColor.SEXTILE.value,
                },
                90: {
                    "name": "Square",
                    "symbol": "□",
                    "orb": 8,
                    "color": AspectColor.SQUARE.value,
                },
                120: {
                    "name": "Trine",
                    "symbol": "△",
                    "orb": 9,
                    "color": AspectColor.TRINE.value,
                },
                180: {
                    "name": "Opposition",
                    "symbol": "☍",
                    "orb": 10,
                    "color": AspectColor.OPPOSITION.value,
                },
                30: {
                    "name": "Semisextile",
                    "symbol": "⚺",
                    "orb": 2,
                    "color": AspectColor.SEMISEXTILE.value,
                },
                45: {
                    "name": "Semisquare",
                    "symbol": "∠",
                    "orb": 2,
                    "color": AspectColor.SEMISQUARE.value,
                },
                135: {
                    "name": "Sesquisquare",
                    "symbol": "⚼",
                    "orb": 2,
                    "color": AspectColor.SESQUISQUARE.value,
                },
                150: {
                    "name": "Quincunx",
                    "symbol": "⚻",
                    "orb": 3,
                    "color": AspectColor.QUINCUNX.value,
                },
                72: {
                    "name": "Quintile",
                    "symbol": "Q",
                    "orb": 2,
                    "color": AspectColor.QUINTILE.value,
                },
                144: {
                    "name": "Biquintile",
                    "symbol": "bQ",
                    "orb": 2,
                    "color": AspectColor.BIQUINTILE.value,
                },
            }

            # Calculate aspects between all planet pairs
            for i, planet1 in enumerate(celestial_bodies):
                for planet2 in celestial_bodies[i + 1 :]:
                    planet1_data = getattr(subject, planet1, None)
                    planet2_data = getattr(subject, planet2, None)

                    if not planet1_data or not planet2_data:
                        continue

                    pos1 = planet1_data.get("pos", [0])[0]  # longitude
                    pos2 = planet2_data.get("pos", [0])[0]  # longitude

                    # Calculate angle between planets
                    angle = abs(pos1 - pos2)
                    if angle > 180:
                        angle = 360 - angle

                    # Check for aspects
                    for (
                        aspect_angle,
                        aspect_info,
                    ) in aspect_definitions.items():
                        orb = aspect_info["orb"]
                        if abs(angle - aspect_angle) <= orb:
                            # Calculate exactness (how close to exact aspect)
                            exactness = abs(angle - aspect_angle)

                            # Determine if aspect is applying or separating
                            speed1 = planet1_data.get("speed", 0)
                            speed2 = planet2_data.get("speed", 0)
                            applying = self._is_aspect_applying(
                                angle, aspect_angle, speed1, speed2
                            )

                            aspects.append(
                                {
                                    "planet1": planet1_data.get(
                                        "name", planet1.capitalize()
                                    ),
                                    "planet2": planet2_data.get(
                                        "name", planet2.capitalize()
                                    ),
                                    "aspect": aspect_info["name"],
                                    "symbol": aspect_info["symbol"],
                                    "angle": aspect_angle,
                                    "actual_angle": round(angle, 2),
                                    "orb": round(exactness, 2),
                                    "color": aspect_info["color"],
                                    "applying": applying,
                                    "strength": self._calculate_aspect_strength(
                                        exactness, orb
                                    ),
                                    "interpretation": self._get_aspect_interpretation(
                                        planet1, planet2, aspect_info["name"]
                                    ),
                                }
                            )
                            break

            # Sort aspects by exactness (strongest first)
            aspects.sort(key=lambda x: x["orb"])

            logger.info(
                f"KERYKEION_SERVICE_ASPECTS_CALCULATED: {len(aspects)} aspects found"
            )
            return aspects

        except Exception as e:
            logger.error(f"KERYKEION_SERVICE_ASPECTS_ERROR: {e}")
            return []

    def _is_aspect_applying(
        self,
        current_angle: float,
        exact_angle: float,
        speed1: float,
        speed2: float,
    ) -> bool:
        """Determine if aspect is applying (getting closer) or separating"""
        # If the faster planet is catching up to the slower one
        relative_speed = speed1 - speed2

        if current_angle < exact_angle:
            return relative_speed > 0
        else:
            return relative_speed < 0

    def _calculate_aspect_strength(
        self, exactness: float, max_orb: float
    ) -> str:
        """Calculate aspect strength based on orb"""
        if exactness <= 1:
            return "Very Strong"
        elif exactness <= max_orb * 0.3:
            return "Strong"
        elif exactness <= max_orb * 0.6:
            return "Moderate"
        else:
            return "Weak"

    def _get_aspect_interpretation(
        self, planet1: str, planet2: str, aspect: str
    ) -> str:
        """Get basic interpretation for planet-aspect combination"""
        interpretations = {
            ("sun", "moon"): {
                "Conjunction": "Гармония между сознанием и эмоциями",
                "Opposition": "Конфликт между волей и чувствами",
                "Trine": "Естественная интеграция личности",
                "Square": "Внутреннее напряжение между эго и эмоциями",
                "Sextile": "Хорошие возможности для самовыражения",
            },
            ("sun", "mercury"): {
                "Conjunction": "Яркий ум и коммуникативные способности",
                "Sextile": "Гармоничное выражение мыслей",
            },
            ("sun", "venus"): {
                "Conjunction": "Харизма и привлекательность",
                "Trine": "Творческие таланты и обаяние",
                "Sextile": "Художественные способности",
            },
        }

        key = (planet1.lower(), planet2.lower())
        reverse_key = (planet2.lower(), planet1.lower())

        aspect_interpretations = interpretations.get(
            key, interpretations.get(reverse_key, {})
        )
        return aspect_interpretations.get(
            aspect,
            f"{aspect} между {planet1.capitalize()} и {planet2.capitalize()}",
        )

    def calculate_arabic_parts_extended(
        self, subject: Any
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate extended Arabic Parts using Kerykeion data"""
        if not subject:
            return {}

        try:
            parts = {}

            # Get necessary positions
            sun = getattr(subject, "sun", {})
            moon = getattr(subject, "moon", {})
            mercury = getattr(subject, "mercury", {})
            venus = getattr(subject, "venus", {})
            mars = getattr(subject, "mars", {})
            jupiter = getattr(subject, "jupiter", {})
            saturn = getattr(subject, "saturn", {})

            # Get ASC and MC
            asc_pos = 0
            mc_pos = 0
            if hasattr(subject, "first_house") and subject.first_house:
                asc_pos = subject.first_house.get("pos", [0])[0]
            if hasattr(subject, "tenth_house") and subject.tenth_house:
                mc_pos = subject.tenth_house.get("pos", [0])[0]

            sun_pos = sun.get("pos", [0])[0] if sun else 0
            moon_pos = moon.get("pos", [0])[0] if moon else 0
            venus_pos = venus.get("pos", [0])[0] if venus else 0
            mars.get("pos", [0])[0] if mars else 0
            jupiter.get("pos", [0])[0] if jupiter else 0
            saturn.get("pos", [0])[0] if saturn else 0
            mercury.get("pos", [0])[0] if mercury else 0

            # Calculate Parts
            # Part of Fortune (Lot of Fortune)
            fortune_pos = (asc_pos + moon_pos - sun_pos) % 360
            parts["fortune"] = {
                "name": "Часть Фортуны",
                "longitude": fortune_pos,
                "sign": self._get_sign_from_longitude(fortune_pos),
                "degree_in_sign": fortune_pos % 30,
                "formula": "ASC + Moon - Sun",
                "meaning": "Материальное благополучие и удача",
            }

            # Part of Spirit
            spirit_pos = (asc_pos + sun_pos - moon_pos) % 360
            parts["spirit"] = {
                "name": "Часть Духа",
                "longitude": spirit_pos,
                "sign": self._get_sign_from_longitude(spirit_pos),
                "degree_in_sign": spirit_pos % 30,
                "formula": "ASC + Sun - Moon",
                "meaning": "Духовное развитие и жизненная цель",
            }

            # Part of Love
            love_pos = (asc_pos + venus_pos - sun_pos) % 360
            parts["love"] = {
                "name": "Часть Любви",
                "longitude": love_pos,
                "sign": self._get_sign_from_longitude(love_pos),
                "degree_in_sign": love_pos % 30,
                "formula": "ASC + Venus - Sun",
                "meaning": "Романтические отношения и любовь",
            }

            # Part of Marriage
            marriage_pos = (asc_pos + (asc_pos + 180) % 360 - venus_pos) % 360
            parts["marriage"] = {
                "name": "Часть Брака",
                "longitude": marriage_pos,
                "sign": self._get_sign_from_longitude(marriage_pos),
                "degree_in_sign": marriage_pos % 30,
                "formula": "ASC + 7th house cusp - Venus",
                "meaning": "Брак и долгосрочные партнерства",
            }

            # Part of Career
            career_pos = (asc_pos + mc_pos - sun_pos) % 360
            parts["career"] = {
                "name": "Часть Карьеры",
                "longitude": career_pos,
                "sign": self._get_sign_from_longitude(career_pos),
                "degree_in_sign": career_pos % 30,
                "formula": "ASC + MC - Sun",
                "meaning": "Профессиональная реализация",
            }

            logger.info(
                f"KERYKEION_SERVICE_ARABIC_PARTS: {len(parts)} parts calculated"
            )
            return parts

        except Exception as e:
            logger.error(f"KERYKEION_SERVICE_ARABIC_PARTS_ERROR: {e}")
            return {}

    def _get_sign_from_longitude(self, longitude: float) -> str:
        """Get zodiac sign from longitude"""
        signs = [
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
        sign_index = int(longitude / 30) % 12
        return signs[sign_index]

    def _analyze_chart_shape(
        self, planets_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Analyze the overall shape pattern of the chart"""
        if not planets_data:
            return {"shape": "Unknown", "description": "Insufficient data"}

        # Get all planet longitudes
        longitudes = []
        for planet_data in planets_data.values():
            if "longitude" in planet_data:
                longitudes.append(planet_data["longitude"])

        if len(longitudes) < 5:
            return {"shape": "Incomplete", "description": "Not enough planets"}

        longitudes.sort()

        # Calculate the span of planets
        max_gap = 0
        total_span = 0

        for i in range(len(longitudes)):
            next_idx = (i + 1) % len(longitudes)
            gap = (longitudes[next_idx] - longitudes[i]) % 360
            if gap > max_gap:
                max_gap = gap

        total_span = (longitudes[-1] - longitudes[0]) % 360

        # Determine chart shape
        if max_gap > 240:
            return {
                "shape": "Bundle",
                "description": "Все планеты в одной трети зодиака - концентрированная энергия",
            }
        elif max_gap > 180:
            return {
                "shape": "Bowl",
                "description": "Планеты в половине зодиака - односторонняя направленность",
            }
        elif total_span < 120:
            return {
                "shape": "Stellium",
                "description": "Сильная концентрация планет в узком секторе",
            }
        elif max_gap > 120:
            return {
                "shape": "Locomotive",
                "description": "Планеты занимают две трети зодиака с пустым сектором",
            }
        else:
            return {
                "shape": "Splash",
                "description": "Планеты равномерно распределены по зодиаку",
            }

    def _calculate_element_distribution(
        self, planets_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Calculate distribution of elements in the chart"""
        elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}

        # Element mapping for signs
        sign_elements = {
            "Овен": "Fire",
            "Лев": "Fire",
            "Стрелец": "Fire",
            "Телец": "Earth",
            "Дева": "Earth",
            "Козерог": "Earth",
            "Близнецы": "Air",
            "Весы": "Air",
            "Водолей": "Air",
            "Рак": "Water",
            "Скорпион": "Water",
            "Рыбы": "Water",
        }

        for planet_data in planets_data.values():
            sign = planet_data.get("sign")
            element = sign_elements.get(sign)
            if element:
                elements[element] += 1

        return elements

    def _calculate_quality_distribution(
        self, planets_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """Calculate distribution of qualities in the chart"""
        qualities = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}

        # Quality mapping for signs
        sign_qualities = {
            "Овен": "Cardinal",
            "Рак": "Cardinal",
            "Весы": "Cardinal",
            "Козерог": "Cardinal",
            "Телец": "Fixed",
            "Лев": "Fixed",
            "Скорпион": "Fixed",
            "Водолей": "Fixed",
            "Близнецы": "Mutable",
            "Дева": "Mutable",
            "Стрелец": "Mutable",
            "Рыбы": "Mutable",
        }

        for planet_data in planets_data.values():
            sign = planet_data.get("sign")
            quality = sign_qualities.get(sign)
            if quality:
                qualities[quality] += 1

        return qualities

    def _find_dominant_planets(
        self, planets_data: Dict[str, Any], aspects_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Find the most dominant planets in the chart"""
        planet_scores = {}

        # Score based on aspects (each aspect gives points)
        for aspect in aspects_data:
            planet1 = aspect["planet1"].lower()
            planet2 = aspect["planet2"].lower()

            strength_points = {
                "Very Strong": 4,
                "Strong": 3,
                "Moderate": 2,
                "Weak": 1,
            }
            points = strength_points.get(aspect.get("strength", "Weak"), 1)

            planet_scores[planet1] = planet_scores.get(planet1, 0) + points
            planet_scores[planet2] = planet_scores.get(planet2, 0) + points

        # Sort by score and return top 3
        sorted_planets = sorted(
            planet_scores.items(), key=lambda x: x[1], reverse=True
        )
        return [planet.capitalize() for planet, score in sorted_planets[:3]]

    def generate_chart_svg(
        self,
        name: str,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        timezone: str = "Europe/Moscow",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        theme: str = "classic",
    ) -> Optional[str]:
        """Generate SVG chart using Kerykeion"""
        if not self.available or not KerykeionChartSVG:
            logger.error(
                "KERYKEION_SERVICE_SVG: Chart generation not available"
            )
            return None

        subject = self.create_astrological_subject(
            name, birth_datetime, latitude, longitude, timezone, house_system
        )

        if not subject:
            return None

        try:
            # Create chart SVG
            chart = KerykeionChartSVG(subject, theme=theme)
            svg_content = chart.makeSVG()

            logger.info(f"KERYKEION_SERVICE_SVG_SUCCESS: Generated for {name}")
            return svg_content

        except Exception as e:
            logger.error(f"KERYKEION_SERVICE_SVG_ERROR: {e}")
            return None

    def calculate_compatibility_detailed(
        self, person1_data: Dict[str, Any], person2_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate detailed compatibility using Kerykeion data"""
        if not person1_data.get("planets") or not person2_data.get("planets"):
            return {"error": "Insufficient chart data"}

        try:
            compatibility = {
                "overall_score": 0,
                "element_harmony": 0,
                "quality_harmony": 0,
                "sun_moon_connections": [],
                "venus_mars_connections": [],
                "significant_aspects": [],
                "house_overlays": {},
                "composite_analysis": {},
            }

            planets1 = person1_data["planets"]
            planets2 = person2_data["planets"]

            # Analyze Sun-Moon connections
            sun1 = planets1.get("sun", {})
            moon1 = planets1.get("moon", {})
            sun2 = planets2.get("sun", {})
            moon2 = planets2.get("moon", {})

            # Calculate cross aspects between luminaries
            luminaries_aspects = [
                (sun1, sun2, "Sun-Sun"),
                (sun1, moon2, "Sun-Moon"),
                (moon1, sun2, "Moon-Sun"),
                (moon1, moon2, "Moon-Moon"),
            ]

            for lum1, lum2, connection in luminaries_aspects:
                if lum1 and lum2:
                    aspect = self._calculate_aspect_between_points(
                        lum1.get("longitude", 0), lum2.get("longitude", 0)
                    )
                    if aspect:
                        compatibility["sun_moon_connections"].append(
                            {
                                "connection": connection,
                                "aspect": aspect,
                                "harmony_score": self._get_aspect_harmony_score(
                                    aspect
                                ),
                            }
                        )

            # Analyze Venus-Mars connections
            venus1 = planets1.get("venus", {})
            mars1 = planets1.get("mars", {})
            venus2 = planets2.get("venus", {})
            mars2 = planets2.get("mars", {})

            romance_aspects = [
                (venus1, venus2, "Venus-Venus"),
                (venus1, mars2, "Venus-Mars"),
                (mars1, venus2, "Mars-Venus"),
                (mars1, mars2, "Mars-Mars"),
            ]

            for rom1, rom2, connection in romance_aspects:
                if rom1 and rom2:
                    aspect = self._calculate_aspect_between_points(
                        rom1.get("longitude", 0), rom2.get("longitude", 0)
                    )
                    if aspect:
                        compatibility["venus_mars_connections"].append(
                            {
                                "connection": connection,
                                "aspect": aspect,
                                "passion_score": self._get_aspect_passion_score(
                                    aspect
                                ),
                            }
                        )

            # Calculate overall compatibility score
            total_score = 50  # Base score

            # Add scores from Sun-Moon connections
            for conn in compatibility["sun_moon_connections"]:
                total_score += conn["harmony_score"]

            # Add scores from Venus-Mars connections
            for conn in compatibility["venus_mars_connections"]:
                total_score += conn["passion_score"]

            compatibility["overall_score"] = max(0, min(100, total_score))

            logger.info("KERYKEION_SERVICE_COMPATIBILITY_CALCULATED")
            return compatibility

        except Exception as e:
            logger.error(f"KERYKEION_SERVICE_COMPATIBILITY_ERROR: {e}")
            return {"error": f"Compatibility calculation failed: {str(e)}"}

    def _calculate_aspect_between_points(
        self, long1: float, long2: float
    ) -> Optional[str]:
        """Calculate aspect between two longitude points"""
        angle = abs(long1 - long2)
        if angle > 180:
            angle = 360 - angle

        # Check major aspects
        aspects = {
            0: "Conjunction",
            60: "Sextile",
            90: "Square",
            120: "Trine",
            180: "Opposition",
        }

        for aspect_angle, aspect_name in aspects.items():
            orb = 8 if aspect_angle in [0, 90, 120, 180] else 6
            if abs(angle - aspect_angle) <= orb:
                return aspect_name

        return None

    def _get_aspect_harmony_score(self, aspect: str) -> int:
        """Get harmony score for an aspect"""
        scores = {
            "Conjunction": 5,
            "Trine": 8,
            "Sextile": 6,
            "Square": -3,
            "Opposition": -1,
        }
        return scores.get(aspect, 0)

    def _get_aspect_passion_score(self, aspect: str) -> int:
        """Get passion score for Venus-Mars aspects"""
        scores = {
            "Conjunction": 8,
            "Trine": 7,
            "Sextile": 5,
            "Square": 4,  # Tension can create attraction
            "Opposition": 6,  # Strong magnetic attraction
        }
        return scores.get(aspect, 0)

    def get_service_capabilities(self) -> Dict[str, Any]:
        """Get detailed information about service capabilities"""
        return {
            "available": self.available,
            "features": {
                "natal_charts": self.available,
                "aspect_calculation": self.available,
                "arabic_parts": self.available,
                "chart_shapes": self.available,
                "svg_generation": self.available
                and KerykeionChartSVG is not None,
                "house_systems": [system.value for system in HouseSystem]
                if self.available
                else [],
                "zodiac_types": [ztype.value for ztype in ZodiacType]
                if self.available
                else [],
                "aspect_colors": True,
                "detailed_compatibility": self.available,
                "element_analysis": True,
                "quality_analysis": True,
            },
            "limitations": []
            if self.available
            else [
                "Kerykeion library not installed",
                "Advanced features unavailable",
                "Chart generation not possible",
            ],
        }
