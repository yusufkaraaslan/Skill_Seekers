# LlamaIndex Query Engine Example

Complete example showing how to build a query engine using Skill Seekers nodes with LlamaIndex.

## What This Example Does

1. **Loads** Skill Seekers-generated LlamaIndex Nodes
2. **Creates** a persistent VectorStoreIndex
3. **Demonstrates** query engine capabilities
4. **Provides** interactive chat mode with memory

## Prerequisites

```bash
# Install dependencies
pip install llama-index llama-index-llms-openai llama-index-embeddings-openai

# Set API key
export OPENAI_API_KEY=sk-...
```

## Generate Nodes

First, generate LlamaIndex nodes using Skill Seekers:

```bash
# Option 1: Use preset config (e.g., Django)
skill-seekers scrape --config configs/django.json
skill-seekers package output/django --target llama-index

# Option 2: From GitHub repo
skill-seekers github --repo django/django --name django
skill-seekers package output/django --target llama-index

# Output: output/django-llama-index.json
```

## Run the Example

```bash
cd examples/llama-index-query-engine

# Run the quickstart script
python quickstart.py
```

## What You'll See

1. **Nodes loaded** from JSON file
2. **Index created** with embeddings
3. **Example queries** demonstrating the query engine
4. **Interactive chat mode** with conversational memory

## Example Output

```
============================================================
LLAMAINDEX QUERY ENGINE QUICKSTART
============================================================

Step 1: Loading nodes...
✅ Loaded 180 nodes
   Categories: {'overview': 1, 'models': 45, 'views': 38, ...}

Step 2: Creating index...
✅ Index created and persisted to: ./storage
   Nodes indexed: 180

Step 3: Running example queries...

============================================================
EXAMPLE QUERIES
============================================================

QUERY: What is this documentation about?
------------------------------------------------------------
ANSWER:
This documentation covers Django, a high-level Python web framework
that encourages rapid development and clean, pragmatic design...

SOURCES:
  1. overview (SKILL.md) - Score: 0.85
  2. models (models.md) - Score: 0.78

============================================================
INTERACTIVE CHAT MODE
============================================================
Ask questions about the documentation (type 'quit' to exit)

You: How do I create a model?
```

## Features Demonstrated

- **Query Engine** - Semantic search over documentation
- **Chat Engine** - Conversational interface with memory
- **Source Attribution** - Shows which nodes contributed to answers
- **Persistence** - Index saved to disk for reuse

## Files in This Example

- `quickstart.py` - Complete working example
- `README.md` - This file
- `requirements.txt` - Python dependencies

## Next Steps

1. **Customize** - Modify for your specific documentation
2. **Experiment** - Try different index types (Tree, Keyword)
3. **Extend** - Add filters, custom retrievers, hybrid search
4. **Deploy** - Build a production query engine

## Troubleshooting

**"Documents not found"**
- Make sure you've generated nodes first
- Check the `DOCS_PATH` in `quickstart.py` matches your output location

**"OpenAI API key not found"**
- Set environment variable: `export OPENAI_API_KEY=sk-...`

**"Module not found"**
- Install dependencies: `pip install -r requirements.txt`

## Advanced Usage

### Load Persisted Index

```python
from llama_index.core import load_index_from_storage, StorageContext

# Load existing index
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

### Query with Filters

```python
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

filters = MetadataFilters(
    filters=[ExactMatchFilter(key="category", value="models")]
)

query_engine = index.as_query_engine(filters=filters)
```

### Streaming Responses

```python
query_engine = index.as_query_engine(streaming=True)
response = query_engine.query("Explain Django models")

for text in response.response_gen:
    print(text, end="", flush=True)
```

## Related Examples

- [LangChain RAG Pipeline](../langchain-rag-pipeline/)
- [Pinecone Integration](../pinecone-upsert/)

---

**Need help?** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
