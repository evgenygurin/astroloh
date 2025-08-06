"""
Tests for Telegram Bot integration.
"""

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.telegram_adapter import TelegramAdapter


class TestTelegramWebhook:
    """Test Telegram webhook endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @patch("app.api.telegram_bot.multi_platform_handler")
    @patch("app.api.telegram_bot.UserManager")
    def test_telegram_webhook_message(self, mock_user_manager, mock_handler):
        """Test Telegram webhook with text message."""
        # Mock user manager
        mock_user_manager_instance = AsyncMock()
        mock_user_manager.return_value = mock_user_manager_instance

        # Mock handler response
        from app.models.platform_models import UniversalResponse, Button

        mock_response = UniversalResponse(
            text="Привет! Я астролог. Как дела?",
            buttons=[
                Button(title="Гороскоп", payload={"action": "horoscope"}),
                Button(title="Помощь", payload={"action": "help"}),
            ],
            end_session=False,
        )
        # Make handle_request async
        mock_handler.handle_request = AsyncMock(return_value=mock_response)

        # Test request
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                },
                "chat": {
                    "id": 987654321,
                    "type": "private",
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser",
                },
                "date": 1234567890,
                "text": "Привет",
            },
        }

        response = self.client.post("/api/v1/telegram/webhook", json=telegram_update)

        assert response.status_code == 200
        assert response.json()["ok"]

        # Verify handler was called
        mock_handler.handle_request.assert_called_once()

    @patch("app.api.telegram_bot.multi_platform_handler")
    @patch("app.api.telegram_bot.UserManager")
    def test_telegram_webhook_callback_query(self, mock_user_manager, mock_handler):
        """Test Telegram webhook with callback query."""
        # Mock user manager
        mock_user_manager_instance = AsyncMock()
        mock_user_manager.return_value = mock_user_manager_instance

        # Mock handler response
        from app.models.platform_models import UniversalResponse

        mock_response = UniversalResponse(
            text="Отлично! Назовите ваш знак зодиака.", end_session=False
        )
        # Make handle_request async
        mock_handler.handle_request = AsyncMock(return_value=mock_response)

        # Test callback query request
        telegram_update = {
            "update_id": 123456790,
            "callback_query": {
                "id": "callback123",
                "from": {"id": 987654321, "is_bot": False, "first_name": "Test"},
                "message": {
                    "message_id": 2,
                    "from": {"id": 987654321, "is_bot": False, "first_name": "Test"},
                    "chat": {"id": 987654321, "type": "private"},
                    "date": 1234567891,
                },
                "data": "horoscope",
                "chat_instance": "instance123",
            },
        }

        response = self.client.post("/api/v1/telegram/webhook", json=telegram_update)

        assert response.status_code == 200
        assert response.json()["ok"]

        # Verify handler was called
        mock_handler.handle_request.assert_called_once()

    def test_telegram_webhook_invalid_request(self):
        """Test Telegram webhook with invalid request."""
        invalid_request = {"invalid": "data"}

        response = self.client.post("/api/v1/telegram/webhook", json=invalid_request)

        assert response.status_code == 400
        assert "Invalid Telegram request" in response.json()["detail"]

    def test_telegram_health_check(self):
        """Test Telegram health check endpoint."""
        response = self.client.get("/api/v1/telegram/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "telegram_bot"
        assert data["platform"] == "telegram"

    def test_set_telegram_webhook(self):
        """Test setting Telegram webhook."""
        webhook_url = "https://example.com/webhook"

        response = self.client.post(
            f"/api/v1/telegram/set-webhook?webhook_url={webhook_url}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert webhook_url in data["message"]


class TestTelegramAdapter:
    """Test Telegram adapter functionality."""

    def setup_method(self):
        """Set up test adapter."""
        self.adapter = TelegramAdapter()

    def test_validate_telegram_message(self):
        """Test Telegram message validation."""
        valid_update = {
            "update_id": 123,
            "message": {
                "message_id": 456,
                "from": {"id": 789, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567890,
                "text": "Hello",
            },
        }

        assert self.adapter.validate_request(valid_update)

    def test_validate_telegram_callback(self):
        """Test Telegram callback query validation."""
        valid_callback = {
            "update_id": 123,
            "callback_query": {
                "id": "callback123",
                "from": {"id": 789, "is_bot": False, "first_name": "Test"},
                "data": "button_data",
                "chat_instance": "instance",
            },
        }

        assert self.adapter.validate_request(valid_callback)

    def test_convert_telegram_message_to_universal(self):
        """Test converting Telegram message to universal format."""
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "John",
                    "last_name": "Doe",
                    "username": "johndoe",
                    "language_code": "ru",
                },
                "chat": {"id": 987654321, "type": "private"},
                "date": 1234567890,
                "text": "Привет, расскажи гороскоп",
            },
        }

        universal_request = self.adapter.to_universal_request(telegram_update)

        assert universal_request.platform.value == "telegram"
        assert universal_request.user_id == "987654321"
        assert universal_request.session_id == "987654321"
        assert universal_request.text == "Привет, расскажи гороскоп"
        assert universal_request.is_new_session

        # Check user context
        assert "telegram_user" in universal_request.user_context
        assert universal_request.user_context["telegram_user"]["first_name"] == "John"
        assert universal_request.user_context["telegram_user"]["username"] == "johndoe"

    def test_convert_universal_response_to_telegram(self):
        """Test converting universal response to Telegram format."""
        from app.models.platform_models import UniversalResponse, Button

        universal_response = UniversalResponse(
            text="Ваш гороскоп на сегодня очень позитивный! ⭐",
            buttons=[
                Button(title="Завтра", payload={"action": "tomorrow"}),
                Button(title="Совместимость", payload={"action": "compatibility"}),
                Button(title="Помощь", payload={"action": "help"}),
            ],
            end_session=False,
            platform_specific={"chat_id": "987654321"},
        )

        telegram_response = self.adapter.from_universal_response(universal_response)

        assert "send_message" in telegram_response

        send_message = telegram_response["send_message"]
        assert send_message["chat_id"] == 987654321
        assert "гороскоп" in send_message["text"]
        assert send_message["parse_mode"] == "HTML"

        # Check inline keyboard
        assert "reply_markup" in send_message
        keyboard = send_message["reply_markup"]["inline_keyboard"]
        assert len(keyboard) == 3  # 3 buttons
        assert keyboard[0][0]["text"] == "Завтра"
        assert keyboard[1][0]["text"] == "Совместимость"
        assert keyboard[2][0]["text"] == "Помощь"

    def test_convert_universal_response_with_image(self):
        """Test converting universal response with image to Telegram format."""
        from app.models.platform_models import UniversalResponse

        universal_response = UniversalResponse(
            text="Ваша натальная карта",
            image_url="https://example.com/chart.png",
            image_caption="Натальная карта для Льва",
            end_session=False,
            platform_specific={"chat_id": "987654321"},
        )

        telegram_response = self.adapter.from_universal_response(universal_response)

        assert "send_photo" in telegram_response

        send_photo = telegram_response["send_photo"]
        assert send_photo["chat_id"] == 987654321
        assert send_photo["photo"] == "https://example.com/chart.png"
        assert send_photo["caption"] == "Натальная карта для Льва"

    def test_format_telegram_text(self):
        """Test Telegram text formatting."""
        text = "Ваш гороскоп на сегодня:\n\n⭐ Отлично!\n💕 Любовь процветает"
        formatted = self.adapter._format_telegram_text(text)

        # Should preserve emojis and basic formatting
        assert "⭐" in formatted
        assert "💕" in formatted
        assert "гороскоп" in formatted

    def test_long_text_truncation(self):
        """Test that long text is properly truncated for Telegram."""
        long_text = "А" * 5000  # Longer than Telegram's 4096 limit
        formatted = self.adapter._format_telegram_text(long_text)

        assert len(formatted) <= 4090
        assert formatted.endswith("...")
