#!/usr/bin/env python3
"""
Tests for Haystack Adaptor
"""

import json

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestHaystackAdaptor:
    """Test suite for HaystackAdaptor class."""

    def test_adaptor_registration(self):
        """Test that Haystack adaptor is registered."""
        adaptor = get_adaptor("haystack")
        assert adaptor.PLATFORM == "haystack"
        assert adaptor.PLATFORM_NAME == "Haystack (RAG Framework)"

    def test_format_skill_md(self, tmp_path):
        """Test formatting SKILL.md as Haystack Documents."""
        # Create test skill directory
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Test Skill\n\nThis is a test skill for Haystack format.")

        # Create references directory with files
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "getting_started.md").write_text("# Getting Started\n\nQuick start.")
        (refs_dir / "api.md").write_text("# API Reference\n\nAPI docs.")

        # Format as Haystack Documents
        adaptor = get_adaptor("haystack")
        metadata = SkillMetadata(name="test_skill", description="Test skill", version="1.0.0")

        documents_json = adaptor.format_skill_md(skill_dir, metadata)

        # Parse and validate
        documents = json.loads(documents_json)

        assert len(documents) == 3  # SKILL.md + 2 references

        # Check document structure
        for doc in documents:
            assert "content" in doc
            assert "meta" in doc
            assert doc["meta"]["source"] == "test_skill"
            assert doc["meta"]["version"] == "1.0.0"
            assert "category" in doc["meta"]
            assert "file" in doc["meta"]
            assert "type" in doc["meta"]

        # Check categories
        categories = {doc["meta"]["category"] for doc in documents}
        assert "overview" in categories  # From SKILL.md
        assert "getting started" in categories or "api" in categories  # From references

    def test_package_creates_json(self, tmp_path):
        """Test packaging skill into JSON file."""
        # Create test skill
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\n\nTest content.")

        # Package
        adaptor = get_adaptor("haystack")
        output_path = adaptor.package(skill_dir, tmp_path)

        # Verify output
        assert output_path.exists()
        assert output_path.suffix == ".json"
        assert "haystack" in output_path.name

        # Verify content
        with open(output_path) as f:
            documents = json.load(f)

        assert isinstance(documents, list)
        assert len(documents) > 0
        assert "content" in documents[0]
        assert "meta" in documents[0]

    def test_package_output_filename(self, tmp_path):
        """Test package output filename generation."""
        skill_dir = tmp_path / "react"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# React\n\nReact docs.")

        adaptor = get_adaptor("haystack")

        # Test directory output
        output_path = adaptor.package(skill_dir, tmp_path)
        assert output_path.name == "react-haystack.json"

        # Test with .zip extension (should replace)
        output_path = adaptor.package(skill_dir, tmp_path / "test.zip")
        assert output_path.suffix == ".json"
        assert "haystack" in output_path.name

    def test_upload_returns_message(self, tmp_path):
        """Test upload returns instructions (no actual upload)."""
        # Create test package
        package_path = tmp_path / "test-haystack.json"
        package_path.write_text("[]")

        adaptor = get_adaptor("haystack")
        result = adaptor.upload(package_path, "fake-key")

        assert result["success"] is False  # No upload capability
        assert result["skill_id"] is None
        assert "message" in result
        assert "from haystack import Document" in result["message"]
        assert "InMemoryDocumentStore" in result["message"]

    def test_validate_api_key_returns_false(self):
        """Test that API key validation returns False (no API needed)."""
        adaptor = get_adaptor("haystack")
        assert adaptor.validate_api_key("any-key") is False

    def test_get_env_var_name_returns_empty(self):
        """Test that env var name is empty (no API needed)."""
        adaptor = get_adaptor("haystack")
        assert adaptor.get_env_var_name() == ""

    def test_supports_enhancement_returns_false(self):
        """Test that enhancement is not supported."""
        adaptor = get_adaptor("haystack")
        assert adaptor.supports_enhancement() is False

    def test_enhance_returns_false(self, tmp_path):
        """Test that enhance returns False."""
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        adaptor = get_adaptor("haystack")
        result = adaptor.enhance(skill_dir, "fake-key")

        assert result is False

    def test_empty_skill_directory(self, tmp_path):
        """Test handling of empty skill directory."""
        skill_dir = tmp_path / "empty_skill"
        skill_dir.mkdir()

        adaptor = get_adaptor("haystack")
        metadata = SkillMetadata(name="empty_skill", description="Empty", version="1.0.0")

        documents_json = adaptor.format_skill_md(skill_dir, metadata)
        documents = json.loads(documents_json)

        # Should return empty list
        assert documents == []

    def test_references_only(self, tmp_path):
        """Test skill with references but no SKILL.md."""
        skill_dir = tmp_path / "refs_only"
        skill_dir.mkdir()

        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "test.md").write_text("# Test\n\nTest content.")

        adaptor = get_adaptor("haystack")
        metadata = SkillMetadata(name="refs_only", description="Refs only", version="1.0.0")

        documents_json = adaptor.format_skill_md(skill_dir, metadata)
        documents = json.loads(documents_json)

        assert len(documents) == 1
        assert documents[0]["meta"]["category"] == "test"
        assert documents[0]["meta"]["type"] == "reference"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
