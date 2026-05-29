#!/usr/bin/env python3
"""
Tests for UniSkillConfigValidator (unified config format).

Covers edge cases not tested by the legacy format tests in test_config_validation.py.
Tests: invalid source types, invalid merge_mode, invalid marketplace_targets,
       invalid github source fields, empty sources array, non-dict sources.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.config_validator import UniSkillConfigValidator


class TestUniSkillConfigValidator(unittest.TestCase):
    """Tests for UniSkillConfigValidator (unified format)."""

    def test_valid_minimal_unified_config(self):
        """Minimal valid unified config with one documentation source."""
        config = {
            "name": "test-skill",
            "description": "A test skill",
            "sources": [{"type": "documentation", "base_url": "https://example.com/"}],
        }
        validator = UniSkillConfigValidator(config)
        self.assertTrue(validator.validate())

    def test_empty_sources_array_rejected(self):
        """Empty sources array must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_sources_not_an_array_rejected(self):
        """sources must be an array, not a dict or string."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": {"type": "documentation"},
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("must be an array", str(ctx.exception))

    def test_invalid_source_type_rejected(self):
        """Unknown source type must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "not_a_real_type", "base_url": "https://example.com/"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Invalid type", str(ctx.exception))
        self.assertIn("not_a_real_type", str(ctx.exception))

    def test_invalid_merge_mode_rejected(self):
        """Invalid merge_mode must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "documentation", "base_url": "https://example.com/"}],
            "merge_mode": "invalid-mode",
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Invalid merge_mode", str(ctx.exception))

    def test_all_valid_merge_modes_accepted(self):
        """All documented merge modes must be accepted."""
        for mode in ["rule-based", "ai-enhanced", "claude-enhanced"]:
            config = {
                "name": "test",
                "description": "Test",
                "sources": [{"type": "documentation", "base_url": "https://example.com/"}],
                "merge_mode": mode,
            }
            validator = UniSkillConfigValidator(config)
            self.assertTrue(validator.validate(), f"merge_mode '{mode}' should be valid")

    def test_invalid_marketplace_targets_type_rejected(self):
        """marketplace_targets must be an array."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "documentation", "base_url": "https://example.com/"}],
            "marketplace_targets": "claude",
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("must be an array", str(ctx.exception))

    def test_invalid_marketplace_entry_rejected(self):
        """marketplace_targets entries must be objects with marketplace field."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "documentation", "base_url": "https://example.com/"}],
            "marketplace_targets": [{"not_marketplace": "claude"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("missing required field", str(ctx.exception))

    def test_github_source_invalid_repo_format_rejected(self):
        """GitHub source with invalid repo format (no owner/) must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "github", "repo": "react"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Invalid repo format", str(ctx.exception))
        self.assertIn("owner/repo", str(ctx.exception))

    def test_github_source_invalid_code_analysis_depth_rejected(self):
        """github source with invalid code_analysis_depth must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [
                {
                    "type": "github",
                    "repo": "facebook/react",
                    "code_analysis_depth": "deepish",  # invalid
                }
            ],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Invalid code_analysis_depth", str(ctx.exception))

    def test_github_source_invalid_issue_state_rejected(self):
        """github source with invalid issue_state must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [
                {
                    "type": "github",
                    "repo": "facebook/react",
                    "issue_state": "pending",  # invalid
                }
            ],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Invalid issue_state", str(ctx.exception))

    def test_github_source_invalid_ai_mode_rejected(self):
        """github source with invalid ai_mode must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [
                {
                    "type": "github",
                    "repo": "facebook/react",
                    "ai_mode": "offline",  # invalid
                }
            ],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Invalid ai_mode", str(ctx.exception))

    def test_local_source_path_not_a_directory_rejected(self):
        """local source where path exists but is not a directory must be rejected."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [
                {
                    "type": "local",
                    "path": __file__,  # this file, not a directory
                }
            ],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("not a directory", str(ctx.exception))

    def test_video_source_requires_url_or_path_or_playlist(self):
        """video source must have url, path, or playlist."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "video"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))

    def test_openapi_source_requires_path_or_url(self):
        """openapi source must have path or url."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "openapi"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))

    def test_rss_source_requires_url_or_path(self):
        """rss source must have url or path."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "rss"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))

    def test_confluence_source_requires_url_or_path(self):
        """confluence source must have url/base_url or path."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "confluence"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))

    def test_notion_source_requires_url_or_path(self):
        """notion source must have url/database_id/page_id or path."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "notion"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))

    def test_manpage_source_requires_path_or_names(self):
        """manpage source must have path or names."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "manpage"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))

    def test_chat_source_requires_path_or_api_token(self):
        """chat source must have path or token/webhook_url."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [{"type": "chat"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))

    def test_missing_name_rejected(self):
        """Config without name must be rejected."""
        config = {
            "description": "Test",
            "sources": [{"type": "documentation", "base_url": "https://example.com/"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))
        self.assertIn("name", str(ctx.exception))

    def test_missing_description_rejected(self):
        """Config without description must be rejected."""
        config = {
            "name": "test",
            "sources": [{"type": "documentation", "base_url": "https://example.com/"}],
        }
        validator = UniSkillConfigValidator(config)
        with self.assertRaises(ValueError) as ctx:
            validator.validate()
        self.assertIn("Missing required field", str(ctx.exception))
        self.assertIn("description", str(ctx.exception))

    def test_get_sources_by_type(self):
        """get_sources_by_type returns only matching sources."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [
                {"type": "documentation", "base_url": "https://example.com/"},
                {"type": "github", "repo": "facebook/react"},
                {"type": "documentation", "base_url": "https://foo.com/"},
            ],
        }
        validator = UniSkillConfigValidator(config)
        validator.validate()
        docs = validator.get_sources_by_type("documentation")
        self.assertEqual(len(docs), 2)
        github = validator.get_sources_by_type("github")
        self.assertEqual(len(github), 1)

    def test_has_multiple_sources(self):
        """has_multiple_sources returns True when >1 source."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [
                {"type": "documentation", "base_url": "https://example.com/"},
                {"type": "github", "repo": "facebook/react"},
            ],
        }
        validator = UniSkillConfigValidator(config)
        self.assertTrue(validator.has_multiple_sources())

    def test_needs_api_merge(self):
        """needs_api_merge returns True when docs+github with extraction enabled."""
        config = {
            "name": "test",
            "description": "Test",
            "sources": [
                {"type": "documentation", "base_url": "https://example.com/", "extract_api": True},
                {"type": "github", "repo": "facebook/react", "include_code": True},
            ],
        }
        validator = UniSkillConfigValidator(config)
        self.assertTrue(validator.needs_api_merge())


if __name__ == "__main__":
    unittest.main()
