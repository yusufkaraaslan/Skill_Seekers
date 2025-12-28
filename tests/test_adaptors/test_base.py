#!/usr/bin/env python3
"""
Tests for base adaptor and registry
"""

import unittest
from pathlib import Path

from skill_seekers.cli.adaptors import (
    get_adaptor,
    list_platforms,
    is_platform_available,
    SkillAdaptor,
    SkillMetadata,
    ADAPTORS
)


class TestSkillMetadata(unittest.TestCase):
    """Test SkillMetadata dataclass"""

    def test_basic_metadata(self):
        """Test basic metadata creation"""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test skill description"
        )

        self.assertEqual(metadata.name, "test-skill")
        self.assertEqual(metadata.description, "Test skill description")
        self.assertEqual(metadata.version, "1.0.0")  # default
        self.assertIsNone(metadata.author)  # default
        self.assertEqual(metadata.tags, [])  # default

    def test_full_metadata(self):
        """Test metadata with all fields"""
        metadata = SkillMetadata(
            name="react",
            description="React documentation",
            version="2.5.0",
            author="Test Author",
            tags=["react", "javascript", "web"]
        )

        self.assertEqual(metadata.name, "react")
        self.assertEqual(metadata.description, "React documentation")
        self.assertEqual(metadata.version, "2.5.0")
        self.assertEqual(metadata.author, "Test Author")
        self.assertEqual(metadata.tags, ["react", "javascript", "web"])


class TestAdaptorRegistry(unittest.TestCase):
    """Test adaptor registry and factory"""

    def test_list_platforms(self):
        """Test listing available platforms"""
        platforms = list_platforms()

        self.assertIsInstance(platforms, list)
        # Claude should always be available
        self.assertIn('claude', platforms)

    def test_is_platform_available(self):
        """Test checking platform availability"""
        # Claude should be available
        self.assertTrue(is_platform_available('claude'))

        # Unknown platform should not be available
        self.assertFalse(is_platform_available('unknown_platform'))

    def test_get_adaptor_claude(self):
        """Test getting Claude adaptor"""
        adaptor = get_adaptor('claude')

        self.assertIsInstance(adaptor, SkillAdaptor)
        self.assertEqual(adaptor.PLATFORM, 'claude')
        self.assertEqual(adaptor.PLATFORM_NAME, 'Claude AI (Anthropic)')

    def test_get_adaptor_invalid(self):
        """Test getting invalid adaptor raises error"""
        with self.assertRaises(ValueError) as ctx:
            get_adaptor('invalid_platform')

        error_msg = str(ctx.exception)
        self.assertIn('invalid_platform', error_msg)
        self.assertIn('not supported', error_msg)

    def test_get_adaptor_with_config(self):
        """Test getting adaptor with custom config"""
        config = {'custom_setting': 'value'}
        adaptor = get_adaptor('claude', config)

        self.assertEqual(adaptor.config, config)


class TestBaseAdaptorInterface(unittest.TestCase):
    """Test base adaptor interface methods"""

    def setUp(self):
        """Set up test adaptor"""
        self.adaptor = get_adaptor('claude')

    def test_validate_api_key_default(self):
        """Test default API key validation"""
        # Claude adaptor overrides this
        self.assertTrue(self.adaptor.validate_api_key('sk-ant-test123'))
        self.assertFalse(self.adaptor.validate_api_key('invalid'))

    def test_get_env_var_name(self):
        """Test environment variable name"""
        env_var = self.adaptor.get_env_var_name()

        self.assertEqual(env_var, 'ANTHROPIC_API_KEY')

    def test_supports_enhancement(self):
        """Test enhancement support check"""
        # Claude supports enhancement
        self.assertTrue(self.adaptor.supports_enhancement())


if __name__ == '__main__':
    unittest.main()
