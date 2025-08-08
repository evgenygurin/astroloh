"""
Тесты для AI сервиса генерации гороскопов.
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.yandex_models import YandexZodiacSign
from app.services.ai_horoscope_service import AIHoroscopeService
from app.services.horoscope_generator import HoroscopePeriod


class TestAIHoroscopeService:
    """Тесты для AIHoroscopeService."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.service = AIHoroscopeService()

    @pytest.mark.asyncio
    async def test_generate_enhanced_horoscope_with_ai(self):
        """Тест генерации улучшенного гороскопа с AI."""
        # Mock настройки
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = True

            # Mock traditional generator
            mock_base_horoscope = {
                "general_forecast": "Базовый прогноз",
                "astrological_influences": {
                    "moon_phase": {"phase_name": "Полнолуние"},
                    "season_influence": {"season": "Весна"},
                },
                "energy_level": {"level": 75},
            }

            self.service.traditional_generator.generate_personalized_horoscope = MagicMock(
                return_value=mock_base_horoscope
            )

            # Mock AI client
            mock_ai_content = "AI сгенерированный прогноз"
            self.service.gpt_client.generate_horoscope = AsyncMock(
                return_value=mock_ai_content
            )

            result = await self.service.generate_enhanced_horoscope(
                zodiac_sign=YandexZodiacSign.ARIES,
                birth_date=date(1990, 5, 15),
                period=HoroscopePeriod.DAILY,
                use_ai=True,
            )

            assert result["ai_enhanced"] is True
            assert result["general_forecast"] == mock_ai_content
            assert result["generation_method"] == "hybrid"
            assert "traditional_data" in result

    @pytest.mark.asyncio
    async def test_generate_enhanced_horoscope_fallback(self):
        """Тест fallback к традиционному гороскопу."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = False

            mock_base_horoscope = {
                "general_forecast": "Традиционный прогноз",
                "spheres": {"love": "good"},
                "energy_level": {"level": 60},
            }

            self.service.traditional_generator.generate_personalized_horoscope = MagicMock(
                return_value=mock_base_horoscope
            )

            result = await self.service.generate_enhanced_horoscope(
                zodiac_sign=YandexZodiacSign.TAURUS, use_ai=True
            )

            assert result["ai_enhanced"] is False
            assert result["generation_method"] == "traditional"
            assert result["fallback_reason"] == "ai_unavailable"

    @pytest.mark.asyncio
    async def test_generate_enhanced_horoscope_ai_error(self):
        """Тест обработки ошибок AI."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = True

            mock_base_horoscope = {"general_forecast": "Базовый прогноз"}
            self.service.traditional_generator.generate_personalized_horoscope = MagicMock(
                return_value=mock_base_horoscope
            )

            # Mock AI client to raise exception
            self.service.gpt_client.generate_horoscope = AsyncMock(
                side_effect=Exception("AI API Error")
            )

            result = await self.service.generate_enhanced_horoscope(
                zodiac_sign=YandexZodiacSign.GEMINI, use_ai=True
            )

            assert result["ai_enhanced"] is False
            assert result["generation_method"] == "traditional"

    @pytest.mark.asyncio
    async def test_generate_compatibility_analysis_with_ai(self):
        """Тест анализа совместимости с AI."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = True

            mock_ai_analysis = "AI анализ совместимости"
            self.service.gpt_client.generate_compatibility_analysis = (
                AsyncMock(return_value=mock_ai_analysis)
            )

            result = await self.service.generate_compatibility_analysis(
                sign1=YandexZodiacSign.ARIES,
                sign2=YandexZodiacSign.LEO,
                use_ai=True,
            )

            assert result["ai_enhanced"] is True
            assert result["analysis"] == mock_ai_analysis
            assert result["generation_method"] == "yandex_gpt"
            assert result["signs"] == ["овен", "лев"]

    @pytest.mark.asyncio
    async def test_generate_compatibility_analysis_traditional(self):
        """Тест традиционного анализа совместимости."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = False

            result = await self.service.generate_compatibility_analysis(
                sign1=YandexZodiacSign.CANCER,
                sign2=YandexZodiacSign.SCORPIO,
                use_ai=True,
            )

            assert result["ai_enhanced"] is False
            assert result["generation_method"] == "traditional"
            assert "score" in result
            assert isinstance(result["score"], (int, float))

    @pytest.mark.asyncio
    async def test_generate_personalized_advice_with_ai(self):
        """Тест генерации персонализированного совета с AI."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = True

            mock_ai_advice = "AI персонализированный совет"
            self.service.gpt_client.generate_advice = AsyncMock(
                return_value=mock_ai_advice
            )

            result = await self.service.generate_personalized_advice(
                zodiac_sign=YandexZodiacSign.VIRGO,
                topic="карьера",
                user_context={"mood": "optimistic"},
                use_ai=True,
            )

            assert result["ai_enhanced"] is True
            assert result["advice"] == mock_ai_advice
            assert result["topic"] == "карьера"
            assert result["zodiac_sign"] == "дева"

    @pytest.mark.asyncio
    async def test_generate_personalized_advice_traditional(self):
        """Тест традиционного совета."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = False

            # Mock традиционного генератора
            mock_characteristics = {
                YandexZodiacSign.LIBRA: {"keywords": ["гармония", "баланс"]}
            }
            self.service.traditional_generator.sign_characteristics = (
                mock_characteristics
            )

            result = await self.service.generate_personalized_advice(
                zodiac_sign=YandexZodiacSign.LIBRA,
                topic="здоровье",
                use_ai=True,
            )

            assert result["ai_enhanced"] is False
            assert result["generation_method"] == "traditional"
            assert (
                "гармония" in result["advice"] or "баланс" in result["advice"]
            )

    def test_get_traditional_compatibility(self):
        """Тест получения традиционной совместимости."""
        result = self.service._get_traditional_compatibility(
            YandexZodiacSign.ARIES, YandexZodiacSign.SAGITTARIUS
        )

        assert "score" in result
        assert "description" in result
        assert isinstance(result["score"], (int, float))
        assert 0 <= result["score"] <= 100

    def test_generate_traditional_advice_topics(self):
        """Тест генерации традиционных советов по темам."""
        # Mock характеристик знака
        mock_characteristics = {
            YandexZodiacSign.SCORPIO: {
                "keywords": ["интенсивность", "страсть", "трансформация"]
            }
        }
        self.service.traditional_generator.sign_characteristics = (
            mock_characteristics
        )

        # Тест разных тем
        love_advice = self.service._generate_traditional_advice(
            YandexZodiacSign.SCORPIO, "любовь"
        )
        assert "любовных делах" in love_advice

        career_advice = self.service._generate_traditional_advice(
            YandexZodiacSign.SCORPIO, "карьера"
        )
        assert "профессиональной сфере" in career_advice

        health_advice = self.service._generate_traditional_advice(
            YandexZodiacSign.SCORPIO, "здоровье"
        )
        assert "здоровья" in health_advice

        general_advice = self.service._generate_traditional_advice(
            YandexZodiacSign.SCORPIO, None
        )
        assert len(general_advice) > 0

    def test_merge_horoscope_data(self):
        """Тест объединения данных гороскопа."""
        base_data = {
            "general_forecast": "Базовый прогноз",
            "spheres": {"love": "good"},
            "energy_level": {"level": 80},
            "lucky_numbers": [3, 7, 21],
        }

        ai_data = {
            "ai_generated": True,
            "general_forecast": "AI прогноз",
            "generation_method": "yandex_gpt",
        }

        result = self.service._merge_horoscope_data(base_data, ai_data)

        assert result["general_forecast"] == "AI прогноз"
        assert result["ai_enhanced"] is True
        assert result["generation_method"] == "yandex_gpt"
        assert "traditional_data" in result
        assert result["traditional_data"]["spheres"] == {"love": "good"}

    def test_enhance_traditional_horoscope(self):
        """Тест улучшения традиционного гороскопа."""
        base_data = {
            "general_forecast": "Традиционный прогноз",
            "spheres": {"career": "excellent"},
        }

        result = self.service._enhance_traditional_horoscope(base_data)

        assert result["ai_enhanced"] is False
        assert result["generation_method"] == "traditional"
        assert result["fallback_reason"] == "ai_unavailable"
        assert result["general_forecast"] == "Традиционный прогноз"

    @pytest.mark.asyncio
    async def test_check_ai_availability_success(self):
        """Тест успешной проверки доступности AI."""
        self.service.gpt_client.is_available = AsyncMock(return_value=True)

        result = await self.service.check_ai_availability()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_ai_availability_failure(self):
        """Тест неудачной проверки доступности AI."""
        self.service.gpt_client.is_available = AsyncMock(
            side_effect=Exception("Connection error")
        )

        result = await self.service.check_ai_availability()
        assert result is False

    @pytest.mark.asyncio
    async def test_ai_content_generation_none_result(self):
        """Тест обработки None результата от AI."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = True

            # Mock AI client to return None
            self.service.gpt_client.generate_horoscope = AsyncMock(
                return_value=None
            )

            result = await self.service._generate_ai_content(
                zodiac_sign=YandexZodiacSign.AQUARIUS,
                period=HoroscopePeriod.WEEKLY,
                birth_date=date(1985, 12, 1),
                base_data={"astrological_influences": {}},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_enhanced_horoscope_default_target_date(self):
        """Тест использования текущей даты по умолчанию."""
        with patch(
            "app.services.ai_horoscope_service.settings"
        ) as mock_settings:
            mock_settings.ENABLE_AI_GENERATION = False

            mock_base_horoscope = {"general_forecast": "Прогноз"}
            self.service.traditional_generator.generate_personalized_horoscope = MagicMock(
                return_value=mock_base_horoscope
            )

            with patch(
                "app.services.ai_horoscope_service.datetime"
            ) as mock_datetime:
                mock_now = datetime(2023, 6, 15, 12, 0)
                mock_datetime.now.return_value = mock_now

                await self.service.generate_enhanced_horoscope(
                    zodiac_sign=YandexZodiacSign.PISCES, target_date=None
                )

                # Проверяем, что traditional_generator был вызван с текущей датой
                call_args = (
                    self.service.traditional_generator.generate_personalized_horoscope.call_args
                )
                assert call_args[1]["target_date"] == mock_now
