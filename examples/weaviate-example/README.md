# Weaviate Vector Database Example

This example demonstrates how to use Skill Seekers with Weaviate, a powerful vector database with hybrid search capabilities (keyword + semantic).

## What You'll Learn

- How to generate skills in Weaviate format
- How to create a Weaviate schema and upload data
- How to perform hybrid searches (keyword + vector)
- How to filter by metadata categories

## Prerequisites

### 1. Weaviate Instance

**Option A: Weaviate Cloud (Recommended for production)**
- Sign up at https://console.weaviate.cloud/
- Create a free sandbox cluster
- Get your cluster URL and API key

**Option B: Local Docker (Recommended for development)**
```bash
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  semitechnologies/weaviate:latest
```

### 2. Python Dependencies

```bash
pip install -r requirements.txt
```

## Step-by-Step Guide

### Step 1: Generate Skill from Documentation

First, we'll scrape React documentation and package it for Weaviate:

```bash
python 1_generate_skill.py
```

This script will:
1. Scrape React docs (limited to 20 pages for demo)
2. Package the skill in Weaviate format (JSON with schema + objects)
3. Save to `sample_output/react-weaviate.json`

**Expected Output:**
```
✅ Weaviate data packaged successfully!
📦 Output: output/react-weaviate.json
📊 Total objects: 21
📂 Categories: overview (1), guides (8), api (12)
```

**What's in the JSON?**
```json
{
  "schema": {
    "class": "React",
    "description": "React documentation skill",
    "properties": [
      {"name": "content", "dataType": ["text"]},
      {"name": "source", "dataType": ["text"]},
      {"name": "category", "dataType": ["text"]},
      ...
    ]
  },
  "objects": [
    {
      "id": "uuid-here",
      "properties": {
        "content": "React is a JavaScript library...",
        "source": "react",
        "category": "overview",
        ...
      }
    }
  ],
  "class_name": "React"
}
```

### Step 2: Upload to Weaviate

Now we'll create the schema and upload all objects to Weaviate:

```bash
python 2_upload_to_weaviate.py
```

**For local Docker:**
```bash
python 2_upload_to_weaviate.py --url http://localhost:8080
```

**For Weaviate Cloud:**
```bash
python 2_upload_to_weaviate.py \
  --url https://your-cluster.weaviate.network \
  --api-key YOUR_API_KEY
```

This script will:
1. Connect to your Weaviate instance
2. Create the schema (class + properties)
3. Batch upload all objects
4. Verify the upload was successful

**Expected Output:**
```
🔗 Connecting to Weaviate at http://localhost:8080...
✅ Weaviate is ready!

📊 Creating schema: React
✅ Schema created successfully!

📤 Uploading 21 objects in batches...
✅ Batch 1/1 uploaded (21 objects)

✅ Successfully uploaded 21 documents to Weaviate
🔍 Class 'React' now contains 21 objects
```

### Step 3: Query and Search

Now the fun part - querying your knowledge base!

```bash
python 3_query_example.py
```

**For local Docker:**
```bash
python 3_query_example.py --url http://localhost:8080
```

**For Weaviate Cloud:**
```bash
python 3_query_example.py \
  --url https://your-cluster.weaviate.network \
  --api-key YOUR_API_KEY
```

This script demonstrates:
1. **Keyword Search**: Traditional text search
2. **Hybrid Search**: Combines keyword + vector similarity
3. **Metadata Filtering**: Filter by category
4. **Limit and Offset**: Pagination

**Example Queries:**

**Query 1: Hybrid Search**
```
Query: "How do I use React hooks?"
Alpha: 0.5 (50% keyword, 50% vector)

Results:
1. Category: api
   Snippet: Hooks are functions that let you "hook into" React state and lifecycle...

2. Category: guides
   Snippet: To use a Hook, you need to call it at the top level of your component...
```

**Query 2: Filter by Category**
```
Query: API reference
Category: api

Results:
1. useState Hook - Manage component state
2. useEffect Hook - Perform side effects
3. useContext Hook - Access context values
```

## Understanding Weaviate Features

### Hybrid Search (`alpha` parameter)

Weaviate's killer feature is hybrid search, which combines:
- **Keyword Search (BM25)**: Traditional text matching
- **Vector Search (ANN)**: Semantic similarity

Control the balance with `alpha`:
- `alpha=0`: Pure keyword search (BM25 only)
- `alpha=0.5`: Balanced (default - recommended)
- `alpha=1`: Pure vector search (semantic only)

**When to use what:**
- **Exact terms** (API names, error messages): `alpha=0` to `alpha=0.3`
- **Concepts** (how to do X, why does Y): `alpha=0.7` to `alpha=1`
- **General queries**: `alpha=0.5` (balanced)

### Metadata Filtering

Filter results by any property:
```python
.with_where({
    "path": ["category"],
    "operator": "Equal",
    "valueText": "api"
})
```

Supported operators:
- `Equal`, `NotEqual`
- `GreaterThan`, `LessThan`
- `And`, `Or`, `Not`

### Schema Design

Our schema includes:
- **content**: The actual documentation text (vectorized)
- **source**: Skill name (e.g., "react")
- **category**: Document category (e.g., "api", "guides")
- **file**: Source file name
- **type**: Document type ("overview" or "reference")
- **version**: Skill version

## Customization

### Generate Your Own Skill

Want to use a different documentation source? Easy:

```python
# 1_generate_skill.py (modify line 10)
"--config", "configs/vue.json",  # Change to your config
```

Or scrape from scratch:
```bash
skill-seekers scrape --config configs/your_framework.json
skill-seekers package output/your_framework --target weaviate
```

### Adjust Search Parameters

In `3_query_example.py`, modify:
```python
# Adjust hybrid search balance
alpha=0.7  # More semantic, less keyword

# Adjust result count
.with_limit(10)  # Get more results

# Add more filters
.with_where({
    "operator": "And",
    "operands": [
        {"path": ["category"], "operator": "Equal", "valueText": "api"},
        {"path": ["type"], "operator": "Equal", "valueText": "reference"}
    ]
})
```

## Troubleshooting

### Connection Refused
```
Error: Connection refused to http://localhost:8080
```

**Solution:** Ensure Weaviate is running:
```bash
docker ps | grep weaviate
# If not running, start it:
docker start weaviate
```

### Schema Already Exists
```
Error: Class 'React' already exists
```

**Solution:** Delete the existing class:
```bash
# In Python or using Weaviate API
client.schema.delete_class("React")
```

Or use the example's built-in reset:
```bash
python 2_upload_to_weaviate.py --reset
```

### Empty Results
```
Query returned 0 results
```

**Possible causes:**
1. **No embeddings**: Weaviate needs a vectorizer configured (we use default)
2. **Wrong class name**: Check the class name matches
3. **Data not uploaded**: Verify with `client.query.aggregate("React").with_meta_count().do()`

**Solution:** Check object count:
```python
result = client.query.aggregate("React").with_meta_count().do()
print(result)  # Should show {"data": {"Aggregate": {"React": [{"meta": {"count": 21}}]}}}
```

## Next Steps

1. **Try other skills**: Generate skills for your favorite frameworks
2. **Production deployment**: Use Weaviate Cloud for scalability
3. **Add custom vectorizers**: Use OpenAI, Cohere, or local models
4. **Build RAG apps**: Integrate with LangChain or LlamaIndex

## Resources

- **Weaviate Docs**: https://weaviate.io/developers/weaviate
- **Hybrid Search**: https://weaviate.io/developers/weaviate/search/hybrid
- **Python Client**: https://weaviate.io/developers/weaviate/client-libraries/python
- **Skill Seekers Docs**: https://github.com/yourusername/skill-seekers

## File Structure

```
weaviate-example/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── 1_generate_skill.py            # Generate Weaviate-format skill
├── 2_upload_to_weaviate.py        # Upload to Weaviate instance
├── 3_query_example.py             # Query demonstrations
└── sample_output/                 # Example outputs
    ├── react-weaviate.json        # Generated skill (21 objects)
    └── query_results.txt          # Sample query results
```

---

**Last Updated:** February 2026
**Tested With:** Weaviate v1.25.0, Python 3.10+, skill-seekers v2.10.0
