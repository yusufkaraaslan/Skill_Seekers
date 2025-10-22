#!/usr/bin/env python3
"""
Tests for cli/estimate_pages.py functionality
"""

import unittest
import tempfile
import json
from pathlib import Path
import sys

# Add cli directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'cli'))

from estimate_pages import estimate_pages


class TestEstimatePages(unittest.TestCase):
    """Test estimate_pages function"""

    def test_estimate_pages_with_minimal_config(self):
        """Test estimation with minimal configuration"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'rate_limit': 0.1
        }

        # This will make real HTTP request to example.com
        # We use low max_discovery to keep test fast
        result = estimate_pages(config, max_discovery=2, timeout=5)

        # Check result structure
        self.assertIsInstance(result, dict)
        self.assertIn('discovered', result)
        self.assertIn('estimated_total', result)
        # Actual key is elapsed_seconds, not time_elapsed
        self.assertIn('elapsed_seconds', result)

    def test_estimate_pages_returns_discovered_count(self):
        """Test that result contains discovered page count"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'rate_limit': 0.1
        }

        result = estimate_pages(config, max_discovery=1, timeout=5)

        self.assertGreaterEqual(result['discovered'], 0)
        self.assertIsInstance(result['discovered'], int)

    def test_estimate_pages_respects_max_discovery(self):
        """Test that estimation respects max_discovery limit"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'rate_limit': 0.1
        }

        result = estimate_pages(config, max_discovery=3, timeout=5)

        # Should not discover more than max_discovery
        self.assertLessEqual(result['discovered'], 3)

    def test_estimate_pages_with_start_urls(self):
        """Test estimation with custom start_urls"""
        config = {
            'name': 'test',
            'base_url': 'https://example.com/',
            'start_urls': ['https://example.com/'],
            'rate_limit': 0.1
        }

        result = estimate_pages(config, max_discovery=2, timeout=5)

        self.assertIsInstance(result, dict)
        self.assertIn('discovered', result)


class TestEstimatePagesCLI(unittest.TestCase):
    """Test estimate_pages.py command-line interface"""

    def test_cli_help_output(self):
        """Test that --help works"""
        import subprocess

        result = subprocess.run(
            ['python3', 'cli/estimate_pages.py', '--help'],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn('usage:', result.stdout.lower())

    def test_cli_executes_with_help_flag(self):
        """Test that script can be executed with --help"""
        import subprocess

        result = subprocess.run(
            ['python3', 'cli/estimate_pages.py', '--help'],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)

    def test_cli_requires_config_argument(self):
        """Test that CLI requires config file argument"""
        import subprocess

        # Run without config argument
        result = subprocess.run(
            ['python3', 'cli/estimate_pages.py'],
            capture_output=True,
            text=True
        )

        # Should fail (non-zero exit code) or show usage
        self.assertTrue(
            result.returncode != 0 or 'usage' in result.stderr.lower() or 'usage' in result.stdout.lower()
        )


class TestEstimatePagesWithRealConfig(unittest.TestCase):
    """Test estimation with real config files (if available)"""

    def test_estimate_with_real_config_file(self):
        """Test estimation using a real config file (if exists)"""
        config_path = Path('configs/react.json')

        if not config_path.exists():
            self.skipTest("configs/react.json not found")

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Use very low max_discovery to keep test fast
        result = estimate_pages(config, max_discovery=3, timeout=5)

        self.assertIsInstance(result, dict)
        self.assertIn('discovered', result)
        self.assertGreater(result['discovered'], 0)


if __name__ == '__main__':
    unittest.main()
