"""
Advanced Astrological AI Service integrating Kerykeion precision with Yandex GPT intelligence.
Provides sophisticated astrological consultations using professional-grade calculations.
"""

import logging
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional

from app.core.config import settings
from app.models.yandex_models import YandexZodiacSign
from app.services.ai_content_filter import ContentSafetyLevel, ai_content_filter
from app.services.astrology_calculator import AstrologyCalculator
from app.services.enhanced_transit_service import EnhancedTransitService
from app.services.kerykeion_service import HouseSystem, KerykeionService, ZodiacType
from app.services.progression_service import ProgressionService
from app.services.synastry_service import SynastryService
from app.services.yandex_gpt import yandex_gpt_client

logger = logging.getLogger(__name__)


class ConsultationType(Enum):
    """Types of astrological consultations"""

    NATAL_CHART = "natal_chart"
    DAILY_FORECAST = "daily_forecast"
    COMPATIBILITY = "compatibility"
    CAREER_GUIDANCE = "career_guidance"
    LOVE_ANALYSIS = "love_analysis"
    HEALTH_ADVICE = "health_advice"
    FINANCIAL_GUIDANCE = "financial_guidance"
    TRANSIT_ANALYSIS = "transit_analysis"
    PROGRESSION_READING = "progression_reading"
    SPIRITUAL_GUIDANCE = "spiritual_guidance"


class AstroAIService:
    """Advanced Astrological AI Service using Kerykeion + Yandex GPT"""

    def __init__(self):
        self.kerykeion_service = KerykeionService()
        self.gpt_client = yandex_gpt_client
        self.astro_calculator = AstrologyCalculator()
        self.transit_service = EnhancedTransitService()
        self.progression_service = ProgressionService()
        self.synastry_service = SynastryService(self.astro_calculator)

        logger.info("ASTRO_AI_SERVICE_INIT: Service initialized")
        logger.info(
            f"ASTRO_AI_SERVICE_KERYKEION_AVAILABLE: {self.kerykeion_service.is_available()}"
        )

    async def generate_natal_interpretation(
        self,
        name: str,
        birth_date: date,
        birth_time: datetime,
        birth_place: Dict[str, float],
        timezone_str: str = "Europe/Moscow",
        house_system: HouseSystem = HouseSystem.PLACIDUS,
        zodiac_type: ZodiacType = ZodiacType.TROPICAL,
        consultation_focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive natal chart interpretation using Kerykeion + AI.

        Args:
            name: Person's name
            birth_date: Birth date
            birth_time: Birth time
            birth_place: Dict with latitude/longitude
            timezone_str: Timezone string
            house_system: House system to use
            zodiac_type: Zodiac type
            consultation_focus: Specific area of focus

        Returns:
            Complete natal chart interpretation
        """
        logger.info(
            f"ASTRO_AI_NATAL_START: {name}, focus={consultation_focus}"
        )

        try:
            # Get comprehensive natal chart data from Kerykeion
            chart_data = self.kerykeion_service.get_full_natal_chart_data(
                name=name,
                birth_datetime=birth_time,
                latitude=birth_place["latitude"],
                longitude=birth_place["longitude"],
                timezone=timezone_str,
                house_system=house_system,
                zodiac_type=zodiac_type,
            )

            if "error" in chart_data:
                logger.warning(
                    f"ASTRO_AI_NATAL_FALLBACK: Kerykeion error - {chart_data['error']}"
                )
                # Fallback to basic calculator
                chart_data = await self._get_fallback_chart_data(
                    name, birth_time, birth_place, timezone_str
                )

            # Enhance chart data with additional AI-friendly context
            enhanced_chart = await self._enhance_chart_for_ai(chart_data, consultation_focus)

            # Generate AI interpretation using enhanced data
            ai_interpretation = await self._generate_ai_natal_reading(
                name, enhanced_chart, consultation_focus
            )

            # Combine technical data with AI interpretation
            result = {
                "person_info": {
                    "name": name,
                    "birth_date": birth_date.isoformat(),
                    "birth_time": birth_time.isoformat(),
                    "birth_place": birth_place,
                    "timezone": timezone_str
                },
                "chart_data": chart_data,
                "enhanced_analysis": enhanced_chart,
                "ai_interpretation": ai_interpretation,
                "consultation_type": ConsultationType.NATAL_CHART.value,
                "service_info": {
                    "kerykeion_used": "error" not in chart_data,
                    "timestamp": datetime.now().isoformat()
                }
            }

            logger.info(f"ASTRO_AI_NATAL_SUCCESS: {name}")
            return result

        except Exception as e:
            logger.error(f"ASTRO_AI_NATAL_ERROR: {e}")
            return {"error": f"Natal interpretation failed: {str(e)}"}

    async def _enhance_chart_for_ai(
        self, chart_data: Dict[str, Any], focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhances chart data with AI-friendly analysis"""
        try:
            enhanced = {
                "planetary_strengths": self._analyze_planetary_strengths(chart_data),
                "dominant_elements": self._get_dominant_elements(chart_data),
                "key_aspects": self._identify_key_aspects(chart_data),
                "house_emphasis": self._analyze_house_emphasis(chart_data),
                "chart_patterns": self._identify_chart_patterns(chart_data),
                "life_themes": self._extract_life_themes(chart_data, focus)
            }

            # Add Arabic Parts analysis if available
            if self.kerykeion_service.is_available():
                subject = self._get_subject_from_chart_data(chart_data)
                if subject:
                    enhanced["arabic_parts"] = self.kerykeion_service.calculate_arabic_parts_extended(subject)

            return enhanced

        except Exception as e:
            logger.error(f"ASTRO_AI_ENHANCE_ERROR: {e}")
            return {}

    def _analyze_planetary_strengths(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes planetary strengths and dignities"""
        strengths = {}
        planets = chart_data.get("planets", {})

        dignity_scores = {
            # Traditional dignity scores for planets in signs
            "sun": {"Leo": 5, "Aries": 4, "Sagittarius": 3, "Libra": -2, "Aquarius": -2},
            "moon": {"Cancer": 5, "Taurus": 4, "Pisces": 3, "Capricorn": -2, "Scorpio": -2},
            "mercury": {"Gemini": 5, "Virgo": 5, "Aquarius": 3, "Pisces": -2, "Sagittarius": -2},
            "venus": {"Taurus": 5, "Libra": 5, "Pisces": 4, "Virgo": -2, "Aries": -2},
            "mars": {"Aries": 5, "Scorpio": 5, "Leo": 3, "Libra": -2, "Cancer": -2},
            "jupiter": {"Sagittarius": 5, "Pisces": 5, "Cancer": 4, "Gemini": -2, "Virgo": -2},
            "saturn": {"Capricorn": 5, "Aquarius": 5, "Libra": 4, "Cancer": -2, "Leo": -2}
        }

        for planet_name, planet_data in planets.items():
            if planet_name in dignity_scores:
                sign = planet_data.get("sign", "")
                # Convert English sign names to Russian for lookup
                sign_russian = self._get_russian_sign(sign)
                dignity_score = dignity_scores[planet_name].get(sign_russian, 0)
                
                # Factor in aspects and house position
                house = planet_data.get("house")
                house_strength = self._get_house_strength(planet_name, house)
                
                total_strength = dignity_score + house_strength
                strength_level = "weak"
                if total_strength >= 4:
                    strength_level = "very_strong"
                elif total_strength >= 2:
                    strength_level = "strong"
                elif total_strength >= 0:
                    strength_level = "moderate"

                strengths[planet_name] = {
                    "dignity_score": dignity_score,
                    "house_strength": house_strength,
                    "total_strength": total_strength,
                    "level": strength_level,
                    "sign": sign,
                    "house": house
                }

        return strengths

    def _get_house_strength(self, planet: str, house: Optional[int]) -> int:
        """Gets house strength for planet"""
        if not house:
            return 0
            
        # Traditional house strengths for planets
        house_strengths = {
            "sun": {1: 2, 5: 2, 9: 2, 10: 3, 11: 1},
            "moon": {1: 1, 4: 3, 7: 1, 10: 1},
            "mercury": {1: 1, 3: 2, 6: 1, 10: 2},
            "venus": {2: 2, 5: 2, 7: 2, 11: 1},
            "mars": {1: 2, 3: 1, 6: 1, 10: 2},
            "jupiter": {1: 1, 4: 1, 9: 3, 11: 2},
            "saturn": {6: 2, 8: 1, 10: 3, 12: 1}
        }
        
        return house_strengths.get(planet, {}).get(house, 0)

    def _get_dominant_elements(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes elemental balance"""
        element_dist = chart_data.get("element_distribution", {})
        quality_dist = chart_data.get("quality_distribution", {})
        
        total_planets = sum(element_dist.values()) if element_dist else 0
        if total_planets == 0:
            return {}

        # Calculate percentages and find dominant element/quality
        element_percentages = {elem: count/total_planets*100 for elem, count in element_dist.items()}
        quality_percentages = {qual: count/total_planets*100 for qual, count in quality_dist.items()}

        dominant_element = max(element_percentages, key=element_percentages.get) if element_percentages else None
        dominant_quality = max(quality_percentages, key=quality_percentages.get) if quality_percentages else None

        return {
            "element_distribution": element_percentages,
            "quality_distribution": quality_percentages,
            "dominant_element": dominant_element,
            "dominant_quality": dominant_quality,
            "element_balance": self._assess_elemental_balance(element_percentages)
        }

    def _assess_elemental_balance(self, element_percentages: Dict[str, float]) -> str:
        """Assesses the balance of elements"""
        if not element_percentages:
            return "unknown"
            
        values = list(element_percentages.values())
        max_val = max(values)
        min_val = min(values)
        
        if max_val > 60:
            return "heavily_imbalanced"
        elif max_val > 40:
            return "moderately_imbalanced"  
        elif max_val - min_val < 20:
            return "well_balanced"
        else:
            return "slightly_imbalanced"

    def _identify_key_aspects(self, chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifies the most important aspects"""
        aspects = chart_data.get("aspects", [])
        if not aspects:
            return []

        # Sort by strength and select top aspects
        key_aspects = []
        for aspect in aspects[:10]:  # Top 10 aspects
            if aspect.get("orb", 10) <= 6:  # Only tight aspects
                key_aspects.append({
                    "planets": f"{aspect.get('planet1', '')} - {aspect.get('planet2', '')}",
                    "aspect": aspect.get("aspect", ""),
                    "orb": aspect.get("orb", 0),
                    "strength": aspect.get("strength", ""),
                    "interpretation": aspect.get("interpretation", "")
                })

        return key_aspects

    def _analyze_house_emphasis(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes which houses are emphasized"""
        planets = chart_data.get("planets", {})
        house_counts = {}
        
        for planet_data in planets.values():
            house = planet_data.get("house")
            if house:
                house_counts[house] = house_counts.get(house, 0) + 1

        # Find emphasized houses (3+ planets)
        emphasized_houses = {house: count for house, count in house_counts.items() if count >= 2}
        
        return {
            "house_distribution": house_counts,
            "emphasized_houses": emphasized_houses,
            "most_emphasized": max(house_counts, key=house_counts.get) if house_counts else None
        }

    def _identify_chart_patterns(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identifies chart patterns"""
        # Use existing chart shape analysis
        chart_shape = chart_data.get("chart_shape", {})
        
        patterns = {
            "chart_shape": chart_shape.get("shape", "Unknown"),
            "shape_description": chart_shape.get("description", ""),
        }
        
        # Add stellium detection
        planets = chart_data.get("planets", {})
        patterns["stelliums"] = self._detect_stelliums(planets)
        
        return patterns

    def _detect_stelliums(self, planets: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detects stelliums (3+ planets in same sign or house)"""
        sign_groups = {}
        house_groups = {}
        
        for planet_name, planet_data in planets.items():
            sign = planet_data.get("sign")
            house = planet_data.get("house")
            
            if sign:
                if sign not in sign_groups:
                    sign_groups[sign] = []
                sign_groups[sign].append(planet_name)
                
            if house:
                if house not in house_groups:
                    house_groups[house] = []
                house_groups[house].append(planet_name)

        stelliums = []
        
        # Sign stelliums
        for sign, planets_list in sign_groups.items():
            if len(planets_list) >= 3:
                stelliums.append({
                    "type": "sign",
                    "location": sign,
                    "planets": planets_list,
                    "count": len(planets_list)
                })
                
        # House stelliums
        for house, planets_list in house_groups.items():
            if len(planets_list) >= 3:
                stelliums.append({
                    "type": "house",
                    "location": f"House {house}",
                    "planets": planets_list,
                    "count": len(planets_list)
                })
                
        return stelliums

    def _extract_life_themes(self, chart_data: Dict[str, Any], focus: Optional[str]) -> List[str]:
        """Extracts major life themes from chart"""
        themes = []
        
        # Based on dominant planets
        dominant_planets = chart_data.get("dominant_planets", [])
        for planet in dominant_planets[:2]:  # Top 2 dominant planets
            planet_themes = {
                "Sun": "самовыражение и лидерство",
                "Moon": "эмоции и интуиция", 
                "Mercury": "коммуникация и обучение",
                "Venus": "любовь и красота",
                "Mars": "действие и энергия",
                "Jupiter": "расширение и философия",
                "Saturn": "дисциплина и структура"
            }
            
            if planet in planet_themes:
                themes.append(planet_themes[planet])
        
        # Add focus-specific themes
        if focus:
            focus_themes = {
                "career": "профессиональная реализация",
                "love": "любовные отношения",
                "health": "здоровье и благополучие",
                "money": "финансовая стабильность",
                "spiritual": "духовное развитие"
            }
            if focus in focus_themes:
                themes.append(focus_themes[focus])
                
        return themes

    def _get_russian_sign(self, english_sign: str) -> str:
        """Converts English sign name to Russian"""
        sign_map = {
            "Aries": "Овен", "Taurus": "Телец", "Gemini": "Близнецы",
            "Cancer": "Рак", "Leo": "Лев", "Virgo": "Дева",
            "Libra": "Весы", "Scorpio": "Скорпион", "Sagittarius": "Стрелец",
            "Capricorn": "Козерог", "Aquarius": "Водолей", "Pisces": "Рыбы"
        }
        return sign_map.get(english_sign, english_sign)

    async def _generate_ai_natal_reading(
        self, name: str, enhanced_chart: Dict[str, Any], focus: Optional[str]
    ) -> Dict[str, Any]:
        """Generates AI interpretation using enhanced chart data"""
        try:
            # Create comprehensive prompt for Yandex GPT
            prompt = self._build_natal_prompt(name, enhanced_chart, focus)
            
            # Generate AI response
            ai_response = await self.gpt_client.generate_completion(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.7
            )
            
            if not ai_response or "error" in ai_response:
                logger.error("ASTRO_AI_GPT_ERROR: Failed to generate AI response")
                return {"error": "AI generation failed"}

            # Process and structure the response
            interpretation = {
                "summary": ai_response.get("text", "")[:800],  # Limit for Alice
                "key_insights": self._extract_key_insights(ai_response.get("text", "")),
                "recommendations": self._extract_recommendations(ai_response.get("text", "")),
                "focus_area": focus,
                "ai_confidence": ai_response.get("confidence", 0.8)
            }
            
            # Apply content filtering
            filtered_content = await ai_content_filter.filter_astrological_content(
                interpretation["summary"], ContentSafetyLevel.MODERATE
            )
            
            if filtered_content.get("is_safe", True):
                interpretation["summary"] = filtered_content.get("filtered_text", interpretation["summary"])
            else:
                logger.warning("ASTRO_AI_CONTENT_FILTERED: Unsafe content detected")
                interpretation["summary"] = "Астрологический анализ требует дополнительной проверки"

            return interpretation
            
        except Exception as e:
            logger.error(f"ASTRO_AI_READING_ERROR: {e}")
            return {"error": f"AI reading generation failed: {str(e)}"}

    def _build_natal_prompt(
        self, name: str, enhanced_chart: Dict[str, Any], focus: Optional[str]
    ) -> str:
        """Builds comprehensive prompt for natal chart AI interpretation"""
        prompt_parts = [
            f"Создай персональную астрологическую консультацию для {name}.",
            "Используй профессиональный, но дружелюбный тон.",
            ""
        ]
        
        # Add planetary strengths
        if "planetary_strengths" in enhanced_chart:
            strong_planets = [p for p, data in enhanced_chart["planetary_strengths"].items() 
                           if data.get("level") in ["strong", "very_strong"]]
            if strong_planets:
                prompt_parts.append(f"Сильные планеты в карте: {', '.join(strong_planets)}")
        
        # Add dominant elements
        if "dominant_elements" in enhanced_chart:
            dom_elem = enhanced_chart["dominant_elements"]
            if dom_elem.get("dominant_element"):
                prompt_parts.append(f"Доминирующий элемент: {dom_elem['dominant_element']}")
        
        # Add key aspects
        if "key_aspects" in enhanced_chart:
            key_aspects = enhanced_chart["key_aspects"][:3]  # Top 3
            if key_aspects:
                aspects_text = "; ".join([f"{asp['planets']} {asp['aspect']}" for asp in key_aspects])
                prompt_parts.append(f"Ключевые аспекты: {aspects_text}")
        
        # Add life themes
        if "life_themes" in enhanced_chart:
            themes = enhanced_chart["life_themes"][:3]  # Top 3
            if themes:
                prompt_parts.append(f"Основные темы жизни: {', '.join(themes)}")
                
        # Add focus area if specified
        if focus:
            focus_prompts = {
                "career": "Сосредоточься на карьере и профессиональной реализации.",
                "love": "Сделай акцент на любовных отношениях и партнерстве.",
                "health": "Обрати внимание на здоровье и жизненную энергию.",
                "money": "Проанализируй финансовые перспективы.",
                "spiritual": "Рассмотри духовный путь и личностный рост."
            }
            prompt_parts.append(focus_prompts.get(focus, ""))
            
        prompt_parts.extend([
            "",
            "Структура ответа:",
            "1. Краткая характеристика личности (2-3 предложения)",
            "2. Основные сильные стороны",
            "3. Области для развития", 
            "4. Рекомендации и советы",
            "",
            "Ограничь ответ 800 символами для голосового интерфейса."
        ])
        
        return "\n".join(prompt_parts)

    def _extract_key_insights(self, text: str) -> List[str]:
        """Extracts key insights from AI response"""
        # Simple extraction - could be enhanced with NLP
        sentences = text.split(".")
        insights = []
        
        for sentence in sentences[:5]:  # First 5 sentences
            sentence = sentence.strip()
            if len(sentence) > 20 and ("сильный" in sentence.lower() or "особенность" in sentence.lower()):
                insights.append(sentence + ".")
                
        return insights[:3]  # Top 3 insights

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extracts recommendations from AI response"""
        sentences = text.split(".")
        recommendations = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if ("рекомендует" in sentence.lower() or "совет" in sentence.lower() or 
                "стоит" in sentence.lower() or "полезно" in sentence.lower()):
                recommendations.append(sentence + ".")
                
        return recommendations[:3]  # Top 3 recommendations

    async def _get_fallback_chart_data(
        self, name: str, birth_time: datetime, birth_place: Dict[str, float], timezone: str
    ) -> Dict[str, Any]:
        """Gets basic chart data when Kerykeion fails"""
                )
                return await self._generate_basic_natal_interpretation(
                    name, birth_date, consultation_focus
                )

            # Calculate Arabic Parts if available
            subject = self.kerykeion_service.create_astrological_subject(
                name,
                birth_time,
                birth_place["latitude"],
                birth_place["longitude"],
                timezone_str,
                house_system,
                zodiac_type,
            )

            arabic_parts = {}
            if subject:
                arabic_parts = (
                    self.kerykeion_service.calculate_arabic_parts_extended(
                        subject
                    )
                )

            # Create sophisticated AI prompt with Kerykeion data
            ai_interpretation = await self._generate_natal_ai_analysis(
                chart_data, arabic_parts, consultation_focus
            )

            result = {
                "name": name,
                "birth_info": {
                    "date": birth_date.isoformat(),
                    "time": birth_time.isoformat(),
                    "place": birth_place,
                    "timezone": timezone_str,
                },
                "chart_data": chart_data,
                "arabic_parts": arabic_parts,
                "ai_interpretation": ai_interpretation,
                "consultation_type": ConsultationType.NATAL_CHART.value,
                "data_source": "kerykeion_enhanced",
                "generation_timestamp": datetime.now().isoformat(),
            }

            logger.info(f"ASTRO_AI_NATAL_SUCCESS: {name}")
            return result

        except Exception as e:
            logger.error(f"ASTRO_AI_NATAL_ERROR: {e}")
            return await self._generate_basic_natal_interpretation(
                name, birth_date, consultation_focus
            )

    async def generate_compatibility_analysis(
        self,
        person1_data: Dict[str, Any],
        person2_data: Dict[str, Any],
        relationship_type: str = "romantic",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate advanced compatibility analysis using Kerykeion synastry + AI.

        Args:
            person1_data: First person's data (name, birth info)
            person2_data: Second person's data
            relationship_type: Type of relationship
            context: Additional context

        Returns:
            Complete compatibility analysis
        """
        logger.info(f"ASTRO_AI_COMPATIBILITY_START: {relationship_type}")

        try:
            # Get full natal charts for both people
            chart1 = await self._get_or_calculate_natal_chart(person1_data)
            chart2 = await self._get_or_calculate_natal_chart(person2_data)

            if not chart1 or not chart2:
                logger.warning(
                    "ASTRO_AI_COMPATIBILITY_FALLBACK: Chart calculation failed"
                )
                return await self._generate_basic_compatibility(
                    person1_data, person2_data, relationship_type
                )

            # Calculate detailed synastry using Kerykeion
            if self.kerykeion_service.is_available():
                synastry_data = (
                    self.kerykeion_service.calculate_compatibility_detailed(
                        chart1, chart2
                    )
                )
            else:
                synastry_data = {"error": "Kerykeion unavailable"}

            # Generate AI-powered interpretation
            ai_analysis = await self._generate_synastry_ai_analysis(
                chart1, chart2, synastry_data, relationship_type, context
            )

            result = {
                "person1": person1_data["name"],
                "person2": person2_data["name"],
                "relationship_type": relationship_type,
                "chart_data": {
                    "person1_chart": chart1,
                    "person2_chart": chart2,
                    "synastry_analysis": synastry_data,
                },
                "ai_analysis": ai_analysis,
                "consultation_type": ConsultationType.COMPATIBILITY.value,
                "data_source": "kerykeion_synastry",
                "generation_timestamp": datetime.now().isoformat(),
            }

            logger.info("ASTRO_AI_COMPATIBILITY_SUCCESS")
            return result

        except Exception as e:
            logger.error(f"ASTRO_AI_COMPATIBILITY_ERROR: {e}")
            return await self._generate_basic_compatibility(
                person1_data, person2_data, relationship_type
            )

    async def generate_transit_forecast(
        self,
        natal_chart_data: Dict[str, Any],
        forecast_period: int = 30,
        focus_area: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate transit-based forecast using enhanced calculations + AI.

        Args:
            natal_chart_data: Natal chart data
            forecast_period: Days to forecast
            focus_area: Specific area of focus

        Returns:
            Transit forecast with AI interpretation
        """
        logger.info(
            f"ASTRO_AI_TRANSIT_START: period={forecast_period}, focus={focus_area}"
        )

        try:
            # Get enhanced transit data
            if self.kerykeion_service.is_available():
                current_transits = self.transit_service.get_current_transits(
                    natal_chart_data,
                    datetime.now(),
                    include_minor_aspects=True,
                )
                period_forecast = self.transit_service.get_period_forecast(
                    natal_chart_data, days=forecast_period
                )
                important_transits = (
                    self.transit_service.get_important_transits(
                        natal_chart_data,
                        lookback_days=7,
                        lookahead_days=forecast_period,
                    )
                )
            else:
                # Fallback to basic transit calculation
                current_transits = {"error": "Enhanced transits unavailable"}
                period_forecast = {}
                important_transits = {}

            # Generate AI interpretation
            ai_forecast = await self._generate_transit_ai_analysis(
                natal_chart_data,
                current_transits,
                period_forecast,
                important_transits,
                focus_area,
            )

            result = {
                "natal_data": natal_chart_data.get("subject_info", {}),
                "forecast_period": forecast_period,
                "focus_area": focus_area,
                "transit_data": {
                    "current_transits": current_transits,
                    "period_forecast": period_forecast,
                    "important_transits": important_transits,
                },
                "ai_forecast": ai_forecast,
                "consultation_type": ConsultationType.TRANSIT_ANALYSIS.value,
                "data_source": "enhanced_transits",
                "generation_timestamp": datetime.now().isoformat(),
            }

            logger.info("ASTRO_AI_TRANSIT_SUCCESS")
            return result

        except Exception as e:
            logger.error(f"ASTRO_AI_TRANSIT_ERROR: {e}")
            return {"error": f"Transit forecast failed: {str(e)}"}

    async def generate_personalized_advice(
        self,
        zodiac_sign: YandexZodiacSign,
        consultation_type: ConsultationType,
        user_context: Optional[Dict[str, Any]] = None,
        natal_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate personalized advice based on consultation type and available data.

        Args:
            zodiac_sign: User's zodiac sign
            consultation_type: Type of consultation
            user_context: User context data
            natal_data: Optional natal chart data

        Returns:
            Personalized advice
        """
        logger.info(
            f"ASTRO_AI_ADVICE_START: {zodiac_sign.value}, {consultation_type.value}"
        )

        try:
            # Create contextual prompt based on available data
            context = {
                "zodiac_sign": zodiac_sign.value,
                "consultation_type": consultation_type.value,
                "has_natal_data": natal_data is not None,
                "user_context": user_context or {},
            }

            # Generate specialized advice
            ai_advice = await self._generate_specialized_advice(
                consultation_type, context, natal_data
            )

            result = {
                "zodiac_sign": zodiac_sign.value,
                "consultation_type": consultation_type.value,
                "advice": ai_advice,
                "context_used": context,
                "data_source": "personalized_ai",
                "generation_timestamp": datetime.now().isoformat(),
            }

            logger.info(f"ASTRO_AI_ADVICE_SUCCESS: {consultation_type.value}")
            return result

        except Exception as e:
            logger.error(f"ASTRO_AI_ADVICE_ERROR: {e}")
            return {"error": f"Advice generation failed: {str(e)}"}

    # Private helper methods for AI prompt generation

    async def _generate_natal_ai_analysis(
        self,
        chart_data: Dict[str, Any],
        arabic_parts: Dict[str, Any],
        focus: Optional[str],
    ) -> Optional[str]:
        """Generate AI interpretation of natal chart data"""

        # Extract key chart elements
        sun = chart_data.get("planets", {}).get("sun", {})
        moon = chart_data.get("planets", {}).get("moon", {})
        ascendant = chart_data.get("angles", {}).get("ascendant", {})
        dominant_planets = chart_data.get("dominant_planets", [])
        chart_shape = chart_data.get("chart_shape", {})

        # Get strongest aspects
        aspects = chart_data.get("aspects", [])
        major_aspects = [
            asp
            for asp in aspects[:5]
            if asp.get("strength") in ["Very Strong", "Strong"]
        ]

        system_prompt = """Ты — профессиональный астролог с глубокими знаниями западной астрологии.
Создавай точные, проницательные интерпретации натальных карт на основе профессиональных астрологических данных.

Твои интерпретации должны быть:
- Психологически глубокими и проницательными
- Практически применимыми в жизни
- Написанными понятным, но профессиональным языком
- Сбалансированными (сильные стороны и области роста)
- Длиной 600-800 символов для голосового интерфейса

Используй традиционные астрологические знания, но адаптируй их для современного понимания."""

        prompt_parts = [
            "Проанализируй натальную карту со следующими данными:",
            "",
            f"Солнце в {sun.get('sign', 'неизвестно')} в {sun.get('house', '?')} доме",
            f"Луна в {moon.get('sign', 'неизвестно')} в {moon.get('house', '?')} доме",
            f"Асцендент в {ascendant.get('sign', 'неизвестно')}",
            "",
            f"Доминирующие планеты: {', '.join(dominant_planets[:3])}",
            f"Форма карты: {chart_shape.get('shape', 'неопределенная')}",
        ]

        if major_aspects:
            prompt_parts.extend(
                [
                    "",
                    "Ключевые аспекты:",
                    *[
                        f"- {asp['planet1']} {asp['aspect']} {asp['planet2']} ({asp['strength']})"
                        for asp in major_aspects[:3]
                    ],
                ]
            )

        if arabic_parts:
            parts_info = []
            for part_key, part_data in list(arabic_parts.items())[:2]:
                if isinstance(part_data, dict) and "name" in part_data:
                    parts_info.append(
                        f"- {part_data['name']} в {part_data.get('sign', 'неизвестно')}"
                    )

            if parts_info:
                prompt_parts.extend(["", "Арабские части:", *parts_info])

        if focus:
            prompt_parts.extend(["", f"Особое внимание уделить теме: {focus}"])

        prompt_parts.extend(
            [
                "",
                "Создай целостную характеристику личности с акцентом на:",
                "- Основные черты характера и мотивации",
                "- Таланты и способности",
                "- Жизненные задачи и пути развития",
                "- Практические рекомендации",
                "",
                "Используй профессиональную терминологию, но объясняй доступно.",
            ]
        )

        prompt = "\n".join(prompt_parts)

        raw_response = await self.gpt_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800,
        )

        if not raw_response:
            return None

        # Apply content filtering and safety validation
        validation = ai_content_filter.validate_content(
            raw_response, "general"
        )

        if validation["safety_level"] == ContentSafetyLevel.BLOCKED:
            logger.error(
                f"ASTRO_AI_NATAL_CONTENT_BLOCKED: {validation['issues']}"
            )
            return None

        # Use filtered content if available, otherwise original
        filtered_content = validation.get("filtered_content", raw_response)

        # Add disclaimer if needed
        if validation.get("needs_disclaimer", True):
            filtered_content = ai_content_filter.add_appropriate_disclaimer(
                filtered_content, "general"
            )

        logger.info(
            f"ASTRO_AI_NATAL_CONTENT_VALIDATED: safety={validation['safety_level'].value}, "
            f"quality={validation['quality_level'].value}"
        )

        return filtered_content

    async def _generate_synastry_ai_analysis(
        self,
        chart1: Dict[str, Any],
        chart2: Dict[str, Any],
        synastry_data: Dict[str, Any],
        relationship_type: str,
        context: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate AI analysis of synastry data"""

        system_prompt = """Ты — эксперт по астрологической совместимости с глубокими знаниями синастрии.
Анализируй совместимость пар на основе точных астрологических расчетов.

Твой анализ должен быть:
- Сбалансированным (сильные стороны и вызовы)
- Практичным (советы для улучшения отношений)
- Психологически глубоким
- Адаптированным под тип отношений
- Длиной 500-700 символов для голосового интерфейса

Используй профессиональную астрологическую терминологию, но объясняй доступно."""

        # Extract key synastry elements
        person1_sun = chart1.get("planets", {}).get("sun", {})
        person1_moon = chart1.get("planets", {}).get("moon", {})
        person2_sun = chart2.get("planets", {}).get("sun", {})
        person2_moon = chart2.get("planets", {}).get("moon", {})

        overall_score = synastry_data.get("overall_score", 50)
        sun_moon_connections = synastry_data.get("sun_moon_connections", [])
        venus_mars_connections = synastry_data.get(
            "venus_mars_connections", []
        )

        prompt_parts = [
            f"Проанализируй совместимость для {relationship_type} отношений:",
            "",
            f"Партнер 1: Солнце в {person1_sun.get('sign', '?')}, Луна в {person1_moon.get('sign', '?')}",
            f"Партнер 2: Солнце в {person2_sun.get('sign', '?')}, Луна в {person2_moon.get('sign', '?')}",
            "",
            f"Общая совместимость: {overall_score}%",
        ]

        if sun_moon_connections:
            prompt_parts.extend(
                [
                    "",
                    "Связи светил:",
                    *[
                        f"- {conn['connection']}: {conn['aspect']} (гармония: {conn.get('harmony_score', 0)})"
                        for conn in sun_moon_connections[:3]
                    ],
                ]
            )

        if venus_mars_connections:
            prompt_parts.extend(
                [
                    "",
                    "Романтические связи:",
                    *[
                        f"- {conn['connection']}: {conn['aspect']} (страсть: {conn.get('passion_score', 0)})"
                        for conn in venus_mars_connections[:3]
                    ],
                ]
            )

        if context and "challenges" in context:
            prompt_parts.append(f"\nТекущие вызовы: {context['challenges']}")

        prompt_parts.extend(
            [
                "",
                "Создай анализ, включающий:",
                "- Общую оценку совместимости",
                "- Сильные стороны союза",
                "- Потенциальные сложности",
                "- Практические советы для гармонии",
                "",
                "Будь конструктивным и поддерживающим.",
            ]
        )

        prompt = "\n".join(prompt_parts)

        return await self.gpt_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=700,
        )

    async def _generate_transit_ai_analysis(
        self,
        natal_data: Dict[str, Any],
        current_transits: Dict[str, Any],
        period_forecast: Dict[str, Any],
        important_transits: Dict[str, Any],
        focus_area: Optional[str],
    ) -> Optional[str]:
        """Generate AI analysis of transit data"""

        system_prompt = """Ты — опытный астролог-предсказатель, специализирующийся на транзитной астрологии.
Создавай точные прогнозы на основе текущих планетарных влияний и их взаимодействия с натальной картой.

Твои прогнозы должны быть:
- Основанными на реальных астрологических транзитах
- Практически применимыми
- Сбалансированными (возможности и вызовы)
- Содержащими конкретные временные рекомендации
- Длиной 600-800 символов для голосового интерфейса

Используй профессиональную транзитную терминологию, но объясняй доступно."""

        prompt_parts = ["Создай прогноз на основе текущих транзитов:", ""]

        # Add current transit information
        if not current_transits.get("error"):
            transits_list = current_transits.get("transits", [])[:3]
            if transits_list:
                prompt_parts.extend(
                    [
                        "Текущие транзиты:",
                        *[
                            f"- {transit.get('transiting_planet', '?')} {transit.get('aspect', '?')} "
                            f"натальная {transit.get('natal_planet', '?')}"
                            for transit in transits_list
                        ],
                    ]
                )

        # Add period forecast information
        if period_forecast.get("daily_forecasts"):
            upcoming_events = period_forecast.get("upcoming_key_transits", [])[
                :2
            ]
            if upcoming_events:
                prompt_parts.extend(
                    [
                        "",
                        "Предстоящие ключевые события:",
                        *[
                            f"- {event.get('date', '?')}: {event.get('description', '?')}"
                            for event in upcoming_events
                        ],
                    ]
                )

        # Add important transits
        if not important_transits.get("error"):
            major_transits = important_transits.get("major_transits", [])[:2]
            if major_transits:
                prompt_parts.extend(
                    [
                        "",
                        "Важные долгосрочные влияния:",
                        *[
                            f"- {transit.get('planet', '?')}: {transit.get('description', '?')}"
                            for transit in major_transits
                        ],
                    ]
                )

        if focus_area:
            prompt_parts.extend(["", f"Особое внимание области: {focus_area}"])

        prompt_parts.extend(
            [
                "",
                "Создай прогноз, включающий:",
                "- Общую энергетику периода",
                "- Ключевые возможности и вызовы",
                "- Рекомендации по планированию",
                "- Оптимальное время для важных решений",
                "",
                "Будь конкретным и практичным.",
            ]
        )

        prompt = "\n".join(prompt_parts)

        return await self.gpt_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800,
        )

    async def _generate_specialized_advice(
        self,
        consultation_type: ConsultationType,
        context: Dict[str, Any],
        natal_data: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate specialized advice based on consultation type"""

        type_prompts = {
            ConsultationType.CAREER_GUIDANCE: {
                "system": "Ты — астролог-консультант по карьере, помогающий людям найти профессиональное призвание.",
                "focus": "карьерные возможности, профессиональные таланты, оптимальные направления развития",
            },
            ConsultationType.LOVE_ANALYSIS: {
                "system": "Ты — эксперт по астрологии любви, помогающий в романтических вопросах.",
                "focus": "любовные перспективы, привлечение партнера, гармонию в отношениях",
            },
            ConsultationType.HEALTH_ADVICE: {
                "system": "Ты — астро-консультант по здоровью, дающий рекомендации на основе астрологических показаний.",
                "focus": "здоровье, жизненную энергию, профилактику, оптимальные периоды для восстановления",
            },
            ConsultationType.FINANCIAL_GUIDANCE: {
                "system": "Ты — астролог-консультант по финансам, помогающий в денежных вопросах.",
                "focus": "финансовые возможности, денежные потоки, инвестиционные периоды",
            },
            ConsultationType.SPIRITUAL_GUIDANCE: {
                "system": "Ты — духовный астролог, помогающий в вопросах личностного роста.",
                "focus": "духовное развитие, жизненные уроки, кармические задачи, медитативные практики",
            },
        }

        consultation_info = type_prompts.get(
            consultation_type,
            {
                "system": "Ты — профессиональный астролог-консультант.",
                "focus": "общие жизненные вопросы",
            },
        )

        system_prompt = f"""{consultation_info['system']}
Давай практические советы на основе астрологических принципов.

Твои советы должны быть:
- Конкретными и применимыми
- Основанными на астрологических закономерностях
- Вдохновляющими и поддерживающими
- Учитывающими текущие планетарные влияния
- Длиной 400-500 символов для голосового интерфейса

Используй знания астрологии, но объясняй доступно."""

        zodiac_sign = context.get("zodiac_sign", "неизвестный знак")

        prompt_parts = [
            f"Дай астрологический совет для {zodiac_sign}",
            f"по теме: {consultation_info['focus']}",
            "",
        ]

        # Add natal data context if available
        if natal_data and context.get("has_natal_data"):
            sun = natal_data.get("planets", {}).get("sun", {})
            moon = natal_data.get("planets", {}).get("moon", {})
            if sun.get("sign") and moon.get("sign"):
                prompt_parts.append(
                    f"Учитывая: Солнце в {sun['sign']}, Луна в {moon['sign']}"
                )

        # Add user context
        user_context = context.get("user_context", {})
        if user_context.get("mood"):
            prompt_parts.append(f"Настроение: {user_context['mood']}")
        if user_context.get("challenges"):
            prompt_parts.append(
                f"Текущие вызовы: {user_context['challenges']}"
            )

        prompt_parts.extend(
            [
                "",
                "Совет должен содержать:",
                "- Астрологическое обоснование",
                "- Конкретные действия",
                "- Оптимальное время для реализации",
                "- Поддерживающие слова",
                "",
                "Будь мудрым наставником.",
            ]
        )

        prompt = "\n".join(prompt_parts)

        raw_response = await self.gpt_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=500,
        )

        if not raw_response:
            return None

        # Apply content filtering with consultation type context
        consultation_type_mapping = {
            ConsultationType.CAREER_GUIDANCE: "карьера",
            ConsultationType.LOVE_ANALYSIS: "любовь",
            ConsultationType.HEALTH_ADVICE: "здоровье",
            ConsultationType.FINANCIAL_GUIDANCE: "финансы",
            ConsultationType.SPIRITUAL_GUIDANCE: "духовность",
        }

        filter_type = consultation_type_mapping.get(
            consultation_type, "general"
        )
        validation = ai_content_filter.validate_content(
            raw_response, filter_type
        )

        if validation["safety_level"] == ContentSafetyLevel.BLOCKED:
            logger.error(
                f"ASTRO_AI_SPECIALIZED_CONTENT_BLOCKED: {consultation_type.value}, {validation['issues']}"
            )
            return None

        # Use filtered content if available, otherwise original
        filtered_content = validation.get("filtered_content", raw_response)

        # Add appropriate disclaimer based on consultation type
        if validation.get("needs_disclaimer", True):
            filtered_content = ai_content_filter.add_appropriate_disclaimer(
                filtered_content, filter_type
            )

        logger.info(
            f"ASTRO_AI_SPECIALIZED_CONTENT_VALIDATED: type={consultation_type.value}, "
            f"safety={validation['safety_level'].value}, quality={validation['quality_level'].value}"
        )

        return filtered_content

    # Fallback methods for when Kerykeion is unavailable

    async def _get_or_calculate_natal_chart(
        self, person_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get or calculate natal chart data for a person"""
        if not person_data.get("birth_datetime") or not person_data.get(
            "birth_place"
        ):
            logger.warning("ASTRO_AI_INSUFFICIENT_DATA: Missing birth data")
            return None

        try:
            birth_datetime = datetime.fromisoformat(
                person_data["birth_datetime"]
            )
            birth_place = person_data["birth_place"]

            return self.kerykeion_service.get_full_natal_chart_data(
                name=person_data.get("name", "Unknown"),
                birth_datetime=birth_datetime,
                latitude=birth_place["latitude"],
                longitude=birth_place["longitude"],
                timezone=person_data.get("timezone", "Europe/Moscow"),
            )
        except Exception as e:
            logger.error(f"ASTRO_AI_CHART_CALC_ERROR: {e}")
            return None

    async def _generate_basic_natal_interpretation(
        self, name: str, birth_date: date, focus: Optional[str]
    ) -> Dict[str, Any]:
        """Generate basic natal interpretation without Kerykeion"""
        # Calculate zodiac sign from birth date
        zodiac_sign = self.astro_calculator.get_zodiac_sign_from_date(
            birth_date
        )

        # Generate basic AI interpretation
        system_prompt = """Ты — астролог, создающий базовые характеристики личности по знаку зодиака.
Используй классические астрологические знания для создания проницательного портрета."""

        prompt = f"""Создай астрологическую характеристику для {zodiac_sign}.
Дата рождения: {birth_date.strftime('%d %B %Y')}

{f'Особое внимание: {focus}' if focus else ''}

Включи:
- Основные черты характера
- Таланты и способности
- Жизненные задачи
- Практические рекомендации

Длина: 600-800 символов."""

        ai_interpretation = await self.gpt_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=800,
        )

        return {
            "name": name,
            "birth_info": {"date": birth_date.isoformat()},
            "zodiac_sign": zodiac_sign.value
            if hasattr(zodiac_sign, "value")
            else str(zodiac_sign),
            "ai_interpretation": ai_interpretation,
            "data_source": "basic_zodiac",
            "generation_timestamp": datetime.now().isoformat(),
        }

    async def _generate_basic_compatibility(
        self,
        person1_data: Dict[str, Any],
        person2_data: Dict[str, Any],
        relationship_type: str,
    ) -> Dict[str, Any]:
        """Generate basic compatibility without full charts"""
        # Extract zodiac signs or calculate from birth dates
        sign1 = person1_data.get("zodiac_sign")
        sign2 = person2_data.get("zodiac_sign")

        if not sign1 and person1_data.get("birth_date"):
            birth_date1 = date.fromisoformat(person1_data["birth_date"])
            sign1 = self.astro_calculator.get_zodiac_sign_from_date(
                birth_date1
            )

        if not sign2 and person2_data.get("birth_date"):
            birth_date2 = date.fromisoformat(person2_data["birth_date"])
            sign2 = self.astro_calculator.get_zodiac_sign_from_date(
                birth_date2
            )

        # Get basic compatibility score
        if hasattr(self.astro_calculator, "calculate_compatibility_score"):
            compatibility_data = (
                self.astro_calculator.calculate_compatibility_score(
                    sign1, sign2
                )
            )
        else:
            compatibility_data = {
                "total_score": 70,
                "description": "Средняя совместимость",
            }

        # Generate AI analysis
        ai_analysis = await self.gpt_client.generate_compatibility_analysis(
            sign1=str(sign1),
            sign2=str(sign2),
            context={"relationship_type": relationship_type},
        )

        return {
            "person1": person1_data.get("name", "Партнер 1"),
            "person2": person2_data.get("name", "Партнер 2"),
            "relationship_type": relationship_type,
            "zodiac_signs": [str(sign1), str(sign2)],
            "compatibility_score": compatibility_data.get("total_score", 70),
            "ai_analysis": ai_analysis,
            "data_source": "basic_signs",
            "generation_timestamp": datetime.now().isoformat(),
        }

    async def is_enhanced_features_available(self) -> Dict[str, bool]:
        """Check availability of enhanced features"""
        return {
            "kerykeion_service": self.kerykeion_service.is_available(),
            "enhanced_transits": self.transit_service is not None,
            "progressions": self.progression_service is not None,
            "synastry": self.synastry_service is not None,
            "yandex_gpt": await self.gpt_client.is_available()
            if settings.ENABLE_AI_GENERATION
            else False,
        }

    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        availability = await self.is_enhanced_features_available()

        return {
            "service_name": "AstroAIService",
            "version": "1.0.0",
            "initialization_time": datetime.now().isoformat(),
            "feature_availability": availability,
            "supported_consultations": [ct.value for ct in ConsultationType],
            "kerykeion_capabilities": self.kerykeion_service.get_service_capabilities()
            if self.kerykeion_service.is_available()
            else {},
            "ai_enabled": settings.ENABLE_AI_GENERATION,
            "status": "operational"
            if availability["kerykeion_service"] and availability["yandex_gpt"]
            else "limited",
        }


# Global service instance
astro_ai_service = AstroAIService()
