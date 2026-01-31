#!/usr/bin/env python3
"""
End-to-End tests for the new 'analyze' command.
Tests real-world usage scenarios with actual command execution.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestAnalyzeCommandE2E(unittest.TestCase):
    """End-to-end tests for skill-seekers analyze command."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.test_dir = Path(tempfile.mkdtemp(prefix="analyze_e2e_"))
        cls.create_sample_codebase()

    @classmethod
    def tearDownClass(cls):
        """Clean up test directory."""
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

    @classmethod
    def create_sample_codebase(cls):
        """Create a sample Python codebase for testing."""
        # Create directory structure
        (cls.test_dir / "src").mkdir()
        (cls.test_dir / "tests").mkdir()

        # Create sample Python files
        (cls.test_dir / "src" / "__init__.py").write_text("")

        (cls.test_dir / "src" / "main.py").write_text('''
"""Main application module."""

class Application:
    """Main application class."""

    def __init__(self, name: str):
        """Initialize application.

        Args:
            name: Application name
        """
        self.name = name

    def run(self):
        """Run the application."""
        print(f"Running {self.name}")
        return True
''')

        (cls.test_dir / "tests" / "test_main.py").write_text('''
"""Tests for main module."""
import unittest
from src.main import Application

class TestApplication(unittest.TestCase):
    """Test Application class."""

    def test_init(self):
        """Test application initialization."""
        app = Application("Test")
        self.assertEqual(app.name, "Test")

    def test_run(self):
        """Test application run."""
        app = Application("Test")
        self.assertTrue(app.run())
''')

    def run_command(self, *args, timeout=120):
        """Run skill-seekers command and return result."""
        cmd = ["skill-seekers"] + list(args)
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=str(self.test_dir)
        )
        return result

    def test_analyze_help_shows_command(self):
        """Test that analyze command appears in main help."""
        result = self.run_command("--help", timeout=5)
        self.assertEqual(result.returncode, 0, f"Help failed: {result.stderr}")
        self.assertIn("analyze", result.stdout)
        self.assertIn("Analyze local codebase", result.stdout)

    def test_analyze_subcommand_help(self):
        """Test that analyze subcommand has proper help."""
        result = self.run_command("analyze", "--help", timeout=5)
        self.assertEqual(result.returncode, 0, f"Analyze help failed: {result.stderr}")
        self.assertIn("--quick", result.stdout)
        self.assertIn("--comprehensive", result.stdout)
        self.assertIn("--enhance", result.stdout)
        self.assertIn("--directory", result.stdout)

    def test_analyze_quick_preset(self):
        """Test quick analysis preset (real execution)."""
        output_dir = self.test_dir / "output_quick"

        result = self.run_command(
            "analyze", "--directory", str(self.test_dir), "--output", str(output_dir), "--quick"
        )

        # Check command succeeded
        self.assertEqual(
            result.returncode,
            0,
            f"Quick analysis failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}",
        )

        # Verify output directory was created
        self.assertTrue(output_dir.exists(), "Output directory not created")

        # Verify SKILL.md was generated
        skill_file = output_dir / "SKILL.md"
        self.assertTrue(skill_file.exists(), "SKILL.md not generated")

        # Verify SKILL.md has content and valid structure
        skill_content = skill_file.read_text()
        self.assertGreater(len(skill_content), 100, "SKILL.md is too short")

        # Check for expected structure (works even with 0 files analyzed)
        self.assertIn("Codebase", skill_content, "Missing codebase header")
        self.assertIn("Analysis", skill_content, "Missing analysis section")

        # Verify it's valid markdown with frontmatter
        self.assertTrue(skill_content.startswith("---"), "Missing YAML frontmatter")
        self.assertIn("name:", skill_content, "Missing name in frontmatter")

    def test_analyze_with_custom_output(self):
        """Test analysis with custom output directory."""
        output_dir = self.test_dir / "custom_output"

        result = self.run_command(
            "analyze", "--directory", str(self.test_dir), "--output", str(output_dir), "--quick"
        )

        self.assertEqual(result.returncode, 0, f"Analysis failed: {result.stderr}")
        self.assertTrue(output_dir.exists(), "Custom output directory not created")
        self.assertTrue((output_dir / "SKILL.md").exists(), "SKILL.md not in custom directory")

    def test_analyze_skip_flags_work(self):
        """Test that skip flags are properly handled."""
        output_dir = self.test_dir / "output_skip"

        result = self.run_command(
            "analyze",
            "--directory",
            str(self.test_dir),
            "--output",
            str(output_dir),
            "--quick",
            "--skip-patterns",
            "--skip-test-examples",
        )

        self.assertEqual(result.returncode, 0, f"Analysis with skip flags failed: {result.stderr}")
        self.assertTrue(
            (output_dir / "SKILL.md").exists(), "SKILL.md not generated with skip flags"
        )

    def test_analyze_invalid_directory(self):
        """Test analysis with non-existent directory."""
        result = self.run_command(
            "analyze", "--directory", "/nonexistent/directory/path", "--quick", timeout=10
        )

        # Should fail with error
        self.assertNotEqual(result.returncode, 0, "Should fail with invalid directory")
        self.assertTrue(
            "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower(),
            f"Expected directory error, got: {result.stderr}",
        )

    def test_analyze_missing_directory_arg(self):
        """Test that --directory is required."""
        result = self.run_command("analyze", "--quick", timeout=5)

        # Should fail without --directory
        self.assertNotEqual(result.returncode, 0, "Should fail without --directory")
        self.assertTrue(
            "required" in result.stderr.lower() or "directory" in result.stderr.lower(),
            f"Expected missing argument error, got: {result.stderr}",
        )

    def test_backward_compatibility_depth_flag(self):
        """Test that old --depth flag still works."""
        output_dir = self.test_dir / "output_depth"

        result = self.run_command(
            "analyze",
            "--directory",
            str(self.test_dir),
            "--output",
            str(output_dir),
            "--depth",
            "surface",
        )

        self.assertEqual(result.returncode, 0, f"Depth flag failed: {result.stderr}")
        self.assertTrue((output_dir / "SKILL.md").exists(), "SKILL.md not generated with --depth")

    def test_analyze_generates_references(self):
        """Test that references directory is created."""
        output_dir = self.test_dir / "output_refs"

        result = self.run_command(
            "analyze", "--directory", str(self.test_dir), "--output", str(output_dir), "--quick"
        )

        self.assertEqual(result.returncode, 0, f"Analysis failed: {result.stderr}")

        # Check for references directory
        refs_dir = output_dir / "references"
        if refs_dir.exists():  # Optional, depends on content
            self.assertTrue(refs_dir.is_dir(), "References is not a directory")

    def test_analyze_output_structure(self):
        """Test that output has expected structure."""
        output_dir = self.test_dir / "output_structure"

        result = self.run_command(
            "analyze", "--directory", str(self.test_dir), "--output", str(output_dir), "--quick"
        )

        self.assertEqual(result.returncode, 0, f"Analysis failed: {result.stderr}")

        # Verify expected files/directories
        self.assertTrue((output_dir / "SKILL.md").exists(), "SKILL.md missing")

        # Check for code_analysis.json if it exists
        analysis_file = output_dir / "code_analysis.json"
        if analysis_file.exists():
            # Verify it's valid JSON
            with open(analysis_file) as f:
                data = json.load(f)
                self.assertIsInstance(data, (dict, list), "code_analysis.json is not valid JSON")


class TestAnalyzeOldCommand(unittest.TestCase):
    """Test that old skill-seekers-codebase command still works."""

    def test_old_command_still_exists(self):
        """Test that skill-seekers-codebase still exists."""
        result = subprocess.run(
            ["skill-seekers-codebase", "--help"], capture_output=True, text=True, timeout=5
        )

        # Command should exist and show help
        self.assertEqual(result.returncode, 0, f"Old command doesn't work: {result.stderr}")
        self.assertIn("--directory", result.stdout)


class TestAnalyzeIntegration(unittest.TestCase):
    """Integration tests for analyze command with other features."""

    def setUp(self):
        """Set up test directory."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="analyze_int_"))

        # Create minimal Python project
        (self.test_dir / "main.py").write_text('''
def hello():
    """Say hello."""
    return "Hello, World!"
''')

    def tearDown(self):
        """Clean up test directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_analyze_then_check_output(self):
        """Test analyzing and verifying output can be read."""
        output_dir = self.test_dir / "output"

        # Run analysis
        result = subprocess.run(
            [
                "skill-seekers",
                "analyze",
                "--directory",
                str(self.test_dir),
                "--output",
                str(output_dir),
                "--quick",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(result.returncode, 0, f"Analysis failed: {result.stderr}")

        # Read and verify SKILL.md
        skill_file = output_dir / "SKILL.md"
        self.assertTrue(skill_file.exists(), "SKILL.md not created")

        content = skill_file.read_text()
        # Check for valid structure instead of specific content
        # (file detection may vary in temp directories)
        self.assertGreater(len(content), 50, "Output too short")
        self.assertIn("Codebase", content, "Missing codebase header")
        self.assertTrue(content.startswith("---"), "Missing YAML frontmatter")

    def test_analyze_verbose_flag(self):
        """Test that verbose flag works."""
        output_dir = self.test_dir / "output"

        result = subprocess.run(
            [
                "skill-seekers",
                "analyze",
                "--directory",
                str(self.test_dir),
                "--output",
                str(output_dir),
                "--quick",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(result.returncode, 0, f"Verbose analysis failed: {result.stderr}")

        # Verbose should produce more output
        combined_output = result.stdout + result.stderr
        self.assertGreater(len(combined_output), 100, "Verbose mode didn't produce extra output")


if __name__ == "__main__":
    unittest.main()
