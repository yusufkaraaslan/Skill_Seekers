#!/usr/bin/env python3
"""
Tests for quality metrics dashboard.

Validates:
- Completeness analysis
- Accuracy analysis
- Coverage analysis
- Health analysis
- Overall scoring
- Report generation
"""

import pytest
from pathlib import Path
import sys
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.quality_metrics import QualityAnalyzer, MetricLevel


@pytest.fixture
def complete_skill_dir():
    """Create complete skill directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "complete_skill"
        skill_dir.mkdir()

        # Create SKILL.md with substantial content
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Complete Skill\n\n" + ("## Section\nContent. " * 20))

        # Create references
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        (refs_dir / "getting_started.md").write_text("# Getting Started\nGuide content")
        (refs_dir / "api_reference.md").write_text("# API Reference\nAPI docs")
        (refs_dir / "examples.md").write_text("# Examples\nExample code")

        yield skill_dir


@pytest.fixture
def minimal_skill_dir():
    """Create minimal skill directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "minimal_skill"
        skill_dir.mkdir()

        # Only SKILL.md
        (skill_dir / "SKILL.md").write_text("# Minimal")

        yield skill_dir


def test_completeness_full(complete_skill_dir):
    """Test completeness analysis with complete skill."""
    analyzer = QualityAnalyzer(complete_skill_dir)
    score = analyzer.analyze_completeness()

    assert score >= 70  # Should be high (70 is good for test fixture)


def test_completeness_minimal(minimal_skill_dir):
    """Test completeness analysis with minimal skill."""
    analyzer = QualityAnalyzer(minimal_skill_dir)
    score = analyzer.analyze_completeness()

    assert score < 80  # Should be lower


def test_accuracy_clean():
    """Test accuracy analysis with clean content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "clean_skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Clean Skill\n\nNo issues here.")

        analyzer = QualityAnalyzer(skill_dir)
        score = analyzer.analyze_accuracy()

        assert score == 100  # Perfect score


def test_accuracy_with_todos():
    """Test accuracy detects TODO markers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "todo_skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Skill\n\nTODO: Add content\nTODO: Fix this")

        analyzer = QualityAnalyzer(skill_dir)
        score = analyzer.analyze_accuracy()

        assert score < 100  # Deducted for TODOs


def test_accuracy_with_placeholder():
    """Test accuracy detects placeholder text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "placeholder_skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Skill\n\nLorem ipsum dolor sit amet")

        analyzer = QualityAnalyzer(skill_dir)
        score = analyzer.analyze_accuracy()

        assert score < 100  # Deducted for placeholder


def test_coverage_high(complete_skill_dir):
    """Test coverage analysis with good coverage."""
    analyzer = QualityAnalyzer(complete_skill_dir)
    score = analyzer.analyze_coverage()

    assert score >= 60  # Should have decent coverage


def test_coverage_low():
    """Test coverage analysis with low coverage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "low_coverage"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Skill")

        analyzer = QualityAnalyzer(skill_dir)
        score = analyzer.analyze_coverage()

        assert score < 50  # Low coverage


def test_health_good():
    """Test health analysis with healthy skill."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "healthy_skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Healthy Skill\n\nGood content")

        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        analyzer = QualityAnalyzer(skill_dir)
        score = analyzer.analyze_health()

        assert score >= 80  # Healthy


def test_health_empty_files():
    """Test health detects empty files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "empty_files"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("")  # Empty

        analyzer = QualityAnalyzer(skill_dir)
        score = analyzer.analyze_health()

        assert score < 100  # Deducted for empty file


def test_calculate_statistics(complete_skill_dir):
    """Test statistics calculation."""
    analyzer = QualityAnalyzer(complete_skill_dir)
    stats = analyzer.calculate_statistics()

    assert stats["total_files"] > 0
    assert stats["markdown_files"] > 0
    assert stats["total_words"] > 0


def test_overall_score_calculation():
    """Test overall score calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Test Skill\n\nContent")

        analyzer = QualityAnalyzer(skill_dir)

        # Manually set scores
        completeness = 80.0
        accuracy = 90.0
        coverage = 70.0
        health = 85.0

        overall = analyzer.calculate_overall_score(completeness, accuracy, coverage, health)

        assert overall.completeness == 80.0
        assert overall.accuracy == 90.0
        assert overall.coverage == 70.0
        assert overall.health == 85.0
        assert 70 <= overall.total_score <= 90  # Weighted average


def test_grade_assignment():
    """Test grade assignment based on score."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()

        analyzer = QualityAnalyzer(skill_dir)

        # Test various scores
        score_95 = analyzer.calculate_overall_score(95, 95, 95, 95)
        assert score_95.grade == "A+"

        score_85 = analyzer.calculate_overall_score(85, 85, 85, 85)
        assert score_85.grade in ["A-", "B+"]

        score_70 = analyzer.calculate_overall_score(70, 70, 70, 70)
        assert score_70.grade in ["B-", "C+", "C"]


def test_generate_recommendations():
    """Test recommendation generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()

        analyzer = QualityAnalyzer(skill_dir)

        # Low completeness
        score = analyzer.calculate_overall_score(60, 80, 70, 80)
        recommendations = analyzer.generate_recommendations(score)

        assert len(recommendations) > 0
        assert any("completeness" in r.lower() for r in recommendations)


def test_generate_report(complete_skill_dir):
    """Test full report generation."""
    analyzer = QualityAnalyzer(complete_skill_dir)
    report = analyzer.generate_report()

    assert report.skill_name == "complete_skill"
    assert report.overall_score is not None
    assert len(report.metrics) == 4  # 4 analyses
    assert len(report.statistics) > 0
    assert report.timestamp is not None


def test_format_report(complete_skill_dir):
    """Test report formatting."""
    analyzer = QualityAnalyzer(complete_skill_dir)
    report = analyzer.generate_report()
    formatted = analyzer.format_report(report)

    assert "QUALITY METRICS DASHBOARD" in formatted
    assert "OVERALL SCORE" in formatted
    assert "COMPONENT SCORES" in formatted

    # RECOMMENDATIONS only appears if there are recommendations
    if report.recommendations:
        assert "RECOMMENDATIONS" in formatted


def test_metric_levels():
    """Test metric level assignment."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Test")

        analyzer = QualityAnalyzer(skill_dir)
        analyzer.analyze_completeness()

        assert len(analyzer.metrics) > 0
        assert analyzer.metrics[0].level in [MetricLevel.INFO, MetricLevel.WARNING]


def test_empty_skill_directory():
    """Test handling empty skill directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = Path(tmpdir) / "empty"
        empty_dir.mkdir()

        analyzer = QualityAnalyzer(empty_dir)
        report = analyzer.generate_report()

        assert report.overall_score.total_score < 50  # Very low score


def test_metric_suggestions():
    """Test metrics include suggestions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "incomplete_skill"
        skill_dir.mkdir()

        # Minimal content to trigger suggestions
        (skill_dir / "SKILL.md").write_text("# Minimal")

        analyzer = QualityAnalyzer(skill_dir)
        analyzer.analyze_completeness()

        # Should have suggestions
        assert len(analyzer.metrics) > 0
        if analyzer.metrics[0].value < 100:
            assert len(analyzer.metrics[0].suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
