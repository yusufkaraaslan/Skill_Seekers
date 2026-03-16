---
description: One-command skill installation — fetch config, scrape, enhance, package, and install
---

# Install Skill

Complete end-to-end workflow: fetch a config (from preset or URL), scrape the source, optionally enhance with AI, package for the target platform, and install.

## Usage

```
/skill-seekers:install-skill <config-or-source> [--target <platform>] [--enhance]
```

## Instructions

When the user provides a source or config via `$ARGUMENTS`:

1. Determine if the argument is a config preset name, config file path, or a direct source.
2. Use the `install_skill` MCP tool if available, or run the equivalent CLI commands:
   ```bash
   # For preset configs
   skill-seekers install --config "$CONFIG" --target "$TARGET"

   # For direct sources
   skill-seekers create "$SOURCE" --target "$TARGET"
   ```
3. If `--enhance` is specified, run enhancement after initial scraping:
   ```bash
   skill-seekers enhance "$SKILL_DIR" --target "$TARGET"
   ```
4. Report the final skill location and how to use it.

## Target Platforms

`claude`, `openai`, `gemini`, `langchain`, `llamaindex`, `haystack`, `cursor`, `windsurf`, `continue`, `cline`, `markdown`

## Examples

```
/skill-seekers:install-skill react --target claude
/skill-seekers:install-skill https://fastapi.tiangolo.com --target langchain --enhance
/skill-seekers:install-skill pallets/flask
```
