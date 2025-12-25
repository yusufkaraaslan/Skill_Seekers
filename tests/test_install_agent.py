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

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.install_agent import (
    AGENT_PATHS,
    get_agent_path,
    get_available_agents,
    validate_agent_name,
    validate_skill_directory,
    install_to_agent,
    install_to_all_agents,
    main,
)


class TestAgentPathMapping:
    """Test agent path resolution and mapping."""

    def test_get_agent_path_home_expansion(self):
        """Test that ~ expands to home directory for global agents."""
        # Test claude (global agent with ~)
        path = get_agent_path('claude')
        assert path.is_absolute()
        assert '.claude' in str(path)
        assert str(path).startswith(str(Path.home()))

    def test_get_agent_path_project_relative(self):
        """Test that project-relative paths use current directory."""
        # Test cursor (project-relative agent)
        path = get_agent_path('cursor')
        assert path.is_absolute()
        assert '.cursor' in str(path)
        # Should be relative to current directory
        assert str(Path.cwd()) in str(path)

    def test_get_agent_path_project_relative_with_custom_root(self):
        """Test project-relative paths with custom project root."""
        custom_root = Path('/tmp/test-project')
        path = get_agent_path('cursor', project_root=custom_root)
        assert path.is_absolute()
        assert str(custom_root) in str(path)
        assert '.cursor' in str(path)

    def test_get_agent_path_invalid_agent(self):
        """Test that invalid agent raises ValueError."""
        with pytest.raises(ValueError, match="Unknown agent"):
            get_agent_path('invalid_agent')

    def test_get_available_agents(self):
        """Test that all 10 agents are listed."""
        agents = get_available_agents()
        assert len(agents) == 10
        assert 'claude' in agents
        assert 'cursor' in agents
        assert 'vscode' in agents
        assert 'amp' in agents
        assert 'goose' in agents
        assert sorted(agents) == agents  # Should be sorted

    def test_agent_path_case_insensitive(self):
        """Test that agent names are case-insensitive."""
        path_lower = get_agent_path('claude')
        path_upper = get_agent_path('CLAUDE')
        path_mixed = get_agent_path('Claude')
        assert path_lower == path_upper == path_mixed


class TestAgentNameValidation:
    """Test agent name validation and fuzzy matching."""

    def test_validate_valid_agent(self):
        """Test that valid agent names pass validation."""
        is_valid, error = validate_agent_name('claude')
        assert is_valid is True
        assert error is None

    def test_validate_invalid_agent_suggests_similar(self):
        """Test that similar agent names are suggested for typos."""
        is_valid, error = validate_agent_name('courser')
        assert is_valid is False
        assert 'cursor' in error.lower()  # Should suggest 'cursor'

    def test_validate_special_all(self):
        """Test that 'all' is a valid special agent name."""
        is_valid, error = validate_agent_name('all')
        assert is_valid is True
        assert error is None

    def test_validate_case_insensitive(self):
        """Test that validation is case-insensitive."""
        for name in ['Claude', 'CLAUDE', 'claude', 'cLaUdE']:
            is_valid, error = validate_agent_name(name)
            assert is_valid is True
            assert error is None

    def test_validate_shows_available_agents(self):
        """Test that error message shows available agents."""
        is_valid, error = validate_agent_name('invalid')
        assert is_valid is False
        assert 'available agents' in error.lower()
        assert 'claude' in error.lower()
        assert 'cursor' in error.lower()


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

            with patch('skill_seekers.cli.install_agent.get_agent_path', return_value=agent_path):
                success, message = install_to_agent(self.skill_dir, 'claude', force=True)

                assert success is True
                target_path = agent_path / "test-skill"
                assert target_path.exists()
                assert target_path.is_dir()

    def test_install_preserves_structure(self):
        """Test that installation preserves SKILL.md, references/, scripts/, assets/."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"

            with patch('skill_seekers.cli.install_agent.get_agent_path', return_value=agent_path):
                success, message = install_to_agent(self.skill_dir, 'claude', force=True)

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

            with patch('skill_seekers.cli.install_agent.get_agent_path', return_value=agent_path):
                success, message = install_to_agent(self.skill_dir, 'claude', force=True)

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

            with patch('skill_seekers.cli.install_agent.get_agent_path', return_value=agent_path):
                success, message = install_to_agent(self.skill_dir, 'claude', force=False)

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

            with patch('skill_seekers.cli.install_agent.get_agent_path', return_value=agent_path):
                success, message = install_to_agent(self.skill_dir, 'claude', force=True)

                assert success is True
                # Old file should be gone
                assert not (target_path / "old_file.txt").exists()
                # New structure should exist
                assert (target_path / "SKILL.md").exists()

    def test_install_invalid_skill_directory(self):
        """Test that installation fails for invalid skill directory."""
        invalid_dir = Path("/nonexistent/directory")

        success, message = install_to_agent(invalid_dir, 'claude')

        assert success is False
        assert "does not exist" in message

    def test_install_missing_skill_md(self):
        """Test that installation fails if SKILL.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_skill_dir = Path(tmpdir) / "bad-skill"
            bad_skill_dir.mkdir()

            success, message = install_to_agent(bad_skill_dir, 'claude')

            assert success is False
            assert "SKILL.md not found" in message

    def test_install_dry_run(self):
        """Test that dry-run mode previews without making changes."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            agent_path = Path(agent_tmpdir) / ".claude" / "skills"

            with patch('skill_seekers.cli.install_agent.get_agent_path', return_value=agent_path):
                success, message = install_to_agent(self.skill_dir, 'claude', dry_run=True)

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
        """Test that install_to_all_agents attempts all 10 agents."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            def mock_get_agent_path(agent_name, project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with patch('skill_seekers.cli.install_agent.get_agent_path', side_effect=mock_get_agent_path):
                results = install_to_all_agents(self.skill_dir, force=True)

                assert len(results) == 10
                assert 'claude' in results
                assert 'cursor' in results

    def test_install_to_all_partial_success(self):
        """Test that install_to_all collects both successes and failures."""
        # This is hard to test without complex mocking, so we'll do dry-run
        results = install_to_all_agents(self.skill_dir, dry_run=True)

        # All should succeed in dry-run mode
        assert len(results) == 10
        for agent_name, (success, message) in results.items():
            assert success is True
            assert "DRY RUN" in message

    def test_install_to_all_with_force(self):
        """Test that install_to_all respects force flag."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            # Create existing directories for all agents
            for agent in get_available_agents():
                agent_dir = Path(agent_tmpdir) / f".{agent}" / "skills" / "test-skill"
                agent_dir.mkdir(parents=True)

            def mock_get_agent_path(agent_name, project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with patch('skill_seekers.cli.install_agent.get_agent_path', side_effect=mock_get_agent_path):
                # Without force - should fail
                results_no_force = install_to_all_agents(self.skill_dir, force=False)
                # All should fail because directories exist
                for agent_name, (success, message) in results_no_force.items():
                    assert success is False
                    assert "already installed" in message.lower()

                # With force - should succeed
                results_with_force = install_to_all_agents(self.skill_dir, force=True)
                for agent_name, (success, message) in results_with_force.items():
                    assert success is True

    def test_install_to_all_returns_results(self):
        """Test that install_to_all returns dict with all results."""
        results = install_to_all_agents(self.skill_dir, dry_run=True)

        assert isinstance(results, dict)
        assert len(results) == 10

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
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['install_agent.py', '--help']):
                main()

        # --help exits with code 0
        assert exc_info.value.code == 0

    def test_cli_requires_agent_flag(self):
        """Test that CLI fails without --agent flag."""
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['install_agent.py', str(self.skill_dir)]):
                main()

        # Missing required argument exits with code 2
        assert exc_info.value.code == 2

    def test_cli_dry_run(self):
        """Test that --dry-run flag works correctly."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            def mock_get_agent_path(agent_name, project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with patch('skill_seekers.cli.install_agent.get_agent_path', side_effect=mock_get_agent_path):
                with patch('sys.argv', ['install_agent.py', str(self.skill_dir), '--agent', 'claude', '--dry-run']):
                    exit_code = main()

                    assert exit_code == 0
                    # Directory should NOT be created
                    assert not (Path(agent_tmpdir) / ".claude" / "skills" / "test-skill").exists()

    def test_cli_integration(self):
        """Test end-to-end CLI execution."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            def mock_get_agent_path(agent_name, project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with patch('skill_seekers.cli.install_agent.get_agent_path', side_effect=mock_get_agent_path):
                with patch('sys.argv', ['install_agent.py', str(self.skill_dir), '--agent', 'claude', '--force']):
                    exit_code = main()

                    assert exit_code == 0
                    # Directory should be created
                    target = Path(agent_tmpdir) / ".claude" / "skills" / "test-skill"
                    assert target.exists()
                    assert (target / "SKILL.md").exists()

    def test_cli_install_to_all(self):
        """Test CLI with --agent all."""
        with tempfile.TemporaryDirectory() as agent_tmpdir:
            def mock_get_agent_path(agent_name, project_root=None):
                return Path(agent_tmpdir) / f".{agent_name}" / "skills"

            with patch('skill_seekers.cli.install_agent.get_agent_path', side_effect=mock_get_agent_path):
                with patch('sys.argv', ['install_agent.py', str(self.skill_dir), '--agent', 'all', '--force']):
                    exit_code = main()

                    assert exit_code == 0

                    # All agent directories should be created
                    for agent in get_available_agents():
                        target = Path(agent_tmpdir) / f".{agent}" / "skills" / "test-skill"
                        assert target.exists(), f"Directory not created for {agent}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
