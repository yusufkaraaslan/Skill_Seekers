# Qdrant Vector Database Example

Qdrant is a vector similarity search engine with extended filtering support. Built in Rust for maximum performance.

## Quick Start

```bash
# 1. Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant:latest

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate and upload
python 1_generate_skill.py
python 2_upload_to_qdrant.py

# 4. Query
python 3_query_example.py
```

## What Makes Qdrant Special?

- **Advanced Filtering**: Rich payload queries with AND/OR/NOT
- **High Performance**: Rust-based, handles billions of vectors
- **Production Ready**: Clustering, replication, persistence built-in
- **Flexible Storage**: In-memory or on-disk, cloud or self-hosted

## Key Features

### Rich Payload Filtering

```python
# Complex filters
collection.search(
    query_vector=vector,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="category",
                match=models.MatchValue(value="api")
            )
        ],
        should=[
            models.FieldCondition(
                key="type",
                match=models.MatchValue(value="reference")
            )
        ]
    ),
    limit=5
)
```

### Hybrid Search

Combine vector similarity with payload filtering:
- Filter first (fast): Narrow by metadata, then search
- Search first: Find similar, then filter results

### Production Features

- **Snapshots**: Point-in-time backups
- **Replication**: High availability
- **Sharding**: Horizontal scaling
- **Monitoring**: Prometheus metrics

## Files

- `1_generate_skill.py` - Package for Qdrant
- `2_upload_to_qdrant.py` - Upload to Qdrant
- `3_query_example.py` - Query examples

## Resources

- **Qdrant Docs**: https://qdrant.tech/documentation/
- **API Reference**: https://qdrant.tech/documentation/quick-start/
- **Cloud**: https://cloud.qdrant.io/

---

**Note**: Qdrant excels at production deployments with complex filtering needs. For simpler use cases, try ChromaDB.
