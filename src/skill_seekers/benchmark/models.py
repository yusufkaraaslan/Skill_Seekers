"""
Pydantic models for benchmarking.
"""

from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field


class Metric(BaseModel):
    """Single performance metric."""

    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit (seconds, bytes, pages/sec, etc.)")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When metric was recorded"
    )


class TimingResult(BaseModel):
    """Result of a timed operation."""

    operation: str = Field(..., description="Operation name")
    duration: float = Field(..., description="Duration in seconds")
    iterations: int = Field(default=1, description="Number of iterations")
    avg_duration: float = Field(..., description="Average duration per iteration")
    min_duration: float | None = Field(None, description="Minimum duration")
    max_duration: float | None = Field(None, description="Maximum duration")


class MemoryUsage(BaseModel):
    """Memory usage information."""

    operation: str = Field(..., description="Operation name")
    before_mb: float = Field(..., description="Memory before operation (MB)")
    after_mb: float = Field(..., description="Memory after operation (MB)")
    peak_mb: float = Field(..., description="Peak memory during operation (MB)")
    allocated_mb: float = Field(..., description="Memory allocated (MB)")


class BenchmarkReport(BaseModel):
    """Complete benchmark report."""

    name: str = Field(..., description="Benchmark name")
    started_at: datetime = Field(..., description="Start time")
    finished_at: datetime = Field(..., description="Finish time")
    total_duration: float = Field(..., description="Total duration in seconds")

    timings: list[TimingResult] = Field(default_factory=list, description="Timing results")
    memory: list[MemoryUsage] = Field(default_factory=list, description="Memory usage results")
    metrics: list[Metric] = Field(default_factory=list, description="Additional metrics")

    system_info: dict[str, Any] = Field(default_factory=dict, description="System information")
    recommendations: list[str] = Field(
        default_factory=list, description="Optimization recommendations"
    )

    @property
    def summary(self) -> str:
        """Generate summary string."""
        lines = [
            f"Benchmark: {self.name}",
            f"Duration: {self.total_duration:.2f}s",
            f"Operations: {len(self.timings)}",
            f"Peak Memory: {max([m.peak_mb for m in self.memory], default=0):.1f}MB",
        ]
        return "\n".join(lines)


class ComparisonReport(BaseModel):
    """Comparison between two benchmarks."""

    name: str = Field(..., description="Comparison name")
    baseline: BenchmarkReport = Field(..., description="Baseline benchmark")
    current: BenchmarkReport = Field(..., description="Current benchmark")

    improvements: list[str] = Field(default_factory=list, description="Performance improvements")
    regressions: list[str] = Field(default_factory=list, description="Performance regressions")

    speedup_factor: float = Field(..., description="Overall speedup factor")
    memory_change_mb: float = Field(..., description="Memory usage change (MB)")

    @property
    def has_regressions(self) -> bool:
        """Check if there are any regressions."""
        return len(self.regressions) > 0

    @property
    def overall_improvement(self) -> str:
        """Overall improvement summary."""
        if self.speedup_factor > 1.1:
            return f"✅ {(self.speedup_factor - 1) * 100:.1f}% faster"
        elif self.speedup_factor < 0.9:
            return f"❌ {(1 - self.speedup_factor) * 100:.1f}% slower"
        else:
            return "⚠️  Similar performance"
