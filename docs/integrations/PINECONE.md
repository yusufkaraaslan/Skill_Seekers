# Using Skill Seekers with Pinecone

**Last Updated:** February 5, 2026
**Status:** Production Ready
**Difficulty:** Easy ⭐

---

## 🎯 The Problem

Building production-grade vector search applications requires:

- **Scalable Vector Database** - Handle millions of embeddings efficiently
- **Low Latency** - Sub-100ms query response times
- **High Availability** - 99.9% uptime for production apps
- **Easy Integration** - Works with any embedding model

**Example:**
> "When building a customer support bot with RAG, you need to search across 500k+ documentation chunks in <50ms. Managing your own vector database means dealing with scaling, replication, and performance optimization."

---

## ✨ The Solution

Use Skill Seekers to **prepare documentation for Pinecone**:

1. **Generate structured documents** from any source
2. **Create embeddings** with your preferred model (OpenAI, Cohere, etc.)
3. **Upsert to Pinecone** with rich metadata for filtering
4. **Query with context** - Full metadata preserved for filtering and routing

**Result:**
Skill Seekers outputs JSON format ready for Pinecone upsert with all metadata intact.

---

## 🚀 Quick Start (10 Minutes)

### Prerequisites

- Python 3.10+
- Pinecone account (free tier available)
- Embedding model API key (OpenAI or Cohere recommended)

### Installation

```bash
# Install Skill Seekers
pip install skill-seekers

# Install Pinecone client + embeddings
pip install pinecone-client openai

# Or with Cohere embeddings
pip install pinecone-client cohere
```

### Setup Pinecone

```bash
# Get API key from: https://app.pinecone.io/
export PINECONE_API_KEY=your-api-key

# Get OpenAI key for embeddings
export OPENAI_API_KEY=sk-...
```

### Generate Documents

```bash
# Example: React documentation
skill-seekers scrape --config configs/react.json

# Package for Pinecone (uses LangChain format)
skill-seekers package output/react --target langchain

# Output: output/react-langchain.json
```

### Upsert to Pinecone

```python
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import json

# Initialize clients
pc = Pinecone(api_key="your-pinecone-api-key")
openai_client = OpenAI()

# Create index (first time only)
index_name = "react-docs"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI ada-002 dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Connect to index
index = pc.Index(index_name)

# Load documents
with open("output/react-langchain.json") as f:
    documents = json.load(f)

# Create embeddings and upsert
vectors = []
for i, doc in enumerate(documents):
    # Generate embedding
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc["page_content"]
    )
    embedding = response.data[0].embedding

    # Prepare vector with metadata
    vectors.append({
        "id": f"doc_{i}",
        "values": embedding,
        "metadata": {
            "text": doc["page_content"][:1000],  # Store snippet
            "source": doc["metadata"]["source"],
            "category": doc["metadata"]["category"],
            "file": doc["metadata"]["file"],
            "type": doc["metadata"]["type"]
        }
    })

    # Batch upsert every 100 vectors
    if len(vectors) >= 100:
        index.upsert(vectors=vectors)
        vectors = []
        print(f"Upserted {i + 1} documents...")

# Upsert remaining
if vectors:
    index.upsert(vectors=vectors)

print(f"✅ Upserted {len(documents)} documents to Pinecone")
```

### Query Pinecone

```python
# Query with filters
query = "How do I use hooks in React?"

# Generate query embedding
response = openai_client.embeddings.create(
    model="text-embedding-ada-002",
    input=query
)
query_embedding = response.data[0].embedding

# Search with metadata filter
results = index.query(
    vector=query_embedding,
    top_k=3,
    include_metadata=True,
    filter={"category": {"$eq": "hooks"}}  # Filter by category
)

# Display results
for match in results["matches"]:
    print(f"Score: {match['score']:.3f}")
    print(f"Category: {match['metadata']['category']}")
    print(f"Text: {match['metadata']['text'][:200]}...")
    print()
```

---

## 📖 Detailed Setup Guide

### Step 1: Create Pinecone Index

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your-api-key")

# Choose dimensions based on your embedding model:
# - OpenAI ada-002: 1536
# - OpenAI text-embedding-3-small: 1536
# - OpenAI text-embedding-3-large: 3072
# - Cohere embed-english-v3.0: 1024

pc.create_index(
    name="my-docs",
    dimension=1536,  # Match your embedding model
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"  # Choose closest region
    )
)
```

**Available regions:**
- AWS: us-east-1, us-west-2, eu-west-1, ap-southeast-1
- GCP: us-central1, europe-west1, asia-southeast1
- Azure: eastus2, westeurope

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

### Step 3: Create Embeddings Strategy

**Strategy 1: OpenAI (Recommended)**
```python
from openai import OpenAI

client = OpenAI()

def create_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

# Cost: ~$0.0001 per 1K tokens
# Speed: ~1000 docs/minute
# Quality: Excellent for most use cases
```

**Strategy 2: Cohere**
```python
import cohere

co = cohere.Client("your-cohere-api-key")

def create_embedding(text: str) -> list[float]:
    response = co.embed(
        texts=[text],
        model="embed-english-v3.0",
        input_type="search_document"
    )
    return response.embeddings[0]

# Cost: ~$0.0001 per 1K tokens
# Speed: ~1000 docs/minute
# Quality: Excellent, especially for semantic search
```

**Strategy 3: Local Model (SentenceTransformers)**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embedding(text: str) -> list[float]:
    return model.encode(text).tolist()

# Cost: Free
# Speed: ~500-1000 docs/minute (CPU)
# Quality: Good for smaller datasets
# Note: Dimension is 384 for all-MiniLM-L6-v2
```

### Step 4: Batch Upsert Pattern

```python
import json
from typing import List, Dict
from tqdm import tqdm

def batch_upsert_documents(
    index,
    documents_path: str,
    embedding_func,
    batch_size: int = 100
):
    """
    Efficiently upsert documents to Pinecone in batches.

    Args:
        index: Pinecone index object
        documents_path: Path to Skill Seekers JSON output
        embedding_func: Function to create embeddings
        batch_size: Number of documents per batch
    """
    # Load documents
    with open(documents_path) as f:
        documents = json.load(f)

    vectors = []
    for i, doc in enumerate(tqdm(documents, desc="Upserting")):
        # Create embedding
        embedding = embedding_func(doc["page_content"])

        # Prepare vector
        vectors.append({
            "id": f"doc_{i}",
            "values": embedding,
            "metadata": {
                "text": doc["page_content"][:1000],  # Pinecone limit
                "full_text_id": str(i),  # Reference to full text
                **doc["metadata"]  # Preserve all Skill Seekers metadata
            }
        })

        # Batch upsert
        if len(vectors) >= batch_size:
            index.upsert(vectors=vectors)
            vectors = []

    # Upsert remaining
    if vectors:
        index.upsert(vectors=vectors)

    print(f"✅ Upserted {len(documents)} documents")

    # Verify index stats
    stats = index.describe_index_stats()
    print(f"Total vectors in index: {stats['total_vector_count']}")

# Usage
batch_upsert_documents(
    index=pc.Index("my-docs"),
    documents_path="output/react-langchain.json",
    embedding_func=create_embedding,
    batch_size=100
)
```

### Step 5: Query with Filters

```python
def semantic_search(
    index,
    query: str,
    embedding_func,
    top_k: int = 5,
    category: str = None,
    file: str = None
):
    """
    Semantic search with optional metadata filters.

    Args:
        index: Pinecone index
        query: Search query
        embedding_func: Embedding function
        top_k: Number of results
        category: Filter by category
        file: Filter by file
    """
    # Create query embedding
    query_embedding = embedding_func(query)

    # Build filter
    filter_dict = {}
    if category:
        filter_dict["category"] = {"$eq": category}
    if file:
        filter_dict["file"] = {"$eq": file}

    # Query
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict if filter_dict else None
    )

    return results["matches"]

# Example queries
results = semantic_search(
    index=pc.Index("react-docs"),
    query="How do I manage state?",
    embedding_func=create_embedding,
    category="hooks"  # Only search in hooks category
)

for match in results:
    print(f"Score: {match['score']:.3f}")
    print(f"Category: {match['metadata']['category']}")
    print(f"Text: {match['metadata']['text'][:200]}...")
    print()
```

---

## 🎨 Advanced Usage

### Hybrid Search (Keyword + Semantic)

```python
# Pinecone sparse-dense hybrid search
from pinecone_text.sparse import BM25Encoder

# Initialize BM25 encoder
bm25 = BM25Encoder()
bm25.fit(documents)  # Fit on your corpus

def hybrid_search(query: str, top_k: int = 5):
    # Dense embedding
    dense_embedding = create_embedding(query)

    # Sparse embedding (BM25)
    sparse_embedding = bm25.encode_queries(query)

    # Hybrid query
    results = index.query(
        vector=dense_embedding,
        sparse_vector=sparse_embedding,
        top_k=top_k,
        include_metadata=True
    )

    return results["matches"]
```

### Namespace Management

```python
# Organize documents by namespace
namespaces = {
    "stable": documents_v1,
    "beta": documents_v2,
    "archived": old_documents
}

for ns, docs in namespaces.items():
    vectors = prepare_vectors(docs)
    index.upsert(vectors=vectors, namespace=ns)

# Query specific namespace
results = index.query(
    vector=query_embedding,
    top_k=5,
    namespace="stable"  # Only query stable docs
)
```

### Metadata Filtering Patterns

```python
# Exact match
filter={"category": {"$eq": "api"}}

# Multiple values (OR)
filter={"category": {"$in": ["api", "guides"]}}

# Exclude
filter={"type": {"$ne": "deprecated"}}

# Range (for numeric metadata)
filter={"version": {"$gte": 2.0}}

# Multiple conditions (AND)
filter={
    "$and": [
        {"category": {"$eq": "api"}},
        {"version": {"$gte": 2.0}}
    ]
}
```

### RAG Pipeline Integration

```python
from openai import OpenAI

openai_client = OpenAI()

def rag_query(question: str, top_k: int = 3):
    """Complete RAG pipeline with Pinecone."""

    # 1. Retrieve relevant documents
    query_embedding = create_embedding(question)
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    # 2. Build context from results
    context_parts = []
    for match in results["matches"]:
        context_parts.append(
            f"[{match['metadata']['category']}] "
            f"{match['metadata']['text']}"
        )
    context = "\n\n".join(context_parts)

    # 3. Generate answer with LLM
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "Answer based on the provided context."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": [
            {
                "category": m["metadata"]["category"],
                "file": m["metadata"]["file"],
                "score": m["score"]
            }
            for m in results["matches"]
        ]
    }

# Usage
result = rag_query("How do I create a React component?")
print(f"Answer: {result['answer']}\n")
print("Sources:")
for source in result["sources"]:
    print(f"  - {source['category']} ({source['file']}) - Score: {source['score']:.3f}")
```

---

## 💡 Best Practices

### 1. Choose Right Index Configuration

```python
# Serverless (recommended for most cases)
spec=ServerlessSpec(
    cloud="aws",
    region="us-east-1"  # Choose closest to your users
)

# Pod-based (for high throughput, dedicated resources)
spec=PodSpec(
    environment="us-east1-gcp",
    pod_type="p1.x1",  # Small: p1.x1, Medium: p1.x2, Large: p2.x1
    pods=1,
    replicas=1
)
```

### 2. Optimize Metadata Storage

```python
# Store only essential metadata in Pinecone (max 40KB per vector)
# Keep full text elsewhere (database, object storage)

metadata = {
    "text": doc["page_content"][:1000],  # Snippet only
    "full_text_id": str(i),  # Reference to full text
    "category": doc["metadata"]["category"],
    "source": doc["metadata"]["source"],
    # Don't store: full page_content, images, binary data
}
```

### 3. Use Namespaces for Multi-Tenancy

```python
# Per-customer namespaces
namespace = f"customer_{customer_id}"
index.upsert(vectors=vectors, namespace=namespace)

# Query only customer's data
results = index.query(
    vector=query_embedding,
    namespace=namespace,
    top_k=5
)
```

### 4. Monitor Index Performance

```python
# Check index stats
stats = index.describe_index_stats()
print(f"Total vectors: {stats['total_vector_count']}")
print(f"Dimension: {stats['dimension']}")
print(f"Namespaces: {stats.get('namespaces', {})}")

# Monitor query latency
import time
start = time.time()
results = index.query(vector=query_embedding, top_k=5)
latency = time.time() - start
print(f"Query latency: {latency*1000:.2f}ms")
```

### 5. Handle Updates Efficiently

```python
# Update existing vectors (upsert with same ID)
index.upsert(vectors=[{
    "id": "doc_123",
    "values": new_embedding,
    "metadata": updated_metadata
}])

# Delete obsolete vectors
index.delete(ids=["doc_123", "doc_456"])

# Delete by metadata filter
index.delete(filter={"category": {"$eq": "deprecated"}})
```

---

## 🔥 Real-World Example: Customer Support Bot

```python
import json
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

class SupportBotRAG:
    def __init__(self, index_name: str):
        self.pc = Pinecone()
        self.index = self.pc.Index(index_name)
        self.openai = OpenAI()

    def ingest_docs(self, docs_path: str):
        """Ingest Skill Seekers documentation."""
        with open(docs_path) as f:
            documents = json.load(f)

        vectors = []
        for i, doc in enumerate(documents):
            # Create embedding
            response = self.openai.embeddings.create(
                model="text-embedding-ada-002",
                input=doc["page_content"]
            )

            vectors.append({
                "id": f"doc_{i}",
                "values": response.data[0].embedding,
                "metadata": {
                    "text": doc["page_content"][:1000],
                    **doc["metadata"]
                }
            })

            if len(vectors) >= 100:
                self.index.upsert(vectors=vectors)
                vectors = []

        if vectors:
            self.index.upsert(vectors=vectors)

        print(f"✅ Ingested {len(documents)} documents")

    def answer_question(self, question: str, category: str = None):
        """Answer customer question with RAG."""
        # Create query embedding
        response = self.openai.embeddings.create(
            model="text-embedding-ada-002",
            input=question
        )
        query_embedding = response.data[0].embedding

        # Retrieve relevant docs
        filter_dict = {"category": {"$eq": category}} if category else None
        results = self.index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True,
            filter=filter_dict
        )

        # Build context
        context = "\n\n".join([
            m["metadata"]["text"] for m in results["matches"]
        ])

        # Generate answer
        completion = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful support bot. Answer based on the provided documentation."
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
                    "category": m["metadata"]["category"],
                    "score": m["score"]
                }
                for m in results["matches"]
            ]
        }

# Usage
bot = SupportBotRAG("support-docs")
bot.ingest_docs("output/product-docs-langchain.json")

result = bot.answer_question("How do I reset my password?", category="authentication")
print(f"Answer: {result['answer']}")
```

---

## 🐛 Troubleshooting

### Issue: Dimension Mismatch Error

**Problem:** "Dimension mismatch: expected 1536, got 384"

**Solution:** Ensure embedding model dimension matches index
```python
# Check your embedding model dimension
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print(f"Model dimension: {model.get_sentence_embedding_dimension()}")  # 384

# Create index with correct dimension
pc.create_index(name="my-index", dimension=384, ...)
```

### Issue: Rate Limit Errors

**Problem:** "Rate limit exceeded"

**Solution:** Add retry logic and batching
```python
import time
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def upsert_with_retry(index, vectors):
    return index.upsert(vectors=vectors)

# Use smaller batches
batch_size = 50  # Reduce from 100
```

### Issue: High Query Latency

**Solutions:**
```python
# 1. Reduce top_k
results = index.query(vector=query_embedding, top_k=3)  # Instead of 10

# 2. Use metadata filtering to reduce search space
filter={"category": {"$eq": "api"}}

# 3. Use namespaces
namespace="high_priority_docs"

# 4. Consider pod-based index for consistent low latency
spec=PodSpec(environment="us-east1-gcp", pod_type="p1.x2")
```

### Issue: Missing Metadata

**Problem:** Metadata not returned in results

**Solution:** Enable metadata in query
```python
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True  # CRITICAL
)
```

---

## 📊 Cost Optimization

### Embedding Costs

| Provider | Model | Cost per 1M tokens | Speed |
|----------|-------|-------------------|-------|
| OpenAI | ada-002 | $0.10 | Fast |
| OpenAI | text-embedding-3-small | $0.02 | Fast |
| OpenAI | text-embedding-3-large | $0.13 | Fast |
| Cohere | embed-english-v3.0 | $0.10 | Fast |
| Local | SentenceTransformers | Free | Medium |

**Recommendation:** OpenAI text-embedding-3-small (best quality/cost ratio)

### Pinecone Costs

**Serverless (pay per use):**
- Storage: $0.01 per GB/month
- Reads: $0.025 per 100k read units
- Writes: $0.50 per 100k write units

**Pod-based (fixed cost):**
- p1.x1: ~$70/month (1GB storage, 100 QPS)
- p1.x2: ~$140/month (2GB storage, 200 QPS)
- p2.x1: ~$280/month (4GB storage, 400 QPS)

**Example costs for 100k documents:**
- Storage: ~250MB = $0.0025/month
- Writes: 100k = $0.50 one-time
- Reads: 100k queries = $0.025/month

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Documentation:** [https://skillseekersweb.com/](https://skillseekersweb.com/)
- **Pinecone Docs:** [https://docs.pinecone.io/](https://docs.pinecone.io/)

---

## 📚 Related Guides

- [LangChain Integration](./LANGCHAIN.md)
- [LlamaIndex Integration](./LLAMA_INDEX.md)
- [RAG Pipelines Overview](./RAG_PIPELINES.md)

---

## 📖 Next Steps

1. **Try the Quick Start** above
2. **Experiment with different embedding models**
3. **Build your RAG pipeline** with production-ready docs
4. **Share your experience** - we'd love feedback!

---

**Last Updated:** February 5, 2026
**Tested With:** Pinecone Serverless, OpenAI ada-002, GPT-4
**Skill Seekers Version:** v2.9.0+
