# Multi-LLM Platform Support Guide

Skill Seekers supports multiple LLM platforms through a clean adaptor system. The core scraping and content organization remains universal, while packaging and upload are platform-specific.

## Supported Platforms

| Platform | Status | Format | Upload | Enhancement | API Key Required |
|----------|--------|--------|--------|-------------|------------------|
| **Claude AI** | ✅ Full Support | ZIP + YAML | ✅ Automatic | ✅ Yes | ANTHROPIC_API_KEY |
| **Google Gemini** | ✅ Full Support | tar.gz | ✅ Automatic | ✅ Yes | GOOGLE_API_KEY |
| **OpenAI ChatGPT** | ✅ Full Support | ZIP + Vector Store | ✅ Automatic | ✅ Yes | OPENAI_API_KEY |
| **Generic Markdown** | ✅ Export Only | ZIP | ❌ Manual | ❌ No | None |

## Quick Start

### Claude AI (Default)

No changes needed! All existing workflows continue to work:

```bash
# Scrape documentation
skill-seekers scrape --config configs/react.json

# Package for Claude (default)
skill-seekers package output/react/

# Upload to Claude
skill-seekers upload react.zip
```

### Google Gemini

```bash
# Install Gemini support
pip install skill-seekers[gemini]

# Set API key
export GOOGLE_API_KEY=AIzaSy...

# Scrape documentation (same as always)
skill-seekers scrape --config configs/react.json

# Package for Gemini
skill-seekers package output/react/ --target gemini

# Upload to Gemini
skill-seekers upload react-gemini.tar.gz --target gemini

# Optional: Enhance with Gemini
skill-seekers enhance output/react/ --target gemini
```

**Output:** `react-gemini.tar.gz` ready for Google AI Studio

### OpenAI ChatGPT

```bash
# Install OpenAI support
pip install skill-seekers[openai]

# Set API key
export OPENAI_API_KEY=sk-proj-...

# Scrape documentation (same as always)
skill-seekers scrape --config configs/react.json

# Package for OpenAI
skill-seekers package output/react/ --target openai

# Upload to OpenAI (creates Assistant + Vector Store)
skill-seekers upload react-openai.zip --target openai

# Optional: Enhance with GPT-4o
skill-seekers enhance output/react/ --target openai
```

**Output:** OpenAI Assistant created with file search enabled

### Generic Markdown (Universal Export)

```bash
# Package as generic markdown (no dependencies)
skill-seekers package output/react/ --target markdown

# Output: react-markdown.zip with:
#   - README.md
#   - references/*.md
#   - DOCUMENTATION.md (combined)
```

**Use case:** Export for any LLM, documentation hosting, or manual distribution

## Installation Options

### Install Core Package Only

```bash
# Default installation (Claude support only)
pip install skill-seekers
```

### Install with Specific Platform Support

```bash
# Google Gemini support
pip install skill-seekers[gemini]

# OpenAI ChatGPT support
pip install skill-seekers[openai]

# All LLM platforms
pip install skill-seekers[all-llms]

# Development dependencies (includes testing)
pip install skill-seekers[dev]
```

### Install from Source

```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers

# Editable install with all platforms
pip install -e .[all-llms]
```

## Platform Comparison

### Format Differences

**Claude AI:**
- Format: ZIP archive
- SKILL.md: YAML frontmatter + markdown
- Structure: `SKILL.md`, `references/`, `scripts/`, `assets/`
- API: Anthropic Skills API
- Enhancement: Claude Sonnet 4

**Google Gemini:**
- Format: tar.gz archive
- SKILL.md → `system_instructions.md` (plain markdown, no frontmatter)
- Structure: `system_instructions.md`, `references/`, `gemini_metadata.json`
- API: Google Files API + grounding
- Enhancement: Gemini 2.0 Flash

**OpenAI ChatGPT:**
- Format: ZIP archive
- SKILL.md → `assistant_instructions.txt` (plain text)
- Structure: `assistant_instructions.txt`, `vector_store_files/`, `openai_metadata.json`
- API: Assistants API + Vector Store
- Enhancement: GPT-4o

**Generic Markdown:**
- Format: ZIP archive
- Structure: `README.md`, `references/`, `DOCUMENTATION.md` (combined)
- No API integration
- No enhancement support
- Universal compatibility

### API Key Configuration

**Claude AI:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Google Gemini:**
```bash
export GOOGLE_API_KEY=AIzaSy...
```

**OpenAI ChatGPT:**
```bash
export OPENAI_API_KEY=sk-proj-...
```

## Complete Workflow Examples

### Workflow 1: Claude AI (Default)

```bash
# 1. Scrape
skill-seekers scrape --config configs/react.json

# 2. Enhance (optional but recommended)
skill-seekers enhance output/react/

# 3. Package
skill-seekers package output/react/

# 4. Upload
skill-seekers upload react.zip

# Access at: https://claude.ai/skills
```

### Workflow 2: Google Gemini

```bash
# Setup (one-time)
pip install skill-seekers[gemini]
export GOOGLE_API_KEY=AIzaSy...

# 1. Scrape (universal)
skill-seekers scrape --config configs/react.json

# 2. Enhance for Gemini
skill-seekers enhance output/react/ --target gemini

# 3. Package for Gemini
skill-seekers package output/react/ --target gemini

# 4. Upload to Gemini
skill-seekers upload react-gemini.tar.gz --target gemini

# Access at: https://aistudio.google.com/files/
```

### Workflow 3: OpenAI ChatGPT

```bash
# Setup (one-time)
pip install skill-seekers[openai]
export OPENAI_API_KEY=sk-proj-...

# 1. Scrape (universal)
skill-seekers scrape --config configs/react.json

# 2. Enhance with GPT-4o
skill-seekers enhance output/react/ --target openai

# 3. Package for OpenAI
skill-seekers package output/react/ --target openai

# 4. Upload (creates Assistant + Vector Store)
skill-seekers upload react-openai.zip --target openai

# Access at: https://platform.openai.com/assistants/
```

### Workflow 4: Export to All Platforms

```bash
# Install all platforms
pip install skill-seekers[all-llms]

# Scrape once
skill-seekers scrape --config configs/react.json

# Package for all platforms
skill-seekers package output/react/ --target claude
skill-seekers package output/react/ --target gemini
skill-seekers package output/react/ --target openai
skill-seekers package output/react/ --target markdown

# Result:
# - react.zip (Claude)
# - react-gemini.tar.gz (Gemini)
# - react-openai.zip (OpenAI)
# - react-markdown.zip (Universal)
```

## Advanced Usage

### Custom Enhancement Models

Each platform uses its default enhancement model, but you can customize:

```bash
# Use specific model for enhancement (if supported)
skill-seekers enhance output/react/ --target gemini --model gemini-2.0-flash-exp
skill-seekers enhance output/react/ --target openai --model gpt-4o
```

### Programmatic Usage

```python
from skill_seekers.cli.adaptors import get_adaptor

# Get platform-specific adaptor
gemini = get_adaptor('gemini')
openai = get_adaptor('openai')
claude = get_adaptor('claude')

# Package for specific platform
gemini_package = gemini.package(skill_dir, output_path)
openai_package = openai.package(skill_dir, output_path)

# Upload with API key
result = gemini.upload(gemini_package, api_key)
print(f"Uploaded to: {result['url']}")
```

### Platform Detection

Check which platforms are available:

```python
from skill_seekers.cli.adaptors import list_platforms, is_platform_available

# List all registered platforms
platforms = list_platforms()
print(platforms)  # ['claude', 'gemini', 'openai', 'markdown']

# Check if platform is available
if is_platform_available('gemini'):
    print("Gemini adaptor is available")
```

## Backward Compatibility

**100% backward compatible** with existing workflows:

- All existing Claude commands work unchanged
- Default behavior remains Claude-focused
- Optional `--target` flag adds multi-platform support
- No breaking changes to existing configs or workflows

## Platform-Specific Guides

For detailed platform-specific instructions, see:

- [Claude AI Integration](CLAUDE_INTEGRATION.md) (default)
- [Google Gemini Integration](GEMINI_INTEGRATION.md)
- [OpenAI ChatGPT Integration](OPENAI_INTEGRATION.md)

## Troubleshooting

### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'google.generativeai'`

**Solution:**
```bash
pip install skill-seekers[gemini]
```

**Error:** `ModuleNotFoundError: No module named 'openai'`

**Solution:**
```bash
pip install skill-seekers[openai]
```

### API Key Issues

**Error:** `Invalid API key format`

**Solution:** Check your API key format:
- Claude: `sk-ant-...`
- Gemini: `AIza...`
- OpenAI: `sk-proj-...` or `sk-...`

### Package Format Errors

**Error:** `Not a tar.gz file: react.zip`

**Solution:** Use correct --target flag:
```bash
# Gemini requires tar.gz
skill-seekers package output/react/ --target gemini

# OpenAI and Claude use ZIP
skill-seekers package output/react/ --target openai
```

## FAQ

**Q: Can I use the same scraped data for all platforms?**

A: Yes! The scraping phase is universal. Only packaging and upload are platform-specific.

**Q: Do I need separate API keys for each platform?**

A: Yes, each platform requires its own API key. Set them as environment variables.

**Q: Can I enhance with different models?**

A: Yes, each platform uses its own enhancement model:
- Claude: Claude Sonnet 4
- Gemini: Gemini 2.0 Flash
- OpenAI: GPT-4o

**Q: What if I don't want to upload automatically?**

A: Use the `package` command without `upload`. You'll get the packaged file to upload manually.

**Q: Is the markdown export compatible with all LLMs?**

A: Yes! The generic markdown export creates universal documentation that works with any LLM or documentation system.

**Q: Can I contribute a new platform adaptor?**

A: Absolutely! See the [Contributing Guide](../CONTRIBUTING.md) for how to add new platform adaptors.

## Next Steps

1. Choose your target platform
2. Install optional dependencies if needed
3. Set up API keys
4. Follow the platform-specific workflow
5. Upload and test your skill

For more help, see:
- [Quick Start Guide](../QUICKSTART.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [Platform-Specific Guides](.)
