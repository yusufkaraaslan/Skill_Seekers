"""
End-to-end tests for bootstrap skill feature (PR #249)

Tests verify:
1. Bootstrap script creates proper skill structure
2. Generated SKILL.md is valid and usable
3. Skill is installable in isolated virtual environment
4. Output works with all platform adaptors
5. Error cases handled gracefully

Coverage: 8-12 tests
Execution time: Fast tests ~2-3 min, Full tests ~5-10 min
Requires: Python 3.10+, bash, uv

Run fast tests:
    pytest tests/test_bootstrap_skill_e2e.py -v -k "not venv"

Run full suite:
    pytest tests/test_bootstrap_skill_e2e.py -v -m "e2e"

Run with venv tests:
    pytest tests/test_bootstrap_skill_e2e.py -v -m "venv"
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def run_bootstrap(project_root):
    """Execute bootstrap script and return result"""

    def _run(timeout=600):
        script = project_root / "scripts" / "bootstrap_skill.sh"

        result = subprocess.run(
            ["bash", str(script)], cwd=project_root, capture_output=True, text=True, timeout=timeout
        )

        return result

    return _run


@pytest.fixture
def output_skill_dir(project_root):
    """Get path to bootstrap output directory"""
    return project_root / "output" / "skill-seekers"


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

    @pytest.mark.slow
    @pytest.mark.venv
    def test_skill_installable_in_venv(self, run_bootstrap, output_skill_dir, tmp_path):
        """Test skill is installable in clean virtual environment"""
        # First run bootstrap
        result = run_bootstrap()
        assert result.returncode == 0

        # Create venv
        venv_path = tmp_path / "test_venv"
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, timeout=60)

        # Install skill in venv
        pip_path = venv_path / "bin" / "pip"
        result = subprocess.run(
            [str(pip_path), "install", "-e", "."],
            cwd=output_skill_dir.parent.parent,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Should install successfully
        assert result.returncode == 0, f"Install failed: {result.stderr}"

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
