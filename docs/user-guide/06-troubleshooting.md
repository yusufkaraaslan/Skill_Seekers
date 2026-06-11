# Troubleshooting Guide

> **Skill Seekers v3.6.0**

This chapter covers the most common issues. For the **complete troubleshooting guide** with all error codes, platform-specific fixes, and advanced diagnostics, see [docs/TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

---

## Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| `command not found` | `export PATH="$HOME/.local/bin:$PATH"` |
| `ImportError` | `pip install -e .` |
| `Rate limit` | Add `--rate-limit 2.0` |
| `No content` | Check selectors in config |
| `Enhancement fails` | Set `ANTHROPIC_API_KEY` |
| `Out of memory` | Use `--streaming` mode |

---

## Installation Issues

### "command not found: skill-seekers"
**Cause:** pip bin directory not in PATH

```bash
export PATH="$HOME/.local/bin:$PATH"
which skill-seekers
```

### "No module named 'skill_seekers'"
**Cause:** Package not installed

```bash
pip install -e .
python -c "import skill_seekers; print(skill_seekers.__version__)"
```

---

## Scraping Issues

### "Rate limit exceeded"
```bash
skill-seekers create <url> --rate-limit 2.0
export GITHUB_TOKEN=ghp_...
```

### "No content extracted"
**Cause:** Wrong CSS selectors. Check your config or use auto-detection:

```bash
skill-seekers create <url> --preset quick
```

---

## Enhancement Issues

### "Enhancement failed: No API key"
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# Or use LOCAL mode (no API key needed — pick an installed local agent)
skill-seekers enhance output/my-skill/ --agent claude
```

---

## Packaging & Upload Issues

### "Target platform not supported"
```bash
skill-seekers package output/my-skill/ --target claude
# Valid targets: claude, gemini, openai, langchain, llama-index,
#   haystack, pinecone, chroma, weaviate, qdrant, faiss, markdown,
#   deepseek, kimi, qwen, openrouter, together, fireworks, ibm-bob
```

### "Upload failed: Invalid API key"
Check platform-specific env vars:
- Claude: `ANTHROPIC_API_KEY`
- Gemini: `GOOGLE_API_KEY`
- OpenAI: `OPENAI_API_KEY`

---

## Getting Help

### Debug Mode
```bash
skill-seekers create <source> --verbose
export SKILL_SEEKERS_DEBUG=1
```

### Report an Issue
1. Gather info: `skill-seekers --version`, `python --version`
2. Enable debug: `skill-seekers <command> --verbose 2>&1 | tee debug.log`
3. Create issue: https://github.com/yusufkaraaslan/Skill_Seekers/issues

---

**Need more?** See the [complete troubleshooting guide](../TROUBLESHOOTING.md) for:
- All error codes and solutions
- Platform-specific fixes (Docker, K8s, Windows)
- Performance tuning
- Network and SSL issues
- Source-specific troubleshooting (PDF, video, GitHub, etc.)
