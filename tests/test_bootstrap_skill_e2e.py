"""End-to-end bootstrap checks using one isolated sample project per session.

Run with pytest tests/test_bootstrap_skill_e2e.py -v. Requires Python and bash.
"""

from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def run_bootstrap(bootstrap_artifact):
    """Return the session's completed real bootstrap run."""
    return lambda: bootstrap_artifact[0]


@pytest.fixture
def output_skill_dir(bootstrap_artifact):
    """Isolated output, never the developer's output/ directory."""
    return bootstrap_artifact[1]


@pytest.mark.e2e
class TestBootstrapSkillE2E:
    """End-to-end tests for bootstrap skill"""

    def test_bootstrap_creates_output_structure(self, run_bootstrap, output_skill_dir):
        """Verify bootstrap creates correct directory structure"""
        result = run_bootstrap()

        assert result.returncode == 0, f"Bootstrap failed: {result.stderr}"
        assert output_skill_dir.exists(), "Output directory not created"
        assert (output_skill_dir / "SKILL.md").exists(), "SKILL.md not created"
        assert (output_skill_dir / "SKILL.md").stat().st_size > 0, "SKILL.md is empty"

    def test_bootstrap_prepends_header(self, run_bootstrap, output_skill_dir):
        """Verify header template prepended to SKILL.md"""
        result = run_bootstrap()
        assert result.returncode == 0

        content = (output_skill_dir / "SKILL.md").read_text()

        # Check header sections present
        assert "## Prerequisites" in content, "Missing Prerequisites section"
        assert "pip install skill-seekers" in content, "Missing install instruction"
        assert "## Commands" in content, "Missing Commands section"

    def test_bootstrap_validates_yaml_frontmatter(self, run_bootstrap, output_skill_dir):
        """Verify generated SKILL.md has valid YAML frontmatter"""
        result = run_bootstrap()
        assert result.returncode == 0

        content = (output_skill_dir / "SKILL.md").read_text()

        # Check frontmatter structure
        assert content.startswith("---"), "Missing frontmatter start"

        # Find closing delimiter
        lines = content.split("\n")
        closing_found = False
        for _i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                closing_found = True
                break

        assert closing_found, "Missing frontmatter closing delimiter"

        # Check required fields
        assert "name:" in content[:500], "Missing name field"
        assert "description:" in content[:500], "Missing description field"

    def test_bootstrap_output_line_count(self, run_bootstrap, output_skill_dir):
        """Verify output SKILL.md has reasonable line count"""
        result = run_bootstrap()
        assert result.returncode == 0

        line_count = len((output_skill_dir / "SKILL.md").read_text().splitlines())

        # Should be substantial (header ~44 + auto-generated ~200+)
        assert line_count > 100, f"SKILL.md too short: {line_count} lines"
        assert line_count < 2000, f"SKILL.md suspiciously long: {line_count} lines"

    def test_skill_installable_to_claude(self, output_skill_dir, tmp_path, monkeypatch):
        """A generated skill is installed as files, not as a Python package."""
        from skill_seekers.web.installer import install_skill_to_cli

        monkeypatch.setenv("HOME", str(tmp_path))
        import skill_seekers.web.paths as paths

        monkeypatch.setattr(paths, "UI_STATE_DIR", tmp_path / "ui-state")
        monkeypatch.setattr(paths, "TRASH_DIR", tmp_path / "trash")
        monkeypatch.setattr(paths, "MARKET_CACHE_DIR", tmp_path / "market")
        installed = install_skill_to_cli(output_skill_dir, "claude")
        assert (installed / "SKILL.md").read_bytes() == (output_skill_dir / "SKILL.md").read_bytes()
        assert (installed / "references").is_dir()

    def test_skill_packageable_with_adaptors(self, run_bootstrap, output_skill_dir, tmp_path):
        """Verify bootstrap output works with all platform adaptors"""
        result = run_bootstrap()
        assert result.returncode == 0

        # Try to package with claude adaptor (simplest)
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor("claude")

        # Should be able to package without errors
        try:
            package_path = adaptor.package(
                skill_dir=output_skill_dir,  # Path object, not str
                output_path=tmp_path,  # Path object, not str
            )

            assert Path(package_path).exists(), "Package not created"
            assert Path(package_path).stat().st_size > 0, "Package is empty"
        except Exception as e:
            pytest.fail(f"Packaging failed: {e}")
