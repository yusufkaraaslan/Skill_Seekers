---
description: Create an AI skill from any source (URL, repo, PDF, video, notebook, etc.)
---

# Create Skill

Create an AI-ready skill from a source. The source type is auto-detected.

## Usage

```
/skill-seekers:create-skill <source> [--target <platform>] [--output <dir>]
```

## Instructions

When the user provides a source via `$ARGUMENTS`, run the `skill-seekers create` command to generate a skill.

1. Parse the arguments: extract the source (first argument) and any flags.
2. If no `--target` is specified, default to `claude`.
3. If no `--output` is specified, default to `./output`.
4. Run the command:
   ```bash
   skill-seekers create "$SOURCE" --target "$TARGET" --output "$OUTPUT"
   ```
5. After completion, read the generated `SKILL.md` and summarize what was created.

## Source Types (auto-detected)

- **URL** (https://...) → Documentation scraping
- **owner/repo** or github.com URL → GitHub repo analysis
- **file.pdf** → PDF extraction
- **file.ipynb** → Jupyter notebook
- **file.docx** → Word document
- **file.epub** → EPUB book
- **YouTube/Vimeo URL** → Video transcript
- **./directory** → Local codebase analysis
- **file.yaml** with OpenAPI → API spec
- **file.pptx** → PowerPoint
- **file.adoc** → AsciiDoc
- **file.html** → HTML page
- **file.rss** → RSS/Atom feed
- **cmd.1** → Man page

## Examples

```
/skill-seekers:create-skill https://react.dev
/skill-seekers:create-skill pallets/flask --target langchain
/skill-seekers:create-skill ./docs/api.pdf --target openai
/skill-seekers:create-skill https://youtube.com/watch?v=abc123
```
