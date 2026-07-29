---
name: skill-builder
description: Automatically detect source types and build AI skills using Skill Seekers. Use when the user wants to create skills from documentation, repos, PDFs, videos, or other knowledge sources.
---

# Skill Builder

This skill uses the Skill Seekers MCP server, which provides 40 tools for converting knowledge sources into AI-ready skills. If the MCP tools are not available, use the CLI fallback at the bottom of this file instead — do not stop.

## Prerequisites

The MCP tools below only work when the Skill Seekers MCP server is connected:

1. Install the package: `pip install "skill-seekers[mcp]"`
2. Connect the server:
   - Installed as the Skill Seekers plugin? Nothing to do — the plugin's bundled `.mcp.json` starts the server automatically (it still needs step 1).
   - Installed standalone (e.g. copied into `~/.claude/skills/`)? Register the server once: `claude mcp add skill-seekers -- python -m skill_seekers.mcp.server_fastmcp`

If tools like `scrape_docs` or `package_skill` are not in your tool list, the server is not connected. Tell the user about the two steps above, and use the CLI fallback in the meantime.

## When to Use This Skill

Use this skill when the user:
- Wants to create an AI skill from a documentation site, GitHub repo, PDF, video, or other source
- Needs to convert documentation into a format suitable for LLM consumption
- Wants to update or sync existing skills with their source documentation
- Needs to export skills to vector databases (Weaviate, Chroma, FAISS, Qdrant)
- Asks about scraping, converting, or packaging documentation for AI

## Source Type Detection

Automatically detect the source type from user input:

| Input Pattern | Source Type | Tool to Use |
|---------------|-------------|-------------|
| `https://...` (not GitHub/YouTube) | Documentation | `scrape_docs` |
| `owner/repo` or `github.com/...` | GitHub | `scrape_github` |
| `*.pdf` | PDF | `scrape_pdf` |
| YouTube/Vimeo URL or video file | Video | `scrape_video` |
| Local directory path | Codebase | `scrape_codebase` |
| `*.ipynb`, `*.html`, `*.yaml` (OpenAPI), `*.adoc`, `*.pptx`, `*.rss`, `*.1`-`.8` | Various | `scrape_generic` |
| JSON config file | Unified | Use config with `scrape_docs` |

## Recommended Workflow

1. **Detect source type** from the user's input
2. **Generate or fetch config** using `generate_config` or `fetch_config` if needed
3. **Estimate scope** with `estimate_pages` for documentation sites
4. **Scrape the source** using the appropriate scraping tool
5. **Enhance** with `enhance_skill` if the user wants AI-powered improvements
6. **Package** with `package_skill` for the target platform
7. **Export to vector DB** if requested using `export_to_*` tools

## Available MCP Tools

### Config Management
- `generate_config` — Generate a scraping config from a URL
- `list_configs` — List available preset configs
- `validate_config` — Validate a config file

### Scraping (use based on source type)
- `scrape_docs` — Documentation sites
- `scrape_github` — GitHub repositories
- `scrape_pdf` — PDF files
- `scrape_video` — Video transcripts
- `scrape_codebase` — Local code analysis
- `scrape_generic` — Jupyter, HTML, OpenAPI, AsciiDoc, PPTX, RSS, manpage, Confluence, Notion, chat

### Post-processing
- `enhance_skill` — AI-powered skill enhancement
- `package_skill` — Package for target platform
- `upload_skill` — Upload to platform API
- `install_skill` — End-to-end install workflow

### Advanced
- `detect_patterns` — Design pattern detection in code
- `extract_test_examples` — Extract usage examples from tests
- `build_how_to_guides` — Generate how-to guides from tests
- `split_config` — Split large configs into focused skills
- `export_to_weaviate`, `export_to_chroma`, `export_to_faiss`, `export_to_qdrant` — Vector DB export

## CLI Fallback (MCP server not connected)

The same pipeline is available from the command line (requires `pip install skill-seekers`). Run it with the Bash tool:

```bash
skill-seekers create <source>                      # auto-detects: URL, owner/repo, ./path, file.pdf, video URL, ...
skill-seekers package <skill_dir> --target claude  # or gemini/openai/langchain/chroma/...
```

`create` covers detection, scraping, and building in one step; add `--enhance-level 0` to skip AI enhancement. After it finishes, read the generated `SKILL.md` and summarize what was created.
