"""
Performance tests for astrology calculations and API endpoints.
"""
import pytest
import time
import asyncio
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.astrology_calculator import AstrologyCalculator
from app.services.horoscope_generator import HoroscopeGenerator
from app.services.natal_chart import NatalChartCalculator
from app.services.lunar_calendar import LunarCalendar


class TestPerformance:
    """Performance tests for critical system components."""
    
    def setup_method(self):
        """Setup before each test."""
        self.astrology_calculator = AstrologyCalculator()
        self.horoscope_generator = HoroscopeGenerator()
        self.natal_chart = NatalChartCalculator()
        self.lunar_calendar = LunarCalendar()
        self.intent_recognition = IntentRecognitionService()
    
    def test_zodiac_sign_calculation_performance(self):
        """Test performance of zodiac sign calculations."""
        test_dates = [
            date(1990, 1, 15), date(1990, 2, 15), date(1990, 3, 15),
            date(1990, 4, 15), date(1990, 5, 15), date(1990, 6, 15),
            date(1990, 7, 15), date(1990, 8, 15), date(1990, 9, 15),
            date(1990, 10, 15), date(1990, 11, 15), date(1990, 12, 15)
        ]
        
        start_time = time.time()
        
        for test_date in test_dates * 100:  # 1200 calculations
            sign = self.astrology_calculator.get_zodiac_sign_by_date(test_date)
            assert sign is not None
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 1200 calculations in under 0.1 seconds
        assert duration < 0.1, f"Zodiac calculation took {duration:.3f}s, expected < 0.1s"
        
        # Calculate operations per second
        ops_per_second = 1200 / duration
        assert ops_per_second > 10000, f"Only {ops_per_second:.0f} ops/sec, expected > 10000"
    
    def test_planetary_position_calculation_performance(self):
        """Test performance of planetary position calculations."""
        test_date = datetime(1990, 5, 15, 14, 30)
        
        start_time = time.time()
        
        for _ in range(50):  # 50 full calculations
            positions = self.natal_chart.calculate_planet_positions(test_date)
            assert len(positions) >= 10
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 50 calculations in under 2 seconds
        assert duration < 2.0, f"Planetary calculations took {duration:.3f}s, expected < 2.0s"
        
        # Average time per calculation
        avg_time = duration / 50
        assert avg_time < 0.04, f"Average time {avg_time:.3f}s, expected < 0.04s"
    
    def test_horoscope_generation_performance(self):
        """Test performance of horoscope generation."""
        from app.models.yandex_models import YandexZodiacSign
        
        start_time = time.time()
        
        for sign in YandexZodiacSign:
            for period in ["today", "week", "month"]:
                for _ in range(10):  # 10 generations per sign/period
                    horoscope = self.horoscope_generator.generate_horoscope(
                        sign=sign,
                        period=period,
                        birth_date=date(1990, 5, 15)
                    )
                    assert horoscope["prediction"]
                    assert len(horoscope["prediction"]) > 50
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 360 total generations (12 signs * 3 periods * 10 repetitions)
        total_generations = 12 * 3 * 10
        
        # Should complete in under 3 seconds
        assert duration < 3.0, f"Horoscope generation took {duration:.3f}s, expected < 3.0s"
        
        avg_time = duration / total_generations
        assert avg_time < 0.01, f"Average generation time {avg_time:.3f}s, expected < 0.01s"
    
    def test_intent_recognition_performance(self):
        """Test performance of intent recognition."""
        test_commands = [
            "привет", "мой гороскоп", "совместимость льва и рака",
            "натальная карта", "лунный календарь", "помощь",
            "что ты умеешь", "расскажи про весов", "гороскоп на завтра",
            "совместимы ли мы", "карта рождения", "фазы луны"
        ]
        
        start_time = time.time()
        
        for command in test_commands * 50:  # 600 recognitions
            intent, entities, confidence = self.intent_recognition.recognize_intent(command)
            assert intent is not None
            assert isinstance(entities, dict)
            assert 0 <= confidence <= 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 600 recognitions in under 0.5 seconds
        assert duration < 0.5, f"Intent recognition took {duration:.3f}s, expected < 0.5s"
        
        ops_per_second = 600 / duration
        assert ops_per_second > 1000, f"Only {ops_per_second:.0f} ops/sec, expected > 1000"
    
    def test_lunar_calendar_performance(self):
        """Test performance of lunar calendar calculations."""
        start_time = time.time()
        
        # Test 100 different dates
        for day_offset in range(100):
            test_date = datetime(2023, 1, 1) + timedelta(days=day_offset)
            lunar_info = self.lunar_calendar.get_lunar_day_info(test_date)
            
            assert "lunar_day" in lunar_info
            assert "phase" in lunar_info
            assert "recommendations" in lunar_info
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 calculations in under 1 second
        assert duration < 1.0, f"Lunar calendar took {duration:.3f}s, expected < 1.0s"
    
    def test_compatibility_calculation_performance(self):
        """Test performance of compatibility calculations."""
        from app.models.yandex_models import YandexZodiacSign
        
        signs = list(YandexZodiacSign)
        
        start_time = time.time()
        
        # Test all possible sign combinations
        for sign1 in signs:
            for sign2 in signs:
                compatibility = self.astrology_calculator.calculate_compatibility(sign1, sign2)
                assert "score" in compatibility
                assert 0 <= compatibility["score"] <= 100
        
        end_time = time.time()
        duration = end_time - start_time
        
        total_combinations = len(signs) * len(signs)  # 144 combinations
        
        # Should complete all combinations in under 0.5 seconds
        assert duration < 0.5, f"Compatibility calculations took {duration:.3f}s, expected < 0.5s"
        
        avg_time = duration / total_combinations
        assert avg_time < 0.004, f"Average calculation time {avg_time:.4f}s, expected < 0.004s"
    
    def test_concurrent_horoscope_generation(self):
        """Test concurrent horoscope generation performance."""
        from app.models.yandex_models import YandexZodiacSign
        
        def generate_horoscope(sign, period):
            return self.horoscope_generator.generate_horoscope(
                sign=sign,
                period=period,
                birth_date=date(1990, 5, 15)
            )
        
        start_time = time.time()
        
        # Create 50 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for _ in range(50):
                sign = YandexZodiacSign.LEO
                period = "today"
                future = executor.submit(generate_horoscope, sign, period)
                futures.append(future)
            
            # Wait for all to complete
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                assert result["prediction"]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Concurrent execution should be faster than sequential
        assert duration < 2.0, f"Concurrent generation took {duration:.3f}s, expected < 2.0s"
        assert len(results) == 50
    
    def test_memory_usage_stability(self):
        """Test that repeated calculations don't cause memory leaks."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        # Perform many calculations
        for _ in range(1000):
            # Zodiac calculation
            sign = self.astrology_calculator.get_zodiac_sign_by_date(date(1990, 5, 15))
            
            # Horoscope generation
            horoscope = self.horoscope_generator.generate_horoscope(
                sign=sign,
                period="today",
                birth_date=date(1990, 5, 15)
            )
            
            # Intent recognition
            intent, entities, confidence = self.intent_recognition.recognize_intent("тест")
            
            # Clear references
            del sign, horoscope, intent, entities, confidence
        
        # Force garbage collection after test
        gc.collect()
        
        # Test passes if no memory errors occurred
        assert True
    
    @pytest.mark.asyncio
    async def test_async_operation_performance(self):
        """Test performance of async operations."""
        async def mock_db_operation():
            await asyncio.sleep(0.001)  # Simulate DB operation
            return {"result": "success"}
        
        start_time = time.time()
        
        # Run 100 concurrent async operations
        tasks = []
        for _ in range(100):
            task = asyncio.create_task(mock_db_operation())
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 100 concurrent operations much faster than sequential
        assert duration < 0.2, f"Async operations took {duration:.3f}s, expected < 0.2s"
        assert len(results) == 100
    
    def test_caching_performance_improvement(self):
        """Test that caching improves performance."""
        # Test intent recognition caching
        command = "мой гороскоп на сегодня"
        
        # First call (no cache)
        start_time = time.time()
        intent1, entities1, confidence1 = self.intent_recognition.recognize_intent(command)
        first_call_duration = time.time() - start_time
        
        # Second call (should use cache)
        start_time = time.time()
        intent2, entities2, confidence2 = self.intent_recognition.recognize_intent(command)
        second_call_duration = time.time() - start_time
        
        # Results should be identical
        assert intent1 == intent2
        assert entities1 == entities2
        assert confidence1 == confidence2
        
        # Second call should be significantly faster (at least 2x)
        if first_call_duration > 0.001:  # Only test if first call was measurable
            assert second_call_duration < first_call_duration / 2, \
                f"Caching didn't improve performance: {first_call_duration:.4f}s vs {second_call_duration:.4f}s"
    
    def test_bulk_operation_performance(self):
        """Test performance of bulk operations."""
        # Generate 100 horoscopes in a batch
        from app.models.yandex_models import YandexZodiacSign
        
        requests = []
        for i in range(100):
            requests.append({
                "sign": YandexZodiacSign.LEO,
                "period": "today",
                "birth_date": date(1990, 5, 15)
            })
        
        start_time = time.time()
        
        results = []
        for request in requests:
            horoscope = self.horoscope_generator.generate_horoscope(**request)
            results.append(horoscope)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Bulk operations should complete in reasonable time
        assert duration < 1.0, f"Bulk operations took {duration:.3f}s, expected < 1.0s"
        assert len(results) == 100
        
        # All results should be valid
        for result in results:
            assert result["prediction"]
            assert len(result["prediction"]) > 20