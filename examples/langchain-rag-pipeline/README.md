# LangChain RAG Pipeline Example

Complete example showing how to build a RAG (Retrieval-Augmented Generation) pipeline using Skill Seekers documents with LangChain.

## What This Example Does

1. **Loads** Skill Seekers-generated LangChain Documents
2. **Creates** a persistent Chroma vector store
3. **Builds** a RAG query engine with GPT-4
4. **Queries** the documentation with natural language

## Prerequisites

```bash
# Install dependencies
pip install langchain langchain-community langchain-openai chromadb openai

# Set API key
export OPENAI_API_KEY=sk-...
```

## Generate Documents

First, generate LangChain documents using Skill Seekers:

```bash
# Option 1: Use preset config (e.g., React)
skill-seekers scrape --config configs/react.json
skill-seekers package output/react --target langchain

# Option 2: From GitHub repo
skill-seekers github --repo facebook/react --name react
skill-seekers package output/react --target langchain

# Output: output/react-langchain.json
```

## Run the Example

```bash
cd examples/langchain-rag-pipeline

# Run the quickstart script
python quickstart.py
```

## What You'll See

1. **Documents loaded** from JSON file
2. **Vector store created** with embeddings
3. **Example queries** demonstrating RAG
4. **Interactive mode** to ask your own questions

## Example Output

```
============================================================
LANGCHAIN RAG PIPELINE QUICKSTART
============================================================

Step 1: Loading documents...
✅ Loaded 150 documents
   Categories: {'overview', 'hooks', 'components', 'api'}

Step 2: Creating vector store...
✅ Vector store created at: ./chroma_db
   Documents indexed: 150

Step 3: Creating QA chain...
✅ QA chain created

Step 4: Running example queries...

============================================================
QUERY: How do I use React hooks?
============================================================

ANSWER:
React hooks are functions that let you use state and lifecycle features
in functional components. The most common hooks are useState and useEffect...

SOURCES:
  1. hooks (hooks.md)
     Preview: # React Hooks\n\nHooks are a way to reuse stateful logic...

  2. api (api_reference.md)
     Preview: ## useState\n\nReturns a stateful value and a function...
```

## Files in This Example

- `quickstart.py` - Complete working example
- `README.md` - This file
- `requirements.txt` - Python dependencies

## Next Steps

1. **Customize** - Modify the example for your use case
2. **Experiment** - Try different vector stores (FAISS, Pinecone)
3. **Extend** - Add conversational memory, filters, hybrid search
4. **Deploy** - Build a production RAG application

## Troubleshooting

**"Documents not found"**
- Make sure you've generated documents first
- Check the path in `quickstart.py` matches your output location

**"OpenAI API key not found"**
- Set environment variable: `export OPENAI_API_KEY=sk-...`

**"Module not found"**
- Install dependencies: `pip install -r requirements.txt`

## Related Examples

- [LlamaIndex RAG Pipeline](../llama-index-query-engine/)
- [Pinecone Integration](../pinecone-upsert/)

---

**Need help?** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
