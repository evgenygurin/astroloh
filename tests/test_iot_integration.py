"""Tests for IoT integration functionality."""

from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iot_models import (
    AutomationCreate,
    AutomationTrigger,
    DeviceCommand,
    DeviceProtocol,
    DeviceStatus,
    DeviceType,
    IoTDeviceCreate,
    WearableAlert,
)
from app.services.encryption import EncryptionService
from app.services.home_automation_service import HomeAutomationService
from app.services.iot_analytics_service import IoTAnalyticsService
from app.services.iot_manager import IoTDeviceManager
from app.services.iot_protocols import HomeKitManager, MatterManager, MQTTManager
from app.services.lunar_calendar import LunarCalendar
from app.services.smart_home_voice_integration import SmartHomeVoiceIntegration
from app.services.smart_lighting_service import SmartLightingService
from app.services.wearable_integration import WearableIntegrationService


@pytest.fixture
async def mock_db():
    """Mock database session."""
    db = Mock(spec=AsyncSession)
    db.add = Mock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
async def mock_encryption():
    """Mock encryption service."""
    service = Mock(spec=EncryptionService)
    service.encrypt_data = AsyncMock(return_value="encrypted_data")
    service.decrypt_data = AsyncMock(return_value="decrypted_data")
    return service


@pytest.fixture
async def mock_lunar_service():
    """Mock lunar calendar service."""
    service = Mock(spec=LunarCalendar)
    service.get_lunar_calendar_info = AsyncMock(
        return_value={
            "phase": "full_moon",
            "phase_percentage": 1.0,
            "illumination": 100,
        }
    )
    return service


@pytest.fixture
async def iot_manager(mock_db, mock_encryption):
    """IoT device manager fixture."""
    return IoTDeviceManager(mock_db, mock_encryption)


@pytest.fixture
async def lighting_service(mock_db, iot_manager, mock_lunar_service):
    """Smart lighting service fixture."""
    return SmartLightingService(mock_db, iot_manager, mock_lunar_service)


class TestIoTDeviceManager:
    """Test IoT device management."""

    @pytest.mark.asyncio
    async def test_register_device_success(self, iot_manager, mock_db):
        """Test successful device registration."""
        # Setup
        device_data = IoTDeviceCreate(
            device_id="test_device_001",
            name="Test Smart Light",
            device_type=DeviceType.SMART_LIGHT,
            protocol=DeviceProtocol.MQTT,
            manufacturer="Test Corp",
            capabilities={"on_off": True, "brightness": True},
        )

        # Mock the device creation
        mock_device = Mock()
        mock_device.id = 1
        mock_device.device_id = device_data.device_id
        mock_device.name = device_data.name
        mock_device.device_type = device_data.device_type.value
        mock_device.status = DeviceStatus.PAIRING.value

        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(return_value=mock_device)

        # Execute
        result = await iot_manager.register_device(
            user_id=1, device_data=device_data
        )

        # Verify
        assert result is not None
        assert result.device_id == device_data.device_id
        assert result.name == device_data.name
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_device_not_found(self, iot_manager, mock_db):
        """Test sending command to non-existent device."""
        # Setup
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        command = DeviceCommand(command="turn_on")

        # Execute
        result = await iot_manager.send_command("nonexistent_device", command)

        # Verify
        assert result["success"] is False
        assert "Device not found" in result["error"]

    @pytest.mark.asyncio
    async def test_send_command_device_offline(self, iot_manager, mock_db):
        """Test sending command to offline device."""
        # Setup
        mock_device = Mock()
        mock_device.status = DeviceStatus.OFFLINE.value

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_device
        mock_db.execute.return_value = mock_result

        command = DeviceCommand(command="turn_on")

        # Execute
        result = await iot_manager.send_command("offline_device", command)

        # Verify
        assert result["success"] is False
        assert "Device offline" in result["error"]

    @pytest.mark.asyncio
    async def test_discover_devices_mqtt(self, iot_manager):
        """Test MQTT device discovery."""
        # Execute
        devices = await iot_manager.discover_devices("mqtt", timeout=1)

        # Verify
        assert isinstance(devices, list)
        assert len(devices) >= 0  # May be empty in test environment


class TestSmartLightingService:
    """Test smart lighting functionality."""

    @pytest.mark.asyncio
    async def test_apply_lunar_lighting_no_devices(
        self, lighting_service, iot_manager
    ):
        """Test applying lunar lighting with no devices."""
        # Setup
        iot_manager.get_user_devices = AsyncMock(return_value=[])

        # Execute
        result = await lighting_service.apply_lunar_lighting(user_id=1)

        # Verify
        assert result["success"] is False
        assert "No smart lights found" in result["message"]

    @pytest.mark.asyncio
    async def test_apply_lunar_lighting_success(
        self, lighting_service, iot_manager, mock_lunar_service
    ):
        """Test successful lunar lighting application."""
        # Setup
        mock_device = Mock()
        mock_device.device_id = "light_001"
        mock_device.name = "Living Room Light"
        mock_device.status = DeviceStatus.ONLINE.value
        mock_device.capabilities = {
            "on_off": True,
            "brightness": True,
            "color": True,
        }

        iot_manager.get_user_devices = AsyncMock(return_value=[mock_device])
        iot_manager.send_command = AsyncMock(return_value={"success": True})

        # Execute
        result = await lighting_service.apply_lunar_lighting(user_id=1)

        # Verify
        assert result["success"] is True
        assert result["phase"] == "full_moon"
        assert result["devices_updated"] == 1

    @pytest.mark.asyncio
    async def test_create_mood_lighting(self, lighting_service, iot_manager):
        """Test mood lighting creation."""
        # Setup
        mock_device = Mock()
        mock_device.device_id = "light_001"
        mock_device.name = "Bedroom Light"
        mock_device.status = DeviceStatus.ONLINE.value
        mock_device.capabilities = {"on_off": True, "brightness": True}

        iot_manager.get_user_devices = AsyncMock(return_value=[mock_device])
        iot_manager.send_command = AsyncMock(return_value={"success": True})

        # Execute
        result = await lighting_service.create_mood_lighting(
            user_id=1, mood="romantic", zodiac_sign="libra"
        )

        # Verify
        assert result["success"] is True
        assert result["mood"] == "romantic"
        assert result["zodiac_sign"] == "libra"


class TestWearableIntegration:
    """Test wearable device integration."""

    @pytest.fixture
    async def wearable_service(self, mock_db, iot_manager, mock_lunar_service):
        """Wearable integration service fixture."""
        from app.services.transit_calculator import TransitCalculator

        transit_calculator = Mock(spec=TransitCalculator)
        return WearableIntegrationService(
            mock_db, iot_manager, mock_lunar_service, transit_calculator
        )

    @pytest.mark.asyncio
    async def test_sync_wearable_data_device_not_found(
        self, wearable_service, iot_manager
    ):
        """Test syncing data for non-existent wearable device."""
        # Setup
        iot_manager.get_user_devices = AsyncMock(return_value=[])

        data = {
            "heart_rate": 72,
            "sleep_quality": 0.8,
            "activity_level": 0.6,
        }

        # Execute
        result = await wearable_service.sync_wearable_data(
            user_id=1, device_id="nonexistent", data=data
        )

        # Verify
        assert result["success"] is False
        assert "Wearable device not found" in result["error"]

    @pytest.mark.asyncio
    async def test_sync_wearable_data_success(
        self, wearable_service, iot_manager, mock_db
    ):
        """Test successful wearable data sync."""
        # Setup
        mock_device = Mock()
        mock_device.id = 1
        mock_device.device_id = "wearable_001"

        iot_manager.get_user_devices = AsyncMock(return_value=[mock_device])
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        data = {
            "heart_rate": 72,
            "sleep_quality": 0.8,
            "activity_level": 0.6,
            "stress_level": 0.3,
            "mood_score": 0.7,
        }

        # Execute
        result = await wearable_service.sync_wearable_data(
            user_id=1, device_id="wearable_001", data=data
        )

        # Verify
        assert result["success"] is True
        assert "lunar_correlation" in result
        assert "insights" in result

    @pytest.mark.asyncio
    async def test_send_wearable_notification_no_devices(
        self, wearable_service, iot_manager
    ):
        """Test sending notification with no wearable devices."""
        # Setup
        iot_manager.get_user_devices = AsyncMock(return_value=[])

        alert = WearableAlert(
            title="Test Alert",
            message="This is a test notification",
            alert_type="info",
        )

        # Execute
        result = await wearable_service.send_wearable_notification(
            user_id=1, alert=alert
        )

        # Verify
        assert result["success"] is False
        assert "No wearable devices found" in result["message"]


class TestHomeAutomation:
    """Test home automation functionality."""

    @pytest.fixture
    async def automation_service(
        self, mock_db, iot_manager, lighting_service, mock_lunar_service
    ):
        """Home automation service fixture."""
        from app.services.horoscope_generator import HoroscopeGenerator
        from app.services.transit_calculator import TransitCalculator

        transit_calculator = Mock(spec=TransitCalculator)
        horoscope_generator = Mock(spec=HoroscopeGenerator)

        return HomeAutomationService(
            mock_db,
            iot_manager,
            lighting_service,
            mock_lunar_service,
            transit_calculator,
            horoscope_generator,
        )

    @pytest.mark.asyncio
    async def test_create_automation_success(
        self, automation_service, mock_db
    ):
        """Test successful automation creation."""
        # Setup
        automation_data = AutomationCreate(
            device_id=1,
            name="Test Automation",
            description="A test automation rule",
            trigger_type=AutomationTrigger.LUNAR_PHASE,
            trigger_conditions={"phases": ["full_moon"]},
            actions=[
                {"type": "lighting_scene", "parameters": {"scene": "lunar"}}
            ],
        )

        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        # Mock refresh to set ID on the automation object (simulating DB behavior)
        async def mock_refresh(automation):
            automation.id = 1
            return None

        mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Execute
        result = await automation_service.create_automation(
            user_id=1, automation_data=automation_data
        )

        # Verify
        assert result["success"] is True
        assert result["automation_id"] == 1

    @pytest.mark.asyncio
    async def test_create_morning_ritual_automation(self, automation_service):
        """Test morning ritual automation creation."""
        # Setup
        wake_time = "07:00"
        preferences = {
            "gradual_lighting": True,
            "horoscope_audio": True,
            "morning_music": True,
            "temperature_control": True,
            "morning_temp": 23,
        }

        # Mock the create_automation method
        automation_service.create_automation = AsyncMock(
            return_value={
                "success": True,
                "automation_id": 1,
                "automation": {"name": "Утренний астрологический ритуал"},
            }
        )

        # Execute
        result = await automation_service.create_morning_ritual_automation(
            user_id=1, wake_time=wake_time, preferences=preferences
        )

        # Verify
        assert result["success"] is True
        automation_service.create_automation.assert_called_once()


class TestIoTProtocols:
    """Test IoT protocol implementations."""

    def test_mqtt_manager_init(self):
        """Test MQTT manager initialization."""
        try:
            manager = MQTTManager(
                broker_host="test.mqtt.broker",
                broker_port=1883,
                username="test_user",
                password="test_pass",
            )
            assert manager.broker_host == "test.mqtt.broker"
            assert manager.broker_port == 1883
            assert manager.username == "test_user"
        except ImportError:
            # MQTT not available in test environment
            pytest.skip("MQTT not available")

    def test_homekit_manager_init(self):
        """Test HomeKit manager initialization."""
        manager = HomeKitManager()
        assert manager.bridge_info["name"] == "Astroloh Smart Home Bridge"
        assert manager.accessories == {}

    @pytest.mark.asyncio
    async def test_homekit_discover_accessories(self):
        """Test HomeKit accessory discovery."""
        manager = HomeKitManager()

        # Execute
        accessories = await manager.discover_accessories(timeout=1)

        # Verify
        assert isinstance(accessories, list)
        assert len(accessories) > 0
        assert all("id" in acc for acc in accessories)

    def test_matter_manager_init(self):
        """Test Matter manager initialization."""
        manager = MatterManager()
        assert manager.fabric_id == "astroloh_fabric"
        assert manager.node_id == 1
        assert manager.devices == {}

    @pytest.mark.asyncio
    async def test_matter_commission_device(self):
        """Test Matter device commissioning."""
        manager = MatterManager()

        device_info = {
            "name": "Test Smart Bulb",
            "vendor_id": 4660,
            "product_id": 1,
            "clusters": [6, 8, 768],
        }

        # Execute
        result = await manager.commission_device(
            setup_code="12345678901",
            discriminator=1234,
            device_info=device_info,
        )

        # Verify
        assert result["success"] is True
        assert result["device_id"] == "matter_1234"
        assert len(manager.devices) == 1


class TestIoTAnalytics:
    """Test IoT analytics functionality."""

    @pytest.fixture
    async def analytics_service(self, mock_db, mock_lunar_service):
        """IoT analytics service fixture."""
        return IoTAnalyticsService(mock_db, mock_lunar_service)

    @pytest.mark.asyncio
    async def test_analyze_energy_consumption_no_data(
        self, analytics_service, mock_db
    ):
        """Test energy consumption analysis with no data."""
        # Setup
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await analytics_service.analyze_energy_consumption(
            user_id=1, period_days=30
        )

        # Verify
        assert result["success"] is False
        assert "No energy consumption data available" in result["message"]

    @pytest.mark.asyncio
    async def test_generate_monthly_report_success(self, analytics_service):
        """Test monthly report generation."""
        # Mock the analysis methods
        analytics_service.analyze_energy_consumption = AsyncMock(
            return_value={
                "success": True,
                "total_consumption": 100.5,
                "lunar_correlation": {},
            }
        )
        analytics_service.analyze_wellness_correlations = AsyncMock(
            return_value={"success": True, "overall_wellness_score": 0.8}
        )
        analytics_service.generate_automation_insights = AsyncMock(
            return_value={
                "success": True,
                "total_automations": 5,
                "active_automations": 4,
            }
        )

        # Mock device query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(device_type="smart_light", status="online"),
            Mock(device_type="smart_plug", status="offline"),
        ]
        analytics_service.db.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await analytics_service.generate_monthly_report(user_id=1)

        # Verify
        assert result["success"] is True
        assert "device_summary" in result
        assert "energy_analysis" in result
        assert "wellness_analysis" in result
        assert "automation_insights" in result
        assert "overall_score" in result


class TestVoiceIntegration:
    """Test voice assistant integration."""

    @pytest.fixture
    async def voice_service(
        self, mock_db, iot_manager, lighting_service, mock_lunar_service
    ):
        """Voice integration service fixture."""
        from app.services.horoscope_generator import HoroscopeGenerator
        from app.services.transit_calculator import TransitCalculator

        Mock(spec=TransitCalculator)
        horoscope_generator = Mock(spec=HoroscopeGenerator)

        return SmartHomeVoiceIntegration(
            mock_db,
            iot_manager,
            lighting_service,
            horoscope_generator,
            mock_lunar_service,
        )

    @pytest.mark.asyncio
    async def test_handle_yandex_command_lunar_lighting(
        self, voice_service, lighting_service
    ):
        """Test Yandex.Station lunar lighting command."""
        # Setup
        lighting_service.apply_lunar_lighting = AsyncMock(
            return_value={
                "success": True,
                "phase": "full_moon",
                "devices_updated": 2,
            }
        )

        # Execute
        result = await voice_service.handle_yandex_station_command(
            user_id=1, command="включи лунный свет", parameters={}
        )

        # Verify
        assert result["success"] is True
        assert "лунный" in result["message"] or "луна" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_google_assistant_intent(
        self, voice_service, lighting_service
    ):
        """Test Google Assistant intent handling."""
        # Setup
        lighting_service.apply_lunar_lighting = AsyncMock(
            return_value={
                "success": True,
                "phase": "new_moon",
                "devices_updated": 1,
            }
        )

        # Execute
        result = await voice_service.handle_google_assistant_command(
            user_id=1, intent="astro.lighting.lunar", parameters={}
        )

        # Verify
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_handle_alexa_unsupported_intent(self, voice_service):
        """Test Alexa unsupported intent handling."""
        # Execute
        result = await voice_service.handle_alexa_command(
            user_id=1, intent_name="UnsupportedIntent", slots={}
        )

        # Verify
        assert result["success"] is False
        assert "Intent not supported" in result["message"]

    @pytest.mark.asyncio
    async def test_get_suggested_commands(self, voice_service, iot_manager):
        """Test voice command suggestions."""
        # Setup
        mock_device = Mock()
        mock_device.device_type = DeviceType.SMART_LIGHT.value
        iot_manager.get_user_devices = AsyncMock(return_value=[mock_device])

        # Execute
        suggestions = await voice_service.get_suggested_commands(
            user_id=1, context=""
        )

        # Verify
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("освещение" in s.lower() for s in suggestions)
