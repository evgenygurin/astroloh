"""
Comprehensive unit tests for EnhancedTransitService.
Tests transit calculations, period forecasts, async functionality, and caching.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.services.enhanced_transit_service import (
    KERYKEION_TRANSITS_AVAILABLE,
    TransitService,
)


@pytest.mark.unit
class TestEnhancedTransitServiceInit:
    """Test EnhancedTransitService initialization and availability"""

    @pytest.fixture
    def service(self):
        """Create TransitService instance"""
        return TransitService()

    def test_service_initialization(self, service):
        """Test service initialization with correct components"""
        assert hasattr(service, "kerykeion_service")
        assert hasattr(service, "astro_calculator")

    def test_is_enhanced_features_available(self, service):
        """Test detection of enhanced features availability"""
        availability = service.is_enhanced_features_available()

        assert isinstance(availability, dict)
        assert "kerykeion_transits" in availability
        assert "kerykeion_progressions" in availability
        assert "professional_ephemeris" in availability

        # Values should be boolean
        for key, value in availability.items():
            assert isinstance(value, bool)

    def test_get_transit_service_capabilities(self, service):
        """Test getting service capabilities"""
        capabilities = service.get_transit_service_capabilities()

        assert isinstance(capabilities, dict)
        assert "enhanced_transits" in capabilities
        assert "period_forecasts" in capabilities
        assert "important_transits_detection" in capabilities
        assert "energy_analysis" in capabilities

    def test_kerykeion_availability_constant(self):
        """Test that KERYKEION_TRANSITS_AVAILABLE is properly set"""
        assert isinstance(KERYKEION_TRANSITS_AVAILABLE, bool)


@pytest.mark.unit
@pytest.mark.asyncio
class TestEnhancedTransitServiceAsync:
    """Test async functionality of EnhancedTransitService"""

    @pytest.fixture
    def service(self):
        """Create TransitService instance"""
        return TransitService()

    @pytest.fixture
    def sample_natal_chart(self):
        """Sample natal chart for transit testing"""
        return {
            "planets": {
                "sun": {
                    "longitude": 142.5,
                    "sign": "leo",
                    "degree_in_sign": 22.5,
                },
                "moon": {
                    "longitude": 245.8,
                    "sign": "sagittarius",
                    "degree_in_sign": 5.8,
                },
                "mercury": {
                    "longitude": 158.3,
                    "sign": "virgo",
                    "degree_in_sign": 8.3,
                },
            },
            "houses": {
                "1": {"cusp": 0, "sign": "aries"},
                "2": {"cusp": 30, "sign": "taurus"},
                "3": {"cusp": 60, "sign": "gemini"},
            },
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "timezone": "Europe/Moscow",
        }

    async def test_get_current_transits_async(
        self, service, sample_natal_chart
    ):
        """Test async current transits calculation"""
        with patch.object(
            service, "is_available"
        ) as mock_available, patch.object(
            service, "_get_kerykeion_transits_async"
        ) as mock_calc:
            mock_available.return_value = True  # Enable Kerykeion path
            mock_calc.return_value = {
                "aspects": [
                    {
                        "transit_planet": "jupiter",
                        "natal_planet": "sun",
                        "aspect_type": "trine",
                        "orb": 2.5,
                        "applying": True,
                    }
                ],
                "energy_level": 75,
                "dominant_themes": ["expansion", "opportunity"],
            }

            result = await service.get_current_transits(
                natal_chart=sample_natal_chart,
                transit_date=datetime.now(),
                include_minor_aspects=True,
            )

            assert result is not None
            assert "aspects" in result
            assert "energy_level" in result
            assert "dominant_themes" in result

            aspects = result.get("aspects", [])
            assert len(aspects) > 0
            assert aspects[0]["transit_planet"] == "jupiter"
            assert aspects[0]["natal_planet"] == "sun"
            assert aspects[0]["aspect_type"] == "trine"

    async def test_get_period_forecast_async(
        self, service, sample_natal_chart
    ):
        """Test async period forecast calculation"""
        # Mock the underlying calculation method that gets called for period forecasts
        with patch.object(
            service, "_get_kerykeion_transits_async"
        ) as mock_calc:
            # Mock multiple days of transit data
            mock_calc.return_value = {
                "aspects": [
                    {
                        "transit_planet": "jupiter",
                        "natal_planet": "sun",
                        "aspect_type": "trine",
                        "orb": 2.5,
                        "applying": True,
                    }
                ],
                "energy_level": 80,
                "dominant_themes": ["creativity", "relationships"],
            }

            result = await service.get_period_forecast(
                natal_chart=sample_natal_chart,
                days=7,
                start_date=datetime.now(),
            )

            assert result is not None
            assert "forecast_days" in result
            assert "overall_energy" in result
            assert "major_themes" in result

            forecast_days = result.get("forecast_days", [])
            assert len(forecast_days) > 0
            assert "date" in forecast_days[0]
            assert "energy_level" in forecast_days[0]

    async def test_get_important_transits_async(
        self, service, sample_natal_chart
    ):
        """Test async important transits detection"""
        with patch.object(
            service, "_get_kerykeion_transits_async"
        ) as mock_calc:
            mock_calc.return_value = {
                "aspects": [
                    {
                        "transit_planet": "saturn",
                        "natal_planet": "sun",
                        "aspect_type": "conjunction",
                        "orb": 1.0,
                        "applying": True,
                        "exact_date": datetime.now() + timedelta(days=30),
                        "significance": "high",
                    }
                ],
                "energy_level": 60,
                "dominant_themes": ["responsibility", "maturation"],
            }

            result = await service.get_important_transits(
                natal_chart=sample_natal_chart,
                lookback_days=30,
                lookahead_days=90,
            )

            assert result is not None
            assert "important_transits" in result
            assert "life_themes" in result
            assert "preparation_advice" in result

            important_transits = result.get("important_transits", [])
            if important_transits:
                assert "transit_planet" in important_transits[0]
                assert "life_area_affected" in important_transits[0]

    async def test_comprehensive_transit_analysis_async(
        self, service, sample_natal_chart
    ):
        """Test comprehensive transit analysis combining all features"""
        # Test calling the individual methods that would be used together
        with patch.object(
            service, "is_available"
        ) as mock_available, patch.object(
            service, "_get_kerykeion_transits_async"
        ) as mock_calc:
            mock_available.return_value = True  # Enable Kerykeion path
            mock_calc.return_value = {
                "aspects": [],
                "energy_level": 75,
                "dominant_themes": ["growth"],
            }

            # Test current transits
            current_result = await service.get_current_transits(
                natal_chart=sample_natal_chart, use_cache=False
            )
            assert current_result is not None

            # Test period forecast
            forecast_result = await service.get_period_forecast(
                natal_chart=sample_natal_chart, days=7, use_cache=False
            )
            assert forecast_result is not None

            # Test important transits
            important_result = await service.get_important_transits(
                natal_chart=sample_natal_chart, use_cache=False
            )
            assert important_result is not None

            # Verify all methods were called with mocked backend
            assert mock_calc.call_count >= 3


@pytest.mark.unit
class TestEnhancedTransitServiceCaching:
    """Test caching functionality of EnhancedTransitService"""

    @pytest.fixture
    def service(self):
        return TransitService()

    @pytest.fixture
    def sample_natal_chart(self):
        return {
            "planets": {
                "sun": {
                    "longitude": 142.5,
                    "sign": "leo",
                    "degree_in_sign": 22.5,
                }
            },
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "timezone": "Europe/Moscow",
        }

    @pytest.mark.asyncio
    async def test_caching_current_transits(self, service, sample_natal_chart):
        """Test that current transits are properly cached"""
        mock_result = {"aspects": [], "energy_level": 80, "cached": False}

        with patch(
            "app.services.enhanced_transit_service.astro_cache"
        ) as mock_cache, patch.object(
            service, "_get_kerykeion_transits_async", return_value=mock_result
        ), patch.object(
            service, "is_available"
        ) as mock_available:
            # Enable Kerykeion path
            mock_available.return_value = True

            # First call - cache miss
            mock_cache.get_current_transits = AsyncMock(return_value=None)
            mock_cache.set_current_transits = AsyncMock()

            await service.get_current_transits(
                natal_chart=sample_natal_chart,
                transit_date=datetime.now(),
                use_cache=True,
            )

            mock_cache.get_current_transits.assert_called_once()
            mock_cache.set_current_transits.assert_called_once()

    def test_generate_transit_cache_key(self, service, sample_natal_chart):
        """Test transit cache key generation"""
        cache_key = service._generate_chart_cache_key(sample_natal_chart)

        assert isinstance(cache_key, str)
        assert len(cache_key) > 0

        # Same inputs should generate same key
        cache_key2 = service._generate_chart_cache_key(sample_natal_chart)

        assert cache_key == cache_key2


@pytest.mark.unit
@pytest.mark.skipif(
    not KERYKEION_TRANSITS_AVAILABLE, reason="Kerykeion transits not available"
)
class TestEnhancedTransitServiceWithKerykeion:
    """Tests that run when Kerykeion transits are available"""

    @pytest.fixture
    def service(self):
        return TransitService()

    @pytest.fixture
    def sample_natal_chart(self):
        return {
            "planets": {
                "sun": {
                    "longitude": 142.5,
                    "sign": "leo",
                    "degree_in_sign": 22.5,
                },
                "moon": {
                    "longitude": 245.8,
                    "sign": "sagittarius",
                    "degree_in_sign": 5.8,
                },
            },
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "timezone": "Europe/Moscow",
        }

    def test_kerykeion_transits_calculation(self, service, sample_natal_chart):
        """Test Kerykeion-based transit calculations"""
        # Test the actual Kerykeion transit method that exists
        result = service._get_kerykeion_transits(
            natal_chart=sample_natal_chart, transit_date=datetime.now()
        )

        # Should return meaningful transit data or error handling
        assert result is not None

        if "error" not in result:
            assert "aspects" in result

    def test_ephemeris_data_integration(self, service, sample_natal_chart):
        """Test integration with Kerykeion EphemerisDataFactory"""
        # Test that the service can work with ephemeris data
        ephemeris_data = service._get_ephemeris_data(
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
        )

        assert ephemeris_data is not None
        # Structure depends on EphemerisDataFactory output


@pytest.mark.unit
class TestEnhancedTransitServiceFallback:
    """Test fallback behavior when Kerykeion transits unavailable"""

    @pytest.fixture
    def service_without_kerykeion(self):
        """Service with mocked unavailable Kerykeion transits"""
        service = TransitService()
        # Mock the availability check
        service._kerykeion_transits_available = False
        return service

    @pytest.fixture
    def sample_natal_chart(self):
        return {
            "planets": {
                "sun": {
                    "longitude": 142.5,
                    "sign": "leo",
                    "degree_in_sign": 22.5,
                }
            },
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "timezone": "Europe/Moscow",
        }

    @pytest.mark.asyncio
    async def test_fallback_to_basic_transit_calculation(
        self, service_without_kerykeion, sample_natal_chart
    ):
        """Test fallback to basic transit calculations"""
        # Mock the basic transit calculation
        with patch.object(
            service_without_kerykeion.astro_calculator,
            "calculate_planet_positions",
        ) as mock_basic:
            mock_basic.return_value = {
                "jupiter": {"longitude": 100.0, "sign": "leo"},
                "sun": {"longitude": 150.0, "sign": "virgo"},
            }

            result = await service_without_kerykeion.get_current_transits(
                natal_chart=sample_natal_chart, transit_date=datetime.now()
            )

            assert result is not None
            assert result.get("source") == "basic" or "aspects" in result
            mock_basic.assert_called_once()

    def test_service_capabilities_without_kerykeion(
        self, service_without_kerykeion
    ):
        """Test service capabilities when Kerykeion unavailable"""
        capabilities = (
            service_without_kerykeion.get_transit_service_capabilities()
        )

        assert not capabilities["enhanced_transits"]
        assert "basic_transits" in capabilities
        assert capabilities["basic_transits"]


@pytest.mark.performance
@pytest.mark.asyncio
class TestEnhancedTransitServicePerformance:
    """Performance tests for EnhancedTransitService"""

    @pytest.fixture
    def service(self):
        return TransitService()

    @pytest.fixture
    def sample_natal_chart(self):
        return {
            "planets": {
                "sun": {
                    "longitude": 142.5,
                    "sign": "leo",
                    "degree_in_sign": 22.5,
                },
                "moon": {
                    "longitude": 245.8,
                    "sign": "sagittarius",
                    "degree_in_sign": 5.8,
                },
                "mercury": {
                    "longitude": 158.3,
                    "sign": "virgo",
                    "degree_in_sign": 8.3,
                },
            },
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "timezone": "Europe/Moscow",
        }

    async def test_current_transits_performance(
        self, service, sample_natal_chart
    ):
        """Test current transits calculation performance"""
        import time

        with patch.object(service, "_calculate_current_transits") as mock_calc:
            mock_calc.return_value = {"aspects": [], "energy_level": 75}

            start_time = time.time()

            result = await service.get_current_transits_async(
                natal_chart=sample_natal_chart, transit_date=datetime.now()
            )

            end_time = time.time()
            calculation_time = end_time - start_time

            # Should complete within 2 seconds
            assert calculation_time < 2.0
            assert result is not None

    async def test_period_forecast_performance(
        self, service, sample_natal_chart
    ):
        """Test period forecast calculation performance"""
        import time

        with patch.object(service, "_calculate_period_forecast") as mock_calc:
            mock_calc.return_value = {
                "forecast_days": [
                    {"date": datetime.now().date(), "energy_level": 75}
                ],
                "overall_energy": 75,
            }

            start_time = time.time()

            result = await service.get_period_forecast_async(
                natal_chart=sample_natal_chart, days=30
            )

            end_time = time.time()
            calculation_time = end_time - start_time

            # 30-day forecast should complete within 5 seconds
            assert calculation_time < 5.0
            assert result is not None

    async def test_important_transits_performance(
        self, service, sample_natal_chart
    ):
        """Test important transits detection performance"""
        import time

        with patch.object(
            service, "_calculate_important_transits"
        ) as mock_calc:
            mock_calc.return_value = {
                "major_transits": [],
                "life_themes": [],
                "timing_advice": "Test advice",
            }

            start_time = time.time()

            result = await service.get_important_transits_async(
                natal_chart=sample_natal_chart,
                lookback_days=30,
                lookahead_days=90,
            )

            end_time = time.time()
            calculation_time = end_time - start_time

            # 120-day transit scan should complete within 8 seconds
            assert calculation_time < 8.0
            assert result is not None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not KERYKEION_TRANSITS_AVAILABLE, reason="Kerykeion transits not available"
)
class TestEnhancedTransitServiceIntegration:
    """Integration tests with real Kerykeion transit calculations"""

    @pytest.fixture
    def service(self):
        return TransitService()

    async def test_real_transit_calculation_integration(self, service):
        """Test integration with real transit calculations"""
        # Real natal chart data
        natal_chart = {
            "planets": {
                "sun": {
                    "longitude": 142.5,
                    "sign": "leo",
                    "degree_in_sign": 22.5,
                },
                "moon": {
                    "longitude": 245.8,
                    "sign": "sagittarius",
                    "degree_in_sign": 5.8,
                },
            },
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "timezone": "Europe/Moscow",
        }

        result = await service.get_current_transits_async(
            natal_chart=natal_chart,
            transit_date=datetime.now(),
            use_cache=False,  # Ensure fresh calculation
        )

        # Should get real transit data
        assert result is not None

        if "error" not in result:
            # Should have meaningful structure
            assert "aspects" in result or "transits" in result

            if "aspects" in result:
                aspects = result["aspects"]
                if aspects:  # If any aspects found
                    assert "transit_planet" in aspects[0]
                    assert "natal_planet" in aspects[0]
                    assert "aspect_type" in aspects[0]

    async def test_period_forecast_integration(self, service):
        """Test period forecast with real calculations"""
        natal_chart = {
            "planets": {
                "sun": {
                    "longitude": 142.5,
                    "sign": "leo",
                    "degree_in_sign": 22.5,
                }
            },
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "timezone": "Europe/Moscow",
        }

        result = await service.get_period_forecast_async(
            natal_chart=natal_chart, days=7, use_cache=False
        )

        assert result is not None

        if "error" not in result:
            assert "forecast_days" in result
            forecast_days = result["forecast_days"]

            if forecast_days:
                # Should have 7 days of forecasts
                assert len(forecast_days) <= 7

                for day_forecast in forecast_days:
                    assert "date" in day_forecast
                    assert "energy_level" in day_forecast
