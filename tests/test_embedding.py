"""
Tests for embedding generation system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

# Skip all tests if numpy is not installed
pytest.importorskip("numpy")

from skill_seekers.embedding.models import (
    EmbeddingRequest,
    BatchEmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingResponse,
    HealthResponse,
    ModelInfo,
)
from skill_seekers.embedding.generator import EmbeddingGenerator
from skill_seekers.embedding.cache import EmbeddingCache


# ========================================
# Cache Tests
# ========================================


def test_cache_init():
    """Test cache initialization."""
    cache = EmbeddingCache(":memory:")
    assert cache.size() == 0


def test_cache_set_get():
    """Test cache set and get."""
    cache = EmbeddingCache(":memory:")

    embedding = [0.1, 0.2, 0.3]
    cache.set("hash123", embedding, "test-model")

    retrieved = cache.get("hash123")
    assert retrieved == embedding


def test_cache_has():
    """Test cache has method."""
    cache = EmbeddingCache(":memory:")

    embedding = [0.1, 0.2, 0.3]
    cache.set("hash123", embedding, "test-model")

    assert cache.has("hash123") is True
    assert cache.has("nonexistent") is False


def test_cache_delete():
    """Test cache deletion."""
    cache = EmbeddingCache(":memory:")

    embedding = [0.1, 0.2, 0.3]
    cache.set("hash123", embedding, "test-model")

    assert cache.has("hash123") is True

    cache.delete("hash123")

    assert cache.has("hash123") is False


def test_cache_clear():
    """Test cache clearing."""
    cache = EmbeddingCache(":memory:")

    cache.set("hash1", [0.1], "model1")
    cache.set("hash2", [0.2], "model2")
    cache.set("hash3", [0.3], "model1")

    assert cache.size() == 3

    # Clear specific model
    deleted = cache.clear(model="model1")
    assert deleted == 2
    assert cache.size() == 1

    # Clear all
    deleted = cache.clear()
    assert deleted == 1
    assert cache.size() == 0


def test_cache_stats():
    """Test cache statistics."""
    cache = EmbeddingCache(":memory:")

    cache.set("hash1", [0.1], "model1")
    cache.set("hash2", [0.2], "model2")
    cache.set("hash3", [0.3], "model1")

    stats = cache.stats()

    assert stats["total"] == 3
    assert stats["by_model"]["model1"] == 2
    assert stats["by_model"]["model2"] == 1


def test_cache_context_manager():
    """Test cache as context manager."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        with EmbeddingCache(tmp_path) as cache:
            cache.set("hash1", [0.1], "model1")
            assert cache.size() == 1

        # Verify database file exists
        assert Path(tmp_path).exists()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ========================================
# Generator Tests
# ========================================


def test_generator_init():
    """Test generator initialization."""
    generator = EmbeddingGenerator()
    assert generator is not None


def test_generator_list_models():
    """Test listing models."""
    generator = EmbeddingGenerator()
    models = generator.list_models()

    assert len(models) > 0
    assert all("name" in m for m in models)
    assert all("provider" in m for m in models)
    assert all("dimensions" in m for m in models)


def test_generator_get_model_info():
    """Test getting model info."""
    generator = EmbeddingGenerator()

    info = generator.get_model_info("text-embedding-3-small")

    assert info["provider"] == "openai"
    assert info["dimensions"] == 1536
    assert info["max_tokens"] == 8191


def test_generator_get_model_info_invalid():
    """Test getting model info for invalid model."""
    generator = EmbeddingGenerator()

    with pytest.raises(ValueError, match="Unknown model"):
        generator.get_model_info("nonexistent-model")


def test_generator_compute_hash():
    """Test hash computation."""
    hash1 = EmbeddingGenerator.compute_hash("text1", "model1")
    hash2 = EmbeddingGenerator.compute_hash("text1", "model1")
    hash3 = EmbeddingGenerator.compute_hash("text2", "model1")
    hash4 = EmbeddingGenerator.compute_hash("text1", "model2")

    # Same text+model = same hash
    assert hash1 == hash2

    # Different text = different hash
    assert hash1 != hash3

    # Different model = different hash
    assert hash1 != hash4


@patch("skill_seekers.embedding.generator.SENTENCE_TRANSFORMERS_AVAILABLE", False)
def test_generator_sentence_transformers_not_available():
    """Test sentence-transformers not available."""
    generator = EmbeddingGenerator()

    with pytest.raises(ImportError, match="sentence-transformers is required"):
        generator.generate("test", model="all-MiniLM-L6-v2")


@patch("skill_seekers.embedding.generator.OPENAI_AVAILABLE", False)
def test_generator_openai_not_available():
    """Test OpenAI not available."""
    generator = EmbeddingGenerator()

    with pytest.raises(ImportError, match="OpenAI is required"):
        generator.generate("test", model="text-embedding-3-small")


@patch("skill_seekers.embedding.generator.VOYAGE_AVAILABLE", False)
def test_generator_voyage_not_available():
    """Test Voyage AI not available."""
    generator = EmbeddingGenerator()

    with pytest.raises(ImportError, match="voyageai is required"):
        generator.generate("test", model="voyage-3")


def test_generator_voyage_model_info():
    """Test getting Voyage AI model info."""
    generator = EmbeddingGenerator()

    info = generator.get_model_info("voyage-3")

    assert info["provider"] == "voyage"
    assert info["dimensions"] == 1024
    assert info["max_tokens"] == 32000


def test_generator_voyage_large_2_model_info():
    """Test getting Voyage Large 2 model info."""
    generator = EmbeddingGenerator()

    info = generator.get_model_info("voyage-large-2")

    assert info["provider"] == "voyage"
    assert info["dimensions"] == 1536
    assert info["cost_per_million"] == 0.12


# ========================================
# Model Tests
# ========================================


def test_embedding_request():
    """Test EmbeddingRequest model."""
    request = EmbeddingRequest(text="Hello world", model="text-embedding-3-small", normalize=True)

    assert request.text == "Hello world"
    assert request.model == "text-embedding-3-small"
    assert request.normalize is True


def test_batch_embedding_request():
    """Test BatchEmbeddingRequest model."""
    request = BatchEmbeddingRequest(
        texts=["text1", "text2", "text3"], model="text-embedding-3-small", batch_size=32
    )

    assert len(request.texts) == 3
    assert request.batch_size == 32


def test_embedding_response():
    """Test EmbeddingResponse model."""
    response = EmbeddingResponse(
        embedding=[0.1, 0.2, 0.3], model="test-model", dimensions=3, cached=False
    )

    assert len(response.embedding) == 3
    assert response.dimensions == 3
    assert response.cached is False


def test_batch_embedding_response():
    """Test BatchEmbeddingResponse model."""
    response = BatchEmbeddingResponse(
        embeddings=[[0.1, 0.2], [0.3, 0.4]],
        model="test-model",
        dimensions=2,
        count=2,
        cached_count=1,
    )

    assert len(response.embeddings) == 2
    assert response.count == 2
    assert response.cached_count == 1


def test_health_response():
    """Test HealthResponse model."""
    response = HealthResponse(
        status="ok",
        version="1.0.0",
        models=["model1", "model2"],
        cache_enabled=True,
        cache_size=100,
    )

    assert response.status == "ok"
    assert len(response.models) == 2
    assert response.cache_size == 100


def test_model_info():
    """Test ModelInfo model."""
    info = ModelInfo(
        name="test-model",
        provider="openai",
        dimensions=1536,
        max_tokens=8191,
        cost_per_million=0.02,
    )

    assert info.name == "test-model"
    assert info.provider == "openai"
    assert info.cost_per_million == 0.02


# ========================================
# Integration Tests
# ========================================


def test_cache_batch_operations():
    """Test cache batch operations."""
    cache = EmbeddingCache(":memory:")

    # Set multiple embeddings
    cache.set("hash1", [0.1, 0.2], "model1")
    cache.set("hash2", [0.3, 0.4], "model1")
    cache.set("hash3", [0.5, 0.6], "model1")

    # Get batch
    embeddings, cached_flags = cache.get_batch(["hash1", "hash2", "hash999", "hash3"])

    assert len(embeddings) == 4
    assert embeddings[0] == [0.1, 0.2]
    assert embeddings[1] == [0.3, 0.4]
    assert embeddings[2] is None  # Cache miss
    assert embeddings[3] == [0.5, 0.6]

    assert cached_flags == [True, True, False, True]


def test_generator_normalize():
    """Test embedding normalization."""
    import numpy as np

    embedding = [3.0, 4.0]  # Length 5
    normalized = EmbeddingGenerator._normalize(embedding)

    # Check unit length
    length = np.linalg.norm(normalized)
    assert abs(length - 1.0) < 1e-6


def test_cache_persistence():
    """Test cache persistence to file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp_path = tmp.name

    try:
        # Create cache and add data
        cache1 = EmbeddingCache(tmp_path)
        cache1.set("hash1", [0.1, 0.2, 0.3], "model1")
        cache1.close()

        # Reopen cache and verify data persists
        cache2 = EmbeddingCache(tmp_path)
        retrieved = cache2.get("hash1")
        assert retrieved == [0.1, 0.2, 0.3]
        cache2.close()

    finally:
        Path(tmp_path).unlink(missing_ok=True)
