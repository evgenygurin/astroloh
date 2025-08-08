"""
Сервис расчета астрологических транзитов и их влияния на натальную карту.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pytz

from app.services.astrology_calculator import AstrologyCalculator


class TransitCalculator:
    """Калькулятор транзитов и их влияний."""

    def __init__(self):
        self.astro_calc = AstrologyCalculator()
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
