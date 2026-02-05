# Using Skill Seekers with LlamaIndex

**Last Updated:** February 5, 2026
**Status:** Production Ready
**Difficulty:** Easy ⭐

---

## 🎯 The Problem

Building knowledge bases and query engines with LlamaIndex requires well-structured documentation. Manually preparing documents is:

- **Labor-Intensive** - Scraping, chunking, and formatting takes hours
- **Inconsistent** - Manual processes lead to quality variations
- **Hard to Update** - Documentation changes require complete rework

**Example:**
> "When building a LlamaIndex query engine for FastAPI documentation, you need to extract 300+ pages, structure them properly, and maintain consistent metadata. This typically takes 3-5 hours."

---

## ✨ The Solution

Use Skill Seekers as **essential preprocessing** before LlamaIndex:

1. **Generate LlamaIndex Nodes** from any documentation source
2. **Pre-structured with IDs** and rich metadata
3. **Ready for indexes** (VectorStoreIndex, TreeIndex, KeywordTableIndex)
4. **One command** - complete documentation in minutes

**Result:**
Skill Seekers outputs JSON files with LlamaIndex Node format, ready to build indexes and query engines.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- LlamaIndex installed: `pip install llama-index`
- OpenAI API key (for embeddings): `export OPENAI_API_KEY=sk-...`

### Installation

```bash
# Install Skill Seekers
pip install skill-seekers

# Verify installation
skill-seekers --version
```

### Generate LlamaIndex Nodes

```bash
# Example: Django framework documentation
skill-seekers scrape --config configs/django.json

# Package as LlamaIndex Nodes
skill-seekers package output/django --target llama-index

# Output: output/django-llama-index.json
```

### Build Query Engine

```python
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex
import json

# Load nodes
with open("output/django-llama-index.json") as f:
    nodes_data = json.load(f)

# Convert to LlamaIndex Nodes
nodes = [
    TextNode(
        text=node["text"],
        metadata=node["metadata"],
        id_=node["id_"]
    )
    for node in nodes_data
]

print(f"Loaded {len(nodes)} nodes")

# Create index
index = VectorStoreIndex(nodes)

# Create query engine
query_engine = index.as_query_engine()

# Query
response = query_engine.query("How do I create a Django model?")
print(response)
```

---

## 📖 Detailed Setup Guide

### Step 1: Choose Your Documentation Source

**Option A: Use Preset Config (Fastest)**
```bash
# Available presets: django, fastapi, vue, etc.
skill-seekers scrape --config configs/django.json
```

**Option B: From GitHub Repository**
```bash
# Scrape from GitHub repo
skill-seekers github --repo django/django --name django-skill
```

**Option C: Custom Documentation**
```bash
# Create custom config
skill-seekers scrape --config configs/my-docs.json
```

### Step 2: Generate LlamaIndex Format

```bash
# Convert to LlamaIndex Nodes
skill-seekers package output/django --target llama-index

# Output structure:
# output/django-llama-index.json
# [
#   {
#     "text": "...",
#     "metadata": {
#       "source": "django",
#       "category": "models",
#       "file": "models.md"
#     },
#     "id_": "unique-hash-id",
#     "embedding": null
#   }
# ]
```

**What You Get:**
- ✅ Pre-structured nodes with unique IDs
- ✅ Rich metadata (source, category, file, type)
- ✅ Clean text (code blocks preserved)
- ✅ Ready for indexing

### Step 3: Create Vector Store Index

```python
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore
import json

# Load nodes
with open("output/django-llama-index.json") as f:
    nodes_data = json.load(f)

nodes = [
    TextNode(
        text=node["text"],
        metadata=node["metadata"],
        id_=node["id_"]
    )
    for node in nodes_data
]

# Create index
index = VectorStoreIndex(nodes)

# Persist for later use
index.storage_context.persist(persist_dir="./storage")

print(f"✅ Index created with {len(nodes)} nodes")
```

**Load Persisted Index:**
```python
from llama_index.core import load_index_from_storage, StorageContext

# Load from disk
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)

print("✅ Index loaded from storage")
```

### Step 4: Create Query Engine

**Basic Query Engine:**
```python
# Create query engine
query_engine = index.as_query_engine(
    similarity_top_k=3,  # Return top 3 relevant chunks
    response_mode="compact"
)

# Query
response = query_engine.query("How do I create a Django model?")
print(response)
```

**Chat Engine (Conversational):**
```python
from llama_index.core.chat_engine import CondenseQuestionChatEngine

# Create chat engine with memory
chat_engine = index.as_chat_engine(
    chat_mode="condense_question",
    verbose=True
)

# Chat
response = chat_engine.chat("Tell me about Django models")
print(response)

# Follow-up (maintains context)
response = chat_engine.chat("How do I add fields?")
print(response)
```

---

## 🎨 Advanced Usage

### Custom Index Types

**Tree Index (For Summarization):**
```python
from llama_index.core import TreeIndex

tree_index = TreeIndex(nodes)
query_engine = tree_index.as_query_engine()

# Better for summarization queries
response = query_engine.query("Summarize Django's ORM capabilities")
```

**Keyword Table Index (For Keyword Search):**
```python
from llama_index.core import KeywordTableIndex

keyword_index = KeywordTableIndex(nodes)
query_engine = keyword_index.as_query_engine()

# Better for keyword-based queries
response = query_engine.query("foreign key relationships")
```

### Query with Filters

```python
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Filter by category
filters = MetadataFilters(
    filters=[
        ExactMatchFilter(key="category", value="models")
    ]
)

query_engine = index.as_query_engine(
    similarity_top_k=3,
    filters=filters
)

# Only searches in "models" category
response = query_engine.query("How do relationships work?")
```

### Custom Retrieval

```python
from llama_index.core.retrievers import VectorIndexRetriever

# Custom retriever with specific settings
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=5,
)

# Get source nodes
nodes = retriever.retrieve("django models")

for node in nodes:
    print(f"Score: {node.score:.3f}")
    print(f"Category: {node.metadata['category']}")
    print(f"Text: {node.text[:100]}...\n")
```

### Multi-Source Knowledge Base

```python
# Combine multiple documentation sources
sources = ["django", "fastapi", "flask"]
all_nodes = []

for source in sources:
    with open(f"output/{source}-llama-index.json") as f:
        nodes_data = json.load(f)

    nodes = [
        TextNode(
            text=node["text"],
            metadata=node["metadata"],
            id_=node["id_"]
        )
        for node in nodes_data
    ]
    all_nodes.extend(nodes)

# Create unified index
index = VectorStoreIndex(all_nodes)
print(f"✅ Created index with {len(all_nodes)} nodes from {len(sources)} sources")
```

---

## 💡 Best Practices

### 1. Persist Your Indexes
```python
# Save to avoid re-indexing
index.storage_context.persist(persist_dir="./storage")

# Load when needed
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

### 2. Use Streaming for Long Responses
```python
query_engine = index.as_query_engine(
    streaming=True
)

response = query_engine.query("Explain Django in detail")
for text in response.response_gen:
    print(text, end="", flush=True)
```

### 3. Add Response Synthesis
```python
from llama_index.core.response_synthesizers import ResponseMode

query_engine = index.as_query_engine(
    response_mode=ResponseMode.TREE_SUMMARIZE,  # Better for long docs
    similarity_top_k=5
)
```

### 4. Monitor Performance
```python
import time

start = time.time()
response = query_engine.query("your question")
elapsed = time.time() - start

print(f"Query took {elapsed:.2f}s")
print(f"Used {len(response.source_nodes)} source nodes")
```

---

## 🔥 Real-World Example

### Building a FastAPI Documentation Assistant

**Step 1: Generate Nodes**
```bash
# Scrape FastAPI docs
skill-seekers scrape --config configs/fastapi.json

# Convert to LlamaIndex format
skill-seekers package output/fastapi --target llama-index
```

**Step 2: Build Index and Query Engine**
```python
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex
from llama_index.core.chat_engine import CondenseQuestionChatEngine
import json

# Load nodes
with open("output/fastapi-llama-index.json") as f:
    nodes_data = json.load(f)

nodes = [
    TextNode(
        text=node["text"],
        metadata=node["metadata"],
        id_=node["id_"]
    )
    for node in nodes_data
]

# Create index
index = VectorStoreIndex(nodes)
index.storage_context.persist(persist_dir="./fastapi_index")

print(f"✅ FastAPI index created with {len(nodes)} nodes")

# Create chat engine
chat_engine = index.as_chat_engine(
    chat_mode="condense_question",
    verbose=True
)

# Interactive loop
print("\n🤖 FastAPI Documentation Assistant")
print("Ask me anything about FastAPI (type 'quit' to exit)\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() in ['quit', 'exit', 'q']:
        print("👋 Goodbye!")
        break

    if not user_input:
        continue

    response = chat_engine.chat(user_input)
    print(f"\nAssistant: {response}\n")

    # Show sources
    print("Sources:")
    for node in response.source_nodes:
        cat = node.metadata.get('category', 'unknown')
        file = node.metadata.get('file', 'unknown')
        print(f"  - {cat} ({file})")
    print()
```

**Result:**
- Complete FastAPI documentation indexed
- Conversational interface with memory
- Source attribution for transparency
- Instant responses (<1 second)

---

## 🐛 Troubleshooting

### Issue: Index Too Large
**Solution:** Use hybrid indexing or split by category
```python
# Create separate indexes per category
categories = set(node["metadata"]["category"] for node in nodes_data)

indexes = {}
for category in categories:
    cat_nodes = [
        TextNode(**node)
        for node in nodes_data
        if node["metadata"]["category"] == category
    ]
    indexes[category] = VectorStoreIndex(cat_nodes)
```

### Issue: Slow Queries
**Solution:** Reduce similarity_top_k or use caching
```python
query_engine = index.as_query_engine(
    similarity_top_k=2,  # Reduce from 3 to 2
)
```

### Issue: Missing Dependencies
**Solution:** Install LlamaIndex components
```bash
pip install llama-index llama-index-core
pip install llama-index-llms-openai  # For OpenAI LLM
pip install llama-index-embeddings-openai  # For OpenAI embeddings
```

---

## 📊 Before vs After Comparison

| Aspect | Manual Process | With Skill Seekers |
|--------|---------------|-------------------|
| **Time to Setup** | 3-5 hours | 5 minutes |
| **Node Structure** | Manual, inconsistent | Automatic, structured |
| **Metadata** | Often missing | Rich, comprehensive |
| **IDs** | Manual generation | Auto-generated (stable) |
| **Maintenance** | Re-process everything | Re-run one command |
| **Updates** | Hours of work | 5 minutes |

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Documentation:** [https://skillseekersweb.com/](https://skillseekersweb.com/)
- **Twitter:** [@_yUSyUS_](https://x.com/_yUSyUS_)

---

## 📚 Related Guides

- [LangChain Integration](./LANGCHAIN.md)
- [Pinecone Integration](./PINECONE.md)
- [RAG Pipelines Overview](./RAG_PIPELINES.md)

---

## 📖 Next Steps

1. **Try the Quick Start** above
2. **Explore different index types** (Tree, Keyword, List)
3. **Build your query engine** with production-ready docs
4. **Share your experience** - we'd love feedback!

---

**Last Updated:** February 5, 2026
**Tested With:** LlamaIndex v0.10.0+, OpenAI GPT-4
**Skill Seekers Version:** v2.9.0+
