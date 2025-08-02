"""
Tests for security and data protection functionality.
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.encryption import (
    DataProtectionManager,
    EncryptionService,
    SecurityUtils,
)
from app.services.gdpr_compliance import GDPRComplianceService
from app.services.user_manager import SessionManager, UserManager


class TestEncryptionService:
    """Tests for encryption service."""

    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption."""
        encryption = EncryptionService("test-secret-key-32-characters!!")

        original_data = "Sensitive user data"
        encrypted = encryption.encrypt(original_data)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original_data
        assert encrypted != original_data.encode()

    def test_encrypt_decrypt_empty_string(self):
        """Test encryption of empty strings."""
        encryption = EncryptionService("test-secret-key-32-characters!!")

        encrypted = encryption.encrypt("")
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == ""

    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        encryption = EncryptionService("test-secret-key-32-characters!!")

        original_dict = {
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_location": "Moscow, Russia",
        }

        encrypted = encryption.encrypt_dict(original_dict)
        decrypted = encryption.decrypt_dict(encrypted)

        assert decrypted == original_dict

    def test_encryption_with_different_keys(self):
        """Test that different keys produce different results."""
        encryption1 = EncryptionService("test-secret-key-32-characters!!")
        encryption2 = EncryptionService("another-secret-key-32-chars!!")

        data = "test data"
        encrypted1 = encryption1.encrypt(data)
        encrypted2 = encryption2.encrypt(data)

        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails."""
        encryption1 = EncryptionService("test-secret-key-32-characters!!")
        encryption2 = EncryptionService("another-secret-key-32-chars!!")

        data = "test data"
        encrypted = encryption1.encrypt(data)

        with pytest.raises(Exception):
            encryption2.decrypt(encrypted)


class TestSecurityUtils:
    """Tests for security utilities."""

    def test_hash_ip(self):
        """Test IP address hashing."""
        ip1 = "192.168.1.1"
        ip2 = "10.0.0.1"

        hash1 = SecurityUtils.hash_ip(ip1)
        hash2 = SecurityUtils.hash_ip(ip2)

        assert hash1 != hash2
        assert len(hash1) == 64  # SHA256 hash length
        assert hash1 == SecurityUtils.hash_ip(ip1)  # Consistent hashing

    def test_hash_user_agent(self):
        """Test User-Agent hashing."""
        ua1 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ua2 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

        hash1 = SecurityUtils.hash_user_agent(ua1)
        hash2 = SecurityUtils.hash_user_agent(ua2)

        assert hash1 != hash2
        assert len(hash1) == 64  # SHA256 hash length

    def test_generate_verification_code(self):
        """Test verification code generation."""
        code1 = SecurityUtils.generate_verification_code()
        code2 = SecurityUtils.generate_verification_code()

        assert code1 != code2
        assert len(code1) == 32  # 16 bytes hex = 32 characters
        assert all(c in "0123456789abcdef" for c in code1)

    def test_sanitize_input(self):
        """Test input sanitization."""
        dangerous_input = "<script>alert('xss')</script>\"&malicious\x00\x08"
        sanitized = SecurityUtils.sanitize_input(dangerous_input)

        assert "<" not in sanitized
        assert ">" not in sanitized
        assert '"' not in sanitized
        assert "&" not in sanitized
        assert "\x00" not in sanitized

    def test_sanitize_input_max_length(self):
        """Test input length limitation."""
        long_input = "a" * 2000
        sanitized = SecurityUtils.sanitize_input(long_input, max_length=100)

        assert len(sanitized) == 100

    def test_session_expiry_check(self):
        """Test session expiry checking."""
        expired_time = datetime.utcnow() - timedelta(hours=1)
        valid_time = datetime.utcnow() + timedelta(hours=1)

        assert SecurityUtils.is_session_expired(expired_time)
        assert not SecurityUtils.is_session_expired(valid_time)

    def test_generate_session_expiry(self):
        """Test session expiry generation."""
        expiry = SecurityUtils.generate_session_expiry(24)
        expected = datetime.utcnow() + timedelta(hours=24)

        # Allow 1 minute tolerance for test execution time
        assert abs((expiry - expected).total_seconds()) < 60


class TestDataProtectionManager:
    """Tests for data protection manager."""

    def test_encrypt_birth_data(self):
        """Test birth data encryption."""
        encryption = EncryptionService("test-secret-key-32-characters!!")
        manager = DataProtectionManager(encryption)

        birth_date = "1990-05-15"
        birth_time = "14:30"
        birth_location = "Moscow, Russia"

        encrypted = manager.encrypt_birth_data(
            birth_date, birth_time, birth_location
        )

        assert "encrypted_birth_date" in encrypted
        assert "encrypted_birth_time" in encrypted
        assert "encrypted_birth_location" in encrypted
        assert all(isinstance(v, bytes) for v in encrypted.values())

    def test_decrypt_birth_data(self):
        """Test birth data decryption."""
        encryption = EncryptionService("test-secret-key-32-characters!!")
        manager = DataProtectionManager(encryption)

        birth_date = "1990-05-15"
        birth_time = "14:30"
        birth_location = "Moscow, Russia"

        encrypted = manager.encrypt_birth_data(
            birth_date, birth_time, birth_location
        )
        decrypted = manager.decrypt_birth_data(
            encrypted["encrypted_birth_date"],
            encrypted["encrypted_birth_time"],
            encrypted["encrypted_birth_location"],
        )

        assert decrypted["birth_date"] == birth_date
        assert decrypted["birth_time"] == birth_time
        assert decrypted["birth_location"] == birth_location

    def test_encrypt_decrypt_name(self):
        """Test name encryption and decryption."""
        encryption = EncryptionService("test-secret-key-32-characters!!")
        manager = DataProtectionManager(encryption)

        name = "John Doe"
        encrypted = manager.encrypt_name(name)
        decrypted = manager.decrypt_name(encrypted)

        assert decrypted == name
        assert isinstance(encrypted, bytes)

    def test_should_delete_user_data(self):
        """Test user data deletion policy."""
        encryption = EncryptionService("test-secret-key-32-characters!!")
        manager = DataProtectionManager(encryption)

        old_date = datetime.utcnow() - timedelta(days=400)
        recent_date = datetime.utcnow() - timedelta(days=100)

        assert manager.should_delete_user_data(old_date, 365)
        assert not manager.should_delete_user_data(recent_date, 365)


@pytest.mark.asyncio
class TestUserManager:
    """Tests for user manager."""

    async def test_get_or_create_user_new(self):
        """Test creating a new user."""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        manager = UserManager(mock_db)

        _ = await manager.get_or_create_user("test_yandex_id")

        assert mock_db.add.called
        assert mock_db.commit.called

    async def test_get_or_create_user_existing(self):
        """Test getting an existing user."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.yandex_user_id = "test_yandex_id"

        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = (
            mock_user
        )
        mock_db.commit = AsyncMock()

        manager = UserManager(mock_db)

        user = await manager.get_or_create_user("test_yandex_id")

        assert user == mock_user
        assert not mock_db.add.called
        assert mock_db.commit.called  # For updating last_accessed

    async def test_update_user_birth_data(self):
        """Test updating user birth data."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        manager = UserManager(mock_db)
        user_id = uuid.uuid4()

        result = await manager.update_user_birth_data(
            user_id, "1990-05-15", "14:30", "Moscow, Russia", "Taurus"
        )

        assert result is True
        assert mock_db.execute.called
        assert mock_db.commit.called

    async def test_set_data_consent(self):
        """Test setting data consent."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        manager = UserManager(mock_db)
        user_id = uuid.uuid4()

        result = await manager.set_data_consent(user_id, True, 365)

        assert result is True
        assert mock_db.execute.called
        assert mock_db.commit.called


@pytest.mark.asyncio
class TestSessionManager:
    """Tests for session manager."""

    async def test_create_session(self):
        """Test creating a new session."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        manager = SessionManager(mock_db)
        user_id = uuid.uuid4()
        session_id = "test_session_id"

        _ = await manager.create_session(user_id, session_id)

        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    async def test_get_active_session(self):
        """Test getting an active session."""
        mock_session = MagicMock()
        mock_session.expires_at = datetime.utcnow() + timedelta(hours=1)

        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = (
            mock_session
        )

        manager = SessionManager(mock_db)

        session = await manager.get_active_session("test_session_id")

        assert session == mock_session

    async def test_get_expired_session(self):
        """Test getting an expired session."""
        mock_session = MagicMock()
        mock_session.expires_at = datetime.utcnow() - timedelta(hours=1)
        mock_session.is_active = True

        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = (
            mock_session
        )
        mock_db.commit = AsyncMock()

        manager = SessionManager(mock_db)

        session = await manager.get_active_session("test_session_id")

        assert session is None
        assert mock_session.is_active is False
        assert mock_db.commit.called

    async def test_update_session_state(self):
        """Test updating session state."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        manager = SessionManager(mock_db)

        result = await manager.update_session_state(
            "test_session_id", "waiting_birth_date", {"some": "context"}
        )

        assert result is True
        assert mock_db.execute.called
        assert mock_db.commit.called


@pytest.mark.asyncio
class TestGDPRCompliance:
    """Tests for GDPR compliance service."""

    async def test_get_user_data_summary(self):
        """Test getting user data summary."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.yandex_user_id = "test_id"
        mock_user.created_at = datetime.utcnow()
        mock_user.last_accessed = datetime.utcnow()
        mock_user.data_consent = True
        mock_user.data_retention_days = 365
        mock_user.zodiac_sign = "Taurus"
        mock_user.gender = "M"
        mock_user.encrypted_name = b"encrypted_name"

        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = (
            mock_user
        )
        mock_db.execute.return_value.scalar.return_value = 5  # horoscope count

        service = GDPRComplianceService(mock_db)
        service.user_manager.get_user_birth_data = AsyncMock(
            return_value={"birth_date": "1990-05-15", "birth_time": "14:30"}
        )

        summary = await service.get_user_data_summary(mock_user.id)

        assert summary is not None
        assert summary["yandex_user_id"] == "test_id"
        assert summary["data_consent"] is True
        assert "personal_data" in summary
        assert "activity_statistics" in summary

    async def test_export_user_data(self):
        """Test exporting user data."""
        mock_db = AsyncMock()
        service = GDPRComplianceService(mock_db)

        # Mock the get_user_data_summary method
        service.get_user_data_summary = AsyncMock(
            return_value={
                "user_id": str(uuid.uuid4()),
                "yandex_user_id": "test_id",
            }
        )
        service._get_horoscope_history = AsyncMock(return_value=[])

        user_id = uuid.uuid4()
        export_data = await service.export_user_data(user_id)

        assert export_data is not None
        assert "export_metadata" in export_data
        assert "user_profile" in export_data
        assert "horoscope_history" in export_data
        assert "legal_notice" in export_data

    async def test_request_data_deletion(self):
        """Test requesting data deletion."""
        mock_db = AsyncMock()
        service = GDPRComplianceService(mock_db)

        # Mock the user manager
        service.user_manager.request_data_deletion = AsyncMock(
            return_value="verification_code"
        )

        user_id = uuid.uuid4()
        code = await service.request_data_deletion(user_id, "User request")

        assert code == "verification_code"
        assert service.user_manager.request_data_deletion.called

    async def test_generate_compliance_report(self):
        """Test generating compliance report."""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar.return_value = 100
        mock_db.execute.return_value.fetchall.return_value = [
            ("data_access", 50),
            ("consent_update", 25),
        ]

        service = GDPRComplianceService(mock_db)

        report = await service.generate_compliance_report()

        assert report is not None
        assert "report_period" in report
        assert "user_statistics" in report
        assert "gdpr_requests" in report
        assert "security_events" in report
        assert "compliance_measures" in report


class TestDataMinimization:
    """Tests for data minimization functionality."""

    def test_extract_essential_birth_data(self):
        """Test extracting essential birth data."""
        from app.services.gdpr_compliance import DataMinimizationService

        full_data = {
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_location": "Moscow, Russia",
            "unnecessary_field": "not needed",
            "another_field": "also not needed",
        }

        essential = DataMinimizationService.extract_essential_birth_data(
            full_data
        )

        assert len(essential) == 3
        assert "birth_date" in essential
        assert "birth_time" in essential
        assert "birth_location" in essential
        assert "unnecessary_field" not in essential

    def test_anonymize_analytics_data(self):
        """Test anonymizing data for analytics."""
        from app.services.gdpr_compliance import DataMinimizationService

        data = {
            "user_id": "12345",
            "yandex_user_id": "yandex_123",
            "birth_date": "1990-05-15",
            "zodiac_sign": "Taurus",
            "request_type": "daily_horoscope",
        }

        anonymized = DataMinimizationService.anonymize_analytics_data(data)

        assert "user_id" not in anonymized
        assert "yandex_user_id" not in anonymized
        assert "birth_date" not in anonymized
        assert "birth_year" in anonymized
        assert "birth_season" in anonymized
        assert anonymized["birth_year"] == 1990
        assert anonymized["birth_season"] == "spring"
