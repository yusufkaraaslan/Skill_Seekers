# Pinecone Upsert Example

Complete example showing how to upsert Skill Seekers documents to Pinecone and perform semantic search.

## What This Example Does

1. **Creates** a Pinecone serverless index
2. **Loads** Skill Seekers-generated documents (LangChain format)
3. **Generates** embeddings with OpenAI
4. **Upserts** documents to Pinecone with metadata
5. **Demonstrates** semantic search capabilities
6. **Provides** interactive search mode

## Prerequisites

```bash
# Install dependencies
pip install pinecone-client openai

# Set API keys
export PINECONE_API_KEY=your-pinecone-api-key
export OPENAI_API_KEY=sk-...
```

## Generate Documents

First, generate LangChain-format documents using Skill Seekers:

```bash
# Option 1: Use preset config (e.g., Django)
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target langchain

# Option 2: From GitHub repo
skill-seekers github --repo django/django --name django
skill-seekers package output/django --target langchain

# Output: output/django-langchain.json
```

## Run the Example

```bash
cd examples/pinecone-upsert

# Run the quickstart script
python quickstart.py
```

## What You'll See

1. **Index creation** (if it doesn't exist)
2. **Documents loaded** with category breakdown
3. **Batch upsert** with progress tracking
4. **Example queries** demonstrating semantic search
5. **Interactive search mode** for your own queries

## Example Output

```
============================================================
PINECONE UPSERT QUICKSTART
============================================================

Step 1: Creating Pinecone index...
✅ Index created: skill-seekers-demo

Step 2: Loading documents...
✅ Loaded 180 documents
   Categories: {'api': 38, 'guides': 45, 'models': 42, 'overview': 1, ...}

Step 3: Upserting to Pinecone...
Upserting 180 documents...
Batch size: 100
  Upserted 100/180 documents...
  Upserted 180/180 documents...
✅ Upserted all documents to Pinecone
   Total vectors in index: 180

Step 4: Running example queries...
============================================================

QUERY: How do I create a Django model?
------------------------------------------------------------
  Score: 0.892
  Category: models
  Text: Django models are Python classes that define the structure of your database tables...

  Score: 0.854
  Category: api
  Text: To create a model, inherit from django.db.models.Model and define fields...

============================================================
INTERACTIVE SEMANTIC SEARCH
============================================================
Search the documentation (type 'quit' to exit)

Query: What are Django views?
```

## Features Demonstrated

- **Serverless Index** - Auto-scaling Pinecone infrastructure
- **Batch Upsertion** - Efficient bulk loading (100 docs/batch)
- **Metadata Filtering** - Category-based search filters
- **Semantic Search** - Vector similarity matching
- **Interactive Mode** - Real-time query interface

## Files in This Example

- `quickstart.py` - Complete working example
- `README.md` - This file
- `requirements.txt` - Python dependencies

## Cost Estimate

For 1000 documents:
- **Embeddings:** ~$0.01 (OpenAI ada-002)
- **Storage:** ~$0.03/month (Pinecone serverless)
- **Queries:** ~$0.025 per 100k queries

**Total first month:** ~$0.04 + query costs

## Customization Options

### Change Index Name

```python
INDEX_NAME = "my-custom-index"  # Line 215
```

### Adjust Batch Size

```python
batch_upsert(index, openai_client, documents, batch_size=50)  # Line 239
```

### Filter by Category

```python
matches = semantic_search(
    index=index,
    openai_client=openai_client,
    query="your query",
    category="models"  # Only search in "models" category
)
```

### Use Different Embedding Model

```python
# In create_embeddings() function
response = openai_client.embeddings.create(
    model="text-embedding-3-small",  # Cheaper, smaller dimension
    input=texts
)

# Update index dimension to 1536 (for text-embedding-3-small)
create_index(pc, INDEX_NAME, dimension=1536)
```

## Troubleshooting

**"Index already exists"**
- Normal message if you've run the script before
- The script will reuse the existing index

**"PINECONE_API_KEY not set"**
- Get API key from: https://app.pinecone.io/
- Set environment variable: `export PINECONE_API_KEY=your-key`

**"OPENAI_API_KEY not set"**
- Get API key from: https://platform.openai.com/api-keys
- Set environment variable: `export OPENAI_API_KEY=sk-...`

**"Documents not found"**
- Make sure you've generated documents first (see "Generate Documents" above)
- Check the `DOCS_PATH` in `quickstart.py` matches your output location

**"Rate limit exceeded"**
- OpenAI or Pinecone rate limit hit
- Reduce batch_size: `batch_size=50` or `batch_size=25`
- Add delays between batches

## Advanced Usage

### Load Existing Index

```python
from pinecone import Pinecone

pc = Pinecone(api_key="your-api-key")
index = pc.Index("skill-seekers-demo")

# Query immediately (no need to re-upsert)
results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True
)
```

### Update Existing Documents

```python
# Upsert with same ID to update
index.upsert(vectors=[{
    "id": "doc_123",
    "values": new_embedding,
    "metadata": updated_metadata
}])
```

### Delete Documents

```python
# Delete by ID
index.delete(ids=["doc_123", "doc_456"])

# Delete by metadata filter
index.delete(filter={"category": {"$eq": "deprecated"}})

# Delete all (namespace)
index.delete(delete_all=True)
```

### Use Namespaces

```python
# Upsert to namespace
index.upsert(vectors=vectors, namespace="production")

# Query specific namespace
results = index.query(
    vector=query_embedding,
    namespace="production",
    top_k=5
)
```

## Related Examples

- [LangChain RAG Pipeline](../langchain-rag-pipeline/)
- [LlamaIndex Query Engine](../llama-index-query-engine/)

---

**Need help?** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
