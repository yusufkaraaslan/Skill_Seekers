---
description: One-command skill creation and packaging for a target platform
---

# Install Skill

End-to-end workflow: create a skill from any source, then package it for a target LLM platform.

## Usage

```
/skill-seekers:install-skill <source> [--target <platform>] [--preset <level>]
```

## Instructions

When the user provides a source via `$ARGUMENTS`:

1. Parse the arguments: extract source, `--target` (default: claude), `--preset` (default: quick).
2. Run the create command:
   ```bash
   skill-seekers create "$SOURCE" --preset "$PRESET" --output ./output
   ```
3. Find the generated skill directory (look for the directory containing SKILL.md in ./output/).
4. Run the package command for the target platform:
   ```bash
   skill-seekers package "$SKILL_DIR" --target "$TARGET"
   ```
5. Report what was created and where to find the packaged output.

## Target Platforms

`claude` (default), `openai`, `gemini`, `langchain`, `llamaindex`, `haystack`, `cursor`, `windsurf`, `continue`, `cline`, `markdown`

## Examples

```
/skill-seekers:install-skill https://react.dev --target claude
/skill-seekers:install-skill pallets/flask --target langchain -p standard
/skill-seekers:install-skill ./docs/api.pdf --target openai
```
