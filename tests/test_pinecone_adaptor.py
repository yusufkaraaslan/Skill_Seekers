#!/usr/bin/env python3
"""
Tests for Pinecone adaptor and doc_version metadata flow.
"""

import json

import pytest

from skill_seekers.cli.adaptors.base import SkillMetadata


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_skill_dir(tmp_path):
    """Create a minimal skill directory with SKILL.md and references."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    skill_md = """---
name: test-skill
description: A test skill for pinecone
doc_version: 16.2
---

# Test Skill

This is a test skill for Pinecone adaptor testing.

## Quick Start

Get started quickly.
"""
    (skill_dir / "SKILL.md").write_text(skill_md)

    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "api_reference.md").write_text("# API Reference\n\nSome API docs.\n")
    (refs_dir / "getting_started.md").write_text(
        "# Getting Started\n\nSome getting started docs.\n"
    )

    return skill_dir


@pytest.fixture
def sample_skill_dir_no_doc_version(tmp_path):
    """Create a skill directory without doc_version in frontmatter."""
    skill_dir = tmp_path / "no-version-skill"
    skill_dir.mkdir()

    skill_md = """---
name: no-version-skill
description: A test skill without doc_version
---

# No Version Skill

Content here.
"""
    (skill_dir / "SKILL.md").write_text(skill_md)

    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "api.md").write_text("# API\n\nAPI docs.\n")

    return skill_dir


# ---------------------------------------------------------------------------
# Pinecone Adaptor Tests
# ---------------------------------------------------------------------------


class TestPineconeAdaptor:
    """Test Pinecone adaptor functionality."""

    def test_import(self):
        """PineconeAdaptor can be imported."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        assert PineconeAdaptor is not None

    def test_platform_constants(self):
        """Platform constants are set correctly."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        assert adaptor.PLATFORM == "pinecone"
        assert adaptor.PLATFORM_NAME == "Pinecone (Vector Database)"
        assert adaptor.DEFAULT_API_ENDPOINT is None

    def test_registered_in_factory(self):
        """PineconeAdaptor is registered in the adaptor factory."""
        from skill_seekers.cli.adaptors import ADAPTORS

        assert "pinecone" in ADAPTORS

    def test_get_adaptor(self):
        """get_adaptor('pinecone') returns PineconeAdaptor instance."""
        from skill_seekers.cli.adaptors import get_adaptor
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = get_adaptor("pinecone")
        assert isinstance(adaptor, PineconeAdaptor)

    def test_format_skill_md_structure(self, sample_skill_dir):
        """format_skill_md returns valid JSON with expected structure."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        metadata = SkillMetadata(
            name="test-skill",
            description="Test skill",
            version="1.0.0",
            doc_version="16.2",
        )
        result = adaptor.format_skill_md(sample_skill_dir, metadata)
        data = json.loads(result)

        assert "index_name" in data
        assert "namespace" in data
        assert "dimension" in data
        assert "metric" in data
        assert "vectors" in data
        assert data["dimension"] == 1536
        assert data["metric"] == "cosine"

    def test_format_skill_md_vectors_have_metadata(self, sample_skill_dir):
        """Each vector has id and metadata fields."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        metadata = SkillMetadata(
            name="test-skill",
            description="Test",
            doc_version="16.2",
        )
        result = adaptor.format_skill_md(sample_skill_dir, metadata)
        data = json.loads(result)

        assert len(data["vectors"]) > 0
        for vec in data["vectors"]:
            assert "id" in vec
            assert "metadata" in vec
            assert "text" in vec["metadata"]
            assert "source" in vec["metadata"]
            assert "category" in vec["metadata"]
            assert "file" in vec["metadata"]
            assert "type" in vec["metadata"]
            assert "version" in vec["metadata"]
            assert "doc_version" in vec["metadata"]

    def test_format_skill_md_doc_version_propagates(self, sample_skill_dir):
        """doc_version flows into every vector's metadata."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        metadata = SkillMetadata(
            name="test-skill",
            description="Test",
            doc_version="16.2",
        )
        result = adaptor.format_skill_md(sample_skill_dir, metadata)
        data = json.loads(result)

        for vec in data["vectors"]:
            assert vec["metadata"]["doc_version"] == "16.2"

    def test_format_skill_md_empty_doc_version(self, sample_skill_dir):
        """Empty doc_version is preserved as empty string."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        metadata = SkillMetadata(name="test-skill", description="Test", doc_version="")
        result = adaptor.format_skill_md(sample_skill_dir, metadata)
        data = json.loads(result)

        for vec in data["vectors"]:
            assert vec["metadata"]["doc_version"] == ""

    def test_format_skill_md_has_overview_and_references(self, sample_skill_dir):
        """Output includes overview (SKILL.md) and reference documents."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        metadata = SkillMetadata(name="test-skill", description="Test")
        result = adaptor.format_skill_md(sample_skill_dir, metadata)
        data = json.loads(result)

        categories = {vec["metadata"]["category"] for vec in data["vectors"]}
        types = {vec["metadata"]["type"] for vec in data["vectors"]}
        assert "overview" in categories
        assert "documentation" in types
        assert "reference" in types

    def test_package_creates_file(self, sample_skill_dir, tmp_path):
        """package() creates a JSON file at expected path."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        output_path = adaptor.package(sample_skill_dir, tmp_path)

        assert output_path.exists()
        assert output_path.name.endswith("-pinecone.json")

        data = json.loads(output_path.read_text())
        assert "vectors" in data
        assert len(data["vectors"]) > 0

    def test_package_reads_frontmatter_metadata(self, sample_skill_dir, tmp_path):
        """package() reads doc_version from SKILL.md frontmatter."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        output_path = adaptor.package(sample_skill_dir, tmp_path)

        data = json.loads(output_path.read_text())
        for vec in data["vectors"]:
            assert vec["metadata"]["doc_version"] == "16.2"

    def test_package_with_chunking(self, sample_skill_dir, tmp_path):
        """package() with chunking enabled produces valid output."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        output_path = adaptor.package(
            sample_skill_dir, tmp_path, enable_chunking=True, chunk_max_tokens=64
        )

        data = json.loads(output_path.read_text())
        assert "vectors" in data
        assert len(data["vectors"]) > 0

    def test_index_name_derived_from_skill_name(self, sample_skill_dir, tmp_path):
        """index_name and namespace are derived from skill directory name."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        output_path = adaptor.package(sample_skill_dir, tmp_path)

        data = json.loads(output_path.read_text())
        assert data["index_name"] == "test-skill"
        assert data["namespace"] == "test-skill"

    def test_no_values_field_in_vectors(self, sample_skill_dir, tmp_path):
        """Vectors have no 'values' field — embeddings are added at upload time."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        output_path = adaptor.package(sample_skill_dir, tmp_path)

        data = json.loads(output_path.read_text())
        for vec in data["vectors"]:
            assert "values" not in vec

    def test_text_truncation(self):
        """_truncate_text_for_metadata respects byte limit."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        # Short text should not be truncated
        assert adaptor._truncate_text_for_metadata("hello") == "hello"

        # Very long text should be truncated
        long_text = "x" * 50000
        truncated = adaptor._truncate_text_for_metadata(long_text)
        assert len(truncated.encode("utf-8")) <= 40000

    def test_validate_api_key_returns_false(self):
        """validate_api_key returns False (no key needed for packaging)."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        assert adaptor.validate_api_key("some-key") is False

    def test_get_env_var_name(self):
        """get_env_var_name returns PINECONE_API_KEY."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        assert adaptor.get_env_var_name() == "PINECONE_API_KEY"

    def test_supports_enhancement_false(self):
        """Pinecone doesn't support enhancement."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        assert adaptor.supports_enhancement() is False

    def test_upload_without_pinecone_installed(self, tmp_path):
        """upload() returns helpful error when pinecone not installed."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        # Create a dummy package file
        pkg = tmp_path / "test-pinecone.json"
        pkg.write_text(json.dumps({"vectors": [], "index_name": "test", "namespace": "test"}))

        # This will either work (if pinecone is installed) or return error
        result = adaptor.upload(pkg)
        # Without API key, should fail
        assert result["success"] is False

    def _make_mock_pinecone(self, monkeypatch):
        """Helper: stub the pinecone module so upload() can run without a real server."""
        import sys
        import types
        from unittest.mock import MagicMock

        mock_module = types.ModuleType("pinecone")
        mock_index = MagicMock()
        mock_pc = MagicMock()
        mock_pc.list_indexes.return_value = []  # no existing indexes
        mock_pc.Index.return_value = mock_index
        mock_module.Pinecone = MagicMock(return_value=mock_pc)
        mock_module.ServerlessSpec = MagicMock()
        monkeypatch.setitem(sys.modules, "pinecone", mock_module)
        return mock_pc, mock_index

    def _make_package(self, tmp_path, vectors=None):
        """Helper: create a minimal Pinecone package JSON."""
        if vectors is None:
            vectors = [{"id": "a", "metadata": {"text": "hello world"}}]
        pkg = tmp_path / "test-pinecone.json"
        pkg.write_text(
            json.dumps(
                {
                    "vectors": vectors,
                    "index_name": "test",
                    "namespace": "test",
                    "metric": "cosine",
                    "dimension": 1536,
                }
            )
        )
        return pkg

    def test_upload_success_has_url_key(self, tmp_path, monkeypatch):
        """upload() success return dict includes 'url' key (prevents KeyError in package_skill.py)."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        mock_pc, _mock_index = self._make_mock_pinecone(monkeypatch)
        monkeypatch.setattr(
            adaptor,
            "_generate_openai_embeddings",
            lambda docs: [[0.0] * 1536] * len(docs),
        )
        pkg = self._make_package(tmp_path)

        result = adaptor.upload(pkg, api_key="fake-key")
        assert result["success"] is True
        assert "url" in result  # key must exist to avoid KeyError in package_skill.py
        # Value should be None for Pinecone (no web URL)
        assert result["url"] is None

    def test_embedding_dimension_autodetect_st(self, tmp_path, monkeypatch):
        """sentence-transformers upload creates index with dimension=384."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        mock_pc, _mock_index = self._make_mock_pinecone(monkeypatch)
        monkeypatch.setattr(
            adaptor,
            "_generate_st_embeddings",
            lambda docs: [[0.0] * 384] * len(docs),
        )
        pkg = self._make_package(tmp_path)

        result = adaptor.upload(
            pkg,
            api_key="fake-key",
            embedding_function="sentence-transformers",
        )
        assert result["success"] is True
        # Verify create_index was called with dimension=384
        mock_pc.create_index.assert_called_once()
        call_kwargs = mock_pc.create_index.call_args
        assert call_kwargs.kwargs["dimension"] == 384

    def test_embedding_dimension_autodetect_openai(self, tmp_path, monkeypatch):
        """openai upload creates index with dimension=1536."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        mock_pc, _mock_index = self._make_mock_pinecone(monkeypatch)
        monkeypatch.setattr(
            adaptor,
            "_generate_openai_embeddings",
            lambda docs: [[0.0] * 1536] * len(docs),
        )
        pkg = self._make_package(tmp_path)

        result = adaptor.upload(
            pkg,
            api_key="fake-key",
            embedding_function="openai",
        )
        assert result["success"] is True
        mock_pc.create_index.assert_called_once()
        call_kwargs = mock_pc.create_index.call_args
        assert call_kwargs.kwargs["dimension"] == 1536

    def test_embedding_before_index_creation(self, tmp_path, monkeypatch):
        """If embedding generation fails, index is never created (no side-effects)."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        mock_pc, _mock_index = self._make_mock_pinecone(monkeypatch)

        def fail_embeddings(_docs):
            raise RuntimeError("OPENAI_API_KEY not set")

        monkeypatch.setattr(adaptor, "_generate_openai_embeddings", fail_embeddings)
        pkg = self._make_package(tmp_path)

        result = adaptor.upload(pkg, api_key="fake-key")
        assert result["success"] is False
        # Index must NOT have been created since embedding failed first
        mock_pc.create_index.assert_not_called()

    def test_embedding_dimension_explicit_override(self, tmp_path, monkeypatch):
        """Explicit dimension kwarg overrides both auto-detect and JSON file value."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        mock_pc, _mock_index = self._make_mock_pinecone(monkeypatch)
        monkeypatch.setattr(
            adaptor,
            "_generate_openai_embeddings",
            lambda docs: [[0.0] * 768] * len(docs),
        )
        pkg = self._make_package(tmp_path)

        result = adaptor.upload(
            pkg,
            api_key="fake-key",
            embedding_function="openai",
            dimension=768,
        )
        assert result["success"] is True
        mock_pc.create_index.assert_called_once()
        call_kwargs = mock_pc.create_index.call_args
        assert call_kwargs.kwargs["dimension"] == 768

    def test_deterministic_ids(self, sample_skill_dir):
        """IDs are deterministic — same input produces same ID."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        metadata = SkillMetadata(name="test-skill", description="Test")

        result1 = adaptor.format_skill_md(sample_skill_dir, metadata)
        result2 = adaptor.format_skill_md(sample_skill_dir, metadata)

        data1 = json.loads(result1)
        data2 = json.loads(result2)

        ids1 = [v["id"] for v in data1["vectors"]]
        ids2 = [v["id"] for v in data2["vectors"]]
        assert ids1 == ids2


# ---------------------------------------------------------------------------
# doc_version Metadata Tests (cross-adaptor)
# ---------------------------------------------------------------------------


class TestDocVersionMetadata:
    """Test doc_version flows through all RAG adaptors."""

    def test_skill_metadata_has_doc_version(self):
        """SkillMetadata dataclass has doc_version field."""
        meta = SkillMetadata(name="test", description="test", doc_version="3.2")
        assert meta.doc_version == "3.2"

    def test_skill_metadata_doc_version_default_empty(self):
        """doc_version defaults to empty string."""
        meta = SkillMetadata(name="test", description="test")
        assert meta.doc_version == ""

    def test_read_frontmatter(self, sample_skill_dir):
        """_read_frontmatter reads doc_version from SKILL.md."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        fm = adaptor._read_frontmatter(sample_skill_dir)
        assert fm["doc_version"] == "16.2"
        assert fm["name"] == "test-skill"

    def test_read_frontmatter_missing(self, sample_skill_dir_no_doc_version):
        """_read_frontmatter returns empty string when doc_version is absent."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        fm = adaptor._read_frontmatter(sample_skill_dir_no_doc_version)
        assert fm.get("doc_version") is None  # key not present

    def test_build_skill_metadata_reads_doc_version(self, sample_skill_dir):
        """_build_skill_metadata populates doc_version from frontmatter."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        meta = adaptor._build_skill_metadata(sample_skill_dir)
        assert meta.doc_version == "16.2"
        assert meta.name == "test-skill"

    def test_build_skill_metadata_no_doc_version(self, sample_skill_dir_no_doc_version):
        """_build_skill_metadata defaults to empty string when frontmatter has no doc_version."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        meta = adaptor._build_skill_metadata(sample_skill_dir_no_doc_version)
        assert meta.doc_version == ""

    def test_build_metadata_dict_includes_doc_version(self):
        """_build_metadata_dict includes doc_version in output."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        meta = SkillMetadata(name="test", description="desc", doc_version="3.0")
        result = adaptor._build_metadata_dict(meta)
        assert "doc_version" in result
        assert result["doc_version"] == "3.0"

    def test_build_metadata_dict_empty_doc_version(self):
        """_build_metadata_dict preserves empty doc_version."""
        from skill_seekers.cli.adaptors.pinecone_adaptor import PineconeAdaptor

        adaptor = PineconeAdaptor()
        meta = SkillMetadata(name="test", description="desc")
        result = adaptor._build_metadata_dict(meta)
        assert "doc_version" in result
        assert result["doc_version"] == ""

    @pytest.mark.parametrize(
        "platform",
        ["chroma", "faiss", "langchain", "llama-index", "haystack", "pinecone"],
    )
    def test_doc_version_in_package_output(self, platform, sample_skill_dir, tmp_path):
        """doc_version appears in package output for all RAG adaptors."""
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor(platform)
        output_path = adaptor.package(sample_skill_dir, tmp_path)

        data = json.loads(output_path.read_text())

        # Each adaptor has a different structure — extract metadata dicts
        meta_list = _extract_metadata_from_package(platform, data)
        assert len(meta_list) > 0, f"No metadata found in {platform} output"

        for meta in meta_list:
            assert "doc_version" in meta, f"doc_version missing in {platform} metadata: {meta}"
            assert meta["doc_version"] == "16.2", (
                f"doc_version mismatch in {platform}: expected '16.2', got '{meta['doc_version']}'"
            )

    @pytest.mark.parametrize(
        "platform",
        ["chroma", "faiss", "langchain", "llama-index", "haystack", "pinecone"],
    )
    def test_empty_doc_version_in_package_output(
        self, platform, sample_skill_dir_no_doc_version, tmp_path
    ):
        """Empty doc_version is preserved (not omitted) in all adaptors."""
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor(platform)
        output_path = adaptor.package(sample_skill_dir_no_doc_version, tmp_path)

        data = json.loads(output_path.read_text())
        meta_list = _extract_metadata_from_package(platform, data)
        assert len(meta_list) > 0

        for meta in meta_list:
            assert "doc_version" in meta


# Qdrant and Weaviate may not be installed — test separately if available
class TestDocVersionQdrant:
    """Test doc_version in Qdrant adaptor (may require qdrant client)."""

    def test_qdrant_doc_version(self, sample_skill_dir, tmp_path):
        from skill_seekers.cli.adaptors import ADAPTORS

        if "qdrant" not in ADAPTORS:
            pytest.skip("Qdrant adaptor not available")
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor("qdrant")
        output_path = adaptor.package(sample_skill_dir, tmp_path)
        data = json.loads(output_path.read_text())

        for point in data["points"]:
            assert "doc_version" in point["payload"]
            assert point["payload"]["doc_version"] == "16.2"


class TestWeaviateUploadReturnKeys:
    """Test Weaviate upload() return dict has required keys."""

    def test_weaviate_upload_success_has_url_key(self, sample_skill_dir, tmp_path, monkeypatch):
        """Weaviate upload() success return includes 'url' key (prevents KeyError in package_skill.py)."""
        import sys
        import types
        from unittest.mock import MagicMock

        from skill_seekers.cli.adaptors import ADAPTORS

        if "weaviate" not in ADAPTORS:
            pytest.skip("Weaviate adaptor not available")

        from skill_seekers.cli.adaptors.weaviate import WeaviateAdaptor

        adaptor = WeaviateAdaptor()

        # Stub the weaviate module
        mock_module = types.ModuleType("weaviate")
        mock_client = MagicMock()
        mock_client.is_ready.return_value = True
        mock_module.Client = MagicMock(return_value=mock_client)
        mock_module.AuthApiKey = MagicMock()
        monkeypatch.setitem(sys.modules, "weaviate", mock_module)

        # Create a minimal weaviate package
        output_path = adaptor.package(sample_skill_dir, tmp_path)
        result = adaptor.upload(output_path)

        assert result["success"] is True
        assert "url" in result
        assert result["url"] is None


class TestDocVersionWeaviate:
    """Test doc_version in Weaviate adaptor (may require weaviate client)."""

    def test_weaviate_doc_version(self, sample_skill_dir, tmp_path):
        from skill_seekers.cli.adaptors import ADAPTORS

        if "weaviate" not in ADAPTORS:
            pytest.skip("Weaviate adaptor not available")
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor("weaviate")
        output_path = adaptor.package(sample_skill_dir, tmp_path)
        data = json.loads(output_path.read_text())

        for obj in data["objects"]:
            assert "doc_version" in obj["properties"]
            assert obj["properties"]["doc_version"] == "16.2"

    def test_weaviate_schema_includes_doc_version(self, sample_skill_dir, tmp_path):
        from skill_seekers.cli.adaptors import ADAPTORS

        if "weaviate" not in ADAPTORS:
            pytest.skip("Weaviate adaptor not available")
        from skill_seekers.cli.adaptors import get_adaptor

        adaptor = get_adaptor("weaviate")
        output_path = adaptor.package(sample_skill_dir, tmp_path)
        data = json.loads(output_path.read_text())

        property_names = [p["name"] for p in data["schema"]["properties"]]
        assert "doc_version" in property_names


# ---------------------------------------------------------------------------
# CLI Flag Tests
# ---------------------------------------------------------------------------


class TestDocVersionCLIFlag:
    """Test --doc-version CLI flag is accepted."""

    def test_common_arguments_has_doc_version(self):
        """COMMON_ARGUMENTS includes doc_version."""
        from skill_seekers.cli.arguments.common import COMMON_ARGUMENTS

        assert "doc_version" in COMMON_ARGUMENTS

    def test_create_arguments_has_doc_version(self):
        """UNIVERSAL_ARGUMENTS includes doc_version."""
        from skill_seekers.cli.arguments.create import UNIVERSAL_ARGUMENTS

        assert "doc_version" in UNIVERSAL_ARGUMENTS

    def test_doc_version_flag_parsed(self):
        """--doc-version is parsed correctly by argparse."""
        import argparse
        from skill_seekers.cli.arguments.common import add_common_arguments

        parser = argparse.ArgumentParser()
        add_common_arguments(parser)
        args = parser.parse_args(["--doc-version", "16.2"])
        assert args.doc_version == "16.2"

    def test_doc_version_default_empty(self):
        """--doc-version defaults to empty string."""
        import argparse
        from skill_seekers.cli.arguments.common import add_common_arguments

        parser = argparse.ArgumentParser()
        add_common_arguments(parser)
        args = parser.parse_args([])
        assert args.doc_version == ""


# ---------------------------------------------------------------------------
# Package choices test
# ---------------------------------------------------------------------------


class TestPineconeInPackageChoices:
    """Test pinecone is in package CLI choices."""

    def test_pinecone_in_package_arguments(self):
        """pinecone is listed in package --target choices."""
        from skill_seekers.cli.arguments.package import PACKAGE_ARGUMENTS

        choices = PACKAGE_ARGUMENTS["target"]["kwargs"]["choices"]
        assert "pinecone" in choices


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_metadata_from_package(platform: str, data: dict) -> list[dict]:
    """Extract metadata dicts from adaptor-specific package format."""
    meta_list = []

    if platform == "pinecone":
        for vec in data.get("vectors", []):
            meta_list.append(vec.get("metadata", {}))
    elif platform == "chroma":
        for meta in data.get("metadatas", []):
            meta_list.append(meta)
    elif platform == "faiss":
        for meta in data.get("metadatas", []):
            meta_list.append(meta)
    elif platform == "langchain":
        for doc in data if isinstance(data, list) else []:
            meta_list.append(doc.get("metadata", {}))
    elif platform == "llama-index":
        for node in data if isinstance(data, list) else []:
            meta_list.append(node.get("metadata", {}))
    elif platform == "haystack":
        for doc in data if isinstance(data, list) else []:
            meta_list.append(doc.get("meta", {}))
    elif platform == "qdrant":
        for point in data.get("points", []):
            meta_list.append(point.get("payload", {}))
    elif platform == "weaviate":
        for obj in data.get("objects", []):
            meta_list.append(obj.get("properties", {}))

    return meta_list
