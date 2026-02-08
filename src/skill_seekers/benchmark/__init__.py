"""
Performance benchmarking suite for Skill Seekers.

Measures and analyzes performance of:
- Documentation scraping
- Embedding generation
- Storage operations
- End-to-end workflows

Features:
- Accurate timing measurements
- Memory usage tracking
- CPU profiling
- Comparison reports
- Optimization recommendations

Usage:
    from skill_seekers.benchmark import Benchmark

    # Create benchmark
    benchmark = Benchmark("scraping-test")

    # Time operations
    with benchmark.timer("scrape_pages"):
        scrape_docs(config)

    # Generate report
    report = benchmark.report()
"""

from .framework import Benchmark, BenchmarkResult
from .runner import BenchmarkRunner
from .models import BenchmarkReport, Metric

__all__ = [
    "Benchmark",
    "BenchmarkResult",
    "BenchmarkRunner",
    "BenchmarkReport",
    "Metric",
]
