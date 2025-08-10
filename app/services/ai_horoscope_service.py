"""
AI-powered сервис генерации гороскопов с интеграцией Yandex GPT.
Теперь интегрирован с AstroAIService для расширенных возможностей.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.models.yandex_models import YandexZodiacSign
from app.services.horoscope_generator import HoroscopeGenerator, HoroscopePeriod
from app.services.yandex_gpt import yandex_gpt_client
from app.utils.astro_time_utils import utcnow, current_timestamp

logger = logging.getLogger(__name__)


class AIHoroscopeService:
    """AI-powered сервис для генерации гороскопов."""

    def __init__(self):
        self.traditional_generator = HoroscopeGenerator()
        self.gpt_client = yandex_gpt_client

        # Lazy import to avoid circular dependencies
        self._astro_ai_service = None

    @property
    def astro_ai_service(self):
        """Lazy initialization of AstroAIService"""
        if self._astro_ai_service is None:
            try:
                from app.services.astro_ai_service import astro_ai_service

                self._astro_ai_service = astro_ai_service
            except ImportError as e:
                logger.warning(f"AstroAIService not available: {e}")
                self._astro_ai_service = None
        return self._astro_ai_service

    async def generate_enhanced_horoscope(
        self,
        zodiac_sign: YandexZodiacSign,
        birth_date: Optional[date] = None,
        birth_time: Optional[datetime] = None,
        period: HoroscopePeriod = HoroscopePeriod.DAILY,
        target_date: Optional[datetime] = None,
        forecast_date: Optional[date] = None,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Генерирует улучшенный гороскоп с использованием AI.

        Args:
            zodiac_sign: Знак зодиака
            birth_date: Дата рождения
            birth_time: Время рождения
            period: Период прогноза
            target_date: Целевая дата
            use_ai: Использовать ли AI генерацию

        Returns:
            Словарь с данными гороскопа
        """
        if target_date is None:
            target_date = utcnow()

        # Если указана дата прогноза, используем её вместо target_date
        if forecast_date is not None:
            target_date = datetime.combine(forecast_date, datetime.min.time())

        # Получаем базовые астрологические данные
        base_horoscope = (
            self.traditional_generator.generate_personalized_horoscope(
                zodiac_sign=zodiac_sign,
                birth_date=birth_date,
                birth_time=birth_time,
                period=period,
                target_date=target_date,
            )
        )

        # Если AI включен и доступен, генерируем улучшенный контент
        logger.error(
            f"🔍 DEBUG: AI check - use_ai={use_ai}, enabled={settings.ENABLE_AI_GENERATION}"
        )
        print(
            f"🔍 DEBUG: AI check - use_ai={use_ai}, enabled={settings.ENABLE_AI_GENERATION}"
        )
        if use_ai and settings.ENABLE_AI_GENERATION:
            logger.info(
                f"AI_HOROSCOPE_GENERATION_START: sign={zodiac_sign}, period={period}"
            )
            print("🔍 DEBUG: About to call _generate_ai_content")
            try:
                ai_enhanced = await self._generate_ai_content(
                    zodiac_sign=zodiac_sign,
                    period=period,
                    birth_date=birth_date,
                    base_data=base_horoscope,
                    forecast_date=forecast_date,
                )

                print(
                    f"🔍 DEBUG: AI enhanced result: {ai_enhanced is not None}"
                )
                if ai_enhanced:
                    logger.info(
                        "AI_HOROSCOPE_SUCCESS: Enhanced horoscope generated"
                    )
                    print("✅ DEBUG: Returning AI enhanced horoscope")
                    # Комбинируем традиционные данные с AI контентом
                    return self._merge_horoscope_data(
                        base_horoscope, ai_enhanced
                    )
                else:
                    logger.warning(
                        "AI_HOROSCOPE_EMPTY: AI returned empty result"
                    )
                    print("⚠️ DEBUG: AI returned None, falling back")

            except Exception as e:
                logger.error(f"AI_HOROSCOPE_ERROR: {e}", exc_info=True)
                print(f"❌ DEBUG: AI exception: {e}")
        else:
            logger.info(
                f"AI_HOROSCOPE_DISABLED: use_ai={use_ai}, enabled={settings.ENABLE_AI_GENERATION}"
            )
            print("🚫 DEBUG: AI disabled, using traditional")

        # Fallback: возвращаем традиционный гороскоп
        print("🔄 DEBUG: Using traditional fallback")
        return self._enhance_traditional_horoscope(base_horoscope)

    async def _generate_ai_content(
        self,
        zodiac_sign: YandexZodiacSign,
        period: HoroscopePeriod,
        birth_date: Optional[date],
        base_data: Dict[str, Any],
        forecast_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """Генерирует AI контент для гороскопа."""

        # Подготавливаем контекст для AI
        context = {
            "moon_phase": base_data.get("astrological_influences", {})
            .get("moon_phase", {})
            .get("phase_name"),
            "season": base_data.get("astrological_influences", {})
            .get("season_influence", {})
            .get("season"),
            "energy_level": base_data.get("energy_level", {}).get("level", 60),
        }

        # Генерируем основной гороскоп
        logger.info(
            f"AI_GENERATE_CONTENT_START: Calling Yandex GPT for {zodiac_sign.value}"
        )
        logger.error("🔥 FORCE: About to call gpt_client.generate_horoscope")
        print(f"🔥 DEBUG: Calling generate_horoscope with context: {context}")
        ai_horoscope = await self.gpt_client.generate_horoscope(
            zodiac_sign=zodiac_sign.value,
            period=period.value,
            birth_date=birth_date.isoformat() if birth_date else None,
            forecast_date=forecast_date.strftime("%d %B %Y")
            if forecast_date
            else None,
            additional_context=context,
        )
        logger.error(
            f"🔥 FORCE: generate_horoscope returned: {ai_horoscope is not None}"
        )
        print(
            f"🔥 DEBUG: AI horoscope result: {ai_horoscope[:100] if ai_horoscope else 'None'}"
        )

        if not ai_horoscope:
            logger.warning(
                f"AI_GENERATE_CONTENT_FAILED: Yandex GPT returned None for {zodiac_sign.value}"
            )
            return None

        return {
            "ai_generated": True,
            "general_forecast": ai_horoscope,
            "prediction": ai_horoscope,  # For backward compatibility
            "generation_method": "hybrid",
        }

    def _merge_horoscope_data(
        self, base_data: Dict[str, Any], ai_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Объединяет традиционные и AI данные."""

        merged = base_data.copy()

        # Заменяем основной прогноз на AI версию
        if "general_forecast" in ai_data:
            merged["general_forecast"] = ai_data["general_forecast"]
            merged["prediction"] = ai_data["general_forecast"]

        # Добавляем метаданные AI
        merged.update(
            {
                "ai_enhanced": True,
                "ai_generated": ai_data.get("ai_generated", True),
                "generation_method": ai_data.get(
                    "generation_method", "hybrid"
                ),
                "ai_confidence": "high",
            }
        )

        # Сохраняем традиционные данные в отдельном поле
        merged["traditional_data"] = {
            "spheres": base_data.get("spheres", {}),
            "energy_level": base_data.get("energy_level", {}),
            "lucky_numbers": base_data.get("lucky_numbers", []),
            "lucky_colors": base_data.get("lucky_colors", []),
            "astrological_influences": base_data.get(
                "astrological_influences", {}
            ),
        }

        return merged

    def _enhance_traditional_horoscope(
        self, base_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Улучшает традиционный гороскоп без AI."""

        enhanced = base_data.copy()
        enhanced.update(
            {
                "ai_enhanced": False,
                "generation_method": "traditional",
                "fallback_reason": "ai_unavailable",
            }
        )

        return enhanced

    async def generate_compatibility_analysis(
        self,
        sign1: YandexZodiacSign,
        sign2: YandexZodiacSign,
        context: Optional[Dict[str, Any]] = None,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Генерирует анализ совместимости с использованием AI.

        Args:
            sign1: Первый знак зодиака
            sign2: Второй знак зодиака
            context: Дополнительный контекст
            use_ai: Использовать ли AI

        Returns:
            Анализ совместимости
        """
        # Получаем традиционный анализ совместимости
        traditional_compatibility = self._get_traditional_compatibility(
            sign1, sign2
        )

        if use_ai and settings.ENABLE_AI_GENERATION:
            try:
                ai_analysis = (
                    await self.gpt_client.generate_compatibility_analysis(
                        sign1=sign1.value, sign2=sign2.value, context=context
                    )
                )

                if ai_analysis:
                    return {
                        "signs": [sign1.value, sign2.value],
                        "analysis": ai_analysis,
                        "traditional_score": traditional_compatibility[
                            "score"
                        ],
                        "ai_enhanced": True,
                        "generation_method": "yandex_gpt",
                    }

            except Exception as e:
                logger.error(f"AI compatibility analysis failed: {e}")

        # Fallback к традиционному анализу
        return {
            "signs": [sign1.value, sign2.value],
            "analysis": traditional_compatibility["description"],
            "score": traditional_compatibility["score"],
            "ai_enhanced": False,
            "generation_method": "traditional",
        }

    def _get_traditional_compatibility(
        self, sign1: YandexZodiacSign, sign2: YandexZodiacSign
    ) -> Dict[str, Any]:
        """Получает традиционный анализ совместимости."""

        # Используем astrology calculator для получения базового скора
        from app.services.astrology_calculator import AstrologyCalculator

        calc = AstrologyCalculator()

        compatibility_score = calc.calculate_compatibility_score(sign1, sign2)

        return {
            "score": compatibility_score.get("total_score", 70),
            "description": compatibility_score.get(
                "description", "Умеренная совместимость"
            ),
        }

    async def generate_personalized_advice(
        self,
        zodiac_sign: YandexZodiacSign,
        topic: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Генерирует персонализированный совет.

        Args:
            zodiac_sign: Знак зодиака
            topic: Тема совета
            user_context: Пользовательский контекст
            use_ai: Использовать ли AI

        Returns:
            Персонализированный совет
        """
        if use_ai and settings.ENABLE_AI_GENERATION:
            try:
                # Подготавливаем контекст для AI
                ai_context = {}
                if user_context:
                    if "mood" in user_context:
                        ai_context["mood"] = user_context["mood"]
                    if "recent_challenges" in user_context:
                        ai_context["current_challenges"] = user_context[
                            "recent_challenges"
                        ]

                ai_advice = await self.gpt_client.generate_advice(
                    zodiac_sign=zodiac_sign.value,
                    topic=topic,
                    context=ai_context,
                )

                if ai_advice:
                    return {
                        "zodiac_sign": zodiac_sign.value,
                        "topic": topic or "общий",
                        "advice": ai_advice,
                        "ai_enhanced": True,
                        "generation_method": "yandex_gpt",
                    }

            except Exception as e:
                logger.error(f"AI advice generation failed: {e}")

        # Fallback к традиционному совету
        traditional_advice = self._generate_traditional_advice(
            zodiac_sign, topic
        )

        return {
            "zodiac_sign": zodiac_sign.value,
            "topic": topic or "общий",
            "advice": traditional_advice,
            "ai_enhanced": False,
            "generation_method": "traditional",
        }

    def _generate_traditional_advice(
        self, zodiac_sign: YandexZodiacSign, topic: Optional[str]
    ) -> str:
        """Генерирует традиционный совет."""

        # Получаем характеристики знака
        sign_data = self.traditional_generator.sign_characteristics.get(
            zodiac_sign, {}
        )
        keywords = sign_data.get("keywords", ["гармония", "развитие"])

        import random

        keyword = random.choice(keywords)

        if topic == "любовь":
            return f"В любовных делах проявите вашу природную {keyword}. Звезды благоволят искренности."
        elif topic == "карьера":
            return f"В профессиональной сфере используйте вашу {keyword}. Время для новых инициатив."
        elif topic == "здоровье":
            return f"Для здоровья важна ваша способность к {keyword}. Слушайте сигналы тела."
        else:
            return f"Сегодня особенно важно проявить вашу {keyword}. Доверьтесь интуиции."

    async def generate_natal_chart_interpretation(
        self,
        name: str,
        birth_date: date,
        birth_time: datetime,
        birth_place: Dict[str, float],
        timezone_str: str = "Europe/Moscow",
        focus_area: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует интерпретацию натальной карты с использованием Kerykeion + AI.

        Args:
            name: Имя человека
            birth_date: Дата рождения
            birth_time: Время рождения
            birth_place: Место рождения (latitude, longitude)
            timezone_str: Часовой пояс
            focus_area: Область фокусировки

        Returns:
            Интерпретация натальной карты
        """
        logger.info(
            f"AI_NATAL_INTERPRETATION_START: {name}, focus={focus_area}"
        )

        if self.astro_ai_service and settings.ENABLE_AI_GENERATION:
            try:
                from app.services.astro_ai_service import HouseSystem, ZodiacType

                result = (
                    await self.astro_ai_service.generate_natal_interpretation(
                        name=name,
                        birth_date=birth_date,
                        birth_time=birth_time,
                        birth_place=birth_place,
                        timezone_str=timezone_str,
                        house_system=HouseSystem.PLACIDUS,
                        zodiac_type=ZodiacType.TROPICAL,
                        consultation_focus=focus_area,
                    )
                )

                logger.info(
                    "AI_NATAL_INTERPRETATION_SUCCESS: Enhanced interpretation generated"
                )
                return result

            except Exception as e:
                logger.error(f"AI_NATAL_INTERPRETATION_ERROR: {e}")

        # Fallback to basic interpretation
        return await self._generate_basic_natal_fallback(
            name, birth_date, focus_area
        )

    async def generate_enhanced_compatibility_analysis(
        self,
        person1_data: Dict[str, Any],
        person2_data: Dict[str, Any],
        relationship_type: str = "романтические",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует улучшенный анализ совместимости с использованием синастрии.

        Args:
            person1_data: Данные первого человека
            person2_data: Данные второго человека
            relationship_type: Тип отношений
            context: Дополнительный контекст

        Returns:
            Анализ совместимости
        """
        logger.info(f"AI_ENHANCED_COMPATIBILITY_START: {relationship_type}")

        if self.astro_ai_service and settings.ENABLE_AI_GENERATION:
            try:
                result = await self.astro_ai_service.generate_compatibility_analysis(
                    person1_data=person1_data,
                    person2_data=person2_data,
                    relationship_type=relationship_type,
                    context=context,
                )

                logger.info(
                    "AI_ENHANCED_COMPATIBILITY_SUCCESS: Advanced analysis generated"
                )
                return result

            except Exception as e:
                logger.error(f"AI_ENHANCED_COMPATIBILITY_ERROR: {e}")

        # Fallback to existing compatibility method
        sign1 = YandexZodiacSign(person1_data.get("zodiac_sign", "лев"))
        sign2 = YandexZodiacSign(person2_data.get("zodiac_sign", "дева"))

        return await self.generate_compatibility_analysis(
            sign1=sign1, sign2=sign2, context=context, use_ai=True
        )

    async def generate_transit_forecast_analysis(
        self,
        zodiac_sign: YandexZodiacSign,
        birth_date: Optional[date] = None,
        birth_time: Optional[datetime] = None,
        birth_place: Optional[Dict[str, float]] = None,
        forecast_period: int = 30,
        focus_area: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует прогноз на основе транзитов с использованием AI.

        Args:
            zodiac_sign: Знак зодиака
            birth_date: Дата рождения (для точных расчетов)
            birth_time: Время рождения
            birth_place: Место рождения
            forecast_period: Период прогноза в днях
            focus_area: Область фокусировки

        Returns:
            Прогноз на основе транзитов
        """
        logger.info(
            f"AI_TRANSIT_FORECAST_START: {zodiac_sign.value}, period={forecast_period}"
        )

        if self.astro_ai_service and settings.ENABLE_AI_GENERATION:
            try:
                # If we have full birth data, use enhanced analysis
                if birth_date and birth_time and birth_place:
                    from app.services.astro_ai_service import HouseSystem, ZodiacType

                    # Get natal chart first
                    natal_data = self.astro_ai_service.kerykeion_service.get_full_natal_chart_data(
                        name="User",
                        birth_datetime=birth_time,
                        latitude=birth_place["latitude"],
                        longitude=birth_place["longitude"],
                        timezone="Europe/Moscow",
                        house_system=HouseSystem.PLACIDUS,
                        zodiac_type=ZodiacType.TROPICAL,
                    )

                    if not natal_data.get("error"):
                        result = await self.astro_ai_service.generate_transit_forecast(
                            natal_chart_data=natal_data,
                            forecast_period=forecast_period,
                            focus_area=focus_area,
                        )

                        logger.info(
                            "AI_TRANSIT_FORECAST_SUCCESS: Enhanced forecast generated"
                        )
                        return result

                # Fallback to basic sign-based forecast
                from app.services.astro_ai_service import ConsultationType

                result = (
                    await self.astro_ai_service.generate_personalized_advice(
                        zodiac_sign=zodiac_sign,
                        consultation_type=ConsultationType.TRANSIT_ANALYSIS,
                        user_context={
                            "focus_area": focus_area,
                            "period": forecast_period,
                        },
                    )
                )

                logger.info(
                    "AI_TRANSIT_FORECAST_SUCCESS: Basic forecast generated"
                )
                return result

            except Exception as e:
                logger.error(f"AI_TRANSIT_FORECAST_ERROR: {e}")

        # Fallback to traditional enhanced horoscope
        return await self.generate_enhanced_horoscope(
            zodiac_sign=zodiac_sign,
            birth_date=birth_date,
            birth_time=birth_time,
            period=HoroscopePeriod.MONTHLY
            if forecast_period > 7
            else HoroscopePeriod.DAILY,
            use_ai=True,
        )

    async def generate_specialized_consultation(
        self,
        zodiac_sign: YandexZodiacSign,
        consultation_type: str,
        user_context: Optional[Dict[str, Any]] = None,
        birth_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Генерирует специализированную консультацию по определенной теме.

        Args:
            zodiac_sign: Знак зодиака
            consultation_type: Тип консультации (карьера, любовь, здоровье, финансы)
            user_context: Пользовательский контекст
            birth_data: Данные о рождении

        Returns:
            Специализированная консультация
        """
        logger.info(
            f"AI_SPECIALIZED_CONSULTATION_START: {zodiac_sign.value}, type={consultation_type}"
        )

        if self.astro_ai_service and settings.ENABLE_AI_GENERATION:
            try:
                from app.services.astro_ai_service import ConsultationType

                # Map consultation types
                consultation_map = {
                    "карьера": ConsultationType.CAREER_GUIDANCE,
                    "любовь": ConsultationType.LOVE_ANALYSIS,
                    "здоровье": ConsultationType.HEALTH_ADVICE,
                    "финансы": ConsultationType.FINANCIAL_GUIDANCE,
                    "духовность": ConsultationType.SPIRITUAL_GUIDANCE,
                    "развитие": ConsultationType.SPIRITUAL_GUIDANCE,
                }

                consultation_enum = consultation_map.get(
                    consultation_type.lower(), ConsultationType.CAREER_GUIDANCE
                )

                # Get natal data if available
                natal_data = None
                if (
                    birth_data
                    and birth_data.get("birth_date")
                    and birth_data.get("birth_time")
                    and birth_data.get("birth_place")
                ):
                    try:
                        natal_data = self.astro_ai_service.kerykeion_service.get_full_natal_chart_data(
                            name=birth_data.get("name", "User"),
                            birth_datetime=birth_data["birth_time"],
                            latitude=birth_data["birth_place"]["latitude"],
                            longitude=birth_data["birth_place"]["longitude"],
                            timezone=birth_data.get(
                                "timezone", "Europe/Moscow"
                            ),
                        )
                        if natal_data.get("error"):
                            natal_data = None
                    except Exception as e:
                        logger.warning(f"AI_SPECIALIZED_NATAL_DATA_ERROR: {e}")
                        natal_data = None

                result = (
                    await self.astro_ai_service.generate_personalized_advice(
                        zodiac_sign=zodiac_sign,
                        consultation_type=consultation_enum,
                        user_context=user_context,
                        natal_data=natal_data,
                    )
                )

                logger.info(
                    f"AI_SPECIALIZED_CONSULTATION_SUCCESS: {consultation_type}"
                )
                return result

            except Exception as e:
                logger.error(f"AI_SPECIALIZED_CONSULTATION_ERROR: {e}")

        # Fallback to existing advice generation
        return await self.generate_personalized_advice(
            zodiac_sign=zodiac_sign,
            topic=consultation_type,
            user_context=user_context,
            use_ai=True,
        )

    async def get_enhanced_service_status(self) -> Dict[str, Any]:
        """
        Получает статус расширенного сервиса.

        Returns:
            Статус сервиса с информацией о возможностях
        """
        status = {
            "ai_horoscope_service": True,
            "yandex_gpt_available": await self.check_ai_availability(),
            "astro_ai_service_available": self.astro_ai_service is not None,
            "enhanced_features": {},
        }

        if self.astro_ai_service:
            try:
                enhanced_status = (
                    await self.astro_ai_service.get_service_status()
                )
                status["enhanced_features"] = enhanced_status
            except Exception as e:
                logger.error(f"AI_SERVICE_STATUS_ERROR: {e}")
                status["enhanced_features"] = {"error": str(e)}

        return status

    async def _generate_basic_natal_fallback(
        self, name: str, birth_date: date, focus_area: Optional[str]
    ) -> Dict[str, Any]:
        """Базовая интерпретация натальной карты без Kerykeion"""
        from app.services.astrology_calculator import AstrologyCalculator

        calc = AstrologyCalculator()
        zodiac_sign = calc.get_zodiac_sign_from_date(birth_date)

        # Generate AI interpretation based on zodiac sign
        topic = focus_area or "характер"
        advice = await self.generate_personalized_advice(
            zodiac_sign=zodiac_sign,
            topic=f"натальная карта с фокусом на {topic}",
            user_context={"birth_date": birth_date.isoformat()},
            use_ai=True,
        )

        return {
            "name": name,
            "birth_info": {"date": birth_date.isoformat()},
            "zodiac_sign": zodiac_sign.value,
            "interpretation": advice.get(
                "advice", "Характеристика недоступна"
            ),
            "data_source": "basic_fallback",
            "generation_timestamp": current_timestamp(),
        }

    async def check_ai_availability(self) -> bool:
        """Проверяет доступность AI сервисов."""
        try:
            return await self.gpt_client.is_available()
        except Exception as e:
            logger.error(f"AI availability check failed: {e}")
            return False


# Глобальный экземпляр сервиса
ai_horoscope_service = AIHoroscopeService()
