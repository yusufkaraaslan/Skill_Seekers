#!/usr/bin/env python3
"""
Performance benchmarking CLI.

Measure and analyze performance of scraping, embedding, and storage operations.
"""

import sys
import argparse
import json
from pathlib import Path

from ..benchmark import Benchmark, BenchmarkRunner, BenchmarkReport


def run_command(args):
    """Run benchmark from config."""
    runner = BenchmarkRunner(output_dir=Path(args.output_dir))

    # Load benchmark config
    with open(args.config) as f:
        config = json.load(f)

    benchmark_type = config.get("type", "custom")

    if benchmark_type == "scraping":
        run_scraping_benchmark(runner, config)
    elif benchmark_type == "embedding":
        run_embedding_benchmark(runner, config)
    elif benchmark_type == "storage":
        run_storage_benchmark(runner, config)
    else:
        print(f"❌ Unknown benchmark type: {benchmark_type}")
        sys.exit(1)


def run_scraping_benchmark(runner, config):
    """Run scraping benchmark."""
    from .doc_scraper import scrape_all, build_skill

    def benchmark_func(bench: Benchmark):
        scrape_config_path = config.get("scrape_config")

        # Time scraping
        with bench.timer("scrape_docs"), bench.memory("scrape_docs"):
            pages = scrape_all(scrape_config_path)

        # Track metrics
        bench.metric("pages_scraped", len(pages), "pages")

        # Time building
        with bench.timer("build_skill"), bench.memory("build_skill"):
            build_skill(scrape_config_path, pages)

    name = config.get("name", "scraping-benchmark")
    report = runner.run(name, benchmark_func)

    print(f"\n{report.summary}")


def run_embedding_benchmark(runner, config):
    """Run embedding benchmark."""
    from ..embedding.generator import EmbeddingGenerator

    def benchmark_func(bench: Benchmark):
        generator = EmbeddingGenerator()

        model = config.get("model", "text-embedding-3-small")
        texts = config.get("sample_texts", ["Test text"])

        # Single embedding
        with bench.timer("single_embedding"):
            generator.generate(texts[0], model=model)

        # Batch embedding
        if len(texts) > 1:
            with bench.timer("batch_embedding"), bench.memory("batch_embedding"):
                embeddings = generator.generate_batch(texts, model=model)

            bench.metric(
                "embeddings_per_sec", len(embeddings) / bench.result.timings[-1].duration, "emb/sec"
            )

    name = config.get("name", "embedding-benchmark")
    report = runner.run(name, benchmark_func)

    print(f"\n{report.summary}")


def run_storage_benchmark(runner, config):
    """Run storage benchmark."""
    from .storage import get_storage_adaptor
    from tempfile import NamedTemporaryFile

    def benchmark_func(bench: Benchmark):
        provider = config.get("provider", "s3")
        bucket = config.get("bucket")

        storage = get_storage_adaptor(provider, bucket=bucket)

        # Create test file
        with NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test data" * 1000)
            test_file = Path(f.name)

        try:
            # Upload benchmark
            with bench.timer("upload"):
                storage.upload_file(test_file, "benchmark_test.txt")

            # Download benchmark
            download_path = test_file.parent / "downloaded.txt"
            with bench.timer("download"):
                storage.download_file("benchmark_test.txt", download_path)

            # Cleanup
            storage.delete_file("benchmark_test.txt")
            download_path.unlink(missing_ok=True)

        finally:
            test_file.unlink(missing_ok=True)

    name = config.get("name", "storage-benchmark")
    report = runner.run(name, benchmark_func)

    print(f"\n{report.summary}")


def compare_command(args):
    """Compare two benchmarks."""
    runner = BenchmarkRunner()

    comparison = runner.compare(baseline_path=Path(args.baseline), current_path=Path(args.current))

    print(f"\n📊 Comparison: {comparison.name}\n")
    print(f"Overall: {comparison.overall_improvement}\n")

    if comparison.improvements:
        print("✅ Improvements:")
        for improvement in comparison.improvements:
            print(f"   • {improvement}")

    if comparison.regressions:
        print("\n⚠️  Regressions:")
        for regression in comparison.regressions:
            print(f"   • {regression}")

    if args.fail_on_regression and comparison.has_regressions:
        print("\n❌ Benchmark failed: regressions detected")
        sys.exit(1)


def list_command(args):
    """List saved benchmarks."""
    runner = BenchmarkRunner(output_dir=Path(args.output_dir))

    benchmarks = runner.list_benchmarks()

    if not benchmarks:
        print("No benchmarks found")
        return

    print(f"\n📊 Saved benchmarks ({len(benchmarks)}):\n")

    for bench in benchmarks:
        print(f"• {bench['name']}")
        print(f"  Date: {bench['started_at']}")
        print(f"  Duration: {bench['duration']:.2f}s")
        print(f"  Operations: {bench['operations']}")
        print(f"  Path: {bench['path']}\n")


def show_command(args):
    """Show benchmark details."""
    with open(args.path) as f:
        data = json.load(f)

    report = BenchmarkReport(**data)

    print(f"\n{report.summary}\n")

    if report.timings:
        print("⏱️  Timings:")
        for timing in sorted(report.timings, key=lambda t: t.duration, reverse=True):
            print(f"   • {timing.operation}: {timing.duration:.2f}s")

    if report.memory:
        print("\n💾 Memory:")
        for mem in sorted(report.memory, key=lambda m: m.peak_mb, reverse=True):
            print(f"   • {mem.operation}: {mem.peak_mb:.0f}MB peak ({mem.allocated_mb:+.0f}MB)")

    if report.metrics:
        print("\n📈 Metrics:")
        for metric in report.metrics:
            print(f"   • {metric.name}: {metric.value:.2f} {metric.unit}")

    if report.recommendations:
        print("\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"   • {rec}")


def cleanup_command(args):
    """Cleanup old benchmarks."""
    runner = BenchmarkRunner(output_dir=Path(args.output_dir))

    runner.cleanup_old(keep_latest=args.keep)

    print("✅ Cleanup complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Performance benchmarking suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run scraping benchmark
  skill-seekers-benchmark run --config benchmarks/scraping.json

  # Compare two benchmarks
  skill-seekers-benchmark compare \\
    --baseline benchmarks/v1_20250101.json \\
    --current benchmarks/v2_20250115.json

  # List all benchmarks
  skill-seekers-benchmark list

  # Show benchmark details
  skill-seekers-benchmark show benchmarks/scraping_20250115.json

  # Cleanup old benchmarks
  skill-seekers-benchmark cleanup --keep 5
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run benchmark")
    run_parser.add_argument("--config", required=True, help="Benchmark config file")
    run_parser.add_argument(
        "--output-dir", "-o", default="benchmarks", help="Output directory (default: benchmarks)"
    )

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two benchmarks")
    compare_parser.add_argument("--baseline", required=True, help="Baseline benchmark")
    compare_parser.add_argument("--current", required=True, help="Current benchmark")
    compare_parser.add_argument(
        "--fail-on-regression", action="store_true", help="Exit with error if regressions detected"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List saved benchmarks")
    list_parser.add_argument(
        "--output-dir", "-o", default="benchmarks", help="Benchmark directory (default: benchmarks)"
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Show benchmark details")
    show_parser.add_argument("path", help="Path to benchmark file")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old benchmarks")
    cleanup_parser.add_argument(
        "--output-dir", "-o", default="benchmarks", help="Benchmark directory (default: benchmarks)"
    )
    cleanup_parser.add_argument(
        "--keep",
        type=int,
        default=5,
        help="Number of latest benchmarks to keep per name (default: 5)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "run":
            run_command(args)
        elif args.command == "compare":
            compare_command(args)
        elif args.command == "list":
            list_command(args)
        elif args.command == "show":
            show_command(args)
        elif args.command == "cleanup":
            cleanup_command(args)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
