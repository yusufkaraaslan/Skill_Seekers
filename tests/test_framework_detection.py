"""
Tests for framework detection fix (Issue #239).

Verifies that framework detection works correctly by detecting imports
from Python files, even if those files have no classes or functions.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


class TestFrameworkDetection(unittest.TestCase):
    """Tests for Issue #239 - Framework detection with import-only files"""

    def setUp(self):
        """Create temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_project = Path(self.temp_dir) / "test_project"
        self.test_project.mkdir()
        self.output_dir = Path(self.temp_dir) / "output"

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_flask_framework_detection_from_imports(self):
        """Test that Flask is detected from import statements (Issue #239)."""
        # Create simple Flask project with import-only __init__.py
        app_dir = self.test_project / "app"
        app_dir.mkdir()

        # File with only imports (no classes/functions)
        (app_dir / "__init__.py").write_text("from flask import Flask\napp = Flask(__name__)")

        # File with Flask routes
        (app_dir / "routes.py").write_text(
            "from flask import render_template\n"
            "from app import app\n\n"
            "@app.route('/')\n"
            "def index():\n"
            "    return render_template('index.html')\n"
        )

        # Run codebase analyzer
        from skill_seekers.cli.codebase_scraper import main as scraper_main
        import sys

        old_argv = sys.argv
        try:
            sys.argv = [
                "skill-seekers-codebase",
                "--directory",
                str(self.test_project),
                "--output",
                str(self.output_dir),
                "--depth",
                "deep",
                "--ai-mode",
                "none",
                "--skip-patterns",
                "--skip-test-examples",
                "--skip-how-to-guides",
                "--skip-config-patterns",
                "--skip-docs",
            ]
            scraper_main()
        finally:
            sys.argv = old_argv

        # Verify Flask was detected
        arch_file = self.output_dir / "references" / "architecture" / "architectural_patterns.json"
        self.assertTrue(arch_file.exists(), "Architecture file should be created")

        with open(arch_file) as f:
            arch_data = json.load(f)

        self.assertIn("frameworks_detected", arch_data)
        self.assertIn(
            "Flask", arch_data["frameworks_detected"], "Flask should be detected from imports"
        )

    def test_files_with_imports_are_included(self):
        """Test that files with only imports are included in analysis (Issue #239)."""
        # Create file with only imports
        (self.test_project / "imports_only.py").write_text(
            "import django\nfrom flask import Flask\nimport requests"
        )

        # Run codebase analyzer
        from skill_seekers.cli.codebase_scraper import main as scraper_main
        import sys

        old_argv = sys.argv
        try:
            sys.argv = [
                "skill-seekers-codebase",
                "--directory",
                str(self.test_project),
                "--output",
                str(self.output_dir),
                "--depth",
                "deep",
                "--ai-mode",
                "none",
            ]
            scraper_main()
        finally:
            sys.argv = old_argv

        # Verify file was analyzed
        code_analysis = self.output_dir / "code_analysis.json"
        self.assertTrue(code_analysis.exists(), "Code analysis file should exist")

        with open(code_analysis) as f:
            analysis_data = json.load(f)

        # File should be included
        self.assertGreater(len(analysis_data["files"]), 0, "Files with imports should be included")

        # Find our import-only file
        import_file = next(
            (f for f in analysis_data["files"] if "imports_only.py" in f["file"]), None
        )
        self.assertIsNotNone(import_file, "Import-only file should be in analysis")

        # Verify imports were extracted
        self.assertIn("imports", import_file, "Imports should be extracted")
        self.assertGreater(len(import_file["imports"]), 0, "Should have captured imports")
        self.assertIn("django", import_file["imports"], "Django import should be captured")
        self.assertIn("flask", import_file["imports"], "Flask import should be captured")

    def test_no_false_positive_frameworks(self):
        """Test that framework detection doesn't produce false positives (Issue #239)."""
        # Create project with "app" directory but no Flask
        app_dir = self.test_project / "app"
        app_dir.mkdir()

        # File with no framework imports
        (app_dir / "utils.py").write_text("def my_function():\n    return 'hello'\n")

        # Run codebase analyzer
        from skill_seekers.cli.codebase_scraper import main as scraper_main
        import sys

        old_argv = sys.argv
        try:
            sys.argv = [
                "skill-seekers-codebase",
                "--directory",
                str(self.test_project),
                "--output",
                str(self.output_dir),
                "--depth",
                "deep",
                "--ai-mode",
                "none",
            ]
            scraper_main()
        finally:
            sys.argv = old_argv

        # Check frameworks detected
        arch_file = self.output_dir / "references" / "architecture" / "architectural_patterns.json"

        if arch_file.exists():
            with open(arch_file) as f:
                arch_data = json.load(f)

            frameworks = arch_data.get("frameworks_detected", [])
            # Should not detect Flask just from "app" directory name
            self.assertNotIn("Flask", frameworks, "Should not detect Flask without imports")
            # Should not detect other frameworks with "app" in markers
            for fw in ["ASP.NET", "Rails", "Laravel"]:
                self.assertNotIn(fw, frameworks, f"Should not detect {fw} without real evidence")


if __name__ == "__main__":
    unittest.main()
