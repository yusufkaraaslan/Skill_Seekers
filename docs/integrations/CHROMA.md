# Chroma Integration with Skill Seekers

**Status:** ✅ Production Ready
**Difficulty:** Beginner
**Last Updated:** February 7, 2026

---

## ❌ The Problem

Building RAG applications with Chroma involves several challenges:

1. **Embedding Model Setup** - Need to choose and configure embedding models (local vs API) manually
2. **Collection Management** - Creating and managing collections with metadata requires boilerplate code
3. **Local-First Complexity** - Setting up persistent storage and dealing with file paths

**Example Pain Point:**

```python
# Manual embedding + collection setup for each framework
import chromadb
from chromadb.utils import embedding_functions

# Choose embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="sk-...",
    model_name="text-embedding-ada-002"
)

# Create client + collection
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.create_collection(
    name="react_docs",
    embedding_function=openai_ef,
    metadata={"description": "React documentation"}
)

# Manually parse and add documents...
```

---

## ✅ The Solution

Skill Seekers automates Chroma integration with structured, production-ready data:

**Benefits:**
- ✅ Auto-formatted documents with embeddings included
- ✅ Consistent collection structure across all frameworks
- ✅ Works with local models (Sentence Transformers) or API embeddings (OpenAI, Cohere)
- ✅ Persistent storage with automatic path management
- ✅ Metadata-rich for precise filtering

**Result:** 5-minute setup, production-ready local vector search with zero external dependencies.

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites

```bash
# Install Chroma
pip install chromadb>=0.4.22

# For local embeddings (optional, free)
pip install sentence-transformers

# For OpenAI embeddings (optional)
pip install openai

# Or with Skill Seekers
pip install skill-seekers[all-llms]
```

**What you need:**
- Python 3.10+
- No external services required (fully local!)
- Optional: OpenAI API key for better embeddings

### Generate Chroma-Ready Documents

```bash
# Step 1: Scrape documentation
skill-seekers scrape --config configs/react.json

# Step 2: Package for Chroma (creates LangChain format)
skill-seekers package output/react --target langchain

# Output: output/react-langchain.json (Chroma-compatible)
```

### Upload to Chroma (Local)

```python
import chromadb
import json

# Create persistent client (data saved to disk)
client = chromadb.PersistentClient(path="./chroma_db")

# Create collection with local embeddings (free!)
collection = client.get_or_create_collection(
    name="react_docs",
    metadata={"description": "React documentation from Skill Seekers"}
)

# Load documents
with open("output/react-langchain.json") as f:
    documents = json.load(f)

# Add to collection (Chroma generates embeddings automatically)
collection.add(
    documents=[doc["page_content"] for doc in documents],
    metadatas=[doc["metadata"] for doc in documents],
    ids=[f"doc_{i}" for i in range(len(documents))]
)

print(f"✅ Added {len(documents)} documents to Chroma")
print(f"Total in collection: {collection.count()}")
```

### Query with Filters

```python
# Semantic search with metadata filter
results = collection.query(
    query_texts=["How do I use React hooks?"],
    n_results=3,
    where={"category": "hooks"}  # Filter by category
)

for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
    print(f"\n{i+1}. Category: {metadata['category']}")
    print(f"   Source: {metadata['source']}")
    print(f"   Content: {doc[:200]}...")
```

**That's it!** Chroma is now running locally with your documentation.

---

## 📖 Detailed Setup Guide

### Step 1: Choose Storage Mode

**Option A: Persistent (Recommended for Production)**

```python
import chromadb

# Data persists to disk
client = chromadb.PersistentClient(
    path="./chroma_db"  # Specify database directory
)

# Database files saved to ./chroma_db/
# Survives script restarts
```

**Option B: In-Memory (Fast, for Development)**

```python
# Data lost when script ends
client = chromadb.Client()

# Fast, but temporary
# Perfect for experimentation
```

**Option C: HTTP Client (Remote Chroma Server)**

```bash
# Start Chroma server
chroma run --path ./chroma_db --port 8000
```

```python
# Connect to remote server
client = chromadb.HttpClient(host="localhost", port=8000)

# Great for microservices architecture
```

**Option D: Docker (Production)**

```bash
# docker-compose.yml
version: '3'
services:
  chroma:
    image: ghcr.io/chroma-core/chroma:latest
    volumes:
      - ./chroma-data:/chroma/chroma
    ports:
      - "8000:8000"
    environment:
      - ANONYMIZED_TELEMETRY=False

# Start Chroma
docker-compose up -d
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

### Step 3: Choose Embedding Function

**Option A: Default (Sentence Transformers - Free)**

```python
# Chroma uses all-MiniLM-L6-v2 by default
collection = client.get_or_create_collection(name="docs")

# Automatically downloads model on first use (~90MB)
# Dimensions: 384
# Speed: ~500 docs/sec on CPU
# Quality: Good for most use cases
```

**Option B: OpenAI (Best Quality)**

```python
from chromadb.utils import embedding_functions

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="sk-...",
    model_name="text-embedding-ada-002"
)

collection = client.get_or_create_collection(
    name="docs",
    embedding_function=openai_ef
)

# Cost: ~$0.0001 per 1K tokens
# Dimensions: 1536
# Quality: Excellent
```

**Option C: Local Sentence Transformers (Customizable)**

```python
from chromadb.utils import embedding_functions

sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"  # Better quality than default
)

collection = client.get_or_create_collection(
    name="docs",
    embedding_function=sentence_transformer_ef
)

# Free, local, customizable
# Dimensions: 768 (all-mpnet-base-v2)
# Quality: Better than default
```

**Option D: Cohere**

```python
cohere_ef = embedding_functions.CohereEmbeddingFunction(
    api_key="your-cohere-key",
    model_name="embed-english-v3.0"
)

collection = client.get_or_create_collection(
    name="docs",
    embedding_function=cohere_ef
)
```

### Step 4: Add Documents with Metadata

```python
import json

# Load Skill Seekers documents
with open("output/django-langchain.json") as f:
    documents = json.load(f)

# Prepare for Chroma
docs_content = []
docs_metadata = []
docs_ids = []

for i, doc in enumerate(documents):
    docs_content.append(doc["page_content"])
    docs_metadata.append(doc["metadata"])
    docs_ids.append(f"doc_{i}")

# Add to collection (batch operation)
collection.add(
    documents=docs_content,
    metadatas=docs_metadata,
    ids=docs_ids
)

print(f"✅ Added {len(documents)} documents")
print(f"Collection size: {collection.count()}")
```

### Step 5: Query with Advanced Filters

```python
# Simple query
results = collection.query(
    query_texts=["How do I create models?"],
    n_results=5
)

# With metadata filter
results = collection.query(
    query_texts=["Django authentication"],
    n_results=3,
    where={"category": "authentication"}
)

# Multiple filters (AND logic)
results = collection.query(
    query_texts=["user registration"],
    n_results=3,
    where={
        "$and": [
            {"category": "authentication"},
            {"type": "tutorial"}
        ]
    }
)

# Filter with OR
results = collection.query(
    query_texts=["components"],
    n_results=5,
    where={
        "$or": [
            {"category": "components"},
            {"category": "hooks"}
        ]
    }
)

# Filter with IN
results = collection.query(
    query_texts=["data handling"],
    n_results=5,
    where={"category": {"$in": ["models", "views", "serializers"]}}
)

# Extract results
for doc, metadata, distance in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
):
    print(f"Distance: {distance:.3f}")
    print(f"Category: {metadata['category']}")
    print(f"Content: {doc[:200]}...")
    print()
```

---

## 🚀 Advanced Usage

### 1. Multiple Collections for Different Frameworks

```python
# Create separate collections
frameworks = ["react", "vue", "angular", "svelte"]

for framework in frameworks:
    collection = client.get_or_create_collection(
        name=f"{framework}_docs",
        metadata={
            "framework": framework,
            "version": "latest",
            "last_updated": "2026-02-07"
        }
    )

    # Load framework-specific documents
    with open(f"output/{framework}-langchain.json") as f:
        docs = json.load(f)

    collection.add(
        documents=[d["page_content"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
        ids=[f"doc_{i}" for i in range(len(docs))]
    )

# Query specific framework
react_collection = client.get_collection(name="react_docs")
results = react_collection.query(
    query_texts=["useState hook"],
    n_results=3
)
```

### 2. Update Documents Efficiently

```python
# Update existing document (same ID)
collection.update(
    ids=["doc_42"],
    documents=["Updated content for React hooks..."],
    metadatas=[{"category": "hooks", "updated": "2026-02-07"}]
)

# Upsert (update or insert)
collection.upsert(
    ids=["doc_42"],
    documents=["New or updated content..."],
    metadatas=[{"category": "hooks"}]
)

# Delete specific documents
collection.delete(ids=["doc_42", "doc_99"])

# Delete by filter
collection.delete(where={"category": "deprecated"})
```

### 3. Pre-Compute Embeddings for Faster Ingestion

```python
from chromadb.utils import embedding_functions
import openai

# Generate embeddings separately
openai_client = openai.OpenAI()
embeddings = []

for doc in documents:
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc["page_content"]
    )
    embeddings.append(response.data[0].embedding)

# Add with pre-computed embeddings (faster)
collection.add(
    documents=[d["page_content"] for d in documents],
    embeddings=embeddings,  # Skip embedding generation
    metadatas=[d["metadata"] for d in documents],
    ids=[f"doc_{i}" for i in range(len(documents))]
)
```

### 4. Hybrid Search (Vector + Keyword)

```python
# Get all documents matching keyword filter
results = collection.query(
    query_texts=["state management"],
    n_results=100,  # Get many candidates
    where_document={"$contains": "useState"}  # Keyword filter
)

# Chroma re-ranks by semantic similarity
# Results contain "useState" AND are semantically similar to "state management"
```

### 5. Collection Management

```python
# List all collections
collections = client.list_collections()
for collection in collections:
    print(f"{collection.name}: {collection.count()} documents")
    print(f"  Metadata: {collection.metadata}")

# Get collection info
collection = client.get_collection(name="react_docs")
print(f"Count: {collection.count()}")
print(f"Metadata: {collection.metadata}")

# Delete collection
client.delete_collection(name="old_docs")

# Rename collection (create new, copy data, delete old)
old = client.get_collection(name="react_docs")
new = client.create_collection(name="react_docs_v2")

# Copy all documents
old_data = old.get()
new.add(
    ids=old_data["ids"],
    documents=old_data["documents"],
    metadatas=old_data["metadatas"],
    embeddings=old_data["embeddings"]
)

client.delete_collection(name="react_docs")
```

---

## 📋 Best Practices

### 1. Use Persistent Storage for Production

```python
# ✅ Good: Data persists
client = chromadb.PersistentClient(path="./chroma_db")

# ❌ Bad: Data lost on restart
client = chromadb.Client()

# Store DB in appropriate location
import os
db_path = os.path.expanduser("~/.local/share/my_app/chroma_db")
client = chromadb.PersistentClient(path=db_path)
```

### 2. Batch Operations for Large Datasets

```python
# ✅ Good: Batch add (fast)
batch_size = 1000
for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    collection.add(
        documents=[d["page_content"] for d in batch],
        metadatas=[d["metadata"] for d in batch],
        ids=[f"doc_{i+j}" for j in range(len(batch))]
    )
    print(f"Added {i + len(batch)}/{len(documents)}...")

# ❌ Bad: One at a time (slow)
for i, doc in enumerate(documents):
    collection.add(
        documents=[doc["page_content"]],
        metadatas=[doc["metadata"]],
        ids=[f"doc_{i}"]
    )
```

### 3. Choose Embedding Model Wisely

```python
# For speed (local development):
# - Default Chroma (all-MiniLM-L6-v2): 384 dims, fast
collection = client.get_or_create_collection(name="docs")

# For quality (production):
# - OpenAI ada-002: 1536 dims, best quality
openai_ef = embedding_functions.OpenAIEmbeddingFunction(...)
collection = client.get_or_create_collection(name="docs", embedding_function=openai_ef)

# For balance (offline production):
# - all-mpnet-base-v2: 768 dims, good quality, free
mpnet_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)
collection = client.get_or_create_collection(name="docs", embedding_function=mpnet_ef)
```

### 4. Use Metadata Filters to Reduce Search Space

```python
# ✅ Good: Filter then search (fast)
results = collection.query(
    query_texts=["authentication"],
    n_results=3,
    where={"category": "auth"}  # Only search auth docs
)

# ❌ Slow: Search everything, filter later
results = collection.query(
    query_texts=["authentication"],
    n_results=100
)
filtered = [r for r in results if r["metadata"]["category"] == "auth"]
```

### 5. Handle Updates with Upsert

```python
# ✅ Good: Upsert (idempotent)
collection.upsert(
    ids=["doc_42"],
    documents=["Updated content..."],
    metadatas=[{"updated": "2026-02-07"}]
)

# ❌ Bad: Delete then add (race conditions)
try:
    collection.delete(ids=["doc_42"])
except:
    pass
collection.add(ids=["doc_42"], ...)
```

---

## 🔥 Real-World Example: Local RAG Chatbot

```python
import chromadb
import json
from openai import OpenAI

class LocalRAGChatbot:
    def __init__(self, db_path: str = "./chroma_db"):
        """Initialize chatbot with local Chroma database."""
        self.client = chromadb.PersistentClient(path=db_path)
        self.openai = OpenAI()  # For chat completion only
        self.collection = None

    def ingest_framework(self, framework: str, docs_path: str):
        """Ingest documentation for a framework."""
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=f"{framework}_docs",
            metadata={"framework": framework}
        )

        # Load documents
        with open(docs_path) as f:
            documents = json.load(f)

        # Batch add (Chroma generates embeddings locally)
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            self.collection.add(
                documents=[d["page_content"] for d in batch],
                metadatas=[d["metadata"] for d in batch],
                ids=[f"doc_{i+j}" for j in range(len(batch))]
            )

            if (i + batch_size) < len(documents):
                print(f"Ingested {i + batch_size}/{len(documents)}...")

        print(f"✅ Ingested {len(documents)} documents for {framework}")
        print(f"Collection size: {self.collection.count()}")

    def chat(self, question: str, category: str = None):
        """Answer question using RAG."""
        if not self.collection:
            raise ValueError("No framework ingested. Call ingest_framework() first.")

        # Retrieve relevant documents
        where_filter = {"category": category} if category else None

        results = self.collection.query(
            query_texts=[question],
            n_results=5,
            where=where_filter
        )

        # Build context from results
        context_parts = []
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            context_parts.append(f"[{metadata['category']}] {doc}")

        context = "\n\n".join(context_parts)

        # Generate answer using GPT-4
        completion = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer based on the provided documentation context."
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
                    "category": m["category"],
                    "source": m["source"],
                    "file": m["file"]
                }
                for m in results["metadatas"][0]
            ],
            "context_used": len(context)
        }

    def list_frameworks(self):
        """List all ingested frameworks."""
        collections = self.client.list_collections()
        return [
            {
                "name": c.name,
                "count": c.count(),
                "metadata": c.metadata
            }
            for c in collections
        ]

# Usage
chatbot = LocalRAGChatbot(db_path="./my_docs_db")

# Ingest multiple frameworks
chatbot.ingest_framework("react", "output/react-langchain.json")
chatbot.ingest_framework("django", "output/django-langchain.json")

# Interactive chat
frameworks = chatbot.list_frameworks()
print(f"Available frameworks: {[f['name'] for f in frameworks]}")

# Select framework
chatbot.collection = chatbot.client.get_collection("react_docs")

# Ask questions
questions = [
    "How do I use useState?",
    "What is useEffect for?",
    "How do I handle form input?"
]

for question in questions:
    print(f"\nQ: {question}")
    result = chatbot.chat(question, category="hooks")
    print(f"A: {result['answer']}")
    print(f"Sources: {[s['file'] for s in result['sources'][:2]]}")
    print(f"Context size: {result['context_used']} chars")
```

**Output:**
```
✅ Ingested 1247 documents for react
Collection size: 1247
✅ Ingested 892 documents for django
Collection size: 892

Available frameworks: ['react_docs', 'django_docs']

Q: How do I use useState?
A: useState is a React Hook that lets you add state to functional components.
   Call it at the top level: const [count, setCount] = useState(0)
Sources: ['hooks/useState.md', 'hooks/overview.md']
Context size: 2340 chars

Q: What is useEffect for?
A: useEffect performs side effects in functional components, like fetching data,
   subscriptions, or DOM manipulation. It runs after render.
Sources: ['hooks/useEffect.md', 'hooks/rules.md']
Context size: 2156 chars
```

---

## 🐛 Troubleshooting

### Issue: Model Download Stuck

**Problem:** "Downloading model..." hangs indefinitely

**Solutions:**

1. **Check internet connection:**
```bash
curl -I https://huggingface.co
```

2. **Manually download model:**
```python
from sentence_transformers import SentenceTransformer

# Force download
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model downloaded!")
```

3. **Use pre-downloaded model:**
```python
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="/path/to/local/model"
)
```

### Issue: Dimension Mismatch

**Problem:** "Dimensionality mismatch: expected 384, got 1536"

**Solution:** Collections remember their embedding function
```python
# Delete and recreate with correct embedding function
client.delete_collection(name="docs")

openai_ef = embedding_functions.OpenAIEmbeddingFunction(...)
collection = client.create_collection(
    name="docs",
    embedding_function=openai_ef  # 1536 dims
)
```

### Issue: Slow Queries

**Problem:** Queries take >1 second on 10K documents

**Solutions:**

1. **Use smaller n_results:**
```python
# ✅ Fast: Get only what you need
results = collection.query(query_texts=["..."], n_results=5)

# ❌ Slow: Large result sets
results = collection.query(query_texts=["..."], n_results=100)
```

2. **Filter with metadata:**
```python
# ✅ Fast: Reduce search space
results = collection.query(
    query_texts=["..."],
    n_results=5,
    where={"category": "specific"}  # Only search subset
)
```

3. **Use HttpClient for parallelism:**
```bash
# Start Chroma server
chroma run --path ./chroma_db
```

```python
# Connect multiple clients
client = chromadb.HttpClient(host="localhost", port=8000)
```

### Issue: Database Locked

**Problem:** "Database is locked" error

**Solutions:**

1. **Check for other processes:**
```bash
lsof ./chroma_db/chroma.sqlite3
# Kill any hung processes
```

2. **Use HttpClient instead:**
```bash
chroma run --path ./chroma_db --port 8000
```

```python
client = chromadb.HttpClient(host="localhost", port=8000)
```

3. **Enable WAL mode (Write-Ahead Logging):**
```python
import sqlite3
conn = sqlite3.connect("./chroma_db/chroma.sqlite3")
conn.execute("PRAGMA journal_mode=WAL")
conn.close()
```

### Issue: Collection Not Found

**Problem:** "Collection 'docs' does not exist"

**Solutions:**

1. **List existing collections:**
```python
collections = client.list_collections()
print([c.name for c in collections])
```

2. **Use get_or_create:**
```python
# ✅ Safe: Creates if missing
collection = client.get_or_create_collection(name="docs")

# ❌ Fails if missing
collection = client.get_collection(name="docs")
```

### Issue: Out of Memory

**Problem:** Python crashes when adding large dataset

**Solutions:**

1. **Batch with smaller size:**
```python
batch_size = 500  # Reduce from 1000
for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    collection.add(...)
```

2. **Use HttpClient + server:**
```bash
# Server handles memory better
chroma run --path ./chroma_db
```

3. **Pre-compute embeddings externally:**
```python
# Generate embeddings in separate script
# Then add with embeddings parameter
collection.add(
    documents=[...],
    embeddings=precomputed_embeddings,
    ...
)
```

---

## 📊 Before vs. After

| Aspect | Without Skill Seekers | With Skill Seekers |
|--------|----------------------|-------------------|
| **Data Preparation** | Custom scraping + parsing logic | One command: `skill-seekers scrape` |
| **Embedding Setup** | Manual model selection and config | Auto-configured with sensible defaults |
| **Metadata** | Manual extraction from docs | Auto-extracted (category, source, file, type) |
| **Storage** | Complex path management | Simple: `PersistentClient(path="...")` |
| **Local-First** | Requires external services | Fully local with Sentence Transformers |
| **Setup Time** | 2-4 hours | 5 minutes |
| **Code Required** | 300+ lines scraping logic | 20 lines upload script |
| **External Deps** | OpenAI API required | Optional (works offline!) |

---

## 🎯 Next Steps

### Enhance Your Chroma Integration

1. **Try Different Embedding Models:**
   ```python
   # Better quality (still local)
   ef = embedding_functions.SentenceTransformerEmbeddingFunction(
       model_name="all-mpnet-base-v2"
   )
   ```

2. **Implement Semantic Chunking:**
   ```bash
   skill-seekers scrape --config configs/fastapi.json --chunk-for-rag --chunk-size 512
   ```

3. **Set Up Multi-Collection Search:**
   ```python
   # Search across multiple frameworks
   for name in ["react_docs", "vue_docs", "angular_docs"]:
       collection = client.get_collection(name)
       results = collection.query(...)
   ```

4. **Deploy with Docker:**
   ```bash
   docker run -p 8000:8000 -v ./chroma-data:/chroma/chroma ghcr.io/chroma-core/chroma:latest
   ```

### Related Guides

- **[LangChain Integration](LANGCHAIN.md)** - Use Chroma as vector store in LangChain
- **[LlamaIndex Integration](LLAMA_INDEX.md)** - Use Chroma with LlamaIndex
- **[RAG Pipelines Guide](RAG_PIPELINES.md)** - Build complete RAG systems
- **[INTEGRATIONS.md](INTEGRATIONS.md)** - See all integration options

### Resources

- **Chroma Docs:** https://docs.trychroma.com/
- **Python Client:** https://docs.trychroma.com/reference/py-client
- **Support:** https://github.com/yusufkaraaslan/Skill_Seekers/discussions

---

**Questions?** Open an issue: https://github.com/yusufkaraaslan/Skill_Seekers/issues
**Website:** https://skillseekersweb.com/
**Last Updated:** February 7, 2026
