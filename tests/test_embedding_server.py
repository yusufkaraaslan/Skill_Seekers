"""Tests for the FastAPI embedding server (embedding/server.py).

Uses starlette TestClient for in-process HTTP testing.
"""

import pytest
from unittest.mock import patch

try:
    from starlette.testclient import TestClient
    from skill_seekers.embedding.server import app as _embedding_app

    STARLETTE_AVAILABLE = True
except (ImportError, SystemExit):
    STARLETTE_AVAILABLE = False

pytestmark = pytest.mark.skipif(not STARLETTE_AVAILABLE, reason="Starlette not installed")


@pytest.fixture
def mock_generator():
    with patch("skill_seekers.embedding.server.generator") as mock_gen:
        mock_gen.list_models.return_value = [
            {
                "name": "text-embedding-3-small",
                "provider": "openai",
                "dimensions": 1536,
                "max_tokens": 8191,
            },
            {
                "name": "text-embedding-3-large",
                "provider": "openai",
                "dimensions": 3072,
                "max_tokens": 8191,
            },
        ]
        mock_gen.generate.return_value = [0.1, 0.2, 0.3]
        mock_gen.generate_batch.return_value = ([[0.1, 0.2], [0.3, 0.4]], 2)
        mock_gen.compute_hash.return_value = "mock_hash_abc123"
        yield mock_gen


@pytest.fixture
def mock_cache():
    with patch("skill_seekers.embedding.server.cache") as mock_cache:
        mock_cache.has.return_value = False
        mock_cache.get.return_value = None
        mock_cache.size.return_value = 42
        mock_cache.stats.return_value = {
            "total": 42,
            "by_model": {"text-embedding-3-small": 42},
            "top_accessed": [],
            "expired": 0,
            "ttl_days": 30,
        }
        mock_cache.clear.return_value = 5
        mock_cache.clear_expired.return_value = 3
        yield mock_cache


@pytest.fixture
def client(mock_generator, mock_cache):  # noqa: ARG001
    with TestClient(_embedding_app) as c:
        yield c


class TestRoot:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Skill Seekers Embedding API"
        assert data["version"] == "1.0.0"
        assert "/docs" in data["docs"]
        assert "/health" in data["health"]


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        assert "models" in data
        assert data["cache_enabled"] is True
        assert data["cache_size"] == 42


class TestModels:
    def test_list_models(self, client):
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["models"]) == 2
        assert data["models"][0]["name"] == "text-embedding-3-small"
        assert data["models"][0]["provider"] == "openai"
        assert data["models"][0]["dimensions"] == 1536


class TestEmbedText:
    def test_embed_single_text(self, client):
        response = client.post(
            "/embed", json={"text": "Hello world", "model": "text-embedding-3-small"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "text-embedding-3-small"
        assert len(data["embedding"]) == 3
        assert data["cached"] is False

    def test_embed_cached(self, client, mock_cache, mock_generator):
        mock_cache.has.return_value = True
        mock_cache.get.return_value = [0.5, 0.6, 0.7]

        response = client.post(
            "/embed", json={"text": "cached text", "model": "text-embedding-3-small"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["embedding"] == [0.5, 0.6, 0.7]

    def test_embed_with_normalize(self, client):
        response = client.post("/embed", json={"text": "test", "normalize": False})
        assert response.status_code == 200


class TestEmbedBatch:
    def test_embed_batch(self, client):
        response = client.post("/embed/batch", json={"texts": ["text1", "text2"]})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["dimensions"] == 2
        assert len(data["embeddings"]) == 2

    def test_embed_batch_empty(self, client, mock_generator):
        mock_generator.generate_batch.return_value = ([[0.1]], 1)

        response = client.post("/embed/batch", json={"texts": ["one"]})
        assert response.status_code == 200


class TestEmbedSkill:
    def test_embed_skill(self, client, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "# Test Skill\n\nThis is a test skill with enough content\n" * 5
        )

        response = client.post("/embed/skill", json={"skill_path": str(skill_dir)})
        assert response.status_code == 200
        data = response.json()
        assert data["skill_name"] == "test-skill"
        assert data["model"] == "text-embedding-3-small"

    def test_embed_skill_not_found(self, client):
        response = client.post("/embed/skill", json={"skill_path": "/nonexistent/path"})
        assert response.status_code == 404

    def test_embed_skill_no_skill_md(self, client, tmp_path):
        skill_dir = tmp_path / "empty-skill"
        skill_dir.mkdir()

        response = client.post("/embed/skill", json={"skill_path": str(skill_dir)})
        assert response.status_code == 404


class TestCacheEndpoints:
    def test_cache_stats(self, client):
        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 42

    def test_clear_cache_all(self, client):
        response = client.post("/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["deleted"] == 5

    def test_clear_cache_by_model(self, client):
        response = client.post("/cache/clear?model=text-embedding-3-small")
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "text-embedding-3-small"

    def test_clear_expired(self, client):
        response = client.post("/cache/clear-expired")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["deleted"] == 3
