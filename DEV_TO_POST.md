# Skill Seekers v3.0.0: The Universal Documentation Preprocessor for AI Systems

![Skill Seekers v3.0.0 Banner](https://skillseekersweb.com/images/blog/v3-release-banner.png)

> 🚀 **One command converts any documentation into structured knowledge for any AI system.**

## TL;DR

- 🎯 **16 output formats** (was 4 in v2.x)
- 🛠️ **26 MCP tools** for AI agents
- ✅ **1,852 tests** passing
- ☁️ **Cloud storage** support (S3, GCS, Azure)
- 🔄 **CI/CD ready** with GitHub Action

```bash
pip install skill-seekers
skill-seekers scrape --config react.json
```

---

## The Problem We're All Solving

Raise your hand if you've written this code before:

```python
# The custom scraper we all write
import requests
from bs4 import BeautifulSoup

def scrape_docs(url):
    # Handle pagination
    # Extract clean text
    # Preserve code blocks
    # Add metadata
    # Chunk properly
    # Format for vector DB
    # ... 200 lines later
    pass
```

**Every AI project needs documentation preprocessing.**

- **RAG pipelines**: "Scrape these docs, chunk them, embed them..."
- **AI coding tools**: "I wish Cursor knew this framework..."
- **Claude skills**: "Convert this documentation into a skill"

We all rebuild the same infrastructure. **Stop rebuilding. Start using.**

---

## Meet Skill Seekers v3.0.0

One command → Any format → Production-ready

### For RAG Pipelines

```bash
# LangChain Documents
skill-seekers scrape --format langchain --config react.json

# LlamaIndex TextNodes
skill-seekers scrape --format llama-index --config vue.json

# Pinecone-ready markdown
skill-seekers scrape --target markdown --config django.json
```

**Then in Python:**

```python
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor('langchain')
documents = adaptor.load_documents("output/react/")

# Now use with any vector store
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma.from_documents(
    documents,
    OpenAIEmbeddings()
)
```

### For AI Coding Assistants

```bash
# Give Cursor framework knowledge
skill-seekers scrape --target claude --config react.json
cp output/react-claude/.cursorrules ./
```

**Result:** Cursor now knows React hooks, patterns, and best practices from the actual documentation.

### For Claude AI

```bash
# Complete workflow: fetch → scrape → enhance → package → upload
skill-seekers install --config react.json
```

---

## What's New in v3.0.0

### 16 Platform Adaptors

| Category | Platforms | Use Case |
|----------|-----------|----------|
| **RAG/Vectors** | LangChain, LlamaIndex, Chroma, FAISS, Haystack, Qdrant, Weaviate | Build production RAG pipelines |
| **AI Platforms** | Claude, Gemini, OpenAI | Create AI skills |
| **AI Coding** | Cursor, Windsurf, Cline, Continue.dev | Framework-specific AI assistance |
| **Generic** | Markdown | Any vector database |

### 26 MCP Tools

Your AI agent can now prepare its own knowledge:

```
🔧 Config: generate_config, list_configs, validate_config
🌐 Scraping: scrape_docs, scrape_github, scrape_pdf, scrape_codebase
📦 Packaging: package_skill, upload_skill, enhance_skill, install_skill
☁️ Cloud: upload to S3, GCS, Azure
🔗 Sources: fetch_config, add_config_source
✂️ Splitting: split_config, generate_router
🗄️ Vector DBs: export_to_weaviate, export_to_chroma, export_to_faiss, export_to_qdrant
```

### Cloud Storage

```bash
# Upload to AWS S3
skill-seekers cloud upload output/ --provider s3 --bucket my-bucket

# Or Google Cloud Storage
skill-seekers cloud upload output/ --provider gcs --bucket my-bucket

# Or Azure Blob Storage
skill-seekers cloud upload output/ --provider azure --container my-container
```

### CI/CD Ready

```yaml
# .github/workflows/update-docs.yml
- uses: skill-seekers/action@v1
  with:
    config: configs/react.json
    format: langchain
```

Auto-update your AI knowledge when documentation changes.

---

## Why This Matters

### Before Skill Seekers

```
Week 1: Build custom scraper
Week 2: Handle edge cases
Week 3: Format for your tool
Week 4: Maintain and debug
```

### After Skill Seekers

```
15 minutes: Install and run
Done: Production-ready output
```

---

## Real Example: React + LangChain + Chroma

```bash
# 1. Install
pip install skill-seekers langchain-chroma langchain-openai

# 2. Scrape React docs
skill-seekers scrape --format langchain --config configs/react.json

# 3. Create RAG pipeline
```

```python
from skill_seekers.cli.adaptors import get_adaptor
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

# Load documents
adaptor = get_adaptor('langchain')
documents = adaptor.load_documents("output/react/")

# Create vector store
vectorstore = Chroma.from_documents(
    documents,
    OpenAIEmbeddings()
)

# Query
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(),
    retriever=vectorstore.as_retriever()
)

result = qa_chain.invoke({"query": "What are React Hooks?"})
print(result["result"])
```

**That's it.** 15 minutes from docs to working RAG pipeline.

---

## Production Ready

- ✅ **1,852 tests** across 100 test files
- ✅ **58,512 lines** of Python code
- ✅ **CI/CD** on every commit
- ✅ **Docker** images available
- ✅ **Multi-platform** (Ubuntu, macOS)
- ✅ **Python 3.10-3.13** tested

---

## Get Started

```bash
# Install
pip install skill-seekers

# Try an example
skill-seekers scrape --config configs/react.json

# Or create your own config
skill-seekers config --wizard
```

---

## Links

- 🌐 **Website:** https://skillseekersweb.com
- 💻 **GitHub:** https://github.com/yusufkaraaslan/Skill_Seekers
- 📖 **Documentation:** https://skillseekersweb.com/docs
- 📦 **PyPI:** https://pypi.org/project/skill-seekers/

---

## What's Next?

- ⭐ Star us on GitHub if you hate writing scrapers
- 🐛 Report issues (1,852 tests but bugs happen)
- 💡 Suggest features (we're building in public)
- 🚀 Share your use case

---

*Skill Seekers v3.0.0 was released on February 10, 2026. This is our biggest release yet - transforming from a Claude skill generator into a universal documentation preprocessor for the entire AI ecosystem.*

---

## Tags

#python #ai #machinelearning #rag #langchain #llamaindex #opensource #developer_tools #cursor #claude #docker #cloud
