# OpenAI ChatGPT Integration Guide

Complete guide for creating and deploying skills to OpenAI ChatGPT using Skill Seekers.

## Overview

Skill Seekers packages documentation into OpenAI-compatible formats optimized for:
- **Assistants API** for custom AI assistants
- **Vector Store + File Search** for accurate retrieval
- **GPT-4o** for enhancement and responses

## Setup

### 1. Install OpenAI Support

```bash
# Install with OpenAI dependencies
pip install skill-seekers[openai]

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
skill-seekers upload --target openai --api-key sk-proj-...
```

## Complete Workflow

### Step 1: Scrape Documentation

```bash
# Use any config (scraping is platform-agnostic)
skill-seekers scrape --config configs/react.json

# Or use a unified config for multi-source
skill-seekers unified --config configs/react_unified.json
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
# Create ZIP package for OpenAI Assistants
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

### Step 4: Upload to OpenAI (Creates Assistant)

```bash
# Upload and create Assistant with Vector Store
skill-seekers upload react-openai.zip --target openai

# With API key
skill-seekers upload react-openai.zip --target openai --api-key sk-proj-...
```

**What it does:**
1. Creates Vector Store for documentation
2. Uploads reference files to Vector Store
3. Creates Assistant with file_search tool
4. Links Vector Store to Assistant

**Output:**
```
✅ Upload successful!
Assistant ID: asst_abc123xyz
URL: https://platform.openai.com/assistants/asst_abc123xyz
Message: Assistant created with 15 knowledge files
```

### Step 5: Use Your Assistant

Access your assistant in the OpenAI Platform:

1. Go to [OpenAI Platform](https://platform.openai.com/assistants)
2. Find your assistant in the list
3. Test in Playground or use via API

## What Makes OpenAI Different?

### Format: Assistant Instructions (Plain Text)

**Claude format:**
```markdown
---
name: react
---

# React Documentation
...
```

**OpenAI format:**
```text
You are an expert assistant for React.

Your Knowledge Base:
- Getting started guide
- React hooks reference
- Component API

When users ask questions about React:
1. Search the knowledge files
2. Provide code examples
...
```

Plain text instructions optimized for Assistant API.

### Architecture: Assistant + Vector Store

OpenAI uses a two-part system:
1. **Assistant** - The AI agent with instructions and tools
2. **Vector Store** - Embedded documentation for semantic search

### Tool: file_search

The Assistant uses the `file_search` tool to:
- Semantically search documentation
- Find relevant code examples
- Provide accurate, source-based answers

## Using Your OpenAI Assistant

### Option 1: OpenAI Playground (Web UI)

1. Go to [OpenAI Platform](https://platform.openai.com/assistants)
2. Select your assistant
3. Click "Test in Playground"
4. Ask questions about your documentation

### Option 2: Assistants API (Python)

```python
from openai import OpenAI

# Initialize client
client = OpenAI(api_key='sk-proj-...')

# Create thread
thread = client.beta.threads.create()

# Send message
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="How do I use React hooks?"
)

# Run assistant
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id='asst_abc123xyz'  # Your assistant ID
)

# Wait for completion
while run.status != 'completed':
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

# Get response
messages = client.beta.threads.messages.list(thread_id=thread.id)
print(messages.data[0].content[0].text.value)
```

### Option 3: Streaming Responses

```python
from openai import OpenAI

client = OpenAI(api_key='sk-proj-...')

# Create thread and message
thread = client.beta.threads.create()
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Explain React hooks"
)

# Stream response
with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id='asst_abc123xyz'
) as stream:
    for event in stream:
        if event.event == 'thread.message.delta':
            print(event.data.delta.content[0].text.value, end='')
```

## Advanced Usage

### Update Assistant Instructions

```python
from openai import OpenAI

client = OpenAI(api_key='sk-proj-...')

# Update assistant
client.beta.assistants.update(
    assistant_id='asst_abc123xyz',
    instructions="""
You are an expert React assistant.

Focus on modern best practices using:
- React 18+ features
- Functional components
- Hooks-based patterns

When answering:
1. Search knowledge files first
2. Provide working code examples
3. Explain the "why" not just the "what"
"""
)
```

### Add More Files to Vector Store

```python
from openai import OpenAI

client = OpenAI(api_key='sk-proj-...')

# Upload new file
with open('new_guide.md', 'rb') as f:
    file = client.files.create(file=f, purpose='assistants')

# Add to vector store
client.beta.vector_stores.files.create(
    vector_store_id='vs_abc123',
    file_id=file.id
)
```

### Programmatic Package and Upload

```python
from skill_seekers.cli.adaptors import get_adaptor
from pathlib import Path

# Get adaptor
openai_adaptor = get_adaptor('openai')

# Package skill
package_path = openai_adaptor.package(
    skill_dir=Path('output/react'),
    output_path=Path('output/react-openai.zip')
)

# Upload (creates Assistant + Vector Store)
result = openai_adaptor.upload(
    package_path=package_path,
    api_key='sk-proj-...'
)

if result['success']:
    print(f"✅ Assistant created!")
    print(f"ID: {result['skill_id']}")
    print(f"URL: {result['url']}")
else:
    print(f"❌ Upload failed: {result['message']}")
```

## OpenAI-Specific Features

### 1. Semantic Search (file_search)

The Assistant uses embeddings to:
- Find semantically similar content
- Understand intent vs. keywords
- Surface relevant examples automatically

### 2. Citations and Sources

Assistants can provide:
- Source attribution
- File references
- Quote extraction

### 3. Function Calling (Optional)

Extend your assistant with custom tools:

```python
client.beta.assistants.update(
    assistant_id='asst_abc123xyz',
    tools=[
        {"type": "file_search"},
        {"type": "function", "function": {
            "name": "run_code_example",
            "description": "Execute React code examples",
            "parameters": {...}
        }}
    ]
)
```

### 4. Multi-Modal Support

Include images in your documentation:
- Screenshots
- Diagrams
- Architecture charts

## Troubleshooting

### Issue: `openai not installed`

**Solution:**
```bash
pip install skill-seekers[openai]
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

### Issue: `Assistant creation failed`

**Possible causes:**
- API key lacks permissions
- Rate limit exceeded
- File too large

**Solution:**
```bash
# Verify API key
python3 -c "from openai import OpenAI; print(OpenAI(api_key='sk-proj-...').models.list())"

# Check rate limits
# Visit: https://platform.openai.com/account/limits

# Reduce file count
skill-seekers package output/react/ --target openai --max-files 20
```

### Issue: Enhancement fails

**Solution:**
```bash
# Check API quota and billing
# Visit: https://platform.openai.com/account/billing

# Try with smaller skill
skill-seekers enhance output/react/ --target openai --max-files 5

# Use without enhancement
skill-seekers package output/react/ --target openai
# (Skip enhancement step)
```

### Issue: file_search not working

**Symptoms:** Assistant doesn't reference documentation

**Solution:**
- Verify Vector Store has files
- Check Assistant tool configuration
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
run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
print(f"Input tokens: {run.usage.prompt_tokens}")
print(f"Output tokens: {run.usage.completion_tokens}")
```

### 5. Update Regularly

```bash
# Re-scrape updated documentation
skill-seekers scrape --config configs/react.json

# Re-enhance and upload (creates new Assistant)
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

1. ✅ Install OpenAI support: `pip install skill-seekers[openai]`
2. ✅ Get API key from OpenAI Platform
3. ✅ Scrape your documentation
4. ✅ Enhance with GPT-4o
5. ✅ Package for OpenAI
6. ✅ Upload and create Assistant
7. ✅ Test in Playground

## Resources

- [OpenAI Platform](https://platform.openai.com/)
- [Assistants API Documentation](https://platform.openai.com/docs/assistants/overview)
- [OpenAI Pricing](https://openai.com/pricing)
- [Multi-LLM Support Guide](MULTI_LLM_SUPPORT.md)

## Feedback

Found an issue or have suggestions? [Open an issue](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
