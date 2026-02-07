#!/usr/bin/env python3
"""
Tests for MCP vector database tools.

Validates the 4 new vector database export tools:
- export_to_weaviate
- export_to_chroma
- export_to_faiss
- export_to_qdrant
"""

import pytest
from pathlib import Path
import sys
import tempfile
import json
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.mcp.tools.vector_db_tools import (
    export_to_weaviate_impl,
    export_to_chroma_impl,
    export_to_faiss_impl,
    export_to_qdrant_impl,
)


def run_async(coro):
    """Helper to run async functions in sync tests."""
    return asyncio.run(coro)


@pytest.fixture
def test_skill_dir():
    """Create a test skill directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()

        # Create SKILL.md
        (skill_dir / "SKILL.md").write_text(
            "# Test Skill\n\n"
            "This is a test skill for vector database export.\n\n"
            "## Getting Started\n\n"
            "Quick start guide content.\n"
        )

        # Create references
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()

        (refs_dir / "api.md").write_text("# API Reference\n\nAPI documentation.")
        (refs_dir / "examples.md").write_text("# Examples\n\nCode examples.")

        yield skill_dir


def test_export_to_weaviate(test_skill_dir):
    """Test Weaviate export tool."""
    output_dir = test_skill_dir.parent

    args = {
        "skill_dir": str(test_skill_dir),
        "output_dir": str(output_dir),
    }

    result = run_async(export_to_weaviate_impl(args))

    # Check result structure
    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], "text")

    # Check result content
    text = result[0].text
    assert "✅ Weaviate Export Complete!" in text
    assert "test_skill-weaviate.json" in text
    assert "weaviate.Client" in text  # Check for usage instructions


def test_export_to_chroma(test_skill_dir):
    """Test Chroma export tool."""
    output_dir = test_skill_dir.parent

    args = {
        "skill_dir": str(test_skill_dir),
        "output_dir": str(output_dir),
    }

    result = run_async(export_to_chroma_impl(args))

    # Check result structure
    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], "text")

    # Check result content
    text = result[0].text
    assert "✅ Chroma Export Complete!" in text
    assert "test_skill-chroma.json" in text
    assert "chromadb" in text  # Check for usage instructions


def test_export_to_faiss(test_skill_dir):
    """Test FAISS export tool."""
    output_dir = test_skill_dir.parent

    args = {
        "skill_dir": str(test_skill_dir),
        "output_dir": str(output_dir),
    }

    result = run_async(export_to_faiss_impl(args))

    # Check result structure
    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], "text")

    # Check result content
    text = result[0].text
    assert "✅ FAISS Export Complete!" in text
    assert "test_skill-faiss.json" in text
    assert "import faiss" in text  # Check for usage instructions


def test_export_to_qdrant(test_skill_dir):
    """Test Qdrant export tool."""
    output_dir = test_skill_dir.parent

    args = {
        "skill_dir": str(test_skill_dir),
        "output_dir": str(output_dir),
    }

    result = run_async(export_to_qdrant_impl(args))

    # Check result structure
    assert isinstance(result, list)
    assert len(result) == 1
    assert hasattr(result[0], "text")

    # Check result content
    text = result[0].text
    assert "✅ Qdrant Export Complete!" in text
    assert "test_skill-qdrant.json" in text
    assert "QdrantClient" in text  # Check for usage instructions


def test_export_with_default_output_dir(test_skill_dir):
    """Test export with default output directory."""
    args = {"skill_dir": str(test_skill_dir)}

    # Should use parent directory as default
    result = run_async(export_to_weaviate_impl(args))

    assert isinstance(result, list)
    assert len(result) == 1
    text = result[0].text
    assert "✅" in text
    assert "test_skill-weaviate.json" in text


def test_export_missing_skill_dir():
    """Test export with missing skill directory."""
    args = {"skill_dir": "/nonexistent/path"}

    result = run_async(export_to_weaviate_impl(args))

    assert isinstance(result, list)
    assert len(result) == 1
    text = result[0].text
    assert "❌ Error" in text
    assert "not found" in text


def test_all_exports_create_files(test_skill_dir):
    """Test that all export tools create output files."""
    output_dir = test_skill_dir.parent

    # Test all 4 exports
    exports = [
        ("weaviate", export_to_weaviate_impl),
        ("chroma", export_to_chroma_impl),
        ("faiss", export_to_faiss_impl),
        ("qdrant", export_to_qdrant_impl),
    ]

    for target, export_func in exports:
        args = {
            "skill_dir": str(test_skill_dir),
            "output_dir": str(output_dir),
        }

        result = run_async(export_func(args))

        # Check success
        assert isinstance(result, list)
        text = result[0].text
        assert "✅" in text

        # Check file exists
        expected_file = output_dir / f"test_skill-{target}.json"
        assert expected_file.exists(), f"{target} export file not created"

        # Check file content is valid JSON
        with open(expected_file) as f:
            data = json.load(f)
            assert isinstance(data, dict)


def test_export_output_includes_instructions():
    """Test that export outputs include usage instructions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Test")

        # Create minimal references
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "guide.md").write_text("# Guide")

        args = {"skill_dir": str(skill_dir)}

        # Test Weaviate includes instructions
        result = run_async(export_to_weaviate_impl(args))
        text = result[0].text
        assert "Next Steps:" in text
        assert "Upload to Weaviate:" in text
        assert "Query with hybrid search:" in text
        assert "Resources:" in text

        # Test Chroma includes instructions
        result = run_async(export_to_chroma_impl(args))
        text = result[0].text
        assert "Next Steps:" in text
        assert "Load into Chroma:" in text
        assert "Query the collection:" in text

        # Test FAISS includes instructions
        result = run_async(export_to_faiss_impl(args))
        text = result[0].text
        assert "Next Steps:" in text
        assert "Build FAISS index:" in text
        assert "Search:" in text

        # Test Qdrant includes instructions
        result = run_async(export_to_qdrant_impl(args))
        text = result[0].text
        assert "Next Steps:" in text
        assert "Upload to Qdrant:" in text
        assert "Search with filters:" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
