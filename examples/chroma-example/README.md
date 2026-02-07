# ChromaDB Vector Database Example

This example demonstrates how to use Skill Seekers with ChromaDB, the AI-native open-source embedding database. Chroma is designed to be simple, fast, and easy to use locally.

## What You'll Learn

- How to generate skills in ChromaDB format
- How to create local Chroma collections
- How to perform semantic searches
- How to filter by metadata categories

## Why ChromaDB?

- **No Server Required**: Works entirely in-process (perfect for development)
- **Simple API**: Clean Python interface, no complex setup
- **Fast**: Built for speed with smart indexing
- **Open Source**: MIT licensed, community-driven

## Prerequisites

### Python Dependencies

```bash
pip install -r requirements.txt
```

That's it! No Docker, no server setup. Chroma runs entirely in your Python process.

## Step-by-Step Guide

### Step 1: Generate Skill from Documentation

First, we'll scrape Vue documentation and package it for ChromaDB:

```bash
python 1_generate_skill.py
```

This script will:
1. Scrape Vue docs (limited to 20 pages for demo)
2. Package the skill in ChromaDB format (JSON with documents + metadata + IDs)
3. Save to `output/vue-chroma.json`

**Expected Output:**
```
✅ ChromaDB data packaged successfully!
📦 Output: output/vue-chroma.json
📊 Total documents: 21
📂 Categories: overview (1), guides (8), api (12)
```

**What's in the JSON?**
```json
{
  "documents": [
    "Vue is a progressive JavaScript framework...",
    "Components are the building blocks..."
  ],
  "metadatas": [
    {
      "source": "vue",
      "category": "overview",
      "file": "SKILL.md",
      "type": "documentation",
      "version": "1.0.0"
    }
  ],
  "ids": [
    "a1b2c3d4e5f6...",
    "b2c3d4e5f6g7..."
  ],
  "collection_name": "vue"
}
```

### Step 2: Create Collection and Upload

Now we'll create a ChromaDB collection and load all documents:

```bash
python 2_upload_to_chroma.py
```

This script will:
1. Create an in-memory Chroma client (or persistent with `--persist`)
2. Create a collection with the skill name
3. Add all documents with metadata and IDs
4. Verify the upload was successful

**Expected Output:**
```
📊 Creating ChromaDB client...
✅ Client created (in-memory)

📦 Creating collection: vue
✅ Collection created!

📤 Adding 21 documents to collection...
✅ Successfully added 21 documents to ChromaDB

🔍 Collection 'vue' now contains 21 documents
```

**Persistent Storage:**
```bash
# Save to disk for later use
python 2_upload_to_chroma.py --persist ./chroma_db
```

### Step 3: Query and Search

Now search your knowledge base!

```bash
python 3_query_example.py
```

**With persistent storage:**
```bash
python 3_query_example.py --persist ./chroma_db
```

This script demonstrates:
1. **Semantic Search**: Natural language queries
2. **Metadata Filtering**: Filter by category
3. **Top-K Results**: Get most relevant documents
4. **Distance Scoring**: See how relevant each result is

**Example Queries:**

**Query 1: Semantic Search**
```
Query: "How do I create a Vue component?"
Top 3 results:

1. [Distance: 0.234] guides/components.md
   Components are reusable Vue instances with a name. You can use them as custom
   elements inside a root Vue instance...

2. [Distance: 0.298] api/component_api.md
   The component API reference describes all available options for defining
   components using the Options API...

3. [Distance: 0.312] guides/single_file_components.md
   Single-File Components (SFCs) allow you to define templates, logic, and
   styling in a single .vue file...
```

**Query 2: Filtered Search**
```
Query: "reactivity"
Filter: category = "api"

Results:
1. ref() - Create reactive references
2. reactive() - Create reactive proxies
3. computed() - Create computed properties
```

## Understanding ChromaDB Features

### Semantic Search

Chroma automatically:
- Generates embeddings for your documents (using default model)
- Indexes them for fast similarity search
- Finds semantically similar content

**Distance Scores:**
- Lower = more similar
- `0.0` = identical
- `< 0.5` = very relevant
- `0.5-1.0` = somewhat relevant
- `> 1.0` = less relevant

### Metadata Filtering

Filter results before semantic search:
```python
collection.query(
    query_texts=["your query"],
    n_results=5,
    where={"category": "api"}
)
```

**Supported operators:**
- `$eq`: Equal to
- `$ne`: Not equal to
- `$gt`, `$gte`: Greater than (or equal)
- `$lt`, `$lte`: Less than (or equal)
- `$in`: In list
- `$nin`: Not in list

**Complex filters:**
```python
where={
    "$and": [
        {"category": {"$eq": "api"}},
        {"type": {"$eq": "reference"}}
    ]
}
```

### Collection Management

```python
# List all collections
client.list_collections()

# Get collection
collection = client.get_collection("vue")

# Get count
collection.count()

# Delete collection
client.delete_collection("vue")
```

## Customization

### Use Your Own Embeddings

Chroma supports custom embedding functions:

```python
from chromadb.utils import embedding_functions

# OpenAI embeddings
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="your-key",
    model_name="text-embedding-ada-002"
)

collection = client.create_collection(
    name="your_skill",
    embedding_function=openai_ef
)
```

**Supported embedding functions:**
- **OpenAI**: `text-embedding-ada-002` (best quality)
- **Cohere**: `embed-english-v2.0`
- **HuggingFace**: Various models (local, no API key)
- **Sentence Transformers**: Local models

### Generate Different Skills

```bash
# Change the config in 1_generate_skill.py
"--config", "configs/django.json",  # Your framework

# Or use CLI directly
skill-seekers scrape --config configs/flask.json
skill-seekers package output/flask --target chroma
```

### Adjust Query Parameters

In `3_query_example.py`:

```python
# Get more results
n_results=10  # Default is 5

# Include more metadata
include=["documents", "metadatas", "distances"]

# Different distance metrics
# (configure when creating collection)
metadata={"hnsw:space": "cosine"}  # or "l2", "ip"
```

## Performance Tips

1. **Batch Operations**: Add documents in batches for better performance
   ```python
   collection.add(
       documents=batch_docs,
       metadatas=batch_metadata,
       ids=batch_ids
   )
   ```

2. **Persistent Storage**: Use `--persist` for production
   ```bash
   python 2_upload_to_chroma.py --persist ./prod_db
   ```

3. **Custom Embeddings**: Use OpenAI for best quality (costs $)
4. **Index Tuning**: Adjust HNSW parameters for speed vs accuracy

## Troubleshooting

### Import Error
```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution:**
```bash
pip install chromadb
```

### Collection Already Exists
```
Error: Collection 'vue' already exists
```

**Solution:**
```python
# Delete existing collection
client.delete_collection("vue")

# Or use --reset flag
python 2_upload_to_chroma.py --reset
```

### Empty Results
```
Query returned empty results
```

**Possible causes:**
1. Collection empty: Check `collection.count()`
2. Query too specific: Try broader queries
3. Wrong collection name: Verify collection exists

**Debug:**
```python
# Check collection contents
collection.get()  # Get all documents

# Check embedding function
collection._embedding_function  # Should not be None
```

### Performance Issues
```
Query is slow
```

**Solutions:**
1. Use persistent storage (faster than in-memory for large datasets)
2. Reduce `n_results` (fewer results = faster)
3. Add metadata filters to narrow search space
4. Consider using OpenAI embeddings (better quality = faster convergence)

## Next Steps

1. **Try other skills**: Package your favorite documentation
2. **Build a chatbot**: Integrate with LangChain or LlamaIndex
3. **Production deployment**: Use persistent storage + API wrapper
4. **Custom embeddings**: Experiment with different models

## Resources

- **ChromaDB Docs**: https://docs.trychroma.com/
- **GitHub**: https://github.com/chroma-core/chroma
- **Discord**: https://discord.gg/MMeYNTmh3x
- **Skill Seekers**: https://github.com/yourusername/skill-seekers

## File Structure

```
chroma-example/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── 1_generate_skill.py            # Generate ChromaDB-format skill
├── 2_upload_to_chroma.py          # Create collection and upload
├── 3_query_example.py             # Query demonstrations
└── sample_output/                 # Example outputs
    ├── vue-chroma.json            # Generated skill (21 docs)
    └── query_results.txt          # Sample query results
```

## Comparison: Chroma vs Weaviate

| Feature | ChromaDB | Weaviate |
|---------|----------|----------|
| **Setup** | ✅ No server needed | ⚠️ Docker/Cloud required |
| **API** | ✅ Very simple | ⚠️ More complex |
| **Performance** | ✅ Fast for < 1M docs | ✅ Scales to billions |
| **Hybrid Search** | ❌ Semantic only | ✅ Keyword + semantic |
| **Production** | ✅ Good for small-medium | ✅ Built for scale |

**Use Chroma for:** Development, prototypes, small-medium datasets (< 1M docs)
**Use Weaviate for:** Production, large datasets (> 1M docs), hybrid search

---

**Last Updated:** February 2026
**Tested With:** ChromaDB v0.4.22, Python 3.10+, skill-seekers v2.10.0
