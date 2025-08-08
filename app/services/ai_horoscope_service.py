"""
AI-powered сервис генерации гороскопов с интеграцией Yandex GPT.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.models.yandex_models import YandexZodiacSign
from app.services.horoscope_generator import HoroscopeGenerator, HoroscopePeriod
from app.services.yandex_gpt import yandex_gpt_client


logger = logging.getLogger(__name__)


class AIHoroscopeService:
    """AI-powered сервис для генерации гороскопов."""

    def __init__(self):
        self.traditional_generator = HoroscopeGenerator()
        self.gpt_client = yandex_gpt_client

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
            target_date = datetime.now()
        
        # Если указана дата прогноза, используем её вместо target_date
        if forecast_date is not None:
            target_date = datetime.combine(forecast_date, datetime.min.time())

        # Получаем базовые астрологические данные
        base_horoscope = self.traditional_generator.generate_personalized_horoscope(
            zodiac_sign=zodiac_sign,
            birth_date=birth_date,
            birth_time=birth_time,
            period=period,
            target_date=target_date,
        )

        # Если AI включен и доступен, генерируем улучшенный контент
        logger.error(f"🔍 DEBUG: AI check - use_ai={use_ai}, enabled={settings.ENABLE_AI_GENERATION}")
        print(f"🔍 DEBUG: AI check - use_ai={use_ai}, enabled={settings.ENABLE_AI_GENERATION}")
        if use_ai and settings.ENABLE_AI_GENERATION:
            logger.info(f"AI_HOROSCOPE_GENERATION_START: sign={zodiac_sign}, period={period}")
            print(f"🔍 DEBUG: About to call _generate_ai_content")
            try:
                ai_enhanced = await self._generate_ai_content(
                    zodiac_sign=zodiac_sign,
                    period=period,
                    birth_date=birth_date,
                    base_data=base_horoscope,
                    forecast_date=forecast_date,
                )

                print(f"🔍 DEBUG: AI enhanced result: {ai_enhanced is not None}")
                if ai_enhanced:
                    logger.info(f"AI_HOROSCOPE_SUCCESS: Enhanced horoscope generated")
                    print(f"✅ DEBUG: Returning AI enhanced horoscope")
                    # Комбинируем традиционные данные с AI контентом
                    return self._merge_horoscope_data(base_horoscope, ai_enhanced)
                else:
                    logger.warning(f"AI_HOROSCOPE_EMPTY: AI returned empty result")
                    print(f"⚠️ DEBUG: AI returned None, falling back")

            except Exception as e:
                logger.error(f"AI_HOROSCOPE_ERROR: {e}", exc_info=True)
                print(f"❌ DEBUG: AI exception: {e}")
        else:
            logger.info(f"AI_HOROSCOPE_DISABLED: use_ai={use_ai}, enabled={settings.ENABLE_AI_GENERATION}")
            print(f"🚫 DEBUG: AI disabled, using traditional")

        # Fallback: возвращаем традиционный гороскоп
        print(f"🔄 DEBUG: Using traditional fallback")
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
        logger.info(f"AI_GENERATE_CONTENT_START: Calling Yandex GPT for {zodiac_sign.value}")
        logger.error(f"🔥 FORCE: About to call gpt_client.generate_horoscope")
        print(f"🔥 DEBUG: Calling generate_horoscope with context: {context}")
        ai_horoscope = await self.gpt_client.generate_horoscope(
            zodiac_sign=zodiac_sign.value,
            period=period.value,
            birth_date=birth_date.isoformat() if birth_date else None,
            forecast_date=forecast_date.strftime("%d %B %Y") if forecast_date else None,
            additional_context=context,
        )
        logger.error(f"🔥 FORCE: generate_horoscope returned: {ai_horoscope is not None}")
        print(f"🔥 DEBUG: AI horoscope result: {ai_horoscope[:100] if ai_horoscope else 'None'}")

        if not ai_horoscope:
            logger.warning(f"AI_GENERATE_CONTENT_FAILED: Yandex GPT returned None for {zodiac_sign.value}")
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
        merged.update({
            "ai_enhanced": True,
            "ai_generated": ai_data.get("ai_generated", True),
            "generation_method": ai_data.get("generation_method", "hybrid"),
            "ai_confidence": "high",
        })

        # Сохраняем традиционные данные в отдельном поле
        merged["traditional_data"] = {
            "spheres": base_data.get("spheres", {}),
            "energy_level": base_data.get("energy_level", {}),
            "lucky_numbers": base_data.get("lucky_numbers", []),
            "lucky_colors": base_data.get("lucky_colors", []),
            "astrological_influences": base_data.get("astrological_influences", {}),
        }

        return merged

    def _enhance_traditional_horoscope(
        self, base_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Улучшает традиционный гороскоп без AI."""

        enhanced = base_data.copy()
        enhanced.update({
            "ai_enhanced": False,
            "generation_method": "traditional",
            "fallback_reason": "ai_unavailable",
        })

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
        traditional_compatibility = self._get_traditional_compatibility(sign1, sign2)

        if use_ai and settings.ENABLE_AI_GENERATION:
            try:
                ai_analysis = await self.gpt_client.generate_compatibility_analysis(
                    sign1=sign1.value, sign2=sign2.value, context=context
                )

                if ai_analysis:
                    return {
                        "signs": [sign1.value, sign2.value],
                        "analysis": ai_analysis,
                        "traditional_score": traditional_compatibility["score"],
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
                    zodiac_sign=zodiac_sign.value, topic=topic, context=ai_context
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
        traditional_advice = self._generate_traditional_advice(zodiac_sign, topic)

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
        sign_data = self.traditional_generator.sign_characteristics.get(zodiac_sign, {})
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
            return (
                f"Сегодня особенно важно проявить вашу {keyword}. Доверьтесь интуиции."
            )

    async def check_ai_availability(self) -> bool:
        """Проверяет доступность AI сервисов."""
        try:
            return await self.gpt_client.is_available()
        except Exception as e:
            logger.error(f"AI availability check failed: {e}")
            return False


# Глобальный экземпляр сервиса
ai_horoscope_service = AIHoroscopeService()
