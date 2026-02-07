# Qdrant Integration with Skill Seekers

**Status:** ✅ Production Ready
**Difficulty:** Intermediate
**Last Updated:** February 7, 2026

---

## ❌ The Problem

Building RAG applications with Qdrant involves several challenges:

1. **Collection Schema Complexity** - Defining vector configurations, payload schemas, and distance metrics requires understanding Qdrant's data model
2. **Payload Filtering Setup** - Rich metadata filtering requires proper payload indexing and field types
3. **Deployment Options** - Choosing between local, Docker, cloud, or cluster mode adds configuration overhead

**Example Pain Point:**

```python
# Manual Qdrant setup for each framework
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI

# Create client + collection
client = QdrantClient(url="http://localhost:6333")
client.create_collection(
    collection_name="react_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Generate embeddings manually
openai_client = OpenAI()
points = []
for i, doc in enumerate(documents):
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc
    )
    points.append(PointStruct(
        id=i,
        vector=response.data[0].embedding,
        payload={"text": doc[:1000], "metadata": {...}}  # Manual metadata
    ))

# Upload points
client.upsert(collection_name="react_docs", points=points)
```

---

## ✅ The Solution

Skill Seekers automates Qdrant integration with structured, production-ready data:

**Benefits:**
- ✅ Auto-formatted documents with rich payload metadata
- ✅ Consistent collection structure across all frameworks
- ✅ Works with Qdrant Cloud, self-hosted, or Docker
- ✅ Advanced filtering with indexed payloads
- ✅ High-performance Rust engine (10K+ QPS)

**Result:** 10-minute setup, production-ready vector search with enterprise performance.

---

## ⚡ Quick Start (10 Minutes)

### Prerequisites

```bash
# Install Qdrant client
pip install qdrant-client>=1.7.0

# OpenAI for embeddings
pip install openai>=1.0.0

# Or with Skill Seekers
pip install skill-seekers[all-llms]
```

**What you need:**
- Qdrant instance (local, Docker, or Cloud)
- OpenAI API key (for embeddings)

### Start Qdrant (Docker)

```bash
# Start Qdrant locally
docker run -p 6333:6333 qdrant/qdrant

# Or with persistence
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### Generate Qdrant-Ready Documents

```bash
# Step 1: Scrape documentation
skill-seekers scrape --config configs/react.json

# Step 2: Package for Qdrant (creates LangChain format)
skill-seekers package output/react --target langchain

# Output: output/react-langchain.json (Qdrant-compatible)
```

### Upload to Qdrant

```python
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI

# Connect to Qdrant
client = QdrantClient(url="http://localhost:6333")
openai_client = OpenAI()

# Create collection
collection_name = "react_docs"
client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Load documents
with open("output/react-langchain.json") as f:
    documents = json.load(f)

# Generate embeddings and upload
points = []
for i, doc in enumerate(documents):
    # Generate embedding
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc["page_content"]
    )

    # Create point with payload
    points.append(PointStruct(
        id=i,
        vector=response.data[0].embedding,
        payload={
            "content": doc["page_content"],
            "source": doc["metadata"]["source"],
            "category": doc["metadata"]["category"],
            "file": doc["metadata"]["file"],
            "type": doc["metadata"]["type"]
        }
    ))

    # Batch upload every 100 points
    if len(points) >= 100:
        client.upsert(collection_name=collection_name, points=points)
        points = []
        print(f"Uploaded {i + 1} documents...")

# Upload remaining
if points:
    client.upsert(collection_name=collection_name, points=points)

print(f"✅ Uploaded {len(documents)} documents to Qdrant")
```

### Query with Filters

```python
# Search with metadata filter
results = client.search(
    collection_name="react_docs",
    query_vector=query_embedding,
    limit=3,
    query_filter={
        "must": [
            {"key": "category", "match": {"value": "hooks"}}
        ]
    }
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Category: {result.payload['category']}")
    print(f"Content: {result.payload['content'][:200]}...")
    print()
```

---

## 📖 Detailed Setup Guide

### Step 1: Deploy Qdrant

**Option A: Docker (Local Development)**

```bash
# Basic setup
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# With persistent storage
docker run -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# With configuration
docker run -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  -v $(pwd)/qdrant_config.yaml:/qdrant/config/production.yaml \
  qdrant/qdrant
```

**Option B: Qdrant Cloud (Production)**

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a cluster (free tier available)
3. Get your API endpoint and API key
4. Note your cluster URL: `https://your-cluster.qdrant.io`

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key"
)
```

**Option C: Self-Hosted Binary**

```bash
# Download Qdrant
wget https://github.com/qdrant/qdrant/releases/download/v1.7.0/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz

# Run Qdrant
./qdrant

# Access at http://localhost:6333
```

**Option D: Kubernetes (Production Cluster)**

```bash
helm repo add qdrant https://qdrant.to/helm
helm install qdrant qdrant/qdrant

# With custom values
helm install qdrant qdrant/qdrant -f values.yaml
```

### Step 2: Generate Skill Seekers Documents

**Option A: Documentation Website**
```bash
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target langchain
```

**Option B: GitHub Repository**
```bash
skill-seekers github --repo django/django --name django
skill-seekers package output/django --target langchain
```

**Option C: Local Codebase**
```bash
skill-seekers analyze --directory /path/to/repo
skill-seekers package output/codebase --target langchain
```

**Option D: RAG-Optimized Chunking**
```bash
skill-seekers scrape --config configs/fastapi.json --chunk-for-rag --chunk-size 512
skill-seekers package output/fastapi --target langchain
```

### Step 3: Create Collection with Payload Schema

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

client = QdrantClient(url="http://localhost:6333")

# Create collection with vector config
client.recreate_collection(
    collection_name="documentation",
    vectors_config=VectorParams(
        size=1536,  # OpenAI ada-002 dimension
        distance=Distance.COSINE  # or EUCLID, DOT
    )
)

# Create payload indexes for filtering (optional but recommended)
client.create_payload_index(
    collection_name="documentation",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="documentation",
    field_name="source",
    field_schema=PayloadSchemaType.KEYWORD
)

print("✅ Collection created with payload indexes")
```

### Step 4: Batch Upload with Progress

```python
import json
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI

client = QdrantClient(url="http://localhost:6333")
openai_client = OpenAI()

# Load documents
with open("output/django-langchain.json") as f:
    documents = json.load(f)

# Batch upload with progress
batch_size = 100
collection_name = "documentation"

for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    points = []

    for j, doc in enumerate(batch):
        # Generate embedding
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=doc["page_content"]
        )

        # Create point
        points.append(PointStruct(
            id=i + j,
            vector=response.data[0].embedding,
            payload={
                "content": doc["page_content"],
                "source": doc["metadata"]["source"],
                "category": doc["metadata"]["category"],
                "file": doc["metadata"]["file"],
                "type": doc["metadata"]["type"],
                "url": doc["metadata"].get("url", "")
            }
        ))

    # Upload batch
    client.upsert(collection_name=collection_name, points=points)
    print(f"Uploaded {min(i + batch_size, len(documents))}/{len(documents)}...")

print(f"✅ Uploaded {len(documents)} documents to Qdrant")

# Verify upload
info = client.get_collection(collection_name)
print(f"Collection size: {info.points_count}")
```

### Step 5: Advanced Querying

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue
from openai import OpenAI

openai_client = OpenAI()

# Generate query embedding
query = "How do I use Django models?"
response = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input=query
)
query_embedding = response.data[0].embedding

# Simple search
results = client.search(
    collection_name="documentation",
    query_vector=query_embedding,
    limit=5
)

# Search with single filter
results = client.search(
    collection_name="documentation",
    query_vector=query_embedding,
    limit=5,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="models")
            )
        ]
    )
)

# Search with multiple filters (AND logic)
results = client.search(
    collection_name="documentation",
    query_vector=query_embedding,
    limit=5,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="models")),
            FieldCondition(key="type", match=MatchValue(value="tutorial"))
        ]
    )
)

# Search with OR logic
results = client.search(
    collection_name="documentation",
    query_vector=query_embedding,
    limit=5,
    query_filter=Filter(
        should=[
            FieldCondition(key="category", match=MatchValue(value="models")),
            FieldCondition(key="category", match=MatchValue(value="views"))
        ]
    )
)

# Extract results
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Category: {result.payload['category']}")
    print(f"Content: {result.payload['content'][:200]}...")
    print()
```

---

## 🚀 Advanced Usage

### 1. Named Vectors for Multi-Model Embeddings

```python
from qdrant_client.models import VectorParams, Distance

# Create collection with multiple vector spaces
client.recreate_collection(
    collection_name="documentation",
    vectors_config={
        "text-ada-002": VectorParams(size=1536, distance=Distance.COSINE),
        "cohere-v3": VectorParams(size=1024, distance=Distance.COSINE)
    }
)

# Upload with multiple vectors
point = PointStruct(
    id=1,
    vector={
        "text-ada-002": openai_embedding,
        "cohere-v3": cohere_embedding
    },
    payload={"content": "..."}
)

# Search specific vector
results = client.search(
    collection_name="documentation",
    query_vector=("text-ada-002", query_embedding),
    limit=5
)
```

### 2. Scroll API for Large Result Sets

```python
# Retrieve all points matching filter (pagination)
offset = None
all_results = []

while True:
    results = client.scroll(
        collection_name="documentation",
        scroll_filter=Filter(
            must=[FieldCondition(key="category", match=MatchValue(value="api"))]
        ),
        limit=100,
        offset=offset
    )

    points, next_offset = results
    all_results.extend(points)

    if next_offset is None:
        break
    offset = next_offset

print(f"Retrieved {len(all_results)} total points")
```

### 3. Snapshot and Backup

```python
# Create snapshot
snapshot_info = client.create_snapshot(collection_name="documentation")
snapshot_name = snapshot_info.name

print(f"Created snapshot: {snapshot_name}")

# Download snapshot
client.download_snapshot(
    collection_name="documentation",
    snapshot_name=snapshot_name,
    output_path=f"./backups/{snapshot_name}"
)

# Restore from snapshot
client.restore_snapshot(
    collection_name="documentation",
    snapshot_path=f"./backups/{snapshot_name}"
)
```

### 4. Clustering and Sharding

```python
# Create collection with sharding
from qdrant_client.models import ShardingMethod

client.recreate_collection(
    collection_name="large_docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    shard_number=4,  # Distribute across 4 shards
    sharding_method=ShardingMethod.AUTO
)

# Points automatically distributed across shards
```

### 5. Recommendation API

```python
# Find similar documents to existing ones
results = client.recommend(
    collection_name="documentation",
    positive=[1, 5, 10],  # Point IDs to find similar to
    negative=[15],  # Point IDs to avoid
    limit=5
)

# Recommend with filters
results = client.recommend(
    collection_name="documentation",
    positive=[1, 5, 10],
    limit=5,
    query_filter=Filter(
        must=[FieldCondition(key="category", match=MatchValue(value="hooks"))]
    )
)
```

---

## 📋 Best Practices

### 1. Create Payload Indexes for Frequent Filters

```python
# Index fields you filter on frequently
client.create_payload_index(
    collection_name="documentation",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)

# Dramatically speeds up filtered search
# Before: 500ms, After: 10ms
```

### 2. Choose the Right Distance Metric

```python
# Cosine: Best for normalized embeddings (OpenAI, Cohere)
vectors_config=VectorParams(size=1536, distance=Distance.COSINE)

# Euclidean: For absolute distances
vectors_config=VectorParams(size=1536, distance=Distance.EUCLID)

# Dot Product: For unnormalized vectors
vectors_config=VectorParams(size=1536, distance=Distance.DOT)

# Recommendation: Use COSINE for most cases
```

### 3. Use Batch Upsert for Performance

```python
# ✅ Good: Batch upsert (100-1000 points)
points = [...]  # 100 points
client.upsert(collection_name="docs", points=points)

# ❌ Bad: One at a time (slow!)
for point in points:
    client.upsert(collection_name="docs", points=[point])

# Batch is 10-100x faster
```

### 4. Monitor Collection Stats

```python
# Get collection info
info = client.get_collection("documentation")
print(f"Points: {info.points_count}")
print(f"Vectors: {info.vectors_count}")
print(f"Indexed: {info.indexed_vectors_count}")
print(f"Status: {info.status}")

# Check cluster info
cluster_info = client.get_cluster_info()
print(f"Peers: {len(cluster_info.peers)}")
```

### 5. Use Wait Parameter for Consistency

```python
# Ensure point is indexed before returning
from qdrant_client.models import UpdateStatus

result = client.upsert(
    collection_name="documentation",
    points=points,
    wait=True  # Wait until indexed
)

assert result.status == UpdateStatus.COMPLETED
```

---

## 🔥 Real-World Example: Multi-Tenant Documentation System

```python
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from openai import OpenAI

class MultiTenantDocsSystem:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        """Initialize multi-tenant documentation system."""
        self.client = QdrantClient(url=qdrant_url)
        self.openai = OpenAI()

    def create_tenant_collection(self, tenant: str):
        """Create collection for a tenant."""
        collection_name = f"docs_{tenant}"

        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )

        # Create indexes for common filters
        for field in ["category", "source", "type"]:
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema="keyword"
            )

        print(f"✅ Created collection for tenant: {tenant}")

    def ingest_tenant_docs(self, tenant: str, docs_path: str):
        """Ingest documentation for a tenant."""
        collection_name = f"docs_{tenant}"

        with open(docs_path) as f:
            documents = json.load(f)

        # Batch upload
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            points = []

            for j, doc in enumerate(batch):
                # Generate embedding
                response = self.openai.embeddings.create(
                    model="text-embedding-ada-002",
                    input=doc["page_content"]
                )

                points.append(PointStruct(
                    id=i + j,
                    vector=response.data[0].embedding,
                    payload={
                        "content": doc["page_content"],
                        "tenant": tenant,
                        **doc["metadata"]
                    }
                ))

            self.client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True
            )

        print(f"✅ Ingested {len(documents)} docs for {tenant}")

    def query_tenant(self, tenant: str, question: str, category: str = None):
        """Query specific tenant's documentation."""
        collection_name = f"docs_{tenant}"

        # Generate query embedding
        response = self.openai.embeddings.create(
            model="text-embedding-ada-002",
            input=question
        )
        query_embedding = response.data[0].embedding

        # Build filter
        query_filter = None
        if category:
            query_filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value=category))]
            )

        # Search
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=5,
            query_filter=query_filter
        )

        # Build context
        context = "\n\n".join([r.payload["content"][:500] for r in results])

        # Generate answer
        completion = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful assistant for {tenant} documentation."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}"
                }
            ]
        )

        return {
            "answer": completion.choices[0].message.content,
            "sources": [
                {
                    "category": r.payload["category"],
                    "score": r.score
                }
                for r in results
            ]
        }

    def cross_tenant_search(self, question: str, tenants: list[str]):
        """Search across multiple tenants."""
        all_results = {}

        for tenant in tenants:
            try:
                result = self.query_tenant(tenant, question)
                all_results[tenant] = result["answer"]
            except Exception as e:
                all_results[tenant] = f"Error: {e}"

        return all_results

# Usage
system = MultiTenantDocsSystem()

# Set up tenants
tenants = ["react", "vue", "angular"]
for tenant in tenants:
    system.create_tenant_collection(tenant)
    system.ingest_tenant_docs(tenant, f"output/{tenant}-langchain.json")

# Query specific tenant
result = system.query_tenant("react", "How do I use hooks?", category="hooks")
print(f"React Answer: {result['answer']}")

# Cross-tenant search
comparison = system.cross_tenant_search(
    question="How do I handle state?",
    tenants=["react", "vue", "angular"]
)

for tenant, answer in comparison.items():
    print(f"\n{tenant.upper()}:")
    print(answer[:200] + "...")
```

---

## 🐛 Troubleshooting

### Issue: Connection Refused

**Problem:** "Connection refused at http://localhost:6333"

**Solutions:**

1. **Check Qdrant is running:**
```bash
curl http://localhost:6333/healthz
docker ps | grep qdrant
```

2. **Verify ports:**
```bash
# API: 6333, gRPC: 6334
lsof -i :6333
```

3. **Check Docker logs:**
```bash
docker logs <qdrant-container-id>
```

### Issue: Point Upload Failed

**Problem:** "Point with id X already exists"

**Solutions:**

1. **Use upsert instead of upload:**
```python
# Upsert replaces existing points
client.upsert(collection_name="docs", points=points)
```

2. **Delete and recreate:**
```python
client.delete_collection("docs")
client.recreate_collection(...)
```

### Issue: Slow Filtered Search

**Problem:** Filtered queries take >1 second

**Solutions:**

1. **Create payload index:**
```python
client.create_payload_index(
    collection_name="docs",
    field_name="category",
    field_schema="keyword"
)
```

2. **Check index status:**
```python
info = client.get_collection("docs")
print(f"Indexed: {info.indexed_vectors_count}/{info.points_count}")
```

---

## 📊 Before vs. After

| Aspect | Without Skill Seekers | With Skill Seekers |
|--------|----------------------|-------------------|
| **Data Preparation** | Custom scraping + parsing logic | One command: `skill-seekers scrape` |
| **Collection Setup** | Manual vector config + payload schema | Standard LangChain format |
| **Metadata** | Manual extraction from docs | Auto-extracted (category, source, file, type) |
| **Payload Filtering** | Complex filter construction | Consistent metadata keys |
| **Performance** | 10K+ QPS (Rust engine) | 10K+ QPS (same, but easier setup) |
| **Setup Time** | 3-5 hours | 10 minutes |
| **Code Required** | 400+ lines | 30 lines upload script |

---

## 🎯 Next Steps

### Related Guides

- **[Weaviate Integration](WEAVIATE.md)** - Alternative vector database
- **[RAG Pipelines Guide](RAG_PIPELINES.md)** - Build complete RAG systems
- **[Multi-LLM Support](MULTI_LLM_SUPPORT.md)** - Use different embedding models
- **[INTEGRATIONS.md](INTEGRATIONS.md)** - See all integration options

### Resources

- **Qdrant Docs:** https://qdrant.tech/documentation/
- **Python Client:** https://qdrant.tech/documentation/quick-start/
- **Support:** https://github.com/yusufkaraaslan/Skill_Seekers/discussions

---

**Questions?** Open an issue: https://github.com/yusufkaraaslan/Skill_Seekers/issues
**Website:** https://skillseekersweb.com/
**Last Updated:** February 7, 2026
