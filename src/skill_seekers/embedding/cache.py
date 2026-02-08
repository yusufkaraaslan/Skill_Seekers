"""
Caching layer for embeddings.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta


class EmbeddingCache:
    """
    SQLite-based cache for embeddings.

    Stores embeddings with their text hashes to avoid regeneration.
    Supports TTL (time-to-live) for cache entries.

    Examples:
        cache = EmbeddingCache("/path/to/cache.db")

        # Store embedding
        cache.set("hash123", [0.1, 0.2, 0.3], model="text-embedding-3-small")

        # Retrieve embedding
        embedding = cache.get("hash123")

        # Check if cached
        if cache.has("hash123"):
            print("Embedding is cached")
    """

    def __init__(self, db_path: str = ":memory:", ttl_days: int = 30):
        """
        Initialize embedding cache.

        Args:
            db_path: Path to SQLite database (":memory:" for in-memory)
            ttl_days: Time-to-live for cache entries in days
        """
        self.db_path = db_path
        self.ttl_days = ttl_days

        # Create database directory if needed
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                hash TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,
                model TEXT NOT NULL,
                dimensions INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model ON embeddings(model)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON embeddings(created_at)
        """)

        self.conn.commit()

    def set(self, hash_key: str, embedding: list[float], model: str) -> None:
        """
        Store embedding in cache.

        Args:
            hash_key: Hash of text+model
            embedding: Embedding vector
            model: Model name
        """
        cursor = self.conn.cursor()

        now = datetime.utcnow().isoformat()
        embedding_json = json.dumps(embedding)
        dimensions = len(embedding)

        cursor.execute(
            """
            INSERT OR REPLACE INTO embeddings
            (hash, embedding, model, dimensions, created_at, accessed_at, access_count)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
            (hash_key, embedding_json, model, dimensions, now, now),
        )

        self.conn.commit()

    def get(self, hash_key: str) -> list[float] | None:
        """
        Retrieve embedding from cache.

        Args:
            hash_key: Hash of text+model

        Returns:
            Embedding vector if cached and not expired, None otherwise
        """
        cursor = self.conn.cursor()

        # Get embedding
        cursor.execute(
            """
            SELECT embedding, created_at
            FROM embeddings
            WHERE hash = ?
        """,
            (hash_key,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        embedding_json, created_at = row

        # Check TTL
        created = datetime.fromisoformat(created_at)
        if datetime.utcnow() - created > timedelta(days=self.ttl_days):
            # Expired, delete and return None
            self.delete(hash_key)
            return None

        # Update access stats
        now = datetime.utcnow().isoformat()
        cursor.execute(
            """
            UPDATE embeddings
            SET accessed_at = ?, access_count = access_count + 1
            WHERE hash = ?
        """,
            (now, hash_key),
        )
        self.conn.commit()

        return json.loads(embedding_json)

    def get_batch(self, hash_keys: list[str]) -> tuple[list[list[float] | None], list[bool]]:
        """
        Retrieve multiple embeddings from cache.

        Args:
            hash_keys: List of hashes

        Returns:
            Tuple of (embeddings list, cached flags)
            embeddings list contains None for cache misses
        """
        embeddings = []
        cached_flags = []

        for hash_key in hash_keys:
            embedding = self.get(hash_key)
            embeddings.append(embedding)
            cached_flags.append(embedding is not None)

        return embeddings, cached_flags

    def has(self, hash_key: str) -> bool:
        """
        Check if embedding is cached and not expired.

        Args:
            hash_key: Hash of text+model

        Returns:
            True if cached and not expired, False otherwise
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT created_at
            FROM embeddings
            WHERE hash = ?
        """,
            (hash_key,),
        )

        row = cursor.fetchone()
        if not row:
            return False

        # Check TTL
        created = datetime.fromisoformat(row[0])
        if datetime.utcnow() - created > timedelta(days=self.ttl_days):
            # Expired
            self.delete(hash_key)
            return False

        return True

    def delete(self, hash_key: str) -> None:
        """
        Delete embedding from cache.

        Args:
            hash_key: Hash of text+model
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            DELETE FROM embeddings
            WHERE hash = ?
        """,
            (hash_key,),
        )

        self.conn.commit()

    def clear(self, model: str | None = None) -> int:
        """
        Clear cache entries.

        Args:
            model: If provided, only clear entries for this model

        Returns:
            Number of entries deleted
        """
        cursor = self.conn.cursor()

        if model:
            cursor.execute(
                """
                DELETE FROM embeddings
                WHERE model = ?
            """,
                (model,),
            )
        else:
            cursor.execute("DELETE FROM embeddings")

        deleted = cursor.rowcount
        self.conn.commit()

        return deleted

    def clear_expired(self) -> int:
        """
        Clear expired cache entries.

        Returns:
            Number of entries deleted
        """
        cursor = self.conn.cursor()

        cutoff = (datetime.utcnow() - timedelta(days=self.ttl_days)).isoformat()

        cursor.execute(
            """
            DELETE FROM embeddings
            WHERE created_at < ?
        """,
            (cutoff,),
        )

        deleted = cursor.rowcount
        self.conn.commit()

        return deleted

    def size(self) -> int:
        """
        Get number of cached embeddings.

        Returns:
            Number of cache entries
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM embeddings")
        return cursor.fetchone()[0]

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cursor = self.conn.cursor()

        # Total entries
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total = cursor.fetchone()[0]

        # Entries by model
        cursor.execute("""
            SELECT model, COUNT(*)
            FROM embeddings
            GROUP BY model
        """)
        by_model = {row[0]: row[1] for row in cursor.fetchall()}

        # Most accessed
        cursor.execute("""
            SELECT hash, model, access_count
            FROM embeddings
            ORDER BY access_count DESC
            LIMIT 10
        """)
        top_accessed = [
            {"hash": row[0], "model": row[1], "access_count": row[2]} for row in cursor.fetchall()
        ]

        # Expired entries
        cutoff = (datetime.utcnow() - timedelta(days=self.ttl_days)).isoformat()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM embeddings
            WHERE created_at < ?
        """,
            (cutoff,),
        )
        expired = cursor.fetchone()[0]

        return {
            "total": total,
            "by_model": by_model,
            "top_accessed": top_accessed,
            "expired": expired,
            "ttl_days": self.ttl_days,
        }

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
