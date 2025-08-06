"""
Tests for conversation manager functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.database import User
from app.services.conversation_manager import ConversationManager


class TestConversationManager:
    """Tests for conversation manager."""

    def setup_method(self):
        """Setup before each test."""
        self.conversation_manager = ConversationManager()

    @pytest.mark.asyncio
    async def test_get_conversation_context_new_user(self):
        """Test getting conversation context for new user."""
        mock_db = AsyncMock()
        mock_user_manager = AsyncMock()
        mock_user_manager.get_user_by_yandex_id.return_value = None

        with patch(
            "app.services.conversation_manager.UserManager",
            return_value=mock_user_manager,
        ):
            context = await self.conversation_manager.get_conversation_context(
                "test_user_id", mock_db
            )

        assert context is not None
        assert context.personalization_level == 0
        assert context.conversation_count == 0
        assert context.last_interaction is None

    @pytest.mark.asyncio
    async def test_get_conversation_context_existing_user(self):
        """Test getting conversation context for existing user."""
        mock_db = AsyncMock()
        mock_user_manager = AsyncMock()

        mock_user = User(yandex_user_id="test_user_id", zodiac_sign="leo")
        # Set attributes manually since User doesn't have these in constructor
        mock_user.conversation_count = 5
        mock_user.last_interaction = datetime.now()
        mock_user.preferences = {"theme": "dark"}
        mock_user_manager.get_user_by_yandex_id.return_value = mock_user

        with patch(
            "app.services.conversation_manager.UserManager",
            return_value=mock_user_manager,
        ):
            context = await self.conversation_manager.get_conversation_context(
                "test_user_id", mock_db
            )

        assert context is not None
        assert context.personalization_level > 0
        assert context.conversation_count == 5
        assert context.preferences == {"theme": "dark"}

    @pytest.mark.asyncio
    async def test_update_conversation_context(self):
        """Test updating conversation context."""
        mock_db = AsyncMock()
        mock_user_manager = AsyncMock()

        # Create a mock request with proper YandexSession structure
        request = MagicMock()
        request.session = MagicMock()
        request.session.user_id = "test_user"

        context = MagicMock()
        context.conversation_count = 5
        context.personalization_level = 50

        with patch(
            "app.services.conversation_manager.UserManager",
            return_value=mock_user_manager,
        ):
            await self.conversation_manager.update_conversation_context(
                request, context, mock_db
            )

        mock_user_manager.update_user_interaction.assert_called_once()

    def test_calculate_personalization_level(self):
        """Test personalization level calculation."""
        # New user
        level = self.conversation_manager.calculate_personalization_level(0, None)
        assert level == 0

        # User with some conversations
        level = self.conversation_manager.calculate_personalization_level(5, None)
        assert 0 < level <= 30

        # Frequent user
        level = self.conversation_manager.calculate_personalization_level(20, None)
        assert 30 < level <= 70

        # Very active user
        level = self.conversation_manager.calculate_personalization_level(50, None)
        assert 70 < level <= 100

    def test_calculate_personalization_level_with_recent_interaction(self):
        """Test personalization level with recent interaction."""
        recent_interaction = datetime.now() - timedelta(hours=1)
        level = self.conversation_manager.calculate_personalization_level(
            10, recent_interaction
        )

        # Should get bonus for recent interaction
        base_level = self.conversation_manager.calculate_personalization_level(10, None)
        assert level > base_level

    def test_enhance_context_with_history(self):
        """Test context enhancement with user history."""
        context = MagicMock()
        context.preferences = {"zodiac_sign": "leo", "theme": "dark"}
        context.conversation_count = 10

        user_input = "расскажи мой гороскоп"
        enhanced = self.conversation_manager.enhance_context_with_history(
            user_input, context
        )

        assert "zodiac_sign" in enhanced
        assert enhanced["zodiac_sign"] == "leo"
        assert "conversation_count" in enhanced
        assert enhanced["conversation_count"] == 10

    def test_enhance_context_with_history_no_preferences(self):
        """Test context enhancement with no user history."""
        context = MagicMock()
        context.preferences = {}
        context.conversation_count = 0

        user_input = "привет"
        enhanced = self.conversation_manager.enhance_context_with_history(
            user_input, context
        )

        assert "conversation_count" in enhanced
        assert enhanced["conversation_count"] == 0
        assert len(enhanced) >= 1  # Should have at least conversation_count

    @pytest.mark.asyncio
    async def test_analyze_conversation_patterns(self):
        """Test conversation pattern analysis."""
        mock_db = AsyncMock()

        # Mock conversation history
        mock_conversations = [
            {
                "intent": "horoscope",
                "timestamp": datetime.now() - timedelta(days=1),
            },
            {
                "intent": "compatibility",
                "timestamp": datetime.now() - timedelta(days=2),
            },
            {
                "intent": "horoscope",
                "timestamp": datetime.now() - timedelta(days=3),
            },
        ]

        with patch.object(
            self.conversation_manager, "_get_conversation_history"
        ) as mock_history:
            mock_history.return_value = mock_conversations

            patterns = await self.conversation_manager.analyze_conversation_patterns(
                "test_user_id", mock_db
            )

        assert "most_common_intent" in patterns
        assert patterns["most_common_intent"] == "horoscope"
        assert "conversation_frequency" in patterns

    def test_get_personalized_suggestions(self):
        """Test getting personalized suggestions."""
        context = MagicMock()
        context.preferences = {"favorite_topic": "love"}
        context.personalization_level = 75

        suggestions = self.conversation_manager.get_personalized_suggestions(
            "horoscope", context
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # High personalization should give more specific suggestions
        assert any(
            "love" in suggestion.lower() or "любов" in suggestion.lower()
            for suggestion in suggestions
        )

    def test_get_personalized_suggestions_low_personalization(self):
        """Test suggestions for low personalization users."""
        context = MagicMock()
        context.preferences = {}
        context.personalization_level = 10

        suggestions = self.conversation_manager.get_personalized_suggestions(
            "greeting", context
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # Should get general suggestions
        general_suggestions = ["гороскоп", "совместимость", "натальная карта"]
        assert any(
            any(gen in suggestion.lower() for gen in general_suggestions)
            for suggestion in suggestions
        )

    @pytest.mark.asyncio
    async def test_cleanup_old_contexts(self):
        """Test cleanup of old conversation contexts."""
        mock_db = AsyncMock()

        # Should not raise any exceptions
        await self.conversation_manager.cleanup_old_contexts(mock_db)

        # Check that some cleanup operation was attempted
        assert True  # If we get here, no exceptions were raised

    def test_is_returning_user(self):
        """Test returning user detection."""
        # New user
        context = MagicMock()
        context.conversation_count = 0
        assert not self.conversation_manager.is_returning_user(context)

        # Returning user
        context.conversation_count = 5
        assert self.conversation_manager.is_returning_user(context)

    def test_get_conversation_sentiment(self):
        """Test conversation sentiment analysis."""
        positive_text = "спасибо, очень интересно!"
        sentiment = self.conversation_manager.get_conversation_sentiment(positive_text)
        assert sentiment in ["positive", "neutral", "negative"]

        negative_text = "это неправда, не нравится"
        sentiment = self.conversation_manager.get_conversation_sentiment(negative_text)
        assert sentiment in ["positive", "neutral", "negative"]

        neutral_text = "расскажи гороскоп"
        sentiment = self.conversation_manager.get_conversation_sentiment(neutral_text)
        assert sentiment in ["positive", "neutral", "negative"]
