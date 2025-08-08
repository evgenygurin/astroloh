"""
Расширенный сервис транзитов с интеграцией Kerykeion.
Использует TransitsTimeRangeFactory для профессионального анализа транзитов.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pytz

from app.services.kerykeion_service import KerykeionService
from app.services.astrology_calculator import AstrologyCalculator
from app.models.transit_models import (
    TransitAspect, 
    TransitData, 
    TransitRequest, 
    TransitAnalysisResult
)

logger = logging.getLogger(__name__)

# Try to import Kerykeion transit functionality
try:
    from kerykeion import AstrologicalSubject
    from kerykeion.ephemeris import EphemerisDataFactory
    # Try different import paths for TransitsTimeRangeFactory
    try:
        from kerykeion.transits import TransitsTimeRangeFactory
    except ImportError:
        try:
            from kerykeion import TransitsTimeRangeFactory
        except ImportError:
            TransitsTimeRangeFactory = None
    
    KERYKEION_TRANSITS_AVAILABLE = TransitsTimeRangeFactory is not None
    logger.info("ENHANCED_TRANSIT_SERVICE_INIT: Kerykeion transits available")
except ImportError as e:
    logger.warning(f"ENHANCED_TRANSIT_SERVICE_INIT: Kerykeion transits not available - {e}")
    KERYKEION_TRANSITS_AVAILABLE = False
    TransitsTimeRangeFactory = None
    EphemerisDataFactory = None


class TransitService:
    """Расширенный сервис для анализа транзитов с поддержкой Kerykeion."""

    def __init__(self):
        self.kerykeion_service = KerykeionService()
        self.astro_calculator = AstrologyCalculator()
        self.logger = logging.getLogger(__name__)
        
        # Орбы для транзитных аспектов (более точные для профессиональной астрологии)
        self.transit_orbs = {
            0: 8,    # Соединение
            30: 2,   # Полусекстиль
            45: 2,   # Полуквадрат
            60: 6,   # Секстиль
            72: 2,   # Квинтиль
            90: 8,   # Квадрат
            120: 8,  # Трин
            135: 2,  # Сесквиквадрат
            144: 2,  # Биквинтиль
            150: 3,  # Квинкунс
            180: 8,  # Оппозиция
        }

    def is_available(self) -> bool:
        """Проверяет доступность Kerykeion транзитов."""
        return KERYKEION_TRANSITS_AVAILABLE and self.kerykeion_service.is_available()

    def get_current_transits(
        self,
        natal_chart: Dict[str, Any],
        transit_date: Optional[datetime] = None,
        include_minor_aspects: bool = True
    ) -> Dict[str, Any]:
        """
        Получает текущие транзиты к натальной карте.
        
        Args:
            natal_chart: Данные натальной карты
            transit_date: Дата для расчета транзитов
            include_minor_aspects: Включать минорные аспекты
        """
        if transit_date is None:
            transit_date = datetime.now(pytz.UTC)

        logger.info(f"ENHANCED_TRANSIT_SERVICE_CURRENT_START: {transit_date.strftime('%Y-%m-%d')}")

        # Попробуем использовать Kerykeion, если доступен
        if self.is_available():
            return self._get_kerykeion_transits(natal_chart, transit_date, include_minor_aspects)
        else:
            # Fallback к базовому калькулятору
            logger.warning("ENHANCED_TRANSIT_SERVICE_FALLBACK: Using basic calculator")
            return self._get_basic_transits(natal_chart, transit_date)

    def _get_kerykeion_transits(
        self,
        natal_chart: Dict[str, Any],
        transit_date: datetime,
        include_minor_aspects: bool
    ) -> Dict[str, Any]:
        """Получает транзиты через Kerykeion."""
        try:
            # Создаем натальную карту как AstrologicalSubject
            birth_datetime = datetime.fromisoformat(natal_chart.get("birth_datetime", "2000-01-01T12:00:00"))
            coordinates = natal_chart.get("coordinates", {"latitude": 55.7558, "longitude": 37.6176})
            
            natal_subject = self.kerykeion_service.create_astrological_subject(
                name="NatalChart",
                birth_datetime=birth_datetime,
                latitude=coordinates["latitude"],
                longitude=coordinates["longitude"]
            )
            
            if not natal_subject:
                logger.error("ENHANCED_TRANSIT_SERVICE_NATAL_ERROR: Failed to create natal subject")
                return self._get_basic_transits(natal_chart, transit_date)

            # Создаем эфемериды для периода транзитов
            start_date = transit_date - timedelta(days=1)
            end_date = transit_date + timedelta(days=1)
            
            if EphemerisDataFactory:
                ephemeris_factory = EphemerisDataFactory(
                    start_datetime=start_date,
                    end_datetime=end_date,
                    step_type="hours",
                    step=6  # Каждые 6 часов для точности
                )
                ephemeris_data = ephemeris_factory.get_ephemeris_data()
                
                # Создаем транзитную фабрику
                if TransitsTimeRangeFactory:
                    transit_factory = TransitsTimeRangeFactory(
                        natal_chart=natal_subject,
                        ephemeris_data_points=ephemeris_data
                    )
                    transit_results = transit_factory.get_transit_moments()
                    
                    # Обрабатываем результаты
                    processed_transits = self._process_kerykeion_transit_results(
                        transit_results, 
                        transit_date,
                        include_minor_aspects
                    )
                    
                    logger.info("ENHANCED_TRANSIT_SERVICE_KERYKEION_SUCCESS")
                    return processed_transits

        except Exception as e:
            logger.error(f"ENHANCED_TRANSIT_SERVICE_KERYKEION_ERROR: {e}")
        
        # Fallback к базовому методу
        return self._get_basic_transits(natal_chart, transit_date)

    def _process_kerykeion_transit_results(
        self,
        transit_results: List[Any],
        target_date: datetime,
        include_minor_aspects: bool
    ) -> Dict[str, Any]:
        """Обрабатывает результаты транзитов от Kerykeion."""
        active_transits = []
        approaching_transits = []
        
        for result in transit_results:
            # Извлекаем информацию о транзите
            transit_info = self._extract_transit_info(result, target_date)
            if not transit_info:
                continue
                
            # Проверяем, подходит ли аспект по настройкам
            aspect_angle = transit_info.get("angle", 0)
            if not include_minor_aspects and aspect_angle not in [0, 60, 90, 120, 180]:
                continue
                
            orb = transit_info.get("orb", 10)
            if orb <= 2:  # Точные аспекты
                active_transits.append(transit_info)
            elif orb <= 8:  # Приближающиеся
                approaching_transits.append(transit_info)
        
        # Сортируем по точности
        active_transits.sort(key=lambda x: x.get("orb", 10))
        approaching_transits.sort(key=lambda x: x.get("orb", 10))
        
        return {
            "date": target_date.isoformat(),
            "active_transits": active_transits[:10],
            "approaching_transits": approaching_transits[:5],
            "summary": self._create_enhanced_transit_summary(active_transits),
            "daily_influences": self._get_enhanced_daily_influences(active_transits),
            "energy_assessment": self._assess_energy_patterns(active_transits),
            "timing_recommendations": self._get_timing_recommendations(active_transits),
            "source": "kerykeion"
        }

    def _extract_transit_info(self, transit_result: Any, target_date: datetime) -> Optional[Dict[str, Any]]:
        """Извлекает информацию о транзите из результата Kerykeion."""
        try:
            # Эта часть зависит от структуры данных, возвращаемых TransitsTimeRangeFactory
            # Адаптируем под реальную структуру данных
            return {
                "transit_planet": getattr(transit_result, "transiting_planet", "Unknown"),
                "natal_planet": getattr(transit_result, "natal_planet", "Unknown"),
                "aspect": getattr(transit_result, "aspect_name", "Unknown"),
                "angle": getattr(transit_result, "aspect_angle", 0),
                "orb": getattr(transit_result, "orb", 10),
                "exact_angle": getattr(transit_result, "exact_angle", 0),
                "influence": self._get_enhanced_transit_influence(
                    getattr(transit_result, "transiting_planet", "Unknown"),
                    getattr(transit_result, "natal_planet", "Unknown"),
                    getattr(transit_result, "aspect_name", "Unknown")
                ),
                "strength": self._calculate_enhanced_aspect_strength(
                    getattr(transit_result, "orb", 10),
                    getattr(transit_result, "aspect_angle", 0)
                ),
                "nature": self._get_enhanced_aspect_nature(
                    getattr(transit_result, "aspect_name", "Unknown")
                ),
                "peak_date": getattr(transit_result, "exact_date", target_date).isoformat(),
                "duration_days": getattr(transit_result, "duration", 3),
            }
        except Exception as e:
            logger.error(f"ENHANCED_TRANSIT_SERVICE_EXTRACT_ERROR: {e}")
            return None

    def _get_basic_transits(
        self,
        natal_chart: Dict[str, Any],
        transit_date: datetime
    ) -> Dict[str, Any]:
        """Fallback метод для получения транзитов через базовый калькулятор."""
        logger.info("ENHANCED_TRANSIT_SERVICE_BASIC_FALLBACK")
        
        # Получаем натальные планеты
        natal_planets = natal_chart.get("planets", {})
        
        # Получаем текущие позиции планет
        current_positions = self.astro_calculator.calculate_planet_positions(transit_date)
        
        active_transits = []
        approaching_transits = []
        
        for transit_planet, transit_data in current_positions.items():
            for natal_planet, natal_data in natal_planets.items():
                aspects = self._calculate_basic_transit_aspects(
                    transit_data, natal_data, transit_planet, natal_planet
                )
                
                for aspect in aspects:
                    orb = aspect.get("orb", 10)
                    if orb <= 2:
                        active_transits.append(aspect)
                    elif orb <= 8:
                        approaching_transits.append(aspect)
        
        return {
            "date": transit_date.isoformat(),
            "active_transits": active_transits[:10],
            "approaching_transits": approaching_transits[:5],
            "summary": self._create_enhanced_transit_summary(active_transits),
            "daily_influences": self._get_enhanced_daily_influences(active_transits),
            "source": "basic"
        }

    def _calculate_basic_transit_aspects(
        self,
        transit_data: Dict[str, Any],
        natal_data: Dict[str, Any], 
        transit_planet: str,
        natal_planet: str
    ) -> List[Dict[str, Any]]:
        """Вычисляет аспекты базовым методом."""
        aspects = []
        transit_longitude = transit_data["longitude"]
        natal_longitude = natal_data["longitude"]
        
        # Вычисляем угол между планетами
        angle = abs(transit_longitude - natal_longitude)
        if angle > 180:
            angle = 360 - angle
        
        # Проверяем аспекты
        for aspect_angle, orb in self.transit_orbs.items():
            if abs(angle - aspect_angle) <= orb:
                exactness = abs(angle - aspect_angle)
                
                aspects.append({
                    "transit_planet": transit_planet,
                    "natal_planet": natal_planet,
                    "aspect": self._get_aspect_name(aspect_angle),
                    "angle": aspect_angle,
                    "orb": exactness,
                    "exact_angle": angle,
                    "influence": self._get_enhanced_transit_influence(
                        transit_planet, natal_planet, self._get_aspect_name(aspect_angle)
                    ),
                    "strength": self._calculate_enhanced_aspect_strength(exactness, aspect_angle),
                    "nature": self._get_enhanced_aspect_nature(self._get_aspect_name(aspect_angle)),
                })
        
        return aspects

    def get_period_forecast(
        self,
        natal_chart: Dict[str, Any],
        days: int = 7,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Получает прогноз транзитов на период.
        
        Args:
            natal_chart: Данные натальной карты
            days: Количество дней для прогноза
            start_date: Начальная дата (по умолчанию сегодня)
        """
        if start_date is None:
            start_date = datetime.now(pytz.UTC)
            
        logger.info(f"ENHANCED_TRANSIT_SERVICE_PERIOD_START: {days} days from {start_date}")
        
        daily_forecasts = []
        important_dates = []
        overall_themes = set()
        
        for i in range(days):
            forecast_date = start_date + timedelta(days=i)
            daily_transits = self.get_current_transits(natal_chart, forecast_date)
            
            daily_forecast = {
                "date": forecast_date.strftime("%Y-%m-%d"),
                "energy_level": self._calculate_daily_energy(daily_transits),
                "main_influences": daily_transits.get("daily_influences", [])[:3],
                "recommendations": self._get_daily_recommendations(daily_transits),
            }
            
            daily_forecasts.append(daily_forecast)
            
            # Находим важные даты
            for transit in daily_transits.get("active_transits", []):
                if transit.get("strength") in ["очень сильный", "сильный"]:
                    important_dates.append({
                        "date": forecast_date.strftime("%Y-%m-%d"),
                        "event": f"{transit['transit_planet']} {transit['aspect']} {transit['natal_planet']}",
                        "significance": transit.get("influence", "Важное транзитное влияние")
                    })
            
            # Собираем общие темы
            for influence in daily_transits.get("daily_influences", []):
                theme = self._extract_theme_from_influence(influence)
                if theme:
                    overall_themes.add(theme)
        
        return {
            "period": f"{days} дней",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "daily_forecasts": daily_forecasts,
            "important_dates": important_dates[:5],  # Топ-5 важных дат
            "overall_themes": list(overall_themes)[:5],
            "period_summary": self._create_period_summary(daily_forecasts),
            "general_advice": self._get_period_advice(overall_themes)
        }

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
        today = datetime.now(pytz.UTC)
        start_date = today - timedelta(days=lookback_days)
        end_date = today + timedelta(days=lookahead_days)
        
        logger.info(f"ENHANCED_TRANSIT_SERVICE_IMPORTANT_RANGE: {start_date} to {end_date}")
        
        major_transits = []
        life_changing_events = []
        
        # Анализируем медленные планеты (Юпитер, Сатурн, Уран, Нептун, Плутон)
        slow_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        
        current_date = start_date
        while current_date <= end_date:
            daily_transits = self.get_current_transits(natal_chart, current_date)
            
            for transit in daily_transits.get("active_transits", []):
                transit_planet = transit.get("transit_planet", "")
                
                # Фокусируемся на транзитах медленных планет
                if transit_planet in slow_planets:
                    major_transits.append({
                        **transit,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "planet_speed": self._get_planet_speed(transit_planet),
                        "duration_estimate": self._estimate_transit_duration(
                            transit_planet, 
                            transit.get("aspect", "")
                        ),
                        "life_area_affected": self._get_affected_life_area(
                            transit.get("natal_planet", "")
                        ),
                        "transformation_level": self._assess_transformation_level(
                            transit_planet, 
                            transit.get("aspect", "")
                        )
                    })
            
            current_date += timedelta(days=7)  # Проверяем каждую неделю
        
        # Убираем дубликаты и сортируем по важности
        unique_transits = self._deduplicate_transits(major_transits)
        important_transits = sorted(
            unique_transits, 
            key=lambda x: (x.get("transformation_level", 0), -x.get("orb", 10))
        )[:10]
        
        return {
            "analysis_period": f"{lookback_days + lookahead_days} дней",
            "important_transits": important_transits,
            "life_themes": self._extract_life_themes(important_transits),
            "transformation_timeline": self._create_transformation_timeline(important_transits),
            "preparation_advice": self._get_preparation_advice(important_transits),
            "spiritual_guidance": self._get_spiritual_guidance(important_transits)
        }

    # Helper methods for enhanced functionality

    def _get_enhanced_transit_influence(self, transit_planet: str, natal_planet: str, aspect: str) -> str:
        """Получает расширенное описание влияния транзита."""
        # Более детальные интерпретации транзитов
        detailed_influences = {
            ("Jupiter", "Sun", "Trine"): "Период расширения личной силы и уверенности в себе. Удачное время для лидерства и новых начинаний.",
            ("Saturn", "Moon", "Square"): "Эмоциональные ограничения и необходимость структурировать чувственную сферу. Время дисциплины в отношениях.",
            ("Uranus", "Mercury", "Conjunction"): "Революционные идеи и неожиданные озарения. Возможны резкие изменения в мышлении и коммуникации.",
            ("Neptune", "Venus", "Opposition"): "Иллюзии в любви и творчестве. Важно различать фантазии и реальность в отношениях.",
            ("Pluto", "Mars", "Square"): "Интенсивная трансформация энергии и действий. Возможны силовые конфликты и внутренние революции."
        }
        
        key = (transit_planet, natal_planet, aspect)
        return detailed_influences.get(key, f"Взаимодействие {transit_planet} и {natal_planet} через {aspect}")

    def _calculate_enhanced_aspect_strength(self, orb: float, aspect_angle: float) -> str:
        """Вычисляет силу аспекта с учетом типа аспекта."""
        # Разные аспекты имеют разные допустимые орбы
        max_orbs = {0: 8, 60: 6, 90: 8, 120: 8, 180: 8, 30: 2, 45: 2, 135: 2, 150: 3}
        max_orb = max_orbs.get(aspect_angle, 5)
        
        strength_ratio = (max_orb - orb) / max_orb
        
        if strength_ratio >= 0.8:
            return "очень сильный"
        elif strength_ratio >= 0.6:
            return "сильный"
        elif strength_ratio >= 0.4:
            return "умеренный"
        else:
            return "слабый"

    def _get_enhanced_aspect_nature(self, aspect_name: str) -> str:
        """Возвращает расширенную природу аспекта."""
        natures = {
            "Соединение": "интенсификация",
            "Секстиль": "гармоничная возможность",
            "Квадрат": "динамическое напряжение",
            "Трин": "естественный поток",
            "Оппозиция": "поляризация и осознание",
            "Полусекстиль": "тонкая связь",
            "Полуквадрат": "скрытое раздражение",
            "Сесквиквадрат": "нарастающее напряжение",
            "Квинкунс": "необходимость адаптации",
            "Квинтиль": "творческий потенциал",
            "Биквинтиль": "художественное выражение"
        }
        return natures.get(aspect_name, "нейтральное взаимодействие")

    def _create_enhanced_transit_summary(self, active_transits: List[Dict[str, Any]]) -> str:
        """Создает улучшенное резюме транзитов."""
        if not active_transits:
            return "Спокойный период для внутренней работы и планирования"

        # Анализируем доминирующие планеты
        planet_influences = {}
        for transit in active_transits:
            planet = transit.get("transit_planet", "")
            if planet:
                planet_influences[planet] = planet_influences.get(planet, 0) + 1

        dominant_planet = max(planet_influences, key=planet_influences.get) if planet_influences else None
        
        # Анализируем природу аспектов
        harmonious_count = sum(1 for t in active_transits 
                             if t.get("nature", "") in ["гармоничная возможность", "естественный поток"])
        challenging_count = sum(1 for t in active_transits 
                              if t.get("nature", "") in ["динамическое напряжение", "поляризация и осознание"])

        if dominant_planet:
            planet_themes = {
                "Jupiter": "расширения и роста",
                "Saturn": "структуры и дисциплины", 
                "Uranus": "изменений и освобождения",
                "Neptune": "духовности и вдохновения",
                "Pluto": "трансформации и обновления",
                "Mars": "действия и энергии",
                "Venus": "любви и гармонии"
            }
            theme = planet_themes.get(dominant_planet, "активности")
            
            if harmonious_count > challenging_count:
                return f"Благоприятный период {theme} с преобладанием гармоничных энергий"
            elif challenging_count > harmonious_count:
                return f"Интенсивный период {theme} с важными вызовами для роста"
            else:
                return f"Сбалансированный период {theme} с возможностями и испытаниями"
        else:
            return "Период разнообразных астрологических влияний"

    def _get_enhanced_daily_influences(self, active_transits: List[Dict[str, Any]]) -> List[str]:
        """Получает улучшенные ключевые влияния дня."""
        influences = []
        
        # Берем самые сильные транзиты
        strong_transits = [t for t in active_transits 
                         if t.get("strength", "") in ["сильный", "очень сильный"]][:3]
        
        for transit in strong_transits:
            influence = (
                f"{transit.get('transit_planet', 'Планета')} "
                f"{transit.get('aspect', 'аспект')} "
                f"{transit.get('natal_planet', 'планета')}: "
                f"{transit.get('influence', 'влияние на жизненные процессы')}"
            )
            influences.append(influence)
        
        return influences

    def _assess_energy_patterns(self, active_transits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Оценивает энергетические паттерны дня."""
        total_energy = 50  # Базовый уровень
        
        for transit in active_transits:
            planet = transit.get("transit_planet", "")
            aspect = transit.get("aspect", "")
            strength = transit.get("strength", "слабый")
            
            # Влияние планет на энергию
            planet_energy = {
                "Mars": 15, "Sun": 12, "Jupiter": 10, "Uranus": 8,
                "Moon": 5, "Venus": 5, "Mercury": 3,
                "Saturn": -5, "Neptune": -3, "Pluto": 0
            }
            
            # Влияние аспектов
            aspect_multiplier = {
                "Соединение": 1.2, "Трин": 1.1, "Секстиль": 1.05,
                "Квадрат": 0.9, "Оппозиция": 0.95
            }
            
            # Влияние силы
            strength_multiplier = {
                "очень сильный": 1.3, "сильный": 1.1, "умеренный": 1.0, "слабый": 0.8
            }
            
            energy_delta = planet_energy.get(planet, 0)
            energy_delta *= aspect_multiplier.get(aspect, 1.0)
            energy_delta *= strength_multiplier.get(strength, 1.0)
            
            total_energy += energy_delta
        
        # Нормализуем от 0 до 100
        total_energy = max(0, min(100, total_energy))
        
        return {
            "level": int(total_energy),
            "description": self._get_energy_description(total_energy),
            "recommendations": self._get_energy_recommendations(total_energy)
        }

    def _get_timing_recommendations(self, active_transits: List[Dict[str, Any]]) -> List[str]:
        """Получает рекомендации по тайминга действий."""
        recommendations = []
        
        for transit in active_transits[:5]:  # Топ-5 транзитов
            planet = transit.get("transit_planet", "")
            aspect = transit.get("aspect", "")
            natal_planet = transit.get("natal_planet", "")
            
            timing_advice = self._get_specific_timing_advice(planet, aspect, natal_planet)
            if timing_advice:
                recommendations.append(timing_advice)
        
        return recommendations[:3]  # Ограничиваем 3 рекомендациями

    # Utility methods

    def _get_aspect_name(self, angle: float) -> str:
        """Возвращает название аспекта по углу."""
        aspect_names = {
            0: "Соединение", 30: "Полусекстиль", 45: "Полуквадрат",
            60: "Секстиль", 72: "Квинтиль", 90: "Квадрат",
            120: "Трин", 135: "Сесквиквадрат", 144: "Биквинтиль",
            150: "Квинкунс", 180: "Оппозиция"
        }
        return aspect_names.get(angle, "Неизвестный")

    def _calculate_daily_energy(self, daily_transits: Dict[str, Any]) -> str:
        """Вычисляет энергетический уровень дня."""
        energy_assessment = daily_transits.get("energy_assessment", {})
        level = energy_assessment.get("level", 50)
        
        if level >= 80:
            return "высокая"
        elif level >= 60:
            return "повышенная"
        elif level >= 40:
            return "умеренная"
        elif level >= 20:
            return "пониженная"
        else:
            return "низкая"

    def _get_daily_recommendations(self, daily_transits: Dict[str, Any]) -> List[str]:
        """Получает рекомендации на день."""
        timing_recs = daily_transits.get("timing_recommendations", [])
        energy_recs = daily_transits.get("energy_assessment", {}).get("recommendations", [])
        
        all_recommendations = timing_recs + energy_recs
        return all_recommendations[:2]  # Ограничиваем 2 рекомендациями на день

    def _extract_theme_from_influence(self, influence: str) -> Optional[str]:
        """Извлекает тему из описания влияния."""
        themes_keywords = {
            "отношения": ["любовь", "партнер", "брак", "отношения"],
            "карьера": ["работа", "карьера", "деньги", "успех", "достижения"],
            "здоровье": ["здоровье", "энергия", "силы", "восстановление"],
            "творчество": ["творчество", "искусство", "вдохновение", "создание"],
            "духовность": ["духовность", "медитация", "развитие", "мудрость"],
            "обучение": ["обучение", "знания", "изучение", "понимание"]
        }
        
        influence_lower = influence.lower()
        for theme, keywords in themes_keywords.items():
            if any(keyword in influence_lower for keyword in keywords):
                return theme
        
        return None

    def _create_period_summary(self, daily_forecasts: List[Dict[str, Any]]) -> str:
        """Создает резюме периода."""
        if not daily_forecasts:
            return "Недостаточно данных для анализа периода"
        
        # Анализируем энергетические уровни
        energy_levels = [f.get("energy_level", "умеренная") for f in daily_forecasts]
        high_energy_days = sum(1 for e in energy_levels if e in ["высокая", "повышенная"])
        
        total_days = len(daily_forecasts)
        high_energy_ratio = high_energy_days / total_days
        
        if high_energy_ratio >= 0.7:
            return f"Энергично насыщенный период с {high_energy_days} днями высокой активности из {total_days}"
        elif high_energy_ratio >= 0.4:
            return f"Сбалансированный период с чередованием активности и спокойствия"
        else:
            return f"Спокойный период, подходящий для внутренней работы и планирования"

    def _get_period_advice(self, themes: set) -> str:
        """Получает общий совет на период."""
        if not themes:
            return "Используйте этот период для саморефлексии и планирования будущего"
        
        theme_advice = {
            "отношения": "Уделите внимание близким людям и укреплению связей",
            "карьера": "Фокусируйтесь на профессиональном развитии и достижении целей",
            "здоровье": "Позаботьтесь о своем физическом и эмоциональном благополучии",
            "творчество": "Дайте волю творческому самовыражению и вдохновению",
            "духовность": "Погрузитесь в духовные практики и самопознание",
            "обучение": "Расширяйте свои знания и навыки"
        }
        
        primary_theme = list(themes)[0] if themes else None
        return theme_advice.get(primary_theme, "Оставайтесь открытыми к новым возможностям и следуйте интуиции")

    def _get_planet_speed(self, planet: str) -> str:
        """Получает скорость планеты."""
        speeds = {
            "Moon": "быстрая", "Mercury": "быстрая", "Venus": "быстрая", "Sun": "быстрая",
            "Mars": "средняя", "Jupiter": "медленная", "Saturn": "медленная",
            "Uranus": "очень медленная", "Neptune": "очень медленная", "Pluto": "очень медленная"
        }
        return speeds.get(planet, "неизвестная")

    def _estimate_transit_duration(self, planet: str, aspect: str) -> str:
        """Оценивает длительность транзита."""
        base_durations = {
            "Jupiter": "2-3 недели", "Saturn": "1-2 месяца", "Uranus": "6-12 месяцев",
            "Neptune": "1-2 года", "Pluto": "2-3 года"
        }
        return base_durations.get(planet, "несколько дней")

    def _get_affected_life_area(self, natal_planet: str) -> str:
        """Определяет затрагиваемую сферу жизни."""
        life_areas = {
            "Sun": "личность и самовыражение",
            "Moon": "эмоции и дом",
            "Mercury": "общение и мышление", 
            "Venus": "любовь и отношения",
            "Mars": "действия и энергия",
            "Jupiter": "рост и возможности",
            "Saturn": "структура и ответственность"
        }
        return life_areas.get(natal_planet, "общие жизненные процессы")

    def _assess_transformation_level(self, transit_planet: str, aspect: str) -> int:
        """Оценивает уровень трансформации от 1 до 10."""
        planet_power = {
            "Pluto": 10, "Uranus": 8, "Neptune": 7, "Saturn": 6, "Jupiter": 4,
            "Mars": 3, "Venus": 2, "Mercury": 2, "Sun": 5, "Moon": 3
        }
        
        aspect_intensity = {
            "Соединение": 1.0, "Оппозиция": 0.9, "Квадрат": 0.8, "Трин": 0.6, "Секстиль": 0.4
        }
        
        base_power = planet_power.get(transit_planet, 1)
        intensity = aspect_intensity.get(aspect, 0.5)
        
        return int(base_power * intensity)

    def _deduplicate_transits(self, transits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаляет дублированные транзиты."""
        seen = set()
        unique = []
        
        for transit in transits:
            key = (
                transit.get("transit_planet", ""),
                transit.get("natal_planet", ""),
                transit.get("aspect", "")
            )
            if key not in seen:
                seen.add(key)
                unique.append(transit)
        
        return unique

    def _extract_life_themes(self, important_transits: List[Dict[str, Any]]) -> List[str]:
        """Извлекает жизненные темы из важных транзитов."""
        themes = set()
        
        for transit in important_transits:
            life_area = transit.get("life_area_affected", "")
            if life_area:
                themes.add(life_area)
        
        return list(themes)[:5]

    def _create_transformation_timeline(self, important_transits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Создает временную линию трансформаций."""
        timeline = []
        
        for transit in important_transits[:5]:  # Топ-5 важных
            timeline.append({
                "period": transit.get("date", ""),
                "transformation": f"{transit.get('transit_planet', '')} {transit.get('aspect', '')} {transit.get('natal_planet', '')}",
                "life_area": transit.get("life_area_affected", ""),
                "intensity": transit.get("transformation_level", 1),
                "duration": transit.get("duration_estimate", "")
            })
        
        return timeline

    def _get_preparation_advice(self, important_transits: List[Dict[str, Any]]) -> List[str]:
        """Получает советы по подготовке к важным транзитам."""
        advice = []
        
        for transit in important_transits[:3]:  # Топ-3 важных
            planet = transit.get("transit_planet", "")
            aspect = transit.get("aspect", "")
            
            preparation_tips = {
                ("Pluto", "Квадрат"): "Готовьтесь к глубоким внутренним изменениям. Отпустите устаревшее.",
                ("Saturn", "Оппозиция"): "Время подвести итоги и принять ответственность за свой путь.",
                ("Uranus", "Соединение"): "Будьте открыты неожиданным возможностям и изменениям.",
            }
            
            tip = preparation_tips.get((planet, aspect))
            if tip:
                advice.append(tip)
        
        if not advice:
            advice.append("Сохраняйте гибкость и доверяйте процессу жизненных изменений")
        
        return advice

    def _get_spiritual_guidance(self, important_transits: List[Dict[str, Any]]) -> str:
        """Получает духовное руководство по важным транзитам."""
        if not important_transits:
            return "Время для внутренней тишины и прислушивания к своей мудрости"
        
        dominant_planet = important_transits[0].get("transit_planet", "")
        
        spiritual_messages = {
            "Pluto": "Доверьтесь процессу трансформации. Смерть старого рождает новое.",
            "Neptune": "Следуйте интуиции и открывайтесь духовным истинам.",
            "Uranus": "Освобождайтесь от ограничений и следуйте своей уникальности.",
            "Saturn": "Примите уроки жизни и найдите мудрость в ограничениях.",
            "Jupiter": "Расширяйте сознание и доверяйте изобилию Вселенной."
        }
        
        return spiritual_messages.get(
            dominant_planet, 
            "Каждый момент — возможность для роста и пробуждения сознания"
        )

    def _get_energy_description(self, level: float) -> str:
        """Получает описание энергетического уровня."""
        if level >= 80:
            return "Очень высокий уровень энергии и активности"
        elif level >= 60:
            return "Повышенная энергия, благоприятное время для действий"
        elif level >= 40:
            return "Умеренная энергия, сбалансированное состояние"
        elif level >= 20:
            return "Пониженная энергия, время для восстановления"
        else:
            return "Низкая энергия, необходим отдых и покой"

    def _get_energy_recommendations(self, level: float) -> List[str]:
        """Получает рекомендации по управлению энергией."""
        if level >= 80:
            return ["Используйте энергию для важных проектов", "Не перенапрягайтесь"]
        elif level >= 60:
            return ["Хорошее время для активных действий", "Планируйте важные встречи"]
        elif level >= 40:
            return ["Сохраняйте баланс активности и отдыха", "Следуйте естественным ритмам"]
        elif level >= 20:
            return ["Больше отдыхайте", "Избегайте излишнего стресса"]
        else:
            return ["Необходим полноценный отдых", "Восстановите силы перед активностью"]

    def _get_specific_timing_advice(self, planet: str, aspect: str, natal_planet: str) -> Optional[str]:
        """Получает конкретный совет по таймингу."""
        timing_combinations = {
            ("Jupiter", "Трин", "Sun"): "Отличное время для начинания новых проектов",
            ("Mars", "Квадрат", "Moon"): "Избегайте эмоциональных решений, подождите 2-3 дня",
            ("Venus", "Секстиль", "Venus"): "Благоприятное время для романтических отношений",
            ("Saturn", "Оппозиция", "Mercury"): "Отложите важные решения, проанализируйте детально",
            ("Mercury", "Соединение", "Sun"): "Хорошее время для переговоров и общения",
        }
        
        return timing_combinations.get((planet, aspect, natal_planet))