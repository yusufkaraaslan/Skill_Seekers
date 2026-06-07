#!/usr/bin/env python3
"""
Tests for registry-derived platform lists.

Guards against the "hardcoded list drifts from the ADAPTORS registry" bug class
(the same one fixed for `enhance` in #395) now applied to upload/install/package:
platform choices must be derived from adaptor capabilities, not hand-maintained.
"""

import argparse
import unittest

from skill_seekers.cli.adaptors import (
    get_adaptor,
    get_enhancement_platforms,
    get_upload_platforms,
)


class TestSupportsUpload(unittest.TestCase):
    """supports_upload() must be True only for adaptors with a real upload/push."""

    def test_real_uploaders(self):
        for name in ("claude", "gemini", "openai", "minimax", "chroma", "weaviate", "pinecone"):
            self.assertTrue(get_adaptor(name).supports_upload(), f"{name} should support upload")

    def test_non_uploaders(self):
        # markdown + vector-DB stubs explicitly do not perform an upload.
        for name in ("markdown", "qdrant", "faiss", "langchain", "llama-index", "haystack"):
            self.assertFalse(
                get_adaptor(name).supports_upload(), f"{name} should NOT support upload"
            )


class TestGetUploadPlatforms(unittest.TestCase):
    def test_includes_openai_compatible_family(self):
        platforms = get_upload_platforms()
        for name in (
            "claude",
            "gemini",
            "openai",
            "minimax",
            "kimi",
            "deepseek",
            "qwen",
            "openrouter",
            "together",
            "fireworks",
            "chroma",
            "weaviate",
            "pinecone",
        ):
            self.assertIn(name, platforms)

    def test_excludes_stubs(self):
        platforms = get_upload_platforms()
        for name in ("markdown", "qdrant", "faiss", "langchain", "haystack"):
            self.assertNotIn(name, platforms)

    def test_superset_of_legacy_choices_non_breaking(self):
        """The new derived list must not drop any previously-valid upload target."""
        legacy = {"claude", "gemini", "openai", "kimi", "chroma", "weaviate"}
        self.assertTrue(legacy.issubset(set(get_upload_platforms())))


class TestEnhancementListUnchanged(unittest.TestCase):
    def test_minimax_present_markdown_absent(self):
        platforms = get_enhancement_platforms()
        self.assertIn("minimax", platforms)
        self.assertNotIn("markdown", platforms)


class TestArgumentBuildersDeriveChoices(unittest.TestCase):
    """The dict-based builders must inject registry-derived choices."""

    def _parse(self, add_args, argv):
        parser = argparse.ArgumentParser()
        add_args(parser)
        return parser.parse_args(argv)

    def test_upload_accepts_openai_compatible_and_vector(self):
        from skill_seekers.cli.arguments.upload import add_upload_arguments

        for target in ("minimax", "deepseek", "pinecone"):
            args = self._parse(add_upload_arguments, ["pkg.zip", "--target", target])
            self.assertEqual(args.target, target)

    def test_upload_rejects_unknown_target(self):
        from skill_seekers.cli.arguments.upload import add_upload_arguments

        parser = argparse.ArgumentParser()
        add_upload_arguments(parser)
        with self.assertRaises(SystemExit):
            parser.parse_args(["pkg.zip", "--target", "notaplatform"])

    def test_package_accepts_all_registered_platforms(self):
        from skill_seekers.cli.arguments.package import add_package_arguments

        for target in ("minimax", "qdrant", "markdown"):
            args = self._parse(add_package_arguments, ["output/x", "--target", target])
            self.assertEqual(args.target, target)


if __name__ == "__main__":
    unittest.main()
