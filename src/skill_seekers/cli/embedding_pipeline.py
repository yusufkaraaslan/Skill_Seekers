#!/usr/bin/env python3
"""
Custom Embedding Pipeline

Provides flexible embedding generation with multiple providers,
batch processing, caching, and cost tracking.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""

    provider: str  # 'openai', 'cohere', 'huggingface', 'local'
    model: str
    dimension: int
    batch_size: int = 100
    cache_dir: Path | None = None
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embeddings: list[list[float]]
    metadata: dict[str, Any] = field(default_factory=dict)
    cached_count: int = 0
    generated_count: int = 0
    total_time: float = 0.0
    cost_estimate: float = 0.0


@dataclass
class CostTracker:
    """Track embedding generation costs."""

    total_tokens: int = 0
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    estimated_cost: float = 0.0

    def add_request(self, token_count: int, cost: float, from_cache: bool = False):
        """Add a request to tracking."""
        self.total_requests += 1
        self.total_tokens += token_count
        self.estimated_cost += cost

        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def get_stats(self) -> dict[str, Any]:
        """Get statistics."""
        cache_rate = (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0

        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_rate": f"{cache_rate:.1f}%",
            "estimated_cost": f"${self.estimated_cost:.4f}",
        }


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass

    @abstractmethod
    def estimate_cost(self, token_count: int) -> float:
        """Estimate cost for token count."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    # Pricing per 1M tokens (as of 2026)
    PRICING = {
        "text-embedding-ada-002": 0.10,
        "text-embedding-3-small": 0.02,
        "text-embedding-3-large": 0.13,
    }

    DIMENSIONS = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(self, model: str = "text-embedding-ada-002", api_key: str | None = None):
        """Initialize OpenAI provider."""
        self.model = model
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Install with: pip install openai"
                ) from None
        return self._client

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI."""
        client = self._get_client()

        embeddings = []
        for text in texts:
            response = client.embeddings.create(model=self.model, input=text)
            embeddings.append(response.data[0].embedding)

        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.DIMENSIONS.get(self.model, 1536)

    def estimate_cost(self, token_count: int) -> float:
        """Estimate cost."""
        price_per_million = self.PRICING.get(self.model, 0.10)
        return (token_count / 1_000_000) * price_per_million


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider (simulated)."""

    def __init__(self, dimension: int = 384):
        """Initialize local provider."""
        self.dimension = dimension

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using local model (simulated)."""
        # In production, would use sentence-transformers or similar
        embeddings = []
        for text in texts:
            # Deterministic random based on text hash
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            np.random.seed(seed)
            embedding = np.random.randn(self.dimension).tolist()
            embeddings.append(embedding)

        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension

    def estimate_cost(self, token_count: int) -> float:
        """Local models are free."""
        return 0.0


class EmbeddingCache:
    """Cache for embeddings to avoid recomputation."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize cache."""
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._memory_cache: dict[str, list[float]] = {}

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, text: str, model: str) -> str:
        """Compute cache key."""
        key = f"{model}:{text}"
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, text: str, model: str) -> list[float] | None:
        """Get embedding from cache."""
        cache_key = self._compute_hash(text, model)

        # Check memory cache
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Check disk cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text())
                    embedding = data["embedding"]
                    self._memory_cache[cache_key] = embedding
                    return embedding
                except Exception:
                    pass

        return None

    def set(self, text: str, model: str, embedding: list[float]) -> None:
        """Store embedding in cache."""
        cache_key = self._compute_hash(text, model)

        # Store in memory
        self._memory_cache[cache_key] = embedding

        # Store on disk
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                cache_file.write_text(
                    json.dumps(
                        {
                            "text_hash": cache_key,
                            "model": model,
                            "embedding": embedding,
                            "timestamp": time.time(),
                        }
                    )
                )
            except Exception as e:
                print(f"⚠️  Warning: Failed to write cache: {e}")


class EmbeddingPipeline:
    """
    Flexible embedding generation pipeline.

    Supports multiple providers, batch processing, caching, and cost tracking.
    """

    def __init__(self, config: EmbeddingConfig):
        """Initialize pipeline."""
        self.config = config
        self.provider = self._create_provider()
        self.cache = EmbeddingCache(config.cache_dir)
        self.cost_tracker = CostTracker()

    def _create_provider(self) -> EmbeddingProvider:
        """Create provider based on config."""
        if self.config.provider == "openai":
            return OpenAIEmbeddingProvider(self.config.model)
        elif self.config.provider == "local":
            return LocalEmbeddingProvider(self.config.dimension)
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    def generate_batch(self, texts: list[str], show_progress: bool = True) -> EmbeddingResult:
        """
        Generate embeddings for batch of texts.

        Args:
            texts: List of texts to embed
            show_progress: Show progress output

        Returns:
            EmbeddingResult with embeddings and metadata
        """
        start_time = time.time()
        embeddings = []
        cached_count = 0
        generated_count = 0

        if show_progress:
            print(f"🔄 Generating embeddings...")
            print(f"   Texts: {len(texts)}")
            print(f"   Provider: {self.config.provider}")
            print(f"   Model: {self.config.model}")
            print(f"   Batch size: {self.config.batch_size}")

        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]
            batch_embeddings = []
            to_generate = []
            to_generate_indices = []

            # Check cache
            for j, text in enumerate(batch):
                cached = self.cache.get(text, self.config.model)
                if cached:
                    batch_embeddings.append(cached)
                    cached_count += 1
                else:
                    to_generate.append(text)
                    to_generate_indices.append(j)

            # Generate missing embeddings
            if to_generate:
                new_embeddings = self.provider.generate_embeddings(to_generate)

                # Store in cache
                for text, embedding in zip(to_generate, new_embeddings, strict=False):
                    self.cache.set(text, self.config.model, embedding)

                # Track cost
                total_tokens = sum(self._estimate_tokens(t) for t in to_generate)
                cost = self.provider.estimate_cost(total_tokens)
                self.cost_tracker.add_request(total_tokens, cost, from_cache=False)

                # Merge with cached
                for idx, embedding in zip(to_generate_indices, new_embeddings, strict=False):
                    batch_embeddings.insert(idx, embedding)

                generated_count += len(to_generate)

            embeddings.extend(batch_embeddings)

            if show_progress and len(texts) > self.config.batch_size:
                progress = min(i + self.config.batch_size, len(texts))
                print(f"   Progress: {progress}/{len(texts)} ({progress / len(texts) * 100:.1f}%)")

        total_time = time.time() - start_time

        if show_progress:
            print(f"\n✅ Embeddings generated!")
            print(f"   Total: {len(embeddings)}")
            print(f"   Cached: {cached_count}")
            print(f"   Generated: {generated_count}")
            print(f"   Time: {total_time:.2f}s")

            if self.config.provider != "local":
                stats = self.cost_tracker.get_stats()
                print(f"   Cost: {stats['estimated_cost']}")

        return EmbeddingResult(
            embeddings=embeddings,
            metadata={
                "provider": self.config.provider,
                "model": self.config.model,
                "dimension": self.provider.get_dimension(),
            },
            cached_count=cached_count,
            generated_count=generated_count,
            total_time=total_time,
            cost_estimate=self.cost_tracker.estimated_cost,
        )

    def validate_dimensions(self, embeddings: list[list[float]]) -> bool:
        """
        Validate embedding dimensions.

        Args:
            embeddings: List of embeddings to validate

        Returns:
            True if valid
        """
        expected_dim = self.provider.get_dimension()

        for i, embedding in enumerate(embeddings):
            if len(embedding) != expected_dim:
                print(
                    f"❌ Dimension mismatch at index {i}: "
                    f"expected {expected_dim}, got {len(embedding)}"
                )
                return False

        return True

    def get_cost_stats(self) -> dict[str, Any]:
        """Get cost tracking statistics."""
        return self.cost_tracker.get_stats()


def example_usage():
    """Example usage of embedding pipeline."""
    from pathlib import Path

    # Configure pipeline
    config = EmbeddingConfig(
        provider="local",  # Use 'openai' for production
        model="text-embedding-ada-002",
        dimension=384,
        batch_size=50,
        cache_dir=Path("output/.embeddings_cache"),
    )

    # Initialize pipeline
    pipeline = EmbeddingPipeline(config)

    # Generate embeddings
    texts = [
        "This is the first document.",
        "Here is the second document.",
        "And this is the third document.",
    ]

    result = pipeline.generate_batch(texts)

    print(f"\n📊 Results:")
    print(f"   Embeddings: {len(result.embeddings)}")
    print(f"   Dimension: {len(result.embeddings[0])}")
    print(f"   Cached: {result.cached_count}")
    print(f"   Generated: {result.generated_count}")

    # Validate
    is_valid = pipeline.validate_dimensions(result.embeddings)
    print(f"   Valid: {is_valid}")

    # Cost stats
    stats = pipeline.get_cost_stats()
    print(f"\n💰 Cost Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    example_usage()
