# Google Gemini Integration Guide

Complete guide for creating and deploying skills to Google Gemini using Skill Seekers.

## Overview

Skill Seekers packages documentation into Gemini-compatible formats optimized for:
- **Gemini 2.0 Flash** for enhancement
- **Files API** for document upload
- **Grounding** for accurate, source-based responses

## Setup

### 1. Install Gemini Support

```bash
# Install with Gemini dependencies
pip install skill-seekers[gemini]

# Verify installation
pip list | grep google-generativeai
```

### 2. Get Google API Key

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key"
3. Create new API key or use existing
4. Copy the key (starts with `AIza`)

### 3. Configure API Key

```bash
# Set as environment variable (recommended)
export GOOGLE_API_KEY=AIzaSy...

# Or pass directly to commands
skill-seekers upload --target gemini --api-key AIzaSy...
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

### Step 2: Enhance with Gemini (Optional but Recommended)

```bash
# Enhance SKILL.md using Gemini 2.0 Flash
skill-seekers enhance output/react/ --target gemini

# With API key specified
skill-seekers enhance output/react/ --target gemini --api-key AIzaSy...
```

**What it does:**
- Analyzes all reference documentation
- Extracts 5-10 best code examples
- Creates comprehensive quick reference
- Adds key concepts and usage guidance
- Generates plain markdown (no YAML frontmatter)

**Time:** 20-40 seconds
**Cost:** ~$0.01-0.05 (using Gemini 2.0 Flash)
**Quality boost:** 3/10 → 9/10

### Step 3: Package for Gemini

```bash
# Create tar.gz package for Gemini
skill-seekers package output/react/ --target gemini

# Result: react-gemini.tar.gz
```

**Package structure:**
```
react-gemini.tar.gz/
├── system_instructions.md  # Main documentation (plain markdown)
├── references/             # Individual reference files
│   ├── getting_started.md
│   ├── hooks.md
│   ├── components.md
│   └── ...
└── gemini_metadata.json    # Platform metadata
```

### Step 4: Upload to Gemini

```bash
# Upload to Google AI Studio
skill-seekers upload react-gemini.tar.gz --target gemini

# With API key
skill-seekers upload react-gemini.tar.gz --target gemini --api-key AIzaSy...
```

**Output:**
```
✅ Upload successful!
Skill ID: files/abc123xyz
URL: https://aistudio.google.com/app/files/abc123xyz
Files uploaded: 15 files
```

### Step 5: Use in Gemini

Access your uploaded files in Google AI Studio:

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Navigate to **Files** section
3. Find your uploaded skill files
4. Use with Gemini API or AI Studio

## What Makes Gemini Different?

### Format: Plain Markdown (No YAML)

**Claude format:**
```markdown
---
name: react
description: React framework
---

# React Documentation
...
```

**Gemini format:**
```markdown
# React Documentation

**Description:** React framework for building user interfaces

## Quick Reference
...
```

No YAML frontmatter - Gemini uses plain markdown for better compatibility.

### Package: tar.gz Instead of ZIP

Gemini uses `.tar.gz` compression for better Unix compatibility and smaller file sizes.

### Upload: Files API + Grounding

Files are uploaded to Google's Files API and made available for grounding in Gemini responses.

## Using Your Gemini Skill

### Option 1: Google AI Studio (Web UI)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create new chat or app
3. Reference your uploaded files in prompts:
   ```
   Using the React documentation files, explain hooks
   ```

### Option 2: Gemini API (Python)

```python
import google.generativeai as genai

# Configure with your API key
genai.configure(api_key='AIzaSy...')

# Create model
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Use with uploaded files (automatic grounding)
response = model.generate_content(
    "How do I use React hooks?",
    # Files automatically available via grounding
)

print(response.text)
```

### Option 3: Gemini API with File Reference

```python
import google.generativeai as genai

# Configure
genai.configure(api_key='AIzaSy...')

# Get your uploaded file
files = genai.list_files()
react_file = next(f for f in files if 'react' in f.display_name.lower())

# Use file in generation
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content([
    "Explain React hooks in detail",
    react_file
])

print(response.text)
```

## Advanced Usage

### Enhance with Custom Prompt

The enhancement process can be customized by modifying the adaptor:

```python
from skill_seekers.cli.adaptors import get_adaptor
from pathlib import Path

# Get Gemini adaptor
adaptor = get_adaptor('gemini')

# Enhance with custom parameters
success = adaptor.enhance(
    skill_dir=Path('output/react'),
    api_key='AIzaSy...'
)
```

### Programmatic Upload

```python
from skill_seekers.cli.adaptors import get_adaptor
from pathlib import Path

# Get adaptor
gemini = get_adaptor('gemini')

# Package skill
package_path = gemini.package(
    skill_dir=Path('output/react'),
    output_path=Path('output/react-gemini.tar.gz')
)

# Upload
result = gemini.upload(
    package_path=package_path,
    api_key='AIzaSy...'
)

if result['success']:
    print(f"✅ Uploaded to: {result['url']}")
    print(f"Skill ID: {result['skill_id']}")
else:
    print(f"❌ Upload failed: {result['message']}")
```

### Manual Package Extraction

If you want to inspect or modify the package:

```bash
# Extract tar.gz
tar -xzf react-gemini.tar.gz -C extracted/

# View structure
tree extracted/

# Modify files if needed
nano extracted/system_instructions.md

# Re-package
tar -czf react-gemini-modified.tar.gz -C extracted .
```

## Gemini-Specific Features

### 1. Grounding Support

Gemini automatically grounds responses in your uploaded documentation files, providing:
- Source attribution
- Accurate citations
- Reduced hallucination

### 2. Multimodal Capabilities

Gemini can process:
- Text documentation
- Code examples
- Images (if included in PDFs)
- Tables and diagrams

### 3. Long Context Window

Gemini 2.0 Flash supports:
- Up to 1M token context
- Entire documentation sets in single context
- Better understanding of cross-references

## Troubleshooting

### Issue: `google-generativeai not installed`

**Solution:**
```bash
pip install skill-seekers[gemini]
```

### Issue: `Invalid API key format`

**Error:** API key doesn't start with `AIza`

**Solution:**
- Get new key from [Google AI Studio](https://aistudio.google.com/)
- Verify you're using Google API key, not GCP service account

### Issue: `Not a tar.gz file`

**Error:** Wrong package format

**Solution:**
```bash
# Use --target gemini for tar.gz format
skill-seekers package output/react/ --target gemini

# NOT:
skill-seekers package output/react/  # Creates .zip (Claude format)
```

### Issue: `File upload failed`

**Possible causes:**
- API key lacks permissions
- File too large (check limits)
- Network connectivity

**Solution:**
```bash
# Verify API key works
python3 -c "import google.generativeai as genai; genai.configure(api_key='AIza...'); print(list(genai.list_models())[:2])"

# Check file size
ls -lh react-gemini.tar.gz

# Try with verbose output
skill-seekers upload react-gemini.tar.gz --target gemini --verbose
```

### Issue: Enhancement fails

**Solution:**
```bash
# Check API quota
# Visit: https://aistudio.google.com/apikey

# Try with smaller skill
skill-seekers enhance output/react/ --target gemini --max-files 5

# Use without enhancement
skill-seekers package output/react/ --target gemini
# (Skip enhancement step)
```

## Best Practices

### 1. Organize Documentation

Structure your SKILL.md clearly:
- Start with overview
- Add quick reference section
- Group related concepts
- Include practical examples

### 2. Optimize File Count

- Combine related topics into single files
- Use clear file naming
- Keep total under 100 files for best performance

### 3. Test with Gemini

After upload, test with sample questions:
```
1. How do I get started with [topic]?
2. What are the core concepts?
3. Show me a practical example
4. What are common pitfalls?
```

### 4. Update Regularly

```bash
# Re-scrape updated documentation
skill-seekers scrape --config configs/react.json

# Re-enhance and upload
skill-seekers enhance output/react/ --target gemini
skill-seekers package output/react/ --target gemini
skill-seekers upload react-gemini.tar.gz --target gemini
```

## Cost Estimation

**Gemini 2.0 Flash pricing:**
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

**Typical skill enhancement:**
- Input: ~50K-200K tokens (docs)
- Output: ~5K-10K tokens (enhanced SKILL.md)
- Cost: $0.01-0.05 per skill

**File upload:** Free (no per-file charges)

## Next Steps

1. ✅ Install Gemini support: `pip install skill-seekers[gemini]`
2. ✅ Get API key from Google AI Studio
3. ✅ Scrape your documentation
4. ✅ Enhance with Gemini
5. ✅ Package for Gemini
6. ✅ Upload and test

## Resources

- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini Pricing](https://ai.google.dev/pricing)
- [Multi-LLM Support Guide](MULTI_LLM_SUPPORT.md)

## Feedback

Found an issue or have suggestions? [Open an issue](https://github.com/yusufkaraaslan/Skill_Seekers/issues)
