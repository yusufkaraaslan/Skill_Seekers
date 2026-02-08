"""
Benchmark execution and orchestration.
"""

import json
from pathlib import Path
from typing import Any
from collections.abc import Callable
from datetime import datetime

from .framework import Benchmark
from .models import BenchmarkReport, ComparisonReport


class BenchmarkRunner:
    """
    Run and compare benchmarks.

    Examples:
        runner = BenchmarkRunner()

        # Run single benchmark
        report = runner.run("scraping-v2", scraping_benchmark)

        # Compare with baseline
        comparison = runner.compare(
            baseline_path="benchmarks/v1.json",
            current_path="benchmarks/v2.json"
        )

        # Run suite
        reports = runner.run_suite({
            "scraping": scraping_benchmark,
            "embedding": embedding_benchmark,
        })
    """

    def __init__(self, output_dir: Path | None = None):
        """
        Initialize runner.

        Args:
            output_dir: Directory for benchmark results
        """
        self.output_dir = output_dir or Path("benchmarks")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self, name: str, benchmark_func: Callable[[Benchmark], None], save: bool = True
    ) -> BenchmarkReport:
        """
        Run single benchmark.

        Args:
            name: Benchmark name
            benchmark_func: Function that performs benchmark
            save: Whether to save results

        Returns:
            Benchmark report

        Examples:
            def scraping_benchmark(bench):
                with bench.timer("scrape"):
                    scrape_docs(config)

            report = runner.run("scraping-v2", scraping_benchmark)
        """
        benchmark = Benchmark(name)

        # Run benchmark
        benchmark_func(benchmark)

        # Generate report
        report = benchmark.report()

        # Save if requested
        if save:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.json"
            path = self.output_dir / filename

            with open(path, "w") as f:
                f.write(report.model_dump_json(indent=2))

            print(f"📊 Saved benchmark: {path}")

        return report

    def run_suite(
        self, benchmarks: dict[str, Callable[[Benchmark], None]], save: bool = True
    ) -> dict[str, BenchmarkReport]:
        """
        Run multiple benchmarks.

        Args:
            benchmarks: Dict of name -> benchmark function
            save: Whether to save results

        Returns:
            Dict of name -> report

        Examples:
            reports = runner.run_suite({
                "scraping": scraping_benchmark,
                "embedding": embedding_benchmark,
            })
        """
        reports = {}

        for name, func in benchmarks.items():
            print(f"\n🏃 Running benchmark: {name}")
            report = self.run(name, func, save=save)
            reports[name] = report

            print(report.summary)

        return reports

    def compare(self, baseline_path: Path, current_path: Path) -> ComparisonReport:
        """
        Compare two benchmark reports.

        Args:
            baseline_path: Path to baseline report
            current_path: Path to current report

        Returns:
            Comparison report

        Examples:
            comparison = runner.compare(
                baseline_path=Path("benchmarks/v1.json"),
                current_path=Path("benchmarks/v2.json")
            )

            print(comparison.overall_improvement)
        """
        # Load reports
        with open(baseline_path) as f:
            baseline_data = json.load(f)
            baseline = BenchmarkReport(**baseline_data)

        with open(current_path) as f:
            current_data = json.load(f)
            current = BenchmarkReport(**current_data)

        # Calculate changes
        improvements = []
        regressions = []

        # Compare timings
        baseline_timings = {t.operation: t for t in baseline.timings}
        current_timings = {t.operation: t for t in current.timings}

        for op, current_timing in current_timings.items():
            if op in baseline_timings:
                baseline_timing = baseline_timings[op]

                speedup = baseline_timing.duration / current_timing.duration

                if speedup > 1.1:  # >10% faster
                    improvements.append(
                        f"'{op}': {(speedup - 1) * 100:.1f}% faster "
                        f"({baseline_timing.duration:.2f}s → {current_timing.duration:.2f}s)"
                    )
                elif speedup < 0.9:  # >10% slower
                    regressions.append(
                        f"'{op}': {(1 - speedup) * 100:.1f}% slower "
                        f"({baseline_timing.duration:.2f}s → {current_timing.duration:.2f}s)"
                    )

        # Compare memory
        baseline_memory = {m.operation: m for m in baseline.memory}
        current_memory = {m.operation: m for m in current.memory}

        for op, current_mem in current_memory.items():
            if op in baseline_memory:
                baseline_mem = baseline_memory[op]

                mem_change = current_mem.peak_mb - baseline_mem.peak_mb

                if mem_change < -10:  # >10MB reduction
                    improvements.append(
                        f"'{op}' memory: {abs(mem_change):.0f}MB reduction "
                        f"({baseline_mem.peak_mb:.0f}MB → {current_mem.peak_mb:.0f}MB)"
                    )
                elif mem_change > 10:  # >10MB increase
                    regressions.append(
                        f"'{op}' memory: {mem_change:.0f}MB increase "
                        f"({baseline_mem.peak_mb:.0f}MB → {current_mem.peak_mb:.0f}MB)"
                    )

        # Overall speedup
        speedup_factor = baseline.total_duration / current.total_duration

        # Memory change
        baseline_peak = max([m.peak_mb for m in baseline.memory], default=0)
        current_peak = max([m.peak_mb for m in current.memory], default=0)
        memory_change_mb = current_peak - baseline_peak

        return ComparisonReport(
            name=f"{baseline.name} vs {current.name}",
            baseline=baseline,
            current=current,
            improvements=improvements,
            regressions=regressions,
            speedup_factor=speedup_factor,
            memory_change_mb=memory_change_mb,
        )

    def list_benchmarks(self) -> list[dict[str, Any]]:
        """
        List saved benchmarks.

        Returns:
            List of benchmark metadata

        Examples:
            benchmarks = runner.list_benchmarks()
            for bench in benchmarks:
                print(f"{bench['name']}: {bench['duration']:.1f}s")
        """
        benchmarks = []

        for path in self.output_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)

                benchmarks.append(
                    {
                        "name": data["name"],
                        "path": str(path),
                        "started_at": data["started_at"],
                        "duration": data["total_duration"],
                        "operations": len(data.get("timings", [])),
                    }
                )
            except Exception:
                # Skip invalid files
                continue

        # Sort by date
        benchmarks.sort(key=lambda b: b["started_at"], reverse=True)

        return benchmarks

    def get_latest(self, name: str) -> Path | None:
        """
        Get path to latest benchmark with given name.

        Args:
            name: Benchmark name

        Returns:
            Path to latest report, or None

        Examples:
            latest = runner.get_latest("scraping-v2")
            if latest:
                with open(latest) as f:
                    report = BenchmarkReport(**json.load(f))
        """
        matching = []

        for path in self.output_dir.glob(f"{name}_*.json"):
            matching.append(path)

        if not matching:
            return None

        # Sort by modification time
        matching.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        return matching[0]

    def cleanup_old(self, keep_latest: int = 5):
        """
        Remove old benchmark files.

        Args:
            keep_latest: Number of latest benchmarks to keep per name

        Examples:
            runner.cleanup_old(keep_latest=3)
        """
        # Group by benchmark name
        by_name: dict[str, list[Path]] = {}

        for path in self.output_dir.glob("*.json"):
            # Extract name from filename (name_timestamp.json)
            parts = path.stem.split("_")
            if len(parts) >= 2:
                name = "_".join(parts[:-1])  # Everything except timestamp

                if name not in by_name:
                    by_name[name] = []

                by_name[name].append(path)

        # Keep only latest N for each name
        removed = 0

        for name, paths in by_name.items():
            # Sort by modification time
            paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Remove old ones
            for path in paths[keep_latest:]:
                path.unlink()
                removed += 1

        if removed > 0:
            print(f"🗑️  Removed {removed} old benchmark(s)")
