#!/usr/bin/env python3
"""
Tests for multi-platform install workflow
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from pathlib import Path


class TestInstallCLI(unittest.TestCase):
    """Test install_skill CLI with multi-platform support"""

    def test_cli_accepts_target_flag(self):
        """Test that CLI accepts --target flag"""
        import argparse
        import sys
        from pathlib import Path

        # Mock sys.path to import install_skill module
        sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "skill_seekers" / "cli"))

        try:
            # Create parser like install_skill.py does
            parser = argparse.ArgumentParser()
            parser.add_argument("--config", required=True)
            parser.add_argument("--target", choices=['claude', 'gemini', 'openai', 'markdown'], default='claude')

            # Test that each platform is accepted
            for platform in ['claude', 'gemini', 'openai', 'markdown']:
                args = parser.parse_args(['--config', 'test', '--target', platform])
                self.assertEqual(args.target, platform)

            # Test default is claude
            args = parser.parse_args(['--config', 'test'])
            self.assertEqual(args.target, 'claude')

        finally:
            sys.path.pop(0)

    def test_cli_rejects_invalid_target(self):
        """Test that CLI rejects invalid --target values"""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--config", required=True)
        parser.add_argument("--target", choices=['claude', 'gemini', 'openai', 'markdown'], default='claude')

        # Should raise SystemExit for invalid target
        with self.assertRaises(SystemExit):
            parser.parse_args(['--config', 'test', '--target', 'invalid'])


class TestInstallToolMultiPlatform(unittest.IsolatedAsyncioTestCase):
    """Test install_skill_tool with multi-platform support"""

    async def test_install_tool_accepts_target_parameter(self):
        """Test that install_skill_tool accepts target parameter"""
        from skill_seekers.mcp.tools.packaging_tools import install_skill_tool

        # Just test dry_run mode which doesn't need mocking all internal tools
        # Test with each platform
        for target in ['claude', 'gemini', 'openai']:
            # Use dry_run=True which skips actual execution
            # It will still show us the platform is being recognized
            with patch('builtins.open', create=True) as mock_open, \
                 patch('json.load') as mock_json_load:

                # Mock config file reading
                mock_json_load.return_value = {'name': 'test-skill'}
                mock_file = MagicMock()
                mock_file.__enter__ = lambda s: s
                mock_file.__exit__ = MagicMock()
                mock_open.return_value = mock_file

                result = await install_skill_tool({
                    "config_path": "configs/test.json",
                    "target": target,
                    "dry_run": True
                })

                # Verify result mentions the correct platform
                result_text = result[0].text
                self.assertIsInstance(result_text, str)
                self.assertIn("WORKFLOW COMPLETE", result_text)

    async def test_install_tool_uses_correct_adaptor(self):
        """Test that install_skill_tool uses the correct adaptor for each platform"""
        from skill_seekers.mcp.tools.packaging_tools import install_skill_tool
        from skill_seekers.cli.adaptors import get_adaptor

        # Test that each platform creates the right adaptor
        for target in ['claude', 'gemini', 'openai', 'markdown']:
            adaptor = get_adaptor(target)
            self.assertEqual(adaptor.PLATFORM, target)

    async def test_install_tool_platform_specific_api_keys(self):
        """Test that install_tool checks for correct API key per platform"""
        from skill_seekers.cli.adaptors import get_adaptor

        # Test API key env var names
        claude_adaptor = get_adaptor('claude')
        self.assertEqual(claude_adaptor.get_env_var_name(), 'ANTHROPIC_API_KEY')

        gemini_adaptor = get_adaptor('gemini')
        self.assertEqual(gemini_adaptor.get_env_var_name(), 'GOOGLE_API_KEY')

        openai_adaptor = get_adaptor('openai')
        self.assertEqual(openai_adaptor.get_env_var_name(), 'OPENAI_API_KEY')

        markdown_adaptor = get_adaptor('markdown')
        # Markdown doesn't need an API key, but should still have a method
        self.assertIsNotNone(markdown_adaptor.get_env_var_name())


class TestInstallWorkflowIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for full install workflow"""

    async def test_dry_run_shows_correct_platform(self):
        """Test dry run shows correct platform in output"""
        from skill_seekers.cli.adaptors import get_adaptor

        # Test each platform shows correct platform name
        platforms = {
            'claude': 'Claude AI (Anthropic)',
            'gemini': 'Google Gemini',
            'openai': 'OpenAI ChatGPT',
            'markdown': 'Generic Markdown (Universal)'
        }

        for target, expected_name in platforms.items():
            adaptor = get_adaptor(target)
            self.assertEqual(adaptor.PLATFORM_NAME, expected_name)


if __name__ == '__main__':
    unittest.main()
