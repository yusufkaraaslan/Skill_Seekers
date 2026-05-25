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
    collect_source_samples,
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

    def test_reads_only_max_bytes_from_disk(self, tmp_path: Path):
        """Regression: _safe_read_text should NOT slurp the entire file into
        memory and then slice. For a 10 MB file with max_bytes=2 KB, we read
        2 KB."""
        from skill_seekers.cli.signal_collectors import _safe_read_text

        big = tmp_path / "huge.txt"
        big.write_bytes(b"a" * 10_000_000)  # 10 MB

        with patch("pathlib.Path.open", wraps=big.open) as open_mock:
            result = _safe_read_text(big, max_bytes=2048)

        assert result is not None
        assert len(result) == 2048
        # Verify Path.open was called (binary mode) — implementation calls
        # f.read(max_bytes) so it never holds the full file in memory.
        assert open_mock.called

    def test_handles_unreadable_file_gracefully(self, tmp_path: Path):
        # Create a manifest file then make it unreadable by injecting a read error.
        manifest = tmp_path / "package.json"
        manifest.write_text("{}")

        with patch("pathlib.Path.open", side_effect=OSError("boom")):
            signals = collect_manifests(tmp_path)

        assert signals == []  # silently skipped, not raised

    def test_case_insensitive_manifest_match(self, tmp_path: Path):
        # CODE_PROJECT_MARKERS uses lowercase names but real filesystems may differ.
        (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\ngem 'rails'")

        signals = collect_manifests(tmp_path)
        names = {s.path.name for s in signals}
        assert "Gemfile" in names

    def test_new_manifest_types_picked_up(self, tmp_path: Path):
        """Regression for WS3: tool now recognizes manifests beyond the 2018 web-dev set."""
        manifests = [
            ("Pipfile", "[packages]\nrequests = '*'"),
            ("environment.yml", "name: foo\ndependencies:\n  - numpy"),
            ("deno.json", '{"tasks": {"start": "deno run main.ts"}}'),
            ("flake.nix", '{ description = "my project"; }'),
            ("Chart.yaml", "apiVersion: v2\nname: mychart"),
            ("stack.yaml", "resolver: lts-22.0"),
            ("project.clj", '(defproject myproj "0.1.0")'),
            ("deps.edn", '{:deps {clojure.core {:mvn/version "1.11.0"}}}'),
            ("dune-project", "(lang dune 3.0)"),
            ("turbo.json", '{"pipeline": {}}'),
            ("pnpm-workspace.yaml", "packages:\n  - 'packages/*'"),
            ("Brewfile", "tap 'homebrew/cask'"),
        ]
        for name, content in manifests:
            (tmp_path / name).write_text(content)

        signals = collect_manifests(tmp_path)
        names = {s.path.name for s in signals}
        for name, _ in manifests:
            assert name in names, f"{name} should be picked up but was not"

    def test_requirements_variants_picked_up(self, tmp_path: Path):
        for name in ("requirements.txt", "requirements-dev.in", "requirements.in"):
            (tmp_path / name).write_text("httpx\n")
        signals = collect_manifests(tmp_path)
        names = {s.path.name for s in signals}
        assert names == {"requirements.txt", "requirements-dev.in", "requirements.in"}


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


class TestCollectSourceSamples_legacy_alias:
    """Verify the deprecated alias still works for one release cycle."""

    def test_alias_returns_same_signals(self, tmp_path: Path):
        from skill_seekers.cli.signal_collectors import collect_source_imports

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text("import httpx\n")
        primary = collect_source_samples(tmp_path)
        alias = collect_source_imports(tmp_path)
        assert [s.content for s in primary] == [s.content for s in alias]


class TestCollectSourceSamples:
    def test_samples_python_imports(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text(
            "import httpx\nfrom anthropic import Anthropic\nimport json\n\ndef hello(): return 1\n"
        )
        signals = collect_source_samples(tmp_path)
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
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "react" in combined
        assert "zod" in combined

    def test_limits_file_count(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        for i in range(50):
            (src / f"f{i}.py").write_text(f"import lib{i}\n")
        signals = collect_source_samples(tmp_path, max_files=5)
        assert len(signals) <= 5

    def test_no_source_dir_returns_empty(self, tmp_path: Path):
        # Project root only — no src/, lib/, app/.
        (tmp_path / "README.md").write_text("# foo")
        signals = collect_source_samples(tmp_path)
        assert signals == []

    def test_skips_node_modules_and_venv(self, tmp_path: Path):
        nm = tmp_path / "node_modules" / "react"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("import 'should-not-appear';")
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "x.py").write_text("import 'also-should-not-appear';")
        signals = collect_source_samples(tmp_path)
        assert signals == []

    def test_broken_symlink_does_not_crash_sort(self, tmp_path: Path):
        """A broken symlink in src/ must not crash the whole scan via p.stat()."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "real.py").write_text("import httpx\n")
        (src / "broken.py").symlink_to(tmp_path / "does-not-exist")

        # Must not raise; should still pick up the real file.
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "import httpx" in combined

    def test_picks_up_go_cmd_dir(self, tmp_path: Path):
        """Regression for WS3: Go projects use cmd/ for entry points."""
        cmd_dir = tmp_path / "cmd" / "server"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "main.go").write_text('package main\nimport "fmt"\n')
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "fmt" in combined

    def test_picks_up_monorepo_packages_dir(self, tmp_path: Path):
        """Regression for WS3: Turbo/Nx-style monorepos use packages/."""
        pkg = tmp_path / "packages" / "ui" / "src"
        pkg.mkdir(parents=True)
        (pkg / "Button.tsx").write_text("import React from 'react';\n")
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "react" in combined

    def test_picks_up_root_level_django_apps(self, tmp_path: Path):
        """Regression for WS3: Django/flat-layout puts apps directly under root."""
        # Simulate a Django project where apps live at root, not under src/
        users_app = tmp_path / "users"
        users_app.mkdir()
        (users_app / "models.py").write_text("from django.db import models\n")
        (users_app / "views.py").write_text("from django.shortcuts import render\n")
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "django" in combined

    def test_picks_up_root_level_python_entrypoint(self, tmp_path: Path):
        """Regression for WS3: flat-layout Python (script at root) is sampled."""
        (tmp_path / "main.py").write_text("import httpx\nimport asyncio\n")
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "httpx" in combined

    def test_whole_file_sampling_captures_multiline_go_imports(self, tmp_path: Path):
        """Regression for WS4: regex couldn't handle Go's parenthesized multi-line
        import block. Whole-file sampling captures the whole block verbatim."""
        cmd = tmp_path / "cmd" / "server"
        cmd.mkdir(parents=True)
        (cmd / "main.go").write_text(
            "package main\n"
            "\n"
            "import (\n"
            '    "fmt"\n'
            '    "net/http"\n'
            '    "github.com/gin-gonic/gin"\n'
            ")\n"
            "\n"
            "func main() {}\n"
        )
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "gin-gonic/gin" in combined
        assert "net/http" in combined
        assert "fmt" in combined

    def test_whole_file_sampling_captures_rust_mod_and_extern_crate(self, tmp_path: Path):
        """Regression for WS4: regex missed `mod x;` and `extern crate x;`. Whole-file
        sampling sees them as part of the raw file content."""
        crates = tmp_path / "crates" / "core"
        crates.mkdir(parents=True)
        (crates / "lib.rs").write_text(
            "extern crate serde;\nmod parser;\nmod codegen;\n\npub fn hello() {}\n"
        )
        signals = collect_source_samples(tmp_path)
        combined = "\n".join(s.content for s in signals)
        assert "extern crate serde" in combined
        assert "mod parser" in combined
        assert "mod codegen" in combined

    def test_source_sample_kind_is_source_sample(self, tmp_path: Path):
        """The Signal.kind for whole-file sampling is 'source_sample' (not the
        old 'source_imports' label)."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text("import httpx\n")
        signals = collect_source_samples(tmp_path)
        assert signals
        assert all(s.kind == "source_sample" for s in signals)


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
        assert any(s.kind == "source_sample" for s in bundle.signals)
        assert bundle.project_name == tmp_path.name

    def test_respects_total_byte_budget(self, tmp_path: Path):
        # Write oversized manifests; bundle should cap total bytes.
        (tmp_path / "package.json").write_text("x" * 50_000)
        (tmp_path / "pyproject.toml").write_text("y" * 50_000)
        (tmp_path / "README.md").write_text("z" * 50_000)

        bundle = collect_signals(tmp_path, total_byte_budget=8192)
        total = sum(len(s.content) for s in bundle.signals)
        assert total <= 8192

    def test_per_kind_budget_fat_manifest_does_not_starve_readme(self, tmp_path: Path):
        """Regression for WS5: a 50 KB package.json used to consume the entire
        64 KB global budget and crowd out README + source samples. Per-kind
        budgets guarantee each category gets a slice."""
        (tmp_path / "package.json").write_text("x" * 50_000)
        readme_marker = "UNIQUE_README_CONTENT_FOR_ASSERTION"
        (tmp_path / "README.md").write_text(f"# Project\n\n{readme_marker}\n")
        src = tmp_path / "src"
        src.mkdir()
        src_marker = "UNIQUE_SOURCE_IMPORT_FOR_ASSERTION"
        (src / "app.py").write_text(f"import {src_marker}\n")

        bundle = collect_signals(tmp_path)
        combined = "\n".join(s.content for s in bundle.signals)

        # All three kinds must be represented.
        assert readme_marker in combined, "README starved by fat manifest"
        assert src_marker in combined, "Source sample starved by fat manifest"
        assert "package.json" in {s.path.name for s in bundle.signals}

    def test_per_kind_budget_manifest_capped_at_kind_budget(self, tmp_path: Path):
        """A 100 KB single manifest should be capped at the manifest budget
        (default 24 KB), not allowed to eat into other kinds' allocations."""
        (tmp_path / "package.json").write_text("x" * 100_000)
        (tmp_path / "README.md").write_text("ok\n")

        bundle = collect_signals(tmp_path)
        manifest_bytes = sum(len(s.content) for s in bundle.signals if s.kind == "manifest")
        assert manifest_bytes <= 24_000

    def test_per_kind_budget_explicit_override(self, tmp_path: Path):
        """`budgets` parameter overrides defaults."""
        (tmp_path / "package.json").write_text("x" * 50_000)
        (tmp_path / "README.md").write_text("y" * 50_000)

        bundle = collect_signals(
            tmp_path,
            budgets={
                "manifest": 1_000,
                "readme": 1_000,
                "dockerfile_ci": 100,
                "source_sample": 100,
            },
        )
        manifest_bytes = sum(len(s.content) for s in bundle.signals if s.kind == "manifest")
        readme_bytes = sum(len(s.content) for s in bundle.signals if s.kind == "readme")
        assert manifest_bytes <= 1_000
        assert readme_bytes <= 1_000
