"""
Сервис анализа совместимости с расширенными возможностями.
Комплексный анализ отношений с использованием различных астрологических техник.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.yandex_models import YandexZodiacSign
from app.services.synastry_service import PartnerData, SynastryResult, SynastryService

logger = logging.getLogger(__name__)


class CompatibilityType:
    """Типы совместимости для анализа"""
    
    ROMANTIC = "romantic"
    FRIENDSHIP = "friendship"
    BUSINESS = "business"
    FAMILY = "family"


class CompatibilityAnalyzer:
    """Расширенный анализатор совместимости"""

    def __init__(self, synastry_service: SynastryService):
        self.synastry_service = synastry_service
        logger.info("COMPATIBILITY_ANALYZER_INIT: Compatibility analyzer initialized")

    async def analyze_full_compatibility(
        self,
        person1: PartnerData,
        person2: PartnerData,
        compatibility_type: str = CompatibilityType.ROMANTIC,
    ) -> Dict[str, Any]:
        """
        Полный анализ совместимости между двумя партнерами
        
        Args:
            person1: Данные первого партнера
            person2: Данные второго партнера
            compatibility_type: Тип анализируемых отношений
        
        Returns:
            Полный отчет о совместимости
        """
        logger.info(
            f"COMPATIBILITY_FULL_ANALYSIS_START: Analyzing {compatibility_type} compatibility for {person1.name} and {person2.name}"
        )

        try:
            # Получаем синастрию
            synastry = await self.synastry_service.calculate_synastry(person1, person2)

            # Анализ по знакам зодиака
            zodiac_compatibility = self._analyze_zodiac_compatibility(
                person1.zodiac_sign, person2.zodiac_sign, compatibility_type
            )

            # Композитная карта
            composite_chart = await self.synastry_service.calculate_composite_chart(
                person1, person2
            )

            # Создаем итоговый отчет
            compatibility_report = {
                "overall_score": self._calculate_overall_score(synastry, zodiac_compatibility),
                "compatibility_type": compatibility_type,
                "synastry_analysis": self._format_synastry_analysis(synastry),
                "zodiac_analysis": zodiac_compatibility,
                "composite_analysis": composite_chart,
                "strengths": synastry.strengths + zodiac_compatibility.get("strengths", []),
                "challenges": synastry.challenges + zodiac_compatibility.get("challenges", []),
                "advice": synastry.advice + zodiac_compatibility.get("advice", []),
                "relationship_themes": self._identify_relationship_themes(synastry, zodiac_compatibility),
                "growth_potential": self._assess_growth_potential(synastry, zodiac_compatibility),
            }

            logger.info(
                f"COMPATIBILITY_FULL_ANALYSIS_SUCCESS: Generated report with {compatibility_report['overall_score']:.1f}% compatibility"
            )

            return compatibility_report

        except Exception as e:
            logger.error(f"COMPATIBILITY_FULL_ANALYSIS_ERROR: Analysis failed: {e}")
            return self._create_fallback_report(person1, person2, compatibility_type)

    def _analyze_zodiac_compatibility(
        self,
        sign1: Optional[YandexZodiacSign],
        sign2: Optional[YandexZodiacSign],
        compatibility_type: str,
    ) -> Dict[str, Any]:
        """Анализирует совместимость по знакам зодиака с учетом типа отношений"""
        
        if not sign1 or not sign2:
            return {"score": 50, "description": "Недостаточно данных для анализа"}

        # Элементы знаков
        elements = {
            YandexZodiacSign.ARIES: "fire",
            YandexZodiacSign.LEO: "fire",
            YandexZodiacSign.SAGITTARIUS: "fire",
            YandexZodiacSign.TAURUS: "earth",
            YandexZodiacSign.VIRGO: "earth",
            YandexZodiacSign.CAPRICORN: "earth",
            YandexZodiacSign.GEMINI: "air",
            YandexZodiacSign.LIBRA: "air",
            YandexZodiacSign.AQUARIUS: "air",
            YandexZodiacSign.CANCER: "water",
            YandexZodiacSign.SCORPIO: "water",
            YandexZodiacSign.PISCES: "water",
        }

        # Качества знаков
        qualities = {
            YandexZodiacSign.ARIES: "cardinal",
            YandexZodiacSign.CANCER: "cardinal",
            YandexZodiacSign.LIBRA: "cardinal",
            YandexZodiacSign.CAPRICORN: "cardinal",
            YandexZodiacSign.TAURUS: "fixed",
            YandexZodiacSign.LEO: "fixed",
            YandexZodiacSign.SCORPIO: "fixed",
            YandexZodiacSign.AQUARIUS: "fixed",
            YandexZodiacSign.GEMINI: "mutable",
            YandexZodiacSign.VIRGO: "mutable",
            YandexZodiacSign.SAGITTARIUS: "mutable",
            YandexZodiacSign.PISCES: "mutable",
        }

        element1 = elements.get(sign1)
        element2 = elements.get(sign2)
        quality1 = qualities.get(sign1)
        quality2 = qualities.get(sign2)

        # Совместимость элементов
        element_compatibility = self._get_element_compatibility(element1, element2)
        
        # Совместимость качеств
        quality_compatibility = self._get_quality_compatibility(quality1, quality2)

        # Модификатор в зависимости от типа отношений
        type_modifier = self._get_type_modifier(
            sign1, sign2, compatibility_type
        )

        base_score = (element_compatibility + quality_compatibility) / 2
        final_score = min(100, max(0, base_score + type_modifier))

        analysis = {
            "score": final_score,
            "element_match": element_compatibility,
            "quality_match": quality_compatibility,
            "elements": f"{element1} + {element2}",
            "qualities": f"{quality1} + {quality2}",
            "strengths": [],
            "challenges": [],
            "advice": [],
        }

        # Добавляем интерпретации
        self._add_element_interpretations(analysis, element1, element2)
        self._add_quality_interpretations(analysis, quality1, quality2)
        self._add_type_specific_advice(analysis, compatibility_type, final_score)

        return analysis

    def _get_element_compatibility(self, element1: str, element2: str) -> float:
        """Возвращает совместимость элементов (0-100)"""
        compatibility_matrix = {
            ("fire", "fire"): 85,
            ("fire", "air"): 90,
            ("fire", "earth"): 40,
            ("fire", "water"): 30,
            ("earth", "earth"): 80,
            ("earth", "water"): 85,
            ("earth", "air"): 45,
            ("air", "air"): 75,
            ("air", "water"): 35,
            ("water", "water"): 80,
        }
        
        key = (element1, element2)
        reverse_key = (element2, element1)
        
        return compatibility_matrix.get(key) or compatibility_matrix.get(reverse_key) or 50

    def _get_quality_compatibility(self, quality1: str, quality2: str) -> float:
        """Возвращает совместимость качеств (0-100)"""
        compatibility_matrix = {
            ("cardinal", "cardinal"): 60,  # Конкуренция лидеров
            ("cardinal", "fixed"): 70,     # Инициатор + стабилизатор
            ("cardinal", "mutable"): 80,   # Лидер + адаптивный
            ("fixed", "fixed"): 50,        # Два упрямых
            ("fixed", "mutable"): 85,      # Стабильность + гибкость
            ("mutable", "mutable"): 75,    # Взаимная адаптация
        }
        
        key = (quality1, quality2)
        reverse_key = (quality2, quality1)
        
        return compatibility_matrix.get(key) or compatibility_matrix.get(reverse_key) or 60

    def _get_type_modifier(
        self, sign1: YandexZodiacSign, sign2: YandexZodiacSign, compatibility_type: str
    ) -> float:
        """Возвращает модификатор в зависимости от типа отношений"""
        
        # Особые сочетания для разных типов отношений
        if compatibility_type == CompatibilityType.BUSINESS:
            # В бизнесе важны земные знаки и кардинальные качества
            earth_signs = {YandexZodiacSign.TAURUS, YandexZodiacSign.VIRGO, YandexZodiacSign.CAPRICORN}
            if sign1 in earth_signs or sign2 in earth_signs:
                return 10
        
        elif compatibility_type == CompatibilityType.ROMANTIC:
            # В романтических отношениях важны водные и воздушные знаки
            romantic_pairs = [
                (YandexZodiacSign.CANCER, YandexZodiacSign.SCORPIO),
                (YandexZodiacSign.LEO, YandexZodiacSign.LIBRA),
                (YandexZodiacSign.TAURUS, YandexZodiacSign.PISCES),
            ]
            
            for pair in romantic_pairs:
                if (sign1, sign2) == pair or (sign2, sign1) == pair:
                    return 15
        
        elif compatibility_type == CompatibilityType.FRIENDSHIP:
            # В дружбе хорошо сочетаются воздушные знаки
            air_signs = {YandexZodiacSign.GEMINI, YandexZodiacSign.LIBRA, YandexZodiacSign.AQUARIUS}
            if sign1 in air_signs and sign2 in air_signs:
                return 12
        
        return 0

    def _add_element_interpretations(
        self, analysis: Dict, element1: str, element2: str
    ):
        """Добавляет интерпретации совместимости элементов"""
        
        element_descriptions = {
            ("fire", "fire"): {
                "strengths": ["Общая энергичность", "Взаимное вдохновение", "Активный образ жизни"],
                "challenges": ["Соперничество", "Импульсивность", "Быстрое выгорание"],
            },
            ("fire", "air"): {
                "strengths": ["Огонь разжигает воздух", "Творческий союз", "Динамичные отношения"],
                "challenges": ["Поверхностность", "Непостоянство", "Недостаток заземления"],
            },
            ("earth", "water"): {
                "strengths": ["Взаимная поддержка", "Стабильность", "Глубокая связь"],
                "challenges": ["Медлительность", "Сопротивление переменам", "Рутина"],
            },
            ("fire", "water"): {
                "strengths": ["Страстность", "Эмоциональная интенсивность"],
                "challenges": ["Конфликт стихий", "Огонь может испарить воду", "Эмоциональные взрывы"],
            },
        }
        
        key = (element1, element2)
        reverse_key = (element2, element1)
        
        descriptions = element_descriptions.get(key) or element_descriptions.get(reverse_key)
        
        if descriptions:
            analysis["strengths"].extend(descriptions["strengths"])
            analysis["challenges"].extend(descriptions["challenges"])

    def _add_quality_interpretations(
        self, analysis: Dict, quality1: str, quality2: str
    ):
        """Добавляет интерпретации совместимости качеств"""
        
        quality_descriptions = {
            ("cardinal", "fixed"): {
                "strengths": ["Инициатива + стабильность", "Баланс действия и терпения"],
                "challenges": ["Конфликт темпов", "Упрямство против напора"],
            },
            ("fixed", "mutable"): {
                "strengths": ["Стабильность + адаптивность", "Надежность + гибкость"],
                "challenges": ["Различные подходы к переменам"],
            },
            ("cardinal", "mutable"): {
                "strengths": ["Лидерство + поддержка", "Инициатива + адаптация"],
                "challenges": ["Разная скорость принятия решений"],
            },
        }
        
        key = (quality1, quality2)
        reverse_key = (quality2, quality1)
        
        descriptions = quality_descriptions.get(key) or quality_descriptions.get(reverse_key)
        
        if descriptions:
            analysis["strengths"].extend(descriptions["strengths"])
            analysis["challenges"].extend(descriptions["challenges"])

    def _add_type_specific_advice(
        self, analysis: Dict, compatibility_type: str, score: float
    ):
        """Добавляет советы специфичные для типа отношений"""
        
        if compatibility_type == CompatibilityType.ROMANTIC:
            if score >= 70:
                analysis["advice"].extend([
                    "Развивайте романтическую близость",
                    "Планируйте совместные приключения",
                    "Поддерживайте страсть и новизну"
                ])
            else:
                analysis["advice"].extend([
                    "Работайте над эмоциональной связью",
                    "Найдите компромисс в различиях",
                    "Уделяйте время романтическим моментам"
                ])
        
        elif compatibility_type == CompatibilityType.BUSINESS:
            if score >= 70:
                analysis["advice"].extend([
                    "Используйте сильные стороны каждого",
                    "Разделите зоны ответственности",
                    "Поддерживайте профессиональное общение"
                ])
            else:
                analysis["advice"].extend([
                    "Четко определите роли и обязанности",
                    "Установите ясные границы",
                    "Фокусируйтесь на общих целях"
                ])

    def _calculate_overall_score(
        self, synastry: SynastryResult, zodiac_analysis: Dict
    ) -> float:
        """Вычисляет общий балл совместимости"""
        
        synastry_weight = 0.7  # Синастрия важнее
        zodiac_weight = 0.3    # Базовая совместимость знаков
        
        synastry_score = synastry.compatibility_score
        zodiac_score = zodiac_analysis.get("score", 50)
        
        overall_score = synastry_score * synastry_weight + zodiac_score * zodiac_weight
        
        return round(overall_score, 1)

    def _format_synastry_analysis(self, synastry: SynastryResult) -> Dict[str, Any]:
        """Форматирует анализ синастрии для отчета"""
        
        return {
            "aspects_count": len(synastry.aspects),
            "major_aspects": [
                aspect for aspect in synastry.aspects
                if aspect.get("aspect") in ["Соединение", "Оппозиция", "Трин", "Квадрат"]
            ][:5],  # Топ-5 важных аспектов
            "compatibility_score": synastry.compatibility_score,
            "house_overlays": synastry.house_overlays,
        }

    def _identify_relationship_themes(
        self, synastry: SynastryResult, zodiac_analysis: Dict
    ) -> List[str]:
        """Определяет основные темы отношений"""
        
        themes = []
        
        # На основе аспектов
        if len(synastry.aspects) > 10:
            themes.append("Интенсивная связь с множеством взаимодействий")
        elif len(synastry.aspects) < 5:
            themes.append("Спокойные отношения с пространством для независимости")
        
        # На основе элементов
        elements = zodiac_analysis.get("elements", "")
        if "fire" in elements and "air" in elements:
            themes.append("Динамичные и вдохновляющие отношения")
        elif "earth" in elements and "water" in elements:
            themes.append("Стабильные и эмоционально глубокие отношения")
        
        # На основе общего счета
        overall_score = self._calculate_overall_score(synastry, zodiac_analysis)
        if overall_score >= 80:
            themes.append("Отношения с высоким потенциалом гармонии")
        elif overall_score <= 40:
            themes.append("Отношения-вызов, требующие усилий")
        
        return themes

    def _assess_growth_potential(
        self, synastry: SynastryResult, zodiac_analysis: Dict
    ) -> Dict[str, Any]:
        """Оценивает потенциал роста отношений"""
        
        growth_factors = {
            "learning_opportunities": [],
            "development_areas": [],
            "long_term_potential": "medium",
        }
        
        # Анализ вызовов как возможностей роста
        if synastry.challenges:
            growth_factors["learning_opportunities"].extend([
                "Преодоление различий в подходах",
                "Развитие терпения и понимания",
                "Работа с напряженными аспектами"
            ])
        
        # Области развития
        element_match = zodiac_analysis.get("element_match", 50)
        if element_match < 60:
            growth_factors["development_areas"].append("Гармонизация энергий")
        
        quality_match = zodiac_analysis.get("quality_match", 50)
        if quality_match < 60:
            growth_factors["development_areas"].append("Синхронизация темпа жизни")
        
        # Долгосрочный потенциал
        overall_score = self._calculate_overall_score(synastry, zodiac_analysis)
        if overall_score >= 70:
            growth_factors["long_term_potential"] = "high"
        elif overall_score <= 40:
            growth_factors["long_term_potential"] = "low"
        
        return growth_factors

    def _create_fallback_report(
        self, person1: PartnerData, person2: PartnerData, compatibility_type: str
    ) -> Dict[str, Any]:
        """Создает базовый отчет при ошибках"""
        
        return {
            "overall_score": 50,
            "compatibility_type": compatibility_type,
            "synastry_analysis": {"aspects_count": 0, "compatibility_score": 50},
            "zodiac_analysis": {"score": 50, "description": "Базовый анализ недоступен"},
            "strengths": ["Потенциал для развития отношений"],
            "challenges": ["Недостаточно данных для детального анализа"],
            "advice": ["Узнайте друг друга лучше", "Найдите общие интересы"],
            "relationship_themes": ["Отношения в стадии изучения"],
            "growth_potential": {
                "learning_opportunities": ["Открытие новых граней партнера"],
                "development_areas": ["Все аспекты отношений"],
                "long_term_potential": "unknown",
            },
        }