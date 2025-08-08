"""
Сервис расчета астрологических транзитов и их влияния на натальную карту.
Теперь интегрирован с Enhanced Transit Service и Progression Service для полной функциональности.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pytz

from app.services.astrology_calculator import AstrologyCalculator
from app.services.enhanced_transit_service import TransitService
from app.services.progression_service import ProgressionService


class TransitCalculator:
    """Калькулятор транзитов и их влияний."""

    def __init__(self):
        self.astro_calc = AstrologyCalculator()
        self.transit_service = TransitService()
        self.progression_service = ProgressionService()
        self.logger = logging.getLogger(__name__)

        # Орбы влияния для транзитных аспектов
        self.transit_orbs = {
            0: 8,  # Соединение
            60: 6,  # Секстиль
            90: 8,  # Квадрат
            120: 8,  # Трин
            180: 8,  # Оппозиция
        }

        # Скорости планет (градусов в день) для прогнозирования
        self.planet_speeds = {
            "Sun": 1.0,
            "Moon": 13.2,
            "Mercury": 1.4,
            "Venus": 1.2,
            "Mars": 0.5,
            "Jupiter": 0.083,
            "Saturn": 0.033,
            "Uranus": 0.011,
            "Neptune": 0.006,
            "Pluto": 0.004,
        }

        # Описания транзитных влияний
        self.transit_influences = {
            ("Sun", "Sun"): "Время обновления жизненной энергии и целей",
            ("Sun", "Moon"): "Гармония между сознанием и эмоциями",
            ("Sun", "Mercury"): "Активизация интеллекта и коммуникации",
            ("Sun", "Venus"): "Период любви, красоты и творчества",
            ("Sun", "Mars"): "Мощный заряд энергии и инициативы",
            ("Jupiter", "Sun"): "Удачный период для роста и экспансии",
            ("Saturn", "Sun"): "Время дисциплины и структурирования",
            ("Uranus", "Sun"): "Неожиданные изменения и освобождение",
            ("Neptune", "Sun"): "Духовные озарения и вдохновение",
            ("Pluto", "Sun"): "Глубокая трансформация личности",
        }

    def calculate_current_transits(
        self,
        natal_planets: Dict[str, Dict[str, Any]],
        transit_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Вычисляет текущие транзиты к натальной карте."""

        if transit_date is None:
            transit_date = datetime.now(pytz.UTC)

        # Получаем текущие позиции планет
        current_positions = self.astro_calc.calculate_planet_positions(
            transit_date
        )

        # Находим активные транзитные аспекты
        active_transits = []
        approaching_transits = []

        for transit_planet, transit_data in current_positions.items():
            for natal_planet, natal_data in natal_planets.items():
                # Вычисляем аспекты между транзитной и натальной планетой
                aspects = self._calculate_transit_aspects(
                    transit_data, natal_data, transit_planet, natal_planet
                )

                for aspect in aspects:
                    if aspect["orb"] <= self.transit_orbs.get(
                        aspect["angle"], 8
                    ):
                        if aspect["orb"] <= 2:  # Точные аспекты
                            active_transits.append(aspect)
                        else:  # Приближающиеся аспекты
                            approaching_transits.append(aspect)

        # Сортируем по орбу (сначала самые точные)
        active_transits.sort(key=lambda x: x["orb"])
        approaching_transits.sort(key=lambda x: x["orb"])

        return {
            "date": transit_date.isoformat(),
            "active_transits": active_transits[:10],  # Топ-10 активных
            "approaching_transits": approaching_transits[
                :5
            ],  # Топ-5 приближающихся
            "summary": self._create_transit_summary(active_transits),
            "daily_influences": self._get_daily_influences(active_transits),
        }

    def _calculate_transit_aspects(
        self,
        transit_data: Dict[str, Any],
        natal_data: Dict[str, Any],
        transit_planet: str,
        natal_planet: str,
    ) -> List[Dict[str, Any]]:
        """Вычисляет аспекты между транзитной и натальной планетой."""

        aspects = []
        transit_longitude = transit_data["longitude"]
        natal_longitude = natal_data["longitude"]

        # Вычисляем угол между планетами
        angle = abs(transit_longitude - natal_longitude)
        if angle > 180:
            angle = 360 - angle

        # Проверяем основные аспекты
        for aspect_angle, orb in self.transit_orbs.items():
            if abs(angle - aspect_angle) <= orb:
                aspect_name = self._get_aspect_name(aspect_angle)

                # Определяем точность аспекта
                exactness = abs(angle - aspect_angle)

                # Получаем влияние этого транзита
                influence = self._get_transit_influence(
                    transit_planet, natal_planet, aspect_name
                )

                aspects.append(
                    {
                        "transit_planet": transit_planet,
                        "natal_planet": natal_planet,
                        "aspect": aspect_name,
                        "angle": aspect_angle,
                        "orb": exactness,
                        "exact_angle": angle,
                        "influence": influence,
                        "strength": self._calculate_aspect_strength(
                            exactness, aspect_angle
                        ),
                        "nature": self._get_aspect_nature(aspect_name),
                    }
                )

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

    def _get_aspect_nature(self, aspect_name: str) -> str:
        """Возвращает природу аспекта."""
        natures = {
            "Соединение": "усиление",
            "Секстиль": "гармония",
            "Трин": "поток",
            "Квадрат": "напряжение",
            "Оппозиция": "противостояние",
        }
        return natures.get(aspect_name, "нейтральный")

    def _calculate_aspect_strength(
        self, orb: float, aspect_angle: float
    ) -> str:
        """Вычисляет силу аспекта."""
        if orb <= 1:
            return "очень сильный"
        elif orb <= 3:
            return "сильный"
        elif orb <= 5:
            return "умеренный"
        else:
            return "слабый"

    def _get_transit_influence(
        self, transit_planet: str, natal_planet: str, aspect: str
    ) -> str:
        """Получает описание влияния транзита."""

        # Пробуем прямое сочетание
        influence = self.transit_influences.get((transit_planet, natal_planet))
        if influence:
            return influence

        # Общие влияния по транзитным планетам
        general_influences = {
            "Jupiter": "Расширение и удача в делах",
            "Saturn": "Ограничения и необходимость дисциплины",
            "Uranus": "Неожиданные изменения и освобождение",
            "Neptune": "Духовность и иллюзии",
            "Pluto": "Трансформация и обновление",
            "Mars": "Энергия и действие",
            "Venus": "Любовь и гармония",
            "Mercury": "Коммуникация и мышление",
            "Sun": "Самовыражение и жизненная сила",
            "Moon": "Эмоции и интуиция",
        }

        base_influence = general_influences.get(
            transit_planet, "Влияние на жизненные процессы"
        )

        # Модифицируем в зависимости от аспекта
        if aspect in ["Квадрат", "Оппозиция"]:
            return f"Вызов: {base_influence.lower()}"
        elif aspect in ["Трин", "Секстиль"]:
            return f"Возможность: {base_influence.lower()}"
        else:
            return base_influence

    def _create_transit_summary(
        self, active_transits: List[Dict[str, Any]]
    ) -> str:
        """Создает краткое резюме транзитов."""

        if not active_transits:
            return "Спокойный период без значительных транзитных влияний"

        # Анализируем доминирующие влияния
        strong_transits = [
            t
            for t in active_transits
            if t["strength"] in ["сильный", "очень сильный"]
        ]

        if not strong_transits:
            return "Период слабых транзитных влияний, время для спокойного развития"

        # Группируем по природе аспектов
        harmonious = [
            t for t in strong_transits if t["nature"] in ["гармония", "поток"]
        ]
        challenging = [
            t
            for t in strong_transits
            if t["nature"] in ["напряжение", "противостояние"]
        ]

        if len(harmonious) > len(challenging):
            return "Благоприятный период для роста и новых возможностей"
        elif len(challenging) > len(harmonious):
            return "Период вызовов и испытаний, требующий внимательности"
        else:
            return "Сбалансированный период с возможностями и вызовами"

    def _get_daily_influences(
        self, active_transits: List[Dict[str, Any]]
    ) -> List[str]:
        """Получает ключевые влияния дня."""

        influences = []

        # Берем только самые сильные транзиты
        strong_transits = [
            t
            for t in active_transits
            if t["strength"] in ["сильный", "очень сильный"]
        ][:3]

        for transit in strong_transits:
            influence_text = f"{transit['transit_planet']} {transit['aspect']} {transit['natal_planet']}: {transit['influence']}"
            influences.append(influence_text)

        return influences

    def calculate_solar_return(
        self,
        birth_date: date,
        year: int,
        birth_place: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Вычисляет соляр (годовую карту) на день рождения."""

        if birth_place is None:
            birth_place = {"latitude": 55.7558, "longitude": 37.6176}  # Москва

        # Находим точное время соляра (когда Солнце возвращается в натальную позицию)
        natal_datetime = datetime.combine(birth_date, datetime.min.time())
        self.astro_calc.calculate_planet_positions(natal_datetime)["Sun"][
            "longitude"
        ]

        # Приблизительная дата соляра
        solar_date = date(year, birth_date.month, birth_date.day)
        solar_datetime = datetime.combine(solar_date, datetime.min.time())

        # Рассчитываем позиции планет на соляр
        solar_positions = self.astro_calc.calculate_planet_positions(
            solar_datetime, birth_place["latitude"], birth_place["longitude"]
        )

        # Рассчитываем дома для соляра
        solar_houses = self.astro_calc.calculate_houses(
            solar_datetime, birth_place["latitude"], birth_place["longitude"]
        )

        # Интерпретируем соляр
        interpretation = self._interpret_solar_return(
            solar_positions, solar_houses
        )

        return {
            "year": year,
            "date": solar_date.isoformat(),
            "planets": solar_positions,
            "houses": solar_houses,
            "interpretation": interpretation,
            "themes": self._get_solar_themes(solar_positions, solar_houses),
        }

    def _interpret_solar_return(
        self,
        positions: Dict[str, Dict[str, Any]],
        houses: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Интерпретирует соляр."""

        # Анализируем асцендент соляра
        ascendant = houses.get("ascendant", {})
        asc_sign = ascendant.get("sign", "Овен")

        # Анализируем акцентированные дома
        planet_house_distribution = self._analyze_house_emphasis(
            positions, houses
        )

        return {
            "year_theme": self._get_year_theme(asc_sign),
            "key_areas": self._get_key_life_areas(planet_house_distribution),
            "challenges": self._identify_solar_challenges(positions),
            "opportunities": self._identify_solar_opportunities(positions),
        }

    def _get_year_theme(self, ascendant_sign: str) -> str:
        """Определяет тему года по асценденту соляра."""

        themes = {
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
            "Рыбы": "Год духовного развития",
        }

        return themes.get(ascendant_sign, "Год личностного роста")

    def _analyze_house_emphasis(
        self,
        positions: Dict[str, Dict[str, Any]],
        houses: Dict[int, Dict[str, Any]],
    ) -> Dict[int, int]:
        """Анализирует распределение планет по домам."""

        house_count = {}

        for planet, planet_data in positions.items():
            planet_longitude = planet_data["longitude"]

            # Определяем, в каком доме находится планета
            for house_num in range(1, 13):
                house_start = houses.get(house_num, {}).get(
                    "cusp_longitude", (house_num - 1) * 30
                )
                house_end = houses.get(house_num % 12 + 1, {}).get(
                    "cusp_longitude", house_num * 30
                )

                if house_start <= planet_longitude < house_end:
                    house_count[house_num] = house_count.get(house_num, 0) + 1
                    break

        return house_count

    def _get_key_life_areas(
        self, house_distribution: Dict[int, int]
    ) -> List[str]:
        """Определяет ключевые сферы жизни года."""

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
            12: "духовность и подсознание",
        }

        # Находим наиболее акцентированные дома
        emphasized_houses = sorted(
            house_distribution.items(), key=lambda x: x[1], reverse=True
        )[:3]

        key_areas = []
        for house_num, count in emphasized_houses:
            if count > 0:
                area = house_meanings.get(house_num, f"дом {house_num}")
                key_areas.append(area)

        return key_areas

    def _identify_solar_challenges(
        self, positions: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Определяет вызовы года."""

        challenges = []

        # Анализируем напряженные аспекты в соляре
        aspects = self.astro_calc.calculate_aspects(positions)

        for aspect in aspects:
            if (
                aspect["aspect"] in ["Квадрат", "Оппозиция"]
                and aspect["orb"] <= 5
            ):
                challenge = f"Напряжение между {aspect['planet1']} и {aspect['planet2']}"
                challenges.append(challenge)

        return challenges[:3]  # Ограничиваем тремя основными

    def _identify_solar_opportunities(
        self, positions: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Определяет возможности года."""

        opportunities = []

        # Анализируем гармоничные аспекты в соляре
        aspects = self.astro_calc.calculate_aspects(positions)

        for aspect in aspects:
            if aspect["aspect"] in ["Трин", "Секстиль"] and aspect["orb"] <= 5:
                opportunity = (
                    f"Гармония между {aspect['planet1']} и {aspect['planet2']}"
                )
                opportunities.append(opportunity)

        return opportunities[:3]  # Ограничиваем тремя основными

    def _get_solar_themes(
        self,
        positions: Dict[str, Dict[str, Any]],
        houses: Dict[int, Dict[str, Any]],
    ) -> List[str]:
        """Получает основные темы года."""

        themes = []

        # Анализируем позицию Солнца в доме
        sun_longitude = positions.get("Sun", {}).get("longitude", 0)

        for house_num in range(1, 13):
            house_start = houses.get(house_num, {}).get(
                "cusp_longitude", (house_num - 1) * 30
            )
            house_end = houses.get(house_num % 12 + 1, {}).get(
                "cusp_longitude", house_num * 30
            )

            if house_start <= sun_longitude < house_end:
                house_themes = {
                    1: "Фокус на личном развитии",
                    2: "Внимание к финансам и ресурсам",
                    3: "Активная коммуникация",
                    4: "Семейные дела в приоритете",
                    5: "Творческое самовыражение",
                    6: "Здоровье и ежедневная рутина",
                    7: "Отношения и партнерство",
                    8: "Трансформации и изменения",
                    9: "Расширение мировоззрения",
                    10: "Карьерные достижения",
                    11: "Социальные связи и цели",
                    12: "Spiritual introspection и внутренняя работа",
                }

                theme = house_themes.get(
                    house_num, f"Влияние {house_num}-го дома"
                )
                themes.append(theme)
                break

        return themes

    def calculate_lunar_return(
        self,
        birth_date: date,
        target_month: int,
        target_year: int,
        birth_place: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Вычисляет лунар (месячную карту) на новолуние."""

        if birth_place is None:
            birth_place = {"latitude": 55.7558, "longitude": 37.6176}

        # Находим новолуние в указанном месяце
        new_moon_date = self._find_new_moon(target_year, target_month)

        if not new_moon_date:
            # Fallback к середине месяца
            new_moon_date = datetime(target_year, target_month, 15)

        # Рассчитываем позиции планет на лунар
        lunar_positions = self.astro_calc.calculate_planet_positions(
            new_moon_date, birth_place["latitude"], birth_place["longitude"]
        )

        # Рассчитываем дома для лунара
        lunar_houses = self.astro_calc.calculate_houses(
            new_moon_date, birth_place["latitude"], birth_place["longitude"]
        )

        return {
            "month": target_month,
            "year": target_year,
            "new_moon_date": new_moon_date.isoformat(),
            "planets": lunar_positions,
            "houses": lunar_houses,
            "interpretation": self._interpret_lunar_return(lunar_positions),
            "monthly_themes": self._get_monthly_themes(lunar_positions),
        }

    def _find_new_moon(self, year: int, month: int) -> Optional[datetime]:
        """Находит дату новолуния в указанном месяце."""

        # Простое приближение - используем лунный цикл ~29.5 дней
        # В реальной астрологии нужны точные эфемериды

        try:
            # Проверяем середину месяца
            test_date = datetime(year, month, 15)
            moon_phase = self.astro_calc.calculate_moon_phase(test_date)

            # Если фаза близка к новолунию (0-30 градусов)
            if moon_phase["angle"] <= 30 or moon_phase["angle"] >= 330:
                return test_date

            # Иначе возвращаем приблизительную дату
            return datetime(year, month, 1)

        except Exception:
            return None

    def _interpret_lunar_return(
        self, positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """Интерпретирует лунар."""

        moon_sign = positions.get("Moon", {}).get("sign", "Рак")
        sun_sign = positions.get("Sun", {}).get("sign", "Лев")

        return {
            "emotional_theme": f"Эмоциональный фокус месяца связан с энергией {moon_sign}",
            "action_theme": f"Активность месяца направлена через энергию {sun_sign}",
            "general_advice": "Следуйте лунным ритмам для гармоничного развития",
        }

    def _get_monthly_themes(
        self, positions: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Получает темы месяца."""

        themes = []

        # Анализируем основные планеты
        moon_sign = positions.get("Moon", {}).get("sign", "Рак")
        positions.get("Mercury", {}).get("sign", "Близнецы")

        moon_themes = {
            "Овен": "Эмоциональная активность и инициатива",
            "Телец": "Стабильность и комфорт",
            "Близнецы": "Любознательность и общение",
            "Рак": "Забота и семейные дела",
            "Лев": "Творчество и самовыражение",
            "Дева": "Организация и детали",
            "Весы": "Гармония в отношениях",
            "Скорпион": "Глубокие эмоциональные процессы",
            "Стрелец": "Стремление к новому",
            "Козерог": "Практичность и цели",
            "Водолей": "Независимость и инновации",
            "Рыбы": "Интуиция и сострадание",
        }

        theme = moon_themes.get(moon_sign, "Эмоциональное развитие")
        themes.append(theme)

        return themes

    # Enhanced methods using new services

    def get_enhanced_current_transits(
        self,
        natal_chart: Dict[str, Any],
        transit_date: Optional[datetime] = None,
        include_minor_aspects: bool = True
    ) -> Dict[str, Any]:
        """
        Получает расширенные текущие транзиты через Enhanced Transit Service.
        
        Args:
            natal_chart: Данные натальной карты
            transit_date: Дата для расчета транзитов
            include_minor_aspects: Включать минорные аспекты
        """
        self.logger.info("TRANSIT_CALCULATOR_ENHANCED_CURRENT: Using enhanced transit service")
        
        # Используем новый Enhanced Transit Service для профессионального анализа
        enhanced_result = self.transit_service.get_current_transits(
            natal_chart, 
            transit_date, 
            include_minor_aspects
        )
        
        # Если Enhanced service недоступен, используем базовый метод
        if enhanced_result.get("source") == "basic" or not enhanced_result:
            self.logger.warning("TRANSIT_CALCULATOR_ENHANCED_FALLBACK: Using legacy method")
            natal_planets = natal_chart.get("planets", {})
            return self.calculate_current_transits(natal_planets, transit_date)
        
        return enhanced_result

    def get_period_forecast(
        self,
        natal_chart: Dict[str, Any],
        days: int = 7,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Получает прогноз транзитов на период через Enhanced Transit Service.
        
        Args:
            natal_chart: Данные натальной карты
            days: Количество дней для прогноза
            start_date: Начальная дата
        """
        self.logger.info(f"TRANSIT_CALCULATOR_PERIOD_FORECAST: {days} days forecast")
        
        return self.transit_service.get_period_forecast(natal_chart, days, start_date)

    def get_important_transits(
        self,
        natal_chart: Dict[str, Any],
        lookback_days: int = 30,
        lookahead_days: int = 90
    ) -> Dict[str, Any]:
        """
        Получает важные транзиты в расширенном периоде.
        
        Args:
            natal_chart: Данные натальной карты
            lookback_days: Дни назад для анализа
            lookahead_days: Дни вперед для прогноза
        """
        self.logger.info("TRANSIT_CALCULATOR_IMPORTANT: Analyzing major transits")
        
        return self.transit_service.get_important_transits(
            natal_chart, 
            lookback_days, 
            lookahead_days
        )

    def get_secondary_progressions(
        self,
        natal_chart: Dict[str, Any],
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Вычисляет вторичные прогрессии через Progression Service.
        
        Args:
            natal_chart: Данные натальной карты
            target_date: Дата для расчета прогрессий
        """
        self.logger.info("TRANSIT_CALCULATOR_PROGRESSIONS: Calculating secondary progressions")
        
        return self.progression_service.get_secondary_progressions(natal_chart, target_date)

    def get_enhanced_solar_return(
        self,
        natal_chart: Dict[str, Any],
        year: int,
        location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Вычисляет расширенный соляр через Progression Service.
        
        Args:
            natal_chart: Данные натальной карты
            year: Год соляра
            location: Место для расчета
        """
        self.logger.info(f"TRANSIT_CALCULATOR_SOLAR_RETURN_ENHANCED: {year}")
        
        # Используем новый Progression Service для расширенного анализа
        enhanced_result = self.progression_service.get_solar_return(natal_chart, year, location)
        
        # Дополняем базовыми данными если нужно
        if not enhanced_result:
            birth_date = datetime.fromisoformat(natal_chart.get("birth_datetime", "2000-01-01T12:00:00")).date()
            return self.calculate_solar_return(birth_date, year, location)
        
        return enhanced_result

    def get_enhanced_lunar_return(
        self,
        natal_chart: Dict[str, Any],
        month: int,
        year: int,
        location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Вычисляет расширенный лунар через Progression Service.
        
        Args:
            natal_chart: Данные натальной карты
            month: Месяц лунара
            year: Год лунара
            location: Место для расчета
        """
        self.logger.info(f"TRANSIT_CALCULATOR_LUNAR_RETURN_ENHANCED: {month}/{year}")
        
        # Используем новый Progression Service
        enhanced_result = self.progression_service.get_lunar_return(natal_chart, month, year, location)
        
        # Дополняем базовыми данными если нужно
        if not enhanced_result:
            birth_date = datetime.fromisoformat(natal_chart.get("birth_datetime", "2000-01-01T12:00:00")).date()
            return self.calculate_lunar_return(birth_date, month, year, location)
        
        return enhanced_result

    def get_comprehensive_transit_analysis(
        self,
        natal_chart: Dict[str, Any],
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Получает комплексный анализ транзитов и прогрессий.
        
        Args:
            natal_chart: Данные натальной карты
            analysis_period_days: Период анализа в днях
        """
        self.logger.info("TRANSIT_CALCULATOR_COMPREHENSIVE: Full transit analysis")
        
        current_date = datetime.now(pytz.UTC)
        current_year = current_date.year
        current_month = current_date.month
        
        # Получаем все виды анализа
        current_transits = self.get_enhanced_current_transits(natal_chart)
        period_forecast = self.get_period_forecast(natal_chart, analysis_period_days)
        important_transits = self.get_important_transits(natal_chart)
        progressions = self.get_secondary_progressions(natal_chart)
        solar_return = self.get_enhanced_solar_return(natal_chart, current_year)
        lunar_return = self.get_enhanced_lunar_return(natal_chart, current_month, current_year)
        
        # Создаем комплексный анализ
        comprehensive_analysis = {
            "analysis_date": current_date.isoformat(),
            "analysis_period": f"{analysis_period_days} дней",
            
            # Основные компоненты
            "current_transits": current_transits,
            "period_forecast": period_forecast,
            "important_transits": important_transits,
            "progressions": progressions,
            "solar_return": solar_return,
            "lunar_return": lunar_return,
            
            # Интегрированные выводы
            "integrated_themes": self._extract_integrated_themes(
                current_transits, period_forecast, important_transits, progressions
            ),
            "life_phase_analysis": self._analyze_current_life_phase(progressions, solar_return),
            "timing_recommendations": self._create_timing_recommendations(
                current_transits, period_forecast, important_transits
            ),
            "spiritual_guidance": self._create_spiritual_guidance(
                progressions, important_transits, solar_return
            ),
            
            # Сводка
            "executive_summary": self._create_executive_summary(
                current_transits, period_forecast, important_transits, progressions
            )
        }
        
        self.logger.info("TRANSIT_CALCULATOR_COMPREHENSIVE_SUCCESS: Analysis complete")
        return comprehensive_analysis

    def is_enhanced_features_available(self) -> Dict[str, bool]:
        """Проверяет доступность расширенных функций."""
        return {
            "kerykeion_transits": self.transit_service.is_available(),
            "kerykeion_progressions": self.progression_service.is_available(),
            "enhanced_analysis": True,
            "comprehensive_forecasts": True
        }

    # Helper methods for comprehensive analysis

    def _extract_integrated_themes(
        self,
        current_transits: Dict[str, Any],
        period_forecast: Dict[str, Any],
        important_transits: Dict[str, Any],
        progressions: Dict[str, Any]
    ) -> List[str]:
        """Извлекает интегрированные темы из всех видов анализа."""
        themes = set()
        
        # Темы из текущих транзитов
        for influence in current_transits.get("daily_influences", []):
            theme = self._extract_theme_from_text(influence)
            if theme:
                themes.add(theme)
        
        # Темы из прогноза периода
        for theme in period_forecast.get("overall_themes", []):
            themes.add(theme)
        
        # Темы из важных транзитов
        for theme in important_transits.get("life_themes", []):
            themes.add(theme)
        
        # Темы из прогрессий
        interpretation = progressions.get("interpretation", {})
        if isinstance(interpretation, dict):
            for trend in interpretation.get("general_trends", []):
                theme = self._extract_theme_from_text(trend)
                if theme:
                    themes.add(theme)
        
        return list(themes)[:5]  # Ограничиваем топ-5 темами

    def _analyze_current_life_phase(
        self,
        progressions: Dict[str, Any],
        solar_return: Dict[str, Any]
    ) -> Dict[str, str]:
        """Анализирует текущую жизненную фазу."""
        interpretation = progressions.get("interpretation", {})
        
        if isinstance(interpretation, dict):
            life_stage = interpretation.get("life_stage", "Переходный период")
            current_age = interpretation.get("current_age", 0)
        else:
            life_stage = "Переходный период"
            current_age = 0
        
        solar_theme = solar_return.get("interpretation", {}).get("year_theme", "Год развития")
        
        return {
            "life_stage": life_stage,
            "current_age": str(current_age),
            "year_focus": solar_theme,
            "development_phase": self._determine_development_phase(current_age),
            "key_lessons": self._get_age_appropriate_lessons(current_age)
        }

    def _create_timing_recommendations(
        self,
        current_transits: Dict[str, Any],
        period_forecast: Dict[str, Any],
        important_transits: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Создает рекомендации по таймингу действий."""
        recommendations = []
        
        # Из текущих транзитов
        timing_recs = current_transits.get("timing_recommendations", [])
        for rec in timing_recs[:2]:
            recommendations.append({
                "period": "сейчас",
                "recommendation": rec,
                "source": "current_transits"
            })
        
        # Из важных дат периода
        important_dates = period_forecast.get("important_dates", [])
        for date_info in important_dates[:2]:
            recommendations.append({
                "period": date_info.get("date", ""),
                "recommendation": f"Обратите внимание: {date_info.get('significance', '')}",
                "source": "period_forecast"
            })
        
        # Из подготовки к важным транзитам
        prep_advice = important_transits.get("preparation_advice", [])
        for advice in prep_advice[:1]:
            recommendations.append({
                "period": "долгосрочно",
                "recommendation": advice,
                "source": "important_transits"
            })
        
        return recommendations[:5]

    def _create_spiritual_guidance(
        self,
        progressions: Dict[str, Any],
        important_transits: Dict[str, Any],
        solar_return: Dict[str, Any]
    ) -> str:
        """Создает духовное руководство."""
        spiritual_messages = []
        
        # Из прогрессий
        spiritual_evolution = progressions.get("spiritual_evolution")
        if spiritual_evolution:
            spiritual_messages.append(spiritual_evolution)
        
        # Из важных транзитов
        spiritual_guidance = important_transits.get("spiritual_guidance")
        if spiritual_guidance:
            spiritual_messages.append(spiritual_guidance)
        
        # Базовое сообщение
        if not spiritual_messages:
            spiritual_messages.append("Каждый момент жизни несет возможности для роста и развития сознания")
        
        return " ".join(spiritual_messages[:2])

    def _create_executive_summary(
        self,
        current_transits: Dict[str, Any],
        period_forecast: Dict[str, Any],
        important_transits: Dict[str, Any],
        progressions: Dict[str, Any]
    ) -> str:
        """Создает исполнительное резюме анализа."""
        summary_parts = []
        
        # Текущее состояние
        current_summary = current_transits.get("summary", "")
        if current_summary:
            summary_parts.append(f"Сейчас: {current_summary}")
        
        # Период
        period_summary = period_forecast.get("period_summary", "")
        if period_summary:
            summary_parts.append(f"Период: {period_summary}")
        
        # Долгосрочно
        if important_transits.get("important_transits"):
            summary_parts.append("Долгосрочно ожидаются значительные астрологические влияния")
        
        # Прогрессии
        interpretation = progressions.get("interpretation", {})
        if isinstance(interpretation, dict):
            life_stage = interpretation.get("life_stage", "")
            if life_stage:
                summary_parts.append(f"Жизненная фаза: {life_stage}")
        
        if not summary_parts:
            return "Период стабильного развития с возможностями для личностного роста"
        
        return ". ".join(summary_parts[:3]) + "."

    def _extract_theme_from_text(self, text: str) -> Optional[str]:
        """Извлекает тему из текста."""
        if not text:
            return None
        
        text_lower = text.lower()
        theme_keywords = {
            "отношения": ["любовь", "отношения", "партнер", "брак", "семья"],
            "карьера": ["работа", "карьера", "деньги", "успех", "достижения", "бизнес"],
            "здоровье": ["здоровье", "энергия", "силы", "восстановление", "лечение"],
            "творчество": ["творчество", "искусство", "вдохновение", "создание", "творческий"],
            "духовность": ["духовность", "медитация", "развитие", "мудрость", "сознание"],
            "обучение": ["обучение", "знания", "изучение", "понимание", "образование"],
            "трансформация": ["трансформация", "изменения", "обновление", "перемены"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return theme
        
        return None

    def _determine_development_phase(self, age: int) -> str:
        """Определяет фазу развития по возрасту."""
        if age < 29:
            return "Формирование и поиск идентичности"
        elif age < 42:
            return "Активная реализация и достижения"
        elif age < 58:
            return "Мастерство и наставничество"
        else:
            return "Мудрость и духовное развитие"

    def _get_age_appropriate_lessons(self, age: int) -> str:
        """Получает уроки, соответствующие возрасту."""
        if age < 21:
            return "Самопознание и формирование ценностей"
        elif age < 29:
            return "Принятие ответственности и независимость"
        elif age < 42:
            return "Баланс между амбициями и отношениями"
        elif age < 58:
            return "Передача опыта и развитие мудрости"
        else:
            return "Принятие жизненного пути и духовное созревание"
