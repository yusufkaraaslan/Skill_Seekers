# Using Skill Seekers with LangChain

**Last Updated:** February 5, 2026
**Status:** Production Ready
**Difficulty:** Easy ⭐

---

## 🎯 The Problem

Building RAG (Retrieval-Augmented Generation) applications with LangChain requires high-quality, structured documentation for your vector stores. Manually scraping and chunking documentation is:

- **Time-Consuming** - Hours spent scraping docs and formatting them
- **Error-Prone** - Inconsistent chunking, missing metadata, broken references
- **Not Maintainable** - Documentation updates require re-scraping everything

**Example:**
> "When building a RAG chatbot for React documentation, you need to scrape 500+ pages, chunk them properly, add metadata, and load into a vector store. This typically takes 4-6 hours of manual work."

---

## ✨ The Solution

Use Skill Seekers as **essential preprocessing** before LangChain:

1. **Generate LangChain Documents** from any documentation source
2. **Pre-chunked and structured** with proper metadata
3. **Ready for vector stores** (Chroma, Pinecone, FAISS, etc.)
4. **One command** - scrape, chunk, format in minutes

**Result:**
Skill Seekers outputs JSON files with LangChain Document format, ready to load directly into your RAG pipeline.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- LangChain installed: `pip install langchain langchain-community`
- OpenAI API key (for embeddings): `export OPENAI_API_KEY=sk-...`

### Installation

```bash
# Install Skill Seekers
pip install skill-seekers

# Verify installation
skill-seekers --version
```

### Generate LangChain Documents

```bash
# Example: React framework documentation
skill-seekers scrape --config configs/react.json

# Package as LangChain Documents
skill-seekers package output/react --target langchain

# Output: output/react-langchain.json
```

### Load into LangChain

```python
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import json

# Load documents
with open("output/react-langchain.json") as f:
    docs_data = json.load(f)

# Convert to LangChain Documents
documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in docs_data
]

print(f"Loaded {len(documents)} documents")

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(documents, embeddings)

# Query
results = vectorstore.similarity_search("How do I use React hooks?", k=3)
for doc in results:
    print(f"\n{doc.metadata['category']}: {doc.page_content[:200]}...")
```

---

## 📖 Detailed Setup Guide

### Step 1: Choose Your Documentation Source

**Option A: Use Preset Config (Fastest)**
```bash
# Available presets: react, vue, django, fastapi, etc.
skill-seekers scrape --config configs/react.json
```

**Option B: From GitHub Repository**
```bash
# Scrape from GitHub repo (includes code + docs)
skill-seekers github --repo facebook/react --name react-skill
```

**Option C: Custom Documentation**
```bash
# Create custom config for your docs
skill-seekers scrape --config configs/my-docs.json
```

### Step 2: Generate LangChain Format

```bash
# Convert to LangChain Documents
skill-seekers package output/react --target langchain

# Output structure:
# output/react-langchain.json
# [
#   {
#     "page_content": "...",
#     "metadata": {
#       "source": "react",
#       "category": "hooks",
#       "file": "hooks.md",
#       "type": "reference"
#     }
#   }
# ]
```

**What You Get:**
- ✅ Pre-chunked documents (semantic boundaries preserved)
- ✅ Rich metadata (source, category, file, type)
- ✅ Clean markdown (code blocks preserved)
- ✅ Ready for embeddings

### Step 3: Load into Vector Store

**Option 1: Chroma (Local, Persistent)**
```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import json

# Load documents
with open("output/react-langchain.json") as f:
    docs_data = json.load(f)

documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in docs_data
]

# Create persistent Chroma store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents,
    embeddings,
    persist_directory="./chroma_db"
)

print(f"✅ {len(documents)} documents loaded into Chroma")
```

**Option 2: FAISS (Fast, In-Memory)**
```python
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import json

with open("output/react-langchain.json") as f:
    docs_data = json.load(f)

documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in docs_data
]

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

# Save for later use
vectorstore.save_local("faiss_index")

print(f"✅ {len(documents)} documents loaded into FAISS")
```

**Option 3: Pinecone (Cloud, Scalable)**
```python
from langchain.vectorstores import Pinecone as LangChainPinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import json
import pinecone

# Initialize Pinecone
pinecone.init(api_key="your-api-key", environment="us-west1-gcp")
index_name = "react-docs"

if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=1536)

# Load documents
with open("output/react-langchain.json") as f:
    docs_data = json.load(f)

documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in docs_data
]

# Upload to Pinecone
embeddings = OpenAIEmbeddings()
vectorstore = LangChainPinecone.from_documents(
    documents,
    embeddings,
    index_name=index_name
)

print(f"✅ {len(documents)} documents uploaded to Pinecone")
```

### Step 4: Build RAG Chain

```python
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# Create retriever from vector store
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# Create RAG chain
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# Query
query = "How do I use React hooks?"
result = qa_chain({"query": query})

print(f"Answer: {result['result']}")
print(f"\nSources:")
for doc in result['source_documents']:
    print(f"  - {doc.metadata['category']}: {doc.metadata['file']}")
```

---

## 🎨 Advanced Usage

### Filter by Metadata

```python
# Search only in specific categories
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 5,
        "filter": {"category": "hooks"}
    }
)
```

### Custom Metadata Enrichment

```python
# Add custom metadata before loading
for doc_data in docs_data:
    doc_data["metadata"]["indexed_at"] = datetime.now().isoformat()
    doc_data["metadata"]["version"] = "18.2.0"

documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in docs_data
]
```

### Multi-Source Documentation

```python
# Combine multiple documentation sources
sources = ["react", "vue", "angular"]
all_documents = []

for source in sources:
    with open(f"output/{source}-langchain.json") as f:
        docs_data = json.load(f)

    documents = [
        Document(page_content=doc["page_content"], metadata=doc["metadata"])
        for doc in docs_data
    ]
    all_documents.extend(documents)

# Create unified vector store
vectorstore = Chroma.from_documents(all_documents, embeddings)
print(f"✅ Loaded {len(all_documents)} documents from {len(sources)} sources")
```

---

## 💡 Best Practices

### 1. Start with Presets
Use tested configurations to avoid scraping issues:
```bash
ls configs/  # See available presets
skill-seekers scrape --config configs/django.json
```

### 2. Test Queries Before Full Pipeline
```python
# Quick test with similarity search
results = vectorstore.similarity_search("your query", k=3)
for doc in results:
    print(f"{doc.metadata['category']}: {doc.page_content[:100]}")
```

### 3. Use Persistent Storage
```python
# Save Chroma DB for reuse
vectorstore = Chroma.from_documents(
    documents,
    embeddings,
    persist_directory="./chroma_db"  # ← Persists to disk
)

# Later: load existing DB
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
```

### 4. Monitor Token Usage
```python
# Check document sizes before embedding
total_tokens = sum(len(doc["page_content"].split()) for doc in docs_data)
print(f"Estimated tokens: {total_tokens * 1.3:.0f}")  # Rough estimate
```

---

## 🔥 Real-World Example

### Building a React Documentation Chatbot

**Step 1: Generate Documents**
```bash
# Scrape React docs
skill-seekers scrape --config configs/react.json

# Convert to LangChain format
skill-seekers package output/react --target langchain
```

**Step 2: Create Vector Store**
```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import json

# Load documents
with open("output/react-langchain.json") as f:
    docs_data = json.load(f)

documents = [
    Document(page_content=doc["page_content"], metadata=doc["metadata"])
    for doc in docs_data
]

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents,
    embeddings,
    persist_directory="./react_chroma"
)

print(f"✅ Loaded {len(documents)} React documentation chunks")
```

**Step 3: Build Conversational RAG**
```python
# Create conversational chain with memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model_name="gpt-4", temperature=0),
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    memory=memory,
    return_source_documents=True
)

# Chat loop
while True:
    query = input("\nYou: ")
    if query.lower() in ['quit', 'exit']:
        break

    result = qa_chain({"question": query})
    print(f"\nAssistant: {result['answer']}")

    print(f"\nSources:")
    for doc in result['source_documents']:
        print(f"  - {doc.metadata['category']}: {doc.metadata['file']}")
```

**Result:**
- Complete React documentation in 100-200 documents
- Sub-second query responses
- Source attribution for every answer
- Conversational context maintained

---

## 🐛 Troubleshooting

### Issue: Too Many Documents
**Solution:** Filter by category or split into multiple indexes
```python
# Filter specific categories
hooks_docs = [
    doc for doc in docs_data
    if doc["metadata"]["category"] == "hooks"
]
```

### Issue: Large Documents
**Solution:** Documents are already chunked, but you can re-chunk if needed
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

split_documents = text_splitter.split_documents(documents)
```

### Issue: Missing Dependencies
**Solution:** Install LangChain components
```bash
pip install langchain langchain-community langchain-openai
pip install chromadb  # For Chroma
pip install faiss-cpu  # For FAISS
```

---

## 📊 Before vs After Comparison

| Aspect | Manual Process | With Skill Seekers |
|--------|---------------|-------------------|
| **Time to Setup** | 4-6 hours | 5 minutes |
| **Documentation Coverage** | 50-70% (cherry-picked) | 95-100% (comprehensive) |
| **Metadata Quality** | Manual, inconsistent | Automatic, structured |
| **Maintenance** | Re-scrape everything | Re-run one command |
| **Code Examples** | Often missing | Preserved with syntax |
| **Updates** | Hours of work | 5 minutes |

---

## 🤝 Community & Support

- **Questions:** [GitHub Discussions](https://github.com/yusufkaraaslan/Skill_Seekers/discussions)
- **Issues:** [GitHub Issues](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
- **Documentation:** [https://skillseekersweb.com/](https://skillseekersweb.com/)
- **Twitter:** [@_yUSyUS_](https://x.com/_yUSyUS_)

---

## 📚 Related Guides

- [LlamaIndex Integration](./LLAMA_INDEX.md)
- [Pinecone Integration](./PINECONE.md)
- [RAG Pipelines Overview](./RAG_PIPELINES.md)

---

## 📖 Next Steps

1. **Try the Quick Start** above
2. **Explore other vector stores** (Pinecone, Weaviate, Qdrant)
3. **Build your RAG application** with production-ready docs
4. **Share your experience** - we'd love to hear how you use it!

---

**Last Updated:** February 5, 2026
**Tested With:** LangChain v0.1.0+, OpenAI Embeddings
**Skill Seekers Version:** v2.9.0+
