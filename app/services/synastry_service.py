"""
Сервис синастрии и анализа совместимости на базе Kerykeion.
Полноценная система анализа отношений между двумя картами рождения.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.yandex_models import UserContext, YandexZodiacSign
from app.services.astrology_calculator import AstrologyCalculator, NatalChart

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


class SynastryService:
    """Сервис для расчета синастрии и анализа совместимости"""

    def __init__(self, astrology_calculator: AstrologyCalculator):
        self.calculator = astrology_calculator
        logger.info("SYNASTRY_SERVICE_INIT: Synastry service initialized")

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
                logger.warning("SYNASTRY_CHART_CREATION_FAILED: Cannot create natal charts")
                return self._create_basic_compatibility_result(person1, person2)

            # Используем существующий метод расчета синастрии
            synastry_data = self.calculator.calculate_synastry(chart1, chart2, orb_factor)

            # Создаем детализированный результат
            result = SynastryResult()
            result.aspects = synastry_data.get("aspects", [])
            result.compatibility_score = synastry_data.get("compatibility_score", 0)
            result.element_compatibility = synastry_data.get("element_compatibility", {})
            result.quality_compatibility = synastry_data.get("quality_compatibility", {})
            result.house_overlays = synastry_data.get("house_overlays", {})
            result.composite_midpoints = synastry_data.get("composite_midpoints", {})

            # Анализируем аспекты и создаем интерпретации
            await self._analyze_aspects(result)
            await self._analyze_compatibility_patterns(result, person1, person2)
            await self._generate_relationship_advice(result, person1, person2)

            logger.info(
                f"SYNASTRY_CALCULATE_SUCCESS: Generated synastry with {len(result.aspects)} aspects, compatibility score: {result.compatibility_score:.1f}%"
            )

            return result

        except Exception as e:
            logger.error(f"SYNASTRY_CALCULATE_ERROR: Failed to calculate synastry: {e}")
            return self._create_basic_compatibility_result(person1, person2)

    async def _create_natal_chart(self, person: PartnerData) -> Optional[NatalChart]:
        """Создает натальную карту для партнера"""
        try:
            # Используем время рождения или полдень по умолчанию
            birth_time = person.birth_time or person.birth_date.replace(hour=12, minute=0)
            
            # Координаты Москвы по умолчанию
            latitude = 55.7558
            longitude = 37.6176

            chart = self.calculator.create_natal_chart(
                name=person.name,
                birth_datetime=birth_time,
                latitude=latitude,
                longitude=longitude,
            )
            
            logger.debug(f"SYNASTRY_CHART_CREATED: Created chart for {person.name}")
            return chart

        except Exception as e:
            logger.error(f"SYNASTRY_CHART_ERROR: Failed to create chart for {person.name}: {e}")
            return None

    def _create_basic_compatibility_result(
        self, person1: PartnerData, person2: PartnerData
    ) -> SynastryResult:
        """Создает базовый результат совместимости по знакам зодиака"""
        logger.info("SYNASTRY_BASIC_COMPATIBILITY: Falling back to basic zodiac compatibility")
        
        result = SynastryResult()
        
        # Используем знаки зодиака для базовой совместимости
        if person1.zodiac_sign and person2.zodiac_sign:
            compatibility_data = self.calculator.calculate_compatibility_score(
                person1.zodiac_sign, person2.zodiac_sign
            )
            
            result.compatibility_score = compatibility_data.get("total_score", 0)
            result.element_compatibility = compatibility_data.get("element_compatibility", {})
            result.relationship_highlights = [
                compatibility_data.get("description", "Совместимость определена по знакам зодиака")
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
            planet1 = aspect.get("planet1", "").split("_")[-1] if "_" in aspect.get("planet1", "") else aspect.get("planet1", "")
            planet2 = aspect.get("planet2", "").split("_")[-1] if "_" in aspect.get("planet2", "") else aspect.get("planet2", "")
            
            score = aspect_scores.get(aspect_name, 0)
            
            if score > 0:
                harmonious_aspects.append(f"{planet1} {aspect.get('aspect_symbol', '')} {planet2}")
            elif score < 0:
                challenging_aspects.append(f"{planet1} {aspect.get('aspect_symbol', '')} {planet2}")
        
        if harmonious_aspects:
            result.strengths.append(f"Гармоничные аспекты: {', '.join(harmonious_aspects[:3])}")
        
        if challenging_aspects:
            result.challenges.append(f"Напряженные аспекты: {', '.join(challenging_aspects[:3])}")

    async def _analyze_compatibility_patterns(
        self, result: SynastryResult, person1: PartnerData, person2: PartnerData
    ):
        """Анализирует паттерны совместимости"""
        
        # Анализ совместимости по элементам
        element_scores = result.element_compatibility
        best_element = max(element_scores.items(), key=lambda x: x[1]) if element_scores else None
        
        if best_element and best_element[1] > 70:
            result.relationship_highlights.append(
                f"Отличная совместимость в сфере {best_element[0].lower()}"
            )
        
        # Анализ общего счета совместимости
        if result.compatibility_score >= 80:
            result.relationship_highlights.append("Исключительно высокая совместимость")
        elif result.compatibility_score >= 60:
            result.relationship_highlights.append("Хорошая совместимость с потенциалом роста")
        elif result.compatibility_score >= 40:
            result.relationship_highlights.append("Средняя совместимость, требует работы над отношениями")
        else:
            result.challenges.append("Низкая базовая совместимость, много различий")

    async def _generate_relationship_advice(
        self, result: SynastryResult, person1: PartnerData, person2: PartnerData
    ):
        """Генерирует советы для отношений"""
        
        # Общие советы на основе совместимости
        if result.compatibility_score >= 70:
            result.advice.extend([
                "Поддерживайте открытое общение",
                "Развивайте совместные интересы",
                "Цените различия друг друга"
            ])
        elif result.compatibility_score >= 40:
            result.advice.extend([
                "Работайте над пониманием различий",
                "Ищите компромиссы в спорных вопросах",
                "Уделяйте время развитию отношений"
            ])
        else:
            result.advice.extend([
                "Требуется терпение и взаимопонимание",
                "Фокусируйтесь на общих целях",
                "Рассмотрите помощь специалиста по отношениям"
            ])

    async def calculate_composite_chart(
        self, person1: PartnerData, person2: PartnerData
    ) -> Optional[Dict[str, Any]]:
        """
        Вычисляет композитную карту отношений
        
        Returns:
            Словарь с данными композитной карты или None при ошибке
        """
        logger.info(f"SYNASTRY_COMPOSITE_START: Creating composite chart for {person1.name} and {person2.name}")
        
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
                        "sign": self.calculator._get_sign_from_longitude(midpoint).name_ru,
                        "degree_in_sign": midpoint % 30
                    }
            
            logger.info(f"SYNASTRY_COMPOSITE_SUCCESS: Created composite chart with {len(composite_planets)} planets")
            
            return {
                "planets": composite_planets,
                "relationship_theme": "Композитная карта показывает энергию отношений как единого целого"
            }
            
        except Exception as e:
            logger.error(f"SYNASTRY_COMPOSITE_ERROR: Failed to create composite chart: {e}")
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
            ("Sun", "Moon", "Соединение"): "Прекрасное взаимопонимание на эмоциональном уровне",
            ("Sun", "Moon", "Трин"): "Гармоничное сочетание мужской и женской энергий",
            ("Sun", "Moon", "Оппозиция"): "Притягивающие противоположности, нужен баланс",
            
            ("Venus", "Mars", "Соединение"): "Сильное физическое и эмоциональное притяжение",
            ("Venus", "Mars", "Трин"): "Естественная гармония в романтических отношениях",
            ("Venus", "Mars", "Квадрат"): "Страстные, но временами конфликтные отношения",
            
            ("Mercury", "Mercury", "Соединение"): "Отличное интеллектуальное понимание",
            ("Mercury", "Venus", "Трин"): "Красивое и гармоничное общение",
            ("Mercury", "Mars", "Квадрат"): "Споры и разногласия в общении",
        }
        
        key = (planet1, planet2, aspect_name)
        reverse_key = (planet2, planet1, aspect_name)
        
        return interpretations.get(key) or interpretations.get(reverse_key) or f"{planet1} и {planet2} в аспекте {aspect_name}"