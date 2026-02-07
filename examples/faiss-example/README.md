# FAISS Vector Database Example

Facebook AI Similarity Search (FAISS) is a library for efficient similarity search of dense vectors. Perfect for large-scale semantic search.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate skill
python 1_generate_skill.py

# 3. Build FAISS index (requires OpenAI API key)
export OPENAI_API_KEY=sk-...
python 2_build_faiss_index.py

# 4. Query the index
python 3_query_example.py
```

## What's Different About FAISS?

- **No database server**: Pure Python library
- **Blazing fast**: Optimized C++ implementation
- **Scales to billions**: Efficient for massive datasets
- **Requires embeddings**: You must generate vectors (we use OpenAI)

## Key Features

### Generate Embeddings

FAISS doesn't generate embeddings - you must provide them:

```python
from openai import OpenAI
client = OpenAI()

# Generate embedding
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="Your text here"
)
embedding = response.data[0].embedding  # 1536-dim vector
```

### Build Index

```python
import faiss
import numpy as np

# Create index (L2 distance)
dimension = 1536  # OpenAI ada-002
index = faiss.IndexFlatL2(dimension)

# Add vectors
vectors = np.array(embeddings).astype('float32')
index.add(vectors)

# Save to disk
faiss.write_index(index, "skill.index")
```

### Search

```python
# Load index
index = faiss.read_index("skill.index")

# Query (returns distances + indices)
distances, indices = index.search(query_vector, k=5)
```

## Cost Estimate

OpenAI embeddings: ~$0.10 per 1M tokens
- 20 documents (~10K tokens): < $0.001
- 1000 documents (~500K tokens): ~$0.05

## Files Structure

- `1_generate_skill.py` - Package for FAISS
- `2_build_faiss_index.py` - Generate embeddings & build index
- `3_query_example.py` - Search queries

## Resources

- **FAISS GitHub**: https://github.com/facebookresearch/faiss
- **FAISS Wiki**: https://github.com/facebookresearch/faiss/wiki
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings

---

**Note**: FAISS is best for advanced users who need maximum performance at scale. For simpler use cases, try ChromaDB or Weaviate.
