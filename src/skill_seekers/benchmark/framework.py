"""
Core benchmarking framework.
"""

import time
import psutil
import functools
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from collections.abc import Callable
from pathlib import Path

from .models import Metric, TimingResult, MemoryUsage, BenchmarkReport


class BenchmarkResult:
    """
    Stores benchmark results during execution.

    Examples:
        result = BenchmarkResult("test-benchmark")
        result.add_timing(...)
        result.add_memory(...)
        report = result.to_report()
    """

    def __init__(self, name: str):
        """
        Initialize result collector.

        Args:
            name: Benchmark name
        """
        self.name = name
        self.started_at = datetime.utcnow()
        self.finished_at: datetime | None = None

        self.timings: list[TimingResult] = []
        self.memory: list[MemoryUsage] = []
        self.metrics: list[Metric] = []
        self.system_info: dict[str, Any] = {}
        self.recommendations: list[str] = []

    def add_timing(self, result: TimingResult):
        """Add timing result."""
        self.timings.append(result)

    def add_memory(self, usage: MemoryUsage):
        """Add memory usage."""
        self.memory.append(usage)

    def add_metric(self, metric: Metric):
        """Add custom metric."""
        self.metrics.append(metric)

    def add_recommendation(self, text: str):
        """Add optimization recommendation."""
        self.recommendations.append(text)

    def set_system_info(self):
        """Collect system information."""
        self.system_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "python_version": f"{psutil.version_info[0]}.{psutil.version_info[1]}",
        }

    def to_report(self) -> BenchmarkReport:
        """
        Generate final report.

        Returns:
            Complete benchmark report
        """
        if not self.finished_at:
            self.finished_at = datetime.utcnow()

        if not self.system_info:
            self.set_system_info()

        total_duration = (self.finished_at - self.started_at).total_seconds()

        return BenchmarkReport(
            name=self.name,
            started_at=self.started_at,
            finished_at=self.finished_at,
            total_duration=total_duration,
            timings=self.timings,
            memory=self.memory,
            metrics=self.metrics,
            system_info=self.system_info,
            recommendations=self.recommendations,
        )


class Benchmark:
    """
    Main benchmarking interface.

    Provides context managers and decorators for timing and profiling.

    Examples:
        # Create benchmark
        benchmark = Benchmark("scraping-test")

        # Time operations
        with benchmark.timer("scrape_pages"):
            scrape_docs(config)

        # Track memory
        with benchmark.memory("process_data"):
            process_large_dataset()

        # Generate report
        report = benchmark.report()
        print(report.summary)
    """

    def __init__(self, name: str):
        """
        Initialize benchmark.

        Args:
            name: Benchmark name
        """
        self.name = name
        self.result = BenchmarkResult(name)

    @contextmanager
    def timer(self, operation: str, iterations: int = 1):
        """
        Time an operation.

        Args:
            operation: Operation name
            iterations: Number of iterations (for averaging)

        Yields:
            None

        Examples:
            with benchmark.timer("load_pages"):
                load_all_pages()
        """
        start = time.perf_counter()

        try:
            yield
        finally:
            duration = time.perf_counter() - start

            timing = TimingResult(
                operation=operation,
                duration=duration,
                iterations=iterations,
                avg_duration=duration / iterations if iterations > 1 else duration,
            )

            self.result.add_timing(timing)

    @contextmanager
    def memory(self, operation: str):
        """
        Track memory usage.

        Args:
            operation: Operation name

        Yields:
            None

        Examples:
            with benchmark.memory("embed_docs"):
                generate_embeddings()
        """
        process = psutil.Process()

        # Get memory before
        mem_before = process.memory_info().rss / (1024**2)  # MB

        # Track peak during operation
        peak_memory = mem_before

        try:
            yield
        finally:
            # Get memory after
            mem_after = process.memory_info().rss / (1024**2)  # MB
            peak_memory = max(peak_memory, mem_after)

            usage = MemoryUsage(
                operation=operation,
                before_mb=mem_before,
                after_mb=mem_after,
                peak_mb=peak_memory,
                allocated_mb=mem_after - mem_before,
            )

            self.result.add_memory(usage)

    def measure(
        self,
        func: Callable,
        *args,
        operation: str | None = None,
        track_memory: bool = False,
        **kwargs,
    ) -> Any:
        """
        Measure function execution.

        Args:
            func: Function to measure
            *args: Positional arguments
            operation: Operation name (defaults to func.__name__)
            track_memory: Whether to track memory
            **kwargs: Keyword arguments

        Returns:
            Function result

        Examples:
            result = benchmark.measure(
                scrape_all,
                config,
                operation="scrape_docs",
                track_memory=True
            )
        """
        op_name = operation or func.__name__

        if track_memory:
            with self.memory(op_name), self.timer(op_name):
                return func(*args, **kwargs)
        else:
            with self.timer(op_name):
                return func(*args, **kwargs)

    def timed(self, operation: str | None = None, track_memory: bool = False):
        """
        Decorator for timing functions.

        Args:
            operation: Operation name (defaults to func.__name__)
            track_memory: Whether to track memory

        Returns:
            Decorated function

        Examples:
            @benchmark.timed("load_config")
            def load_config(path):
                return json.load(open(path))
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self.measure(
                    func, *args, operation=operation, track_memory=track_memory, **kwargs
                )

            return wrapper

        return decorator

    def metric(self, name: str, value: float, unit: str):
        """
        Record custom metric.

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement

        Examples:
            benchmark.metric("pages_per_sec", 12.5, "pages/sec")
        """
        metric = Metric(name=name, value=value, unit=unit)
        self.result.add_metric(metric)

    def recommend(self, text: str):
        """
        Add optimization recommendation.

        Args:
            text: Recommendation text

        Examples:
            if duration > 5.0:
                benchmark.recommend("Consider caching results")
        """
        self.result.add_recommendation(text)

    def report(self) -> BenchmarkReport:
        """
        Generate final report.

        Returns:
            Complete benchmark report
        """
        return self.result.to_report()

    def save(self, path: Path):
        """
        Save report to JSON file.

        Args:
            path: Output file path

        Examples:
            benchmark.save(Path("benchmarks/scraping_v2.json"))
        """
        report = self.report()

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(report.model_dump_json(indent=2))

    def analyze(self):
        """
        Analyze results and generate recommendations.

        Automatically called by report(), but can be called manually.
        """
        # Analyze timing bottlenecks
        if self.result.timings:
            sorted_timings = sorted(self.result.timings, key=lambda t: t.duration, reverse=True)

            slowest = sorted_timings[0]
            total_time = sum(t.duration for t in self.result.timings)

            if slowest.duration > total_time * 0.5:
                self.recommend(
                    f"Bottleneck: '{slowest.operation}' takes "
                    f"{slowest.duration:.1f}s ({slowest.duration / total_time * 100:.0f}% of total)"
                )

        # Analyze memory usage
        if self.result.memory:
            peak = max(m.peak_mb for m in self.result.memory)

            if peak > 1000:  # >1GB
                self.recommend(
                    f"High memory usage: {peak:.0f}MB peak. Consider processing in batches."
                )

            # Check for memory leaks
            for usage in self.result.memory:
                if usage.allocated_mb > 100:  # >100MB allocated
                    self.recommend(
                        f"Large allocation in '{usage.operation}': "
                        f"{usage.allocated_mb:.0f}MB. Check for memory leaks."
                    )
