"""
Comprehensive integration tests for Yandex Alice voice interface.
Tests webhook processing, intent recognition, AI generation, and voice-optimized responses.
"""

from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from app.api.yandex_dialogs import yandex_webhook
from app.models.yandex_models import YandexZodiacSign
from app.services.ai_horoscope_service import AIHoroscopeService
from app.services.intent_recognition import IntentRecognizer, YandexIntent
from app.services.yandex_gpt import YandexGPTClient


class AliceTestData:
    """Test data for Alice voice interface testing"""

    # Standard Alice request format
    ALICE_REQUEST_TEMPLATE = {
        "meta": {
            "locale": "ru-RU",
            "timezone": "Europe/Moscow",
            "client_id": "alice/test",
            "interfaces": {
                "screen": {},
                "payments": {},
                "account_linking": {},
            },
        },
        "session": {
            "message_id": 1,
            "session_id": "test_session_123",
            "skill_id": "astroloh_skill",
            "user_id": "alice_user_456",
            "user": {"user_id": "alice_user_456"},
            "application": {"application_id": "alice_app_789"},
            "new": False,
        },
        "request": {
            "command": "",
            "original_utterance": "",
            "type": "SimpleUtterance",
            "markup": {"dangerous_context": False},
            "payload": {},
            "nlu": {"tokens": [], "entities": [], "intents": {}},
        },
        "version": "1.0",
    }

    # Voice commands to test
    VOICE_COMMANDS = {
        "greetings": [
            "привет",
            "здравствуй",
            "добро утро",
            "добрый день",
            "алиса помоги с астрологией",
        ],
        "horoscopes": [
            "дай гороскоп для льва",
            "гороскоп овна на сегодня",
            "расскажи про гороскоп",
            "что говорят звезды льву",
        ],
        "compatibility": [
            "совместимость льва и овна",
            "подходит ли дева скорпиону",
            "совместимость знаков",
            "синастрия",
        ],
        "transits": [
            "что меня ждет сегодня",
            "покажи транзиты",
            "прогноз на неделю",
            "важные транзиты",
        ],
        "ai_features": [
            "интерпретация натальной карты",
            "карьерный совет",
            "любовная консультация",
            "духовная консультация",
        ],
        "help": ["помощь", "что ты умеешь", "список команд", "возможности"],
    }


@pytest.mark.integration
class TestAliceWebhookIntegration:
    """Test complete webhook processing pipeline"""

    def create_alice_request(
        self, command: str, utterance: str = None
    ) -> Dict[str, Any]:
        """Create Alice request with specified command"""
        request = AliceTestData.ALICE_REQUEST_TEMPLATE.copy()
        request["request"]["command"] = command
        request["request"]["original_utterance"] = utterance or command
        request["request"]["nlu"]["tokens"] = command.split()
        return request

    @pytest.mark.asyncio
    async def test_webhook_greeting_flow(self):
        """Test complete greeting flow through webhook"""
        for greeting in AliceTestData.VOICE_COMMANDS["greetings"][:2]:
            alice_request = self.create_alice_request(greeting)

            # Mock dependencies
            with patch("app.core.database.get_database") as mock_db, patch(
                "app.services.session_manager.SessionManager"
            ) as mock_session_mgr:
                mock_db.return_value.__aenter__.return_value = AsyncMock()
                mock_session_mgr.return_value.get_user_context = AsyncMock(
                    return_value=None
                )
                mock_session_mgr.return_value.update_user_context = AsyncMock()

                # Convert dict to YandexRequestModel
                from app.models.yandex_models import YandexRequestModel

                alice_request_model = YandexRequestModel(**alice_request)
                response = await yandex_webhook(alice_request_model)

                # Should return valid Alice response (YandexResponseModel)
                assert hasattr(response, "response")
                assert hasattr(response.response, "text")
                assert response.response.text
                assert hasattr(response.response, "tts")
                assert response.version == "1.0"

                # Response should be greeting
                response_text = response.response.text.lower()
                greeting_indicators = [
                    "привет",
                    "добро пожаловать",
                    "здравствуй",
                    "рад",
                    "астролог",
                    "возвращением",
                    "интересует",
                ]
                # Debug: print response to see what we got
                print(f"Response text: '{response_text}'")
                assert any(
                    indicator in response_text
                    for indicator in greeting_indicators
                ), f"No greeting indicators found in: {response_text}"

    @pytest.mark.asyncio
    async def test_webhook_horoscope_flow(self):
        """Test complete horoscope generation flow"""
        for horoscope_cmd in AliceTestData.VOICE_COMMANDS["horoscopes"][:2]:
            alice_request = self.create_alice_request(horoscope_cmd)

            with patch(
                "app.api.yandex_dialogs.get_database_session"
            ) as mock_db, patch(
                "app.services.session_manager.SessionManager"
            ) as mock_session_mgr, patch(
                "app.services.horoscope_generator.HoroscopeGenerator"
            ) as mock_horoscope:
                mock_db.return_value.__aenter__.return_value = AsyncMock()
                mock_session_mgr.return_value.get_user_context = AsyncMock(
                    return_value=None
                )
                mock_session_mgr.return_value.update_user_context = AsyncMock()

                # Mock horoscope generation
                mock_horoscope.return_value.generate_horoscope = AsyncMock(
                    return_value={
                        "prediction": "Отличный день для новых начинаний!",
                        "energy_level": 85,
                        "lucky_numbers": [7, 14, 21],
                        "lucky_color": "золотой",
                    }
                )

                response = await yandex_webhook(alice_request)

                # Should return horoscope response
                assert "response" in response
                response_text = response["response"]["text"]

                # Should contain horoscope content
                assert len(response_text) > 50  # Substantial content
                assert len(response_text) <= 800  # Alice TTS limit

                # Should be in Russian
                russian_indicators = ["день", "звезды", "прогноз", "удача"]
                assert any(
                    indicator in response_text.lower()
                    for indicator in russian_indicators
                )

    @pytest.mark.asyncio
    async def test_webhook_compatibility_flow(self):
        """Test complete compatibility analysis flow"""
        compatibility_cmd = "совместимость льва и овна"
        alice_request = self.create_alice_request(compatibility_cmd)

        with patch(
            "app.api.yandex_dialogs.get_database_session"
        ) as mock_db, patch(
            "app.services.session_manager.SessionManager"
        ) as mock_session_mgr, patch(
            "app.services.compatibility_analyzer.CompatibilityAnalyzer"
        ) as mock_compat:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            mock_session_mgr.return_value.get_user_context = AsyncMock(
                return_value=None
            )
            mock_session_mgr.return_value.update_user_context = AsyncMock()

            # Mock compatibility analysis
            mock_compat.return_value.analyze_compatibility = AsyncMock(
                return_value={
                    "score": 88,
                    "description": "Отличная совместимость!",
                    "strengths": ["энергия", "лидерство", "взаимопонимание"],
                    "challenges": ["упрямство", "соревновательность"],
                    "advice": "Больше компромиссов в отношениях",
                }
            )

            response = await yandex_webhook(alice_request)

            # Should return compatibility response
            assert "response" in response
            response_text = response["response"]["text"]

            # Should contain compatibility analysis
            compatibility_indicators = [
                "совместимость",
                "отношения",
                "пара",
                "%",
            ]
            assert any(
                indicator in response_text.lower()
                for indicator in compatibility_indicators
            )

            # Should respect character limit
            assert len(response_text) <= 600  # Compatibility limit

    @pytest.mark.asyncio
    async def test_webhook_error_handling(self):
        """Test webhook error handling and fallbacks"""
        alice_request = self.create_alice_request("сломанная команда")

        with patch("app.api.yandex_dialogs.get_database_session") as mock_db:
            mock_db.return_value.__aenter__.return_value = AsyncMock()

            # Simulate database error
            mock_db.side_effect = Exception("Database connection failed")

            response = await yandex_webhook(alice_request)

            # Should still return valid response (error handling)
            assert "response" in response
            assert "text" in response["response"]
            assert not response["response"]["end_session"]

            # Error message should be user-friendly
            error_text = response["response"]["text"].lower()
            harsh_errors = ["exception", "traceback", "error", "failed"]
            assert not any(
                harsh_error in error_text for harsh_error in harsh_errors
            )


@pytest.mark.integration
class TestIntentRecognitionIntegration:
    """Test intent recognition with Alice voice patterns"""

    @pytest.fixture
    def intent_recognizer(self):
        return IntentRecognizer()

    def test_horoscope_intent_recognition(self, intent_recognizer):
        """Test horoscope intent recognition accuracy"""
        horoscope_commands = AliceTestData.VOICE_COMMANDS["horoscopes"]

        for command in horoscope_commands:
            result = intent_recognizer.recognize_intent(command)

            assert result["intent"] == YandexIntent.HOROSCOPE
            assert "zodiac_sign" in result["entities"]

            # Should extract zodiac sign
            zodiac_sign = result["entities"]["zodiac_sign"]
            if zodiac_sign:
                assert isinstance(zodiac_sign, YandexZodiacSign)

    def test_compatibility_intent_recognition(self, intent_recognizer):
        """Test compatibility intent recognition accuracy"""
        compatibility_commands = AliceTestData.VOICE_COMMANDS["compatibility"]

        for command in compatibility_commands:
            result = intent_recognizer.recognize_intent(command)

            expected_intents = [
                YandexIntent.COMPATIBILITY,
                YandexIntent.SYNASTRY,
            ]
            assert result["intent"] in expected_intents

            # Should extract zodiac signs for compatibility
            entities = result["entities"]
            assert "zodiac_sign" in entities or "partner_sign" in entities

    def test_ai_intent_recognition(self, intent_recognizer):
        """Test AI consultation intent recognition"""
        ai_commands = AliceTestData.VOICE_COMMANDS["ai_features"]

        for command in ai_commands:
            result = intent_recognizer.recognize_intent(command)

            # Should recognize AI-related intents
            ai_intents = [
                YandexIntent.AI_NATAL_INTERPRETATION,
                YandexIntent.AI_CAREER_CONSULTATION,
                YandexIntent.AI_LOVE_CONSULTATION,
                YandexIntent.AI_SPIRITUAL_CONSULTATION,
            ]

            assert (
                result["intent"] in ai_intents
                or result["intent"] != YandexIntent.UNKNOWN
            )

    def test_entity_extraction_accuracy(self, intent_recognizer):
        """Test entity extraction accuracy"""
        test_cases = [
            (
                "гороскоп для льва на завтра",
                {"zodiac_sign": "leo", "date": "tomorrow"},
            ),
            (
                "совместимость овна и рыб",
                {"zodiac_sign": "aries", "partner_sign": "pisces"},
            ),
            (
                "что ждет близнецов сегодня",
                {"zodiac_sign": "gemini", "date": "today"},
            ),
            (
                "прогноз для девы на неделю",
                {"zodiac_sign": "virgo", "period": "week"},
            ),
        ]

        for command, expected_entities in test_cases:
            result = intent_recognizer.recognize_intent(command)
            entities = result["entities"]

            # Check expected entities are extracted
            for entity_type, expected_value in expected_entities.items():
                if entity_type == "zodiac_sign" and entities.get(
                    "zodiac_sign"
                ):
                    # Zodiac sign should match
                    extracted_sign = entities["zodiac_sign"]
                    sign_name = (
                        extracted_sign.value.lower()
                        if hasattr(extracted_sign, "value")
                        else str(extracted_sign).lower()
                    )
                    assert (
                        expected_value in sign_name
                        or sign_name in expected_value
                    )

                elif entity_type in entities:
                    # Other entities should be present
                    assert entities[entity_type] is not None

    def test_voice_preprocessing_accuracy(self, intent_recognizer):
        """Test voice preprocessing for common speech recognition errors"""
        voice_error_cases = [
            (
                "гароскоп для льва",
                "гороскоп для льва",
            ),  # Speech recognition error
            ("асталог помоги", "астролог помоги"),  # Common mispronunciation
            ("гороскоп ля льва", "гороскоп для льва"),  # Preposition error
            ("транзиды сегодня", "транзиты сегодня"),  # Consonant confusion
        ]

        for incorrect_input, expected_correction in voice_error_cases:
            # Process the incorrect input
            result = intent_recognizer.recognize_intent(incorrect_input)

            # Should still recognize intent despite errors
            assert result["intent"] != YandexIntent.UNKNOWN

            # Compare with corrected version
            correct_result = intent_recognizer.recognize_intent(
                expected_correction
            )

            # Results should be similar (same intent)
            assert result["intent"] == correct_result["intent"]


@pytest.mark.integration
class TestYandexGPTIntegration:
    """Test Yandex GPT integration for AI-powered responses"""

    @pytest.fixture
    def yandex_gpt_client(self):
        return YandexGPTClient()

    @pytest.fixture
    def ai_horoscope_service(self):
        return AIHoroscopeService()

    @pytest.mark.asyncio
    async def test_yandex_gpt_horoscope_generation(self, yandex_gpt_client):
        """Test Yandex GPT horoscope generation"""
        horoscope_data = {
            "zodiac_sign": "leo",
            "date": "today",
            "moon_phase": {"phase": "Full Moon", "illumination": 98},
            "energy_level": 85,
            "planetary_influences": [
                "jupiter_trine_sun",
                "venus_sextile_mars",
            ],
        }

        with patch.object(
            yandex_gpt_client, "_make_api_request"
        ) as mock_request:
            mock_request.return_value = {
                "result": {
                    "alternatives": [
                        {
                            "message": {
                                "role": "assistant",
                                "text": "Сегодня Львам светят яркие перспективы! Полная Луна дарит мощную энергию для творчества.",
                            }
                        }
                    ]
                }
            }

            result = await yandex_gpt_client.generate_horoscope_response(
                horoscope_data
            )

            assert "text" in result
            assert len(result["text"]) > 30  # Substantial content
            assert len(result["text"]) <= 800  # Alice limit

            # Should be in Russian
            assert any(
                russian_word in result["text"].lower()
                for russian_word in ["лев", "луна", "энергия", "звезды"]
            )

    @pytest.mark.asyncio
    async def test_yandex_gpt_error_handling(self, yandex_gpt_client):
        """Test Yandex GPT error handling and fallbacks"""
        horoscope_data = {"zodiac_sign": "aries", "date": "today"}

        with patch.object(
            yandex_gpt_client, "_make_api_request"
        ) as mock_request:
            # Simulate API error
            mock_request.side_effect = Exception("API request failed")

            result = await yandex_gpt_client.generate_horoscope_response(
                horoscope_data
            )

            # Should return fallback response or error indicator
            assert result is not None
            if "error" in result:
                assert isinstance(result["error"], str)
            elif "text" in result:
                # Fallback text should be reasonable
                assert len(result["text"]) > 10

    @pytest.mark.asyncio
    async def test_ai_horoscope_service_integration(
        self, ai_horoscope_service
    ):
        """Test AI horoscope service integration"""
        with patch("app.core.config.settings") as mock_settings, patch.object(
            ai_horoscope_service, "yandex_gpt_client"
        ) as mock_gpt:
            mock_settings.ENABLE_AI_GENERATION = True
            mock_gpt.generate_horoscope_response = AsyncMock(
                return_value={
                    "text": "Прекрасный день для Овнов! Энергия на высоте.",
                    "confidence": 0.9,
                }
            )

            result = await ai_horoscope_service.generate_ai_horoscope(
                zodiac_sign=YandexZodiacSign.ARIES,
                horoscope_data={"energy_level": 80},
            )

            assert result is not None
            if "text" in result:
                assert len(result["text"]) > 20
                assert "овн" in result["text"].lower()

    @pytest.mark.asyncio
    async def test_ai_consultation_features(self, ai_horoscope_service):
        """Test AI consultation features"""
        consultation_types = ["career", "love", "health", "spiritual"]

        for consultation_type in consultation_types:
            with patch.object(
                ai_horoscope_service, "yandex_gpt_client"
            ) as mock_gpt:
                mock_gpt.generate_consultation_response = AsyncMock(
                    return_value={
                        "text": f"Консультация по {consultation_type} для Льва",
                        "consultation_type": consultation_type,
                    }
                )

                result = await ai_horoscope_service.generate_specialized_consultation(
                    zodiac_sign=YandexZodiacSign.LEO,
                    consultation_type=consultation_type,
                    user_context={},
                )

                assert result is not None
                if "text" in result:
                    assert len(result["text"]) > 30
                    assert consultation_type in result.get(
                        "consultation_type", ""
                    )


@pytest.mark.integration
class TestVoiceInterfaceOptimization:
    """Test Alice voice interface specific optimizations"""

    def test_tts_text_optimization(self):
        """Test text-to-speech optimization"""
        from app.services.response_formatter import ResponseFormatter

        formatter = ResponseFormatter()

        # Test cases with problematic content for TTS
        test_cases = [
            ("Солнце в ♌ Льве", "Солнце в Льве"),  # Remove special symbols
            (
                "Прогноз: 85% удачи!",
                "Прогноз: восемьдесят пять процентов удачи",
            ),  # Numbers to words
            ("E-mail: test@example.com", "Электронная почта"),  # Remove email
            ("URL: https://example.com", ""),  # Remove URLs
            ("Очень длинный текст " * 100, ""),  # Truncate long text
        ]

        for input_text, expected_pattern in test_cases:
            optimized = formatter._optimize_for_tts(input_text)

            # Should not contain problematic characters
            problematic_chars = ["♌", "♊", "♋", "@", "http", "www"]
            for char in problematic_chars:
                assert char not in optimized

            # Should respect length limits
            assert len(optimized) <= 800  # Alice TTS limit

    def test_voice_button_constraints(self):
        """Test voice interface button constraints"""
        from app.services.response_formatter import ResponseFormatter

        formatter = ResponseFormatter()

        # Test with more than 5 buttons (Alice limit)
        many_buttons = [
            {"title": f"Кнопка {i}", "payload": f"button_{i}"}
            for i in range(1, 8)
        ]

        response = formatter.format_horoscope_response(
            text="Тест", buttons=many_buttons
        )

        # Should limit to 5 buttons
        assert len(response.get("buttons", [])) <= 5

        # Button titles should be short enough for voice
        for button in response.get("buttons", []):
            assert len(button["title"]) <= 64  # Alice button title limit

    def test_russian_voice_patterns(self):
        """Test Russian voice pattern optimization"""
        from app.services.russian_astrology_adapter import RussianAstrologyAdapter

        adapter = RussianAstrologyAdapter()

        # Test stress marks for proper pronunciation
        astrological_terms = [
            "Овен",
            "Телец",
            "Близнецы",
            "Рак",
            "Лев",
            "Дева",
            "Весы",
            "Скорпион",
            "Стрелец",
            "Козерог",
            "Водолей",
            "Рыбы",
            "Солнце",
            "Луна",
            "Меркурий",
            "Венера",
            "Марс",
            "Юпитер",
        ]

        for term in astrological_terms:
            voice_optimized = adapter.format_for_voice(
                term, add_stress_marks=True
            )

            # Should be suitable for Russian TTS
            assert isinstance(voice_optimized, str)
            assert len(voice_optimized) > 0

            # Should not break TTS with problematic characters
            problematic_for_tts = ["<", ">", "&", '"', "'", "\\"]
            for char in problematic_for_tts:
                assert char not in voice_optimized

    def test_alice_response_format_compliance(self):
        """Test Alice response format compliance"""
        from app.services.response_formatter import ResponseFormatter

        formatter = ResponseFormatter()

        response = formatter.format_greeting_response(
            "Привет! Добро пожаловать в мир астрологии!"
        )

        # Check Alice response format
        assert "text" in response
        assert "tts" in response
        assert "end_session" in response

        # Text and TTS should be suitable for voice
        assert len(response["text"]) <= 800
        assert len(response["tts"]) <= 800
        assert not response["end_session"]  # Keep session active

        # Should not contain HTML or markup
        html_patterns = ["<script>", "<html>", "<body>", "&lt;", "&gt;"]
        for pattern in html_patterns:
            assert pattern not in response["text"]
            assert pattern not in response["tts"]


@pytest.mark.integration
class TestAliceConversationFlows:
    """Test complete conversation flows with Alice"""

    @pytest.mark.asyncio
    async def test_multi_turn_horoscope_conversation(self):
        """Test multi-turn conversation for horoscope"""
        session_id = "multi_turn_test_123"

        # Turn 1: User asks for horoscope without specifying sign
        alice_request_1 = AliceTestData.ALICE_REQUEST_TEMPLATE.copy()
        alice_request_1["request"]["command"] = "дай гороскоп"
        alice_request_1["session"]["session_id"] = session_id
        alice_request_1["session"]["new"] = True

        with patch(
            "app.api.yandex_dialogs.get_database_session"
        ) as mock_db, patch(
            "app.services.session_manager.SessionManager"
        ) as mock_session_mgr:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            mock_session_mgr.return_value.get_user_context = AsyncMock(
                return_value=None
            )
            mock_session_mgr.return_value.update_user_context = AsyncMock()

            response_1 = await yandex_webhook(alice_request_1)

            # Should ask for zodiac sign
            response_text = response_1["response"]["text"].lower()
            sign_question_indicators = ["знак", "зодиак", "какой", "скажите"]
            assert any(
                indicator in response_text
                for indicator in sign_question_indicators
            )

        # Turn 2: User provides zodiac sign
        alice_request_2 = alice_request_1.copy()
        alice_request_2["request"]["command"] = "лев"
        alice_request_2["session"]["new"] = False
        alice_request_2["session"]["message_id"] = 2

        with patch(
            "app.api.yandex_dialogs.get_database_session"
        ) as mock_db, patch(
            "app.services.session_manager.SessionManager"
        ) as mock_session_mgr, patch(
            "app.services.horoscope_generator.HoroscopeGenerator"
        ) as mock_horoscope:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            mock_session_mgr.return_value.get_user_context = AsyncMock(
                return_value={"awaiting_data": "zodiac_sign"}
            )
            mock_session_mgr.return_value.update_user_context = AsyncMock()

            mock_horoscope.return_value.generate_horoscope = AsyncMock(
                return_value={
                    "prediction": "Отличный день для Льва!",
                    "energy_level": 90,
                }
            )

            response_2 = await yandex_webhook(alice_request_2)

            # Should provide horoscope for Leo
            response_text = response_2["response"]["text"].lower()
            leo_indicators = ["лев", "льв", "отличный"]
            assert any(
                indicator in response_text for indicator in leo_indicators
            )

    @pytest.mark.asyncio
    async def test_conversation_timeout_handling(self):
        """Test conversation timeout handling"""
        # Simulate conversation that has been idle too long
        old_timestamp = datetime.now().timestamp() - 700  # 11+ minutes ago

        alice_request = AliceTestData.ALICE_REQUEST_TEMPLATE.copy()
        alice_request["request"]["command"] = "продолжаем разговор"

        with patch(
            "app.api.yandex_dialogs.get_database_session"
        ) as mock_db, patch(
            "app.services.session_manager.SessionManager"
        ) as mock_session_mgr:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            mock_session_mgr.return_value.get_user_context = AsyncMock(
                return_value={
                    "last_interaction": old_timestamp,
                    "conversation_count": 5,
                }
            )
            mock_session_mgr.return_value.update_user_context = AsyncMock()

            response = await yandex_webhook(alice_request)

            # Should handle timeout gracefully
            assert "response" in response
            response_text = response["response"]["text"].lower()

            # Should not contain error messages
            error_indicators = ["ошибка", "сбой", "проблема"]
            assert not any(
                error in response_text for error in error_indicators
            )

    @pytest.mark.asyncio
    async def test_context_persistence_across_requests(self):
        """Test context persistence in conversation"""
        session_id = "context_test_456"
        user_id = "test_user_789"

        # First request establishes context
        alice_request = AliceTestData.ALICE_REQUEST_TEMPLATE.copy()
        alice_request["request"]["command"] = "я лев"
        alice_request["session"]["session_id"] = session_id
        alice_request["session"]["user_id"] = user_id

        with patch(
            "app.api.yandex_dialogs.get_database_session"
        ) as mock_db, patch(
            "app.services.session_manager.SessionManager"
        ) as mock_session_mgr:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            mock_session_mgr.return_value.get_user_context = AsyncMock(
                return_value=None
            )
            mock_session_mgr.return_value.update_user_context = AsyncMock()

            await yandex_webhook(alice_request)

            # Context should be updated with zodiac sign
            update_calls = (
                mock_session_mgr.return_value.update_user_context.call_args_list
            )
            assert len(update_calls) > 0

        # Second request should use stored context
        alice_request["request"]["command"] = "дай гороскоп"
        alice_request["session"]["message_id"] = 2

        with patch(
            "app.api.yandex_dialogs.get_database_session"
        ) as mock_db, patch(
            "app.services.session_manager.SessionManager"
        ) as mock_session_mgr, patch(
            "app.services.horoscope_generator.HoroscopeGenerator"
        ) as mock_horoscope:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            mock_session_mgr.return_value.get_user_context = AsyncMock(
                return_value={
                    "preferences": {"zodiac_sign": "leo"},
                    "conversation_count": 1,
                }
            )
            mock_session_mgr.return_value.update_user_context = AsyncMock()

            mock_horoscope.return_value.generate_horoscope = AsyncMock(
                return_value={
                    "prediction": "Гороскоп для Льва готов!",
                    "energy_level": 85,
                }
            )

            response_2 = await yandex_webhook(alice_request)

            # Should generate horoscope without asking for sign again
            response_text = response_2["response"]["text"].lower()
            leo_indicators = ["лев", "льв"]
            assert any(
                indicator in response_text for indicator in leo_indicators
            )

            # Should not ask for zodiac sign
            sign_question_indicators = ["какой знак", "скажите знак"]
            assert not any(
                indicator in response_text
                for indicator in sign_question_indicators
            )


@pytest.mark.performance
class TestAlicePerformanceRequirements:
    """Test Alice-specific performance requirements"""

    @pytest.mark.asyncio
    async def test_response_time_requirements(self):
        """Test that responses meet Alice time requirements"""
        import time

        alice_request = AliceTestData.ALICE_REQUEST_TEMPLATE.copy()
        alice_request["request"]["command"] = "дай гороскоп для льва"

        with patch(
            "app.api.yandex_dialogs.get_database_session"
        ) as mock_db, patch(
            "app.services.session_manager.SessionManager"
        ) as mock_session_mgr, patch(
            "app.services.horoscope_generator.HoroscopeGenerator"
        ) as mock_horoscope:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            mock_session_mgr.return_value.get_user_context = AsyncMock(
                return_value=None
            )
            mock_session_mgr.return_value.update_user_context = AsyncMock()
            mock_horoscope.return_value.generate_horoscope = AsyncMock(
                return_value={"prediction": "Тестовый гороскоп"}
            )

            start_time = time.time()
            response = await yandex_webhook(alice_request)
            end_time = time.time()

            response_time = end_time - start_time

            # Alice requires responses within 3-5 seconds
            assert response_time < 5.0, f"Response too slow: {response_time}s"
            assert response is not None
            assert "response" in response

    def test_memory_usage_optimization(self):
        """Test memory usage stays within reasonable limits"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple intent recognizers (memory intensive operation)
        recognizers = []
        for i in range(10):
            recognizer = IntentRecognizer()
            recognizers.append(recognizer)

            # Test recognition
            recognizer.recognize_intent("тестовая команда")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for this test)
        assert (
            memory_increase < 100
        ), f"Excessive memory usage: {memory_increase}MB increase"

        # Clean up
        del recognizers
