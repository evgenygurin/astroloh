"""
Tests for configuration module.
"""
from unittest.mock import patch

from app.core.config import Settings, settings


class TestSettings:
    """Test configuration settings."""

    def test_settings_default_values(self):
        """Test default settings values."""
        
        class TestSettings(Settings):
            class Config:
                env_file = None  # Don't load .env file
        
        with patch.dict('os.environ', {}, clear=True):
            test_settings = TestSettings()
            
            assert test_settings.DEBUG is False
            assert test_settings.SECRET_KEY is not None
            assert test_settings.API_V1_STR == "/api/v1"
            assert test_settings.PROJECT_NAME == "Astroloh"

    def test_settings_from_environment(self):
        """Test settings loaded from environment variables."""
        with patch.dict('os.environ', {
            'DEBUG': 'true',
            'SECRET_KEY': 'test-secret-key',
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb'
        }):
            test_settings = Settings()
            
            assert test_settings.DEBUG is True
            assert test_settings.SECRET_KEY == 'test-secret-key'
            assert test_settings.DATABASE_URL == 'postgresql://test:test@localhost:5432/testdb'

    def test_settings_singleton(self):
        """Test that settings is a singleton instance."""
        
        assert isinstance(settings, Settings)

    def test_database_url_optional(self):
        """Test that DATABASE_URL is optional."""
        test_settings = Settings()
        
        # DATABASE_URL should be None or string
        assert test_settings.DATABASE_URL is None or isinstance(test_settings.DATABASE_URL, str)

    def test_encryption_key_generation(self):
        """Test encryption key is generated."""
        test_settings = Settings()
        
        assert test_settings.ENCRYPTION_KEY is not None
        assert len(test_settings.ENCRYPTION_KEY) >= 32

    def test_yandex_gpt_settings(self):
        """Test Yandex GPT related settings."""
        test_settings = Settings()
        
        # Should have default or environment values
        assert hasattr(test_settings, 'YANDEX_GPT_API_KEY')
        assert hasattr(test_settings, 'YANDEX_GPT_FOLDER_ID')
        # These can be None in test environment
        assert test_settings.YANDEX_GPT_API_KEY is None or isinstance(test_settings.YANDEX_GPT_API_KEY, str)

    def test_settings_validation(self):
        """Test settings validation."""
        # Test with invalid debug value
        with patch.dict('os.environ', {'DEBUG': 'invalid'}):
            test_settings = Settings()
            # Should handle invalid boolean gracefully - 'invalid' != 'true' so it should be False
            assert test_settings.DEBUG is False

    def test_cors_origins_setting(self):
        """Test CORS origins configuration."""
        test_settings = Settings()
        
        # Should have CORS origins defined
        assert hasattr(test_settings, 'CORS_ORIGINS')
        assert isinstance(test_settings.CORS_ORIGINS, list)

    def test_timezone_setting(self):
        """Test timezone configuration.""" 
        test_settings = Settings()
        
        # Should have timezone setting
        if hasattr(test_settings, 'TIMEZONE'):
            assert isinstance(test_settings.TIMEZONE, str)