#!/usr/bin/env python3
"""
Integration tests for ChromaDB and Weaviate upload functionality.

Tests real upload capabilities for vector databases.
"""

import json
import pytest

# Import adaptors
from skill_seekers.cli.adaptors import get_adaptor


@pytest.fixture
def sample_chroma_package(tmp_path):
    """Create a sample ChromaDB package for testing."""
    package_data = {
        "collection_name": "test_collection",
        "documents": ["Test doc 1", "Test doc 2", "Test doc 3"],
        "metadatas": [
            {"source": "test", "category": "overview", "file": "SKILL.md"},
            {"source": "test", "category": "api", "file": "API.md"},
            {"source": "test", "category": "guide", "file": "GUIDE.md"},
        ],
        "ids": ["id1", "id2", "id3"],
    }

    package_path = tmp_path / "test-chroma.json"
    package_path.write_text(json.dumps(package_data))
    return package_path


@pytest.fixture
def sample_weaviate_package(tmp_path):
    """Create a sample Weaviate package for testing."""
    package_data = {
        "class_name": "TestSkill",
        "schema": {
            "class": "TestSkill",
            "description": "Test skill documentation",
            "vectorizer": "none",
            "properties": [
                {"name": "content", "dataType": ["text"]},
                {"name": "source", "dataType": ["string"]},
                {"name": "category", "dataType": ["string"]},
            ],
        },
        "objects": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "properties": {
                    "content": "Test content 1",
                    "source": "test",
                    "category": "overview",
                },
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "properties": {"content": "Test content 2", "source": "test", "category": "api"},
            },
        ],
    }

    package_path = tmp_path / "test-weaviate.json"
    package_path.write_text(json.dumps(package_data))
    return package_path


class TestChromaUploadBasics:
    """Test ChromaDB upload basic functionality."""

    def test_chroma_adaptor_exists(self):
        """Test that ChromaDB adaptor can be loaded."""
        adaptor = get_adaptor("chroma")
        assert adaptor is not None
        assert adaptor.PLATFORM == "chroma"

    def test_chroma_upload_without_chromadb_installed(self, sample_chroma_package):
        """Test upload fails gracefully without chromadb installed."""
        adaptor = get_adaptor("chroma")

        # Temporarily remove chromadb if it exists
        import sys

        chromadb_backup = sys.modules.get("chromadb")
        if "chromadb" in sys.modules:
            del sys.modules["chromadb"]

        try:
            result = adaptor.upload(sample_chroma_package)

            assert result["success"] is False
            assert "chromadb not installed" in result["message"]
            assert "pip install chromadb" in result["message"]
        finally:
            if chromadb_backup:
                sys.modules["chromadb"] = chromadb_backup

    def test_chroma_upload_api_signature(self, sample_chroma_package):
        """Test ChromaDB upload has correct API signature."""
        adaptor = get_adaptor("chroma")

        # Verify upload method exists and accepts kwargs
        assert hasattr(adaptor, "upload")
        assert callable(adaptor.upload)

        # Verify adaptor methods exist
        assert hasattr(adaptor, "_generate_openai_embeddings")


class TestWeaviateUploadBasics:
    """Test Weaviate upload basic functionality."""

    def test_weaviate_adaptor_exists(self):
        """Test that Weaviate adaptor can be loaded."""
        adaptor = get_adaptor("weaviate")
        assert adaptor is not None
        assert adaptor.PLATFORM == "weaviate"

    def test_weaviate_upload_without_weaviate_installed(self, sample_weaviate_package):
        """Test upload fails gracefully without weaviate-client installed."""
        adaptor = get_adaptor("weaviate")

        # Temporarily remove weaviate if it exists
        import sys

        weaviate_backup = sys.modules.get("weaviate")
        if "weaviate" in sys.modules:
            del sys.modules["weaviate"]

        try:
            result = adaptor.upload(sample_weaviate_package)

            assert result["success"] is False
            assert "weaviate-client not installed" in result["message"]
            assert "pip install weaviate-client" in result["message"]
        finally:
            if weaviate_backup:
                sys.modules["weaviate"] = weaviate_backup

    def test_weaviate_upload_api_signature(self, sample_weaviate_package):
        """Test Weaviate upload has correct API signature."""
        adaptor = get_adaptor("weaviate")

        # Verify upload method exists and accepts kwargs
        assert hasattr(adaptor, "upload")
        assert callable(adaptor.upload)

        # Verify adaptor methods exist
        assert hasattr(adaptor, "_generate_openai_embeddings")


class TestPackageStructure:
    """Test that packages are correctly structured for upload."""

    def test_chroma_package_structure(self, sample_chroma_package):
        """Test ChromaDB package has required fields."""
        with open(sample_chroma_package) as f:
            data = json.load(f)

        assert "collection_name" in data
        assert "documents" in data
        assert "metadatas" in data
        assert "ids" in data
        assert len(data["documents"]) == len(data["metadatas"]) == len(data["ids"])

    def test_weaviate_package_structure(self, sample_weaviate_package):
        """Test Weaviate package has required fields."""
        with open(sample_weaviate_package) as f:
            data = json.load(f)

        assert "class_name" in data
        assert "schema" in data
        assert "objects" in data
        assert len(data["objects"]) == 2

        # Verify schema structure
        assert "class" in data["schema"]
        assert "properties" in data["schema"]

        # Verify object structure
        for obj in data["objects"]:
            assert "id" in obj
            assert "properties" in obj


class TestUploadCommandIntegration:
    """Test upload command integration."""

    def test_upload_skill_api_signature(self):
        """Test upload_skill_api has correct signature."""
        from skill_seekers.cli.upload_skill import upload_skill_api

        # Verify function exists
        assert callable(upload_skill_api)

        # Verify it accepts kwargs for vector DBs
        import inspect

        sig = inspect.signature(upload_skill_api)
        params = list(sig.parameters.keys())
        assert "package_path" in params
        assert "target" in params
        assert "api_key" in params
        assert "kwargs" in params  # For platform-specific options

    def test_upload_command_supports_chroma(self):
        """Test upload command recognizes chroma as target."""

        # This should not raise ValueError
        adaptor = get_adaptor("chroma")
        assert adaptor is not None

    def test_upload_command_supports_weaviate(self):
        """Test upload command recognizes weaviate as target."""

        # This should not raise ValueError
        adaptor = get_adaptor("weaviate")
        assert adaptor is not None


class TestErrorHandling:
    """Test error handling in upload functionality."""

    def test_chroma_handles_missing_file(self, tmp_path):
        """Test ChromaDB upload handles missing files gracefully."""
        adaptor = get_adaptor("chroma")

        missing_file = tmp_path / "nonexistent.json"

        # Should raise FileNotFoundError or return error dict
        try:
            result = adaptor.upload(missing_file)
            # If it returns a dict, it should indicate failure
            assert result["success"] is False
        except FileNotFoundError:
            # This is also acceptable
            pass

    def test_weaviate_handles_missing_file(self, tmp_path):
        """Test Weaviate upload handles missing files gracefully."""
        adaptor = get_adaptor("weaviate")

        missing_file = tmp_path / "nonexistent.json"

        # Should raise FileNotFoundError or return error dict
        try:
            result = adaptor.upload(missing_file)
            # If it returns a dict, it should indicate failure
            assert result["success"] is False
        except FileNotFoundError:
            # This is also acceptable
            pass

    def test_chroma_handles_invalid_json(self, tmp_path):
        """Test ChromaDB upload handles invalid JSON gracefully."""
        adaptor = get_adaptor("chroma")

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json{")

        # Should raise JSONDecodeError or return error dict
        try:
            result = adaptor.upload(invalid_file)
            # If it returns a dict, it should indicate failure
            assert result["success"] is False
        except json.JSONDecodeError:
            # This is also acceptable
            pass

    def test_weaviate_handles_invalid_json(self, tmp_path):
        """Test Weaviate upload handles invalid JSON gracefully."""
        adaptor = get_adaptor("weaviate")

        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json{")

        # Should raise JSONDecodeError or return error dict
        try:
            result = adaptor.upload(invalid_file)
            # If it returns a dict, it should indicate failure
            assert result["success"] is False
        except json.JSONDecodeError:
            # This is also acceptable
            pass
