"""
Comprehensive performance and load tests for Kerykeion integration.
Tests system performance under various load conditions and validates optimization systems.
"""

import asyncio
import statistics
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from app.services.astro_cache_service import astro_cache
from app.services.async_kerykeion_service import AsyncKerykeionService
from app.services.enhanced_transit_service import TransitService
from app.services.kerykeion_service import KERYKEION_AVAILABLE, KerykeionService


@pytest.mark.performance
class TestKerykeionServicePerformance:
    """Test KerykeionService performance characteristics"""

    @pytest.fixture
    def service(self):
        return KerykeionService()

    @pytest.fixture
    def sample_birth_data_sets(self):
        """Generate diverse birth data for performance testing"""
        return [
            {
                "name": f"Test Subject {i}",
                "birth_datetime": datetime(
                    1990 + i % 30, 1 + i % 12, 1 + i % 28, 12 + i % 12, i % 60
                ),
                "latitude": 55.7558 + (i % 20 - 10) * 0.1,
                "longitude": 37.6176 + (i % 20 - 10) * 0.1,
                "timezone": "Europe/Moscow",
            }
            for i in range(100)
        ]

    @pytest.mark.skipif(
        not KERYKEION_AVAILABLE, reason="Kerykeion not available"
    )
    def test_single_chart_calculation_performance(self, service):
        """Test performance of single chart calculations"""
        birth_data = {
            "name": "Performance Test",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow",
        }

        # Measure multiple calculations for statistical reliability
        calculation_times = []

        for _ in range(10):
            start_time = time.perf_counter()

            chart_data = service.get_full_natal_chart_data(**birth_data)

            end_time = time.perf_counter()
            calculation_time = end_time - start_time

            if "error" not in chart_data:
                calculation_times.append(calculation_time)

        if calculation_times:
            avg_time = statistics.mean(calculation_times)
            median_time = statistics.median(calculation_times)
            max_time = max(calculation_times)

            # Performance assertions
            assert (
                avg_time < 3.0
            ), f"Average calculation time too slow: {avg_time:.2f}s"
            assert (
                median_time < 2.5
            ), f"Median calculation time too slow: {median_time:.2f}s"
            assert (
                max_time < 5.0
            ), f"Worst calculation time too slow: {max_time:.2f}s"

            print(
                f"Single chart performance: avg={avg_time:.2f}s, median={median_time:.2f}s, max={max_time:.2f}s"
            )

    @pytest.mark.skipif(
        not KERYKEION_AVAILABLE, reason="Kerykeion not available"
    )
    def test_batch_calculation_performance(
        self, service, sample_birth_data_sets
    ):
        """Test performance of batch chart calculations"""
        batch_size = 10
        test_data = sample_birth_data_sets[:batch_size]

        start_time = time.perf_counter()

        results = []
        for birth_data in test_data:
            try:
                chart_data = service.get_full_natal_chart_data(**birth_data)
                if "error" not in chart_data:
                    results.append(chart_data)
            except Exception as e:
                print(f"Chart calculation failed: {e}")

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Performance metrics
        successful_calculations = len(results)
        avg_time_per_chart = total_time / max(successful_calculations, 1)

        # Assertions
        assert (
            successful_calculations >= batch_size * 0.8
        ), "Too many failed calculations"
        assert (
            avg_time_per_chart < 4.0
        ), f"Batch calculation too slow: {avg_time_per_chart:.2f}s per chart"
        assert (
            total_time < 30.0
        ), f"Total batch time too slow: {total_time:.2f}s"

        print(
            f"Batch performance: {successful_calculations}/{batch_size} successful, {avg_time_per_chart:.2f}s per chart"
        )

    def test_memory_usage_stability(self, service):
        """Test memory usage remains stable during calculations"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform multiple calculations
        for i in range(20):
            birth_data = {
                "name": f"Memory Test {i}",
                "birth_datetime": datetime(
                    1990, 1 + i % 12, 1 + i % 28, 12, 0
                ),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow",
            }

            try:
                chart_data = service.get_full_natal_chart_data(**birth_data)
                # Force some processing
                if "planets" in chart_data:
                    chart_data["planets"]
            except Exception:
                continue

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory should not increase excessively
        assert (
            memory_increase < 50
        ), f"Memory leak detected: {memory_increase:.2f}MB increase"

        print(
            f"Memory stability: {memory_increase:.2f}MB increase after 20 calculations"
        )


@pytest.mark.performance
@pytest.mark.asyncio
class TestAsyncKerykeionServicePerformance:
    """Test async service performance and concurrency"""

    @pytest.fixture
    async def service(self):
        service = AsyncKerykeionService(max_workers=4)
        yield service
        service.executor.shutdown(wait=True)

    async def test_async_calculation_performance(self, service):
        """Test async calculation performance"""
        birth_data = {
            "name": "Async Performance Test",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow",
        }

        # Test with mocked underlying service for consistent results
        with patch.object(
            service.kerykeion_service, "get_full_natal_chart_data"
        ) as mock_calc:
            mock_calc.return_value = {
                "planets": {"sun": {"sign": "leo", "degree": 22.5}},
                "houses": {"1": {"cusp": 0, "sign": "aries"}},
                "aspects": [],
            }

            # Measure async performance
            calculation_times = []

            for _ in range(5):
                start_time = time.perf_counter()

                result = await service.calculate_natal_chart_async(
                    **birth_data
                )

                end_time = time.perf_counter()
                calculation_time = end_time - start_time

                if result:
                    calculation_times.append(calculation_time)

            if calculation_times:
                avg_time = statistics.mean(calculation_times)

                # Async should add minimal overhead
                assert (
                    avg_time < 1.0
                ), f"Async overhead too high: {avg_time:.3f}s"

                print(
                    f"Async calculation performance: {avg_time:.3f}s average"
                )

    async def test_concurrent_calculation_performance(self, service):
        """Test performance under concurrent load"""
        birth_data_sets = [
            {
                "name": f"Concurrent Test {i}",
                "birth_datetime": datetime(
                    1990 + i, 1 + i % 12, 1 + i % 28, 12, 0
                ),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow",
            }
            for i in range(10)
        ]

        with patch.object(
            service.kerykeion_service, "get_full_natal_chart_data"
        ) as mock_calc:
            mock_calc.return_value = {
                "planets": {"sun": {"sign": "leo"}},
                "houses": {"1": {"cusp": 0}},
                "aspects": [],
            }

            start_time = time.perf_counter()

            # Run concurrent calculations
            tasks = [
                service.calculate_natal_chart_async(**birth_data)
                for birth_data in birth_data_sets
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.perf_counter()
            total_time = end_time - start_time

            # Count successful results
            successful_results = sum(
                1 for result in results if not isinstance(result, Exception)
            )

            # Concurrent execution should be faster than sequential
            assert (
                total_time < 5.0
            ), f"Concurrent execution too slow: {total_time:.2f}s"
            assert (
                successful_results >= len(birth_data_sets) * 0.8
            ), "Too many concurrent failures"

            print(
                f"Concurrent performance: {successful_results}/{len(birth_data_sets)} successful in {total_time:.2f}s"
            )

    async def test_performance_monitoring_integration(self, service):
        """Test integration with performance monitoring"""
        initial_stats = service.get_performance_stats()

        with patch.object(
            service.kerykeion_service, "get_full_natal_chart_data"
        ) as mock_calc:
            mock_calc.return_value = {
                "planets": {},
                "houses": {},
                "aspects": [],
            }

            # Perform calculations
            for i in range(5):
                await service.calculate_natal_chart_async(
                    name=f"Monitoring Test {i}",
                    birth_datetime=datetime(1990, 8, 15, 14, 30),
                    latitude=55.7558,
                    longitude=37.6176,
                    timezone="Europe/Moscow",
                )

        final_stats = service.get_performance_stats()

        # Performance stats should be updated
        assert (
            final_stats["total_operations"] > initial_stats["total_operations"]
        )
        assert (
            final_stats["async_operations"] > initial_stats["async_operations"]
        )
        assert final_stats["average_calculation_time"] >= 0

        print(
            f"Performance monitoring: {final_stats['total_operations']} operations tracked"
        )


@pytest.mark.performance
@pytest.mark.asyncio
class TestCacheServicePerformance:
    """Test caching system performance"""

    async def test_cache_hit_performance(self):
        """Test cache hit performance"""
        cache_key = "test_performance_key"
        test_data = {
            "planets": {"sun": {"sign": "leo", "degree": 22.5}},
            "houses": {"1": {"cusp": 0, "sign": "aries"}},
            "timestamp": time.time(),
        }

        # Store in cache
        await astro_cache.cache_data(cache_key, test_data, ttl_hours=1)

        # Measure cache hit performance
        hit_times = []

        for _ in range(100):  # Many cache hits
            start_time = time.perf_counter()

            cached_result = await astro_cache.get_cached_data(cache_key)

            end_time = time.perf_counter()
            hit_time = end_time - start_time

            if cached_result:
                hit_times.append(hit_time)

        if hit_times:
            avg_hit_time = statistics.mean(hit_times)
            max_hit_time = max(hit_times)

            # Cache hits should be very fast
            assert (
                avg_hit_time < 0.01
            ), f"Cache hits too slow: {avg_hit_time:.4f}s average"
            assert (
                max_hit_time < 0.05
            ), f"Worst cache hit too slow: {max_hit_time:.4f}s"

            print(
                f"Cache hit performance: {avg_hit_time:.4f}s average, {max_hit_time:.4f}s max"
            )

    async def test_cache_miss_performance(self):
        """Test cache miss performance"""
        non_existent_keys = [f"non_existent_key_{i}" for i in range(50)]

        miss_times = []

        for key in non_existent_keys:
            start_time = time.perf_counter()

            cached_result = await astro_cache.get_cached_data(key)

            end_time = time.perf_counter()
            miss_time = end_time - start_time

            miss_times.append(miss_time)
            assert cached_result is None

        avg_miss_time = statistics.mean(miss_times)
        max_miss_time = max(miss_times)

        # Cache misses should also be fast
        assert (
            avg_miss_time < 0.01
        ), f"Cache misses too slow: {avg_miss_time:.4f}s average"
        assert (
            max_miss_time < 0.05
        ), f"Worst cache miss too slow: {max_miss_time:.4f}s"

        print(
            f"Cache miss performance: {avg_miss_time:.4f}s average, {max_miss_time:.4f}s max"
        )

    async def test_cache_storage_performance(self):
        """Test cache storage performance under load"""
        storage_times = []

        for i in range(50):
            test_data = {
                "id": i,
                "planets": {
                    f"planet_{j}": {"sign": f"sign_{j}", "degree": j * 10}
                    for j in range(10)
                },
                "houses": {
                    str(k): {"cusp": k * 30, "sign": f"sign_{k}"}
                    for k in range(1, 13)
                },
                "aspects": [
                    {"planet1": "sun", "planet2": "moon", "orb": 2.5}
                    for _ in range(20)
                ],
            }

            cache_key = f"storage_test_{i}"

            start_time = time.perf_counter()

            await astro_cache.cache_data(cache_key, test_data, ttl_hours=1)

            end_time = time.perf_counter()
            storage_time = end_time - start_time

            storage_times.append(storage_time)

        avg_storage_time = statistics.mean(storage_times)
        max_storage_time = max(storage_times)

        # Cache storage should be reasonably fast
        assert (
            avg_storage_time < 0.1
        ), f"Cache storage too slow: {avg_storage_time:.4f}s average"
        assert (
            max_storage_time < 0.5
        ), f"Worst cache storage too slow: {max_storage_time:.4f}s"

        print(
            f"Cache storage performance: {avg_storage_time:.4f}s average, {max_storage_time:.4f}s max"
        )


@pytest.mark.performance
@pytest.mark.asyncio
class TestSystemLoadTesting:
    """System-wide load testing"""

    @pytest.fixture
    async def services(self):
        """Set up all services for load testing"""
        kerykeion_service = KerykeionService()
        async_service = AsyncKerykeionService(max_workers=8)
        transit_service = TransitService()

        yield {
            "kerykeion": kerykeion_service,
            "async_kerykeion": async_service,
            "transit": transit_service,
        }

        # Cleanup
        async_service.executor.shutdown(wait=True)

    async def test_mixed_workload_performance(self, services):
        """Test system performance under mixed workload"""
        # Create diverse workload
        tasks = []

        # Natal chart calculations
        for i in range(5):
            birth_data = {
                "name": f"Load Test Subject {i}",
                "birth_datetime": datetime(
                    1990 + i, 1 + i % 12, 1 + i % 28, 12, 0
                ),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow",
            }

            with patch.object(
                services["kerykeion"], "get_full_natal_chart_data"
            ) as mock_calc:
                mock_calc.return_value = {
                    "planets": {},
                    "houses": {},
                    "aspects": [],
                }
                tasks.append(
                    services["async_kerykeion"].calculate_natal_chart_async(
                        **birth_data
                    )
                )

        # Transit calculations
        for i in range(3):
            sample_natal_chart = {
                "planets": {"sun": {"longitude": 142.5, "sign": "leo"}},
                "birth_datetime": datetime(1990, 8, 15, 14, 30),
            }

            with patch.object(
                services["transit"], "_calculate_current_transits"
            ) as mock_transit:
                mock_transit.return_value = {"aspects": [], "energy_level": 75}
                tasks.append(
                    services["transit"].get_current_transits_async(
                        natal_chart=sample_natal_chart,
                        transit_date=datetime.now(),
                    )
                )

        # Execute mixed workload
        start_time = time.perf_counter()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Analyze results
        successful_results = sum(
            1 for result in results if not isinstance(result, Exception)
        )

        # Performance assertions
        assert total_time < 10.0, f"Mixed workload too slow: {total_time:.2f}s"
        assert (
            successful_results >= len(tasks) * 0.8
        ), f"Too many failures: {successful_results}/{len(tasks)}"

        print(
            f"Mixed workload: {successful_results}/{len(tasks)} successful in {total_time:.2f}s"
        )

    async def test_sustained_load_performance(self, services):
        """Test performance under sustained load"""
        duration_seconds = 10  # Test for 10 seconds
        end_time = time.time() + duration_seconds

        completed_operations = 0
        error_count = 0

        async def sustained_worker():
            nonlocal completed_operations, error_count

            while time.time() < end_time:
                try:
                    birth_data = {
                        "name": f"Sustained Test {completed_operations}",
                        "birth_datetime": datetime(1990, 8, 15, 14, 30),
                        "latitude": 55.7558,
                        "longitude": 37.6176,
                        "timezone": "Europe/Moscow",
                    }

                    with patch.object(
                        services["kerykeion"], "get_full_natal_chart_data"
                    ) as mock_calc:
                        mock_calc.return_value = {
                            "planets": {},
                            "houses": {},
                            "aspects": [],
                        }

                        result = await services[
                            "async_kerykeion"
                        ].calculate_natal_chart_async(**birth_data)

                        if result:
                            completed_operations += 1

                        # Small delay to prevent overwhelming
                        await asyncio.sleep(0.1)

                except Exception:
                    error_count += 1
                    await asyncio.sleep(0.1)  # Back off on errors

        # Run multiple concurrent workers
        workers = [sustained_worker() for _ in range(3)]
        await asyncio.gather(*workers)

        # Calculate performance metrics
        operations_per_second = completed_operations / duration_seconds
        error_rate = error_count / max(completed_operations + error_count, 1)

        # Performance assertions
        assert (
            operations_per_second >= 5
        ), f"Sustained throughput too low: {operations_per_second:.2f} ops/sec"
        assert error_rate < 0.1, f"Error rate too high: {error_rate:.2%}"

        print(
            f"Sustained load: {operations_per_second:.2f} ops/sec, {error_rate:.2%} error rate"
        )

    def test_memory_usage_under_load(self, services):
        """Test memory usage stability under load"""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Record initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_samples = [initial_memory]

        # Simulate load
        for batch in range(5):  # 5 batches
            for i in range(10):  # 10 operations per batch
                try:
                    birth_data = {
                        "name": f"Memory Load Test {batch}_{i}",
                        "birth_datetime": datetime(
                            1990 + batch, 1 + i % 12, 1 + i % 28, 12, 0
                        ),
                        "latitude": 55.7558,
                        "longitude": 37.6176,
                        "timezone": "Europe/Moscow",
                    }

                    # Simulate chart calculation
                    services[
                        "kerykeion"
                    ].get_full_natal_chart_data(**birth_data)

                except Exception:
                    pass  # Continue testing memory even if calculations fail

            # Sample memory after each batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)

        # Analyze memory usage
        final_memory = memory_samples[-1]
        max_memory = max(memory_samples)
        memory_growth = final_memory - initial_memory
        memory_peak = max_memory - initial_memory

        # Memory assertions
        assert (
            memory_growth < 100
        ), f"Excessive memory growth: {memory_growth:.2f}MB"
        assert memory_peak < 150, f"Memory peak too high: {memory_peak:.2f}MB"

        print(
            f"Memory under load: {memory_growth:.2f}MB growth, {memory_peak:.2f}MB peak"
        )


@pytest.mark.performance
class TestPerformanceRegressionDetection:
    """Test for performance regressions"""

    def test_baseline_performance_metrics(self):
        """Establish baseline performance metrics"""
        service = KerykeionService()

        if not service.is_available():
            pytest.skip("Kerykeion not available for performance baseline")

        birth_data = {
            "name": "Baseline Test",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow",
        }

        # Measure baseline performance
        times = []
        memory_usage = []

        import os

        import psutil

        process = psutil.Process(os.getpid())

        for _ in range(5):
            initial_memory = process.memory_info().rss / 1024 / 1024

            start_time = time.perf_counter()
            chart_data = service.get_full_natal_chart_data(**birth_data)
            end_time = time.perf_counter()

            final_memory = process.memory_info().rss / 1024 / 1024

            if "error" not in chart_data:
                times.append(end_time - start_time)
                memory_usage.append(final_memory - initial_memory)

        if times:
            # Establish baseline metrics
            baseline_metrics = {
                "average_time": statistics.mean(times),
                "median_time": statistics.median(times),
                "p95_time": sorted(times)[int(len(times) * 0.95)]
                if len(times) > 1
                else times[0],
                "average_memory": statistics.mean(memory_usage)
                if memory_usage
                else 0,
                "timestamp": time.time(),
            }

            # Store baseline for future regression tests
            # In a real implementation, this would be stored persistently
            print(f"Baseline metrics: {baseline_metrics}")

            # Basic sanity checks
            assert (
                baseline_metrics["average_time"] < 10.0
            ), "Baseline performance too slow"
            assert (
                baseline_metrics["p95_time"] < 15.0
            ), "95th percentile too slow"

            return baseline_metrics

    def test_performance_regression_detection(self):
        """Test for performance regressions against baseline"""
        # This would compare current performance against stored baseline
        baseline_metrics = self.test_baseline_performance_metrics()

        if not baseline_metrics:
            pytest.skip("No baseline metrics available")

        # Current performance test
        service = KerykeionService()

        birth_data = {
            "name": "Regression Test",
            "birth_datetime": datetime(1990, 8, 15, 14, 30),
            "latitude": 55.7558,
            "longitude": 37.6176,
            "timezone": "Europe/Moscow",
        }

        current_times = []

        for _ in range(5):
            start_time = time.perf_counter()
            chart_data = service.get_full_natal_chart_data(**birth_data)
            end_time = time.perf_counter()

            if "error" not in chart_data:
                current_times.append(end_time - start_time)

        if current_times:
            current_average = statistics.mean(current_times)
            current_p95 = (
                sorted(current_times)[int(len(current_times) * 0.95)]
                if len(current_times) > 1
                else current_times[0]
            )

            # Check for regression (50% slower than baseline)
            regression_threshold = 1.5

            time_regression = (
                current_average / baseline_metrics["average_time"]
            )
            p95_regression = current_p95 / baseline_metrics["p95_time"]

            # Regression detection
            assert (
                time_regression < regression_threshold
            ), f"Performance regression detected: {time_regression:.2f}x slower than baseline"
            assert (
                p95_regression < regression_threshold
            ), f"P95 performance regression: {p95_regression:.2f}x slower than baseline"

            print(
                f"Regression check: {time_regression:.2f}x avg time, {p95_regression:.2f}x p95 time"
            )


@pytest.mark.slow
@pytest.mark.performance
class TestStressAndReliabilityTesting:
    """Stress testing and reliability validation"""

    def test_extended_runtime_stability(self):
        """Test stability over extended runtime (marked as slow test)"""
        service = KerykeionService()

        if not service.is_available():
            pytest.skip("Kerykeion not available for stress testing")

        test_duration = 60  # 1 minute of continuous testing
        end_time = time.time() + test_duration

        successful_operations = 0
        failed_operations = 0
        operation_times = []

        while time.time() < end_time:
            birth_data = {
                "name": f"Stress Test {successful_operations + failed_operations}",
                "birth_datetime": datetime(1990, 8, 15, 14, 30),
                "latitude": 55.7558,
                "longitude": 37.6176,
                "timezone": "Europe/Moscow",
            }

            try:
                start_time = time.perf_counter()
                chart_data = service.get_full_natal_chart_data(**birth_data)
                end_time_op = time.perf_counter()

                operation_time = end_time_op - start_time

                if "error" not in chart_data:
                    successful_operations += 1
                    operation_times.append(operation_time)
                else:
                    failed_operations += 1

            except Exception:
                failed_operations += 1

            # Small delay to prevent overwhelming the system
            time.sleep(0.1)

        total_operations = successful_operations + failed_operations
        success_rate = successful_operations / max(total_operations, 1)

        if operation_times:
            avg_operation_time = statistics.mean(operation_times)
            time_std_dev = (
                statistics.stdev(operation_times)
                if len(operation_times) > 1
                else 0
            )
        else:
            avg_operation_time = 0
            time_std_dev = 0

        # Stability assertions
        assert (
            success_rate >= 0.95
        ), f"Success rate too low: {success_rate:.2%}"
        assert (
            avg_operation_time < 5.0
        ), f"Average operation time degraded: {avg_operation_time:.2f}s"
        assert (
            time_std_dev < 2.0
        ), f"Operation time too variable: {time_std_dev:.2f}s std dev"

        print(
            f"Extended stability: {success_rate:.2%} success rate, "
            f"{avg_operation_time:.2f}±{time_std_dev:.2f}s operation time"
        )

    def test_resource_exhaustion_recovery(self):
        """Test recovery from resource exhaustion scenarios"""
        service = AsyncKerykeionService(max_workers=2)  # Limited workers

        try:
            # Create resource pressure
            large_batch_size = 50
            birth_data_sets = [
                {
                    "name": f"Resource Test {i}",
                    "birth_datetime": datetime(
                        1990 + i % 30, 1 + i % 12, 1 + i % 28, 12, 0
                    ),
                    "latitude": 55.7558,
                    "longitude": 37.6176,
                    "timezone": "Europe/Moscow",
                }
                for i in range(large_batch_size)
            ]

            # Submit all tasks at once to create pressure
            async def resource_test():
                tasks = []
                for birth_data in birth_data_sets:
                    with patch.object(
                        service.kerykeion_service, "get_full_natal_chart_data"
                    ) as mock_calc:
                        mock_calc.return_value = {
                            "planets": {},
                            "houses": {},
                            "aspects": [],
                        }
                        tasks.append(
                            service.calculate_natal_chart_async(**birth_data)
                        )

                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results

            # Run the resource test
            results = asyncio.run(resource_test())

            # Check recovery
            successful_results = sum(
                1 for result in results if not isinstance(result, Exception)
            )

            # Should handle resource pressure gracefully
            assert (
                successful_results >= large_batch_size * 0.7
            ), f"Poor recovery from resource pressure: {successful_results}/{large_batch_size} successful"

            print(
                f"Resource recovery: {successful_results}/{large_batch_size} operations completed under pressure"
            )

        finally:
            service.executor.shutdown(wait=True)
