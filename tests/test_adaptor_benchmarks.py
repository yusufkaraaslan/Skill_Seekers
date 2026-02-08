#!/usr/bin/env python3
"""
Performance Benchmarks for Platform Adaptors

Measures:
- format_skill_md() performance across all adaptors
- Complete package operation performance
- Scaling behavior with increasing reference count
- Output file sizes

Usage:
    # Run all benchmarks
    pytest tests/test_adaptor_benchmarks.py -v

    # Run with benchmark marker
    pytest tests/test_adaptor_benchmarks.py -v -m benchmark

    # Generate detailed output
    pytest tests/test_adaptor_benchmarks.py -v -s
"""

import json
import tempfile
import time
import unittest
from pathlib import Path

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


@pytest.mark.benchmark
class TestAdaptorBenchmarks(unittest.TestCase):
    """Performance benchmark suite for adaptors"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up"""
        self.temp_dir.cleanup()

    def _create_skill_with_n_references(self, n: int, skill_name: str = "benchmark") -> Path:
        """
        Create a skill directory with N reference files.

        Args:
            n: Number of reference files to create
            skill_name: Name of the skill

        Returns:
            Path to skill directory
        """
        skill_dir = Path(self.temp_dir.name) / f"skill_{n}_refs"
        skill_dir.mkdir(exist_ok=True)

        # Create SKILL.md (5KB)
        skill_content = f"# {skill_name.title()} Skill\n\n" + "Lorem ipsum dolor sit amet. " * 500
        (skill_dir / "SKILL.md").write_text(skill_content)

        # Create N reference files (5KB each)
        refs_dir = skill_dir / "references"
        refs_dir.mkdir(exist_ok=True)

        for i in range(n):
            content = f"# Reference {i}\n\n" + f"Content for reference {i}. " * 500
            (refs_dir / f"ref_{i:03d}.md").write_text(content)

        return skill_dir

    def test_benchmark_format_skill_md_all_adaptors(self):
        """Benchmark format_skill_md across all adaptors"""
        print("\n" + "=" * 80)
        print("BENCHMARK: format_skill_md() - All Adaptors")
        print("=" * 80)

        # Create test skill (10 references)
        skill_dir = self._create_skill_with_n_references(10)
        metadata = SkillMetadata(name="benchmark", description="Benchmark test")

        # Platforms to benchmark
        platforms = [
            "claude",
            "gemini",
            "openai",
            "markdown",  # IDE integrations
            "langchain",
            "llama-index",
            "haystack",  # RAG frameworks
            "weaviate",
            "chroma",
            "faiss",
            "qdrant",  # Vector DBs
        ]

        results = {}

        for platform in platforms:
            adaptor = get_adaptor(platform)

            # Warm up (1 iteration)
            adaptor.format_skill_md(skill_dir, metadata)

            # Benchmark (5 iterations)
            times = []
            for _ in range(5):
                start = time.perf_counter()
                formatted = adaptor.format_skill_md(skill_dir, metadata)
                end = time.perf_counter()
                times.append(end - start)

                # Validate output
                self.assertIsInstance(formatted, str)
                self.assertGreater(len(formatted), 0)

            # Calculate statistics
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            results[platform] = {"avg": avg_time, "min": min_time, "max": max_time}

            print(
                f"{platform:15} - Avg: {avg_time * 1000:6.2f}ms | "
                f"Min: {min_time * 1000:6.2f}ms | Max: {max_time * 1000:6.2f}ms"
            )

        # Performance assertions (should complete in reasonable time)
        for platform, metrics in results.items():
            self.assertLess(
                metrics["avg"],
                0.5,  # Should average < 500ms
                f"{platform} format_skill_md too slow: {metrics['avg'] * 1000:.2f}ms",
            )

    def test_benchmark_package_operations(self):
        """Benchmark complete package operation"""
        print("\n" + "=" * 80)
        print("BENCHMARK: package() - Complete Operation")
        print("=" * 80)

        # Create test skill (10 references)
        skill_dir = self._create_skill_with_n_references(10)

        # Benchmark subset of platforms (representative sample)
        platforms = ["claude", "langchain", "chroma", "weaviate", "faiss"]

        results = {}

        for platform in platforms:
            adaptor = get_adaptor(platform)

            # Benchmark packaging
            start = time.perf_counter()
            package_path = adaptor.package(skill_dir, self.output_dir)
            end = time.perf_counter()

            elapsed = end - start

            # Get file size
            file_size_kb = package_path.stat().st_size / 1024

            results[platform] = {"time": elapsed, "size_kb": file_size_kb}

            print(f"{platform:15} - Time: {elapsed * 1000:7.2f}ms | Size: {file_size_kb:7.1f} KB")

            # Validate output
            self.assertTrue(package_path.exists())

        # Performance assertions
        for platform, metrics in results.items():
            self.assertLess(
                metrics["time"],
                1.0,  # Should complete < 1 second
                f"{platform} packaging too slow: {metrics['time'] * 1000:.2f}ms",
            )
            self.assertLess(
                metrics["size_kb"],
                1000,  # Should be < 1MB for 10 refs
                f"{platform} package too large: {metrics['size_kb']:.1f}KB",
            )

    def test_benchmark_scaling_with_reference_count(self):
        """Test how performance scales with reference count"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Scaling with Reference Count")
        print("=" * 80)

        # Test with LangChain (representative RAG adaptor)
        adaptor = get_adaptor("langchain")
        metadata = SkillMetadata(name="scaling_test", description="Scaling benchmark test")

        reference_counts = [1, 5, 10, 25, 50]
        results = []

        print(f"\n{'Refs':>4} | {'Time (ms)':>10} | {'Time/Ref':>10} | {'Size (KB)':>10}")
        print("-" * 50)

        for ref_count in reference_counts:
            skill_dir = self._create_skill_with_n_references(ref_count)

            # Benchmark format_skill_md
            start = time.perf_counter()
            formatted = adaptor.format_skill_md(skill_dir, metadata)
            end = time.perf_counter()

            elapsed = end - start
            time_per_ref = elapsed / ref_count

            # Get output size
            json.loads(formatted)
            size_kb = len(formatted) / 1024

            results.append(
                {
                    "count": ref_count,
                    "time": elapsed,
                    "time_per_ref": time_per_ref,
                    "size_kb": size_kb,
                }
            )

            print(
                f"{ref_count:4} | {elapsed * 1000:10.2f} | {time_per_ref * 1000:10.3f} | {size_kb:10.1f}"
            )

        # Analyze scaling behavior
        # Time per ref should not increase significantly (linear scaling)
        first_per_ref = results[0]["time_per_ref"]
        last_per_ref = results[-1]["time_per_ref"]

        scaling_factor = last_per_ref / first_per_ref

        print(f"\nScaling Factor: {scaling_factor:.2f}x")
        print(f"(Time per ref at 50 refs / Time per ref at 1 ref)")

        # Assert linear or sub-linear scaling (not exponential)
        self.assertLess(scaling_factor, 3.0, f"Non-linear scaling detected: {scaling_factor:.2f}x")

    def test_benchmark_json_vs_zip_size_comparison(self):
        """Compare output sizes: JSON vs ZIP/tar.gz"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Output Size Comparison")
        print("=" * 80)

        # Create test skill (10 references)
        skill_dir = self._create_skill_with_n_references(10)

        # Package with different formats
        formats = {
            "claude": ("ZIP", ".zip"),
            "gemini": ("tar.gz", ".tar.gz"),
            "langchain": ("JSON", ".json"),
            "weaviate": ("JSON", ".json"),
        }

        results = {}

        print(f"\n{'Platform':15} | {'Format':8} | {'Size (KB)':>10}")
        print("-" * 50)

        for platform, (format_name, ext) in formats.items():
            adaptor = get_adaptor(platform)
            package_path = adaptor.package(skill_dir, self.output_dir)

            size_kb = package_path.stat().st_size / 1024

            results[platform] = {"format": format_name, "size_kb": size_kb}

            print(f"{platform:15} | {format_name:8} | {size_kb:10.1f}")

        # Analyze results
        json_sizes = [v["size_kb"] for k, v in results.items() if v["format"] == "JSON"]
        compressed_sizes = [
            v["size_kb"] for k, v in results.items() if v["format"] in ["ZIP", "tar.gz"]
        ]

        if json_sizes and compressed_sizes:
            avg_json = sum(json_sizes) / len(json_sizes)
            avg_compressed = sum(compressed_sizes) / len(compressed_sizes)

            print(f"\nAverage JSON size: {avg_json:.1f} KB")
            print(f"Average compressed size: {avg_compressed:.1f} KB")
            print(f"Compression ratio: {avg_json / avg_compressed:.2f}x")

    def test_benchmark_metadata_overhead(self):
        """Measure metadata processing overhead"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Metadata Processing Overhead")
        print("=" * 80)

        skill_dir = self._create_skill_with_n_references(10)

        # Minimal metadata
        minimal_meta = SkillMetadata(name="test", description="Test")

        # Rich metadata
        rich_meta = SkillMetadata(
            name="test",
            description="A comprehensive test skill for benchmarking purposes",
            version="2.5.0",
            author="Benchmark Suite",
            tags=["test", "benchmark", "performance", "validation", "quality"],
        )

        adaptor = get_adaptor("langchain")

        # Benchmark with minimal metadata
        times_minimal = []
        for _ in range(5):
            start = time.perf_counter()
            adaptor.format_skill_md(skill_dir, minimal_meta)
            end = time.perf_counter()
            times_minimal.append(end - start)

        # Benchmark with rich metadata
        times_rich = []
        for _ in range(5):
            start = time.perf_counter()
            adaptor.format_skill_md(skill_dir, rich_meta)
            end = time.perf_counter()
            times_rich.append(end - start)

        avg_minimal = sum(times_minimal) / len(times_minimal)
        avg_rich = sum(times_rich) / len(times_rich)

        overhead = avg_rich - avg_minimal
        overhead_pct = (overhead / avg_minimal) * 100

        print(f"\nMinimal metadata: {avg_minimal * 1000:.2f}ms")
        print(f"Rich metadata:    {avg_rich * 1000:.2f}ms")
        print(f"Overhead:         {overhead * 1000:.2f}ms ({overhead_pct:.1f}%)")

        # Overhead should be negligible (< 10%)
        self.assertLess(overhead_pct, 10.0, f"Metadata overhead too high: {overhead_pct:.1f}%")

    def test_benchmark_empty_vs_full_skill(self):
        """Compare performance: empty skill vs full skill"""
        print("\n" + "=" * 80)
        print("BENCHMARK: Empty vs Full Skill")
        print("=" * 80)

        adaptor = get_adaptor("chroma")
        metadata = SkillMetadata(name="test", description="Test benchmark")

        # Empty skill
        empty_dir = Path(self.temp_dir.name) / "empty"
        empty_dir.mkdir()

        start = time.perf_counter()
        adaptor.format_skill_md(empty_dir, metadata)
        empty_time = time.perf_counter() - start

        # Full skill (50 references)
        full_dir = self._create_skill_with_n_references(50)

        start = time.perf_counter()
        adaptor.format_skill_md(full_dir, metadata)
        full_time = time.perf_counter() - start

        print(f"\nEmpty skill: {empty_time * 1000:.2f}ms")
        print(f"Full skill (50 refs): {full_time * 1000:.2f}ms")
        print(f"Ratio: {full_time / empty_time:.1f}x")

        # Empty should be very fast
        self.assertLess(empty_time, 0.01, "Empty skill processing too slow")

        # Full should scale reasonably
        self.assertLess(full_time, 0.5, "Full skill processing too slow")


if __name__ == "__main__":
    # Run benchmarks
    unittest.main(verbosity=2)
