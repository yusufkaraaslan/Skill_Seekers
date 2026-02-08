#!/usr/bin/env python3
"""
Tests for custom embedding pipeline.

Validates:
- Multiple provider support
- Batch processing
- Caching mechanism
- Cost tracking
- Dimension validation
"""

import pytest
from pathlib import Path
import sys
import tempfile

# Skip all tests if numpy is not installed
pytest.importorskip("numpy")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_seekers.cli.embedding_pipeline import (
    EmbeddingConfig,
    EmbeddingPipeline,
    LocalEmbeddingProvider,
    EmbeddingCache,
    CostTracker,
)


def test_local_provider_generation():
    """Test local embedding provider."""
    provider = LocalEmbeddingProvider(dimension=128)

    texts = ["test document 1", "test document 2"]
    embeddings = provider.generate_embeddings(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 128
    assert len(embeddings[1]) == 128


def test_local_provider_deterministic():
    """Test local provider generates deterministic embeddings."""
    provider = LocalEmbeddingProvider(dimension=64)

    text = "same text"
    emb1 = provider.generate_embeddings([text])[0]
    emb2 = provider.generate_embeddings([text])[0]

    # Should be identical for same text
    assert emb1 == emb2


def test_local_provider_cost():
    """Test local provider cost estimation."""
    provider = LocalEmbeddingProvider()

    cost = provider.estimate_cost(1000)
    assert cost == 0.0  # Local is free


def test_cache_memory():
    """Test memory cache functionality."""
    cache = EmbeddingCache()

    text = "test text"
    model = "test-model"
    embedding = [0.1, 0.2, 0.3]

    # Set and get
    cache.set(text, model, embedding)
    retrieved = cache.get(text, model)

    assert retrieved == embedding


def test_cache_miss():
    """Test cache miss returns None."""
    cache = EmbeddingCache()

    result = cache.get("nonexistent", "model")
    assert result is None


def test_cache_disk():
    """Test disk cache functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = EmbeddingCache(cache_dir=Path(tmpdir))

        text = "test text"
        model = "test-model"
        embedding = [0.1, 0.2, 0.3]

        # Set
        cache.set(text, model, embedding)

        # Create new cache instance (clears memory)
        cache2 = EmbeddingCache(cache_dir=Path(tmpdir))

        # Should retrieve from disk
        retrieved = cache2.get(text, model)
        assert retrieved == embedding


def test_cost_tracker():
    """Test cost tracking."""
    tracker = CostTracker()

    # Add requests
    tracker.add_request(token_count=1000, cost=0.01, from_cache=False)
    tracker.add_request(token_count=500, cost=0.005, from_cache=True)

    stats = tracker.get_stats()

    assert stats["total_requests"] == 2
    assert stats["total_tokens"] == 1500
    assert stats["cache_hits"] == 1
    assert stats["cache_misses"] == 1
    assert "50.0%" in stats["cache_rate"]


def test_pipeline_initialization():
    """Test pipeline initialization."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=128, batch_size=10)

    pipeline = EmbeddingPipeline(config)

    assert pipeline.config == config
    assert pipeline.provider is not None
    assert pipeline.cache is not None


def test_pipeline_generate_batch():
    """Test batch embedding generation."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=64, batch_size=2)

    pipeline = EmbeddingPipeline(config)

    texts = ["doc 1", "doc 2", "doc 3"]
    result = pipeline.generate_batch(texts, show_progress=False)

    assert len(result.embeddings) == 3
    assert len(result.embeddings[0]) == 64
    assert result.generated_count == 3
    assert result.cached_count == 0


def test_pipeline_caching():
    """Test pipeline uses caching."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = EmbeddingConfig(
            provider="local",
            model="test-model",
            dimension=32,
            batch_size=10,
            cache_dir=Path(tmpdir),
        )

        pipeline = EmbeddingPipeline(config)

        texts = ["same doc", "same doc", "different doc"]

        # First generation
        result1 = pipeline.generate_batch(texts, show_progress=False)
        assert result1.cached_count == 0
        assert result1.generated_count == 3

        # Second generation (should use cache)
        result2 = pipeline.generate_batch(texts, show_progress=False)
        assert result2.cached_count == 3
        assert result2.generated_count == 0


def test_pipeline_batch_processing():
    """Test large batch is processed in chunks."""
    config = EmbeddingConfig(
        provider="local",
        model="test-model",
        dimension=16,
        batch_size=3,  # Small batch size
    )

    pipeline = EmbeddingPipeline(config)

    # 10 texts with batch size 3 = 4 batches
    texts = [f"doc {i}" for i in range(10)]
    result = pipeline.generate_batch(texts, show_progress=False)

    assert len(result.embeddings) == 10


def test_validate_dimensions_valid():
    """Test dimension validation with valid embeddings."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=128)

    pipeline = EmbeddingPipeline(config)

    embeddings = [[0.1] * 128, [0.2] * 128]
    is_valid = pipeline.validate_dimensions(embeddings)

    assert is_valid


def test_validate_dimensions_invalid():
    """Test dimension validation with invalid embeddings."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=128)

    pipeline = EmbeddingPipeline(config)

    # Wrong dimension
    embeddings = [[0.1] * 64, [0.2] * 128]
    is_valid = pipeline.validate_dimensions(embeddings)

    assert not is_valid


def test_embedding_result_metadata():
    """Test embedding result includes metadata."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=256)

    pipeline = EmbeddingPipeline(config)

    texts = ["test"]
    result = pipeline.generate_batch(texts, show_progress=False)

    assert "provider" in result.metadata
    assert "model" in result.metadata
    assert "dimension" in result.metadata
    assert result.metadata["dimension"] == 256


def test_cost_stats():
    """Test cost statistics tracking."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=64)

    pipeline = EmbeddingPipeline(config)

    texts = ["doc 1", "doc 2"]
    pipeline.generate_batch(texts, show_progress=False)

    stats = pipeline.get_cost_stats()

    assert "total_requests" in stats
    assert "cache_hits" in stats
    assert "estimated_cost" in stats


def test_empty_batch():
    """Test handling empty batch."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=32)

    pipeline = EmbeddingPipeline(config)

    result = pipeline.generate_batch([], show_progress=False)

    assert len(result.embeddings) == 0
    assert result.generated_count == 0


def test_single_document():
    """Test single document generation."""
    config = EmbeddingConfig(provider="local", model="test-model", dimension=128)

    pipeline = EmbeddingPipeline(config)

    result = pipeline.generate_batch(["single doc"], show_progress=False)

    assert len(result.embeddings) == 1
    assert len(result.embeddings[0]) == 128


def test_different_dimensions():
    """Test different embedding dimensions."""
    for dim in [64, 128, 256, 512]:
        config = EmbeddingConfig(provider="local", model="test-model", dimension=dim)

        pipeline = EmbeddingPipeline(config)
        result = pipeline.generate_batch(["test"], show_progress=False)

        assert len(result.embeddings[0]) == dim


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
