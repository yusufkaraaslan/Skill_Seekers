# MiniMax AI Integration Guide

Complete guide for using Skill Seekers with MiniMax AI platform.

---

## Overview

**MiniMax AI** is a Chinese AI company offering OpenAI-compatible APIs with their M2.7 model. Skill Seekers packages documentation for use with MiniMax's platform.

### Key Features

- **OpenAI-Compatible API**: Uses standard OpenAI client library
- **MiniMax-M2.7 Model**: Powerful LLM for enhancement and chat
- **Simple ZIP Format**: Easy packaging with system instructions
- **Knowledge Files**: Reference documentation included in package

---

## Prerequisites

### 1. Get MiniMax API Key

1. Visit [MiniMax Platform](https://platform.minimaxi.com/)
2. Create an account and verify
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the key (starts with `eyJ` - JWT format)

### 2. Install Dependencies

```bash
# Install MiniMax support (includes openai library)
pip install skill-seekers[minimax]

# Or install all LLM platforms
pip install skill-seekers[all-llms]
```

### 3. Configure Environment

```bash
export MINIMAX_API_KEY=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Add to your `~/.bashrc`, `~/.zshrc`, or `.env` file for persistence.

---

## Complete Workflow

### Step 1: Scrape Documentation

```bash
# Scrape documentation website
skill-seekers scrape --config configs/react.json

# Or use quick preset
skill-seekers create https://docs.python.org/3/ --preset quick
```

### Step 2: Enhance with MiniMax-M2.7

```bash
# Enhance SKILL.md using MiniMax AI
skill-seekers enhance output/react/ --target minimax

# With custom model (if available)
skill-seekers enhance output/react/ --target minimax --model MiniMax-M2.7
```

This step:
- Reads reference documentation
- Generates enhanced system instructions
- Creates backup of original SKILL.md
- Uses MiniMax-M2.7 for AI enhancement

### Step 3: Package for MiniMax

```bash
# Package as MiniMax-compatible ZIP
skill-seekers package output/react/ --target minimax

# Custom output path
skill-seekers package output/react/ --target minimax --output my-skill.zip
```

**Output structure:**
```
react-minimax.zip
├── system_instructions.txt    # Main instructions (from SKILL.md)
├── knowledge_files/           # Reference documentation
│   ├── guide.md
│   ├── api-reference.md
│   └── examples.md
└── minimax_metadata.json      # Skill metadata
```

### Step 4: Validate Package

```bash
# Validate package with MiniMax API
skill-seekers upload react-minimax.zip --target minimax
```

This validates:
- Package structure
- API connectivity
- System instructions format

**Note:** MiniMax doesn't have persistent skill storage like Claude. The upload validates your package but you'll use the ZIP file directly with MiniMax's API.

---

## Using Your Skill

### Direct API Usage

```python
from openai import OpenAI
import zipfile
import json

# Extract package
with zipfile.ZipFile('react-minimax.zip', 'r') as zf:
    with zf.open('system_instructions.txt') as f:
        system_instructions = f.read().decode('utf-8')
    
    # Load metadata
    with zf.open('minimax_metadata.json') as f:
        metadata = json.load(f)

# Initialize MiniMax client (OpenAI-compatible)
client = OpenAI(
    api_key="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    base_url="https://api.minimax.io/v1"
)

# Use with chat completions
response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": "How do I create a React component?"}
    ],
    temperature=0.3,
    max_tokens=2000
)

print(response.choices[0].message.content)
```

### With Knowledge Files

```python
import zipfile
from pathlib import Path

# Extract knowledge files
with zipfile.ZipFile('react-minimax.zip', 'r') as zf:
    zf.extractall('extracted_skill')

# Read all knowledge files
knowledge_dir = Path('extracted_skill/knowledge_files')
knowledge_files = []
for md_file in knowledge_dir.glob('*.md'):
    knowledge_files.append({
        'name': md_file.name,
        'content': md_file.read_text()
    })

# Include in context (truncate if too long)
context = "\n\n".join([f"## {kf['name']}\n{kf['content'][:5000]}" 
                     for kf in knowledge_files[:5]])

response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: What are React hooks?"}
    ]
)
```

---

## API Reference

### SkillAdaptor Methods

```python
from skill_seekers.cli.adaptors import get_adaptor

# Get MiniMax adaptor
adaptor = get_adaptor('minimax')

# Format SKILL.md as system instructions
instructions = adaptor.format_skill_md(skill_dir, metadata)

# Package skill
package_path = adaptor.package(skill_dir, output_path)

# Validate package with MiniMax API
result = adaptor.upload(package_path, api_key)
print(result['message'])  # Validation result

# Enhance SKILL.md
success = adaptor.enhance(skill_dir, api_key)
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MINIMAX_API_KEY` | Your MiniMax API key (JWT format) | Yes |

---

## Troubleshooting

### Invalid API Key Format

**Error:** `Invalid API key format`

**Solution:** MiniMax API keys use JWT format starting with `eyJ`. Check:
```bash
# Should start with 'eyJ'
echo $MINIMAX_API_KEY | head -c 10
# Output: eyJhbGciOi
```

### OpenAI Library Not Installed

**Error:** `ModuleNotFoundError: No module named 'openai'`

**Solution:**
```bash
pip install skill-seekers[minimax]
# or
pip install openai>=1.0.0
```

### Upload Timeout

**Error:** `Upload timed out`

**Solution:**
- Check internet connection
- Try again (temporary network issue)
- Verify API key is correct
- Check MiniMax platform status

### Connection Error

**Error:** `Connection error`

**Solution:**
- Verify internet connectivity
- Check if MiniMax API endpoint is accessible:
```bash
curl https://api.minimax.io/v1/models
```
- Try with VPN if in restricted region

### Package Validation Failed

**Error:** `Invalid package: system_instructions.txt not found`

**Solution:**
- Ensure SKILL.md exists before packaging
- Check package contents:
```bash
unzip -l react-minimax.zip
```
- Re-package the skill

---

## Best Practices

### 1. Keep References Organized

Structure your documentation:
```
output/react/
├── SKILL.md              # Main instructions
├── references/
│   ├── 01-getting-started.md
│   ├── 02-components.md
│   ├── 03-hooks.md
│   └── 04-api-reference.md
└── assets/
    └── diagrams/
```

### 2. Use Enhancement

Always enhance before packaging:
```bash
# Enhancement improves system instructions quality
skill-seekers enhance output/react/ --target minimax
```

### 3. Test Before Deployment

```bash
# Validate package
skill-seekers upload react-minimax.zip --target minimax

# If successful, package is ready to use
```

### 4. Version Your Skills

```bash
# Include version in output name
skill-seekers package output/react/ --target minimax --output react-v2.0-minimax.zip
```

---

## Comparison with Other Platforms

| Feature | MiniMax | Claude | Gemini | OpenAI |
|---------|---------|--------|--------|--------|
| **Format** | ZIP | ZIP | tar.gz | ZIP |
| **Upload** | Validation | Full API | Full API | Full API |
| **Enhancement** | MiniMax-M2.7 | Claude Sonnet | Gemini 2.0 | GPT-4o |
| **API Type** | OpenAI-compatible | Anthropic | Google | OpenAI |
| **Key Format** | JWT (eyJ...) | sk-ant... | AIza... | sk-... |
| **Knowledge Files** | Included in ZIP | Included | Included | Vector Store |

---

## Advanced Usage

### Custom Enhancement Prompt

Programmatically customize enhancement:

```python
from skill_seekers.cli.adaptors import get_adaptor
from pathlib import Path

adaptor = get_adaptor('minimax')
skill_dir = Path('output/react')

# Build custom prompt
references = adaptor._read_reference_files(skill_dir / 'references')
prompt = adaptor._build_enhancement_prompt(
    skill_name='React',
    references=references,
    current_skill_md=(skill_dir / 'SKILL.md').read_text()
)

# Customize prompt
prompt += "\n\nADDITIONAL FOCUS: Emphasize React 18 concurrent features."

# Use with your own API call
```

### Batch Processing

```bash
# Process multiple frameworks
for framework in react vue angular; do
    skill-seekers scrape --config configs/${framework}.json
    skill-seekers enhance output/${framework}/ --target minimax
    skill-seekers package output/${framework}/ --target minimax --output ${framework}-minimax.zip
done
```

---

## Resources

- [MiniMax Platform](https://platform.minimaxi.com/)
- [MiniMax API Documentation](https://platform.minimaxi.com/document)
- [OpenAI Python Client](https://github.com/openai/openai-python)
- [Multi-LLM Support Guide](MULTI_LLM_SUPPORT.md)

---

## Next Steps

1. Get your [MiniMax API key](https://platform.minimaxi.com/)
2. Install dependencies: `pip install skill-seekers[minimax]`
3. Try the [Quick Start example](#complete-workflow)
4. Explore [advanced usage](#advanced-usage) patterns

For help, see [Troubleshooting](#troubleshooting) or open an issue on GitHub.
