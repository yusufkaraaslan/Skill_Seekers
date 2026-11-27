# OpenAI ChatGPT Integration Guide

Complete guide for creating and deploying skills to OpenAI ChatGPT using Skill Seekers.

## Overview

Skill Seekers packages documentation into OpenAI-compatible formats optimized for:
- **Responses API** for answering questions using your skill
- **Vector Store + File Search** for accurate retrieval
- **GPT-4o** for enhancement and responses

## Setup

### 1. Install OpenAI Support

```bash
# Install with OpenAI dependencies
pip install "skill-seekers[openai]"

# Verify installation
pip list | grep openai
```

### 2. Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Navigate to **API keys** section
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-` or `sk-`)

### 3. Configure API Key

```bash
# Set as environment variable (recommended)
export OPENAI_API_KEY=sk-proj-...

# Or pass directly to commands
skill-seekers upload react-openai.zip --target openai --api-key sk-proj-...
```

## Complete Workflow

### Step 1: Scrape Documentation

```bash
# Use any config (scraping is platform-agnostic)
skill-seekers create --config configs/react.json

# Or use a unified config for multi-source
skill-seekers create --config configs/react_unified.json
```

**Result:** `output/react/` skill directory with references

### Step 2: Enhance with GPT-4o (Optional but Recommended)

```bash
# Enhance SKILL.md using GPT-4o
skill-seekers enhance output/react/ --target openai

# With API key specified
skill-seekers enhance output/react/ --target openai --api-key sk-proj-...
```

**What it does:**
- Analyzes all reference documentation
- Extracts 5-10 best code examples
- Creates comprehensive assistant instructions
- Adds response guidelines and search strategy
- Formats as plain text (no YAML frontmatter)

**Time:** 20-40 seconds
**Cost:** ~$0.15-0.30 (using GPT-4o)
**Quality boost:** 3/10 → 9/10

### Step 3: Package for OpenAI

```bash
# Create ZIP package for OpenAI file search
skill-seekers package output/react/ --target openai

# Result: react-openai.zip
```

**Package structure:**
```
react-openai.zip/
├── assistant_instructions.txt  # Main instructions for Assistant
├── vector_store_files/        # Files for Vector Store + file_search
│   ├── getting_started.md
│   ├── hooks.md
│   ├── components.md
│   └── ...
└── openai_metadata.json       # Platform metadata
```

### Step 4: Upload the knowledge base

```bash
skill-seekers upload react-openai.zip --target openai
```

The command uploads the instructions as a file, creates a vector store and waits for each reference to finish indexing. The vector store metadata records the instructions file ID and the model from the package. Keep the printed vector store ID (`vs_...`). Existing Skill Seekers OpenAI ZIPs use the same command.

### Step 5: Ask a question using the Responses API

```python
from openai import OpenAI

client = OpenAI()
store = client.vector_stores.retrieve("vs_...")  # ID printed by upload
instructions = client.files.content(store.metadata["instructions_file_id"]).text
tools = [{"type": "file_search", "vector_store_ids": [store.id]}] if store.file_counts.completed else []

response = client.responses.create(
    model=store.metadata["model"],
    instructions=instructions,
    tools=tools,
    input="Explain a concept from the documentation and cite the source.",
)
print(response.output_text)
```

You can reuse the store from another process in the same OpenAI project. Instructions-only packages also work. In that case, pass an empty tools list as shown above. For streaming, pass `stream=True` to `responses.create` and consume the response events. [OpenAI file search guide](https://developers.openai.com/api/docs/guides/tools-file-search)

### Programmatic upload

```python
import os
from pathlib import Path
from skill_seekers.cli.adaptors import get_adaptor

adaptor = get_adaptor("openai")
package = adaptor.package(Path("output/react"), Path("react-openai.zip"))
result = adaptor.upload(package, os.environ["OPENAI_API_KEY"])
if not result["success"]:
    raise RuntimeError(result["message"])
print(result["vector_store_id"], result["instructions_file_id"])
```

The `skill_id` field now contains the same vector store ID as `vector_store_id`. Update consumers that previously passed an `asst_...` ID to a thread or run. Re-upload the original ZIP to publish a new knowledge base. On a successful upload, the store, references and instructions file remain in your project until you delete them. To retire a store, list its file IDs and read its instructions file ID before deleting the store and those files.

## Troubleshooting

### Issue: `openai not installed`

**Solution:**
```bash
pip install "skill-seekers[openai]"
```

### Issue: `Invalid API key format`

**Error:** API key doesn't start with `sk-`

**Solution:**
- Get new key from [OpenAI Platform](https://platform.openai.com/api-keys)
- Verify you're using API key, not organization ID

### Issue: `Not a ZIP file`

**Error:** Wrong package format

**Solution:**
```bash
# Use --target openai for ZIP format
skill-seekers package output/react/ --target openai

# NOT:
skill-seekers package output/react/ --target gemini  # Creates .tar.gz
```

### Issue: Upload or indexing failed

Check the API error for file size, permissions or rate limits. Skill Seekers attempts to delete every resource ID it received for the failed upload. If cleanup also fails, the error lists the IDs that still need attention. The original ZIP is available for retry.

### Issue: Enhancement fails

**Solution:**
```bash
# Check API quota and billing
# Visit: https://platform.openai.com/account/billing

# Try with smaller skill
skill-seekers enhance output/react/ --target openai

# Use without enhancement
skill-seekers package output/react/ --target openai
# (Skip enhancement step)
```

### Issue: file_search not working

**Symptoms:** Assistant doesn't reference documentation

**Solution:**
- Verify Vector Store has files
- Check the `file_search` tool and vector store ID in your Responses request
- Test with explicit instructions: "Search the knowledge files for information about hooks"

## Best Practices

### 1. Write Clear Assistant Instructions

Focus on:
- Role definition
- Knowledge base description
- Response guidelines
- Search strategy

### 2. Organize Vector Store Files

- Keep files under 512KB each
- Use clear, descriptive filenames
- Structure content with headings
- Include code examples

### 3. Test Assistant Behavior

Test with varied questions:
```
1. Simple facts: "What is React?"
2. How-to questions: "How do I create a component?"
3. Best practices: "What's the best way to manage state?"
4. Troubleshooting: "Why isn't my hook working?"
```

### 4. Monitor Token Usage

```python
# Track tokens in API responses
print(response.usage.input_tokens, response.usage.output_tokens)
```

### 5. Update Regularly

```bash
# Re-scrape updated documentation
skill-seekers create --config configs/react.json

# Re-enhance and upload (creates a new vector store)
skill-seekers enhance output/react/ --target openai
skill-seekers package output/react/ --target openai
skill-seekers upload react-openai.zip --target openai
```

## Cost Estimation

**GPT-4o pricing (as of 2024):**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens

**Typical skill enhancement:**
- Input: ~50K-200K tokens (docs)
- Output: ~5K-10K tokens (enhanced instructions)
- Cost: $0.15-0.30 per skill

**Vector Store:**
- $0.10 per GB per day (storage)
- Typical skill: < 100MB = ~$0.01/day

**API usage:**
- Varies by question volume
- ~$0.01-0.05 per conversation

## Next Steps

1. ✅ Install OpenAI support: `pip install "skill-seekers[openai]"`
2. ✅ Get API key from OpenAI Platform
3. ✅ Scrape your documentation
4. ✅ Enhance with GPT-4o
5. ✅ Package for OpenAI
6. ✅ Upload and save the vector store ID
7. ✅ Test a Responses API request

## Resources

- [OpenAI Platform](https://platform.openai.com/)
- [Responses API file search](https://developers.openai.com/api/docs/guides/tools-file-search)
- [OpenAI Pricing](https://openai.com/pricing)
- [Multi-LLM Support Guide](MULTI_LLM_SUPPORT.md)

## Feedback

Found an issue or have suggestions? [Open an issue](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
