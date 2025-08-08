"""
Сервис прогрессий и временных астрологических техник.
Поддерживает вторичные прогрессии, символические дирекции и возвращения.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pytz

from app.services.kerykeion_service import KerykeionService
from app.services.astrology_calculator import AstrologyCalculator
from app.models.transit_models import (
    ProgressionData,
    ProgressionInterpretation,
    ProgressedPlanet,
    SolarReturnData,
    SolarReturnInterpretation,
    LunarReturnData,
    LunarReturnInterpretation,
    ProgressionRequest,
    SolarReturnRequest,
    LunarReturnRequest,
    ProgressionAnalysisResult,
    YearlyForecast,
    MonthlyGuidance
)

logger = logging.getLogger(__name__)

# Try to import additional Kerykeion features for progressions
try:
    from kerykeion import AstrologicalSubject
    # Try different progression imports
    try:
        from kerykeion.progressions import SecondaryProgressions
    except ImportError:
        SecondaryProgressions = None
    
    try:
        from kerykeion.solar_return import SolarReturn
    except ImportError:
        SolarReturn = None
    
    KERYKEION_PROGRESSIONS_AVAILABLE = SecondaryProgressions is not None
    logger.info("PROGRESSION_SERVICE_INIT: Kerykeion progressions available")
except ImportError as e:
    logger.warning(f"PROGRESSION_SERVICE_INIT: Kerykeion progressions not available - {e}")
    KERYKEION_PROGRESSIONS_AVAILABLE = False
    SecondaryProgressions = None
    SolarReturn = None


class ProgressionService:
    """Сервис для анализа прогрессий и временных техник астрологии."""

    def __init__(self):
        self.kerykeion_service = KerykeionService()
        self.astro_calculator = AstrologyCalculator()
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Проверяет доступность функций прогрессий."""
        return self.kerykeion_service.is_available()

    def get_secondary_progressions(
        self,
        natal_chart: Dict[str, Any],
        target_date: Optional[date] = None,
        include_interpretation: bool = True
    ) -> Dict[str, Any]:
        """
        Вычисляет вторичные прогрессии.
        
        Args:
            natal_chart: Данные натальной карты
            target_date: Дата для расчета прогрессий
            include_interpretation: Включать интерпретацию
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"PROGRESSION_SERVICE_SECONDARY_START: {target_date}")

        birth_date = datetime.fromisoformat(natal_chart.get("birth_datetime", "2000-01-01T12:00:00")).date()
        days_progressed = (target_date - birth_date).days

        # Попробуем использовать Kerykeion, если доступен
        if KERYKEION_PROGRESSIONS_AVAILABLE and self.kerykeion_service.is_available():
            return self._get_kerykeion_progressions(natal_chart, target_date, days_progressed)
        else:
            # Fallback к базовому методу
            logger.warning("PROGRESSION_SERVICE_SECONDARY_FALLBACK: Using basic method")
            return self._get_basic_progressions(natal_chart, target_date, days_progressed)

    def _get_kerykeion_progressions(
        self,
        natal_chart: Dict[str, Any],
        target_date: date,
        days_progressed: int
    ) -> Dict[str, Any]:
        """Получает прогрессии через Kerykeion."""
        try:
            # Создаем натальную карту
            birth_datetime = datetime.fromisoformat(natal_chart.get("birth_datetime", "2000-01-01T12:00:00"))
            coordinates = natal_chart.get("coordinates", {"latitude": 55.7558, "longitude": 37.6176})
            
            natal_subject = self.kerykeion_service.create_astrological_subject(
                name="NatalChart",
                birth_datetime=birth_datetime,
                latitude=coordinates["latitude"],
                longitude=coordinates["longitude"]
            )
            
            if not natal_subject:
                raise ValueError("Failed to create natal subject")

            # Создаем прогрессированную карту (день = год)
            progression_date = birth_datetime + timedelta(days=days_progressed)
            
            progressed_subject = self.kerykeion_service.create_astrological_subject(
                name="ProgressedChart",
                birth_datetime=progression_date,
                latitude=coordinates["latitude"],
                longitude=coordinates["longitude"]
            )

            if not progressed_subject:
                raise ValueError("Failed to create progressed subject")

            # Получаем данные прогрессированных планет
            progressed_planets = self._extract_progressed_planets(progressed_subject)
            
            # Создаем интерпретацию
            interpretation = self._create_progression_interpretation(
                progressed_planets, 
                days_progressed,
                target_date
            )

            logger.info("PROGRESSION_SERVICE_KERYKEION_SUCCESS")
            return {
                "birth_date": birth_datetime.date().isoformat(),
                "progression_date": target_date.isoformat(),
                "days_progressed": days_progressed,
                "progressed_planets": progressed_planets,
                "interpretation": interpretation,
                "key_changes": self._identify_key_changes(progressed_planets, natal_chart.get("planets", {})),
                "life_phase_analysis": self._analyze_life_phase(days_progressed),
                "spiritual_evolution": self._assess_spiritual_evolution(progressed_planets),
                "source": "kerykeion"
            }

        except Exception as e:
            logger.error(f"PROGRESSION_SERVICE_KERYKEION_ERROR: {e}")
            return self._get_basic_progressions(natal_chart, target_date, days_progressed)

    def _get_basic_progressions(
        self,
        natal_chart: Dict[str, Any],
        target_date: date,
        days_progressed: int
    ) -> Dict[str, Any]:
        """Fallback метод для расчета прогрессий."""
        logger.info("PROGRESSION_SERVICE_BASIC_PROGRESSION")
        
        # Простой расчет: день = год
        birth_datetime = datetime.fromisoformat(natal_chart.get("birth_datetime", "2000-01-01T12:00:00"))
        progression_datetime = birth_datetime + timedelta(days=days_progressed)
        
        # Получаем позиции планет на прогрессированную дату
        progressed_positions = self.astro_calculator.calculate_planet_positions(progression_datetime)
        
        # Преобразуем в формат прогрессированных планет
        progressed_planets = {}
        for planet, data in progressed_positions.items():
            progressed_planets[planet] = {
                "longitude": data.get("longitude", 0),
                "sign": data.get("sign", "Unknown"),
                "degree_in_sign": data.get("longitude", 0) % 30,
                "house": data.get("house"),
                "speed": data.get("speed", 0),
                "retrograde": data.get("retrograde", False)
            }

        # Создаем базовую интерпретацию
        interpretation = self._create_basic_progression_interpretation(
            progressed_planets, 
            days_progressed,
            target_date
        )

        return {
            "birth_date": birth_datetime.date().isoformat(),
            "progression_date": target_date.isoformat(),
            "days_progressed": days_progressed,
            "progressed_planets": progressed_planets,
            "interpretation": interpretation,
            "key_changes": self._identify_basic_key_changes(progressed_planets),
            "source": "basic"
        }

    def get_solar_return(
        self,
        natal_chart: Dict[str, Any],
        year: int,
        location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Вычисляет соляр (годовую карту).
        
        Args:
            natal_chart: Данные натальной карты
            year: Год соляра
            location: Место для расчета соляра (опционально)
        """
        logger.info(f"PROGRESSION_SERVICE_SOLAR_RETURN_START: {year}")

        birth_datetime = datetime.fromisoformat(natal_chart.get("birth_datetime", "2000-01-01T12:00:00"))
        
        if location is None:
            coordinates = natal_chart.get("coordinates", {"latitude": 55.7558, "longitude": 37.6176})
        else:
            coordinates = location

        # Определяем дату соляра (приблизительно день рождения в указанном году)
        solar_date = date(year, birth_datetime.month, birth_datetime.day)
        
        # Попробуем найти точное время соляра (когда Солнце возвращается в натальную позицию)
        solar_datetime = self._find_exact_solar_return_time(
            birth_datetime, 
            year,
            coordinates
        )

        # Рассчитываем позиции планет на соляр
        solar_positions = self.astro_calculator.calculate_planet_positions(
            solar_datetime, 
            coordinates["latitude"], 
            coordinates["longitude"]
        )

        # Рассчитываем дома для соляра
        solar_houses = self.astro_calculator.calculate_houses(
            solar_datetime,
            coordinates["latitude"], 
            coordinates["longitude"]
        )

        # Создаем интерпретацию соляра
        interpretation = self._interpret_solar_return(
            solar_positions, 
            solar_houses,
            year
        )

        return {
            "year": year,
            "date": solar_date.isoformat(),
            "exact_time": solar_datetime.isoformat(),
            "location": coordinates,
            "planets": solar_positions,
            "houses": solar_houses,
            "interpretation": interpretation,
            "themes": self._get_solar_themes(solar_positions, solar_houses),
            "monthly_highlights": self._get_monthly_highlights(solar_positions),
            "seasonal_guidance": self._get_seasonal_guidance(solar_positions),
            "success_indicators": self._identify_success_indicators(solar_positions, solar_houses),
            "caution_periods": self._identify_caution_periods(solar_positions)
        }

    def get_lunar_return(
        self,
        natal_chart: Dict[str, Any],
        month: int,
        year: int,
        location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Вычисляет лунар (месячную карту).
        
        Args:
            natal_chart: Данные натальной карты
            month: Месяц лунара
            year: Год лунара
            location: Место для расчета лунара
        """
        logger.info(f"PROGRESSION_SERVICE_LUNAR_RETURN_START: {month}/{year}")

        if location is None:
            coordinates = natal_chart.get("coordinates", {"latitude": 55.7558, "longitude": 37.6176})
        else:
            coordinates = location

        # Находим новолуние в указанном месяце (приблизительно)
        new_moon_date = self._find_new_moon_date(year, month)
        
        # Рассчитываем позиции планет на лунар
        lunar_positions = self.astro_calculator.calculate_planet_positions(
            new_moon_date,
            coordinates["latitude"],
            coordinates["longitude"]
        )

        # Рассчитываем дома для лунара
        lunar_houses = self.astro_calculator.calculate_houses(
            new_moon_date,
            coordinates["latitude"],
            coordinates["longitude"]
        )

        # Создаем интерпретацию лунара
        interpretation = self._interpret_lunar_return(
            lunar_positions,
            lunar_houses,
            month
        )

        return {
            "month": month,
            "year": year,
            "new_moon_date": new_moon_date.isoformat(),
            "location": coordinates,
            "planets": lunar_positions,
            "houses": lunar_houses,
            "interpretation": interpretation,
            "monthly_themes": self._get_lunar_themes(lunar_positions),
            "weekly_rhythms": self._get_weekly_rhythms(lunar_positions),
            "emotional_guidance": self._get_emotional_guidance(lunar_positions),
            "optimal_timing": self._get_optimal_lunar_timing(lunar_positions)
        }

    # Helper methods for progressions

    def _extract_progressed_planets(self, progressed_subject: Any) -> Dict[str, Dict[str, Any]]:
        """Извлекает данные прогрессированных планет."""
        progressed_planets = {}
        
        planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
        
        for planet in planets:
            if hasattr(progressed_subject, planet):
                planet_data = getattr(progressed_subject, planet)
                if planet_data:
                    progressed_planets[planet] = {
                        "longitude": planet_data.get("pos", [0])[0],
                        "sign": planet_data.get("sign", "Unknown"),
                        "degree_in_sign": planet_data.get("deg_in_sign", 0),
                        "house": planet_data.get("house"),
                        "speed": planet_data.get("speed", 0),
                        "retrograde": planet_data.get("retrograde", False)
                    }
        
        return progressed_planets

    def _create_progression_interpretation(
        self,
        progressed_planets: Dict[str, Any],
        days_progressed: int,
        target_date: date
    ) -> Dict[str, Any]:
        """Создает интерпретацию прогрессий."""
        current_age = days_progressed // 365
        
        # Определяем этап жизни
        life_stage = self._determine_life_stage(current_age)
        
        # Анализируем прогрессированное Солнце
        prog_sun = progressed_planets.get("sun", {})
        progressed_sun = ProgressedPlanet(
            sign=prog_sun.get("sign", "Unknown"),
            meaning=self._interpret_progressed_sun(prog_sun.get("sign", "Unknown"), current_age)
        )
        
        # Анализируем прогрессированную Луну
        prog_moon = progressed_planets.get("moon", {})
        progressed_moon = ProgressedPlanet(
            sign=prog_moon.get("sign", "Unknown"),
            meaning=self._interpret_progressed_moon(prog_moon.get("sign", "Unknown"))
        )
        
        # Определяем общие тенденции
        general_trends = self._identify_general_trends(progressed_planets, current_age)
        
        return ProgressionInterpretation(
            current_age=current_age,
            life_stage=life_stage,
            progressed_sun=progressed_sun,
            progressed_moon=progressed_moon,
            general_trends=general_trends
        )

    def _create_basic_progression_interpretation(
        self,
        progressed_planets: Dict[str, Any],
        days_progressed: int,
        target_date: date
    ) -> Dict[str, Any]:
        """Создает базовую интерпретацию прогрессий."""
        current_age = days_progressed // 365
        life_stage = self._determine_life_stage(current_age)
        
        return {
            "current_age": current_age,
            "life_stage": life_stage,
            "progressed_sun": {
                "sign": progressed_planets.get("sun", {}).get("sign", "Unknown"),
                "meaning": f"Развитие личности через энергию знака {progressed_planets.get('sun', {}).get('sign', 'Unknown')}"
            },
            "progressed_moon": {
                "sign": progressed_planets.get("moon", {}).get("sign", "Unknown"),
                "meaning": f"Эмоциональное развитие в энергии {progressed_planets.get('moon', {}).get('sign', 'Unknown')}"
            },
            "general_trends": [
                f"Возрастной этап: {life_stage}",
                "Постепенная эволюция личности",
                "Развитие через опыт и время"
            ]
        }

    def _determine_life_stage(self, age: int) -> str:
        """Определяет этап жизни по возрасту."""
        if age < 7:
            return "Детство и формирование основ"
        elif age < 14:
            return "Отрочество и самоидентификация"
        elif age < 21:
            return "Юность и поиск направления"
        elif age < 29:
            return "Молодость и становление"
        elif age < 42:
            return "Зрелость и реализация"
        elif age < 56:
            return "Расцвет и мастерство"
        elif age < 70:
            return "Мудрость и передача опыта"
        else:
            return "Старшая мудрость и духовность"

    def _interpret_progressed_sun(self, sign: str, age: int) -> str:
        """Интерпретирует прогрессированное Солнце."""
        sun_interpretations = {
            "Овен": f"В {age} лет развитие лидерских качеств и инициативности",
            "Телец": f"В {age} лет стремление к стабильности и материальной безопасности",
            "Близнецы": f"В {age} лет активизация коммуникации и обучения",
            "Рак": f"В {age} лет фокус на семье и эмоциональной безопасности",
            "Лев": f"В {age} лет творческое самовыражение и поиск признания",
            "Дева": f"В {age} лет совершенствование навыков и служение",
            "Весы": f"В {age} лет развитие отношений и поиск гармонии",
            "Скорпион": f"В {age} лет глубокие трансформации и исследование тайн",
            "Стрелец": f"В {age} лет расширение горизонтов и поиск смысла",
            "Козерог": f"В {age} лет достижение целей и построение структур",
            "Водолей": f"В {age} лет гуманитарные идеалы и инновации",
            "Рыбы": f"В {age} лет духовное развитие и сострадание"
        }
        
        return sun_interpretations.get(sign, f"В {age} лет развитие через энергию {sign}")

    def _interpret_progressed_moon(self, sign: str) -> str:
        """Интерпретирует прогрессированную Луну."""
        moon_interpretations = {
            "Овен": "Эмоциональная импульсивность и потребность в действии",
            "Телец": "Эмоциональная стабильность и потребность в комфорте",
            "Близнецы": "Эмоциональная любознательность и потребность в общении",
            "Рак": "Эмоциональная чувствительность и потребность в защите",
            "Лев": "Эмоциональная драматичность и потребность в признании",
            "Дева": "Эмоциональная сдержанность и потребность в порядке",
            "Весы": "Эмоциональный поиск гармонии и потребность в партнерстве",
            "Скорпион": "Эмоциональная интенсивность и потребность в глубине",
            "Стрелец": "Эмоциональный оптимизм и потребность в свободе",
            "Козерог": "Эмоциональная серьезность и потребность в структуре",
            "Водолей": "Эмоциональная независимость и потребность в уникальности",
            "Рыбы": "Эмоциональная чуткость и потребность в единении"
        }
        
        return moon_interpretations.get(sign, f"Эмоциональное развитие через {sign}")

    def _identify_key_changes(
        self,
        progressed_planets: Dict[str, Any],
        natal_planets: Dict[str, Any]
    ) -> List[str]:
        """Определяет ключевые изменения в прогрессиях."""
        changes = []
        
        # Сравниваем знаки натальных и прогрессированных планет
        for planet, prog_data in progressed_planets.items():
            natal_data = natal_planets.get(planet, {})
            
            prog_sign = prog_data.get("sign", "")
            natal_sign = natal_data.get("sign", "")
            
            if prog_sign != natal_sign and prog_sign and natal_sign:
                changes.append(
                    f"{planet.capitalize()} перешла из {natal_sign} в {prog_sign} - "
                    f"новая фаза развития в сфере {self._get_planet_sphere(planet)}"
                )
        
        # Если нет смены знаков, указываем на продолжающееся развитие
        if not changes:
            changes.append("Продолжается углубление и развитие в рамках текущих энергий")
        
        return changes[:5]  # Ограничиваем 5 ключевыми изменениями

    def _identify_basic_key_changes(self, progressed_planets: Dict[str, Any]) -> List[str]:
        """Определяет базовые ключевые изменения."""
        return [
            "Постепенное развитие личности через опыт",
            "Эволюция эмоциональных паттернов",
            "Углубление понимания жизненных уроков"
        ]

    def _get_planet_sphere(self, planet: str) -> str:
        """Получает сферу влияния планеты."""
        spheres = {
            "sun": "самовыражения и жизненной цели",
            "moon": "эмоций и внутреннего мира",
            "mercury": "мышления и коммуникации",
            "venus": "отношений и ценностей",
            "mars": "действий и энергии",
            "jupiter": "роста и возможностей",
            "saturn": "структуры и ответственности"
        }
        return spheres.get(planet, "жизненных процессов")

    def _identify_general_trends(self, progressed_planets: Dict[str, Any], age: int) -> List[str]:
        """Определяет общие тенденции развития."""
        trends = []
        
        # Анализируем прогрессированное Солнце
        sun_sign = progressed_planets.get("sun", {}).get("sign", "")
        if sun_sign:
            trends.append(f"Развитие через энергию {sun_sign}")
        
        # Анализируем прогрессированную Луну
        moon_sign = progressed_planets.get("moon", {}).get("sign", "")
        if moon_sign:
            trends.append(f"Эмоциональная настройка на {moon_sign}")
        
        # Возрастные тенденции
        if 28 <= age <= 30:
            trends.append("Важный возрастной переход - время ответственности")
        elif 40 <= age <= 42:
            trends.append("Кризис среднего возраста - переоценка ценностей")
        elif 58 <= age <= 60:
            trends.append("Второй сатурнианский возврат - мудрость и наставничество")
        
        return trends[:4]

    # Solar Return methods

    def _find_exact_solar_return_time(
        self,
        birth_datetime: datetime,
        year: int,
        coordinates: Dict[str, float]
    ) -> datetime:
        """Находит точное время соляра."""
        # Простое приближение - используем день рождения в указанном году
        # В реальной астрологии нужен точный расчет момента возвращения Солнца
        
        approximate_date = datetime(year, birth_datetime.month, birth_datetime.day, birth_datetime.hour, birth_datetime.minute)
        
        # Можно добавить более точный расчет через итерацию
        return approximate_date

    def _interpret_solar_return(
        self,
        solar_positions: Dict[str, Any],
        solar_houses: Dict[int, Any],
        year: int
    ) -> Dict[str, Any]:
        """Интерпретирует соляр."""
        # Анализируем асцендент соляра
        ascendant = solar_houses.get(1, {})
        asc_sign = ascendant.get("sign", "Овен")
        
        # Анализируем Солнце в доме
        sun_house = self._find_planet_house(solar_positions.get("Sun", {}), solar_houses)
        
        # Анализируем Луну в доме
        moon_house = self._find_planet_house(solar_positions.get("Moon", {}), solar_houses)
        
        return {
            "year_theme": self._get_solar_year_theme(asc_sign, sun_house),
            "emotional_focus": self._get_emotional_focus(moon_house),
            "key_areas": self._get_solar_key_areas(solar_positions, solar_houses),
            "challenges": self._identify_solar_challenges(solar_positions),
            "opportunities": self._identify_solar_opportunities(solar_positions),
            "overall_energy": self._assess_solar_energy(solar_positions)
        }

    def _get_solar_year_theme(self, asc_sign: str, sun_house: Optional[int]) -> str:
        """Определяет тему года по асценденту и позиции Солнца."""
        base_themes = {
            "Овен": "Год новых начинаний и лидерства",
            "Телец": "Год стабилизации и материального роста", 
            "Близнецы": "Год обучения и коммуникации",
            "Рак": "Год семьи и эмоционального развития",
            "Лев": "Год творчества и самовыражения",
            "Дева": "Год совершенствования и служения",
            "Весы": "Год отношений и гармонии",
            "Скорпион": "Год трансформации и обновления",
            "Стрелец": "Год расширения горизонтов",
            "Козерог": "Год достижений и структуры",
            "Водолей": "Год инноваций и свободы",
            "Рыбы": "Год духовного развития"
        }
        
        base_theme = base_themes.get(asc_sign, "Год личностного роста")
        
        # Модифицируем в зависимости от дома Солнца
        if sun_house:
            house_focus = {
                1: " с фокусом на личности",
                2: " с фокусом на финансах",
                3: " с фокусом на общении",
                4: " с фокусом на доме и семье",
                5: " с фокусом на творчестве",
                6: " с фокусом на работе и здоровье",
                7: " с фокусом на партнерстве",
                8: " с фокусом на трансформации",
                9: " с фокусом на образовании",
                10: " с фокусом на карьере",
                11: " с фокусом на дружбе и целях",
                12: " с фокусом на духовности"
            }
            base_theme += house_focus.get(sun_house, "")
        
        return base_theme

    def _find_planet_house(self, planet_data: Dict[str, Any], houses: Dict[int, Any]) -> Optional[int]:
        """Находит дом планеты."""
        if not planet_data or not houses:
            return None
        
        planet_longitude = planet_data.get("longitude", 0)
        
        for house_num in range(1, 13):
            house_data = houses.get(house_num, {})
            house_start = house_data.get("cusp_longitude", (house_num - 1) * 30)
            
            next_house = house_num + 1 if house_num < 12 else 1
            next_house_data = houses.get(next_house, {})
            house_end = next_house_data.get("cusp_longitude", house_num * 30)
            
            # Учитываем переход через 0°
            if house_start > house_end:  # Переход через 0°
                if planet_longitude >= house_start or planet_longitude < house_end:
                    return house_num
            else:
                if house_start <= planet_longitude < house_end:
                    return house_num
        
        return 1  # По умолчанию первый дом

    # Lunar Return methods

    def _find_new_moon_date(self, year: int, month: int) -> datetime:
        """Находит дату новолуния в месяце."""
        # Простое приближение - средина месяца
        # В реальной астрологии нужен точный расчет лунных фаз
        
        try:
            new_moon_date = datetime(year, month, 15, 12, 0)  # 15 число в полдень
        except ValueError:
            # Если месяц некорректный, используем январь
            new_moon_date = datetime(year, 1, 15, 12, 0)
        
        return new_moon_date

    def _interpret_lunar_return(
        self,
        lunar_positions: Dict[str, Any],
        lunar_houses: Dict[int, Any],
        month: int
    ) -> Dict[str, Any]:
        """Интерпретирует лунар."""
        moon_data = lunar_positions.get("Moon", {})
        sun_data = lunar_positions.get("Sun", {})
        
        moon_sign = moon_data.get("sign", "Рак")
        sun_sign = sun_data.get("sign", "Лев")
        
        moon_house = self._find_planet_house(moon_data, lunar_houses)
        sun_house = self._find_planet_house(sun_data, lunar_houses)
        
        return {
            "emotional_theme": f"Эмоциональный фокус месяца связан с энергией {moon_sign}",
            "action_theme": f"Активность направлена через энергию {sun_sign}",
            "emotional_house_focus": self._get_house_meaning(moon_house) if moon_house else "общие эмоции",
            "action_house_focus": self._get_house_meaning(sun_house) if sun_house else "общая активность",
            "monthly_advice": self._get_lunar_advice(moon_sign, sun_sign),
            "energy_pattern": self._assess_lunar_energy(lunar_positions)
        }

    def _get_house_meaning(self, house_num: Optional[int]) -> str:
        """Получает значение дома."""
        if not house_num:
            return "неопределенная сфера"
        
        house_meanings = {
            1: "личность и самовыражение",
            2: "финансы и ценности", 
            3: "общение и обучение",
            4: "дом и семья",
            5: "творчество и романтика",
            6: "здоровье и работа",
            7: "партнерство и отношения",
            8: "трансформация и общие ресурсы",
            9: "философия и путешествия",
            10: "карьера и репутация",
            11: "дружба и цели",
            12: "духовность и подсознание"
        }
        
        return house_meanings.get(house_num, f"дом {house_num}")

    # Additional helper methods

    def _get_solar_themes(self, positions: Dict[str, Any], houses: Dict[int, Any]) -> List[str]:
        """Получает темы соляра."""
        themes = []
        
        # Анализируем позицию Солнца
        sun_house = self._find_planet_house(positions.get("Sun", {}), houses)
        if sun_house:
            themes.append(f"Фокус на {self._get_house_meaning(sun_house)}")
        
        # Анализируем стеллиумы (скопления планет)
        house_counts = {}
        for planet, planet_data in positions.items():
            house = self._find_planet_house(planet_data, houses)
            if house:
                house_counts[house] = house_counts.get(house, 0) + 1
        
        # Находим дома с 3+ планетами
        for house, count in house_counts.items():
            if count >= 3:
                themes.append(f"Стеллиум в {self._get_house_meaning(house)}")
        
        return themes[:4]

    def _get_monthly_highlights(self, positions: Dict[str, Any]) -> Dict[int, str]:
        """Получает ключевые моменты по месяцам."""
        # Базовые рекомендации по месяцам на основе солярных данных
        highlights = {}
        
        sun_sign = positions.get("Sun", {}).get("sign", "")
        
        if sun_sign == "Овен":  # Если соляр в Овне
            highlights.update({
                4: "Пик энергии и новые начинания",
                7: "Интенсивная активность", 
                10: "Завершение проектов"
            })
        
        # Можно добавить более сложную логику
        return highlights

    def _get_seasonal_guidance(self, positions: Dict[str, Any]) -> Dict[str, str]:
        """Получает сезонные рекомендации."""
        return {
            "весна": "Время новых начинаний и активности",
            "лето": "Пик творческой энергии",
            "осень": "Сбор урожая и подведение итогов",
            "зима": "Внутренняя работа и планирование"
        }

    def _identify_success_indicators(
        self,
        positions: Dict[str, Any],
        houses: Dict[int, Any]
    ) -> List[str]:
        """Определяет индикаторы успеха."""
        indicators = []
        
        # Анализируем Юпитер (удача и расширение)
        jupiter = positions.get("Jupiter", {})
        if jupiter:
            jupiter_house = self._find_planet_house(jupiter, houses)
            if jupiter_house:
                indicators.append(f"Удача в сфере {self._get_house_meaning(jupiter_house)}")
        
        # Анализируем Венеру (гармония и привлекательность)
        venus = positions.get("Venus", {})
        if venus:
            venus_house = self._find_planet_house(venus, houses)
            if venus_house in [2, 5, 7, 8]:  # Благоприятные дома для Венеры
                indicators.append(f"Гармония в {self._get_house_meaning(venus_house)}")
        
        return indicators[:3]

    def _identify_caution_periods(self, positions: Dict[str, Any]) -> List[str]:
        """Определяет периоды осторожности."""
        cautions = []
        
        # Анализируем Сатурн (ограничения)
        saturn = positions.get("Saturn", {})
        if saturn and saturn.get("retrograde", False):
            cautions.append("Осторожность с долгосрочными обязательствами")
        
        # Анализируем Марс (конфликты)
        mars = positions.get("Mars", {})
        if mars and mars.get("retrograde", False):
            cautions.append("Избегайте импульсивных действий")
        
        return cautions[:2]

    def _analyze_life_phase(self, days_progressed: int) -> str:
        """Анализирует жизненную фазу."""
        age = days_progressed // 365
        
        phases = {
            (0, 28): "Формирование и поиск своего пути",
            (28, 56): "Реализация и достижение целей",
            (56, 84): "Мудрость и передача опыта"
        }
        
        for (start, end), phase in phases.items():
            if start <= age < end:
                return phase
        
        return "Особый жизненный период"

    def _assess_spiritual_evolution(self, progressed_planets: Dict[str, Any]) -> str:
        """Оценивает духовную эволюцию."""
        # Анализируем прогрессированные планеты для духовных выводов
        spiritual_signs = ["Рыбы", "Стрелец", "Скорпион", "Водолей"]
        
        spiritual_count = 0
        for planet_data in progressed_planets.values():
            if planet_data.get("sign", "") in spiritual_signs:
                spiritual_count += 1
        
        if spiritual_count >= 3:
            return "Период интенсивного духовного развития"
        elif spiritual_count >= 1:
            return "Возрастающий интерес к духовности"
        else:
            return "Фокус на материальном развитии"

    def _get_emotional_focus(self, moon_house: Optional[int]) -> str:
        """Получает эмоциональный фокус года."""
        if not moon_house:
            return "Общее эмоциональное развитие"
        
        return f"Эмоциональная энергия направлена на {self._get_house_meaning(moon_house)}"

    def _get_solar_key_areas(
        self,
        positions: Dict[str, Any],
        houses: Dict[int, Any]
    ) -> List[str]:
        """Получает ключевые области соляра."""
        key_areas = []
        
        # Анализируем личные планеты в домах
        personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
        
        house_emphasis = {}
        for planet in personal_planets:
            planet_data = positions.get(planet, {})
            house = self._find_planet_house(planet_data, houses)
            if house:
                house_emphasis[house] = house_emphasis.get(house, 0) + 1
        
        # Находим наиболее акцентированные дома
        emphasized_houses = sorted(house_emphasis.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for house, count in emphasized_houses:
            key_areas.append(self._get_house_meaning(house))
        
        return key_areas

    def _identify_solar_challenges(self, positions: Dict[str, Any]) -> List[str]:
        """Определяет вызовы соляра."""
        challenges = []
        
        # Ретроградные планеты создают задержки
        for planet, data in positions.items():
            if data.get("retrograde", False) and planet in ["Mercury", "Venus", "Mars"]:
                challenges.append(f"Задержки и пересмотр в сфере {planet.lower()}")
        
        return challenges[:2]

    def _identify_solar_opportunities(self, positions: Dict[str, Any]) -> List[str]:
        """Определяет возможности соляра."""
        opportunities = []
        
        # Сильные планеты в собственных знаках
        dignities = {
            "Sun": ["Лев"], "Moon": ["Рак"], "Mercury": ["Близнецы", "Дева"],
            "Venus": ["Телец", "Весы"], "Mars": ["Овен", "Скорпион"],
            "Jupiter": ["Стрелец", "Рыбы"], "Saturn": ["Козерог", "Водолей"]
        }
        
        for planet, signs in dignities.items():
            planet_data = positions.get(planet, {})
            if planet_data.get("sign", "") in signs:
                opportunities.append(f"Сильная поддержка в сфере {planet.lower()}")
        
        return opportunities[:3]

    def _assess_solar_energy(self, positions: Dict[str, Any]) -> str:
        """Оценивает энергию соляра."""
        fire_signs = ["Овен", "Лев", "Стрелец"]
        air_signs = ["Близнецы", "Весы", "Водолей"]
        
        fire_count = sum(1 for data in positions.values() 
                        if data.get("sign", "") in fire_signs)
        air_count = sum(1 for data in positions.values() 
                       if data.get("sign", "") in air_signs)
        
        active_count = fire_count + air_count
        
        if active_count >= 6:
            return "Высокоэнергетичный год с активными периодами"
        elif active_count >= 3:
            return "Сбалансированная энергия с периодами активности"
        else:
            return "Спокойный год для внутренней работы"

    def _get_lunar_advice(self, moon_sign: str, sun_sign: str) -> str:
        """Получает совет для лунара."""
        advice_combinations = {
            ("Рак", "Лев"): "Сочетайте эмоциональную чуткость с творческим самовыражением",
            ("Скорпион", "Стрелец"): "Глубокие трансформации откроют новые горизонты",
            ("Рыбы", "Овен"): "Интуиция поможет в принятии решительных действий"
        }
        
        return advice_combinations.get(
            (moon_sign, sun_sign),
            f"Гармонизируйте эмоции {moon_sign} с активностью {sun_sign}"
        )

    def _assess_lunar_energy(self, positions: Dict[str, Any]) -> str:
        """Оценивает энергию лунара."""
        moon_data = positions.get("Moon", {})
        moon_sign = moon_data.get("sign", "")
        
        water_signs = ["Рак", "Скорпион", "Рыбы"]
        earth_signs = ["Телец", "Дева", "Козерог"]
        
        if moon_sign in water_signs:
            return "Интуитивная и эмоциональная энергия месяца"
        elif moon_sign in earth_signs:
            return "Практическая и стабильная энергия месяца"
        else:
            return "Динамичная энергия с переменами"

    def _get_lunar_themes(self, positions: Dict[str, Any]) -> List[str]:
        """Получает темы лунара."""
        themes = []
        
        moon_sign = positions.get("Moon", {}).get("sign", "")
        if moon_sign:
            themes.append(f"Эмоциональная настройка на {moon_sign}")
        
        # Добавляем общие лунные темы
        themes.extend([
            "Внимание к эмоциональным потребностям",
            "Работа с интуицией и подсознанием",
            "Забота о себе и близких"
        ])
        
        return themes[:4]

    def _get_weekly_rhythms(self, positions: Dict[str, Any]) -> Dict[int, str]:
        """Получает недельные ритмы."""
        return {
            1: "Новые эмоциональные впечатления",
            2: "Развитие начатого",
            3: "Кульминация месячной энергии",
            4: "Завершение и подготовка к новому циклу"
        }

    def _get_emotional_guidance(self, positions: Dict[str, Any]) -> List[str]:
        """Получает эмоциональные рекомендации."""
        moon_sign = positions.get("Moon", {}).get("sign", "")
        
        guidance_by_sign = {
            "Овен": ["Следуйте импульсам", "Не подавляйте эмоции"],
            "Телец": ["Ищите стабильность", "Наслаждайтесь простыми удовольствиями"],
            "Близнецы": ["Общайтесь с разными людьми", "Изучайте новое"],
            "Рак": ["Заботьтесь о семье", "Доверяйте интуиции"],
            "Лев": ["Выражайте творчество", "Принимайте внимание"],
            "Дева": ["Наводите порядок", "Заботьтесь о здоровье"],
            "Весы": ["Ищите гармонию", "Развивайте отношения"],
            "Скорпион": ["Исследуйте глубины", "Трансформируйтесь"],
            "Стрелец": ["Расширяйте горизонты", "Следуйте вдохновению"],
            "Козерог": ["Планируйте будущее", "Берите ответственность"],
            "Водолей": ["Будьте собой", "Помогайте другим"],
            "Рыбы": ["Медитируйте", "Развивайте сострадание"]
        }
        
        return guidance_by_sign.get(moon_sign, ["Следуйте сердцу", "Доверяйте процессу"])

    def _get_optimal_lunar_timing(self, positions: Dict[str, Any]) -> Dict[str, str]:
        """Получает оптимальные тайминги для лунара."""
        return {
            "новые_начинания": "Первая неделя месяца",
            "творческие_проекты": "Вторая неделя",
            "завершения": "Третья неделя", 
            "планирование": "Четвертая неделя"
        }