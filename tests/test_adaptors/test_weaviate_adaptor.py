#!/usr/bin/env python3
"""
Tests for Weaviate Adaptor
"""

import json

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestWeaviateAdaptor:
    """Test suite for WeaviateAdaptor class."""

    def test_adaptor_registration(self):
        """Test that Weaviate adaptor is registered."""
        adaptor = get_adaptor("weaviate")
        assert adaptor.PLATFORM == "weaviate"
        assert adaptor.PLATFORM_NAME == "Weaviate (Vector Database)"

    def test_format_skill_md(self, tmp_path):
        """Test formatting SKILL.md as Weaviate objects."""
        # Create test skill directory
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Test Skill\n\nThis is a test skill for Weaviate format.")

        # Create references directory with files
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "getting_started.md").write_text("# Getting Started\n\nQuick start.")
        (refs_dir / "api.md").write_text("# API Reference\n\nAPI docs.")

        # Format as Weaviate objects
        adaptor = get_adaptor("weaviate")
        metadata = SkillMetadata(name="test_skill", description="Test skill", version="1.0.0")

        objects_json = adaptor.format_skill_md(skill_dir, metadata)

        # Parse and validate
        result = json.loads(objects_json)

        assert "schema" in result
        assert "objects" in result
        assert "class_name" in result
        assert len(result["objects"]) == 3  # SKILL.md + 2 references

        # Check object structure
        for obj in result["objects"]:
            assert "id" in obj
            assert "properties" in obj
            props = obj["properties"]
            assert "content" in props
            assert "source" in props
            assert props["source"] == "test_skill"
            assert props["version"] == "1.0.0"
            assert "category" in props
            assert "file" in props
            assert "type" in props

        # Check categories
        categories = {obj["properties"]["category"] for obj in result["objects"]}
        assert "overview" in categories  # From SKILL.md
        assert "getting started" in categories or "api" in categories  # From references

    def test_package_creates_json(self, tmp_path):
        """Test packaging skill into JSON file."""
        # Create test skill
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\n\nTest content.")

        # Package
        adaptor = get_adaptor("weaviate")
        output_path = adaptor.package(skill_dir, tmp_path)

        # Verify output
        assert output_path.exists()
        assert output_path.suffix == ".json"
        assert "weaviate" in output_path.name

        # Verify content
        with open(output_path) as f:
            result = json.load(f)

        assert isinstance(result, dict)
        assert "objects" in result
        assert len(result["objects"]) > 0
        assert "id" in result["objects"][0]
        assert "properties" in result["objects"][0]

    def test_package_output_filename(self, tmp_path):
        """Test package output filename generation."""
        skill_dir = tmp_path / "react"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# React\n\nReact docs.")

        adaptor = get_adaptor("weaviate")

        # Test directory output
        output_path = adaptor.package(skill_dir, tmp_path)
        assert output_path.name == "react-weaviate.json"

        # Test with .zip extension (should replace)
        output_path = adaptor.package(skill_dir, tmp_path / "test.zip")
        assert output_path.suffix == ".json"
        assert "weaviate" in output_path.name

    def test_upload_returns_message(self, tmp_path):
        """Test upload returns instructions (no actual upload)."""
        # Create test package
        package_path = tmp_path / "test-weaviate.json"
        package_path.write_text("[]")

        adaptor = get_adaptor("weaviate")
        result = adaptor.upload(package_path, "fake-key")

        # Upload may fail if weaviate not installed (expected)
        assert "message" in result
        # Either weaviate not installed, invalid JSON, or connection error
        assert (
            "import weaviate" in result["message"]
            or "Failed to connect" in result["message"]
            or result["success"] is False
        )

    def test_validate_api_key_returns_false(self):
        """Test that API key validation returns False (no API needed)."""
        adaptor = get_adaptor("weaviate")
        assert adaptor.validate_api_key("any-key") is False

    def test_get_env_var_name_returns_empty(self):
        """Test that env var name is empty (no API needed)."""
        adaptor = get_adaptor("weaviate")
        assert adaptor.get_env_var_name() == ""

    def test_supports_enhancement_returns_false(self):
        """Test that enhancement is not supported."""
        adaptor = get_adaptor("weaviate")
        assert adaptor.supports_enhancement() is False

    def test_enhance_returns_false(self, tmp_path):
        """Test that enhance returns False."""
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        adaptor = get_adaptor("weaviate")
        result = adaptor.enhance(skill_dir, "fake-key")

        assert result is False

    def test_empty_skill_directory(self, tmp_path):
        """Test handling of empty skill directory."""
        skill_dir = tmp_path / "empty_skill"
        skill_dir.mkdir()

        adaptor = get_adaptor("weaviate")
        metadata = SkillMetadata(name="empty_skill", description="Empty", version="1.0.0")

        objects_json = adaptor.format_skill_md(skill_dir, metadata)
        result = json.loads(objects_json)

        # Should return structure with empty objects array
        assert "objects" in result
        assert result["objects"] == []

    def test_references_only(self, tmp_path):
        """Test skill with references but no SKILL.md."""
        skill_dir = tmp_path / "refs_only"
        skill_dir.mkdir()

        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "test.md").write_text("# Test\n\nTest content.")

        adaptor = get_adaptor("weaviate")
        metadata = SkillMetadata(name="refs_only", description="Refs only", version="1.0.0")

        objects_json = adaptor.format_skill_md(skill_dir, metadata)
        result = json.loads(objects_json)

        assert len(result["objects"]) == 1
        assert result["objects"][0]["properties"]["category"] == "test"
        assert result["objects"][0]["properties"]["type"] == "reference"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
