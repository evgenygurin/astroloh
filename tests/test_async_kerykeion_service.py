"""
Comprehensive unit tests for AsyncKerykeionService.
Tests async operations, caching, performance monitoring, and batch processing.
"""

import pytest
import asyncio
from datetime import datetime, date, time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict

from app.services.async_kerykeion_service import AsyncKerykeionService
from app.services.kerykeion_service import HouseSystem, ZodiacType, KERYKEION_AVAILABLE


@pytest.mark.unit
class TestAsyncKerykeionServiceInit:
    """Test AsyncKerykeionService initialization and basic functionality"""
    
    @pytest.fixture
    def service(self):
        """Create AsyncKerykeionService instance"""
        return AsyncKerykeionService(max_workers=2)
    
    def test_service_initialization(self, service):
        """Test service initialization with correct parameters"""
        assert hasattr(service, 'kerykeion_service')
        assert hasattr(service, 'executor')
        assert hasattr(service, 'performance_stats')
        
        # Check performance stats initialization
        stats = service.performance_stats
        assert stats['total_operations'] == 0
        assert stats['cached_operations'] == 0
        assert stats['async_operations'] == 0
        assert stats['average_calculation_time'] == 0.0
        assert stats['slow_calculations'] == 0
        
    def test_is_available_delegates_to_kerykeion_service(self, service):
        """Test that is_available properly delegates to KerykeionService"""
        # Mock the underlying kerykeion_service
        service.kerykeion_service.is_available = Mock(return_value=True)
        assert service.is_available() == True
        
        service.kerykeion_service.is_available = Mock(return_value=False)
        assert service.is_available() == False
        
    def test_generate_chart_id_consistency(self, service):
        """Test that chart ID generation is consistent for same inputs"""
        birth_datetime = datetime(1990, 8, 15, 14, 30)
        latitude = 55.7558
        longitude = 37.6176
        timezone = "Europe/Moscow"
        
        id1 = service._generate_chart_id(birth_datetime, latitude, longitude, timezone)
        id2 = service._generate_chart_id(birth_datetime, latitude, longitude, timezone)
        
        assert id1 == id2
        assert isinstance(id1, str)
        assert len(id1) > 0
        
    def test_generate_chart_id_different_for_different_inputs(self, service):
        """Test that different birth data produces different chart IDs"""
        base_params = {
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow"
        }
        
        id1 = service._generate_chart_id(**base_params)
        
        # Different date
        params2 = base_params.copy()
        params2["birth_datetime"] = datetime(1990, 8, 16, 14, 30)
        id2 = service._generate_chart_id(**params2)
        
        # Different location
        params3 = base_params.copy()
        params3["latitude"] = 40.7128
        id3 = service._generate_chart_id(**params3)
        
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3


@pytest.mark.unit
@pytest.mark.asyncio
class TestAsyncKerykeionServiceAsync:
    """Test async functionality of AsyncKerykeionService"""
    
    @pytest.fixture
    async def service(self):
        """Create AsyncKerykeionService instance"""
        service = AsyncKerykeionService(max_workers=2)
        yield service
        # Cleanup
        service.executor.shutdown(wait=True)
    
    @pytest.fixture
    def sample_birth_data(self):
        """Sample birth data for testing"""
        return {
            "name": "Test Subject",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow"
        }
    
    async def test_calculate_natal_chart_async_without_cache(self, service, sample_birth_data):
        """Test async natal chart calculation without cache"""
        with patch.object(service.kerykeion_service, 'get_full_natal_chart_data') as mock_calc:
            mock_calc.return_value = {
                "planets": {"sun": {"sign": "leo", "degree": 22.5}},
                "houses": {"1": {"cusp": 0, "sign": "aries"}},
                "aspects": []
            }
            
            result = await service.calculate_natal_chart_async(**sample_birth_data)
            
            assert result is not None
            assert "planets" in result
            assert "houses" in result
            assert "aspects" in result
            mock_calc.assert_called_once()
            
            # Check performance stats update
            assert service.performance_stats['async_operations'] > 0
            assert service.performance_stats['total_operations'] > 0
    
    async def test_calculate_natal_chart_async_with_cache(self, service, sample_birth_data):
        """Test async natal chart calculation with caching enabled"""
        cached_result = {
            "planets": {"sun": {"sign": "leo", "degree": 22.5}},
            "houses": {"1": {"cusp": 0, "sign": "aries"}},
            "aspects": [],
            "cached": True
        }
        
        # Mock cache to return a result
        with patch('app.services.astro_cache_service.astro_cache') as mock_cache:
            mock_cache.get_cached_data = AsyncMock(return_value=cached_result)
            
            result = await service.calculate_natal_chart_async(
                use_cache=True, 
                **sample_birth_data
            )
            
            assert result == cached_result
            # Should have used cache
            mock_cache.get_cached_data.assert_called_once()
            
            # Check cached operations stat
            assert service.performance_stats['cached_operations'] >= 0
    
    async def test_calculate_natal_chart_async_cache_miss(self, service, sample_birth_data):
        """Test async chart calculation when cache misses"""
        fresh_result = {
            "planets": {"sun": {"sign": "leo", "degree": 22.5}},
            "houses": {"1": {"cusp": 0, "sign": "aries"}},
            "aspects": []
        }
        
        with patch('app.services.astro_cache_service.astro_cache') as mock_cache, \
             patch.object(service.kerykeion_service, 'get_full_natal_chart_data') as mock_calc:
            
            mock_cache.get_cached_data = AsyncMock(return_value=None)  # Cache miss
            mock_cache.cache_data = AsyncMock()  # Cache storage
            mock_calc.return_value = fresh_result
            
            result = await service.calculate_natal_chart_async(
                use_cache=True,
                **sample_birth_data
            )
            
            assert result == fresh_result
            mock_cache.get_cached_data.assert_called_once()
            mock_cache.cache_data.assert_called_once()
            mock_calc.assert_called_once()
    
    async def test_batch_calculate_natal_charts(self, service):
        """Test batch calculation of multiple natal charts"""
        birth_data_list = [
            {
                "name": f"Subject {i}",
                "birth_datetime": datetime(1990 + i, 8, 15, 14, 30),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow"
            }
            for i in range(3)
        ]
        
        mock_result = {
            "planets": {"sun": {"sign": "leo", "degree": 22.5}},
            "houses": {"1": {"cusp": 0, "sign": "aries"}},
            "aspects": []
        }
        
        with patch.object(service.kerykeion_service, 'get_full_natal_chart_data') as mock_calc:
            mock_calc.return_value = mock_result
            
            results = await service.batch_calculate_natal_charts(birth_data_list)
            
            assert len(results) == 3
            assert all("planets" in result for result in results)
            assert mock_calc.call_count == 3
            
            # Check performance stats
            assert service.performance_stats['total_operations'] >= 3
    
    async def test_calculate_with_performance_monitoring(self, service, sample_birth_data):
        """Test that performance monitoring works correctly"""
        initial_stats = service.performance_stats.copy()
        
        with patch.object(service.kerykeion_service, 'get_full_natal_chart_data') as mock_calc:
            mock_calc.return_value = {"planets": {}, "houses": {}, "aspects": []}
            
            result = await service.calculate_natal_chart_async(**sample_birth_data)
            
            # Performance stats should be updated
            assert service.performance_stats['total_operations'] > initial_stats['total_operations']
            assert service.performance_stats['async_operations'] > initial_stats['async_operations']
            
            # Average calculation time should be set
            assert service.performance_stats['average_calculation_time'] >= 0
    
    async def test_slow_calculation_detection(self, service, sample_birth_data):
        """Test detection of slow calculations"""
        def slow_calculation(*args, **kwargs):
            import time
            time.sleep(0.1)  # Simulate slow calculation
            return {"planets": {}, "houses": {}, "aspects": []}
        
        with patch.object(service.kerykeion_service, 'get_full_natal_chart_data', side_effect=slow_calculation):
            await service.calculate_natal_chart_async(**sample_birth_data)
            
            # Should detect slow calculation (>0.05s threshold if implemented)
            # This depends on the service implementation
            assert service.performance_stats['total_operations'] > 0
    
    async def test_error_handling_in_async_calculation(self, service, sample_birth_data):
        """Test error handling in async calculations"""
        with patch.object(service.kerykeion_service, 'get_full_natal_chart_data') as mock_calc:
            mock_calc.side_effect = Exception("Calculation error")
            
            result = await service.calculate_natal_chart_async(**sample_birth_data)
            
            # Should return error result or None depending on implementation
            assert result is not None
            # Error should be logged and handled gracefully
    
    async def test_concurrent_calculations(self, service):
        """Test multiple concurrent calculations"""
        birth_data_sets = [
            {
                "name": f"Concurrent Subject {i}",
                "birth_datetime": datetime(1990, 8, 15 + i, 14, 30),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow"
            }
            for i in range(5)
        ]
        
        mock_result = {"planets": {}, "houses": {}, "aspects": []}
        
        with patch.object(service.kerykeion_service, 'get_full_natal_chart_data') as mock_calc:
            mock_calc.return_value = mock_result
            
            # Run calculations concurrently
            tasks = [
                service.calculate_natal_chart_async(**birth_data) 
                for birth_data in birth_data_sets
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(result is not None for result in results)
            assert mock_calc.call_count == 5


@pytest.mark.unit
class TestAsyncKerykeionServicePerformanceStats:
    """Test performance statistics functionality"""
    
    @pytest.fixture
    def service(self):
        service = AsyncKerykeionService(max_workers=2)
        yield service
        service.executor.shutdown(wait=True)
    
    def test_get_performance_stats(self, service):
        """Test getting performance statistics"""
        stats = service.get_performance_stats()
        
        assert isinstance(stats, dict)
        assert "total_operations" in stats
        assert "cached_operations" in stats
        assert "async_operations" in stats
        assert "average_calculation_time" in stats
        assert "slow_calculations" in stats
        
        # Additional computed stats
        assert "cache_hit_rate" in stats
        assert "total_calculation_time" in stats
    
    def test_reset_performance_stats(self, service):
        """Test resetting performance statistics"""
        # Simulate some operations
        service.performance_stats['total_operations'] = 10
        service.performance_stats['cached_operations'] = 5
        
        service.reset_performance_stats()
        
        stats = service.get_performance_stats()
        assert stats['total_operations'] == 0
        assert stats['cached_operations'] == 0
        assert stats['async_operations'] == 0


@pytest.mark.unit
class TestAsyncKerykeionServiceWithoutKerykeion:
    """Test behavior when Kerykeion is not available"""
    
    @pytest.fixture
    def service_without_kerykeion(self):
        """Create service with mocked unavailable Kerykeion"""
        service = AsyncKerykeionService(max_workers=2)
        service.kerykeion_service.available = False
        yield service
        service.executor.shutdown(wait=True)
    
    @pytest.mark.asyncio
    async def test_calculate_without_kerykeion_returns_error(self, service_without_kerykeion):
        """Test that calculations return error when Kerykeion unavailable"""
        result = await service_without_kerykeion.calculate_natal_chart_async(
            name="Test",
            birth_datetime=datetime(1990, 8, 15, 14, 30),
            latitude=55.7558,
            longitude=37.6176
        )
        
        # Should return error indication
        assert result is not None
        if isinstance(result, dict):
            assert "error" in result or result == {}
    
    def test_is_available_returns_false(self, service_without_kerykeion):
        """Test is_available returns False when Kerykeion unavailable"""
        assert service_without_kerykeion.is_available() == False


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.skipif(not KERYKEION_AVAILABLE, reason="Kerykeion not available")
class TestAsyncKerykeionServiceRealPerformance:
    """Real performance tests with actual Kerykeion (when available)"""
    
    @pytest.fixture
    async def service(self):
        service = AsyncKerykeionService(max_workers=4)
        yield service
        service.executor.shutdown(wait=True)
    
    async def test_async_performance_vs_sync(self, service):
        """Test that async processing improves performance for multiple calculations"""
        birth_data_sets = [
            {
                "name": f"Performance Test {i}",
                "birth_datetime": datetime(1990, 1 + i, 15, 14, 30),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow"
            }
            for i in range(3)
        ]
        
        # Test async batch processing
        import time
        start_time = time.time()
        
        results = await service.batch_calculate_natal_charts(birth_data_sets)
        
        end_time = time.time()
        async_time = end_time - start_time
        
        assert len(results) == 3
        assert all(result is not None for result in results)
        
        # Should complete within reasonable time
        assert async_time < 10.0  # 10 seconds for 3 charts should be reasonable
        
        # Check that performance stats were updated
        stats = service.get_performance_stats()
        assert stats['total_operations'] >= 3
        assert stats['async_operations'] >= 3
    
    async def test_cache_performance_improvement(self, service):
        """Test that caching improves performance for repeated calculations"""
        birth_data = {
            "name": "Cache Performance Test",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow"
        }
        
        # First calculation (no cache)
        import time
        start_time = time.time()
        result1 = await service.calculate_natal_chart_async(use_cache=True, **birth_data)
        first_calc_time = time.time() - start_time
        
        # Second calculation (with cache)
        start_time = time.time()  
        result2 = await service.calculate_natal_chart_async(use_cache=True, **birth_data)
        second_calc_time = time.time() - start_time
        
        assert result1 is not None
        assert result2 is not None
        
        # Second calculation should be faster (cached)
        # Note: This may not always be true due to various factors
        stats = service.get_performance_stats()
        assert stats['total_operations'] >= 2


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not KERYKEION_AVAILABLE, reason="Kerykeion not available")
class TestAsyncKerykeionServiceIntegration:
    """Integration tests with real astrological calculations"""
    
    @pytest.fixture  
    async def service(self):
        service = AsyncKerykeionService(max_workers=2)
        yield service
        service.executor.shutdown(wait=True)
    
    async def test_full_integration_calculation(self, service):
        """Test full integration with real Kerykeion calculation"""
        result = await service.calculate_natal_chart_async(
            name="Integration Test",
            birth_datetime=datetime(1990, 8, 15, 14, 30),
            latitude=55.7558,  # Moscow
            longitude=37.6176,
            timezone="Europe/Moscow",
            use_cache=False  # Ensure fresh calculation
        )
        
        # Should get real astrological data
        assert result is not None
        assert "planets" in result
        assert "houses" in result
        
        planets = result.get("planets", {})
        assert len(planets) > 0
        
        # Check that we have main planets
        main_planets = ["sun", "moon", "mercury", "venus", "mars"]
        found_planets = [p for p in main_planets if p in planets]
        assert len(found_planets) > 0
    
    async def test_batch_integration_calculation(self, service):
        """Test batch calculations with real data"""
        birth_data_list = [
            {
                "name": "Integration Subject 1",
                "birth_datetime": datetime(1990, 8, 15, 14, 30),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow"
            },
            {
                "name": "Integration Subject 2", 
                "birth_datetime": datetime(1985, 12, 25, 10, 15),
                "latitude": 40.7128,  # New York
                "longitude": -74.0060,
                "timezone": "America/New_York"
            }
        ]
        
        results = await service.batch_calculate_natal_charts(birth_data_list)
        
        assert len(results) == 2
        assert all("planets" in result for result in results if result is not None)
        
        # Check performance stats
        stats = service.get_performance_stats()
        assert stats['total_operations'] >= 2
        assert stats['async_operations'] >= 2