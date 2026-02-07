# Weaviate Integration with Skill Seekers

**Status:** ✅ Production Ready
**Difficulty:** Intermediate
**Last Updated:** February 7, 2026

---

## ❌ The Problem

Building RAG applications with Weaviate involves several challenges:

1. **Manual Data Schema Design** - Need to define GraphQL schemas and object properties manually for each documentation project
2. **Complex Hybrid Search** - Setting up both BM25 keyword search and vector search requires understanding Weaviate's query language
3. **Multi-Tenancy Configuration** - Properly isolating different documentation sets requires tenant management

**Example Pain Point:**

```python
# Manual schema creation for each framework
client.schema.create_class({
    "class": "ReactDocs",
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "category", "dataType": ["string"]},
        {"name": "source", "dataType": ["string"]},
        # ... 10+ more properties
    ],
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {"model": "ada-002"}
    }
})
```

---

## ✅ The Solution

Skill Seekers automates Weaviate integration with structured, production-ready data:

**Benefits:**
- ✅ Auto-formatted objects with all metadata properties
- ✅ Consistent schema across all frameworks
- ✅ Compatible with hybrid search (BM25 + vector)
- ✅ Works with Weaviate Cloud Services (WCS) and self-hosted
- ✅ Supports multi-tenancy for documentation isolation

**Result:** 10-minute setup, production-ready vector search with enterprise features.

---

## ⚡ Quick Start (5 Minutes)

### Prerequisites

```bash
# Install Weaviate Python client
pip install weaviate-client>=3.25.0

# Or with Skill Seekers
pip install skill-seekers[all-llms]
```

**What you need:**
- Weaviate instance (WCS or self-hosted)
- Weaviate API key (if using WCS)
- OpenAI API key (for embeddings)

### Generate Weaviate-Ready Documents

```bash
# Step 1: Scrape documentation
skill-seekers scrape --config configs/react.json

# Step 2: Package for Weaviate (creates LangChain format)
skill-seekers package output/react --target langchain

# Output: output/react-langchain.json (Weaviate-compatible)
```

### Upload to Weaviate

```python
import weaviate
import json

# Connect to Weaviate
client = weaviate.Client(
    url="https://your-instance.weaviate.network",
    auth_client_secret=weaviate.AuthApiKey(api_key="your-api-key"),
    additional_headers={
        "X-OpenAI-Api-Key": "your-openai-key"
    }
)

# Create schema (first time only)
client.schema.create_class({
    "class": "Documentation",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {"model": "ada-002"}
    }
})

# Load documents
with open("output/react-langchain.json") as f:
    documents = json.load(f)

# Batch upload
with client.batch as batch:
    for i, doc in enumerate(documents):
        properties = {
            "content": doc["page_content"],
            "source": doc["metadata"]["source"],
            "category": doc["metadata"]["category"],
            "file": doc["metadata"]["file"],
            "type": doc["metadata"]["type"]
        }
        batch.add_data_object(properties, "Documentation")

        if (i + 1) % 100 == 0:
            print(f"Uploaded {i + 1} documents...")

print(f"✅ Uploaded {len(documents)} documents to Weaviate")
```

### Query with Hybrid Search

```python
# Hybrid search: BM25 + vector similarity
result = client.query.get("Documentation", ["content", "category"]) \
    .with_hybrid(
        query="How do I use React hooks?",
        alpha=0.75  # 0=BM25 only, 1=vector only, 0.5=balanced
    ) \
    .with_limit(3) \
    .do()

for item in result["data"]["Get"]["Documentation"]:
    print(f"Category: {item['category']}")
    print(f"Content: {item['content'][:200]}...")
    print()
```

---

## 📖 Detailed Setup Guide

### Step 1: Set Up Weaviate Instance

**Option A: Weaviate Cloud Services (Recommended)**

1. Sign up at [console.weaviate.cloud](https://console.weaviate.cloud)
2. Create a cluster (free tier available)
3. Get your API endpoint and API key
4. Note your cluster URL: `https://your-cluster.weaviate.network`

**Option B: Self-Hosted (Docker)**

```bash
# docker-compose.yml
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-openai'
      ENABLE_MODULES: 'text2vec-openai'
      OPENAI_APIKEY: 'your-openai-key'
    volumes:
      - ./weaviate-data:/var/lib/weaviate

# Start Weaviate
docker-compose up -d
```

**Option C: Kubernetes (Production)**

```bash
helm repo add weaviate https://weaviate.github.io/weaviate-helm
helm install weaviate weaviate/weaviate \
  --set modules.text2vec-openai.enabled=true \
  --set env.OPENAI_APIKEY=your-key
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

### Step 3: Create Weaviate Schema

```python
import weaviate

client = weaviate.Client(
    url="https://your-instance.weaviate.network",
    auth_client_secret=weaviate.AuthApiKey(api_key="your-api-key"),
    additional_headers={
        "X-OpenAI-Api-Key": "your-openai-key"
    }
)

# Define schema with all Skill Seekers metadata
schema = {
    "class": "Documentation",
    "description": "Framework documentation from Skill Seekers",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "ada-002",
            "vectorizeClassName": False
        }
    },
    "properties": [
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Documentation content",
            "moduleConfig": {
                "text2vec-openai": {"skip": False}
            }
        },
        {
            "name": "source",
            "dataType": ["string"],
            "description": "Framework name"
        },
        {
            "name": "category",
            "dataType": ["string"],
            "description": "Documentation category"
        },
        {
            "name": "file",
            "dataType": ["string"],
            "description": "Source file"
        },
        {
            "name": "type",
            "dataType": ["string"],
            "description": "Document type"
        },
        {
            "name": "url",
            "dataType": ["string"],
            "description": "Original URL"
        }
    ]
}

# Create class (idempotent)
try:
    client.schema.create_class(schema)
    print("✅ Schema created")
except Exception as e:
    print(f"Schema already exists or error: {e}")
```

### Step 4: Batch Upload Documents

```python
import json
from weaviate.util import generate_uuid5

# Load documents
with open("output/django-langchain.json") as f:
    documents = json.load(f)

# Configure batch
client.batch.configure(
    batch_size=100,
    dynamic=True,
    timeout_retries=3,
)

# Upload with batch
with client.batch as batch:
    for i, doc in enumerate(documents):
        properties = {
            "content": doc["page_content"],
            "source": doc["metadata"]["source"],
            "category": doc["metadata"]["category"],
            "file": doc["metadata"]["file"],
            "type": doc["metadata"]["type"],
            "url": doc["metadata"].get("url", "")
        }

        # Generate deterministic UUID
        uuid = generate_uuid5(properties["content"])

        batch.add_data_object(
            data_object=properties,
            class_name="Documentation",
            uuid=uuid
        )

        if (i + 1) % 100 == 0:
            print(f"Uploaded {i + 1}/{len(documents)} documents...")

print(f"✅ Uploaded {len(documents)} documents to Weaviate")

# Verify upload
result = client.query.aggregate("Documentation").with_meta_count().do()
count = result["data"]["Aggregate"]["Documentation"][0]["meta"]["count"]
print(f"Total documents in Weaviate: {count}")
```

### Step 5: Query with Filters

```python
# Hybrid search with category filter
result = client.query.get("Documentation", ["content", "category", "source"]) \
    .with_hybrid(
        query="How do I create a Django model?",
        alpha=0.75
    ) \
    .with_where({
        "path": ["category"],
        "operator": "Equal",
        "valueString": "models"
    }) \
    .with_limit(5) \
    .do()

for item in result["data"]["Get"]["Documentation"]:
    print(f"Source: {item['source']}")
    print(f"Category: {item['category']}")
    print(f"Content: {item['content'][:200]}...")
    print()
```

---

## 🚀 Advanced Usage

### 1. Multi-Tenancy for Framework Isolation

```python
# Enable multi-tenancy on schema
client.schema.update_config("Documentation", {
    "multiTenancyConfig": {"enabled": True}
})

# Add tenants
client.schema.add_class_tenants(
    class_name="Documentation",
    tenants=[
        {"name": "react"},
        {"name": "django"},
        {"name": "fastapi"}
    ]
)

# Upload to specific tenant
with client.batch as batch:
    batch.add_data_object(
        data_object={"content": "...", "category": "hooks"},
        class_name="Documentation",
        tenant="react"
    )

# Query specific tenant
result = client.query.get("Documentation", ["content"]) \
    .with_tenant("react") \
    .with_hybrid(query="React hooks") \
    .do()
```

### 2. Named Vectors for Multiple Embeddings

```python
# Schema with multiple vector spaces
schema = {
    "class": "Documentation",
    "vectorizer": "text2vec-openai",
    "vectorConfig": {
        "content": {
            "vectorizer": {
                "text2vec-openai": {"model": "ada-002"}
            }
        },
        "title": {
            "vectorizer": {
                "text2vec-openai": {"model": "ada-002"}
            }
        }
    },
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "title", "dataType": ["string"]}
    ]
}

# Query specific vector
result = client.query.get("Documentation", ["content", "title"]) \
    .with_near_text({"concepts": ["authentication"]}, target_vector="content") \
    .do()
```

### 3. Generative Search (RAG in Weaviate)

```python
# Answer questions using Weaviate's generative module
result = client.query.get("Documentation", ["content", "category"]) \
    .with_hybrid(query="How do I use Django middleware?") \
    .with_generate(
        single_prompt="Explain this concept: {content}",
        grouped_task="Summarize Django middleware based on these docs"
    ) \
    .with_limit(3) \
    .do()

# Access generated answer
answer = result["data"]["Get"]["Documentation"][0]["_additional"]["generate"]["singleResult"]
print(f"Generated Answer: {answer}")
```

### 4. GraphQL Cross-References

```python
# Create relationships between documentation
schema = {
    "class": "Documentation",
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "relatedTo", "dataType": ["Documentation"]}  # Cross-reference
    ]
}

# Link related docs
client.data_object.reference.add(
    from_class_name="Documentation",
    from_uuid=doc1_uuid,
    from_property_name="relatedTo",
    to_class_name="Documentation",
    to_uuid=doc2_uuid
)

# Query with references
result = client.query.get("Documentation", ["content", "relatedTo {... on Documentation {content}}"]) \
    .with_hybrid(query="React hooks") \
    .do()
```

### 5. Backup and Restore

```python
# Backup all data
backup_name = "docs-backup-2026-02-07"
result = client.backup.create(
    backup_id=backup_name,
    backend="filesystem",
    include_classes=["Documentation"]
)

# Wait for completion
status = client.backup.get_create_status(backup_id=backup_name, backend="filesystem")
print(f"Backup status: {status['status']}")

# Restore from backup
result = client.backup.restore(
    backup_id=backup_name,
    backend="filesystem",
    include_classes=["Documentation"]
)
```

---

## 📋 Best Practices

### 1. Choose the Right Alpha Value

```python
# Alpha controls BM25 vs vector balance
# 0.0 = Pure BM25 (keyword matching)
# 1.0 = Pure vector (semantic search)
# 0.75 = Recommended (75% semantic, 25% keyword)

# For exact terms (API names, functions)
result = client.query.get(...).with_hybrid(query="useState", alpha=0.3).do()

# For conceptual queries
result = client.query.get(...).with_hybrid(query="state management", alpha=0.9).do()

# Balanced (recommended default)
result = client.query.get(...).with_hybrid(query="React hooks", alpha=0.75).do()
```

### 2. Use Tenant Isolation for Multi-Framework

```python
# Separate tenants prevent cross-contamination
tenants = ["react", "vue", "angular", "svelte"]

for tenant in tenants:
    client.schema.add_class_tenants("Documentation", [{"name": tenant}])

# Query only React docs
result = client.query.get("Documentation", ["content"]) \
    .with_tenant("react") \
    .with_hybrid(query="components") \
    .do()
```

### 3. Monitor Performance

```python
# Check cluster health
health = client.cluster.get_nodes_status()
print(f"Nodes: {len(health)}")
for node in health:
    print(f"  {node['name']}: {node['status']}")

# Monitor query performance
import time
start = time.time()
result = client.query.get("Documentation", ["content"]).with_limit(10).do()
latency = time.time() - start
print(f"Query latency: {latency*1000:.2f}ms")

# Check object count
stats = client.query.aggregate("Documentation").with_meta_count().do()
count = stats["data"]["Aggregate"]["Documentation"][0]["meta"]["count"]
print(f"Total objects: {count}")
```

### 4. Handle Updates Efficiently

```python
from weaviate.util import generate_uuid5

# Update existing object (idempotent UUID)
uuid = generate_uuid5("unique-content-identifier")
client.data_object.replace(
    data_object={"content": "updated content", ...},
    class_name="Documentation",
    uuid=uuid
)

# Delete obsolete objects
client.data_object.delete(uuid=uuid, class_name="Documentation")

# Delete by filter
client.batch.delete_objects(
    class_name="Documentation",
    where={
        "path": ["category"],
        "operator": "Equal",
        "valueString": "deprecated"
    }
)
```

### 5. Use Async for Large Uploads

```python
import asyncio
from weaviate import Client

async def upload_batch(client, documents, start_idx, batch_size):
    """Upload documents asynchronously."""
    with client.batch as batch:
        for i in range(start_idx, min(start_idx + batch_size, len(documents))):
            doc = documents[i]
            properties = {
                "content": doc["page_content"],
                **doc["metadata"]
            }
            batch.add_data_object(properties, "Documentation")

async def upload_all(documents, batch_size=100):
    client = Client(url="...", auth_client_secret=...)

    tasks = []
    for i in range(0, len(documents), batch_size):
        tasks.append(upload_batch(client, documents, i, batch_size))

    await asyncio.gather(*tasks)
    print(f"✅ Uploaded {len(documents)} documents")

# Usage
asyncio.run(upload_all(documents))
```

---

## 🔥 Real-World Example: Multi-Framework Documentation Bot

```python
import weaviate
import json
from openai import OpenAI

class MultiFrameworkBot:
    def __init__(self, weaviate_url: str, weaviate_key: str, openai_key: str):
        self.weaviate = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_key),
            additional_headers={"X-OpenAI-Api-Key": openai_key}
        )
        self.openai = OpenAI(api_key=openai_key)

    def setup_tenants(self, frameworks: list[str]):
        """Set up multi-tenancy for frameworks."""
        # Enable multi-tenancy
        self.weaviate.schema.update_config("Documentation", {
            "multiTenancyConfig": {"enabled": True}
        })

        # Add tenants
        tenants = [{"name": fw} for fw in frameworks]
        self.weaviate.schema.add_class_tenants("Documentation", tenants)
        print(f"✅ Set up tenants: {frameworks}")

    def ingest_framework(self, framework: str, docs_path: str):
        """Ingest documentation for specific framework."""
        with open(docs_path) as f:
            documents = json.load(f)

        with self.weaviate.batch as batch:
            batch.configure(batch_size=100)

            for doc in documents:
                properties = {
                    "content": doc["page_content"],
                    "source": doc["metadata"]["source"],
                    "category": doc["metadata"]["category"],
                    "file": doc["metadata"]["file"],
                    "type": doc["metadata"]["type"]
                }

                batch.add_data_object(
                    data_object=properties,
                    class_name="Documentation",
                    tenant=framework
                )

        print(f"✅ Ingested {len(documents)} docs for {framework}")

    def query_framework(self, framework: str, question: str, category: str = None):
        """Query specific framework with hybrid search."""
        # Build query
        query = self.weaviate.query.get("Documentation", ["content", "category", "source"]) \
            .with_tenant(framework) \
            .with_hybrid(query=question, alpha=0.75)

        # Add category filter if specified
        if category:
            query = query.with_where({
                "path": ["category"],
                "operator": "Equal",
                "valueString": category
            })

        result = query.with_limit(3).do()

        # Extract context
        docs = result["data"]["Get"]["Documentation"]
        context = "\n\n".join([doc["content"][:500] for doc in docs])

        # Generate answer
        completion = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert in {framework}. Answer based on the documentation."
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
                    "category": doc["category"],
                    "source": doc["source"]
                }
                for doc in docs
            ]
        }

    def compare_frameworks(self, frameworks: list[str], question: str):
        """Compare how different frameworks handle the same concept."""
        results = {}
        for framework in frameworks:
            try:
                result = self.query_framework(framework, question)
                results[framework] = result["answer"]
            except Exception as e:
                results[framework] = f"Error: {e}"

        return results

# Usage
bot = MultiFrameworkBot(
    weaviate_url="https://your-cluster.weaviate.network",
    weaviate_key="your-weaviate-key",
    openai_key="your-openai-key"
)

# Set up tenants
bot.setup_tenants(["react", "vue", "angular", "svelte"])

# Ingest documentation
bot.ingest_framework("react", "output/react-langchain.json")
bot.ingest_framework("vue", "output/vue-langchain.json")
bot.ingest_framework("angular", "output/angular-langchain.json")
bot.ingest_framework("svelte", "output/svelte-langchain.json")

# Query specific framework
result = bot.query_framework("react", "How do I manage state?", category="hooks")
print(f"React Answer: {result['answer']}")

# Compare frameworks
comparison = bot.compare_frameworks(
    frameworks=["react", "vue", "angular", "svelte"],
    question="How do I handle user input?"
)

for framework, answer in comparison.items():
    print(f"\n{framework.upper()}:")
    print(answer)
```

**Output:**
```
✅ Set up tenants: ['react', 'vue', 'angular', 'svelte']
✅ Ingested 1247 docs for react
✅ Ingested 892 docs for vue
✅ Ingested 1534 docs for angular
✅ Ingested 743 docs for svelte

React Answer: In React, you manage state using the useState hook...

REACT:
Use the useState hook to create controlled components...

VUE:
Vue provides v-model for two-way binding...

ANGULAR:
Angular uses ngModel directive with FormsModule...

SVELTE:
Svelte offers reactive declarations with bind:value...
```

---

## 🐛 Troubleshooting

### Issue: Connection Failed

**Problem:** "Could not connect to Weaviate at http://localhost:8080"

**Solutions:**

1. **Check Weaviate is running:**
```bash
docker ps | grep weaviate
curl http://localhost:8080/v1/meta
```

2. **Verify URL format:**
```python
# Local: no https
client = weaviate.Client("http://localhost:8080")

# WCS: use https
client = weaviate.Client("https://your-cluster.weaviate.network")
```

3. **Check authentication:**
```python
# WCS requires API key
client = weaviate.Client(
    url="https://your-cluster.weaviate.network",
    auth_client_secret=weaviate.AuthApiKey(api_key="your-key")
)
```

### Issue: Schema Already Exists

**Problem:** "Class 'Documentation' already exists"

**Solutions:**

1. **Delete and recreate:**
```python
client.schema.delete_class("Documentation")
client.schema.create_class(schema)
```

2. **Update existing schema:**
```python
client.schema.add_class_properties("Documentation", new_properties)
```

3. **Check existing schema:**
```python
existing = client.schema.get("Documentation")
print(json.dumps(existing, indent=2))
```

### Issue: Embedding API Key Not Set

**Problem:** "Vectorizer requires X-OpenAI-Api-Key header"

**Solution:**
```python
client = weaviate.Client(
    url="https://your-cluster.weaviate.network",
    additional_headers={
        "X-OpenAI-Api-Key": "sk-..."  # OpenAI key
        # or "X-Cohere-Api-Key": "..."
        # or "X-HuggingFace-Api-Key": "..."
    }
)
```

### Issue: Slow Batch Upload

**Problem:** Uploading 10,000 docs takes >10 minutes

**Solutions:**

1. **Enable dynamic batching:**
```python
client.batch.configure(
    batch_size=100,
    dynamic=True,  # Auto-adjust batch size
    timeout_retries=3
)
```

2. **Use parallel batches:**
```python
from concurrent.futures import ThreadPoolExecutor

def upload_chunk(docs_chunk):
    with client.batch as batch:
        for doc in docs_chunk:
            batch.add_data_object(doc, "Documentation")

with ThreadPoolExecutor(max_workers=4) as executor:
    chunk_size = len(documents) // 4
    chunks = [documents[i:i+chunk_size] for i in range(0, len(documents), chunk_size)]
    executor.map(upload_chunk, chunks)
```

### Issue: Hybrid Search Not Working

**Problem:** "with_hybrid() returns no results"

**Solutions:**

1. **Check vectorizer is enabled:**
```python
schema = client.schema.get("Documentation")
print(schema["vectorizer"])  # Should be "text2vec-openai" or similar
```

2. **Try pure vector search:**
```python
# Test vector search works
result = client.query.get("Documentation", ["content"]) \
    .with_near_text({"concepts": ["test query"]}) \
    .do()
```

3. **Verify BM25 index:**
```python
# BM25 requires inverted index
schema["invertedIndexConfig"] = {"bm25": {"enabled": True}}
client.schema.update_config("Documentation", schema)
```

### Issue: Tenant Not Found

**Problem:** "Tenant 'react' does not exist"

**Solutions:**

1. **List existing tenants:**
```python
tenants = client.schema.get_class_tenants("Documentation")
print([t["name"] for t in tenants])
```

2. **Add missing tenant:**
```python
client.schema.add_class_tenants("Documentation", [{"name": "react"}])
```

3. **Check multi-tenancy is enabled:**
```python
schema = client.schema.get("Documentation")
print(schema.get("multiTenancyConfig", {}).get("enabled"))  # Should be True
```

---

## 📊 Before vs. After

| Aspect | Without Skill Seekers | With Skill Seekers |
|--------|----------------------|-------------------|
| **Schema Design** | Manual property definition for each framework | Auto-formatted with consistent structure |
| **Data Ingestion** | Custom scraping + parsing logic | One command: `skill-seekers scrape` |
| **Metadata** | Manual extraction from docs | Auto-extracted (category, source, file, type) |
| **Multi-Framework** | Separate schemas and databases | Single tenant-based schema |
| **Hybrid Search** | Complex query construction | Pre-optimized for BM25 + vector |
| **Setup Time** | 4-6 hours | 10 minutes |
| **Code Required** | 500+ lines scraping logic | 30 lines upload script |
| **Maintenance** | Update scrapers for each site | Update config once |

---

## 🎯 Next Steps

### Enhance Your Weaviate Integration

1. **Add Generative Search:**
   ```bash
   # Enable qna-openai module in Weaviate
   # Then use with_generate() for RAG
   ```

2. **Implement Semantic Chunking:**
   ```bash
   skill-seekers scrape --config configs/fastapi.json --chunk-for-rag --chunk-size 512
   ```

3. **Set Up Multi-Tenancy:**
   - Create tenant per framework
   - Query with `.with_tenant("framework-name")`
   - Isolate different documentation sets

4. **Monitor Performance:**
   - Track query latency
   - Monitor object count
   - Check cluster health

### Related Guides

- **[Haystack Integration](HAYSTACK.md)** - Use Weaviate as document store for Haystack
- **[RAG Pipelines Guide](RAG_PIPELINES.md)** - Build complete RAG systems
- **[Multi-LLM Support](MULTI_LLM_SUPPORT.md)** - Use different embedding models
- **[INTEGRATIONS.md](INTEGRATIONS.md)** - See all integration options

### Resources

- **Weaviate Docs:** https://weaviate.io/developers/weaviate
- **Python Client:** https://weaviate.io/developers/weaviate/client-libraries/python
- **Support:** https://github.com/yusufkaraaslan/Skill_Seekers/discussions

---

**Questions?** Open an issue: https://github.com/yusufkaraaslan/Skill_Seekers/issues
**Website:** https://skillseekersweb.com/
**Last Updated:** February 7, 2026
