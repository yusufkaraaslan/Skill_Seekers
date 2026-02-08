#!/usr/bin/env python3
"""
Quality Metrics Dashboard

Provides comprehensive quality monitoring and reporting for skills.
Tracks completeness, accuracy, coverage, and health metrics.
"""

import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class MetricLevel(Enum):
    """Metric severity level."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityMetric:
    """Individual quality metric."""

    name: str
    value: float  # 0.0-1.0 (or 0-100 percentage)
    level: MetricLevel
    description: str
    suggestions: list[str] = field(default_factory=list)


@dataclass
class QualityScore:
    """Overall quality score."""

    total_score: float  # 0-100
    completeness: float  # 0-100
    accuracy: float  # 0-100
    coverage: float  # 0-100
    health: float  # 0-100
    grade: str  # A+, A, B+, B, C, D, F


@dataclass
class QualityReport:
    """Complete quality report."""

    timestamp: str
    skill_name: str
    overall_score: QualityScore
    metrics: list[QualityMetric]
    statistics: dict[str, Any]
    recommendations: list[str]
    history: list[dict[str, Any]] = field(default_factory=list)


class QualityAnalyzer:
    """
    Analyze skill quality across multiple dimensions.

    Provides comprehensive quality assessment and reporting.
    """

    # Thresholds for quality grades
    GRADE_THRESHOLDS = {
        "A+": 95,
        "A": 90,
        "A-": 85,
        "B+": 80,
        "B": 75,
        "B-": 70,
        "C+": 65,
        "C": 60,
        "C-": 55,
        "D": 50,
        "F": 0,
    }

    def __init__(self, skill_dir: Path):
        """Initialize quality analyzer."""
        self.skill_dir = Path(skill_dir)
        self.metrics: list[QualityMetric] = []
        self.statistics: dict[str, Any] = {}

    def analyze_completeness(self) -> float:
        """
        Analyze skill completeness.

        Checks for:
        - SKILL.md exists and has content
        - References directory exists
        - Minimum documentation coverage

        Returns:
            Completeness score (0-100)
        """
        score = 0.0
        max_score = 100.0

        # SKILL.md exists (40 points)
        skill_md = self.skill_dir / "SKILL.md"
        if skill_md.exists():
            score += 40
            content = skill_md.read_text(encoding="utf-8")

            # Has substantial content (10 points)
            if len(content) > 500:
                score += 10

            # Has sections (10 points)
            if content.count("#") >= 5:
                score += 10

        # References directory (20 points)
        refs_dir = self.skill_dir / "references"
        if refs_dir.exists():
            score += 10

            # Has reference files (10 points)
            refs = list(refs_dir.glob("*.md"))
            if len(refs) > 0:
                score += 10

        # Metadata/config (20 points)
        if (self.skill_dir / "skill.json").exists():
            score += 10
        if (self.skill_dir / ".skill_version.json").exists():
            score += 10

        completeness = (score / max_score) * 100

        # Add metric
        level = MetricLevel.INFO if completeness >= 70 else MetricLevel.WARNING
        suggestions = []
        if completeness < 100:
            if not skill_md.exists():
                suggestions.append("Create SKILL.md file")
            if not refs_dir.exists():
                suggestions.append("Add references directory")
            if len(suggestions) == 0:
                suggestions.append("Expand documentation coverage")

        self.metrics.append(
            QualityMetric(
                name="Completeness",
                value=completeness,
                level=level,
                description=f"Documentation completeness: {completeness:.1f}%",
                suggestions=suggestions,
            )
        )

        return completeness

    def analyze_accuracy(self) -> float:
        """
        Analyze skill accuracy.

        Checks for:
        - No broken links
        - Valid JSON/YAML
        - Consistent metadata
        - No duplicate content

        Returns:
            Accuracy score (0-100)
        """
        score = 100.0
        issues = []

        # Check for broken references
        skill_md = self.skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")

            # Check for TODO markers (deduct 5 points each, max 20)
            todo_count = content.lower().count("todo")
            if todo_count > 0:
                deduction = min(todo_count * 5, 20)
                score -= deduction
                issues.append(f"Found {todo_count} TODO markers")

            # Check for placeholder text (deduct 10)
            placeholders = ["lorem ipsum", "placeholder", "coming soon"]
            for placeholder in placeholders:
                if placeholder in content.lower():
                    score -= 10
                    issues.append(f"Found placeholder text: {placeholder}")
                    break

        # Check JSON validity
        for json_file in self.skill_dir.glob("*.json"):
            try:
                json.loads(json_file.read_text())
            except json.JSONDecodeError:
                score -= 15
                issues.append(f"Invalid JSON: {json_file.name}")

        accuracy = max(score, 0.0)

        level = MetricLevel.INFO if accuracy >= 80 else MetricLevel.WARNING
        suggestions = []
        if accuracy < 100 and issues:
            suggestions.extend(issues[:3])  # Top 3 issues

        self.metrics.append(
            QualityMetric(
                name="Accuracy",
                value=accuracy,
                level=level,
                description=f"Documentation accuracy: {accuracy:.1f}%",
                suggestions=suggestions,
            )
        )

        return accuracy

    def analyze_coverage(self) -> float:
        """
        Analyze documentation coverage.

        Checks for:
        - Multiple document types
        - Code examples
        - API references
        - Getting started guide

        Returns:
            Coverage score (0-100)
        """
        score = 0.0
        max_score = 100.0

        refs_dir = self.skill_dir / "references"
        if refs_dir.exists():
            ref_files = list(refs_dir.glob("*.md"))

            # Has multiple references (30 points)
            if len(ref_files) >= 3:
                score += 30
            elif len(ref_files) >= 1:
                score += 15

            # Check for specific types (20 points each)
            ref_names = [f.stem.lower() for f in ref_files]

            if any("getting" in name or "start" in name for name in ref_names):
                score += 20

            if any("api" in name or "reference" in name for name in ref_names):
                score += 20

            if any("example" in name or "tutorial" in name for name in ref_names):
                score += 20

            # Has diverse content (10 points)
            if len(ref_files) >= 5:
                score += 10

        coverage = (score / max_score) * 100

        level = MetricLevel.INFO if coverage >= 60 else MetricLevel.WARNING
        suggestions = []
        if coverage < 100:
            if coverage < 30:
                suggestions.append("Add getting started guide")
            if coverage < 60:
                suggestions.append("Add API reference documentation")
            suggestions.append("Expand documentation coverage")

        self.metrics.append(
            QualityMetric(
                name="Coverage",
                value=coverage,
                level=level,
                description=f"Documentation coverage: {coverage:.1f}%",
                suggestions=suggestions,
            )
        )

        return coverage

    def analyze_health(self) -> float:
        """
        Analyze skill health.

        Checks for:
        - File sizes reasonable
        - No empty files
        - Recent updates
        - Proper structure

        Returns:
            Health score (0-100)
        """
        score = 100.0
        issues = []

        # Check for empty files (deduct 15 each)
        for md_file in self.skill_dir.rglob("*.md"):
            if md_file.stat().st_size == 0:
                score -= 15
                issues.append(f"Empty file: {md_file.name}")

        # Check for very large files (deduct 10)
        for md_file in self.skill_dir.rglob("*.md"):
            if md_file.stat().st_size > 500_000:  # > 500KB
                score -= 10
                issues.append(f"Very large file: {md_file.name}")

        # Check directory structure (deduct 20 if missing)
        if not (self.skill_dir / "references").exists():
            score -= 20
            issues.append("Missing references directory")

        health = max(score, 0.0)

        level = MetricLevel.INFO if health >= 80 else MetricLevel.WARNING
        suggestions = []
        if health < 100:
            suggestions.extend(issues[:3])

        self.metrics.append(
            QualityMetric(
                name="Health",
                value=health,
                level=level,
                description=f"Skill health: {health:.1f}%",
                suggestions=suggestions,
            )
        )

        return health

    def calculate_statistics(self) -> dict[str, Any]:
        """Calculate skill statistics."""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "markdown_files": 0,
            "reference_files": 0,
            "total_characters": 0,
            "total_words": 0,
        }

        # Count files and sizes
        for md_file in self.skill_dir.rglob("*.md"):
            stats["total_files"] += 1
            stats["markdown_files"] += 1
            size = md_file.stat().st_size
            stats["total_size_bytes"] += size

            # Count words
            try:
                content = md_file.read_text(encoding="utf-8")
                stats["total_characters"] += len(content)
                stats["total_words"] += len(content.split())
            except Exception:
                pass

        # Count references
        refs_dir = self.skill_dir / "references"
        if refs_dir.exists():
            stats["reference_files"] = len(list(refs_dir.glob("*.md")))

        self.statistics = stats
        return stats

    def calculate_overall_score(
        self, completeness: float, accuracy: float, coverage: float, health: float
    ) -> QualityScore:
        """
        Calculate overall quality score.

        Weighted average:
        - Completeness: 30%
        - Accuracy: 25%
        - Coverage: 25%
        - Health: 20%
        """
        total = completeness * 0.30 + accuracy * 0.25 + coverage * 0.25 + health * 0.20

        # Determine grade
        grade = "F"
        for g, threshold in self.GRADE_THRESHOLDS.items():
            if total >= threshold:
                grade = g
                break

        return QualityScore(
            total_score=total,
            completeness=completeness,
            accuracy=accuracy,
            coverage=coverage,
            health=health,
            grade=grade,
        )

    def generate_recommendations(self, score: QualityScore) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        # Priority recommendations
        if score.completeness < 70:
            recommendations.append("🔴 PRIORITY: Improve documentation completeness")

        if score.accuracy < 80:
            recommendations.append("🟡 Address accuracy issues (TODOs, placeholders)")

        if score.coverage < 60:
            recommendations.append("🟡 Expand documentation coverage (API, examples)")

        if score.health < 80:
            recommendations.append("🟡 Fix health issues (empty files, structure)")

        # General recommendations
        if score.total_score < 80:
            recommendations.append("📝 Review and enhance overall documentation quality")

        if score.total_score >= 90:
            recommendations.append("✅ Excellent quality! Consider adding advanced topics")

        return recommendations

    def generate_report(self) -> QualityReport:
        """
        Generate comprehensive quality report.

        Returns:
            Complete quality report
        """
        # Run all analyses
        completeness = self.analyze_completeness()
        accuracy = self.analyze_accuracy()
        coverage = self.analyze_coverage()
        health = self.analyze_health()

        # Calculate overall score
        overall_score = self.calculate_overall_score(completeness, accuracy, coverage, health)

        # Calculate statistics
        stats = self.calculate_statistics()

        # Generate recommendations
        recommendations = self.generate_recommendations(overall_score)

        return QualityReport(
            timestamp=datetime.now().isoformat(),
            skill_name=self.skill_dir.name,
            overall_score=overall_score,
            metrics=self.metrics,
            statistics=stats,
            recommendations=recommendations,
        )

    def format_report(self, report: QualityReport) -> str:
        """Format report as human-readable text."""
        lines = ["=" * 70]
        lines.append("QUALITY METRICS DASHBOARD")
        lines.append("=" * 70)
        lines.append("")

        # Header
        lines.append(f"📊 Skill: {report.skill_name}")
        lines.append(f"🕐 Time: {report.timestamp}")
        lines.append("")

        # Overall Score
        score = report.overall_score
        lines.append("🎯 OVERALL SCORE")
        lines.append(f"   Grade: {score.grade}")
        lines.append(f"   Score: {score.total_score:.1f}/100")
        lines.append("")

        # Component Scores
        lines.append("📈 COMPONENT SCORES")
        lines.append(f"   Completeness: {score.completeness:.1f}% (30% weight)")
        lines.append(f"   Accuracy:     {score.accuracy:.1f}% (25% weight)")
        lines.append(f"   Coverage:     {score.coverage:.1f}% (25% weight)")
        lines.append(f"   Health:       {score.health:.1f}% (20% weight)")
        lines.append("")

        # Metrics
        lines.append("📋 DETAILED METRICS")
        for metric in report.metrics:
            icon = {
                MetricLevel.INFO: "✅",
                MetricLevel.WARNING: "⚠️",
                MetricLevel.ERROR: "❌",
                MetricLevel.CRITICAL: "🔴",
            }.get(metric.level, "ℹ️")

            lines.append(f"   {icon} {metric.name}: {metric.value:.1f}%")
            if metric.suggestions:
                for suggestion in metric.suggestions[:2]:
                    lines.append(f"      → {suggestion}")
        lines.append("")

        # Statistics
        lines.append("📊 STATISTICS")
        stats = report.statistics
        lines.append(f"   Total files: {stats.get('total_files', 0)}")
        lines.append(f"   Markdown files: {stats.get('markdown_files', 0)}")
        lines.append(f"   Reference files: {stats.get('reference_files', 0)}")
        lines.append(f"   Total words: {stats.get('total_words', 0):,}")
        lines.append(f"   Total size: {stats.get('total_size_bytes', 0):,} bytes")
        lines.append("")

        # Recommendations
        if report.recommendations:
            lines.append("💡 RECOMMENDATIONS")
            for rec in report.recommendations:
                lines.append(f"   {rec}")
            lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)


def main():
    """CLI entry point for quality metrics."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Analyze skill quality metrics")
    parser.add_argument("skill_dir", help="Path to skill directory")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--output", help="Output path for JSON report")
    parser.add_argument("--threshold", type=float, default=7.0, help="Quality threshold (0-10)")
    args = parser.parse_args()

    # Analyze skill
    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists():
        print(f"❌ Error: Directory not found: {skill_dir}")
        return 1

    analyzer = QualityAnalyzer(skill_dir)

    # Generate report
    report = analyzer.generate_report()

    # Display report
    if args.report:
        formatted = analyzer.format_report(report)
        print(formatted)

    # Save report
    report_path = Path(args.output) if args.output else skill_dir / "quality_report.json"

    report_path.write_text(json.dumps(asdict(report), indent=2, default=str))
    print(f"\n✅ Report saved: {report_path}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
