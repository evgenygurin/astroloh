"""
Tests for GDPR compliance service.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.gdpr_compliance import GDPRComplianceService


class TestGDPRComplianceService:
    """Test GDPR compliance functionality."""

    def setup_method(self):
        """Setup before each test."""
        self.mock_db = MagicMock()
        # Configure async methods
        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.rollback = AsyncMock()
        self.mock_db.refresh = AsyncMock()
        # Sync methods remain as MagicMock
        self.mock_db.add = MagicMock()
        self.mock_db.delete = MagicMock()
        self.compliance_service = GDPRComplianceService(self.mock_db)
        # Replace the user_manager with a mock
        self.mock_user_manager = AsyncMock()
        self.compliance_service.user_manager = self.mock_user_manager

    @pytest.mark.asyncio
    async def test_get_user_data_summary_existing_user(self):
        """Test getting user data summary for existing user."""
        user_id = uuid.uuid4()

        # Mock user data
        mock_user = MagicMock()
        mock_user.yandex_user_id = "test_user"
        mock_user.created_at = datetime.now()
        mock_user.last_accessed = datetime.now()
        mock_user.data_consent = True
        mock_user.data_retention_days = 365
        mock_user.zodiac_sign = "leo"
        mock_user.gender = "female"
        mock_user.encrypted_name = b"encrypted_name"

        # Setup different mock returns for different database calls
        mock_result_1 = MagicMock()
        mock_result_1.scalar_one_or_none.return_value = mock_user

        mock_result_2 = MagicMock()
        mock_result_2.scalar.return_value = 10

        mock_result_3 = MagicMock()
        mock_result_3.scalar_one_or_none.return_value = datetime.now()

        self.mock_db.execute.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
        ]

        # Mock database write operations
        self.mock_db.add = MagicMock()
        self.mock_db.commit = AsyncMock()

        # Ensure get_user_birth_data returns a coroutine that resolves to the data
        async def mock_get_user_birth_data(user_id):
            return {
                "birth_date": "1990-05-15",
                "birth_time": "14:30",
                "birth_location": "Moscow",
            }

        self.mock_user_manager.get_user_birth_data = mock_get_user_birth_data

        summary = await self.compliance_service.get_user_data_summary(user_id)

        assert summary is not None
        assert summary["user_id"] == str(user_id)
        assert summary["yandex_user_id"] == "test_user"
        assert summary["data_consent"] is True
        assert summary["personal_data"]["zodiac_sign"] == "leo"
        assert summary["activity_statistics"]["total_horoscope_requests"] == 10

    @pytest.mark.asyncio
    async def test_get_user_data_summary_nonexistent_user(self):
        """Test getting user data summary for nonexistent user."""
        user_id = uuid.uuid4()

        # Create properly configured mock result using MagicMock instead of AsyncMock for the result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        # Configure the async execute method to return the mock result
        async def mock_execute(*args, **kwargs):
            return mock_result

        self.mock_db.execute = mock_execute

        summary = await self.compliance_service.get_user_data_summary(user_id)

        assert summary is None

    @pytest.mark.asyncio
    async def test_export_user_data_success(self):
        """Test successful user data export."""
        user_id = uuid.uuid4()

        # Mock summary data
        mock_summary = {
            "user_id": str(user_id),
            "registration_date": datetime.now().isoformat(),
            "data_consent": True,
        }

        with patch.object(
            self.compliance_service,
            "get_user_data_summary",
            return_value=mock_summary,
        ):
            with patch.object(
                self.compliance_service,
                "_get_horoscope_history",
                return_value=[],
            ):
                export_data = await self.compliance_service.export_user_data(user_id)

        assert export_data is not None
        assert "export_metadata" in export_data
        assert "user_profile" in export_data
        assert "horoscope_history" in export_data
        assert "legal_notice" in export_data
        assert export_data["export_metadata"]["format"] == "json"

    @pytest.mark.asyncio
    async def test_export_user_data_no_user(self):
        """Test user data export when user doesn't exist."""
        user_id = uuid.uuid4()

        with patch.object(
            self.compliance_service, "get_user_data_summary", return_value=None
        ):
            export_data = await self.compliance_service.export_user_data(user_id)

        assert export_data is None

    @pytest.mark.asyncio
    async def test_request_data_deletion(self):
        """Test requesting data deletion."""
        user_id = uuid.uuid4()
        reason = "User request"

        self.mock_user_manager.request_data_deletion.return_value = (
            "verification_code_123"
        )

        verification_code = await self.compliance_service.request_data_deletion(
            user_id, reason
        )

        assert verification_code == "verification_code_123"
        self.mock_user_manager.request_data_deletion.assert_called_once_with(
            user_id, reason
        )

    @pytest.mark.asyncio
    async def test_confirm_data_deletion_success(self):
        """Test successful data deletion confirmation."""
        user_id = uuid.uuid4()
        verification_code = "test_code"

        self.mock_user_manager.confirm_data_deletion.return_value = True

        result = await self.compliance_service.confirm_data_deletion(
            user_id, verification_code
        )

        assert result is True
        self.mock_user_manager.confirm_data_deletion.assert_called_once_with(
            user_id, verification_code
        )

    @pytest.mark.asyncio
    async def test_confirm_data_deletion_failure(self):
        """Test failed data deletion confirmation."""
        user_id = uuid.uuid4()
        verification_code = "invalid_code"

        self.mock_user_manager.confirm_data_deletion.return_value = False

        result = await self.compliance_service.confirm_data_deletion(
            user_id, verification_code
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_consent_success(self):
        """Test successful consent update."""
        user_id = uuid.uuid4()

        self.mock_user_manager.set_data_consent.return_value = True

        result = await self.compliance_service.update_consent(
            user_id, True, 365, {"analytics": True, "marketing": False}
        )

        assert result is True
        self.mock_user_manager.set_data_consent.assert_called_once_with(
            user_id, True, 365
        )

    @pytest.mark.asyncio
    async def test_update_consent_failure(self):
        """Test failed consent update."""
        user_id = uuid.uuid4()

        self.mock_user_manager.set_data_consent.return_value = False

        result = await self.compliance_service.update_consent(user_id, False)

        assert result is False

    @pytest.mark.asyncio
    async def test_rectify_user_data_success(self):
        """Test successful user data rectification."""
        user_id = uuid.uuid4()
        correction_data = {"birth_date": "1990-06-15", "gender": "male"}

        self.mock_user_manager.update_user_birth_data.return_value = True

        result = await self.compliance_service.rectify_user_data(
            user_id, correction_data
        )

        assert result is True
        self.mock_user_manager.update_user_birth_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_rectify_user_data_failure(self):
        """Test failed user data rectification."""
        user_id = uuid.uuid4()
        correction_data = {"birth_date": "invalid_date"}

        self.mock_user_manager.update_user_birth_data.return_value = False

        result = await self.compliance_service.rectify_user_data(
            user_id, correction_data
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_rectify_user_data_exception(self):
        """Test user data rectification with exception."""
        user_id = uuid.uuid4()
        correction_data = {"gender": "female"}

        self.mock_db.execute.side_effect = Exception("Database error")

        result = await self.compliance_service.rectify_user_data(
            user_id, correction_data
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_restrict_processing_enable(self):
        """Test enabling processing restriction."""
        user_id = uuid.uuid4()

        self.mock_user_manager.set_data_consent.return_value = True

        result = await self.compliance_service.restrict_processing(
            user_id, True, "User request for restriction"
        )

        assert result is True
        # When restricting, consent should be set to False
        self.mock_user_manager.set_data_consent.assert_called_once_with(
            user_id, False, 365
        )

    @pytest.mark.asyncio
    async def test_restrict_processing_disable(self):
        """Test disabling processing restriction."""
        user_id = uuid.uuid4()

        self.mock_user_manager.set_data_consent.return_value = True

        result = await self.compliance_service.restrict_processing(
            user_id, False, "Restore processing"
        )

        assert result is True
        # When unrestricting, consent should be set to True
        self.mock_user_manager.set_data_consent.assert_called_once_with(
            user_id, True, 365
        )

    @pytest.mark.asyncio
    async def test_restrict_processing_failure(self):
        """Test failed processing restriction."""
        user_id = uuid.uuid4()

        self.mock_user_manager.set_data_consent.side_effect = Exception("Error")

        result = await self.compliance_service.restrict_processing(user_id, True)

        assert result is False

    @pytest.mark.asyncio
    async def test_generate_compliance_report(self):
        """Test generating compliance report."""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        # Mock the execute calls with different results
        mock_result_1 = MagicMock()
        mock_result_1.scalar.return_value = 100  # total users

        mock_result_2 = MagicMock()
        mock_result_2.scalar.return_value = 80  # consented users

        mock_result_3 = MagicMock()
        mock_result_3.scalar.return_value = 5  # deletion requests

        # Mock security events result
        mock_result_4 = MagicMock()
        mock_result_4.all.return_value = [
            ("user_creation", 10),
            ("data_access", 50),
            ("data_deletion", 5),
        ]

        self.mock_db.execute.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
        ]

        report = await self.compliance_service.generate_compliance_report(
            start_date, end_date
        )

        assert report is not None
        assert "report_period" in report
        assert "user_statistics" in report
        assert "gdpr_requests" in report
        assert "security_events" in report
        assert "compliance_measures" in report

        assert report["user_statistics"]["total_users"] == 100
        assert report["user_statistics"]["users_with_consent"] == 80
        assert report["user_statistics"]["consent_rate"] == 80.0
        assert report["gdpr_requests"]["deletion_requests"] == 5

    @pytest.mark.asyncio
    async def test_generate_compliance_report_default_dates(self):
        """Test generating compliance report with default dates."""
        # Mock database results
        mock_result_1 = MagicMock()
        mock_result_1.scalar.return_value = 50

        mock_result_2 = MagicMock()
        mock_result_2.scalar.return_value = 40

        mock_result_3 = MagicMock()
        mock_result_3.scalar.return_value = 2

        mock_result_4 = MagicMock()
        mock_result_4.all.return_value = []

        self.mock_db.execute.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
        ]

        report = await self.compliance_service.generate_compliance_report()

        assert report is not None
        assert "report_period" in report
        # Should use default 30-day period
        start_date = datetime.fromisoformat(report["report_period"]["start_date"])
        end_date = datetime.fromisoformat(report["report_period"]["end_date"])
        assert (end_date - start_date).days >= 29  # Account for timing differences

    @pytest.mark.asyncio
    async def test_get_horoscope_history(self):
        """Test getting horoscope history."""
        user_id = uuid.uuid4()

        # Mock horoscope requests
        mock_requests = []
        for i in range(3):
            req = MagicMock()
            req.request_type = f"daily_{i}"
            req.processed_at = datetime.now() - timedelta(days=i)
            req.encrypted_target_date = b"encrypted" if i % 2 == 0 else None
            req.encrypted_partner_data = b"partner_data" if i == 1 else None
            mock_requests.append(req)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_requests
        mock_result.scalars.return_value = mock_scalars
        self.mock_db.execute.return_value = mock_result

        history = await self.compliance_service._get_horoscope_history(user_id)

        assert len(history) == 3
        assert history[0]["request_type"] == "daily_0"
        assert history[0]["has_target_date"] is True
        assert history[0]["has_partner_data"] is False
        assert history[1]["has_partner_data"] is True

    @pytest.mark.asyncio
    async def test_log_compliance_event(self):
        """Test logging compliance events."""
        user_id = uuid.uuid4()

        await self.compliance_service._log_compliance_event(
            event_type="test_event",
            description="Test description",
            success=True,
            user_id=user_id,
            error_message=None,
        )

        # Verify that a log entry was added to the database
        assert self.mock_db.add.called
        log_entry = self.mock_db.add.call_args[0][0]
        assert log_entry.event_type == "gdpr_test_event"
        assert log_entry.description == "Test description"
        assert log_entry.success is True
        assert log_entry.user_id == user_id

    @pytest.mark.asyncio
    async def test_data_minimization_extract_essential_birth_data(self):
        """Test extracting essential birth data."""
        from app.services.gdpr_compliance import DataMinimizationService

        full_data = {
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_location": "Moscow",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
        }

        essential_data = DataMinimizationService.extract_essential_birth_data(full_data)

        assert "birth_date" in essential_data
        assert "birth_time" in essential_data
        assert "birth_location" in essential_data
        assert "name" not in essential_data
        assert "email" not in essential_data
        assert "phone" not in essential_data

    @pytest.mark.asyncio
    async def test_data_minimization_anonymize_analytics_data(self):
        """Test anonymizing analytics data."""
        from app.services.gdpr_compliance import DataMinimizationService

        data = {
            "user_id": "user_123",
            "yandex_user_id": "yandex_456",
            "name": "John Doe",
            "birth_date": "1990-05-15T00:00:00",
            "request_count": 10,
            "zodiac_sign": "taurus",
        }

        anonymized = DataMinimizationService.anonymize_analytics_data(data)

        assert "user_id" not in anonymized
        assert "yandex_user_id" not in anonymized
        assert "name" not in anonymized
        assert "birth_date" not in anonymized
        assert "birth_year" in anonymized
        assert "birth_season" in anonymized
        assert anonymized["birth_year"] == 1990
        assert anonymized["birth_season"] == "spring"
        assert anonymized["request_count"] == 10
        assert anonymized["zodiac_sign"] == "taurus"

    @pytest.mark.asyncio
    async def test_data_minimization_get_season(self):
        """Test season determination."""
        from app.services.gdpr_compliance import DataMinimizationService

        assert DataMinimizationService._get_season(1) == "winter"
        assert DataMinimizationService._get_season(3) == "spring"
        assert DataMinimizationService._get_season(6) == "summer"
        assert DataMinimizationService._get_season(9) == "autumn"
        assert DataMinimizationService._get_season(13) == "unknown"

    @pytest.mark.asyncio
    async def test_error_handling_in_summary(self):
        """Test error handling in get_user_data_summary."""
        user_id = uuid.uuid4()

        self.mock_db.execute.side_effect = Exception("Database error")

        summary = await self.compliance_service.get_user_data_summary(user_id)

        assert summary is None

    @pytest.mark.asyncio
    async def test_compliance_with_zero_users(self):
        """Test compliance report with zero users."""
        # Mock zero users
        mock_result_1 = MagicMock()
        mock_result_1.scalar.return_value = 0

        mock_result_2 = MagicMock()
        mock_result_2.scalar.return_value = 0

        mock_result_3 = MagicMock()
        mock_result_3.scalar.return_value = 0

        mock_result_4 = MagicMock()
        mock_result_4.all.return_value = []

        self.mock_db.execute.side_effect = [
            mock_result_1,
            mock_result_2,
            mock_result_3,
            mock_result_4,
        ]

        report = await self.compliance_service.generate_compliance_report()

        assert report["user_statistics"]["total_users"] == 0
        assert report["user_statistics"]["consent_rate"] == 0

    @pytest.mark.asyncio
    async def test_rectify_user_data_no_updates(self):
        """Test rectification with no actual updates needed."""
        user_id = uuid.uuid4()
        correction_data = {"unknown_field": "value"}

        result = await self.compliance_service.rectify_user_data(
            user_id, correction_data
        )

        assert result is True  # Should succeed even with no actual updates
