# Skill Seekers GitHub Action

Transform documentation, GitHub repos, PDFs, videos, and 13 other source types into AI-ready skills and RAG knowledge — directly in your CI/CD pipeline.

## Quick Start

```yaml
- uses: yusufkaraaslan/skill-seekers-action@v3
  with:
    source: 'https://react.dev'
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `source` | Yes | — | Source URL, file path, or `owner/repo` |
| `command` | No | `create` | Command: `create`, `scrape`, `github`, `pdf`, `video`, `analyze`, `unified` |
| `target` | No | `claude` | Target platform: `claude`, `openai`, `gemini`, `langchain`, `llamaindex`, `markdown` |
| `config` | No | — | Path to JSON config file |
| `output-dir` | No | `output` | Output directory |
| `extra-args` | No | — | Additional CLI arguments |

## Outputs

| Output | Description |
|--------|-------------|
| `skill-dir` | Path to the generated skill directory |
| `skill-name` | Name of the generated skill |

## Examples

### Auto-update documentation skill weekly

```yaml
name: Update AI Skills
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday 6am UTC
  workflow_dispatch:

jobs:
  update-skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: yusufkaraaslan/skill-seekers-action@v3
        with:
          source: 'https://react.dev'
          target: 'langchain'

      - uses: actions/upload-artifact@v4
        with:
          name: react-skill
          path: output/
```

### Generate skill from GitHub repo

```yaml
- uses: yusufkaraaslan/skill-seekers-action@v3
  with:
    source: 'pallets/flask'
    command: 'github'
    target: 'claude'
```

### Process PDF documentation

```yaml
- uses: actions/checkout@v4

- uses: yusufkaraaslan/skill-seekers-action@v3
  with:
    source: 'docs/api-reference.pdf'
    command: 'pdf'
```

### Unified multi-source build with config

```yaml
- uses: actions/checkout@v4

- uses: yusufkaraaslan/skill-seekers-action@v3
  with:
    config: 'configs/my-project.json'
    command: 'unified'
    target: 'openai'
```

### Commit generated skill back to repo

```yaml
- uses: actions/checkout@v4

- uses: yusufkaraaslan/skill-seekers-action@v3
  id: generate
  with:
    source: 'https://fastapi.tiangolo.com'

- name: Commit skill
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add output/
    git diff --staged --quiet || git commit -m "Update AI skill: ${{ steps.generate.outputs.skill-name }}"
    git push
```

## Environment Variables

Pass API keys as environment variables for AI-enhanced skills:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Supported Source Types

| Type | Example Source |
|------|---------------|
| Documentation (web) | `https://react.dev` |
| GitHub repo | `pallets/flask` or `https://github.com/pallets/flask` |
| PDF | `docs/manual.pdf` |
| Video | `https://youtube.com/watch?v=...` |
| Local codebase | `./src` |
| Jupyter Notebook | `analysis.ipynb` |
| OpenAPI/Swagger | `openapi.yaml` |
| Word (.docx) | `docs/guide.docx` |
| EPUB | `book.epub` |
| PowerPoint | `slides.pptx` |
| AsciiDoc | `docs/guide.adoc` |
| HTML | `page.html` |
| RSS/Atom | `feed.rss` |
| Man pages | `tool.1` |
| Confluence | Via config file |
| Notion | Via config file |
| Chat (Slack/Discord) | Via config file |

## License

MIT
