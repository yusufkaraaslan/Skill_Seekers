"""Tests for the bootstrap skill script."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


class TestBootstrapSkillScript:
    """Tests for scripts/bootstrap_skill.sh"""

    def test_script_exists(self, project_root):
        """Test that bootstrap script exists and is executable."""
        script = project_root / "scripts" / "bootstrap_skill.sh"
        assert script.exists(), "bootstrap_skill.sh should exist"
        assert script.stat().st_mode & 0o111, "bootstrap_skill.sh should be executable"

    def test_header_template_exists(self, project_root):
        """Test that skill header template exists."""
        header = project_root / "scripts" / "skill_header.md"
        assert header.exists(), "skill_header.md should exist"

    def test_header_has_required_sections(self, project_root):
        """Test that header template has required operational sections."""
        header = project_root / "scripts" / "skill_header.md"
        content = header.read_text()

        # Must have prerequisites
        assert "## Prerequisites" in content, "Header must have Prerequisites section"
        assert "pip install skill-seekers" in content, "Header must have pip install instruction"

        # Must have commands table
        assert "## Commands" in content, "Header must have Commands section"
        assert "skill-seekers analyze" in content, "Header must mention analyze command"
        assert "skill-seekers scrape" in content, "Header must mention scrape command"
        assert "skill-seekers github" in content, "Header must mention github command"

    def test_header_has_yaml_frontmatter(self, project_root):
        """Test that header has valid YAML frontmatter."""
        header = project_root / "scripts" / "skill_header.md"
        content = header.read_text()

        assert content.startswith("---"), "Header must start with YAML frontmatter"
        assert "name: skill-seekers" in content, "Header must have skill name"
        assert "description:" in content, "Header must have description"

    @pytest.mark.slow
    def test_bootstrap_script_runs(self, project_root):
        """Test that bootstrap script runs successfully.

        Note: This test is slow as it runs full codebase analysis.
        Run with: pytest -m slow
        """
        script = project_root / "scripts" / "bootstrap_skill.sh"

        # Run script (skip if uv not available)
        result = subprocess.run(
            ["bash", str(script)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        # Check script completed
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Check outputs exist (directory named 'skill-seekers' for Claude Code)
        output_dir = project_root / "output" / "skill-seekers"
        assert output_dir.exists(), "Output directory should be created"

        skill_md = output_dir / "SKILL.md"
        assert skill_md.exists(), "SKILL.md should be created"

        # Check SKILL.md has header prepended
        content = skill_md.read_text()
        assert "## Prerequisites" in content, "SKILL.md should have header prepended"
        assert "pip install skill-seekers" in content, "SKILL.md should have install instructions"
