"""
Тесты для Yandex GPT клиента.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError, ClientTimeout
from aiohttp.web_response import Response

from app.services.yandex_gpt import YandexGPTClient, YandexGPTMessage, YandexGPTRequest


class TestYandexGPTClient:
    """Тесты для YandexGPTClient."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        with patch('app.services.yandex_gpt.settings') as mock_settings:
            mock_settings.YANDEX_API_KEY = "test_api_key"
            mock_settings.YANDEX_FOLDER_ID = "test_folder_id"
            mock_settings.YANDEX_CATALOG_ID = "test_catalog_id"
            
            self.client = YandexGPTClient()

    @pytest.mark.asyncio
    async def test_get_session_creates_new_session(self):
        """Тест создания новой HTTP сессии."""
        session = await self.client._get_session()
        
        assert session is not None
        assert not session.closed
        assert session.timeout.total == 30
        assert session._default_headers["Authorization"] == "Api-Key test_api_key"
        assert session._default_headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self):
        """Тест переиспользования существующей сессии."""
        session1 = await self.client._get_session()
        session2 = await self.client._get_session()
        
        assert session1 is session2

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Тест закрытия HTTP сессии."""
        session = await self.client._get_session()
        await self.client.close()
        
        assert session.closed

    @pytest.mark.asyncio
    async def test_generate_text_success(self):
        """Тест успешной генерации текста."""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {
                        "message": {
                            "text": "Сгенерированный текст"
                        }
                    }
                ]
            }
        }
        
        # Mock HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.client._get_session = AsyncMock(return_value=mock_session)
        
        result = await self.client.generate_text(
            prompt="Тестовый запрос",
            system_prompt="Системный промпт",
            temperature=0.5,
            max_tokens=500
        )
        
        assert result == "Сгенерированный текст"
        
        # Проверяем, что запрос был сформирован правильно
        call_args = mock_session.post.call_args
        assert call_args[0][0] == self.client.completion_url
        
        request_json = call_args[1]["json"]
        assert request_json["modelUri"] == "gpt://test_folder_id/yandexgpt-lite/latest"
        assert request_json["completionOptions"]["temperature"] == 0.5
        assert request_json["completionOptions"]["maxTokens"] == "500"
        assert len(request_json["messages"]) == 2
        assert request_json["messages"][0]["role"] == "system"
        assert request_json["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_text_without_system_prompt(self):
        """Тест генерации текста без системного промпта."""
        mock_response_data = {
            "result": {
                "alternatives": [
                    {
                        "message": {
                            "text": "Ответ без системного промпта"
                        }
                    }
                ]
            }
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.client._get_session = AsyncMock(return_value=mock_session)
        
        result = await self.client.generate_text(
            prompt="Только пользовательский запрос",
            system_prompt=None
        )
        
        assert result == "Ответ без системного промпта"
        
        # Проверяем, что только одно сообщение в запросе
        call_args = mock_session.post.call_args
        request_json = call_args[1]["json"]
        assert len(request_json["messages"]) == 1
        assert request_json["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self):
        """Тест обработки ошибки API."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.client._get_session = AsyncMock(return_value=mock_session)
        
        result = await self.client.generate_text(prompt="Тест ошибки")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_text_unexpected_format(self):
        """Тест обработки неожиданного формата ответа."""
        mock_response_data = {
            "unexpected": "format"
        }
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
        
        self.client._get_session = AsyncMock(return_value=mock_session)
        
        result = await self.client.generate_text(prompt="Тест неожиданного формата")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_text_timeout_error(self):
        """Тест обработки таймаута."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = ClientTimeout()
        
        self.client._get_session = AsyncMock(return_value=mock_session)
        
        result = await self.client.generate_text(prompt="Тест таймаута")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_text_client_error(self):
        """Тест обработки клиентской ошибки."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = ClientError("Connection failed")
        
        self.client._get_session = AsyncMock(return_value=mock_session)
        
        result = await self.client.generate_text(prompt="Тест клиентской ошибки")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_text_general_exception(self):
        """Тест обработки общих исключений."""
        mock_session = AsyncMock()
        mock_session.post.side_effect = Exception("Unexpected error")
        
        self.client._get_session = AsyncMock(return_value=mock_session)
        
        result = await self.client.generate_text(prompt="Тест общего исключения")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_horoscope_success(self):
        """Тест успешной генерации гороскопа."""
        expected_horoscope = "Ваш гороскоп на сегодня..."
        
        self.client.generate_text = AsyncMock(return_value=expected_horoscope)
        
        result = await self.client.generate_horoscope(
            zodiac_sign="овен",
            period="день",
            birth_date="1990-05-15",
            additional_context={
                "moon_phase": "Полнолуние",
                "season": "Весна",
                "energy_level": 80
            }
        )
        
        assert result == expected_horoscope
        
        # Проверяем параметры вызова generate_text
        call_args = self.client.generate_text.call_args
        assert "овен" in call_args[1]["prompt"]
        assert "день" in call_args[1]["prompt"]
        assert "1990-05-15" in call_args[1]["prompt"]
        assert "Полнолуние" in call_args[1]["prompt"]
        assert call_args[1]["temperature"] == 0.7
        assert call_args[1]["max_tokens"] == 800

    @pytest.mark.asyncio
    async def test_generate_horoscope_minimal_params(self):
        """Тест генерации гороскопа с минимальными параметрами."""
        expected_horoscope = "Минимальный гороскоп"
        
        self.client.generate_text = AsyncMock(return_value=expected_horoscope)
        
        result = await self.client.generate_horoscope(zodiac_sign="телец")
        
        assert result == expected_horoscope
        
        # Проверяем, что системный промпт содержит инструкции для астролога
        call_args = self.client.generate_text.call_args
        system_prompt = call_args[1]["system_prompt"]
        assert "астролог" in system_prompt.lower()
        assert "800 символов" in system_prompt

    @pytest.mark.asyncio
    async def test_generate_compatibility_analysis_success(self):
        """Тест успешной генерации анализа совместимости."""
        expected_analysis = "Анализ совместимости знаков"
        
        self.client.generate_text = AsyncMock(return_value=expected_analysis)
        
        result = await self.client.generate_compatibility_analysis(
            sign1="овен",
            sign2="лев",
            context={"relationship_type": "романтические"}
        )
        
        assert result == expected_analysis
        
        # Проверяем параметры вызова
        call_args = self.client.generate_text.call_args
        assert "овен" in call_args[1]["prompt"]
        assert "лев" in call_args[1]["prompt"]
        assert "романтических" in call_args[1]["prompt"]
        assert call_args[1]["temperature"] == 0.6
        assert call_args[1]["max_tokens"] == 600

    @pytest.mark.asyncio
    async def test_generate_compatibility_analysis_without_context(self):
        """Тест генерации анализа совместимости без контекста."""
        expected_analysis = "Базовый анализ совместимости"
        
        self.client.generate_text = AsyncMock(return_value=expected_analysis)
        
        result = await self.client.generate_compatibility_analysis(
            sign1="рак",
            sign2="скорпион"
        )
        
        assert result == expected_analysis

    @pytest.mark.asyncio
    async def test_generate_advice_success(self):
        """Тест успешной генерации совета."""
        expected_advice = "Астрологический совет"
        
        self.client.generate_text = AsyncMock(return_value=expected_advice)
        
        result = await self.client.generate_advice(
            zodiac_sign="дева",
            topic="карьера",
            context={
                "mood": "оптимистичное",
                "current_challenges": "новый проект"
            }
        )
        
        assert result == expected_advice
        
        # Проверяем параметры вызова
        call_args = self.client.generate_text.call_args
        prompt = call_args[1]["prompt"]
        assert "дева" in prompt
        assert "карьера" in prompt
        assert "оптимистичное" in prompt
        assert "новый проект" in prompt
        assert call_args[1]["temperature"] == 0.8
        assert call_args[1]["max_tokens"] == 300

    @pytest.mark.asyncio
    async def test_generate_advice_without_topic_and_context(self):
        """Тест генерации совета без темы и контекста."""
        expected_advice = "Общий совет"
        
        self.client.generate_text = AsyncMock(return_value=expected_advice)
        
        result = await self.client.generate_advice(zodiac_sign="весы")
        
        assert result == expected_advice
        
        call_args = self.client.generate_text.call_args
        system_prompt = call_args[1]["system_prompt"]
        assert "300 символов" in system_prompt

    @pytest.mark.asyncio
    async def test_is_available_success(self):
        """Тест успешной проверки доступности."""
        self.client.generate_text = AsyncMock(return_value="Привет")
        
        result = await self.client.is_available()
        assert result is True
        
        # Проверяем, что был вызван тестовый запрос
        call_args = self.client.generate_text.call_args
        assert call_args[1]["prompt"] == "Привет"
        assert call_args[1]["temperature"] == 0.1
        assert call_args[1]["max_tokens"] == 10

    @pytest.mark.asyncio
    async def test_is_available_no_credentials(self):
        """Тест проверки доступности без учетных данных."""
        self.client.api_key = None
        
        result = await self.client.is_available()
        assert result is False

    @pytest.mark.asyncio 
    async def test_is_available_no_folder_id(self):
        """Тест проверки доступности без folder_id."""
        self.client.folder_id = None
        
        result = await self.client.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_available_api_error(self):
        """Тест проверки доступности с ошибкой API."""
        self.client.generate_text = AsyncMock(return_value=None)
        
        result = await self.client.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_available_exception(self):
        """Тест проверки доступности с исключением."""
        self.client.generate_text = AsyncMock(side_effect=Exception("API Error"))
        
        result = await self.client.is_available()
        assert result is False

    def test_yandex_gpt_message_model(self):
        """Тест модели YandexGPTMessage."""
        message = YandexGPTMessage(role="user", text="Тестовое сообщение")
        
        assert message.role == "user"
        assert message.text == "Тестовое сообщение"

    def test_yandex_gpt_request_model(self):
        """Тест модели YandexGPTRequest."""
        messages = [
            YandexGPTMessage(role="system", text="Системное сообщение"),
            YandexGPTMessage(role="user", text="Пользовательское сообщение")
        ]
        
        request = YandexGPTRequest(
            modelUri="gpt://test/model/latest",
            completionOptions={"temperature": 0.7, "maxTokens": "1000"},
            messages=messages
        )
        
        assert request.modelUri == "gpt://test/model/latest"
        assert request.completionOptions["temperature"] == 0.7
        assert len(request.messages) == 2

    def test_client_initialization(self):
        """Тест инициализации клиента."""
        with patch('app.services.yandex_gpt.settings') as mock_settings:
            mock_settings.YANDEX_API_KEY = "test_key"
            mock_settings.YANDEX_FOLDER_ID = "test_folder"
            mock_settings.YANDEX_CATALOG_ID = "test_catalog"
            
            client = YandexGPTClient()
            
            assert client.api_key == "test_key"
            assert client.folder_id == "test_folder"
            assert client.catalog_id == "test_catalog"
            assert client.base_url == "https://llm.api.cloud.yandex.net"
            assert client.model_uri == "gpt://test_folder/yandexgpt-lite/latest"

    def test_client_initialization_without_catalog_id(self):
        """Тест инициализации клиента без catalog_id."""
        with patch('app.services.yandex_gpt.settings') as mock_settings:
            mock_settings.YANDEX_API_KEY = "test_key"
            mock_settings.YANDEX_FOLDER_ID = "test_folder"
            mock_settings.YANDEX_CATALOG_ID = None
            
            client = YandexGPTClient()
            
            assert client.catalog_id == "test_folder"  # Should fallback to folder_id

    @pytest.mark.asyncio
    async def test_session_recreation_after_close(self):
        """Тест пересоздания сессии после закрытия."""
        session1 = await self.client._get_session()
        await self.client.close()
        
        # После закрытия должна создаться новая сессия
        session2 = await self.client._get_session()
        
        assert session1 is not session2
        assert session1.closed
        assert not session2.closed