# End-to-End Usage Examples: Claude vs Kimi

**Complete workflows for all 17 source types with both agents**

---

## Quick Reference

```bash
# Set your preferred agent (pick one)
export SKILL_SEEKER_AGENT=claude    # Claude Code CLI
export SKILL_SEEKER_AGENT=kimi      # Kimi Code CLI

# Then use ANY scraper - it will use your chosen agent
skill-seekers create <source> --name <skill-name>
```

---

## 1. Documentation Scraping (Web)

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create https://react.dev \
  --name react-docs \
  --preset comprehensive \
  --enhance-level 3 \
  --output ./output/react-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create https://react.dev \
  --name react-docs \
  --preset comprehensive \
  --enhance-level 3 \
  --output ./output/react-kimi
```

### Explicit --agent flag (per-command)
```bash
skill-seekers create https://react.dev --name react-docs --agent claude
skill-seekers create https://react.dev --name react-docs --agent kimi
```

---

## 2. GitHub Repository

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create facebook/react \
  --name react-github \
  --preset comprehensive \
  --local-repo-path ./react-clone \
  --output ./output/react-github-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create facebook/react \
  --name react-github \
  --preset comprehensive \
  --local-repo-path ./react-clone \
  --output ./output/react-github-kimi
```

---

## 3. PDF Documents

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./docs/specification.pdf \
  --name spec-docs \
  --preset standard \
  --output ./output/spec-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./docs/specification.pdf \
  --name spec-docs \
  --preset standard \
  --output ./output/spec-kimi
```

---

## 4. Local Codebase

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./my-project \
  --name my-project-skill \
  --preset comprehensive \
  --languages Python,JavaScript \
  --output ./output/my-project-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./my-project \
  --name my-project-skill \
  --preset comprehensive \
  --languages Python,JavaScript \
  --output ./output/my-project-kimi
```

---

## 5. Video (YouTube)

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --name video-tutorial \
  --preset standard \
  --output ./output/video-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --name video-tutorial \
  --preset standard \
  --output ./output/video-kimi
```

---

## 6. Jupyter Notebooks

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./analysis.ipynb \
  --name notebook-skill \
  --output ./output/notebook-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./analysis.ipynb \
  --name notebook-skill \
  --output ./output/notebook-kimi
```

---

## 7. Word Documents

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./report.docx \
  --name report-skill \
  --output ./output/report-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./report.docx \
  --name report-skill \
  --output ./output/report-kimi
```

---

## 8. EPUB eBooks

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./book.epub \
  --name book-skill \
  --output ./output/book-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./book.epub \
  --name book-skill \
  --output ./output/book-kimi
```

---

## 9. HTML Files

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./docs.html \
  --name html-skill \
  --output ./output/html-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./docs.html \
  --name html-skill \
  --output ./output/html-kimi
```

---

## 10. OpenAPI/Swagger Specs

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./api.yaml \
  --name api-skill \
  --output ./output/api-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./api.yaml \
  --name api-skill \
  --output ./output/api-kimi
```

---

## 11. PowerPoint Presentations

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./slides.pptx \
  --name slides-skill \
  --output ./output/slides-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./slides.pptx \
  --name slides-skill \
  --output ./output/slides-kimi
```

---

## 12. RSS Feeds

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create "https://news.ycombinator.com/rss" \
  --name hackernews-skill \
  --output ./output/rss-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create "https://news.ycombinator.com/rss" \
  --name hackernews-skill \
  --output ./output/rss-kimi
```

---

## 13. Man Pages

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create --man-names git,curl,docker \
  --name cli-tools-skill \
  --output ./output/man-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create --man-names git,curl,docker \
  --name cli-tools-skill \
  --output ./output/man-kimi
```

---

## 14. Confluence

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./confluence-export.zip \
  --name confluence-skill \
  --output ./output/confluence-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./confluence-export.zip \
  --name confluence-skill \
  --output ./output/confluence-kimi
```

---

## 15. Notion

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./notion-export.zip \
  --name notion-skill \
  --output ./output/notion-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./notion-export.zip \
  --name notion-skill \
  --output ./output/notion-kimi
```

---

## 16. Chat (Slack/Discord)

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./slack-export.zip \
  --name slack-skill \
  --platform slack \
  --output ./output/chat-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./slack-export.zip \
  --name slack-skill \
  --platform slack \
  --output ./output/chat-kimi
```

---

## 17. AsciiDoc

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers create ./documentation.adoc \
  --name asciidoc-skill \
  --output ./output/asciidoc-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers create ./documentation.adoc \
  --name asciidoc-skill \
  --output ./output/asciidoc-kimi
```

---

## Unified Config (Multi-Source)

### With Claude Code
```bash
export SKILL_SEEKER_AGENT=claude

skill-seekers unified --config configs/my-project.json \
  --merge-mode ai-enhanced \
  --enhance-level 3 \
  --output ./output/unified-claude
```

### With Kimi
```bash
export SKILL_SEEKER_AGENT=kimi

skill-seekers unified --config configs/my-project.json \
  --merge-mode ai-enhanced \
  --enhance-level 3 \
  --output ./output/unified-kimi
```

---

## Package & Upload

### Package for different platforms
```bash
# Package Claude-enhanced skill for Claude
skill-seekers package ./output/react-claude --target claude

# Package Kimi-enhanced skill for Kimi
skill-seekers package ./output/react-kimi --target kimi

# Package for any platform
skill-seekers package ./output/react-claude --target gemini
skill-seekers package ./output/react-kimi --target openai
```

### Upload to platforms
```bash
# Upload to Claude (needs ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-...
skill-seekers upload ./output/react-claude-claude.zip --target claude

# Upload to Kimi (needs MOONSHOT_API_KEY)
export MOONSHOT_API_KEY=sk-...
skill-seekers upload ./output/react-kimi-kimi.zip --target kimi
```

---

## Complete Workflow Comparison

### Claude Code Workflow
```bash
# 1. Set agent
export SKILL_SEEKER_AGENT=claude

# 2. Create skill (uses Claude for enhancement)
skill-seekers create https://react.dev --name react --preset comprehensive

# 3. Package for Claude
skill-seekers package ./output/react --target claude

# 4. Upload to Claude
skill-seekers upload ./output/react-claude.zip --target claude
```

### Kimi Workflow
```bash
# 1. Set agent
export SKILL_SEEKER_AGENT=kimi

# 2. Create skill (uses Kimi for enhancement)
skill-seekers create https://react.dev --name react --preset comprehensive

# 3. Package for Kimi
skill-seekers package ./output/react --target kimi

# 4. Upload to Kimi
skill-seekers upload ./output/react-kimi.zip --target kimi
```

---

## Key Points

✅ **All 17 scrapers support both agents**  
✅ **Just change `SKILL_SEEKER_AGENT` environment variable**  
✅ **Or use `--agent` flag per-command**  
✅ **Enhancement, packaging, upload all work with both agents**  
✅ **No code changes needed - fully configurable**
