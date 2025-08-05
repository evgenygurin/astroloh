"""
Сервис расчета астрологических транзитов и прогрессий.
Расширяет существующую астрологическую функциональность новыми техниками анализа.
"""
import logging
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pytz

from app.services.astrology_calculator import AstrologyCalculator
from app.models.yandex_models import YandexZodiacSign


class TransitCalculator:
    """Калькулятор транзитов, прогрессий, соляров и лунаров."""

    def __init__(self):
        self.astro_calc = AstrologyCalculator()
        self.logger = logging.getLogger(__name__)

        # Орбы для транзитных аспектов (более строгие чем для натальных)
        self.transit_orbs = {
            0: 3,   # Соединение
            60: 2,  # Секстиль
            90: 3,  # Квадрат
            120: 3, # Трин
            180: 3, # Оппозиция
        }

        # Интерпретации транзитных аспектов
        self.transit_interpretations = {
            "Sun": {
                "description": "Влияние на личность, творчество и жизненную силу",
                "keywords": ["самовыражение", "лидерство", "энергия", "цели"],
            },
            "Moon": {
                "description": "Эмоциональные изменения, семейные вопросы",
                "keywords": ["эмоции", "семья", "интуиция", "настроение"],
            },
            "Mercury": {
                "description": "Коммуникации, обучение, поездки",
                "keywords": ["общение", "учеба", "решения", "информация"],
            },
            "Venus": {
                "description": "Отношения, финансы, творчество",
                "keywords": ["любовь", "деньги", "красота", "гармония"],
            },
            "Mars": {
                "description": "Действия, конфликты, энергия",
                "keywords": ["активность", "конфликты", "инициатива", "страсть"],
            },
            "Jupiter": {
                "description": "Возможности, рост, удача",
                "keywords": ["расширение", "путешествия", "удача", "философия"],
            },
            "Saturn": {
                "description": "Ограничения, структура, ответственность",
                "keywords": ["дисциплина", "работа", "структура", "ограничения"],
            },
            "Uranus": {
                "description": "Неожиданные изменения, свобода",
                "keywords": ["изменения", "свобода", "инновации", "неожиданность"],
            },
            "Neptune": {
                "description": "Иллюзии, духовность, творчество",
                "keywords": ["духовность", "иллюзии", "творчество", "мистика"],
            },
            "Pluto": {
                "description": "Трансформация, власть, глубокие изменения",
                "keywords": ["трансформация", "власть", "возрождение", "глубина"],
            },
        }

    def calculate_current_transits(
        self,
        birth_date: date,
        birth_time: Optional[time] = None,
        birth_place: Optional[Dict[str, float]] = None,
        current_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Вычисляет текущие транзиты планет к натальной карте.
        
        Args:
            birth_date: Дата рождения
            birth_time: Время рождения (по умолчанию полдень)
            birth_place: Место рождения (широта/долгота)
            current_date: Текущая дата (по умолчанию сейчас)
        
        Returns:
            Словарь с информацией о транзитах
        """
        try:
            # Настройка параметров по умолчанию
            if birth_time is None:
                birth_time = time(12, 0)
            if birth_place is None:
                birth_place = {"latitude": 55.7558, "longitude": 37.6176}  # Москва
            if current_date is None:
                current_date = datetime.now(pytz.UTC)

            # Создаем datetime для рождения
            birth_datetime = datetime.combine(birth_date, birth_time)
            birth_datetime = pytz.UTC.localize(birth_datetime)

            # Получаем натальные позиции планет
            natal_positions = self.astro_calc.calculate_planet_positions(
                birth_datetime, birth_place["latitude"], birth_place["longitude"]
            )

            # Получаем текущие позиции планет
            current_positions = self.astro_calc.calculate_planet_positions(
                current_date, birth_place["latitude"], birth_place["longitude"]
            )

            # Вычисляем транзитные аспекты
            transits = self._calculate_transit_aspects(
                natal_positions, current_positions
            )

            # Анализируем важные транзиты
            significant_transits = self._analyze_significant_transits(transits)

            # Генерируем интерпретацию
            interpretation = self._interpret_transits(significant_transits)

            return {
                "calculation_date": current_date.isoformat(),
                "birth_info": {
                    "date": birth_date.isoformat(),
                    "time": birth_time.strftime("%H:%M"),
                    "place": birth_place,
                },
                "natal_positions": natal_positions,
                "current_positions": current_positions,
                "all_transits": transits,
                "significant_transits": significant_transits,
                "interpretation": interpretation,
                "summary": self._create_transit_summary(significant_transits),
            }

        except Exception as e:
            self.logger.error(f"Transit calculation error: {str(e)}")
            return {
                "error": "Не удалось рассчитать транзиты",
                "details": str(e),
                "calculation_date": datetime.now().isoformat(),
            }

    def _calculate_transit_aspects(
        self,
        natal_positions: Dict[str, Dict[str, Any]],
        current_positions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Вычисляет аспекты между транзитными и натальными планетами."""
        transits = []

        for transit_planet, transit_data in current_positions.items():
            for natal_planet, natal_data in natal_positions.items():
                # Получаем долготы планет
                transit_lon = transit_data.get("longitude", 0)
                natal_lon = natal_data.get("longitude", 0)

                # Вычисляем угол между планетами
                angle = abs(transit_lon - natal_lon)
                if angle > 180:
                    angle = 360 - angle

                # Проверяем аспекты с учетом орбов
                for aspect_angle, orb in self.transit_orbs.items():
                    if abs(angle - aspect_angle) <= orb:
                        aspect_name = self._get_aspect_name(aspect_angle)
                        
                        transit_info = {
                            "transit_planet": transit_planet,
                            "natal_planet": natal_planet,
                            "aspect": aspect_name,
                            "aspect_angle": aspect_angle,
                            "exact_angle": angle,
                            "orb": abs(angle - aspect_angle),
                            "transit_position": {
                                "longitude": transit_lon,
                                "sign": transit_data.get("sign"),
                                "degree_in_sign": transit_data.get("degree_in_sign"),
                            },
                            "natal_position": {
                                "longitude": natal_lon,
                                "sign": natal_data.get("sign"),
                                "degree_in_sign": natal_data.get("degree_in_sign"),
                            },
                            "strength": self._calculate_transit_strength(
                                transit_planet, natal_planet, aspect_angle, orb
                            ),
                        }
                        transits.append(transit_info)
                        break

        return transits

    def _analyze_significant_transits(
        self, transits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Выделяет наиболее значимые транзиты."""
        # Сортируем по важности (сила аспекта и близость к точности)
        sorted_transits = sorted(
            transits,
            key=lambda t: (t["strength"], -t["orb"]),
            reverse=True
        )

        # Берем топ-10 наиболее значимых транзитов
        significant = sorted_transits[:10]

        # Добавляем дополнительную информацию
        for transit in significant:
            transit["timing"] = self._analyze_transit_timing(transit)
            transit["interpretation"] = self._get_transit_interpretation(transit)

        return significant

    def _calculate_transit_strength(
        self, transit_planet: str, natal_planet: str, aspect_angle: float, orb: float
    ) -> float:
        """Вычисляет силу транзитного аспекта."""
        # Базовая сила по планетам
        planet_weights = {
            "Sun": 10, "Moon": 9, "Mercury": 6, "Venus": 7, "Mars": 7,
            "Jupiter": 8, "Saturn": 9, "Uranus": 6, "Neptune": 5, "Pluto": 7
        }

        # Сила аспекта
        aspect_weights = {0: 10, 90: 8, 180: 8, 120: 6, 60: 4}

        transit_weight = planet_weights.get(transit_planet, 5)
        natal_weight = planet_weights.get(natal_planet, 5)
        aspect_weight = aspect_weights.get(aspect_angle, 3)

        # Учитываем точность (меньший орб = больше силы)
        max_orb = self.transit_orbs.get(aspect_angle, 3)
        accuracy_factor = (max_orb - orb) / max_orb

        return (transit_weight + natal_weight) * aspect_weight * accuracy_factor / 10

    def _analyze_transit_timing(self, transit: Dict[str, Any]) -> Dict[str, str]:
        """Анализирует тайминг транзита."""
        orb = transit["orb"]
        
        if orb < 0.5:
            timing_phase = "точный"
            description = "Аспект в самой активной фазе"
        elif orb < 1.0:
            timing_phase = "близкий"
            description = "Аспект очень близок к точности"
        elif orb < 2.0:
            timing_phase = "приближающийся"
            description = "Влияние аспекта нарастает"
        else:
            timing_phase = "слабый"
            description = "Влияние аспекта ощущается в фоновом режиме"

        return {
            "phase": timing_phase,
            "description": description,
        }

    def _get_transit_interpretation(self, transit: Dict[str, Any]) -> Dict[str, str]:
        """Создает интерпретацию транзитного аспекта."""
        transit_planet = transit["transit_planet"]
        natal_planet = transit["natal_planet"]
        aspect = transit["aspect"]

        transit_info = self.transit_interpretations.get(transit_planet, {})
        
        # Базовое описание влияния планеты
        base_influence = transit_info.get("description", "Общее влияние на жизнь")
        
        # Характер аспекта
        aspect_nature = self._get_aspect_nature(aspect)
        
        interpretation = {
            "summary": f"{transit_planet} {aspect.lower()} {natal_planet}",
            "influence": base_influence,
            "nature": aspect_nature,
            "advice": self._get_transit_advice(transit_planet, aspect),
        }

        return interpretation

    def _get_aspect_nature(self, aspect: str) -> str:
        """Возвращает характер аспекта."""
        aspect_natures = {
            "Соединение": "интенсивное, концентрированное влияние",
            "Секстиль": "гармоничные возможности, легкие изменения",
            "Квадрат": "напряжение, вызовы, необходимость действий",
            "Трин": "благоприятное течение, естественные возможности",
            "Оппозиция": "поляризация, необходимость баланса",
        }
        return aspect_natures.get(aspect, "смешанное влияние")

    def _get_transit_advice(self, planet: str, aspect: str) -> str:
        """Дает совет по транзитному аспекту."""
        advice_templates = {
            ("Sun", "Соединение"): "Время для проявления лидерства и творчества",
            ("Sun", "Квадрат"): "Преодолевайте препятствия с уверенностью",
            ("Moon", "Соединение"): "Доверьтесь интуиции и эмоциям",
            ("Mercury", "Секстиль"): "Благоприятное время для общения и обучения",
            ("Venus", "Трин"): "Наслаждайтесь гармонией в отношениях",
            ("Mars", "Квадрат"): "Направьте энергию в конструктивное русло",
            ("Jupiter", "Трин"): "Используйте возможности для роста",
            ("Saturn", "Квадрат"): "Время дисциплины и серьезной работы",
        }

        key = (planet, aspect)
        return advice_templates.get(key, "Будьте внимательны к изменениям в жизни")

    def calculate_progressions(
        self,
        birth_date: date,
        birth_time: Optional[time] = None,
        birth_place: Optional[Dict[str, float]] = None,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Вычисляет прогрессии (символическое развитие натальной карты).
        Использует метод "день за год".
        """
        try:
            if birth_time is None:
                birth_time = time(12, 0)
            if birth_place is None:
                birth_place = {"latitude": 55.7558, "longitude": 37.6176}
            if target_date is None:
                target_date = date.today()

            # Вычисляем прогрессивную дату (день за год)
            days_lived = (target_date - birth_date).days
            years_lived = days_lived / 365.25
            progression_date = birth_date + timedelta(days=years_lived)

            # Создаем datetime для прогрессивной даты
            progression_datetime = datetime.combine(progression_date, birth_time)
            progression_datetime = pytz.UTC.localize(progression_datetime)

            # Вычисляем натальные позиции
            birth_datetime = datetime.combine(birth_date, birth_time)
            birth_datetime = pytz.UTC.localize(birth_datetime)
            
            natal_positions = self.astro_calc.calculate_planet_positions(
                birth_datetime, birth_place["latitude"], birth_place["longitude"]
            )

            # Вычисляем прогрессивные позиции
            progressed_positions = self.astro_calc.calculate_planet_positions(
                progression_datetime, birth_place["latitude"], birth_place["longitude"]
            )

            # Анализируем изменения
            progressions = self._analyze_progressions(
                natal_positions, progressed_positions
            )

            return {
                "calculation_date": target_date.isoformat(),
                "birth_info": {
                    "date": birth_date.isoformat(),
                    "time": birth_time.strftime("%H:%M"),
                    "place": birth_place,
                },
                "progression_date": progression_date.isoformat(),
                "years_lived": round(years_lived, 2),
                "natal_positions": natal_positions,
                "progressed_positions": progressed_positions,
                "progressions": progressions,
                "interpretation": self._interpret_progressions(progressions),
            }

        except Exception as e:
            self.logger.error(f"Progression calculation error: {str(e)}")
            return {
                "error": "Не удалось рассчитать прогрессии",
                "details": str(e),
            }

    def _analyze_progressions(
        self,
        natal_positions: Dict[str, Dict[str, Any]],
        progressed_positions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Анализирует прогрессивные изменения."""
        progressions = []

        for planet in ["Sun", "Moon", "Mercury", "Venus", "Mars"]:
            if planet in natal_positions and planet in progressed_positions:
                natal_lon = natal_positions[planet]["longitude"]
                progressed_lon = progressed_positions[planet]["longitude"]
                
                # Вычисляем движение планеты
                movement = progressed_lon - natal_lon
                if movement > 180:
                    movement -= 360
                elif movement < -180:
                    movement += 360

                progression = {
                    "planet": planet,
                    "natal_position": natal_positions[planet],
                    "progressed_position": progressed_positions[planet],
                    "movement_degrees": round(movement, 2),
                    "interpretation": self._interpret_progression_movement(
                        planet, movement
                    ),
                }
                progressions.append(progression)

        return progressions

    def _interpret_progression_movement(
        self, planet: str, movement: float
    ) -> Dict[str, str]:
        """Интерпретирует движение планеты в прогрессии."""
        interpretations = {
            "Sun": "эволюция личности и самовыражения",
            "Moon": "изменение эмоциональных потребностей",
            "Mercury": "развитие мышления и коммуникации",
            "Venus": "трансформация ценностей и отношений",
            "Mars": "изменение способа действий и желаний",
        }

        base_meaning = interpretations.get(planet, "общее развитие")
        
        if abs(movement) < 5:
            phase = "стабильная"
            description = f"Медленное, устойчивое развитие в области {base_meaning}"
        elif abs(movement) < 15:
            phase = "умеренная"
            description = f"Заметные изменения в {base_meaning}"
        else:
            phase = "активная"
            description = f"Значительная трансформация в {base_meaning}"

        return {
            "phase": phase,
            "description": description,
        }

    def _interpret_progressions(
        self, progressions: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Создает общую интерпретацию прогрессий."""
        if not progressions:
            return {"summary": "Прогрессии не рассчитаны"}

        # Анализируем общие тенденции
        active_progressions = [
            p for p in progressions if abs(p["movement_degrees"]) > 10
        ]

        if len(active_progressions) >= 3:
            life_phase = "период активных изменений"
        elif len(active_progressions) >= 1:
            life_phase = "период умеренных изменений"
        else:
            life_phase = "период стабильности"

        return {
            "life_phase": life_phase,
            "summary": f"В вашей жизни наступил {life_phase}",
            "advice": "Следуйте естественному ритму развития личности",
        }

    def calculate_solar_return(
        self,
        birth_date: date,
        birth_time: Optional[time] = None,
        birth_place: Optional[Dict[str, float]] = None,
        target_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Вычисляет соляр (солнечное возвращение) на заданный год.
        """
        try:
            if birth_time is None:
                birth_time = time(12, 0)
            if birth_place is None:
                birth_place = {"latitude": 55.7558, "longitude": 37.6176}
            if target_year is None:
                target_year = date.today().year

            # Находим точную дату солнечного возвращения
            solar_return_date = self._find_solar_return_date(
                birth_date, target_year
            )

            # Создаем datetime для соляра
            solar_datetime = datetime.combine(solar_return_date, birth_time)
            solar_datetime = pytz.UTC.localize(solar_datetime)

            # Вычисляем позиции планет на момент соляра
            solar_positions = self.astro_calc.calculate_planet_positions(
                solar_datetime, birth_place["latitude"], birth_place["longitude"]
            )

            # Вычисляем дома соляра
            solar_houses = self.astro_calc.calculate_houses(
                solar_datetime, birth_place["latitude"], birth_place["longitude"]
            )

            return {
                "solar_year": target_year,
                "solar_date": solar_return_date.isoformat(),
                "birth_info": {
                    "date": birth_date.isoformat(),
                    "time": birth_time.strftime("%H:%M"),
                    "place": birth_place,
                },
                "solar_positions": solar_positions,
                "solar_houses": solar_houses,
                "interpretation": self._interpret_solar_return(
                    solar_positions, solar_houses
                ),
            }

        except Exception as e:
            self.logger.error(f"Solar return calculation error: {str(e)}")
            return {
                "error": "Не удалось рассчитать соляр",
                "details": str(e),
            }

    def _find_solar_return_date(self, birth_date: date, target_year: int) -> date:
        """Находит точную дату солнечного возвращения."""
        # Приблизительная дата (день рождения в целевом году)
        approximate_date = date(target_year, birth_date.month, birth_date.day)
        
        # Для упрощения возвращаем приблизительную дату
        # В реальной реализации здесь бы был точный расчет
        return approximate_date

    def _interpret_solar_return(
        self,
        solar_positions: Dict[str, Dict[str, Any]],
        solar_houses: Dict[int, Dict[str, Any]],
    ) -> Dict[str, str]:
        """Интерпретирует соляр."""
        # Анализируем асцендент соляра
        asc_sign = solar_houses.get("ascendant", {}).get("sign", "Овен")
        
        # Анализируем Солнце в домах
        sun_house = self._find_planet_house(
            solar_positions["Sun"]["longitude"], solar_houses
        )

        year_themes = {
            1: "новые начинания и самопознание",
            2: "материальная стабильность и ценности",
            3: "общение и обучение",
            4: "семья и дом",
            5: "творчество и самовыражение",
            6: "здоровье и работа",
            7: "отношения и партнерство",
            8: "трансформация и глубокие изменения",
            9: "путешествия и философия",
            10: "карьера и репутация",
            11: "дружба и социальные связи",
            12: "духовность и внутренняя работа",
        }

        main_theme = year_themes.get(sun_house, "личностное развитие")

        return {
            "year_theme": main_theme,
            "ascendant_influence": f"Год пройдет под влиянием {asc_sign}",
            "summary": f"Этот год будет посвящен {main_theme}",
        }

    def calculate_lunar_return(
        self,
        birth_date: date,
        birth_time: Optional[time] = None,
        birth_place: Optional[Dict[str, float]] = None,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Вычисляет лунар (лунное возвращение) на ближайший к целевой дате.
        """
        try:
            if birth_time is None:
                birth_time = time(12, 0)
            if birth_place is None:
                birth_place = {"latitude": 55.7558, "longitude": 37.6176}
            if target_date is None:
                target_date = date.today()

            # Находим ближайшее лунное возвращение
            lunar_return_date = self._find_lunar_return_date(
                birth_date, target_date
            )

            # Создаем datetime для лунара
            lunar_datetime = datetime.combine(lunar_return_date, birth_time)
            lunar_datetime = pytz.UTC.localize(lunar_datetime)

            # Вычисляем позиции планет на момент лунара
            lunar_positions = self.astro_calc.calculate_planet_positions(
                lunar_datetime, birth_place["latitude"], birth_place["longitude"]
            )

            return {
                "lunar_date": lunar_return_date.isoformat(),
                "target_date": target_date.isoformat(),
                "birth_info": {
                    "date": birth_date.isoformat(),
                    "time": birth_time.strftime("%H:%M"),
                    "place": birth_place,
                },
                "lunar_positions": lunar_positions,
                "interpretation": self._interpret_lunar_return(lunar_positions),
            }

        except Exception as e:
            self.logger.error(f"Lunar return calculation error: {str(e)}")
            return {
                "error": "Не удалось рассчитать лунар",
                "details": str(e),
            }

    def _find_lunar_return_date(self, birth_date: date, target_date: date) -> date:
        """Находит ближайшую дату лунного возвращения."""
        # Упрощенный расчет - ближайшее новолуние
        # В реальной реализации здесь был бы точный расчет лунных циклов
        
        # Приблизительный лунный цикл 29.5 дней
        days_from_birth = (target_date - birth_date).days
        lunar_cycles = days_from_birth // 29
        
        approximate_return = birth_date + timedelta(days=lunar_cycles * 29)
        
        # Корректируем к ближайшей дате
        if approximate_return < target_date:
            approximate_return += timedelta(days=29)
        
        return approximate_return

    def _interpret_lunar_return(
        self, lunar_positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Интерпретирует лунар."""
        moon_sign = lunar_positions.get("Moon", {}).get("sign", "Рак")
        
        moon_themes = {
            "Овен": "активные эмоции и импульсивность",
            "Телец": "потребность в стабильности и комфорте",
            "Близнецы": "любопытство и общение",
            "Рак": "семейные вопросы и интуиция",
            "Лев": "творческое самовыражение",
            "Дева": "практичность и анализ",
            "Весы": "гармония в отношениях",
            "Скорпион": "глубокие эмоциональные процессы",
            "Стрелец": "поиск смысла и новых горизонтов",
            "Козерог": "ответственность и структура",
            "Водолей": "независимость и инновации",
            "Рыбы": "духовность и сострадание",
        }

        theme = moon_themes.get(moon_sign, "эмоциональное развитие")

        return {
            "monthly_theme": theme,
            "moon_influence": f"Месяц пройдет под влиянием Луны в {moon_sign}",
            "summary": f"Этот лунный месяц будет посвящен {theme}",
        }

    def _find_planet_house(
        self, planet_longitude: float, houses: Dict[int, Dict[str, Any]]
    ) -> int:
        """Определяет, в каком доме находится планета."""
        for house_num in range(1, 13):
            if house_num in houses:
                house_start = houses[house_num]["cusp_longitude"]
                next_house = (house_num % 12) + 1
                
                # Получаем начало следующего дома
                if next_house in houses:
                    house_end = houses[next_house]["cusp_longitude"]
                else:
                    house_end = (house_start + 30) % 360

                # Проверяем, попадает ли планета в этот дом
                if house_start <= house_end:
                    if house_start <= planet_longitude < house_end:
                        return house_num
                else:  # Переход через 0 градусов
                    if planet_longitude >= house_start or planet_longitude < house_end:
                        return house_num

        return 1  # По умолчанию первый дом

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

    def _create_transit_summary(
        self, significant_transits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Создает краткое резюме транзитов."""
        if not significant_transits:
            return {
                "overall_influence": "спокойный",
                "main_themes": ["стабильность"],
                "advice": "Наслаждайтесь периодом относительного спокойствия",
            }

        # Анализируем общие темы
        planet_counts = {}
        aspect_counts = {}
        
        for transit in significant_transits:
            planet = transit["transit_planet"]
            aspect = transit["aspect"]
            
            planet_counts[planet] = planet_counts.get(planet, 0) + 1
            aspect_counts[aspect] = aspect_counts.get(aspect, 0) + 1

        # Определяем доминирующую планету
        dominant_planet = max(planet_counts, key=planet_counts.get)
        
        # Определяем общий характер периода
        challenging_aspects = aspect_counts.get("Квадрат", 0) + aspect_counts.get("Оппозиция", 0)
        harmonious_aspects = aspect_counts.get("Трин", 0) + aspect_counts.get("Секстиль", 0)
        
        if challenging_aspects > harmonious_aspects:
            overall_influence = "вызовы и рост"
            advice = "Используйте напряжение для позитивных изменений"
        elif harmonious_aspects > challenging_aspects:
            overall_influence = "благоприятный"
            advice = "Воспользуйтесь открывающимися возможностями"
        else:
            overall_influence = "смешанный"
            advice = "Балансируйте между действием и размышлением"

        # Основные темы на основе доминирующей планеты
        main_themes = self.transit_interpretations.get(
            dominant_planet, {}
        ).get("keywords", ["изменения"])

        return {
            "overall_influence": overall_influence,
            "dominant_planet": dominant_planet,
            "main_themes": main_themes[:3],
            "transit_count": len(significant_transits),
            "advice": advice,
        }