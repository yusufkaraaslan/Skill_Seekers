# FAISS Integration with Skill Seekers

**Status:** ✅ Production Ready
**Difficulty:** Intermediate
**Last Updated:** February 7, 2026

---

## ❌ The Problem

Building RAG applications with FAISS involves several challenges:

1. **Manual Index Configuration** - Choosing the right FAISS index type (Flat, IVF, HNSW, PQ) requires deep understanding
2. **Embedding Management** - Need to generate and store embeddings separately, track document IDs manually
3. **Billion-Scale Complexity** - Optimizing for large datasets (>1M vectors) requires index training and parameter tuning

**Example Pain Point:**

```python
# Manual FAISS setup for each framework
import faiss
import numpy as np
from openai import OpenAI

# Generate embeddings
client = OpenAI()
embeddings = []
for doc in documents:
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=doc
    )
    embeddings.append(response.data[0].embedding)

# Create index
dimension = 1536
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

# Save index + metadata separately (complex!)
faiss.write_index(index, "index.faiss")
# ... manually track which ID maps to which document
```

---

## ✅ The Solution

Skill Seekers automates FAISS integration with structured, production-ready data:

**Benefits:**
- ✅ Auto-formatted documents with consistent metadata
- ✅ Works with LangChain FAISS wrapper for easy ID tracking
- ✅ Supports flat (small datasets) and IVF (large datasets) indexes
- ✅ GPU acceleration compatible (billion-scale search)
- ✅ Serialization-ready for production deployment

**Result:** 10-minute setup, production-ready similarity search that scales to billions of vectors.

---

## ⚡ Quick Start (10 Minutes)

### Prerequisites

```bash
# Install FAISS (CPU version)
pip install faiss-cpu>=1.7.4

# For GPU support (if available)
pip install faiss-gpu>=1.7.4

# Install LangChain for easy FAISS wrapper
pip install langchain>=0.1.0 langchain-community>=0.0.20

# OpenAI for embeddings
pip install openai>=1.0.0

# Or with Skill Seekers
pip install skill-seekers[all-llms]
```

**What you need:**
- Python 3.10+
- OpenAI API key (for embeddings)
- Optional: CUDA GPU for billion-scale search

### Generate FAISS-Ready Documents

```bash
# Step 1: Scrape documentation
skill-seekers scrape --config configs/react.json

# Step 2: Package for LangChain (FAISS-compatible)
skill-seekers package output/react --target langchain

# Output: output/react-langchain.json (FAISS-ready)
```

### Create FAISS Index with LangChain

```python
import json
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

# Load documents
with open("output/react-langchain.json") as f:
    docs_data = json.load(f)

# Convert to LangChain Documents
documents = [
    Document(
        page_content=doc["page_content"],
        metadata=doc["metadata"]
    )
    for doc in docs_data
]

# Create FAISS index (embeddings generated automatically)
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
vectorstore = FAISS.from_documents(documents, embeddings)

# Save index
vectorstore.save_local("faiss_index")

print(f"✅ Created FAISS index with {len(documents)} documents")
```

### Query FAISS Index

```python
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

# Load index (note: only load indexes from trusted sources)
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

# Similarity search
results = vectorstore.similarity_search(
    query="How do I use React hooks?",
    k=3
)

for i, doc in enumerate(results):
    print(f"\n{i+1}. Category: {doc.metadata['category']}")
    print(f"   Source: {doc.metadata['source']}")
    print(f"   Content: {doc.page_content[:200]}...")
```

### Similarity Search with Scores

```python
# Get similarity scores
results = vectorstore.similarity_search_with_score(
    query="React state management",
    k=5
)

for doc, score in results:
    print(f"Score: {score:.3f}")
    print(f"Category: {doc.metadata['category']}")
    print(f"Content: {doc.page_content[:150]}...")
    print()
```

---

## 📖 Detailed Setup Guide

### Step 1: Choose FAISS Index Type

**Option A: IndexFlatL2 (Exact Search, <100K vectors)**

```python
import faiss

# Flat index: exact nearest neighbors (brute force)
dimension = 1536  # OpenAI ada-002
index = faiss.IndexFlatL2(dimension)

# Pros: 100% accuracy, simple
# Cons: O(n) search time, slow for large datasets
# Use when: <100K vectors, need perfect recall
```

**Option B: IndexIVFFlat (Approximate Search, 100K-10M vectors)**

```python
# IVF index: cluster-based approximate search
quantizer = faiss.IndexFlatL2(dimension)
nlist = 100  # Number of clusters
index = faiss.IndexIVFFlat(quantizer, dimension, nlist)

# Train on sample data
index.train(training_vectors)  # Needs ~30*nlist training vectors
index.add(vectors)

# Pros: Faster than flat, good accuracy
# Cons: Requires training, 90-95% recall
# Use when: 100K-10M vectors
```

**Option C: IndexHNSWFlat (Graph-based, High Recall)**

```python
# HNSW index: hierarchical navigable small world
index = faiss.IndexHNSWFlat(dimension, 32)  # 32 = M (graph connections)

# Pros: Fast, high recall (>95%), no training
# Cons: High memory usage (3-4x flat)
# Use when: Need speed + high recall, have memory
```

**Option D: IndexIVFPQ (Product Quantization, 10M-1B vectors)**

```python
# IVF + PQ: compressed vectors for massive scale
quantizer = faiss.IndexFlatL2(dimension)
nlist = 1000
m = 8  # Number of subvectors
nbits = 8  # Bits per subvector
index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, nbits)

# Train then add
index.train(training_vectors)
index.add(vectors)

# Pros: 16-32x memory reduction, billion-scale
# Cons: Lower recall (80-90%), complex
# Use when: >10M vectors, memory constrained
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

### Step 3: Create FAISS Index (LangChain Wrapper)

```python
import json
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

# Load documents
with open("output/django-langchain.json") as f:
    docs_data = json.load(f)

documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in docs_data
]

# Create embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# For small datasets (<100K): Use default (Flat)
vectorstore = FAISS.from_documents(documents, embeddings)

# For large datasets (>100K): Use IVF
# vectorstore = FAISS.from_documents(
#     documents,
#     embeddings,
#     index_factory_string="IVF100,Flat"
# )

# Save index + docstore + metadata
vectorstore.save_local("faiss_index")

print(f"✅ Created FAISS index with {len(documents)} vectors")
```

### Step 4: Query with Filtering

```python
# Load index (only from trusted sources!)
vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

# Basic similarity search
results = vectorstore.similarity_search(
    query="Django models tutorial",
    k=5
)

# Similarity search with score threshold
results = vectorstore.similarity_search_with_relevance_scores(
    query="Django authentication",
    k=5,
    score_threshold=0.8  # Only return if relevance > 0.8
)

# Maximum marginal relevance (diverse results)
results = vectorstore.max_marginal_relevance_search(
    query="React components",
    k=5,
    fetch_k=20  # Fetch 20, return top 5 diverse
)

# Custom filter function (post-search filtering)
def filter_by_category(docs, category):
    return [doc for doc in docs if doc.metadata.get("category") == category]

results = vectorstore.similarity_search("hooks", k=20)
filtered = filter_by_category(results, "state-management")
```

---

## 🚀 Advanced Usage

### 1. GPU Acceleration (Billion-Scale Search)

```python
import faiss

# Check GPU availability
ngpus = faiss.get_num_gpus()
print(f"GPUs available: {ngpus}")

# Create GPU index
dimension = 1536
cpu_index = faiss.IndexFlatL2(dimension)

# Move to GPU
gpu_index = faiss.index_cpu_to_gpu(
    faiss.StandardGpuResources(),
    0,  # GPU ID
    cpu_index
)

# Add vectors (on GPU)
gpu_index.add(vectors)

# Search (on GPU, 10-100x faster)
distances, indices = gpu_index.search(query_vectors, k=10)

# Move back to CPU for saving
cpu_index = faiss.index_gpu_to_cpu(gpu_index)
faiss.write_index(cpu_index, "index.faiss")
```

### 2. Batch Processing for Large Datasets

```python
import json
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

embeddings = OpenAIEmbeddings()

# Load documents
with open("output/large-dataset-langchain.json") as f:
    all_docs = json.load(f)

# Create index with first batch
batch_size = 10000
first_batch = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in all_docs[:batch_size]
]

vectorstore = FAISS.from_documents(first_batch, embeddings)
print(f"Created index with {batch_size} documents")

# Add remaining batches
for i in range(batch_size, len(all_docs), batch_size):
    batch = [
        Document(page_content=doc["page_content"], metadata=doc["metadata"])
        for doc in all_docs[i:i+batch_size]
    ]

    vectorstore.add_documents(batch)
    print(f"Added documents {i} to {i+len(batch)}")

# Save final index
vectorstore.save_local("large_faiss_index")
print(f"✅ Final index size: {len(all_docs)} documents")
```

### 3. Index Merging for Multi-Source

```python
# Create separate indexes for different sources
vectorstore1 = FAISS.from_documents(docs1, embeddings)
vectorstore2 = FAISS.from_documents(docs2, embeddings)
vectorstore3 = FAISS.from_documents(docs3, embeddings)

# Merge indexes
vectorstore1.merge_from(vectorstore2)
vectorstore1.merge_from(vectorstore3)

# Save merged index
vectorstore1.save_local("merged_index")

# Query combined index
results = vectorstore1.similarity_search("query", k=10)
```

---

## 📋 Best Practices

### 1. Choose Index Type by Dataset Size

```python
# <100K vectors: Flat (exact search)
if num_vectors < 100_000:
    vectorstore = FAISS.from_documents(documents, embeddings)

# 100K-1M vectors: IVF
elif num_vectors < 1_000_000:
    vectorstore = FAISS.from_documents(
        documents,
        embeddings,
        index_factory_string="IVF100,Flat"
    )

# 1M-10M vectors: IVF + PQ
elif num_vectors < 10_000_000:
    vectorstore = FAISS.from_documents(
        documents,
        embeddings,
        index_factory_string="IVF1000,PQ8"
    )

# >10M vectors: GPU + IVF + PQ
else:
    # Use GPU acceleration
    pass
```

### 2. Only Load Indexes from Trusted Sources

```python
# ⚠️ SECURITY: Only load indexes you trust!
# The allow_dangerous_deserialization flag exists because
# LangChain uses Python's serialization which can execute code

# ✅ Safe: Your own indexes
vectorstore = FAISS.load_local("my_index", embeddings, allow_dangerous_deserialization=True)

# ❌ Dangerous: Unknown indexes from internet
# vectorstore = FAISS.load_local("untrusted_index", ...)  # DON'T DO THIS
```

### 3. Use Batch Embedding Generation

```python
from openai import OpenAI

client = OpenAI()

# ✅ Good: Batch API (2048 texts per call)
texts = [doc["page_content"] for doc in documents]

embeddings = []
batch_size = 2048

for i in range(0, len(texts), batch_size):
    batch = texts[i:i + batch_size]
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=batch
    )
    embeddings.extend([e.embedding for e in response.data])

# ❌ Bad: One at a time (slow!)
for text in texts:
    response = client.embeddings.create(model="text-embedding-ada-002", input=text)
    embeddings.append(response.data[0].embedding)
```

---

## 🐛 Troubleshooting

### Issue: Index Too Large for Memory

**Problem:** "MemoryError" when loading index with 10M+ vectors

**Solutions:**

1. **Use Product Quantization:**
```python
# Compress vectors 32x
vectorstore = FAISS.from_documents(
    documents,
    embeddings,
    index_factory_string="IVF1000,PQ8"
)
```

2. **Use GPU:**
```python
# Move to GPU memory
gpu_index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, cpu_index)
```

### Issue: Slow Search on Large Index

**Problem:** Search takes >1 second on 1M+ vectors

**Solutions:**

1. **Use IVF index:**
```python
vectorstore = FAISS.from_documents(
    documents,
    embeddings,
    index_factory_string="IVF100,Flat"
)

# Tune nprobe
vectorstore.index.nprobe = 10  # Balance speed/accuracy
```

2. **GPU acceleration:**
```python
gpu_index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)
```

---

## 📊 Before vs. After

| Aspect | Without Skill Seekers | With Skill Seekers |
|--------|----------------------|-------------------|
| **Data Preparation** | Custom scraping + embedding generation | One command: `skill-seekers scrape` |
| **Index Creation** | Manual FAISS setup with numpy arrays | LangChain wrapper handles complexity |
| **ID Tracking** | Manual mapping of IDs to documents | Automatic docstore integration |
| **Metadata** | Separate storage required | Built into LangChain Documents |
| **Scaling** | Complex index optimization required | Factory strings: `"IVF100,PQ8"` |
| **Setup Time** | 4-6 hours | 10 minutes |
| **Code Required** | 500+ lines | 30 lines with LangChain |

---

## 🎯 Next Steps

### Related Guides

- **[LangChain Integration](LANGCHAIN.md)** - Use FAISS as vector store in LangChain
- **[LlamaIndex Integration](LLAMA_INDEX.md)** - Use FAISS with LlamaIndex
- **[RAG Pipelines Guide](RAG_PIPELINES.md)** - Build complete RAG systems
- **[INTEGRATIONS.md](INTEGRATIONS.md)** - See all integration options

### Resources

- **FAISS Wiki:** https://github.com/facebookresearch/faiss/wiki
- **LangChain FAISS:** https://python.langchain.com/docs/integrations/vectorstores/faiss
- **Support:** https://github.com/yusufkaraaslan/Skill_Seekers/discussions

---

**Questions?** Open an issue: https://github.com/yusufkaraaslan/Skill_Seekers/issues
**Website:** https://skillseekersweb.com/
**Last Updated:** February 7, 2026
