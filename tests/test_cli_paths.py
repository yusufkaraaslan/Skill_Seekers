#!/usr/bin/env python3
"""
Test suite for CLI path corrections
Tests that all CLI scripts use correct cli/ prefix in usage messages, print statements, and subprocess calls
"""

import sys
import os
import unittest
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCLIPathsInDocstrings(unittest.TestCase):
    """Test that all CLI scripts have correct paths in their docstrings"""

    def test_doc_scraper_usage_paths(self):
        """Test doc_scraper.py usage examples use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        doc_scraper_path = cli_dir / 'doc_scraper.py'

        with open(doc_scraper_path, 'r') as f:
            content = f.read()

        # Check that usage examples use cli/ prefix
        self.assertIn('python3 cli/doc_scraper.py --interactive', content)
        self.assertIn('python3 cli/doc_scraper.py --config', content)

        # Ensure old patterns are NOT present
        self.assertNotIn('python3 doc_scraper.py --interactive', content)
        self.assertNotIn('python3 doc_scraper.py --config', content)

    def test_enhance_skill_local_usage_paths(self):
        """Test enhance_skill_local.py usage examples use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        script_path = cli_dir / 'enhance_skill_local.py'

        with open(script_path, 'r') as f:
            content = f.read()

        # Check that usage examples use cli/ prefix
        self.assertIn('python3 cli/enhance_skill_local.py', content)

        # Ensure old patterns are NOT present
        lines_without_cli = [line for line in content.split('\n')
                            if 'python3 enhance_skill_local.py' in line]
        self.assertEqual(len(lines_without_cli), 0,
                        "Found usage of 'python3 enhance_skill_local.py' without cli/ prefix")

    def test_enhance_skill_usage_paths(self):
        """Test enhance_skill.py usage examples use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        script_path = cli_dir / 'enhance_skill.py'

        with open(script_path, 'r') as f:
            content = f.read()

        # Check that usage examples use cli/ prefix
        self.assertIn('python3 cli/enhance_skill.py', content)

        # Ensure old patterns are NOT present
        lines_without_cli = [line for line in content.split('\n')
                            if 'python3 enhance_skill.py' in line and 'cli/' not in line]
        self.assertEqual(len(lines_without_cli), 0,
                        "Found usage of 'python3 enhance_skill.py' without cli/ prefix")

    def test_package_skill_usage_paths(self):
        """Test package_skill.py usage examples use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        script_path = cli_dir / 'package_skill.py'

        with open(script_path, 'r') as f:
            content = f.read()

        # Check that usage examples use cli/ prefix
        self.assertIn('python3 cli/package_skill.py', content)

        # Ensure old patterns are NOT present
        lines_without_cli = [line for line in content.split('\n')
                            if 'python3 package_skill.py' in line and 'cli/' not in line]
        self.assertEqual(len(lines_without_cli), 0,
                        "Found usage of 'python3 package_skill.py' without cli/ prefix")

    def test_estimate_pages_usage_paths(self):
        """Test estimate_pages.py usage examples use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        script_path = cli_dir / 'estimate_pages.py'

        with open(script_path, 'r') as f:
            content = f.read()

        # Check that usage examples use cli/ prefix
        self.assertIn('python3 cli/estimate_pages.py', content)

        # Ensure old patterns are NOT present
        lines_without_cli = [line for line in content.split('\n')
                            if 'python3 estimate_pages.py' in line and 'cli/' not in line]
        self.assertEqual(len(lines_without_cli), 0,
                        "Found usage of 'python3 estimate_pages.py' without cli/ prefix")


class TestCLIPathsInPrintStatements(unittest.TestCase):
    """Test that print statements in CLI scripts use correct paths"""

    def test_doc_scraper_print_statements(self):
        """Test doc_scraper.py print statements use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        doc_scraper_path = cli_dir / 'doc_scraper.py'

        with open(doc_scraper_path, 'r') as f:
            content = f.read()

        # Check print statements for package_skill.py reference
        self.assertIn('python3 cli/package_skill.py', content)

        # Check print statements for enhance_skill.py references
        self.assertIn('python3 cli/enhance_skill.py', content)
        self.assertIn('python3 cli/enhance_skill_local.py', content)

        # Ensure no old hardcoded paths
        self.assertNotIn('/mnt/skills/examples/skill-creator/scripts/', content)

    def test_enhance_skill_local_print_statements(self):
        """Test enhance_skill_local.py print statements use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        script_path = cli_dir / 'enhance_skill_local.py'

        with open(script_path, 'r') as f:
            content = f.read()

        # Check print statements for package_skill.py reference
        self.assertIn('python3 cli/package_skill.py', content)

        # Ensure no old hardcoded paths
        self.assertNotIn('/mnt/skills/examples/skill-creator/scripts/', content)

    def test_enhance_skill_print_statements(self):
        """Test enhance_skill.py print statements use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        script_path = cli_dir / 'enhance_skill.py'

        with open(script_path, 'r') as f:
            content = f.read()

        # Check print statements for package_skill.py reference
        self.assertIn('python3 cli/package_skill.py', content)

        # Ensure no old hardcoded paths
        self.assertNotIn('/mnt/skills/examples/skill-creator/scripts/', content)


class TestCLIPathsInSubprocessCalls(unittest.TestCase):
    """Test that subprocess calls use correct paths"""

    def test_doc_scraper_subprocess_calls(self):
        """Test doc_scraper.py subprocess calls use cli/ prefix"""
        cli_dir = Path(__file__).parent.parent / 'cli'
        doc_scraper_path = cli_dir / 'doc_scraper.py'

        with open(doc_scraper_path, 'r') as f:
            content = f.read()

        # Check subprocess calls
        self.assertIn("'cli/enhance_skill.py'", content)
        self.assertIn("'cli/enhance_skill_local.py'", content)


class TestDocumentationPaths(unittest.TestCase):
    """Test that documentation files use correct CLI paths"""

    def test_quickstart_paths(self):
        """Test QUICKSTART.md uses cli/ prefix"""
        quickstart_path = Path(__file__).parent.parent / 'QUICKSTART.md'

        with open(quickstart_path, 'r') as f:
            content = f.read()

        # Should have cli/ prefix
        self.assertIn('python3 cli/doc_scraper.py', content)
        self.assertIn('python3 cli/enhance_skill_local.py', content)
        self.assertIn('python3 cli/package_skill.py', content)

        # Should NOT have old patterns (except in code blocks showing the difference)
        doc_scraper_without_cli = content.count('python3 doc_scraper.py')
        # Allow zero occurrences
        self.assertEqual(doc_scraper_without_cli, 0,
                        f"Found {doc_scraper_without_cli} occurrences of 'python3 doc_scraper.py' without cli/")

    def test_upload_guide_paths(self):
        """Test docs/UPLOAD_GUIDE.md uses cli/ prefix"""
        upload_guide_path = Path(__file__).parent.parent / 'docs' / 'UPLOAD_GUIDE.md'

        with open(upload_guide_path, 'r') as f:
            content = f.read()

        # Should have cli/ prefix
        self.assertIn('python3 cli/package_skill.py', content)
        self.assertIn('python3 cli/doc_scraper.py', content)
        self.assertIn('python3 cli/enhance_skill_local.py', content)

    def test_enhancement_guide_paths(self):
        """Test docs/ENHANCEMENT.md uses cli/ prefix"""
        enhancement_path = Path(__file__).parent.parent / 'docs' / 'ENHANCEMENT.md'

        with open(enhancement_path, 'r') as f:
            content = f.read()

        # Should have cli/ prefix
        self.assertIn('python3 cli/enhance_skill_local.py', content)
        self.assertIn('python3 cli/enhance_skill.py', content)
        self.assertIn('python3 cli/doc_scraper.py', content)


class TestCLIHelpOutput(unittest.TestCase):
    """Test that --help output is functional (argparse strips paths automatically)"""

    def test_doc_scraper_help_output(self):
        """Test doc_scraper.py --help works correctly"""
        result = subprocess.run(
            ['python3', 'cli/doc_scraper.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        # Should execute successfully and show usage
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())
        self.assertIn('doc_scraper.py', result.stdout)

    def test_package_skill_help_output(self):
        """Test package_skill.py --help works correctly"""
        result = subprocess.run(
            ['python3', 'cli/package_skill.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        # Should execute successfully and show usage
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())
        # The epilog section should show cli/ prefix
        self.assertIn('cli/package_skill.py', result.stdout)


class TestScriptExecutability(unittest.TestCase):
    """Test that scripts can actually be executed with cli/ prefix"""

    def test_doc_scraper_executes_with_cli_prefix(self):
        """Test doc_scraper.py can be executed as cli/doc_scraper.py"""
        result = subprocess.run(
            ['python3', 'cli/doc_scraper.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        # Should execute successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())

    def test_enhance_skill_local_executes_with_cli_prefix(self):
        """Test enhance_skill_local.py can be executed as cli/enhance_skill_local.py"""
        result = subprocess.run(
            ['python3', 'cli/enhance_skill_local.py'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        # Should show usage (exit code 1 because no args)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Usage:', result.stdout)

    def test_package_skill_executes_with_cli_prefix(self):
        """Test package_skill.py can be executed as cli/package_skill.py"""
        result = subprocess.run(
            ['python3', 'cli/package_skill.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        # Should execute successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())

    def test_estimate_pages_executes_with_cli_prefix(self):
        """Test estimate_pages.py can be executed as cli/estimate_pages.py"""
        result = subprocess.run(
            ['python3', 'cli/estimate_pages.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        # Should execute successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())


if __name__ == '__main__':
    unittest.main()
