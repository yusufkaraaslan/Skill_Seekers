"""Keep dependency scans and cycle reporting bounded on developer checkouts."""

from pathlib import Path

import networkx as nx
import pytest

from skill_seekers.cli.codebase_scraper import walk_directory, walk_markdown_files
from skill_seekers.cli.config_extractor import ConfigFileDetector
from skill_seekers.cli.dependency_analyzer import DependencyAnalyzer
from skill_seekers.cli.test_example_extractor import TestExampleExtractor as ExampleExtractor


def test_scanners_skip_custom_virtualenv_and_dependency_trees(tmp_path):
    for name in ("venv_e2e", ".venv", "node_modules", "example.egg-info"):
        directory = tmp_path / name
        directory.mkdir()
        if name == "venv_e2e":
            (directory / "pyvenv.cfg").write_text("home = /usr/bin")
        (directory / "test_vendor.py").write_text("def test_vendor(): pass")
        (directory / "README.md").write_text("# Vendor")
        (directory / "vendor.json").write_text("{}")
    (tmp_path / "test_app.py").write_text("def test_app(): pass")
    (tmp_path / "README.md").write_text("# Application")
    (tmp_path / "config.json").write_text("{}")
    assert [p.name for p in walk_directory(tmp_path)] == ["test_app.py"]
    assert [p.name for p in walk_markdown_files(tmp_path)] == ["README.md"]
    assert ExampleExtractor(enhance_with_ai=False)._find_test_files(tmp_path, True) == [
        tmp_path / "test_app.py"
    ]
    assert {p.name for p in ConfigFileDetector()._walk_directory(tmp_path)} == {
        "test_app.py",
        "README.md",
        "config.json",
    }


def test_ignored_directories_are_pruned_before_descent(tmp_path, monkeypatch):
    import pathspec
    import skill_seekers.cli.file_discovery as discovery

    (tmp_path / "generated").mkdir()
    (tmp_path / "generated/dependency.py").write_text("")
    original = discovery.os.walk
    visited = []

    def walk(*args, **kwargs):
        for row in original(*args, **kwargs):
            visited.append(Path(row[0]).name)
            yield row

    monkeypatch.setattr(discovery.os, "walk", walk)
    assert (
        walk_directory(
            tmp_path, gitignore_spec=pathspec.PathSpec.from_lines("gitwildmatch", ["generated/"])
        )
        == []
    )
    assert "generated" not in visited


def test_dense_cycles_are_sampled_and_reported_as_truncated():
    analyzer = DependencyAnalyzer()
    analyzer.graph = nx.complete_graph([str(i) for i in range(12)], create_using=nx.DiGraph)
    assert len(analyzer.detect_cycles(max_cycles=20)) == 20
    assert analyzer.cycles_truncated
    stats = analyzer.get_statistics()
    assert stats["circular_dependencies"] == 100
    assert stats["circular_dependencies_truncated"]


def test_small_cycle_graph_remains_exact():
    analyzer = DependencyAnalyzer()
    analyzer.graph.add_edges_from([("a", "b"), ("b", "a")])
    assert len(analyzer.detect_cycles()) == 1
    assert not analyzer.cycles_truncated
    with pytest.raises(ValueError):
        analyzer.detect_cycles(0)


def test_config_detector_accepts_relative_directories(tmp_path, monkeypatch):
    (tmp_path / "proj").mkdir()
    (tmp_path / "proj/package.json").write_text("{}")
    monkeypatch.chdir(tmp_path)
    files = ConfigFileDetector().find_config_files(Path("proj"))
    assert [f.relative_path for f in files] == ["package.json"]
