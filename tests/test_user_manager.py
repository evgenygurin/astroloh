"""
Tests for user manager.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.yandex_models import YandexZodiacSign
from app.services.user_manager import UserManager


class TestUserManager:
    """Test user manager functionality."""

    def setup_method(self):
        """Setup before each test."""
        self.mock_db = AsyncMock()
        self.user_manager = UserManager(self.mock_db)

    @pytest.mark.asyncio
    async def test_get_or_create_user_new_user(self):
        """Test creating a new user."""
        # Mock database query to return None (user doesn't exist)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = mock_result

        user_id = "test_user_123"
        await self.user_manager.get_or_create_user(user_id)

        # Verify database operations were called
        assert self.mock_db.execute.called
        assert self.mock_db.add.called
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing_user(self):
        """Test getting an existing user."""
        # Mock existing user
        mock_user = MagicMock()
        mock_user.yandex_user_id = "test_user_123"
        mock_user.zodiac_sign = "leo"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        self.mock_db.execute.return_value = mock_result

        user_id = "test_user_123"
        user = await self.user_manager.get_or_create_user(user_id)

        assert user == mock_user
        # Should not call add for existing user, but should commit to update last_accessed
        assert not self.mock_db.add.called
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_user_birth_data(self):
        """Test updating user birth data."""
        import uuid

        from app.services.encryption import data_protection

        user_id = uuid.uuid4()
        birth_date = "1990-05-15"
        birth_time = "14:30:00"
        birth_location = "Moscow"
        zodiac_sign = "taurus"

        with patch.object(
            data_protection, "encrypt_birth_data"
        ) as mock_encrypt:
            mock_encrypt.return_value = {
                "encrypted_birth_date": b"encrypted_date",
                "encrypted_birth_time": b"encrypted_time",
                "encrypted_birth_location": b"encrypted_location",
            }

            # Mock database query
            mock_result = AsyncMock()
            mock_result.rowcount = 1
            self.mock_db.execute.return_value = mock_result

            result = await self.user_manager.update_user_birth_data(
                user_id, birth_date, birth_time, birth_location, zodiac_sign
            )

            # Verify encryption was called
            assert mock_encrypt.called
            assert self.mock_db.commit.called
            assert result is True

    @pytest.mark.asyncio
    async def test_update_zodiac_via_birth_data(self):
        """Test updating zodiac sign via birth data update."""
        import uuid

        from app.services.encryption import data_protection

        user_id = uuid.uuid4()
        zodiac_sign = "leo"

        with patch.object(
            data_protection, "encrypt_birth_data"
        ) as mock_encrypt:
            mock_encrypt.return_value = {
                "encrypted_birth_date": b"encrypted_date",
                "encrypted_birth_time": b"encrypted_time",
                "encrypted_birth_location": b"encrypted_location",
            }

            # Mock database query
            mock_result = AsyncMock()
            mock_result.rowcount = 1
            self.mock_db.execute.return_value = mock_result

            result = await self.user_manager.update_user_birth_data(
                user_id, "1990-08-10", zodiac_sign=zodiac_sign
            )

            assert result is True
            assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_user_birth_data_encrypted(self):
        """Test getting user birth data when encrypted."""
        import uuid

        from app.services.encryption import data_protection

        user_id = uuid.uuid4()
        mock_user = MagicMock()
        mock_user.encrypted_birth_date = b"encrypted_date"
        mock_user.encrypted_birth_time = b"encrypted_time"
        mock_user.encrypted_birth_location = b"encrypted_location"
        mock_user.zodiac_sign = "taurus"

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        self.mock_db.execute.return_value = mock_result

        with patch.object(
            data_protection, "decrypt_birth_data"
        ) as mock_decrypt:
            mock_decrypt.return_value = {
                "birth_date": "1990-05-15",
                "birth_time": "14:30:00",
                "birth_location": {
                    "latitude": 55.7558,
                    "longitude": 37.6176,
                    "name": "Moscow",
                },
            }

            birth_data = await self.user_manager.get_user_birth_data(user_id)

            assert birth_data is not None
            assert "birth_date" in birth_data
            assert "birth_location" in birth_data
            assert birth_data["zodiac_sign"] == "taurus"

    @pytest.mark.asyncio
    async def test_get_user_birth_data_not_encrypted(self):
        """Test getting user birth data when not encrypted."""
        import uuid

        user_id = uuid.uuid4()

        # Mock database query returning None (no user found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_db.execute.return_value = mock_result

        birth_data = await self.user_manager.get_user_birth_data(user_id)

        assert birth_data is None

    @pytest.mark.asyncio
    async def test_delete_user_data(self):
        """Test deleting user data."""
        mock_user = MagicMock()

        await self.user_manager.delete_user_data(mock_user)

        # Verify encrypted fields are cleared
        assert mock_user.encrypted_birth_date is None
        assert mock_user.encrypted_birth_location is None
        assert mock_user.encrypted_birth_time is None
        assert mock_user.encrypted_name is None
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_last_accessed(self):
        """Test updating user last accessed time."""
        mock_user = MagicMock()

        await self.user_manager.update_last_accessed(mock_user)

        assert mock_user.last_accessed is not None
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_user_preferences(self):
        """Test getting user preferences."""
        mock_user = MagicMock()
        mock_user.zodiac_sign = "leo"
        mock_user.gender = "female"
        mock_user.data_consent = True

        preferences = await self.user_manager.get_user_preferences(mock_user)

        assert preferences["zodiac_sign"] == "leo"
        assert preferences["gender"] == "female"
        assert preferences["data_consent"] is True

    @pytest.mark.asyncio
    async def test_set_user_consent(self):
        """Test setting user data consent."""
        mock_user = MagicMock()

        await self.user_manager.set_user_consent(mock_user, True)

        assert mock_user.data_consent is True
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_users_for_cleanup(self):
        """Test getting users for data cleanup."""
        # Mock users that need cleanup
        mock_users = [MagicMock(), MagicMock()]
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = (
            mock_users
        )

        users = await self.user_manager.get_users_for_cleanup(
            days_threshold=30
        )

        assert len(users) == 2
        assert self.mock_db.execute.called

    @pytest.mark.asyncio
    async def test_create_user_with_consent(self):
        """Test creating user with data consent."""
        user_id = "test_user_123"

        # Mock no existing user
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = (
            None
        )

        await self.user_manager.create_user_with_consent(user_id, consent=True)

        assert self.mock_db.add.called
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_encrypt_data(self):
        """Test data encryption."""
        test_data = "sensitive information"

        with patch(
            "app.services.encryption.EncryptionService"
        ) as mock_encryption:
            mock_encryption.return_value.encrypt.return_value = (
                b"encrypted_data"
            )

            encrypted = self.user_manager._encrypt_data(test_data)

            assert encrypted == b"encrypted_data"

    @pytest.mark.asyncio
    async def test_decrypt_data(self):
        """Test data decryption."""
        encrypted_data = b"encrypted_data"

        with patch(
            "app.services.encryption.EncryptionService"
        ) as mock_encryption:
            mock_encryption.return_value.decrypt.return_value = (
                "decrypted_data"
            )

            decrypted = self.user_manager._decrypt_data(encrypted_data)

            assert decrypted == "decrypted_data"

    @pytest.mark.asyncio
    async def test_get_user_statistics(self):
        """Test getting user statistics."""
        mock_user = MagicMock()
        mock_user.created_at = datetime.now() - timedelta(days=30)
        mock_user.last_accessed = datetime.now() - timedelta(days=1)

        # Mock session count
        self.mock_db.execute.return_value.scalar.return_value = 5

        stats = await self.user_manager.get_user_statistics(mock_user)

        assert "days_since_registration" in stats
        assert "days_since_last_access" in stats
        assert "total_sessions" in stats
        assert stats["total_sessions"] == 5

    @pytest.mark.asyncio
    async def test_is_user_active(self):
        """Test checking if user is active."""
        # Active user
        active_user = MagicMock()
        active_user.last_accessed = datetime.now() - timedelta(days=5)

        assert await self.user_manager.is_user_active(
            active_user, days_threshold=30
        )

        # Inactive user
        inactive_user = MagicMock()
        inactive_user.last_accessed = datetime.now() - timedelta(days=50)

        assert not await self.user_manager.is_user_active(
            inactive_user, days_threshold=30
        )

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test getting user by ID when not found."""
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = (
            None
        )

        user = await self.user_manager.get_user_by_id("nonexistent_user")

        assert user is None

    @pytest.mark.asyncio
    async def test_update_user_gender(self):
        """Test updating user gender."""
        mock_user = MagicMock()

        await self.user_manager.update_user_gender(mock_user, "female")

        assert mock_user.gender == "female"
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_error_handling_database_error(self):
        """Test error handling when database operation fails."""
        self.mock_db.commit.side_effect = Exception("Database error")

        mock_user = MagicMock()

        with pytest.raises(Exception):
            await self.user_manager.update_user_zodiac_sign(
                mock_user, YandexZodiacSign.LEO
            )

    @pytest.mark.asyncio
    async def test_encryption_error_handling(self):
        """Test error handling when encryption fails."""
        mock_user = MagicMock()
        birth_data = {"birth_date": datetime(1990, 5, 15)}

        with patch.object(self.user_manager, "_encrypt_data") as mock_encrypt:
            mock_encrypt.side_effect = Exception("Encryption error")

            with pytest.raises(Exception):
                await self.user_manager.update_user_birth_data(
                    mock_user, birth_data
                )

    @pytest.mark.asyncio
    async def test_decryption_error_handling(self):
        """Test error handling when decryption fails."""
        mock_user = MagicMock()
        mock_user.encrypted_birth_date = b"corrupted_data"

        with patch.object(self.user_manager, "_decrypt_data") as mock_decrypt:
            mock_decrypt.side_effect = Exception("Decryption error")

            birth_data = await self.user_manager.get_user_birth_data(mock_user)

            # Should handle decryption error gracefully
            assert birth_data is None

    @pytest.mark.asyncio
    async def test_user_creation_with_full_data(self):
        """Test creating user with full data set."""
        user_id = "test_user_full"

        # Mock no existing user
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = (
            None
        )

        user_data = {
            "zodiac_sign": YandexZodiacSign.VIRGO,
            "gender": "male",
            "consent": True,
            "retention_days": 365,
        }

        await self.user_manager.create_user_with_full_data(user_id, user_data)

        assert self.mock_db.add.called
        assert self.mock_db.commit.called

    @pytest.mark.asyncio
    async def test_bulk_user_operations(self):
        """Test bulk operations on multiple users."""
        user_ids = ["user1", "user2", "user3"]

        # Mock multiple users
        mock_users = [MagicMock() for _ in user_ids]
        self.mock_db.execute.return_value.scalars.return_value.all.return_value = (
            mock_users
        )

        result = await self.user_manager.bulk_update_last_accessed(user_ids)

        assert result is not None
        assert self.mock_db.commit.called
