# Using Skill Seekers with Haystack

**Last Updated:** February 7, 2026
**Status:** Production Ready
**Difficulty:** Easy ⭐

---

## 🎯 The Problem

Building RAG (Retrieval-Augmented Generation) applications with Haystack requires high-quality, structured documentation for your document stores and pipelines. Manually scraping and preparing documentation is:

- **Time-Consuming** - Hours spent scraping docs, formatting, and structuring
- **Error-Prone** - Inconsistent formatting, missing metadata, broken references
- **Not Scalable** - Multi-language docs and large frameworks are overwhelming

**Example:**
> "When building an enterprise RAG system for FastAPI documentation with Haystack, you need to scrape 300+ pages, structure them with proper metadata, and prepare for multi-language search. This typically takes 6-8 hours of manual work."

---

## ✨ The Solution

Use Skill Seekers as **essential preprocessing** before Haystack:

1. **Generate Haystack Documents** from any documentation source
2. **Pre-structured with metadata** following Haystack 2.x format
3. **Ready for document stores** (InMemoryDocumentStore, Elasticsearch, Weaviate)
4. **One command** - scrape, structure, format in minutes

**Result:**
Skill Seekers outputs JSON files with Haystack Document format (`content` + `meta`), ready to load directly into your Haystack pipelines.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- Haystack 2.x installed: `pip install haystack-ai`
- Optional: Embeddings library (e.g., `sentence-transformers`)

### Installation

```bash
# Install Skill Seekers
pip install skill-seekers

# Verify installation
skill-seekers --version
```

### Generate Haystack Documents

```bash
# Example: Django framework documentation
skill-seekers scrape --config configs/django.json

# Package as Haystack Documents
skill-seekers package output/django --target haystack

# Output: output/django-haystack.json
```

### Load into Haystack

```python
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
import json

# Load documents
with open("output/django-haystack.json") as f:
    docs_data = json.load(f)

# Convert to Haystack Documents
documents = [
    Document(content=doc["content"], meta=doc["meta"])
    for doc in docs_data
]

print(f"Loaded {len(documents)} documents")

# Create document store
document_store = InMemoryDocumentStore()
document_store.write_documents(documents)

# Create retriever
retriever = InMemoryBM25Retriever(document_store=document_store)

# Query
results = retriever.run(query="How do I create Django models?", top_k=3)
for doc in results["documents"]:
    print(f"\n{doc.meta['category']}: {doc.content[:200]}...")
```

---

## 📖 Detailed Setup Guide

### Step 1: Choose Your Documentation Source

Skill Seekers supports multiple documentation sources:

```bash
# Official framework documentation
skill-seekers scrape --config configs/fastapi.json

# GitHub repository
skill-seekers github --repo tiangolo/fastapi

# PDF documentation
skill-seekers pdf --file docs/manual.pdf

# Combine multiple sources
skill-seekers unified \
  --docs https://fastapi.tiangolo.com/ \
  --github tiangolo/fastapi \
  --output output/fastapi-complete
```

### Step 2: Configure Scraping (Optional)

Create a custom config for your documentation:

```json
{
  "name": "my-framework",
  "base_url": "https://docs.example.com/",
  "selectors": {
    "main_content": "article.documentation",
    "title": "h1.page-title",
    "code_blocks": "pre code"
  },
  "categories": {
    "getting_started": ["intro", "quickstart", "installation"],
    "guides": ["tutorial", "guide", "howto"],
    "api": ["api", "reference"]
  },
  "max_pages": 500,
  "rate_limit": 0.5
}
```

Save as `configs/my-framework.json` and use:

```bash
skill-seekers scrape --config configs/my-framework.json
```

### Step 3: Package for Haystack

```bash
# Generate Haystack Documents
skill-seekers package output/my-framework --target haystack

# With semantic chunking for better retrieval
skill-seekers scrape --config configs/my-framework.json --chunk-for-rag
skill-seekers package output/my-framework --target haystack

# Output files:
# - output/my-framework-haystack.json (Haystack Documents)
# - output/my-framework/rag_chunks.json (if chunking enabled)
```

### Step 4: Load into Haystack Pipeline

**Option A: InMemoryDocumentStore (Development)**

```python
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
import json

# Load documents
with open("output/my-framework-haystack.json") as f:
    docs_data = json.load(f)

documents = [
    Document(content=doc["content"], meta=doc["meta"])
    for doc in docs_data
]

# Create in-memory store
document_store = InMemoryDocumentStore()
document_store.write_documents(documents)

# Create BM25 retriever
retriever = InMemoryBM25Retriever(document_store=document_store)

# Query
results = retriever.run(query="your question", top_k=5)
```

**Option B: Elasticsearch (Production)**

```python
from haystack import Document
from haystack.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack.components.retrievers.elasticsearch import ElasticsearchBM25Retriever
import json

# Connect to Elasticsearch
document_store = ElasticsearchDocumentStore(
    hosts=["http://localhost:9200"],
    index="my-framework-docs"
)

# Load and write documents
with open("output/my-framework-haystack.json") as f:
    docs_data = json.load(f)

documents = [
    Document(content=doc["content"], meta=doc["meta"])
    for doc in docs_data
]

document_store.write_documents(documents)

# Create retriever
retriever = ElasticsearchBM25Retriever(document_store=document_store)
```

**Option C: Weaviate (Hybrid Search)**

```python
from haystack import Document
from haystack.document_stores.weaviate import WeaviateDocumentStore
from haystack.components.retrievers.weaviate import WeaviateHybridRetriever
import json

# Connect to Weaviate
document_store = WeaviateDocumentStore(
    host="http://localhost:8080",
    index="MyFrameworkDocs"
)

# Load documents
with open("output/my-framework-haystack.json") as f:
    docs_data = json.load(f)

documents = [
    Document(content=doc["content"], meta=doc["meta"])
    for doc in docs_data
]

# Write with embeddings
from haystack.components.embedders import SentenceTransformersDocumentEmbedder

embedder = SentenceTransformersDocumentEmbedder(
    model="sentence-transformers/all-MiniLM-L6-v2"
)
embedder.warm_up()

docs_with_embeddings = embedder.run(documents)
document_store.write_documents(docs_with_embeddings["documents"])

# Create hybrid retriever (BM25 + vector)
retriever = WeaviateHybridRetriever(document_store=document_store)
```

### Step 5: Build RAG Pipeline

```python
from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator

# Create RAG pipeline
rag_pipeline = Pipeline()

# Add components
rag_pipeline.add_component("retriever", retriever)
rag_pipeline.add_component(
    "prompt_builder",
    PromptBuilder(
        template="""
        Based on the following documentation, answer the question.

        Documentation:
        {% for doc in documents %}
        {{ doc.content }}
        {% endfor %}

        Question: {{ question }}

        Answer:
        """
    )
)
rag_pipeline.add_component(
    "llm",
    OpenAIGenerator(api_key=os.getenv("OPENAI_API_KEY"))
)

# Connect components
rag_pipeline.connect("retriever", "prompt_builder.documents")
rag_pipeline.connect("prompt_builder", "llm")

# Run pipeline
response = rag_pipeline.run({
    "retriever": {"query": "How do I deploy my app?"},
    "prompt_builder": {"question": "How do I deploy my app?"}
})

print(response["llm"]["replies"][0])
```

---

## 🔥 Advanced Usage

### Semantic Chunking for Better Retrieval

```bash
# Enable semantic chunking (preserves code blocks, respects paragraphs)
skill-seekers scrape --config configs/django.json \
  --chunk-for-rag \
  --chunk-size 512 \
  --chunk-overlap 50

# Package chunked output
skill-seekers package output/django --target haystack

# Result: Smaller, more focused documents for better retrieval
```

### Multi-Source RAG System

```bash
# Combine official docs + GitHub issues + PDF guides
skill-seekers unified \
  --docs https://docs.example.com/ \
  --github owner/repo \
  --pdf guides/*.pdf \
  --output output/complete-knowledge

skill-seekers package output/complete-knowledge --target haystack

# Detect conflicts between sources
skill-seekers detect-conflicts output/complete-knowledge
```

### Custom Metadata for Filtering

Haystack Documents include rich metadata for filtering:

```python
# Query with metadata filters
from haystack.dataclasses import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

# Filter by category
results = retriever.run(
    query="deployment",
    top_k=5,
    filters={"field": "category", "operator": "==", "value": "guides"}
)

# Filter by version
results = retriever.run(
    query="api reference",
    filters={"field": "version", "operator": "==", "value": "2.0"}
)

# Multiple filters
results = retriever.run(
    query="authentication",
    filters={
        "operator": "AND",
        "conditions": [
            {"field": "category", "operator": "==", "value": "api"},
            {"field": "type", "operator": "==", "value": "reference"}
        ]
    }
)
```

### Embedding-Based Retrieval

```python
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder
)
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever

# Embed documents
doc_embedder = SentenceTransformersDocumentEmbedder(
    model="sentence-transformers/all-MiniLM-L6-v2"
)
doc_embedder.warm_up()

docs_with_embeddings = doc_embedder.run(documents)
document_store.write_documents(docs_with_embeddings["documents"])

# Create embedding retriever
text_embedder = SentenceTransformersTextEmbedder(
    model="sentence-transformers/all-MiniLM-L6-v2"
)
text_embedder.warm_up()

retriever = InMemoryEmbeddingRetriever(document_store=document_store)

# Query with embeddings
query_embedding = text_embedder.run("How do I deploy?")
results = retriever.run(
    query_embedding=query_embedding["embedding"],
    top_k=5
)
```

### Incremental Updates

```bash
# Initial scrape
skill-seekers scrape --config configs/fastapi.json

# Later: Update only changed pages
skill-seekers scrape --config configs/fastapi.json --skip-existing

# Merge with existing documents
python scripts/merge_documents.py \
  output/fastapi-haystack.json \
  output/fastapi-haystack-new.json
```

---

## ✅ Best Practices

### 1. Use Semantic Chunking for Large Docs

**Why:** Better retrieval quality, more focused results

```bash
# Enable chunking for frameworks with long pages
skill-seekers scrape --config configs/django.json \
  --chunk-for-rag \
  --chunk-size 512 \
  --chunk-overlap 50
```

### 2. Choose Right Document Store

**Development:**
- InMemoryDocumentStore - Fast, no setup

**Production:**
- Elasticsearch - Full-text search, scalable
- Weaviate - Hybrid search (BM25 + vector), multi-modal
- Qdrant - High-performance vector search
- Opensearch - AWS-managed, cost-effective

### 3. Add Metadata Filters

```python
# Always include category in queries for faster results
results = retriever.run(
    query="database models",
    filters={"field": "category", "operator": "==", "value": "guides"}
)
```

### 4. Monitor Retrieval Quality

```python
# Test queries and verify relevance
test_queries = [
    "How do I create a model?",
    "What is the deployment process?",
    "How to handle authentication?"
]

for query in test_queries:
    results = retriever.run(query=query, top_k=3)
    print(f"\nQuery: {query}")
    for i, doc in enumerate(results["documents"], 1):
        print(f"{i}. {doc.meta['file']} - {doc.meta['category']}")
```

### 5. Version Your Documentation

```bash
# Include version in metadata
skill-seekers scrape --config configs/django.json --metadata version=4.2

# Query specific versions
results = retriever.run(
    query="middleware",
    filters={"field": "version", "operator": "==", "value": "4.2"}
)
```

---

## 💼 Real-World Example: FastAPI RAG Chatbot

Complete example of building a FastAPI documentation chatbot:

### Step 1: Generate Documentation

```bash
# Scrape FastAPI docs with chunking
skill-seekers scrape --config configs/fastapi.json \
  --chunk-for-rag \
  --chunk-size 512 \
  --chunk-overlap 50 \
  --max-pages 200

# Package for Haystack
skill-seekers package output/fastapi --target haystack
```

### Step 2: Setup Haystack Pipeline

```python
from haystack import Pipeline, Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
import json
import os

# Load documents
with open("output/fastapi-haystack.json") as f:
    docs_data = json.load(f)

documents = [
    Document(content=doc["content"], meta=doc["meta"])
    for doc in docs_data
]

print(f"Loaded {len(documents)} FastAPI documentation chunks")

# Create document store
document_store = InMemoryDocumentStore()
document_store.write_documents(documents)
print(f"Indexed {document_store.count_documents()} documents")

# Build RAG pipeline
rag = Pipeline()

# Add components
rag.add_component(
    "retriever",
    InMemoryBM25Retriever(document_store=document_store)
)

rag.add_component(
    "prompt",
    PromptBuilder(
        template="""
        You are a FastAPI expert assistant. Answer the question based on the documentation below.

        Documentation:
        {% for doc in documents %}
        ---
        Source: {{ doc.meta.file }}
        Category: {{ doc.meta.category }}

        {{ doc.content }}
        {% endfor %}

        Question: {{ question }}

        Provide a clear, code-focused answer with examples when relevant.
        """
    )
)

rag.add_component(
    "llm",
    OpenAIGenerator(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4"
    )
)

# Connect pipeline
rag.connect("retriever.documents", "prompt.documents")
rag.connect("prompt.prompt", "llm.prompt")

print("Pipeline ready!")
```

### Step 3: Interactive Chat

```python
def ask_fastapi(question: str, top_k: int = 5):
    """Ask a question about FastAPI."""
    response = rag.run({
        "retriever": {"query": question, "top_k": top_k},
        "prompt": {"question": question}
    })

    answer = response["llm"]["replies"][0]
    print(f"\nQuestion: {question}\n")
    print(f"Answer: {answer}\n")

    # Show sources
    docs = response["retriever"]["documents"]
    print("Sources:")
    for doc in docs:
        print(f"  - {doc.meta['file']} ({doc.meta['category']})")

# Example usage
ask_fastapi("How do I create a REST API endpoint?")
ask_fastapi("What is dependency injection in FastAPI?")
ask_fastapi("How do I handle file uploads?")
```

### Step 4: Deploy with FastAPI

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Question(BaseModel):
    text: str
    top_k: int = 5

@app.post("/ask")
async def ask_question(question: Question):
    """Ask a question about FastAPI documentation."""
    response = rag.run({
        "retriever": {"query": question.text, "top_k": question.top_k},
        "prompt": {"question": question.text}
    })

    return {
        "question": question.text,
        "answer": response["llm"]["replies"][0],
        "sources": [
            {
                "file": doc.meta["file"],
                "category": doc.meta["category"],
                "content_preview": doc.content[:200]
            }
            for doc in response["retriever"]["documents"]
        ]
    }

# Run: uvicorn chatbot:app --reload
# Test: curl -X POST http://localhost:8000/ask \
#   -H "Content-Type: application/json" \
#   -d '{"text": "How do I use async functions?"}'
```

**Result:**
- ✅ 200 documentation pages → 450 optimized chunks
- ✅ Sub-second retrieval with BM25
- ✅ Context-aware answers from GPT-4
- ✅ Source attribution for every answer
- ✅ REST API for integration

---

## 🔧 Troubleshooting

### Issue: Documents not loading correctly

**Symptoms:** Empty content, missing metadata

**Solutions:**
```bash
# Verify JSON structure
jq '.[0]' output/fastapi-haystack.json

# Should show:
# {
#   "content": "...",
#   "meta": {
#     "source": "fastapi",
#     "category": "...",
#     ...
#   }
# }

# Regenerate if malformed
skill-seekers package output/fastapi --target haystack --force
```

### Issue: Poor retrieval quality

**Symptoms:** Irrelevant results, missed relevant docs

**Solutions:**
```bash
# 1. Enable semantic chunking
skill-seekers scrape --config configs/fastapi.json --chunk-for-rag

# 2. Adjust chunk size
skill-seekers scrape --config configs/fastapi.json \
  --chunk-for-rag \
  --chunk-size 768 \  # Larger chunks for more context
  --chunk-overlap 100  # More overlap for continuity

# 3. Use hybrid search (BM25 + embeddings)
# See Advanced Usage section
```

### Issue: OutOfMemoryError with large docs

**Symptoms:** Crash when loading thousands of documents

**Solutions:**
```python
# Load documents in batches
import json

def load_documents_batched(file_path, batch_size=100):
    with open(file_path) as f:
        docs_data = json.load(f)

    for i in range(0, len(docs_data), batch_size):
        batch = docs_data[i:i+batch_size]
        documents = [
            Document(content=doc["content"], meta=doc["meta"])
            for doc in batch
        ]
        document_store.write_documents(documents)
        print(f"Loaded batch {i//batch_size + 1}")

load_documents_batched("output/large-framework-haystack.json")
```

### Issue: Haystack version compatibility

**Symptoms:** Import errors, method not found

**Solutions:**
```bash
# Check Haystack version
pip show haystack-ai

# Skill Seekers requires Haystack 2.x
pip install --upgrade "haystack-ai>=2.0.0"

# For Haystack 1.x (legacy), use markdown export instead:
skill-seekers package output/framework --target markdown
```

### Issue: Slow query performance

**Symptoms:** Queries take >2 seconds

**Solutions:**
```python
# 1. Reduce top_k
results = retriever.run(query="...", top_k=3)  # Instead of 10

# 2. Add metadata filters
results = retriever.run(
    query="...",
    filters={"field": "category", "operator": "==", "value": "api"}
)

# 3. Use InMemoryDocumentStore for development
# Switch to Elasticsearch for production scale
```

---

## 📊 Before vs After

| Aspect | Before Skill Seekers | After Skill Seekers |
|--------|---------------------|-------------------|
| **Setup Time** | 6-8 hours manual scraping | 5 minutes automated |
| **Documentation Quality** | Inconsistent, missing metadata | Structured with rich metadata |
| **Chunking** | Manual, error-prone | Semantic, code-preserving |
| **Updates** | Re-scrape everything | Incremental updates |
| **Multi-source** | Complex custom scripts | One unified command |
| **Format** | Custom JSON hacking | Native Haystack Documents |
| **Retrieval Quality** | Poor (large chunks, no metadata) | Excellent (optimized chunks, filters) |
| **Maintenance** | High (scripts break) | Low (one tool, well-tested) |

---

## 🎓 Next Steps

### Try These Examples

1. **Build a chatbot** - Follow the FastAPI example above
2. **Multi-language search** - Scrape docs in multiple languages
3. **Hybrid retrieval** - Combine BM25 + embeddings (see Advanced Usage)
4. **Production deployment** - Use Elasticsearch or Weaviate

### Explore More Integrations

- [LangChain Integration](LANGCHAIN.md) - Alternative RAG framework
- [LlamaIndex Integration](LLAMA_INDEX.md) - Query engine approach
- [Pinecone Integration](PINECONE.md) - Cloud vector database
- [Cursor Integration](CURSOR.md) - AI coding assistant

### Learn More

- [RAG Pipelines Guide](RAG_PIPELINES.md) - Complete RAG overview
- [Chunking Guide](../features/CHUNKING.md) - Semantic chunking details
- [Haystack Documentation](https://docs.haystack.deepset.ai/)
- [Example Repository](../../examples/haystack-pipeline/)

---

## 🤝 Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Haystack Help:** [Haystack Discord](https://discord.gg/haystack)

---

**Ready to build production RAG with Haystack?**

```bash
pip install skill-seekers haystack-ai
skill-seekers scrape --config configs/your-framework.json --chunk-for-rag
skill-seekers package output/your-framework --target haystack
```

Transform documentation into production-ready Haystack pipelines in minutes! 🚀
