"""Tests for signal collectors used by `skill-seekers scan` (issue #327).

The collectors are deterministic, stdlib-only helpers that gather evidence
from a project directory for the AI-driven detector. They do not classify
or interpret — they only sample.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


from skill_seekers.cli.signal_collectors import (
    collect_dockerfile_and_ci,
    collect_manifests,
    collect_readme_excerpt,
    collect_signals,
    collect_source_imports,
    get_git_remote,
    infer_project_name,
)


class TestCollectManifests:
    def test_picks_up_known_manifests(self, tmp_path: Path):
        (tmp_path / "package.json").write_text('{"name": "foo", "dependencies": {"react": "^18"}}')
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "foo"\ndependencies = ["httpx"]'
        )
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "foo"')

        signals = collect_manifests(tmp_path)

        names = {s.path.name for s in signals}
        assert names == {"package.json", "pyproject.toml", "Cargo.toml"}
        assert all(s.kind == "manifest" for s in signals)

    def test_ignores_unrelated_files(self, tmp_path: Path):
        (tmp_path / "README.md").write_text("# unrelated")
        (tmp_path / "random.txt").write_text("nope")

        signals = collect_manifests(tmp_path)
        assert signals == []

    def test_truncates_large_manifests(self, tmp_path: Path):
        big = "x" * 100_000
        (tmp_path / "package.json").write_text(big)

        signals = collect_manifests(tmp_path, max_bytes_per_file=1024)
        assert len(signals) == 1
        assert len(signals[0].content) <= 1024

    def test_handles_unreadable_file_gracefully(self, tmp_path: Path):
        # Create a manifest file then make it unreadable by injecting a read error.
        manifest = tmp_path / "package.json"
        manifest.write_text("{}")

        with patch("pathlib.Path.read_text", side_effect=OSError("boom")):
            signals = collect_manifests(tmp_path)

        assert signals == []  # silently skipped, not raised

    def test_case_insensitive_manifest_match(self, tmp_path: Path):
        # _CODE_PROJECT_MARKERS uses lowercase names but real filesystems may differ.
        (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\ngem 'rails'")

        signals = collect_manifests(tmp_path)
        names = {s.path.name for s in signals}
        assert "Gemfile" in names


class TestCollectReadmeExcerpt:
    def test_picks_up_readme_md(self, tmp_path: Path):
        (tmp_path / "README.md").write_text("# Cool Project\n\nDoes stuff.")
        signal = collect_readme_excerpt(tmp_path)
        assert signal is not None
        assert signal.kind == "readme"
        assert "Cool Project" in signal.content

    def test_picks_up_readme_rst(self, tmp_path: Path):
        (tmp_path / "README.rst").write_text("Cool Project\n============\n")
        signal = collect_readme_excerpt(tmp_path)
        assert signal is not None
        assert signal.kind == "readme"

    def test_no_readme_returns_none(self, tmp_path: Path):
        signal = collect_readme_excerpt(tmp_path)
        assert signal is None

    def test_truncates_large_readme(self, tmp_path: Path):
        (tmp_path / "README.md").write_text("x" * 100_000)
        signal = collect_readme_excerpt(tmp_path, max_bytes=2048)
        assert signal is not None
        assert len(signal.content) <= 2048


class TestCollectDockerfileAndCi:
    def test_picks_up_dockerfile(self, tmp_path: Path):
        (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim")
        signals = collect_dockerfile_and_ci(tmp_path)
        kinds = {s.kind for s in signals}
        names = {s.path.name for s in signals}
        assert "dockerfile" in kinds
        assert "Dockerfile" in names

    def test_picks_up_docker_compose(self, tmp_path: Path):
        (tmp_path / "docker-compose.yml").write_text("services:\n  app: {}")
        signals = collect_dockerfile_and_ci(tmp_path)
        assert any(s.path.name == "docker-compose.yml" for s in signals)

    def test_picks_up_github_workflows(self, tmp_path: Path):
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "ci.yml").write_text("name: CI\non: [push]")
        signals = collect_dockerfile_and_ci(tmp_path)
        assert any(s.path.name == "ci.yml" for s in signals)

    def test_picks_up_makefile(self, tmp_path: Path):
        (tmp_path / "Makefile").write_text("test:\n\tpytest\n")
        signals = collect_dockerfile_and_ci(tmp_path)
        assert any(s.path.name == "Makefile" for s in signals)

    def test_empty_when_no_ci(self, tmp_path: Path):
        signals = collect_dockerfile_and_ci(tmp_path)
        assert signals == []


class TestCollectSourceImports:
    def test_samples_python_imports(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text(
            "import httpx\nfrom anthropic import Anthropic\nimport json\n\ndef hello(): return 1\n"
        )
        signals = collect_source_imports(tmp_path)
        assert signals
        combined = "\n".join(s.content for s in signals)
        assert "import httpx" in combined
        assert "anthropic" in combined

    def test_samples_javascript_imports(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.js").write_text(
            "import React from 'react';\nimport { z } from 'zod';\nconst x = 1;\n"
        )
        signals = collect_source_imports(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "react" in combined
        assert "zod" in combined

    def test_limits_file_count(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        for i in range(50):
            (src / f"f{i}.py").write_text(f"import lib{i}\n")
        signals = collect_source_imports(tmp_path, max_files=5)
        assert len(signals) <= 5

    def test_no_source_dir_returns_empty(self, tmp_path: Path):
        # Project root only — no src/, lib/, app/.
        (tmp_path / "README.md").write_text("# foo")
        signals = collect_source_imports(tmp_path)
        assert signals == []

    def test_skips_node_modules_and_venv(self, tmp_path: Path):
        nm = tmp_path / "node_modules" / "react"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("import 'should-not-appear';")
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "x.py").write_text("import 'also-should-not-appear';")
        signals = collect_source_imports(tmp_path)
        assert signals == []

    def test_broken_symlink_does_not_crash_sort(self, tmp_path: Path):
        """A broken symlink in src/ must not crash the whole scan via p.stat()."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "real.py").write_text("import httpx\n")
        (src / "broken.py").symlink_to(tmp_path / "does-not-exist")

        # Must not raise; should still pick up the real file.
        signals = collect_source_imports(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "import httpx" in combined


class TestGetGitRemote:
    def test_returns_none_when_not_a_repo(self, tmp_path: Path):
        assert get_git_remote(tmp_path) is None

    def test_returns_remote_when_git_repo(self, tmp_path: Path):
        # Simulate `git config --get remote.origin.url` output by stubbing subprocess.
        with patch("skill_seekers.cli.signal_collectors.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "https://github.com/me/proj.git\n"
            assert get_git_remote(tmp_path) == "https://github.com/me/proj.git"

    def test_returns_none_on_subprocess_failure(self, tmp_path: Path):
        with patch(
            "skill_seekers.cli.signal_collectors.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            assert get_git_remote(tmp_path) is None


class TestInferProjectName:
    def test_uses_directory_name(self, tmp_path: Path):
        proj = tmp_path / "my-cool-app"
        proj.mkdir()
        assert infer_project_name(proj) == "my-cool-app"

    def test_strips_trailing_slash(self, tmp_path: Path):
        proj = tmp_path / "another"
        proj.mkdir()
        assert infer_project_name(proj) == "another"


class TestCollectSignals:
    def test_aggregates_all_collectors(self, tmp_path: Path):
        (tmp_path / "package.json").write_text('{"name": "x", "dependencies": {"react": "^18"}}')
        (tmp_path / "README.md").write_text("# X\nUses React.")
        (tmp_path / "Dockerfile").write_text("FROM node:20")
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.js").write_text("import React from 'react';")

        with patch("skill_seekers.cli.signal_collectors.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = ""  # no remote
            bundle = collect_signals(tmp_path)

        kinds = {s.kind for s in bundle.signals}
        assert "manifest" in kinds
        assert "readme" in kinds
        assert "dockerfile" in kinds
        # source-imports kind should appear when src/ exists
        assert any(s.kind == "source_imports" for s in bundle.signals)
        assert bundle.project_name == tmp_path.name

    def test_respects_total_byte_budget(self, tmp_path: Path):
        # Write oversized manifests; bundle should cap total bytes.
        (tmp_path / "package.json").write_text("x" * 50_000)
        (tmp_path / "pyproject.toml").write_text("y" * 50_000)
        (tmp_path / "README.md").write_text("z" * 50_000)

        bundle = collect_signals(tmp_path, total_byte_budget=8192)
        total = sum(len(s.content) for s in bundle.signals)
        assert total <= 8192
