"""
Tests for install_agent CLI tool.

Tests cover:
- Agent path mapping and resolution
- Agent name validation with fuzzy matching
- Skill directory validation
- Installation to single agent
- Installation to all agents
- CLI interface
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.install_agent import (
    get_agent_path,
    get_available_agents,
    get_skill_name,
    install_to_agent,
    install_to_all_agents,
    main,
    validate_agent_name,
    validate_skill_directory,
)


class TestAgentPathMapping:
    """Test agent path resolution and mapping."""

    def test_get_agent_path_home_expansion(self):
        """Test that ~ expands to home directory for global agents."""
        # Test claude (global agent with ~)
        path = get_agent_path("claude")
        assert path.is_absolute()
        assert ".claude" in str(path)
        assert str(path).startswith(str(Path.home()))

    def test_get_agent_path_project_relative(self):
        """Test that project-relative paths use current directory."""
        # Test cursor (project-relative agent)
        path = get_agent_path("cursor")
        assert path.is_absolute()
        assert ".cursor" in str(path)
        # Should be relative to current directory
        assert str(Path.cwd()) in str(path)

    def test_get_agent_path_project_relative_with_custom_root(self):
        """Test project-relative paths with custom project root."""
        custom_root = Path("/tmp/test-project")
        path = get_agent_path("cursor", project_root=custom_root)
        assert path.is_absolute()
        assert str(custom_root) in str(path)
        assert ".cursor" in str(path)

    def test_get_agent_path_invalid_agent(self):
        """Test that invalid agent raises ValueError."""
        with pytest.raises(ValueError, match="Unknown agent"):
            get_agent_path("invalid_agent")

    def test_get_available_agents(self):
        """Test that all 19 agents are listed."""
        agents = get_available_agents()
        assert len(agents) == 19
        assert "claude" in agents
        assert "cursor" in agents
        assert "vscode" in agents
        assert "amp" in agents
        assert "goose" in agents
        assert "neovate" in agents
        assert "roo" in agents
        assert "cline" in agents
        assert "aider" in agents
        assert "bolt" in agents
        assert "kilo" in agents
        assert "continue" in agents
        assert "kimi-code" in agents
        assert "bob" in agents
        assert sorted(agents) == agents  # Should be sorted

    def test_new_agents_project_relative(self):
        """Test that project-relative new agents resolve correctly."""
        for agent in ["roo", "cline", "bolt", "kilo"]:
            path = get_agent_path(agent)
            assert path.is_absolute()
            assert str(Path.cwd()) in str(path)

    def test_new_agents_global(self):
        """Test that global new agents resolve to home directory."""
        for agent in ["aider", "continue", "kimi-code"]:
            path = get_agent_path(agent)
            assert path.is_absolute()
            assert str(path).startswith(str(Path.home()))

    def test_agent_path_case_insensitive(self):
        """Test that agent names are case-insensitive."""
        path_lower = get_agent_path("claude")
        path_upper = get_agent_path("CLAUDE")
        path_mixed = get_agent_path("Claude")
        assert path_lower == path_upper == path_mixed


class TestAgentNameValidation:
    """Test agent name validation and fuzzy matching."""

    def test_validate_valid_agent(self):
        """Test that valid agent names pass validation."""
        is_valid, error = validate_agent_name("claude")
        assert is_valid is True
        assert error is None

    def test_validate_invalid_agent_suggests_similar(self):
        """Test that similar agent names are suggested for typos."""
        is_valid, error = validate_agent_name("courser")
        assert is_valid is False
        assert "cursor" in error.lower()  # Should suggest 'cursor'

    def test_validate_special_all(self):
        """Test that 'all' is a valid special agent name."""
        is_valid, error = validate_agent_name("all")
        assert is_valid is True
        assert error is None

    def test_validate_case_insensitive(self):
        """Test that validation is case-insensitive."""
        for name in ["Claude", "CLAUDE", "claude", "cLaUdE"]:
            is_valid, error = validate_agent_name(name)
            assert is_valid is True
            assert error is None

    def test_validate_shows_available_agents(self):
        """Test that error message shows available agents."""
        is_valid, error = validate_agent_name("invalid")
        assert is_valid is False
        assert "available agents" in error.lower()
        assert "claude" in error.lower()
        assert "cursor" in error.lower()


class TestSkillDirectoryValidation:
    """Test skill directory validation."""

    def test_validate_valid_skill_directory(self):
        """Test that valid skill directory passes validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test Skill")

            is_valid, error = validate_skill_directory(skill_dir)
            assert is_valid is True
            assert error is None

    def test_validate_missing_directory(self):
        """Test that missing directory fails validation."""
        skill_dir = Path("/nonexistent/directory")
        is_valid, error = validate_skill_directory(skill_dir)
        assert is_valid is False
        assert "does not exist" in error

    def test_validate_not_a_directory(self):
        """Test that file (not directory) fails validation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            try:
                is_valid, error = validate_skill_directory(Path(tmpfile.name))
                assert is_valid is False
                assert "not a directory" in error
            finally:
                Path(tmpfile.name).unlink()

    def test_validate_missing_skill_md(self):
        """Test that directory without SKILL.md fails validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()

            is_valid, error = validate_skill_directory(skill_dir)
            assert is_valid is False
            assert "SKILL.md not found" in error


class TestInstallToAgent:
    """Test installation to single agent."""

    def setup_method(self):
        """Create test skill directory before each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.skill_dir = Path(self.tmpdir) / "test-skill"
        self.skill_dir.mkdir()

        # Create SKILL.md
        (self.skill_dir / "SKILL.md").write_text("# Test Skill\n\nThis is a test skill.")

        # Create references directory with files
        refs_dir = self.skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "index.md").write_text("# Index")
        (refs_dir / "getting_started.md").write_text("# Getting Started")

        # Create empty directories
        (self.skill_dir / "scripts").mkdir()
        (self.skill_dir / "assets").mkdir()

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_install_creates_skill_subdirectory(self):
        """Test that installation creates {agent_path}/{skill_name}/ directory."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                return_value=agent_path,
            ):
                success, message = install_to_agent(self.skill_dir, "claude", force=True)

                assert success is True
                target_path = agent_path / "test-skill"
                assert target_path.exists()
                assert target_path.is_dir()

    def test_install_preserves_structure(self):
        """Test that installation preserves SKILL.md, references/, scripts/, assets/."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                return_value=agent_path,
            ):
                success, message = install_to_agent(self.skill_dir, "claude", force=True)

                assert success is True
                target_path = agent_path / "test-skill"

                # Check structure
                assert (target_path / "SKILL.md").exists()
                assert (target_path / "references").exists()
                assert (target_path / "references" / "index.md").exists()
                assert (target_path / "references" / "getting_started.md").exists()
                assert (target_path / "scripts").exists()
                assert (target_path / "assets").exists()

    def test_install_excludes_backups(self):
        """Test that .backup files are excluded from installation."""
        # Create backup file
        (self.skill_dir / "SKILL.md.backup").write_text("# Backup")

        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                return_value=agent_path,
            ):
                success, message = install_to_agent(self.skill_dir, "claude", force=True)

                assert success is True
                target_path = agent_path / "test-skill"

                # Backup should NOT be copied
                assert not (target_path / "SKILL.md.backup").exists()
                # Main file should be copied
                assert (target_path / "SKILL.md").exists()

    def test_install_existing_directory_no_force(self):
        """Test that existing directory without --force fails with clear message."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"
            target_path = agent_path / "test-skill"
            target_path.mkdir(parents=True)

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                return_value=agent_path,
            ):
                success, message = install_to_agent(self.skill_dir, "claude", force=False)

                assert success is False
                assert "already installed" in message.lower()
                assert "--force" in message

    def test_install_existing_directory_with_force(self):
        """Test that existing directory with --force overwrites successfully."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"
            target_path = agent_path / "test-skill"
            target_path.mkdir(parents=True)
            (target_path / "old_file.txt").write_text("old content")

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                return_value=agent_path,
            ):
                success, message = install_to_agent(self.skill_dir, "claude", force=True)

                assert success is True
                # Old file should be gone
                assert not (target_path / "old_file.txt").exists()
                # New structure should exist
                assert (target_path / "SKILL.md").exists()

    def test_install_invalid_skill_directory(self):
        """Test that installation fails for invalid skill directory."""
        invalid_dir = Path("/nonexistent/directory")

        success, message = install_to_agent(invalid_dir, "claude")

        assert success is False
        assert "does not exist" in message

    def test_install_missing_skill_md(self):
        """Test that installation fails if SKILL.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_skill_dir = Path(tmpdir) / "bad-skill"
            bad_skill_dir.mkdir()

            success, message = install_to_agent(bad_skill_dir, "claude")

            assert success is False
            assert "SKILL.md not found" in message

    def test_install_dry_run(self):
        """Test that dry-run mode previews without making changes."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                return_value=agent_path,
            ):
                success, message = install_to_agent(self.skill_dir, "claude", dry_run=True)

                assert success is True
                assert "DRY RUN" in message
                # Directory should NOT be created
                assert not (agent_path / "test-skill").exists()


class TestInstallToAllAgents:
    """Test installation to all agents."""

    def setup_method(self):
        """Create test skill directory before each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.skill_dir = Path(self.tmpdir) / "test-skill"
        self.skill_dir.mkdir()
        (self.skill_dir / "SKILL.md").write_text("# Test Skill")
        (self.skill_dir / "references").mkdir()

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_install_to_all_success(self):
        """Test that install_to_all_agents attempts all 19 agents."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:

            def mock_get_agent_path(agent_name, _project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                side_effect=mock_get_agent_path,
            ):
                results = install_to_all_agents(self.skill_dir, force=True)

                assert len(results) == 19
                assert "claude" in results
                assert "cursor" in results
                assert "bob" in results

    def test_install_to_all_partial_success(self):
        """Test that install_to_all collects both successes and failures."""
        # This is hard to test without complex mocking, so we'll do dry-run
        results = install_to_all_agents(self.skill_dir, dry_run=True)

        # All should succeed in dry-run mode
        assert len(results) == 19
        for _agent_name, (success, message) in results.items():
            assert success is True
            assert "DRY RUN" in message

    def test_install_to_all_with_force(self):
        """Test that install_to_all respects force flag."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            # Create existing directories for all agents
            for agent in get_available_agents():
                agent_dir = Path(agent_tmpdir) / f".{agent}" / "skills" / "test-skill"
                agent_dir.mkdir(parents=True)

            def mock_get_agent_path(agent_name, _project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with patch(
                "skill_seekers.cli.install_agent.get_agent_path",
                side_effect=mock_get_agent_path,
            ):
                # Without force - should fail
                results_no_force = install_to_all_agents(self.skill_dir, force=False)
                # All should fail because directories exist
                for _agent_name, (success, message) in results_no_force.items():
                    assert success is False
                    assert "already installed" in message.lower()

                # With force - should succeed
                results_with_force = install_to_all_agents(self.skill_dir, force=True)
                for _agent_name, (success, _message) in results_with_force.items():
                    assert success is True

    def test_install_to_all_returns_results(self):
        """Test that install_to_all returns dict with all results."""
        results = install_to_all_agents(self.skill_dir, dry_run=True)

        assert isinstance(results, dict)
        assert len(results) == 19

        for agent_name, (success, message) in results.items():
            assert isinstance(success, bool)
            assert isinstance(message, str)
            assert agent_name in get_available_agents()


class TestInstallAgentCLI:
    """Test CLI interface."""

    def setup_method(self):
        """Create test skill directory before each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.skill_dir = Path(self.tmpdir) / "test-skill"
        self.skill_dir.mkdir()
        (self.skill_dir / "SKILL.md").write_text("# Test Skill")
        (self.skill_dir / "references").mkdir()

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cli_help_output(self):
        """Test that --help shows usage information."""
        with (
            pytest.raises(SystemExit) as exc_info,
            patch("sys.argv", ["install_agent.py", "--help"]),
        ):
            main()

        # --help exits with code 0
        assert exc_info.value.code == 0

    def test_cli_requires_agent_flag(self):
        """Test that CLI fails without --agent flag."""
        with (
            pytest.raises(SystemExit) as exc_info,
            patch("sys.argv", ["install_agent.py", str(self.skill_dir)]),
        ):
            main()

        # Missing required argument exits with code 2
        assert exc_info.value.code == 2

    def test_cli_dry_run(self):
        """Test that --dry-run flag works correctly."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:

            def mock_get_agent_path(agent_name, _project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with (
                patch(
                    "skill_seekers.cli.install_agent.get_agent_path",
                    side_effect=mock_get_agent_path,
                ),
                patch(
                    "sys.argv",
                    [
                        "install_agent.py",
                        str(self.skill_dir),
                        "--agent",
                        "claude",
                        "--dry-run",
                    ],
                ),
            ):
                exit_code = main()

                assert exit_code == 0
                # Directory should NOT be created
                assert not (Path(agent_tmpdir) / ".claude" / "skills" / "test-skill").exists()

    def test_cli_integration(self):
        """Test end-to-end CLI execution."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:

            def mock_get_agent_path(agent_name, _project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with (
                patch(
                    "skill_seekers.cli.install_agent.get_agent_path",
                    side_effect=mock_get_agent_path,
                ),
                patch(
                    "sys.argv",
                    [
                        "install_agent.py",
                        str(self.skill_dir),
                        "--agent",
                        "claude",
                        "--force",
                    ],
                ),
            ):
                exit_code = main()

                assert exit_code == 0
                # Directory should be created
                target = Path(agent_tmpdir) / ".claude" / "skills" / "test-skill"
                assert target.exists()
                assert (target / "SKILL.md").exists()

    def test_cli_install_to_all(self):
        """Test CLI with --agent all."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:

            def mock_get_agent_path(agent_name, _project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with (
                patch(
                    "skill_seekers.cli.install_agent.get_agent_path",
                    side_effect=mock_get_agent_path,
                ),
                patch(
                    "sys.argv",
                    [
                        "install_agent.py",
                        str(self.skill_dir),
                        "--agent",
                        "all",
                        "--force",
                    ],
                ),
            ):
                exit_code = main()

                assert exit_code == 0

                # All agent directories should be created
                for agent in get_available_agents():
                    target = Path(agent_tmpdir) / f".{agent}" / "skills" / "test-skill"
                    assert target.exists(), f"Directory not created for {agent}"


class TestFrontmatterNamePreference:
    """Installed dir must match SKILL.md frontmatter name, not the source
    directory name — package_skill suffixes local-target dirs with the
    platform name (e.g. "demo-opencode"), breaking the OpenCode/Claude
    name==directory requirement."""

    def _make_skill(self, tmp_path, dir_name, frontmatter_name):
        d = tmp_path / dir_name
        d.mkdir()
        fm = f"---\nname: {frontmatter_name}\ndescription: test skill\n---\n\n# Test\n"
        (d / "SKILL.md").write_text(fm, encoding="utf-8")
        return d

    def test_frontmatter_name_wins(self, tmp_path):
        d = self._make_skill(tmp_path, "demo-opencode", "demo")
        assert get_skill_name(d) == "demo"

    def test_falls_back_to_dir_name(self, tmp_path):
        d = tmp_path / "plain-dir"
        d.mkdir()
        (d / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
        assert get_skill_name(d) == "plain-dir"

    def test_install_uses_frontmatter_name(self, tmp_path, monkeypatch):
        d = self._make_skill(tmp_path, "demo-opencode", "demo")
        monkeypatch.chdir(tmp_path)  # cursor installs to ./.cursor/skills/
        success, message = install_to_agent(d, "cursor", force=True)
        assert success, message
        installed = tmp_path / ".cursor" / "skills" / "demo"
        assert (installed / "SKILL.md").exists()
        assert not (tmp_path / ".cursor" / "skills" / "demo-opencode").exists()

    def test_quoted_frontmatter_name(self, tmp_path):
        d = tmp_path / "q-dir"
        d.mkdir()
        (d / "SKILL.md").write_text(
            '---\nname: "quoted-name"\ndescription: x\n---\n', encoding="utf-8"
        )
        assert get_skill_name(d) == "quoted-name"


@pytest.mark.parametrize(
    ("frontmatter", "expected"),
    [
        ("name: demo # comment", "demo"),
        ("name: 'demo-name'", "demo-name"),
        ('name: "demo name"', "demo name"),
        ('name: "demo#name"', "demo#name"),
        ('name: "\\u0064emo"', "demo"),
        ("name: >-\n  demo", "demo"),
        ("name: |-\n  demo\n  ---", "fallback"),
        ("metadata:\n  name: nested\nname: actual", "actual"),
        ("name:\ndescription: test", "fallback"),
        ("name: null", "fallback"),
        ("name: false", "fallback"),
        ("name: 123", "fallback"),
        ("name: [demo]", "fallback"),
        ("name: {nested: demo}", "fallback"),
        ('name: ""', "fallback"),
        ('name: "   "', "fallback"),
        ('name: "unterminated', "fallback"),
        ("name: [invalid", "fallback"),
        ("- name: demo", "fallback"),
        ("metadata:\n  name: nested", "fallback"),
        ("name: ../outside", "fallback"),
        ("name: /tmp/outside", "fallback"),
        ("name: ..\\outside", "fallback"),
        ("name: C:\\outside", "fallback"),
        ("name: C:outside", "fallback"),
        ("name: .", "fallback"),
        ("name: ..", "fallback"),
        ('name: "demo\\0name"', "fallback"),
    ],
)
def test_frontmatter_yaml_and_safe_names(tmp_path, frontmatter, expected):
    """Parse complete YAML values; paths and invalid metadata use the folder name."""
    source = tmp_path / "fallback"
    source.mkdir()
    (source / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n# Skill\n", encoding="utf-8")
    assert get_skill_name(source) == expected


@pytest.mark.parametrize(
    "text",
    ["# Skill\nname: body", "---not-frontmatter\nname: body\n---", "---\nname: demo\n"],
)
def test_name_requires_complete_frontmatter(tmp_path, text):
    (tmp_path / "SKILL.md").write_text(text, encoding="utf-8")
    assert get_skill_name(tmp_path) == tmp_path.name


def test_frontmatter_bom_and_crlf(tmp_path):
    (tmp_path / "SKILL.md").write_bytes(b"\xef\xbb\xbf---\r\nname: demo\r\n---\r\n")
    assert get_skill_name(tmp_path) == "demo"


@pytest.mark.parametrize("name", ["../outside", "/absolute", "..\\outside", ".", ".."])
def test_force_cannot_escape_agent_directory(tmp_path, monkeypatch, name):
    source = tmp_path / "source"
    source.mkdir()
    sentinel = tmp_path / "outside" / "keep.txt"
    sentinel.parent.mkdir()
    sentinel.write_text("keep", encoding="utf-8")
    if name == "/absolute":
        name = str(sentinel.parent)
    (source / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    agent_dir = tmp_path / "skills"
    monkeypatch.setattr("skill_seekers.cli.install_agent.get_agent_path", lambda _: agent_dir)
    success, message = install_to_agent(source, "cursor", force=True)
    assert success, message
    assert (agent_dir / "source" / "SKILL.md").read_bytes() == (source / "SKILL.md").read_bytes()
    assert sentinel.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("relationship", ["same", "source-inside-target", "target-inside-source"])
def test_force_refuses_overlapping_source_and_target(tmp_path, monkeypatch, relationship):
    source = tmp_path / "demo"
    if relationship == "source-inside-target":
        source = source / "packaged"
    source.mkdir(parents=True)
    skill_md = source / "SKILL.md"
    skill_md.write_text("---\nname: demo\n---\n# Keep me\n", encoding="utf-8")
    agent_dir = source / "skills" if relationship == "target-inside-source" else tmp_path
    monkeypatch.setattr("skill_seekers.cli.install_agent.get_agent_path", lambda _: agent_dir)
    success, message = install_to_agent(source, "cursor", force=True)
    assert not success
    assert "overlap" in message
    assert skill_md.read_text(encoding="utf-8").endswith("# Keep me\n")
    assert not (source / "skills").exists()


def test_force_refuses_symlink_destination(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep", encoding="utf-8")
    agent_dir = tmp_path / "skills"
    agent_dir.mkdir()
    try:
        (agent_dir / "demo").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks unavailable")
    monkeypatch.setattr("skill_seekers.cli.install_agent.get_agent_path", lambda _: agent_dir)
    success, message = install_to_agent(source, "cursor", force=True)
    assert not success
    assert "Unsafe installation destination" in message
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("agent", ["cursor", "all"])
def test_cli_reports_frontmatter_destination(tmp_path, monkeypatch, capsys, agent):
    from argparse import Namespace

    source = tmp_path / "demo-opencode"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
    monkeypatch.setattr(
        "skill_seekers.cli.install_agent.get_agent_path", lambda name: tmp_path / name / "skills"
    )
    result = main(Namespace(skill_directory=str(source), agent=agent, force=False, dry_run=False))
    assert result == 0
    output = capsys.readouterr().out
    assert str(tmp_path / "cursor" / "skills" / "demo") in output
    assert "skills/demo-opencode" not in output
    assert "Installing skill: demo-opencode" not in output
    assert "Installing skill to all agents: demo-opencode" not in output


def test_opencode_package_install_and_collision(tmp_path, monkeypatch):
    from skill_seekers.cli.adaptors.opencode import OpenCodeAdaptor

    source = tmp_path / "demo"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: demo\n---\n# Demo\n", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    packaged = OpenCodeAdaptor().package(source, output)
    assert packaged.name == "demo-opencode"
    agent_dir = tmp_path / "skills"
    monkeypatch.setattr("skill_seekers.cli.install_agent.get_agent_path", lambda _: agent_dir)
    success, message = install_to_agent(packaged, "opencode", dry_run=True)
    assert success, message
    assert str(agent_dir / "demo") in message
    assert not agent_dir.exists()
    success, message = install_to_agent(packaged, "opencode")
    assert success, message
    installed_md = agent_dir / "demo" / "SKILL.md"
    assert installed_md.read_bytes() == (source / "SKILL.md").read_bytes()
    installed_md.write_text("existing", encoding="utf-8")
    success, message = install_to_agent(packaged, "opencode")
    assert not success
    assert "already installed" in message
    assert "SKILL.md frontmatter" in message
    assert installed_md.read_text(encoding="utf-8") == "existing"
    success, message = install_to_agent(packaged, "opencode", force=True)
    assert success, message
    assert installed_md.read_bytes() == (source / "SKILL.md").read_bytes()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
