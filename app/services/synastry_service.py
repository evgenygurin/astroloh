"""
Сервис синастрии и анализа совместимости на базе Kerykeion.
Полноценная система анализа отношений между двумя картами рождения.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.yandex_models import YandexZodiacSign
from app.services.astrology_calculator import AstrologyCalculator, NatalChart
from app.services.kerykeion_service import KerykeionService

logger = logging.getLogger(__name__)


class PartnerData:
    """Данные партнера для синастрии"""

    def __init__(
        self,
        name: str,
        birth_date: datetime,
        birth_time: Optional[datetime] = None,
        birth_place: Optional[str] = None,
        zodiac_sign: Optional[YandexZodiacSign] = None,
    ):
        self.name = name
        self.birth_date = birth_date
        self.birth_time = birth_time
        self.birth_place = birth_place
        self.zodiac_sign = zodiac_sign


class SynastryResult:
    """Результат анализа синастрии"""

    def __init__(self):
        self.aspects: List[Dict[str, Any]] = []
        self.compatibility_score: float = 0.0
        self.element_compatibility: Dict[str, Any] = {}
        self.quality_compatibility: Dict[str, Any] = {}
        self.house_overlays: Dict[str, List[str]] = {}
        self.composite_midpoints: Dict[str, float] = {}
        self.relationship_highlights: List[str] = []
        self.challenges: List[str] = []
        self.strengths: List[str] = []
        self.advice: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aspects": self.aspects,
            "compatibility_score": self.compatibility_score,
            "element_compatibility": self.element_compatibility,
            "quality_compatibility": self.quality_compatibility,
            "house_overlays": self.house_overlays,
            "composite_midpoints": self.composite_midpoints,
            "relationship_highlights": self.relationship_highlights,
            "challenges": self.challenges,
            "strengths": self.strengths,
            "advice": self.advice,
        }


class SynastryService:
    """Сервис для расчета синастрии и анализа совместимости"""

    def __init__(self, astrology_calculator: AstrologyCalculator):
        self.calculator = astrology_calculator
        self.kerykeion_service = KerykeionService()
        logger.info("SYNASTRY_SERVICE_INIT: Synastry service initialized")
        logger.info(f"SYNASTRY_SERVICE_KERYKEION: Available = {self.kerykeion_service.is_available()}")

    async def calculate_synastry(
        self,
        person1: PartnerData,
        person2: PartnerData,
        orb_factor: float = 1.2,
    ) -> SynastryResult:
        """
        Вычисляет полную синастрию между двумя партнерами

        Args:
            person1: Данные первого партнера
            person2: Данные второго партнера
            orb_factor: Коэффициент орбиса для аспектов

        Returns:
            SynastryResult с полным анализом совместимости
        """
        logger.info(
            f"SYNASTRY_CALCULATE_START: Analyzing compatibility between {person1.name} and {person2.name}"
        )

        try:
            # Создаем натальные карты для обоих партнеров
            chart1 = await self._create_natal_chart(person1)
            chart2 = await self._create_natal_chart(person2)

            if not chart1 or not chart2:
                logger.warning(
                    "SYNASTRY_CHART_CREATION_FAILED: Cannot create natal charts"
                )
                return self._create_basic_compatibility_result(
                    person1, person2
                )

            # Используем существующий метод расчета синастрии
            synastry_data = self.calculator.calculate_synastry(
                chart1, chart2, orb_factor
            )

            # Создаем детализированный результат
            result = SynastryResult()
            result.aspects = synastry_data.get("aspects", [])
            result.compatibility_score = synastry_data.get(
                "compatibility_score", 0
            )
            result.element_compatibility = synastry_data.get(
                "element_compatibility", {}
            )
            result.quality_compatibility = synastry_data.get(
                "quality_compatibility", {}
            )
            result.house_overlays = synastry_data.get("house_overlays", {})
            result.composite_midpoints = synastry_data.get(
                "composite_midpoints", {}
            )

            # Анализируем аспекты и создаем интерпретации
            await self._analyze_aspects(result)
            await self._analyze_compatibility_patterns(
                result, person1, person2
            )
            await self._generate_relationship_advice(result, person1, person2)

            logger.info(
                f"SYNASTRY_CALCULATE_SUCCESS: Generated synastry with {len(result.aspects)} aspects, compatibility score: {result.compatibility_score:.1f}%"
            )

            return result

        except Exception as e:
            logger.error(
                f"SYNASTRY_CALCULATE_ERROR: Failed to calculate synastry: {e}"
            )
            return self._create_basic_compatibility_result(person1, person2)

    async def calculate_advanced_synastry(
        self,
        person1: PartnerData,
        person2: PartnerData,
        latitude1: float = 55.7558,
        longitude1: float = 37.6176,
        latitude2: float = 55.7558,
        longitude2: float = 37.6176,
        timezone1: str = "Europe/Moscow",
        timezone2: str = "Europe/Moscow",
    ) -> Dict[str, Any]:
        """
        Расширенная синастрия с использованием Kerykeion
        """
        logger.info(f"SYNASTRY_ADVANCED_START: {person1.name} + {person2.name}")

        try:
            if not self.kerykeion_service.is_available():
                logger.warning("SYNASTRY_ADVANCED: Fallback to basic calculator")
                basic = await self.calculate_synastry(person1, person2)
                return {
                    "partner1": {"name": person1.name},
                    "partner2": {"name": person2.name},
                    "compatibility": {
                        "overall_score": basic.compatibility_score,
                        "element_compatibility": basic.element_compatibility,
                        "quality_compatibility": basic.quality_compatibility,
                        "aspects": basic.aspects,
                        "strengths": basic.strengths,
                        "challenges": basic.challenges,
                        "advice": basic.advice,
                        "highlights": basic.relationship_highlights,
                    },
                    "house_overlays": basic.house_overlays or {},
                    "composite_chart": {"midpoints": basic.composite_midpoints or {}},
                    "karmic_connections": {"connections": [], "strength": "unknown"},
                    "interpretation": self._generate_synastry_interpretation({
                        "overall_score": basic.compatibility_score
                    }),
                    "service_info": {
                        "method": "Basic Calculator Fallback",
                        "timestamp": datetime.now().isoformat(),
                    },
                }

            # Создаем полные натальные карты через Kerykeion
            birth_time1 = person1.birth_time or person1.birth_date.replace(hour=12, minute=0)
            birth_time2 = person2.birth_time or person2.birth_date.replace(hour=12, minute=0)

            chart1_data = self.kerykeion_service.get_full_natal_chart_data(
                person1.name, birth_time1, latitude1, longitude1, timezone1
            )
            
            chart2_data = self.kerykeion_service.get_full_natal_chart_data(
                person2.name, birth_time2, latitude2, longitude2, timezone2
            )

            if "error" in chart1_data or "error" in chart2_data:
                logger.error("SYNASTRY_ADVANCED_CHART_ERROR: Failed to create charts")
                return {"error": "Failed to create natal charts"}

            # Используем Kerykeion для детального анализа совместимости
            detailed_compatibility = self.kerykeion_service.calculate_compatibility_detailed(
                chart1_data, chart2_data
            )

            if "error" in detailed_compatibility:
                logger.error("SYNASTRY_ADVANCED_COMPATIBILITY_ERROR")
                return detailed_compatibility

            # Анализируем дома и их перекрытия
            house_overlays = self._analyze_house_overlays(
                chart1_data.get("houses", {}),
                chart2_data.get("houses", {}),
                chart1_data.get("planets", {}),
                chart2_data.get("planets", {})
            )

            # Создаем композитную карту (точки середин)
            composite_chart = self._calculate_composite_midpoints(
                chart1_data.get("planets", {}),
                chart2_data.get("planets", {})
            )

            # Анализируем кармические связи (Лунные узлы)
            karmic_connections = self._analyze_karmic_connections(
                chart1_data.get("planets", {}),
                chart2_data.get("planets", {})
            )

            # Создаем полный результат
            result = {
                "partner1": {
                    "name": person1.name,
                    "chart_data": chart1_data
                },
                "partner2": {
                    "name": person2.name, 
                    "chart_data": chart2_data
                },
                "compatibility": detailed_compatibility,
                "house_overlays": house_overlays,
                "composite_chart": composite_chart,
                "karmic_connections": karmic_connections,
                "interpretation": self._generate_synastry_interpretation(detailed_compatibility),
                "service_info": {
                    "method": "Kerykeion Advanced",
                    "timestamp": datetime.now().isoformat()
                }
            }

            logger.info(f"SYNASTRY_ADVANCED_SUCCESS: Generated advanced synastry for {person1.name} + {person2.name}")
            return result

        except Exception as e:
            logger.error(f"SYNASTRY_ADVANCED_ERROR: {e}")
            return {"error": f"Advanced synastry calculation failed: {str(e)}"}

    def _analyze_house_overlays(
        self,
        houses1: Dict[int, Any],
        houses2: Dict[int, Any], 
        planets1: Dict[str, Any],
        planets2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Анализ наложений домов в синастрии"""
        overlays = {}
        
        try:
            # Анализируем, в какие дома партнера 2 попадают планеты партнера 1
            for planet_name, planet_data in planets1.items():
                planet_longitude = planet_data.get("longitude", 0)
                
                # Находим дом, в который попадает планета
                house_number = self._find_house_for_longitude(planet_longitude, houses2)
                
                if house_number:
                    if house_number not in overlays:
                        overlays[house_number] = {"planets": [], "meanings": []}
                    
                    overlays[house_number]["planets"].append({
                        "planet": planet_name,
                        "owner": "partner1",
                        "longitude": planet_longitude
                    })

            # То же самое для планет партнера 2 в домах партнера 1
            for planet_name, planet_data in planets2.items():
                planet_longitude = planet_data.get("longitude", 0)
                house_number = self._find_house_for_longitude(planet_longitude, houses1)
                
                if house_number:
                    if house_number not in overlays:
                        overlays[house_number] = {"planets": [], "meanings": []}
                        
                    overlays[house_number]["planets"].append({
                        "planet": planet_name,
                        "owner": "partner2", 
                        "longitude": planet_longitude
                    })

            # Добавляем интерпретации наложений домов
            for house_num, overlay_data in overlays.items():
                overlay_data["meanings"] = self._get_house_overlay_meanings(house_num, overlay_data["planets"])

            return overlays
            
        except Exception as e:
            logger.error(f"SYNASTRY_HOUSE_OVERLAYS_ERROR: {e}")
            return {}

    def _find_house_for_longitude(self, longitude: float, houses: Dict[int, Any]) -> Optional[int]:
        """Находит номер дома для заданной долготы"""
        for house_num in range(1, 13):
            if house_num in houses:
                house_start = houses[house_num].get("cusp_longitude", 0)
                next_house = house_num + 1 if house_num < 12 else 1
                house_end = houses.get(next_house, {}).get("cusp_longitude", 0)
                
                # Обработка перехода через 0 градусов
                if house_end < house_start:
                    house_end += 360
                    if longitude < house_start:
                        longitude += 360
                
                if house_start <= longitude < house_end:
                    return house_num
        
        return None

    def _calculate_composite_midpoints(
        self, planets1: Dict[str, Any], planets2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Вычисляет композитную карту (точки середин)"""
        composite = {}
        
        try:
            for planet in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
                if planet in planets1 and planet in planets2:
                    long1 = planets1[planet].get("longitude", 0)
                    long2 = planets2[planet].get("longitude", 0)
                    
                    # Вычисляем точку середины
                    midpoint = self._calculate_midpoint(long1, long2)
                    
                    composite[planet] = {
                        "longitude": midpoint,
                        "sign": self._get_sign_from_longitude(midpoint),
                        "degree_in_sign": midpoint % 30,
                        "partner1_longitude": long1,
                        "partner2_longitude": long2
                    }
                    
            return composite
            
        except Exception as e:
            logger.error(f"SYNASTRY_COMPOSITE_ERROR: {e}")
            return {}

    def _calculate_midpoint(self, long1: float, long2: float) -> float:
        """Вычисляет точку середины между двумя долготами"""
        # Определяем кратчайший путь
        diff = abs(long2 - long1)
        
        if diff <= 180:
            # Прямой путь
            return ((long1 + long2) / 2) % 360
        else:
            # Путь через 0 градусов
            return ((long1 + long2 + 360) / 2) % 360

    def _analyze_karmic_connections(
        self, planets1: Dict[str, Any], planets2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Анализ кармических связей через Лунные узлы"""
        karmic = {"connections": [], "strength": "weak"}
        
        try:
            # Получаем позиции Лунных узлов
            node1 = planets1.get("mean_node", {}).get("longitude")
            node2 = planets2.get("mean_node", {}).get("longitude")
            
            if not node1 or not node2:
                return karmic
                
            # Анализируем аспекты между узлами и планетами
            karmic_planets = ["sun", "moon", "venus", "mars", "jupiter", "saturn"]
            
            for planet_name in karmic_planets:
                planet1 = planets1.get(planet_name, {}).get("longitude")
                planet2 = planets2.get(planet_name, {}).get("longitude")
                
                if planet1 is not None:
                    # Планета партнера 1 к узлу партнера 2
                    aspect = self._calculate_aspect_between_points(planet1, node2)
                    if aspect:
                        karmic["connections"].append({
                            "connection": f"{planet_name}1 - Node2",
                            "aspect": aspect,
                            "interpretation": f"Кармическая связь через {planet_name}"
                        })
                        
                if planet2 is not None:
                    # Планета партнера 2 к узлу партнера 1  
                    aspect = self._calculate_aspect_between_points(planet2, node1)
                    if aspect:
                        karmic["connections"].append({
                            "connection": f"{planet_name}2 - Node1", 
                            "aspect": aspect,
                            "interpretation": f"Кармическая связь через {planet_name}"
                        })

            # Оцениваем силу кармических связей
            if len(karmic["connections"]) >= 3:
                karmic["strength"] = "strong"
            elif len(karmic["connections"]) >= 1:
                karmic["strength"] = "moderate"
                
            return karmic
            
        except Exception as e:
            logger.error(f"SYNASTRY_KARMIC_ERROR: {e}")
            return {"connections": [], "strength": "weak"}

    def _calculate_aspect_between_points(self, long1: float, long2: float) -> Optional[str]:
        """Вычисляет аспект между двумя точками"""
        angle = abs(long1 - long2)
        if angle > 180:
            angle = 360 - angle

        aspects = {
            0: ("Conjunction", 8),
            60: ("Sextile", 6), 
            90: ("Square", 8),
            120: ("Trine", 8),
            180: ("Opposition", 8)
        }
        
        for aspect_angle, (aspect_name, orb) in aspects.items():
            if abs(angle - aspect_angle) <= orb:
                return aspect_name
                
        return None

    def _get_sign_from_longitude(self, longitude: float) -> str:
        """Получить знак зодиака по долготе"""
        signs = [
            "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
            "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
        ]
        return signs[int(longitude / 30) % 12]

    def _get_house_overlay_meanings(self, house_num: int, planets: List[Dict]) -> List[str]:
        """Получить значения наложений домов"""
        house_meanings = {
            1: "Влияние на личность и внешний вид",
            2: "Влияние на финансы и ценности", 
            3: "Влияние на общение и ближайшее окружение",
            4: "Влияние на дом и семью",
            5: "Влияние на творчество и романтику",
            6: "Влияние на здоровье и повседневную жизнь",
            7: "Влияние на партнерство и открытых врагов",
            8: "Влияние на интимность и трансформацию",
            9: "Влияние на философию и дальние путешествия",
            10: "Влияние на карьеру и репутацию",
            11: "Влияние на дружбу и надежды",
            12: "Влияние на подсознание и скрытые процессы"
        }
        
        base_meaning = house_meanings.get(house_num, "Неизвестное влияние")
        return [base_meaning]

    def _generate_synastry_interpretation(self, compatibility_data: Dict[str, Any]) -> Dict[str, str]:
        """Генерирует интерпретацию синастрии"""
        score = compatibility_data.get("overall_score", 0)
        
        if score >= 80:
            level = "Исключительная совместимость"
            description = "Очень гармоничные отношения с глубоким пониманием"
        elif score >= 65:
            level = "Хорошая совместимость"
            description = "Благоприятные отношения с хорошими перспективами"
        elif score >= 50:
            level = "Средняя совместимость"
            description = "Отношения требуют работы и компромиссов"
        elif score >= 35:
            level = "Слабая совместимость"
            description = "Сложные отношения с многими проблемами"
        else:
            level = "Низкая совместимость"
            description = "Очень трудные отношения, много конфликтов"
            
        return {
            "level": level,
            "description": description,
            "score": score
        }

    async def _create_natal_chart(
        self, person: PartnerData
    ) -> Optional[NatalChart]:
        """Создает натальную карту для партнера"""
        try:
            # Используем время рождения или полдень по умолчанию
            birth_time = person.birth_time or person.birth_date.replace(
                hour=12, minute=0
            )

            # Координаты Москвы по умолчанию
            latitude = 55.7558
            longitude = 37.6176

            chart = self.calculator.create_natal_chart(
                name=person.name,
                birth_datetime=birth_time,
                latitude=latitude,
                longitude=longitude,
            )

            logger.debug(
                f"SYNASTRY_CHART_CREATED: Created chart for {person.name}"
            )
            return chart

        except Exception as e:
            logger.error(
                f"SYNASTRY_CHART_ERROR: Failed to create chart for {person.name}: {e}"
            )
            return None

    def _create_basic_compatibility_result(
        self, person1: PartnerData, person2: PartnerData
    ) -> SynastryResult:
        """Создает базовый результат совместимости по знакам зодиака"""
        logger.info(
            "SYNASTRY_BASIC_COMPATIBILITY: Falling back to basic zodiac compatibility"
        )

        result = SynastryResult()

        # Используем знаки зодиака для базовой совместимости
        if person1.zodiac_sign and person2.zodiac_sign:
            compatibility_data = self.calculator.calculate_compatibility_score(
                person1.zodiac_sign, person2.zodiac_sign
            )

            result.compatibility_score = compatibility_data.get(
                "total_score", 0
            )
            result.element_compatibility = compatibility_data.get(
                "element_compatibility", {}
            )
            result.relationship_highlights = [
                compatibility_data.get(
                    "description", "Совместимость определена по знакам зодиака"
                )
            ]

        return result

    async def _analyze_aspects(self, result: SynastryResult):
        """Анализирует аспекты и создает интерпретации"""
        harmonious_aspects = []
        challenging_aspects = []

        aspect_scores = {
            "Соединение": 8,
            "Трин": 9,
            "Секстиль": 6,
            "Оппозиция": -5,
            "Квадрат": -8,
            "Квинконс": -3,
        }

        for aspect in result.aspects:
            aspect_name = aspect.get("aspect", "")
            planet1 = (
                aspect.get("planet1", "").split("_")[-1]
                if "_" in aspect.get("planet1", "")
                else aspect.get("planet1", "")
            )
            planet2 = (
                aspect.get("planet2", "").split("_")[-1]
                if "_" in aspect.get("planet2", "")
                else aspect.get("planet2", "")
            )

            score = aspect_scores.get(aspect_name, 0)

            if score > 0:
                harmonious_aspects.append(
                    f"{planet1} {aspect.get('aspect_symbol', '')} {planet2}"
                )
            elif score < 0:
                challenging_aspects.append(
                    f"{planet1} {aspect.get('aspect_symbol', '')} {planet2}"
                )

        if harmonious_aspects:
            result.strengths.append(
                f"Гармоничные аспекты: {', '.join(harmonious_aspects[:3])}"
            )

        if challenging_aspects:
            result.challenges.append(
                f"Напряженные аспекты: {', '.join(challenging_aspects[:3])}"
            )

    async def _analyze_compatibility_patterns(
        self,
        result: SynastryResult,
        person1: PartnerData,
        person2: PartnerData,
    ):
        """Анализирует паттерны совместимости"""

        # Анализ совместимости по элементам
        element_scores = result.element_compatibility
        best_element = (
            max(element_scores.items(), key=lambda x: x[1])
            if element_scores
            else None
        )

        if best_element and best_element[1] > 70:
            result.relationship_highlights.append(
                f"Отличная совместимость в сфере {best_element[0].lower()}"
            )

        # Анализ общего счета совместимости
        if result.compatibility_score >= 80:
            result.relationship_highlights.append(
                "Исключительно высокая совместимость"
            )
        elif result.compatibility_score >= 60:
            result.relationship_highlights.append(
                "Хорошая совместимость с потенциалом роста"
            )
        elif result.compatibility_score >= 40:
            result.relationship_highlights.append(
                "Средняя совместимость, требует работы над отношениями"
            )
        else:
            result.challenges.append(
                "Низкая базовая совместимость, много различий"
            )

    async def _generate_relationship_advice(
        self,
        result: SynastryResult,
        person1: PartnerData,
        person2: PartnerData,
    ):
        """Генерирует советы для отношений"""

        # Общие советы на основе совместимости
        if result.compatibility_score >= 70:
            result.advice.extend(
                [
                    "Поддерживайте открытое общение",
                    "Развивайте совместные интересы",
                    "Цените различия друг друга",
                ]
            )
        elif result.compatibility_score >= 40:
            result.advice.extend(
                [
                    "Работайте над пониманием различий",
                    "Ищите компромиссы в спорных вопросах",
                    "Уделяйте время развитию отношений",
                ]
            )
        else:
            result.advice.extend(
                [
                    "Требуется терпение и взаимопонимание",
                    "Фокусируйтесь на общих целях",
                    "Рассмотрите помощь специалиста по отношениям",
                ]
            )

    async def calculate_composite_chart(
        self, person1: PartnerData, person2: PartnerData
    ) -> Optional[Dict[str, Any]]:
        """
        Вычисляет композитную карту отношений

        Returns:
            Словарь с данными композитной карты или None при ошибке
        """
        logger.info(
            f"SYNASTRY_COMPOSITE_START: Creating composite chart for {person1.name} and {person2.name}"
        )

        try:
            chart1 = await self._create_natal_chart(person1)
            chart2 = await self._create_natal_chart(person2)

            if not chart1 or not chart2:
                return None

            # Вычисляем средние точки планет
            composite_planets = {}

            for planet_name in chart1.planets.keys():
                if planet_name in chart2.planets:
                    lon1 = chart1.planets[planet_name].get("longitude", 0)
                    lon2 = chart2.planets[planet_name].get("longitude", 0)

                    # Вычисляем средние точки с учетом зодиакального круга
                    diff = abs(lon1 - lon2)
                    if diff > 180:
                        # Берем короткий путь через 0/360 градусов
                        if lon1 > lon2:
                            midpoint = ((lon1 + lon2 + 360) / 2) % 360
                        else:
                            midpoint = ((lon1 + lon2 + 360) / 2) % 360
                    else:
                        midpoint = (lon1 + lon2) / 2

                    composite_planets[planet_name] = {
                        "longitude": midpoint,
                        "sign": self.calculator._get_sign_from_longitude(
                            midpoint
                        ).name_ru,
                        "degree_in_sign": midpoint % 30,
                    }

            logger.info(
                f"SYNASTRY_COMPOSITE_SUCCESS: Created composite chart with {len(composite_planets)} planets"
            )

            return {
                "planets": composite_planets,
                "relationship_theme": "Композитная карта показывает энергию отношений как единого целого",
            }

        except Exception as e:
            logger.error(
                f"SYNASTRY_COMPOSITE_ERROR: Failed to create composite chart: {e}"
            )
            return None

    def get_synastry_interpretation(
        self, aspect_name: str, planet1: str, planet2: str
    ) -> str:
        """
        Возвращает интерпретацию конкретного аспекта в синастрии

        Args:
            aspect_name: Название аспекта
            planet1: Первая планета
            planet2: Вторая планета

        Returns:
            Текстовая интерпретация аспекта
        """

        interpretations = {
            (
                "Sun",
                "Moon",
                "Соединение",
            ): "Прекрасное взаимопонимание на эмоциональном уровне",
            (
                "Sun",
                "Moon",
                "Трин",
            ): "Гармоничное сочетание мужской и женской энергий",
            (
                "Sun",
                "Moon",
                "Оппозиция",
            ): "Притягивающие противоположности, нужен баланс",
            (
                "Venus",
                "Mars",
                "Соединение",
            ): "Сильное физическое и эмоциональное притяжение",
            (
                "Venus",
                "Mars",
                "Трин",
            ): "Естественная гармония в романтических отношениях",
            (
                "Venus",
                "Mars",
                "Квадрат",
            ): "Страстные, но временами конфликтные отношения",
            (
                "Mercury",
                "Mercury",
                "Соединение",
            ): "Отличное интеллектуальное понимание",
            ("Mercury", "Venus", "Трин"): "Красивое и гармоничное общение",
            ("Mercury", "Mars", "Квадрат"): "Споры и разногласия в общении",
        }

        key = (planet1, planet2, aspect_name)
        reverse_key = (planet2, planet1, aspect_name)

        return (
            interpretations.get(key)
            or interpretations.get(reverse_key)
            or f"{planet1} и {planet2} в аспекте {aspect_name}"
        )
