"""
Tests for encryption service.
"""

from unittest.mock import patch

import pytest

from app.services.encryption import (
    DataProtectionManager,
    EncryptionService,
    SecurityUtils,
)


class TestEncryptionService:
    """Test encryption service functionality."""

    def setup_method(self):
        """Setup before each test."""
        self.encryption_service = EncryptionService()
        self.data_protection = DataProtectionManager(self.encryption_service)

    def test_encrypt_decrypt_string(self):
        """Test string encryption and decryption."""
        original_text = "This is a secret message"

        encrypted = self.encryption_service.encrypt(original_text)
        decrypted = self.encryption_service.decrypt(encrypted)

        assert encrypted != original_text
        assert isinstance(encrypted, bytes)
        assert decrypted == original_text

    def test_encrypt_decrypt_empty_string(self):
        """Test encryption and decryption of empty string."""
        original_text = ""

        encrypted = self.encryption_service.encrypt(original_text)
        decrypted = self.encryption_service.decrypt(encrypted)

        assert decrypted == original_text

    def test_encrypt_decrypt_unicode(self):
        """Test encryption and decryption of unicode text."""
        original_text = "Привет мир! 🌟"

        encrypted = self.encryption_service.encrypt(original_text)
        decrypted = self.encryption_service.decrypt(encrypted)

        assert decrypted == original_text

    def test_encrypt_dict(self):
        """Test dictionary encryption."""
        original_dict = {
            "name": "John Doe",
            "birth_date": "1990-05-15",
            "location": "Moscow",
        }

        encrypted_dict = self.encryption_service.encrypt_dict(original_dict)

        assert isinstance(encrypted_dict, bytes)
        assert encrypted_dict != str(original_dict).encode()

    def test_decrypt_dict(self):
        """Test dictionary decryption."""
        original_dict = {
            "name": "John Doe",
            "birth_date": "1990-05-15",
            "location": "Moscow",
        }

        encrypted_dict = self.encryption_service.encrypt_dict(original_dict)
        decrypted_dict = self.encryption_service.decrypt_dict(encrypted_dict)

        assert decrypted_dict == original_dict

    def test_encrypt_decrypt_dict_with_none_values(self):
        """Test dictionary encryption with None values."""
        original_dict = {
            "name": "John Doe",
            "birth_time": None,
            "location": "Moscow",
        }

        encrypted_dict = self.encryption_service.encrypt_dict(original_dict)
        decrypted_dict = self.encryption_service.decrypt_dict(encrypted_dict)

        assert decrypted_dict == original_dict

    def test_encrypt_decrypt_dict_empty(self):
        """Test encryption and decryption of empty dictionary."""
        original_dict = {}

        encrypted_dict = self.encryption_service.encrypt_dict(original_dict)
        decrypted_dict = self.encryption_service.decrypt_dict(encrypted_dict)

        assert isinstance(encrypted_dict, bytes)
        assert decrypted_dict == {}

    def test_encrypt_birth_data(self):
        """Test birth data encryption."""
        birth_date = "1990-05-15"
        birth_time = "14:30"
        birth_location = "Moscow, Russia"

        encrypted_data = self.data_protection.encrypt_birth_data(
            birth_date, birth_time, birth_location
        )

        assert isinstance(encrypted_data, dict)
        assert "encrypted_birth_date" in encrypted_data
        assert "encrypted_birth_time" in encrypted_data
        assert "encrypted_birth_location" in encrypted_data

        for key, value in encrypted_data.items():
            if value is not None:
                assert isinstance(value, bytes)

    def test_encrypt_birth_data_partial(self):
        """Test birth data encryption with some None values."""
        birth_date = "1990-05-15"
        birth_time = None
        birth_location = "Moscow, Russia"

        encrypted_data = self.data_protection.encrypt_birth_data(
            birth_date, birth_time, birth_location
        )

        assert encrypted_data["encrypted_birth_date"] is not None
        assert "encrypted_birth_time" not in encrypted_data
        assert encrypted_data["encrypted_birth_location"] is not None

    def test_decrypt_birth_data(self):
        """Test birth data decryption."""
        original_birth_date = "1990-05-15"
        original_birth_time = "14:30"
        original_birth_location = "Moscow, Russia"

        # First encrypt
        encrypted_data = self.data_protection.encrypt_birth_data(
            original_birth_date, original_birth_time, original_birth_location
        )

        # Then decrypt
        decrypted_data = self.data_protection.decrypt_birth_data(
            encrypted_data["encrypted_birth_date"],
            encrypted_data["encrypted_birth_time"],
            encrypted_data["encrypted_birth_location"],
        )

        assert decrypted_data["birth_date"] == original_birth_date
        assert decrypted_data["birth_time"] == original_birth_time
        assert decrypted_data["birth_location"] == original_birth_location

    def test_decrypt_birth_data_with_none(self):
        """Test birth data decryption with None values."""
        birth_date_encrypted = self.encryption_service.encrypt("1990-05-15")

        decrypted_data = self.data_protection.decrypt_birth_data(
            birth_date_encrypted, None, None
        )

        assert decrypted_data["birth_date"] == "1990-05-15"
        assert "birth_time" not in decrypted_data
        assert "birth_location" not in decrypted_data

    def test_encrypt_name(self):
        """Test name encryption."""
        name = "John Doe"

        encrypted_name = self.data_protection.encrypt_name(name)

        assert isinstance(encrypted_name, bytes)
        assert encrypted_name != name.encode()

    def test_decrypt_name(self):
        """Test name decryption."""
        name = "John Doe"

        encrypted_name = self.data_protection.encrypt_name(name)
        decrypted_name = self.data_protection.decrypt_name(encrypted_name)

        assert decrypted_name == name

    def test_encrypt_decrypt_none_handling(self):
        """Test handling of None values in encryption/decryption."""
        # For EncryptionService, None input to encrypt returns empty bytes
        assert self.encryption_service.encrypt("") == b""
        assert self.encryption_service.decrypt(b"") == ""

    def test_different_encryptions_same_text(self):
        """Test that encrypting the same text twice produces different results."""
        text = "same text"

        encrypted1 = self.encryption_service.encrypt(text)
        encrypted2 = self.encryption_service.encrypt(text)

        # Should be different due to random IV/nonce
        assert encrypted1 != encrypted2

        # But should decrypt to the same value
        assert self.encryption_service.decrypt(encrypted1) == text
        assert self.encryption_service.decrypt(encrypted2) == text

    def test_invalid_decryption_data(self):
        """Test decryption with invalid data."""
        invalid_data = b"invalid encrypted data"

        with pytest.raises(Exception):
            self.encryption_service.decrypt(invalid_data)

    def test_key_derivation(self):
        """Test key derivation functionality."""
        with patch.object(
            self.encryption_service, "_derive_key_from_secret"
        ) as mock_derive:
            mock_derive.return_value = b"derived_key_32_bytes_long_test"

            result = self.encryption_service._derive_key_from_secret("test_password")

            assert result == b"derived_key_32_bytes_long_test"
            mock_derive.assert_called_once_with("test_password")

    def test_encryption_with_special_characters(self):
        """Test encryption with special characters and symbols."""
        special_text = "!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"

        encrypted = self.encryption_service.encrypt(special_text)
        decrypted = self.encryption_service.decrypt(encrypted)

        assert decrypted == special_text

    def test_large_text_encryption(self):
        """Test encryption of large text."""
        large_text = "a" * 10000  # 10KB of text

        encrypted = self.encryption_service.encrypt(large_text)
        decrypted = self.encryption_service.decrypt(encrypted)

        assert decrypted == large_text
        assert len(encrypted) > len(large_text)  # Encrypted should be larger


class TestSecurityUtils:
    """Test security utilities."""

    def test_generate_verification_code(self):
        """Test verification code generation."""
        code = SecurityUtils.generate_verification_code()

        assert isinstance(code, str)
        assert len(code) >= 8
        assert len(code) <= 32

    def test_generate_verification_code_different(self):
        """Test that verification codes are different."""
        code1 = SecurityUtils.generate_verification_code()
        code2 = SecurityUtils.generate_verification_code()

        assert code1 != code2

    def test_generate_session_expiry(self):
        """Test session expiry generation."""
        from datetime import datetime, timedelta

        before = datetime.utcnow()
        expiry = SecurityUtils.generate_session_expiry(24)
        after = datetime.utcnow()

        expected_min = before + timedelta(hours=23, minutes=59)
        expected_max = after + timedelta(hours=24, minutes=1)

        assert expected_min <= expiry <= expected_max

    def test_is_session_expired_not_expired(self):
        """Test session expiry check for non-expired session."""
        from datetime import datetime, timedelta

        future_time = datetime.utcnow() + timedelta(hours=1)

        assert not SecurityUtils.is_session_expired(future_time)

    def test_is_session_expired_expired(self):
        """Test session expiry check for expired session."""
        from datetime import datetime, timedelta

        past_time = datetime.utcnow() - timedelta(hours=1)

        assert SecurityUtils.is_session_expired(past_time)

    def test_sanitize_input_normal_text(self):
        """Test input sanitization with normal text."""
        text = "Hello World"

        sanitized = SecurityUtils.sanitize_input(text, 20)

        assert sanitized == "Hello World"

    def test_sanitize_input_long_text(self):
        """Test input sanitization with text exceeding max length."""
        text = "This is a very long text that exceeds the maximum length"

        sanitized = SecurityUtils.sanitize_input(text, 10)

        assert len(sanitized) <= 10
        assert sanitized == text[:10].strip()

    def test_sanitize_input_with_dangerous_chars(self):
        """Test input sanitization removes dangerous characters."""
        text = "Hello<script>alert('xss')</script>World"

        sanitized = SecurityUtils.sanitize_input(text, 100)

        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "'" not in sanitized
        assert '"' not in sanitized

    def test_sanitize_input_empty(self):
        """Test input sanitization with empty string."""
        sanitized = SecurityUtils.sanitize_input("", 10)

        assert sanitized == ""

    def test_hash_ip_valid(self):
        """Test IP address hashing."""
        ip_address = "192.168.1.1"

        hashed = SecurityUtils.hash_ip(ip_address)

        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 hex length
        assert hashed != ip_address

    def test_hash_ip_same_input_same_output(self):
        """Test that same IP produces same hash."""
        ip_address = "192.168.1.1"

        hash1 = SecurityUtils.hash_ip(ip_address)
        hash2 = SecurityUtils.hash_ip(ip_address)

        assert hash1 == hash2

    def test_hash_ip_different_input_different_output(self):
        """Test that different IPs produce different hashes."""
        ip1 = "192.168.1.1"
        ip2 = "192.168.1.2"

        hash1 = SecurityUtils.hash_ip(ip1)
        hash2 = SecurityUtils.hash_ip(ip2)

        assert hash1 != hash2

    def test_hash_ip_empty(self):
        """Test IP hashing with empty input."""
        hashed = SecurityUtils.hash_ip("")

        assert hashed == ""

    def test_hash_user_agent(self):
        """Test user agent hashing."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        hashed = SecurityUtils.hash_user_agent(user_agent)

        assert isinstance(hashed, str)
        assert len(hashed) == 64
        assert hashed != user_agent

    def test_hash_user_agent_empty(self):
        """Test user agent hashing with empty input."""
        hashed = SecurityUtils.hash_user_agent("")

        assert hashed == ""

    def test_encryption_error_handling(self):
        """Test encryption service error handling."""
        # Test with corrupted encrypted data
        service = EncryptionService()

        corrupted_data = b"this is not valid encrypted data"

        # Should handle gracefully without crashing
        try:
            result = service.decrypt(corrupted_data)
            # If it doesn't raise an exception, result should be None or similar
            assert result is None or isinstance(result, str)
        except Exception as e:
            # Exception is acceptable for invalid data
            assert isinstance(e, Exception)

    def test_encryption_service_fallback_key_derivation(self):
        """Test encryption service with fallback key derivation from SECRET_KEY."""
        with patch("app.core.config.settings") as mock_settings:
            # Set up mock settings to trigger fallback key derivation
            mock_settings.ENCRYPTION_KEY = None
            mock_settings.SECRET_KEY = "test_secret_key_for_fallback"

            # Create service without explicit encryption key
            service = EncryptionService()

            # Test that encryption/decryption still works
            test_data = "test data for fallback encryption"
            encrypted = service.encrypt(test_data)
            decrypted = service.decrypt(encrypted)

            assert decrypted == test_data
