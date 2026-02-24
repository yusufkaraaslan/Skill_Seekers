# Packaging Guide

> **Skill Seekers v3.1.0**  
> **Export skills to AI platforms and vector databases**

---

## Overview

Packaging converts your skill directory into a platform-specific format:

```
output/my-skill/ ──▶ Packager ──▶ output/my-skill-{platform}.{format}
    ↓                                ↓
(SKILL.md +        Platform-specific  (ZIP, tar.gz,
 references)        formatting        directories,
                                     FAISS index)
```

---

## Supported Platforms

| Platform | Format | Extension | Best For |
|----------|--------|-----------|----------|
| **Claude AI** | ZIP + YAML | `.zip` | Claude Code, Claude API |
| **Google Gemini** | tar.gz | `.tar.gz` | Gemini skills |
| **OpenAI ChatGPT** | ZIP + Vector | `.zip` | Custom GPTs |
| **LangChain** | Documents | directory | RAG pipelines |
| **LlamaIndex** | TextNodes | directory | Query engines |
| **Haystack** | Documents | directory | Enterprise RAG |
| **Pinecone** | Markdown | `.zip` | Vector upsert |
| **ChromaDB** | Collection | `.zip` | Local vector DB |
| **Weaviate** | Objects | `.zip` | Vector database |
| **Qdrant** | Points | `.zip` | Vector database |
| **FAISS** | Index | `.faiss` | Local similarity |
| **Markdown** | ZIP | `.zip` | Universal export |
| **Cursor** | .cursorrules | file | IDE AI context |
| **Windsurf** | .windsurfrules | file | IDE AI context |
| **Cline** | .clinerules | file | VS Code AI |

---

## Basic Packaging

### Package for Claude (Default)

```bash
# Default packaging
skill-seekers package output/my-skill/

# Explicit target
skill-seekers package output/my-skill/ --target claude

# Output: output/my-skill-claude.zip
```

### Package for Other Platforms

```bash
# Google Gemini
skill-seekers package output/my-skill/ --target gemini
# Output: output/my-skill-gemini.tar.gz

# OpenAI
skill-seekers package output/my-skill/ --target openai
# Output: output/my-skill-openai.zip

# LangChain
skill-seekers package output/my-skill/ --target langchain
# Output: output/my-skill-langchain/ directory

# ChromaDB
skill-seekers package output/my-skill/ --target chroma
# Output: output/my-skill-chroma.zip
```

---

## Multi-Platform Packaging

### Package for All Platforms

```bash
# Create skill once
skill-seekers create <source>

# Package for multiple platforms
for platform in claude gemini openai langchain; do
  echo "Packaging for $platform..."
  skill-seekers package output/my-skill/ --target $platform
done

# Results:
# output/my-skill-claude.zip
# output/my-skill-gemini.tar.gz
# output/my-skill-openai.zip
# output/my-skill-langchain/
```

### Batch Packaging Script

```bash
#!/bin/bash
SKILL_DIR="output/my-skill"
PLATFORMS="claude gemini openai langchain llama-index chroma"

for platform in $PLATFORMS; do
  echo "▶️ Packaging for $platform..."
  skill-seekers package "$SKILL_DIR" --target "$platform"
  
  if [ $? -eq 0 ]; then
    echo "✅ $platform done"
  else
    echo "❌ $platform failed"
 fi
done

echo "🎉 All platforms packaged!"
```

---

## Packaging Options

### Skip Quality Check

```bash
# Skip validation (faster)
skill-seekers package output/my-skill/ --skip-quality-check
```

### Don't Open Output Folder

```bash
# Prevent opening folder after packaging
skill-seekers package output/my-skill/ --no-open
```

### Auto-Upload After Packaging

```bash
# Package and upload
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers package output/my-skill/ --target claude --upload
```

---

## Streaming Mode

For very large skills, use streaming to reduce memory usage:

```bash
# Enable streaming
skill-seekers package output/large-skill/ --streaming

# Custom chunk size
skill-seekers package output/large-skill/ \
  --streaming \
  --streaming-chunk-chars 2000 \
  --streaming-overlap-chars 100
```

**When to use:**
- Skills > 500 pages
- Limited RAM (< 8GB)
- Batch processing many skills

---

## RAG Chunking

Optimize for Retrieval-Augmented Generation:

```bash
# Enable semantic chunking
skill-seekers package output/my-skill/ \
  --target langchain \
  --chunk-for-rag \
  --chunk-tokens 512

# Custom chunk size
skill-seekers package output/my-skill/ \
  --target chroma \
  --chunk-tokens 256 \
  --chunk-overlap-tokens 50
```

**Chunking Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--chunk-for-rag` | auto | Enable chunking |
| `--chunk-tokens` | 512 | Tokens per chunk |
| `--chunk-overlap-tokens` | 50 | Overlap between chunks (tokens) |
| `--no-preserve-code` | - | Allow splitting code blocks |

---

## Platform-Specific Details

### Claude AI

```bash
skill-seekers package output/my-skill/ --target claude
```

**Upload:**
```bash
# Auto-upload
skill-seekers package output/my-skill/ --target claude --upload

# Manual upload
skill-seekers upload output/my-skill-claude.zip --target claude
```

**Format:**
- ZIP archive
- Contains SKILL.md + references/
- Includes YAML manifest

---

### Google Gemini

```bash
skill-seekers package output/my-skill/ --target gemini
```

**Upload:**
```bash
export GOOGLE_API_KEY=AIza...
skill-seekers upload output/my-skill-gemini.tar.gz --target gemini
```

**Format:**
- tar.gz archive
- Optimized for Gemini's format

---

### OpenAI ChatGPT

```bash
skill-seekers package output/my-skill/ --target openai
```

**Upload:**
```bash
export OPENAI_API_KEY=sk-...
skill-seekers upload output/my-skill-openai.zip --target openai
```

**Format:**
- ZIP with vector embeddings
- Ready for Assistants API

---

### LangChain

```bash
skill-seekers package output/my-skill/ --target langchain
```

**Usage:**
```python
from langchain.document_loaders import DirectoryLoader

loader = DirectoryLoader("output/my-skill-langchain/")
docs = loader.load()

# Use in RAG pipeline
```

**Format:**
- Directory of Document objects
- JSON metadata

---

### ChromaDB

```bash
skill-seekers package output/my-skill/ --target chroma
```

**Upload:**
```bash
# Local ChromaDB
skill-seekers upload output/my-skill-chroma.zip --target chroma

# With custom URL
skill-seekers upload output/my-skill-chroma.zip \
  --target chroma \
  --chroma-url http://localhost:8000
```

**Usage:**
```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_collection("my-skill")
```

---

### Weaviate

```bash
skill-seekers package output/my-skill/ --target weaviate
```

**Upload:**
```bash
# Local Weaviate
skill-seekers upload output/my-skill-weaviate.zip --target weaviate

# Weaviate Cloud
skill-seekers upload output/my-skill-weaviate.zip \
  --target weaviate \
  --use-cloud \
  --cluster-url https://xxx.weaviate.network
```

---

### Cursor IDE

```bash
# Package (actually creates .cursorrules file)
skill-seekers package output/my-skill/ --target cursor

# Or install directly
skill-seekers install-agent output/my-skill/ --agent cursor
```

**Result:** `.cursorrules` file in your project root.

---

### Windsurf IDE

```bash
skill-seekers install-agent output/my-skill/ --agent windsurf
```

**Result:** `.windsurfrules` file in your project root.

---

## Quality Check

Before packaging, skills are validated:

```bash
# Check quality
skill-seekers quality output/my-skill/

# Detailed report
skill-seekers quality output/my-skill/ --report

# Set minimum threshold
skill-seekers quality output/my-skill/ --threshold 7.0
```

**Quality Metrics:**
- SKILL.md completeness
- Code example coverage
- Navigation structure
- Reference file organization

---

## Output Structure

### After Packaging

```
output/
├── my-skill/                    # Source skill
│   ├── SKILL.md
│   └── references/
│
├── my-skill-claude.zip          # Claude package
├── my-skill-gemini.tar.gz       # Gemini package
├── my-skill-openai.zip          # OpenAI package
├── my-skill-langchain/          # LangChain directory
├── my-skill-chroma.zip          # ChromaDB package
└── my-skill-weaviate.zip        # Weaviate package
```

---

## Troubleshooting

### "Package validation failed"

**Problem:** SKILL.md is missing or malformed

**Solution:**
```bash
# Check skill structure
ls output/my-skill/

# Rebuild if needed
skill-seekers create --config my-config --skip-scrape

# Or recreate
skill-seekers create <source>
```

### "Target platform not supported"

**Problem:** Typo in target name

**Solution:**
```bash
# Check available targets
skill-seekers package --help

# Common targets: claude, gemini, openai, langchain, chroma, weaviate
```

### "Upload failed"

**Problem:** Missing API key

**Solution:**
```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...

# Try again
skill-seekers upload output/my-skill-claude.zip --target claude
```

### "Out of memory"

**Problem:** Skill too large for memory

**Solution:**
```bash
# Use streaming mode
skill-seekers package output/my-skill/ --streaming

# Smaller chunks
skill-seekers package output/my-skill/ --streaming --streaming-chunk-chars 1000
```

---

## Best Practices

### 1. Package Once, Use Everywhere

```bash
# Create once
skill-seekers create <source>

# Package for all needed platforms
for platform in claude gemini langchain; do
  skill-seekers package output/my-skill/ --target $platform
done
```

### 2. Check Quality Before Packaging

```bash
# Validate first
skill-seekers quality output/my-skill/ --threshold 6.0

# Then package
skill-seekers package output/my-skill/
```

### 3. Use Streaming for Large Skills

```bash
# Automatically detected, but can force
skill-seekers package output/large-skill/ --streaming
```

### 4. Keep Original Skill Directory

Don't delete `output/my-skill/` after packaging - you might want to:
- Re-package for other platforms
- Apply different workflows
- Update and re-enhance

---

## Next Steps

- [Workflows Guide](05-workflows.md) - Apply workflows before packaging
- [MCP Reference](../reference/MCP_REFERENCE.md) - Package via MCP
- [Vector DB Integrations](../integrations/) - Platform-specific guides
