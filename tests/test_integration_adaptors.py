#!/usr/bin/env python3
"""
Integration Tests with Real Vector Databases

Tests complete workflows: package → upload → query → verify

Prerequisites:
    docker-compose -f tests/docker-compose.test.yml up -d

Usage:
    # Run all integration tests
    pytest tests/test_integration_adaptors.py -v -m integration

    # Run specific database
    pytest tests/test_integration_adaptors.py::TestWeaviateIntegration -v -m integration
"""

import json
import time

import pytest

from skill_seekers.cli.adaptors import get_adaptor
from skill_seekers.cli.adaptors.base import SkillMetadata
import contextlib


@pytest.fixture
def sample_skill_dir(tmp_path):
    """Create a sample skill for integration testing."""
    skill_dir = tmp_path / "test_integration_skill"
    skill_dir.mkdir()

    # Create SKILL.md
    skill_md = """# Integration Test Skill

This is a test skill for integration testing with vector databases.

## Core Concepts

- Concept 1: Understanding vector embeddings
- Concept 2: Similarity search algorithms
- Concept 3: Metadata filtering

## Quick Start

Get started with vector databases in 3 steps:
1. Initialize your database
2. Upload your documents
3. Query with semantic search
"""
    (skill_dir / "SKILL.md").write_text(skill_md)

    # Create reference files
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()

    references = {
        "api_reference.md": """# API Reference

## Core Functions

### add_documents(documents, metadata)
Add documents to the vector database.

### query(text, limit=10)
Query the database with semantic search.

### delete_collection(name)
Delete a collection from the database.
""",
        "getting_started.md": """# Getting Started

## Installation

```bash
pip install vector-db-client
```

## Basic Usage

```python
from vector_db import Client

client = Client("http://localhost:8080")
client.add_documents(["doc1", "doc2"])
results = client.query("search query")
```
""",
        "advanced_features.md": """# Advanced Features

## Hybrid Search

Combine keyword and vector search for better results.

## Metadata Filtering

Filter results based on metadata attributes.

## Multi-modal Search

Search across text, images, and audio.
""",
    }

    for filename, content in references.items():
        (refs_dir / filename).write_text(content)

    return skill_dir


def check_service_available(url: str, timeout: int = 5) -> bool:
    """Check if a service is available."""
    try:
        import requests

        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


@pytest.mark.integration
class TestWeaviateIntegration:
    """Integration tests with real Weaviate instance."""

    def test_complete_workflow_with_weaviate(self, sample_skill_dir, tmp_path):
        """Test: package → upload to Weaviate → query → verify."""
        # Check if Weaviate client is installed
        try:
            import weaviate
        except ImportError:
            pytest.skip("weaviate-client not installed (pip install weaviate-client)")

        # Check if Weaviate is running
        if not check_service_available("http://localhost:8080/v1/.well-known/ready"):
            pytest.skip(
                "Weaviate not running (start with: docker-compose -f tests/docker-compose.test.yml up -d)"
            )

        # Connect to Weaviate
        try:
            client = weaviate.Client("http://localhost:8080")
            assert client.is_ready(), "Weaviate not ready"
        except Exception as e:
            pytest.skip(f"Cannot connect to Weaviate: {e}")

        # Package skill
        adaptor = get_adaptor("weaviate")
        SkillMetadata(name="integration_test", description="Integration test skill for Weaviate")
        package_path = adaptor.package(sample_skill_dir, tmp_path)

        assert package_path.exists(), "Package not created"
        assert package_path.suffix == ".json", "Package should be JSON"

        # Load packaged data
        with open(package_path) as f:
            data = json.load(f)

        assert "schema" in data, "Missing schema"
        assert "objects" in data, "Missing objects"
        assert "class_name" in data, "Missing class_name"
        assert len(data["objects"]) > 0, "No objects in package"

        class_name = data["class_name"]

        # Upload to Weaviate
        try:
            # Create schema
            client.schema.create_class(data["schema"])

            # Upload objects (batch)
            with client.batch as batch:
                for obj in data["objects"]:
                    batch.add_data_object(
                        data_object=obj["properties"], class_name=class_name, uuid=obj["id"]
                    )

            # Wait for indexing
            time.sleep(1)

            # Query - Get all objects
            result = (
                client.query.get(class_name, ["content", "source", "category"]).with_limit(10).do()
            )

            # Verify results
            assert "data" in result, "Query returned no data"
            assert "Get" in result["data"], "Invalid query response"
            assert class_name in result["data"]["Get"], "Class not found in response"

            objects = result["data"]["Get"][class_name]
            assert len(objects) > 0, "No objects returned"

            # Verify object structure
            first_obj = objects[0]
            assert "content" in first_obj, "Missing content field"
            assert "source" in first_obj, "Missing source field"
            assert "category" in first_obj, "Missing category field"

            # Verify content
            contents = [obj["content"] for obj in objects]
            assert any("vector" in content.lower() for content in contents), (
                "Expected content not found"
            )

        finally:
            # Cleanup - Delete collection
            with contextlib.suppress(Exception):
                client.schema.delete_class(class_name)

    def test_weaviate_metadata_preservation(self, sample_skill_dir, tmp_path):
        """Test that metadata is correctly stored and retrieved."""
        try:
            import weaviate
        except ImportError:
            pytest.skip("weaviate-client not installed")

        if not check_service_available("http://localhost:8080/v1/.well-known/ready"):
            pytest.skip("Weaviate not running")

        try:
            client = weaviate.Client("http://localhost:8080")
            assert client.is_ready()
        except Exception as e:
            pytest.skip(f"Cannot connect to Weaviate: {e}")

        # Package with rich metadata
        adaptor = get_adaptor("weaviate")
        SkillMetadata(
            name="metadata_test",
            description="Test metadata preservation",
            version="2.0.0",
            author="Integration Test Suite",
            tags=["test", "integration", "weaviate"],
        )
        package_path = adaptor.package(sample_skill_dir, tmp_path)

        with open(package_path) as f:
            data = json.load(f)

        class_name = data["class_name"]

        try:
            # Upload
            client.schema.create_class(data["schema"])
            with client.batch as batch:
                for obj in data["objects"]:
                    batch.add_data_object(
                        data_object=obj["properties"], class_name=class_name, uuid=obj["id"]
                    )

            time.sleep(1)

            # Query and verify metadata
            result = (
                client.query.get(class_name, ["source", "version", "author", "tags"])
                .with_limit(1)
                .do()
            )

            obj = result["data"]["Get"][class_name][0]
            assert obj["source"] == "metadata_test", "Source not preserved"
            assert obj["version"] == "2.0.0", "Version not preserved"
            assert obj["author"] == "Integration Test Suite", "Author not preserved"
            assert "test" in obj["tags"], "Tags not preserved"

        finally:
            with contextlib.suppress(Exception):
                client.schema.delete_class(class_name)


@pytest.mark.integration
class TestChromaIntegration:
    """Integration tests with ChromaDB."""

    def test_complete_workflow_with_chroma(self, sample_skill_dir, tmp_path):
        """Test: package → upload to Chroma → query → verify."""
        # Check if ChromaDB is installed
        try:
            import chromadb
        except ImportError:
            pytest.skip("chromadb not installed (pip install chromadb)")

        # Check if Chroma is running
        if not check_service_available("http://localhost:8000/api/v1/heartbeat"):
            pytest.skip(
                "ChromaDB not running (start with: docker-compose -f tests/docker-compose.test.yml up -d)"
            )

        # Connect to ChromaDB
        try:
            client = chromadb.HttpClient(host="localhost", port=8000)
            client.heartbeat()  # Test connection
        except Exception as e:
            pytest.skip(f"Cannot connect to ChromaDB: {e}")

        # Package skill
        adaptor = get_adaptor("chroma")
        SkillMetadata(
            name="chroma_integration_test", description="Integration test skill for ChromaDB"
        )
        package_path = adaptor.package(sample_skill_dir, tmp_path)

        assert package_path.exists(), "Package not created"
        assert package_path.suffix == ".json", "Package should be JSON"

        # Load packaged data
        with open(package_path) as f:
            data = json.load(f)

        assert "documents" in data, "Missing documents"
        assert "metadatas" in data, "Missing metadatas"
        assert "ids" in data, "Missing ids"
        assert "collection_name" in data, "Missing collection_name"
        assert len(data["documents"]) > 0, "No documents in package"

        collection_name = data["collection_name"]

        # Upload to ChromaDB
        try:
            # Create collection
            collection = client.get_or_create_collection(name=collection_name)

            # Add documents
            collection.add(
                documents=data["documents"], metadatas=data["metadatas"], ids=data["ids"]
            )

            # Wait for indexing
            time.sleep(1)

            # Query - Get all documents
            results = collection.get()

            # Verify results
            assert "documents" in results, "Query returned no documents"
            assert len(results["documents"]) > 0, "No documents returned"
            assert len(results["documents"]) == len(data["documents"]), "Document count mismatch"

            # Verify metadata
            assert "metadatas" in results, "Query returned no metadatas"
            first_metadata = results["metadatas"][0]
            assert "source" in first_metadata, "Missing source in metadata"
            assert "category" in first_metadata, "Missing category in metadata"

            # Verify content
            assert any("vector" in doc.lower() for doc in results["documents"]), (
                "Expected content not found"
            )

        finally:
            # Cleanup - Delete collection
            with contextlib.suppress(Exception):
                client.delete_collection(name=collection_name)

    def test_chroma_query_filtering(self, sample_skill_dir, tmp_path):
        """Test metadata filtering in ChromaDB queries."""
        try:
            import chromadb
        except ImportError:
            pytest.skip("chromadb not installed")

        if not check_service_available("http://localhost:8000/api/v1/heartbeat"):
            pytest.skip("ChromaDB not running")

        try:
            client = chromadb.HttpClient(host="localhost", port=8000)
            client.heartbeat()
        except Exception as e:
            pytest.skip(f"Cannot connect to ChromaDB: {e}")

        # Package and upload
        adaptor = get_adaptor("chroma")
        metadata = SkillMetadata(
            name="chroma_filter_test", description="Test filtering capabilities"
        )
        package_path = adaptor.package(sample_skill_dir, tmp_path)

        with open(package_path) as f:
            data = json.load(f)

        collection_name = data["collection_name"]

        try:
            collection = client.get_or_create_collection(name=collection_name)
            collection.add(
                documents=data["documents"], metadatas=data["metadatas"], ids=data["ids"]
            )

            time.sleep(1)

            # Query with category filter
            results = collection.get(where={"category": "getting started"})

            # Verify filtering worked
            assert len(results["documents"]) > 0, "No documents matched filter"
            for metadata in results["metadatas"]:
                assert metadata["category"] == "getting started", "Filter returned wrong category"

        finally:
            with contextlib.suppress(Exception):
                client.delete_collection(name=collection_name)


@pytest.mark.integration
class TestQdrantIntegration:
    """Integration tests with Qdrant."""

    def test_complete_workflow_with_qdrant(self, sample_skill_dir, tmp_path):
        """Test: package → upload to Qdrant → query → verify."""
        # Check if Qdrant client is installed
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
        except ImportError:
            pytest.skip("qdrant-client not installed (pip install qdrant-client)")

        # Check if Qdrant is running
        if not check_service_available("http://localhost:6333/"):
            pytest.skip(
                "Qdrant not running (start with: docker-compose -f tests/docker-compose.test.yml up -d)"
            )

        # Connect to Qdrant
        try:
            client = QdrantClient(host="localhost", port=6333)
            client.get_collections()  # Test connection
        except Exception as e:
            pytest.skip(f"Cannot connect to Qdrant: {e}")

        # Package skill
        adaptor = get_adaptor("qdrant")
        SkillMetadata(
            name="qdrant_integration_test", description="Integration test skill for Qdrant"
        )
        package_path = adaptor.package(sample_skill_dir, tmp_path)

        assert package_path.exists(), "Package not created"
        assert package_path.suffix == ".json", "Package should be JSON"

        # Load packaged data
        with open(package_path) as f:
            data = json.load(f)

        assert "collection_name" in data, "Missing collection_name"
        assert "points" in data, "Missing points"
        assert "config" in data, "Missing config"
        assert len(data["points"]) > 0, "No points in package"

        collection_name = data["collection_name"]
        vector_size = data["config"]["vector_size"]

        # Upload to Qdrant
        try:
            # Create collection
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

            # Upload points (with placeholder vectors for testing)
            points = []
            for point in data["points"]:
                points.append(
                    PointStruct(
                        id=point["id"],
                        vector=[0.0] * vector_size,  # Placeholder vectors
                        payload=point["payload"],
                    )
                )

            client.upsert(collection_name=collection_name, points=points)

            # Wait for indexing
            time.sleep(1)

            # Query - Get collection info
            collection_info = client.get_collection(collection_name)

            # Verify collection
            assert collection_info.points_count > 0, "No points in collection"
            assert collection_info.points_count == len(data["points"]), "Point count mismatch"

            # Query - Scroll through points
            scroll_result = client.scroll(collection_name=collection_name, limit=10)

            points_list = scroll_result[0]
            assert len(points_list) > 0, "No points returned"

            # Verify point structure
            first_point = points_list[0]
            assert first_point.payload is not None, "Missing payload"
            assert "content" in first_point.payload, "Missing content in payload"
            assert "source" in first_point.payload, "Missing source in payload"
            assert "category" in first_point.payload, "Missing category in payload"

            # Verify content
            contents = [p.payload["content"] for p in points_list]
            assert any("vector" in content.lower() for content in contents), (
                "Expected content not found"
            )

        finally:
            # Cleanup - Delete collection
            with contextlib.suppress(Exception):
                client.delete_collection(collection_name)

    def test_qdrant_payload_filtering(self, sample_skill_dir, tmp_path):
        """Test payload filtering in Qdrant."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import (
                Distance,
                VectorParams,
                PointStruct,
                Filter,
                FieldCondition,
                MatchValue,
            )
        except ImportError:
            pytest.skip("qdrant-client not installed")

        if not check_service_available("http://localhost:6333/"):
            pytest.skip("Qdrant not running")

        try:
            client = QdrantClient(host="localhost", port=6333)
            client.get_collections()
        except Exception as e:
            pytest.skip(f"Cannot connect to Qdrant: {e}")

        # Package and upload
        adaptor = get_adaptor("qdrant")
        SkillMetadata(name="qdrant_filter_test", description="Test filtering capabilities")
        package_path = adaptor.package(sample_skill_dir, tmp_path)

        with open(package_path) as f:
            data = json.load(f)

        collection_name = data["collection_name"]
        vector_size = data["config"]["vector_size"]

        try:
            # Create and upload
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

            points = []
            for point in data["points"]:
                points.append(
                    PointStruct(
                        id=point["id"], vector=[0.0] * vector_size, payload=point["payload"]
                    )
                )

            client.upsert(collection_name=collection_name, points=points)
            time.sleep(1)

            # Query with filter
            scroll_result = client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value="reference"))]
                ),
                limit=10,
            )

            points_list = scroll_result[0]

            # Verify filtering worked
            assert len(points_list) > 0, "No points matched filter"
            for point in points_list:
                assert point.payload["type"] == "reference", "Filter returned wrong type"

        finally:
            with contextlib.suppress(Exception):
                client.delete_collection(collection_name)


if __name__ == "__main__":
    # Run integration tests
    import sys

    sys.exit(pytest.main([__file__, "-v", "-m", "integration"]))
