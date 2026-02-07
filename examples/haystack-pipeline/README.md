# Haystack Pipeline Example

Complete example showing how to use Skill Seekers with Haystack 2.x for building RAG pipelines.

## What This Example Does

- ✅ Converts documentation into Haystack Documents
- ✅ Creates an in-memory document store
- ✅ Builds a BM25 retriever for semantic search
- ✅ Shows complete RAG pipeline workflow

## Prerequisites

```bash
# Install Skill Seekers
pip install skill-seekers

# Install Haystack 2.x
pip install haystack-ai
```

## Quick Start

### 1. Generate React Documentation Skill

```bash
# Scrape React documentation
skill-seekers scrape --config configs/react.json --max-pages 100

# Package for Haystack
skill-seekers package output/react --target haystack
```

This creates `output/react-haystack.json` with Haystack Documents.

### 2. Run the Pipeline

```bash
# Run the example script
python quickstart.py
```

## What the Example Does

### Step 1: Load Documents

```python
from haystack import Document
import json

# Load Haystack documents
with open("../../output/react-haystack.json") as f:
    docs_data = json.load(f)

documents = [
    Document(content=doc["content"], meta=doc["meta"])
    for doc in docs_data
]

print(f"📚 Loaded {len(documents)} documents")
```

### Step 2: Create Document Store

```python
from haystack.document_stores.in_memory import InMemoryDocumentStore

# Create in-memory store
document_store = InMemoryDocumentStore()
document_store.write_documents(documents)

print(f"💾 Indexed {document_store.count_documents()} documents")
```

### Step 3: Build Retriever

```python
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever

# Create BM25 retriever
retriever = InMemoryBM25Retriever(document_store=document_store)

# Query
results = retriever.run(
    query="How do I use useState hook?",
    top_k=3
)

# Display results
for doc in results["documents"]:
    print(f"\n📖 Source: {doc.meta.get('file', 'unknown')}")
    print(f"   Category: {doc.meta.get('category', 'unknown')}")
    print(f"   Preview: {doc.content[:200]}...")
```

## Expected Output

```
📚 Loaded 15 documents
💾 Indexed 15 documents

🔍 Query: How do I use useState hook?

📖 Source: hooks.md
   Category: hooks
   Preview: # React Hooks

React Hooks are functions that let you "hook into" React state and lifecycle features from function components.

## useState

The useState Hook lets you add React state to function components...

📖 Source: getting_started.md
   Category: getting started
   Preview: # Getting Started with React

React is a JavaScript library for building user interfaces...

📖 Source: best_practices.md
   Category: best practices
   Preview: # React Best Practices

When working with Hooks...
```

## Advanced Usage

### With RAG Chunking

For better retrieval quality, use semantic chunking:

```bash
# Generate with chunking
skill-seekers scrape --config configs/react.json --max-pages 100 --chunk-for-rag --chunk-size 512 --chunk-overlap 50

# Use chunked output
python quickstart.py --chunked
```

### With Vector Embeddings

For semantic search instead of BM25:

```python
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever

# Create document store with embeddings
document_store = InMemoryDocumentStore()

# Embed documents
embedder = SentenceTransformersDocumentEmbedder(
    model="sentence-transformers/all-MiniLM-L6-v2"
)
embedder.warm_up()

# Process documents
docs_with_embeddings = embedder.run(documents)
document_store.write_documents(docs_with_embeddings["documents"])

# Create embedding retriever
retriever = InMemoryEmbeddingRetriever(document_store=document_store)

# Query (requires query embedding)
from haystack.components.embedders import SentenceTransformersTextEmbedder

query_embedder = SentenceTransformersTextEmbedder(
    model="sentence-transformers/all-MiniLM-L6-v2"
)
query_embedder.warm_up()

query_embedding = query_embedder.run("How do I use useState?")

results = retriever.run(
    query_embedding=query_embedding["embedding"],
    top_k=3
)
```

### Building Complete RAG Pipeline

For question answering with LLMs:

```python
from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator

# Create RAG pipeline
rag_pipeline = Pipeline()

# Add components
rag_pipeline.add_component("retriever", retriever)
rag_pipeline.add_component("prompt_builder", PromptBuilder(
    template="""
    Based on the following context, answer the question.

    Context:
    {% for doc in documents %}
    {{ doc.content }}
    {% endfor %}

    Question: {{ question }}

    Answer:
    """
))
rag_pipeline.add_component("llm", OpenAIGenerator(api_key="your-key"))

# Connect components
rag_pipeline.connect("retriever", "prompt_builder.documents")
rag_pipeline.connect("prompt_builder", "llm")

# Run pipeline
response = rag_pipeline.run({
    "retriever": {"query": "How do I use useState?"},
    "prompt_builder": {"question": "How do I use useState?"}
})

print(response["llm"]["replies"][0])
```

## Files in This Example

- `README.md` - This file
- `quickstart.py` - Basic BM25 retrieval pipeline
- `requirements.txt` - Python dependencies

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'haystack'

**Solution:** Install Haystack 2.x

```bash
pip install haystack-ai
```

### Issue: Documents not found

**Solution:** Run scraping first

```bash
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target haystack
```

### Issue: Poor retrieval quality

**Solution:** Use semantic chunking or vector embeddings

```bash
# Semantic chunking
skill-seekers scrape --config configs/react.json --chunk-for-rag

# Or use vector embeddings (see Advanced Usage)
```

## Next Steps

1. Try different documentation sources (Django, FastAPI, etc.)
2. Experiment with vector embeddings for semantic search
3. Build complete RAG pipeline with LLM generation
4. Deploy to production with persistent document stores

## Related Examples

- [LangChain RAG Pipeline](../langchain-rag-pipeline/)
- [LlamaIndex Query Engine](../llama-index-query-engine/)
- [Pinecone Vector Store](../pinecone-upsert/)

## Resources

- [Haystack Documentation](https://docs.haystack.deepset.ai/)
- [Skill Seekers Documentation](https://github.com/yusufkaraaslan/Skill_Seekers)
- [Haystack Tutorials](https://haystack.deepset.ai/tutorials)
