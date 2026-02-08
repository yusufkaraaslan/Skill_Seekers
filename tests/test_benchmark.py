"""
Tests for benchmarking suite.
"""

import pytest
import time
import json
from datetime import datetime

# Skip all tests if psutil is not installed
pytest.importorskip("psutil")

from skill_seekers.benchmark import (
    Benchmark,
    BenchmarkResult,
    BenchmarkRunner,
    BenchmarkReport,
    Metric,
)
from skill_seekers.benchmark.models import TimingResult, MemoryUsage


class TestBenchmarkResult:
    """Test BenchmarkResult class."""

    def test_result_initialization(self):
        """Test result initialization."""
        result = BenchmarkResult("test-benchmark")

        assert result.name == "test-benchmark"
        assert isinstance(result.started_at, datetime)
        assert result.finished_at is None
        assert result.timings == []
        assert result.memory == []
        assert result.metrics == []
        assert result.system_info == {}
        assert result.recommendations == []

    def test_add_timing(self):
        """Test adding timing result."""
        result = BenchmarkResult("test")

        timing = TimingResult(operation="test_op", duration=1.5, iterations=1, avg_duration=1.5)

        result.add_timing(timing)

        assert len(result.timings) == 1
        assert result.timings[0].operation == "test_op"
        assert result.timings[0].duration == 1.5

    def test_add_memory(self):
        """Test adding memory usage."""
        result = BenchmarkResult("test")

        usage = MemoryUsage(
            operation="test_op", before_mb=100.0, after_mb=150.0, peak_mb=160.0, allocated_mb=50.0
        )

        result.add_memory(usage)

        assert len(result.memory) == 1
        assert result.memory[0].operation == "test_op"
        assert result.memory[0].allocated_mb == 50.0

    def test_add_metric(self):
        """Test adding custom metric."""
        result = BenchmarkResult("test")

        metric = Metric(name="pages_per_sec", value=12.5, unit="pages/sec")

        result.add_metric(metric)

        assert len(result.metrics) == 1
        assert result.metrics[0].name == "pages_per_sec"
        assert result.metrics[0].value == 12.5

    def test_add_recommendation(self):
        """Test adding recommendation."""
        result = BenchmarkResult("test")

        result.add_recommendation("Consider caching")

        assert len(result.recommendations) == 1
        assert result.recommendations[0] == "Consider caching"

    def test_set_system_info(self):
        """Test collecting system info."""
        result = BenchmarkResult("test")

        result.set_system_info()

        assert "cpu_count" in result.system_info
        assert "memory_total_gb" in result.system_info
        assert result.system_info["cpu_count"] > 0

    def test_to_report(self):
        """Test report generation."""
        result = BenchmarkResult("test")

        timing = TimingResult(operation="test_op", duration=1.0, iterations=1, avg_duration=1.0)
        result.add_timing(timing)

        report = result.to_report()

        assert isinstance(report, BenchmarkReport)
        assert report.name == "test"
        assert report.finished_at is not None
        assert len(report.timings) == 1
        assert report.total_duration > 0


class TestBenchmark:
    """Test Benchmark class."""

    def test_benchmark_initialization(self):
        """Test benchmark initialization."""
        benchmark = Benchmark("test")

        assert benchmark.name == "test"
        assert isinstance(benchmark.result, BenchmarkResult)

    def test_timer_context_manager(self):
        """Test timer context manager."""
        benchmark = Benchmark("test")

        with benchmark.timer("operation"):
            time.sleep(0.1)

        assert len(benchmark.result.timings) == 1
        assert benchmark.result.timings[0].operation == "operation"
        assert benchmark.result.timings[0].duration >= 0.1

    def test_timer_with_iterations(self):
        """Test timer with iterations."""
        benchmark = Benchmark("test")

        with benchmark.timer("operation", iterations=5):
            time.sleep(0.05)

        timing = benchmark.result.timings[0]
        assert timing.iterations == 5
        assert timing.avg_duration < timing.duration

    def test_memory_context_manager(self):
        """Test memory context manager."""
        benchmark = Benchmark("test")

        with benchmark.memory("operation"):
            # Allocate some memory
            pass

        assert len(benchmark.result.memory) == 1
        assert benchmark.result.memory[0].operation == "operation"
        assert benchmark.result.memory[0].allocated_mb >= 0

    def test_measure_function(self):
        """Test measure function."""
        benchmark = Benchmark("test")

        def slow_function(x):
            time.sleep(0.1)
            return x * 2

        result = benchmark.measure(slow_function, 5, operation="multiply")

        assert result == 10
        assert len(benchmark.result.timings) == 1
        assert benchmark.result.timings[0].operation == "multiply"

    def test_measure_with_memory_tracking(self):
        """Test measure with memory tracking."""
        benchmark = Benchmark("test")

        def allocate_memory():
            return [0] * 1000000

        benchmark.measure(allocate_memory, operation="allocate", track_memory=True)

        assert len(benchmark.result.timings) == 1
        assert len(benchmark.result.memory) == 1

    def test_timed_decorator(self):
        """Test timed decorator."""
        benchmark = Benchmark("test")

        @benchmark.timed("decorated_func")
        def my_function(x):
            time.sleep(0.05)
            return x + 1

        result = my_function(5)

        assert result == 6
        assert len(benchmark.result.timings) == 1
        assert benchmark.result.timings[0].operation == "decorated_func"

    def test_timed_decorator_with_memory(self):
        """Test timed decorator with memory tracking."""
        benchmark = Benchmark("test")

        @benchmark.timed("memory_func", track_memory=True)
        def allocate():
            return [0] * 1000000

        allocate()

        assert len(benchmark.result.timings) == 1
        assert len(benchmark.result.memory) == 1

    def test_metric_recording(self):
        """Test metric recording."""
        benchmark = Benchmark("test")

        benchmark.metric("throughput", 125.5, "ops/sec")

        assert len(benchmark.result.metrics) == 1
        assert benchmark.result.metrics[0].name == "throughput"
        assert benchmark.result.metrics[0].value == 125.5

    def test_recommendation_recording(self):
        """Test recommendation recording."""
        benchmark = Benchmark("test")

        benchmark.recommend("Use batch processing")

        assert len(benchmark.result.recommendations) == 1
        assert "batch" in benchmark.result.recommendations[0].lower()

    def test_report_generation(self):
        """Test report generation."""
        benchmark = Benchmark("test")

        with benchmark.timer("op1"):
            time.sleep(0.05)

        benchmark.metric("count", 10, "items")

        report = benchmark.report()

        assert isinstance(report, BenchmarkReport)
        assert report.name == "test"
        assert len(report.timings) == 1
        assert len(report.metrics) == 1

    def test_save_report(self, tmp_path):
        """Test saving report to file."""
        benchmark = Benchmark("test")

        with benchmark.timer("operation"):
            time.sleep(0.05)

        output_path = tmp_path / "benchmark.json"
        benchmark.save(output_path)

        assert output_path.exists()

        # Verify contents
        with open(output_path) as f:
            data = json.load(f)

        assert data["name"] == "test"
        assert len(data["timings"]) == 1

    def test_analyze_bottlenecks(self):
        """Test bottleneck analysis."""
        benchmark = Benchmark("test")

        # Create operations with different durations
        with benchmark.timer("fast"):
            time.sleep(0.01)

        with benchmark.timer("slow"):
            time.sleep(0.2)

        benchmark.analyze()

        # Should have recommendation about bottleneck
        assert len(benchmark.result.recommendations) > 0
        assert any("bottleneck" in r.lower() for r in benchmark.result.recommendations)

    def test_analyze_high_memory(self):
        """Test high memory usage detection."""
        benchmark = Benchmark("test")

        # Simulate high memory usage
        usage = MemoryUsage(
            operation="allocate",
            before_mb=100.0,
            after_mb=1200.0,
            peak_mb=1500.0,
            allocated_mb=1100.0,
        )
        benchmark.result.add_memory(usage)

        benchmark.analyze()

        # Should have recommendation about memory
        assert len(benchmark.result.recommendations) > 0
        assert any("memory" in r.lower() for r in benchmark.result.recommendations)


class TestBenchmarkRunner:
    """Test BenchmarkRunner class."""

    def test_runner_initialization(self, tmp_path):
        """Test runner initialization."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        assert runner.output_dir == tmp_path
        assert runner.output_dir.exists()

    def test_run_benchmark(self, tmp_path):
        """Test running single benchmark."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        def test_benchmark(bench):
            with bench.timer("operation"):
                time.sleep(0.05)

        report = runner.run("test", test_benchmark, save=True)

        assert isinstance(report, BenchmarkReport)
        assert report.name == "test"
        assert len(report.timings) == 1

        # Check file was saved
        saved_files = list(tmp_path.glob("test_*.json"))
        assert len(saved_files) == 1

    def test_run_benchmark_no_save(self, tmp_path):
        """Test running benchmark without saving."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        def test_benchmark(bench):
            with bench.timer("operation"):
                time.sleep(0.05)

        report = runner.run("test", test_benchmark, save=False)

        assert isinstance(report, BenchmarkReport)

        # No files should be saved
        saved_files = list(tmp_path.glob("*.json"))
        assert len(saved_files) == 0

    def test_run_suite(self, tmp_path):
        """Test running benchmark suite."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        def bench1(bench):
            with bench.timer("op1"):
                time.sleep(0.02)

        def bench2(bench):
            with bench.timer("op2"):
                time.sleep(0.03)

        reports = runner.run_suite({"test1": bench1, "test2": bench2})

        assert len(reports) == 2
        assert "test1" in reports
        assert "test2" in reports

        # Check both files saved
        saved_files = list(tmp_path.glob("*.json"))
        assert len(saved_files) == 2

    def test_compare_benchmarks(self, tmp_path):
        """Test comparing benchmarks."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        # Create baseline
        def baseline_bench(bench):
            with bench.timer("operation"):
                time.sleep(0.1)

        runner.run("baseline", baseline_bench, save=True)
        baseline_path = list(tmp_path.glob("baseline_*.json"))[0]

        # Create faster version
        def improved_bench(bench):
            with bench.timer("operation"):
                time.sleep(0.05)

        runner.run("improved", improved_bench, save=True)
        improved_path = list(tmp_path.glob("improved_*.json"))[0]

        # Compare
        from skill_seekers.benchmark.models import ComparisonReport

        comparison = runner.compare(baseline_path, improved_path)

        assert isinstance(comparison, ComparisonReport)
        assert comparison.speedup_factor > 1.0
        assert len(comparison.improvements) > 0

    def test_list_benchmarks(self, tmp_path):
        """Test listing benchmarks."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        # Create some benchmarks
        def test_bench(bench):
            with bench.timer("op"):
                time.sleep(0.02)

        runner.run("bench1", test_bench, save=True)
        runner.run("bench2", test_bench, save=True)

        benchmarks = runner.list_benchmarks()

        assert len(benchmarks) == 2
        assert all("name" in b for b in benchmarks)
        assert all("duration" in b for b in benchmarks)

    def test_get_latest(self, tmp_path):
        """Test getting latest benchmark."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        def test_bench(bench):
            with bench.timer("op"):
                time.sleep(0.02)

        # Run same benchmark twice
        runner.run("test", test_bench, save=True)
        time.sleep(0.1)  # Ensure different timestamps
        runner.run("test", test_bench, save=True)

        latest = runner.get_latest("test")

        assert latest is not None
        assert "test_" in latest.name

    def test_get_latest_not_found(self, tmp_path):
        """Test getting latest when benchmark doesn't exist."""
        runner = BenchmarkRunner(output_dir=tmp_path)

        latest = runner.get_latest("nonexistent")

        assert latest is None

    def test_cleanup_old(self, tmp_path):
        """Test cleaning up old benchmarks."""
        import os

        runner = BenchmarkRunner(output_dir=tmp_path)

        # Create 10 benchmark files with different timestamps
        base_time = time.time()
        for i in range(10):
            filename = f"test_{i:08d}.json"
            file_path = tmp_path / filename

            # Create minimal valid report
            report_data = {
                "name": "test",
                "started_at": datetime.utcnow().isoformat(),
                "finished_at": datetime.utcnow().isoformat(),
                "total_duration": 1.0,
                "timings": [],
                "memory": [],
                "metrics": [],
                "system_info": {},
                "recommendations": [],
            }

            with open(file_path, "w") as f:
                json.dump(report_data, f)

            # Set different modification times
            mtime = base_time - (10 - i) * 60  # Older files have older mtimes
            os.utime(file_path, (mtime, mtime))

        # Verify we have 10 files
        assert len(list(tmp_path.glob("test_*.json"))) == 10

        # Keep only latest 3
        runner.cleanup_old(keep_latest=3)

        remaining = list(tmp_path.glob("test_*.json"))
        assert len(remaining) == 3

        # Verify we kept the newest files (7, 8, 9)
        remaining_names = {f.stem for f in remaining}
        assert "test_00000007" in remaining_names or "test_00000008" in remaining_names


class TestBenchmarkModels:
    """Test benchmark model classes."""

    def test_timing_result_model(self):
        """Test TimingResult model."""
        timing = TimingResult(operation="test", duration=1.5, iterations=10, avg_duration=0.15)

        assert timing.operation == "test"
        assert timing.duration == 1.5
        assert timing.iterations == 10
        assert timing.avg_duration == 0.15

    def test_memory_usage_model(self):
        """Test MemoryUsage model."""
        usage = MemoryUsage(
            operation="allocate", before_mb=100.0, after_mb=200.0, peak_mb=250.0, allocated_mb=100.0
        )

        assert usage.operation == "allocate"
        assert usage.allocated_mb == 100.0
        assert usage.peak_mb == 250.0

    def test_metric_model(self):
        """Test Metric model."""
        metric = Metric(name="throughput", value=125.5, unit="ops/sec")

        assert metric.name == "throughput"
        assert metric.value == 125.5
        assert metric.unit == "ops/sec"
        assert isinstance(metric.timestamp, datetime)

    def test_benchmark_report_summary(self):
        """Test BenchmarkReport summary property."""
        report = BenchmarkReport(
            name="test",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            total_duration=5.0,
            timings=[TimingResult(operation="op1", duration=2.0, iterations=1, avg_duration=2.0)],
            memory=[
                MemoryUsage(
                    operation="op1",
                    before_mb=100.0,
                    after_mb=200.0,
                    peak_mb=250.0,
                    allocated_mb=100.0,
                )
            ],
            metrics=[],
            system_info={},
            recommendations=[],
        )

        summary = report.summary

        assert "test" in summary
        assert "5.00s" in summary
        assert "250.0MB" in summary

    def test_comparison_report_has_regressions(self):
        """Test ComparisonReport has_regressions property."""
        from skill_seekers.benchmark.models import ComparisonReport

        baseline = BenchmarkReport(
            name="baseline",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            total_duration=5.0,
            timings=[],
            memory=[],
            metrics=[],
            system_info={},
            recommendations=[],
        )

        current = BenchmarkReport(
            name="current",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            total_duration=10.0,
            timings=[],
            memory=[],
            metrics=[],
            system_info={},
            recommendations=[],
        )

        comparison = ComparisonReport(
            name="test",
            baseline=baseline,
            current=current,
            improvements=[],
            regressions=["Slower performance"],
            speedup_factor=0.5,
            memory_change_mb=0.0,
        )

        assert comparison.has_regressions is True

    def test_comparison_report_overall_improvement(self):
        """Test ComparisonReport overall_improvement property."""
        from skill_seekers.benchmark.models import ComparisonReport

        baseline = BenchmarkReport(
            name="baseline",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            total_duration=10.0,
            timings=[],
            memory=[],
            metrics=[],
            system_info={},
            recommendations=[],
        )

        current = BenchmarkReport(
            name="current",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            total_duration=5.0,
            timings=[],
            memory=[],
            metrics=[],
            system_info={},
            recommendations=[],
        )

        comparison = ComparisonReport(
            name="test",
            baseline=baseline,
            current=current,
            improvements=[],
            regressions=[],
            speedup_factor=2.0,
            memory_change_mb=0.0,
        )

        improvement = comparison.overall_improvement

        assert "100.0% faster" in improvement
        assert "✅" in improvement
