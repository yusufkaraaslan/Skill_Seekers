#!/usr/bin/env python3
"""
Tests for Qdrant Adaptor
"""

import json

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata


class TestQdrantAdaptor:
    """Test suite for QdrantAdaptor class."""

    def test_adaptor_registration(self):
        """Test that Qdrant adaptor is registered."""
        adaptor = get_adaptor("qdrant")
        assert adaptor.PLATFORM == "qdrant"
        assert adaptor.PLATFORM_NAME == "Qdrant Vector Database"

    def test_format_skill_md(self, tmp_path):
        """Test formatting SKILL.md as Qdrant points."""
        # Create test skill directory
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Test Skill\n\nThis is a test skill for Qdrant format.")

        # Create references directory with files
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "getting_started.md").write_text("# Getting Started\n\nQuick start.")
        (refs_dir / "api.md").write_text("# API Reference\n\nAPI docs.")

        # Format as Qdrant points
        adaptor = get_adaptor("qdrant")
        metadata = SkillMetadata(name="test_skill", description="Test skill", version="1.0.0")

        points_json = adaptor.format_skill_md(skill_dir, metadata)

        # Parse and validate
        result = json.loads(points_json)

        assert "collection_name" in result
        assert "points" in result
        assert "config" in result
        assert len(result["points"]) == 3  # SKILL.md + 2 references

        # Check point structure
        for point in result["points"]:
            assert "id" in point
            assert "vector" in point  # Will be None - user needs to add embeddings
            assert "payload" in point
            payload = point["payload"]
            assert "content" in payload
            assert payload["source"] == "test_skill"
            assert payload["version"] == "1.0.0"
            assert "category" in payload
            assert "file" in payload
            assert "type" in payload

        # Check categories
        categories = {point["payload"]["category"] for point in result["points"]}
        assert "overview" in categories  # From SKILL.md
        assert "getting started" in categories or "api" in categories  # From references

    def test_package_creates_json(self, tmp_path):
        """Test packaging skill into JSON file."""
        # Create test skill
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test\n\nTest content.")

        # Package
        adaptor = get_adaptor("qdrant")
        output_path = adaptor.package(skill_dir, tmp_path)

        # Verify output
        assert output_path.exists()
        assert output_path.suffix == ".json"
        assert "qdrant" in output_path.name

        # Verify content
        with open(output_path) as f:
            result = json.load(f)

        assert isinstance(result, dict)
        assert "points" in result
        assert len(result["points"]) > 0
        assert "id" in result["points"][0]
        assert "payload" in result["points"][0]

    def test_package_output_filename(self, tmp_path):
        """Test package output filename generation."""
        skill_dir = tmp_path / "react"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# React\n\nReact docs.")

        adaptor = get_adaptor("qdrant")

        # Test directory output
        output_path = adaptor.package(skill_dir, tmp_path)
        assert output_path.name == "react-qdrant.json"

        # Test with .zip extension (should replace)
        output_path = adaptor.package(skill_dir, tmp_path / "test.zip")
        assert output_path.suffix == ".json"
        assert "qdrant" in output_path.name

    def test_upload_returns_message(self, tmp_path):
        """Test upload returns instructions (no actual upload)."""
        # Create test package
        package_path = tmp_path / "test-qdrant.json"
        package_path.write_text("[]")

        adaptor = get_adaptor("qdrant")
        result = adaptor.upload(package_path, "fake-key")

        assert result["success"] is False  # No upload capability
        assert result["skill_id"] is None
        assert "message" in result
        assert "from qdrant_client" in result["message"]

    def test_validate_api_key_returns_false(self):
        """Test that API key validation returns False (no API needed)."""
        adaptor = get_adaptor("qdrant")
        assert adaptor.validate_api_key("any-key") is False

    def test_get_env_var_name_returns_empty(self):
        """Test that env var name is QDRANT_API_KEY (optional for Qdrant Cloud)."""
        adaptor = get_adaptor("qdrant")
        assert adaptor.get_env_var_name() == "QDRANT_API_KEY"

    def test_supports_enhancement_returns_false(self):
        """Test that enhancement is not supported."""
        adaptor = get_adaptor("qdrant")
        assert adaptor.supports_enhancement() is False

    def test_enhance_returns_false(self, tmp_path):
        """Test that enhance returns False."""
        skill_dir = tmp_path / "test_skill"
        skill_dir.mkdir()

        adaptor = get_adaptor("qdrant")
        result = adaptor.enhance(skill_dir, "fake-key")

        assert result is False

    def test_empty_skill_directory(self, tmp_path):
        """Test handling of empty skill directory."""
        skill_dir = tmp_path / "empty_skill"
        skill_dir.mkdir()

        adaptor = get_adaptor("qdrant")
        metadata = SkillMetadata(name="empty_skill", description="Empty", version="1.0.0")

        points_json = adaptor.format_skill_md(skill_dir, metadata)
        result = json.loads(points_json)

        # Should return structure with empty points array
        assert "points" in result
        assert result["points"] == []

    def test_references_only(self, tmp_path):
        """Test skill with references but no SKILL.md."""
        skill_dir = tmp_path / "refs_only"
        skill_dir.mkdir()

        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "test.md").write_text("# Test\n\nTest content.")

        adaptor = get_adaptor("qdrant")
        metadata = SkillMetadata(name="refs_only", description="Refs only", version="1.0.0")

        points_json = adaptor.format_skill_md(skill_dir, metadata)
        result = json.loads(points_json)

        assert len(result["points"]) == 1
        assert result["points"][0]["payload"]["category"] == "test"
        assert result["points"][0]["payload"]["type"] == "reference"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
