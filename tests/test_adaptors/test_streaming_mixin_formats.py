#!/usr/bin/env python3
"""
Regression tests: streaming packages must match each adaptor's upload format.

Adding StreamingAdaptorMixin to the 8 RAG adaptors flipped package_skill.py's
`hasattr(adaptor, "package_streaming")` gate, but the mixin's generic default
_convert_chunks_to_platform_format emitted {skill_name, documents, metadatas,
ids, total_chunks, streaming} — which did NOT match what several adaptors'
upload() reads (weaviate reads data["schema"]/data["objects"]/data["class_name"]
-> "Schema creation failed: 'schema'"; pinecone reads data["vectors"] ->
"'vectors'"). Each adaptor now overrides _convert_chunks_to_platform_format to
emit its own native package schema. These tests feed sample chunks (shaped
exactly like StreamingIngester.stream_skill_directory yields) through each
converter and assert the keys its own upload() — or the documented import
snippet embedded in upload()'s message — reads.
"""

import json
import re

import pytest

import skill_seekers.cli.adaptors.streaming_adaptor as streaming_adaptor
from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.streaming_adaptor import StreamingAdaptorMixin

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

RAG_PLATFORMS = [
    "langchain",
    "llama-index",
    "haystack",
    "weaviate",
    "chroma",
    "faiss",
    "qdrant",
    "pinecone",
]


def _chunk(text, file, category, idx, total):
    """One (chunk_text, chunk_meta) tuple shaped exactly like
    StreamingIngester.stream_skill_directory yields."""
    return (
        text,
        {
            "content": text,
            "chunk_id": f"{idx:032x}",
            "source": "my_skill",
            "category": category,
            "file": file,
            "chunk_index": idx,
            "total_chunks": total,
            "char_start": idx * 100,
            "char_end": idx * 100 + len(text),
        },
    )


@pytest.fixture
def sample_chunks():
    return [
        _chunk("# My Skill\n\nOverview text.", "SKILL.md", "overview", 0, 1),
        _chunk("# API\n\nReference text.", "api.md", "api", 1, 2),
        _chunk("More reference text.", "api.md", "api", 2, 2),
    ]


def test_all_rag_adaptors_override_chunk_converter():
    """The mixin's generic default format is not consumable by any registered
    RAG adaptor's upload() — every one must provide its own converter."""
    for platform in RAG_PLATFORMS:
        adaptor = get_adaptor(platform)
        assert (
            type(adaptor)._convert_chunks_to_platform_format
            is not StreamingAdaptorMixin._convert_chunks_to_platform_format
        ), platform


def test_streaming_mixin_does_not_export_dead_example_adaptors():
    """The real adaptors own platform conversion; the old standalone examples
    should not remain as unused module-level classes."""
    assert not hasattr(streaming_adaptor, "StreamingLangChainAdaptor")
    assert not hasattr(streaming_adaptor, "StreamingChromaAdaptor")


class TestWeaviateStreamingFormat:
    """upload() reads data["schema"], data["class_name"], and
    obj["id"]/obj["properties"] for each object (weaviate.py upload)."""

    def test_keys_upload_reads(self, sample_chunks):
        data = get_adaptor("weaviate")._convert_chunks_to_platform_format(sample_chunks, "my_skill")

        # client.schema.create_class(data["schema"]) — the exact read that
        # failed with "Schema creation failed: 'schema'" on the default format
        assert data["schema"]["class"] == "MySkill"
        assert data["class_name"] == "MySkill"

        assert len(data["objects"]) == 3
        for obj in data["objects"]:
            # batch.add_data_object(data_object=obj["properties"], uuid=obj["id"])
            assert UUID_RE.match(obj["id"]), "Weaviate requires RFC 4122 UUIDs"
            assert obj["properties"]["content"]
            assert obj["properties"]["source"] == "my_skill"

        files = [o["properties"]["file"] for o in data["objects"]]
        assert files == ["SKILL.md", "api.md", "api.md"]
        types = [o["properties"]["type"] for o in data["objects"]]
        assert types == ["documentation", "reference", "reference"]


class TestPineconeStreamingFormat:
    """upload() reads data["vectors"] (vec["id"], vec["metadata"]["text"]) and
    data.get("index_name"/"namespace"/"metric"/"dimension")."""

    def test_keys_upload_reads(self, sample_chunks):
        data = get_adaptor("pinecone")._convert_chunks_to_platform_format(sample_chunks, "my_skill")

        # texts = [vec["metadata"]["text"] for vec in data["vectors"]] — the
        # exact read that failed with "'vectors'" on the default format
        texts = [vec["metadata"]["text"] for vec in data["vectors"]]
        assert texts[0].startswith("# My Skill")
        assert len(texts) == 3

        for vec in data["vectors"]:
            assert vec["id"]
            # full text must not be duplicated in metadata (40 KB limit)
            assert "content" not in vec["metadata"]

        assert data["index_name"] == "my-skill"
        assert data["namespace"] == "my-skill"
        assert data["metric"] == "cosine"
        assert data["dimension"] == 1536


class TestChromaStreamingFormat:
    """upload() reads collection.add(documents=data["documents"],
    metadatas=data["metadatas"], ids=data["ids"]) and data.get("collection_name")."""

    def test_keys_upload_reads(self, sample_chunks):
        data = get_adaptor("chroma")._convert_chunks_to_platform_format(sample_chunks, "my_skill")

        assert len(data["documents"]) == len(data["metadatas"]) == len(data["ids"]) == 3
        assert data["collection_name"] == "my-skill"
        assert len(set(data["ids"])) == 3

        # Chroma metadata values must be scalars
        for meta in data["metadatas"]:
            for value in meta.values():
                assert isinstance(value, (str, int, float, bool))


class TestQdrantStreamingFormat:
    """upload()'s documented import snippet reads data["collection_name"],
    data["config"]["vector_size"], and point["id"]/point["payload"]["content"]."""

    def test_keys_import_snippet_reads(self, sample_chunks):
        data = get_adaptor("qdrant")._convert_chunks_to_platform_format(sample_chunks, "my_skill")

        assert data["collection_name"] == "my-skill"
        assert data["config"]["vector_size"] == 1536

        assert len(data["points"]) == 3
        for point in data["points"]:
            # Qdrant point IDs must be UUIDs or unsigned ints
            assert UUID_RE.match(point["id"])
            assert point["payload"]["content"]
            assert point["vector"] is None


class TestFAISSStreamingFormat:
    """upload()'s documented import snippet reads data["documents"],
    data["metadatas"], data["ids"] (and the config hints)."""

    def test_keys_import_snippet_reads(self, sample_chunks):
        data = get_adaptor("faiss")._convert_chunks_to_platform_format(sample_chunks, "my_skill")

        assert len(data["documents"]) == len(data["metadatas"]) == len(data["ids"]) == 3
        assert data["config"]["index_type"] == "IndexFlatL2"
        for meta in data["metadatas"]:
            assert "content" not in meta  # text lives in documents, not metadata
            assert meta["source"] == "my_skill"


class TestLangChainStreamingFormat:
    """Documents must carry the page_content/metadata shape that
    Document(page_content=..., metadata=...) in upload()'s snippet expects."""

    def test_document_shape(self, sample_chunks):
        data = get_adaptor("langchain")._convert_chunks_to_platform_format(
            sample_chunks, "my_skill"
        )

        assert data["streaming"] is True
        assert data["total_chunks"] == 3
        for doc in data["documents"]:
            assert doc["page_content"]
            assert doc["metadata"]["source"] == "my_skill"
            assert doc["metadata"]["type"] in ("documentation", "reference")


class TestLlamaIndexStreamingFormat:
    """Nodes must carry the text/metadata/id_ shape that
    TextNode(text=..., metadata=..., id_=...) in upload()'s snippet expects."""

    def test_node_shape(self, sample_chunks):
        data = get_adaptor("llama-index")._convert_chunks_to_platform_format(
            sample_chunks, "my_skill"
        )

        assert data["streaming"] is True
        assert len(data["nodes"]) == 3
        for node in data["nodes"]:
            assert node["text"]
            assert node["id_"]
            assert node["embedding"] is None
            assert node["metadata"]["source"] == "my_skill"


class TestHaystackStreamingFormat:
    """Documents must carry the content/meta shape that
    Document(content=..., meta=...) in upload()'s snippet expects."""

    def test_document_shape(self, sample_chunks):
        data = get_adaptor("haystack")._convert_chunks_to_platform_format(sample_chunks, "my_skill")

        assert data["streaming"] is True
        assert len(data["documents"]) == 3
        for doc in data["documents"]:
            assert doc["content"]
            assert doc["meta"]["source"] == "my_skill"


class TestStreamingPackageEndToEnd:
    """The verified trigger: `skill-seekers package <skill> --target weaviate
    --streaming` wrote the mixin's generic format and upload() then failed on
    data["schema"] ("Schema creation failed: 'schema'") / data["vectors"]."""

    @pytest.fixture
    def skill_dir(self, tmp_path):
        sk = tmp_path / "my_skill"
        (sk / "references").mkdir(parents=True)
        (sk / "SKILL.md").write_text(
            "---\nname: my_skill\ndescription: x\n---\n# Hello\n" + "content line\n" * 80
        )
        (sk / "references" / "api.md").write_text("# API\n" + "detail\n" * 200)
        return sk

    def test_weaviate_streaming_package_consumable_by_upload(self, skill_dir, tmp_path):
        out = get_adaptor("weaviate").package_streaming(
            skill_dir, tmp_path, chunk_size=500, chunk_overlap=50, batch_size=10
        )
        data = json.loads(out.read_text())

        # Exercise the exact reads upload() performs
        assert data["schema"]["class"] == "MySkill"
        assert data["class_name"] == "MySkill"
        assert data["objects"]
        for obj in data["objects"]:
            assert obj["properties"]["content"]
            assert UUID_RE.match(obj["id"])

    def test_pinecone_streaming_package_consumable_by_upload(self, skill_dir, tmp_path):
        out = get_adaptor("pinecone").package_streaming(
            skill_dir, tmp_path, chunk_size=500, chunk_overlap=50, batch_size=10
        )
        data = json.loads(out.read_text())

        # Exercise the exact reads upload() performs
        texts = [vec["metadata"]["text"] for vec in data["vectors"]]
        assert texts
        assert all(isinstance(t, str) and t for t in texts)
        assert data["index_name"] == "my-skill"

    def test_chroma_streaming_package_consumable_by_upload(self, skill_dir, tmp_path):
        out = get_adaptor("chroma").package_streaming(
            skill_dir, tmp_path, chunk_size=500, chunk_overlap=50, batch_size=10
        )
        data = json.loads(out.read_text())

        assert len(data["documents"]) == len(data["metadatas"]) == len(data["ids"])
        assert data["documents"]
        assert data["collection_name"] == "my-skill"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
