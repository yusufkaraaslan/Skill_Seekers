# 故障排除指南

> **Skill Seekers v3.6.0**

本章涵盖最常见的问题。如需包含所有错误代码、平台特定修复和高级诊断的**完整故障排除指南**，请参阅 [docs/TROUBLESHOOTING.md](../../TROUBLESHOOTING.md)。

---

## 快速修复

| 问题 | 快速修复 |
|-------|-----------|
| `command not found` | `export PATH="$HOME/.local/bin:$PATH"` |
| `ImportError` | `pip install -e .` |
| `Rate limit` | 添加 `--rate-limit 2.0` |
| `No content` | 检查配置中的选择器 |
| `Enhancement fails` | 设置 `ANTHROPIC_API_KEY` |
| `Out of memory` | 使用 `--streaming` 模式 |

---

## 安装问题

### "command not found: skill-seekers"
**原因：** pip 的 bin 目录不在 PATH 中

```bash
export PATH="$HOME/.local/bin:$PATH"
which skill-seekers
```

### "No module named 'skill_seekers'"
**原因：** 包未安装

```bash
pip install -e .
python -c "import skill_seekers; print(skill_seekers.__version__)"
```

---

## 抓取问题

### "Rate limit exceeded"
```bash
skill-seekers create <url> --rate-limit 2.0
export GITHUB_TOKEN=ghp_...
```

### "No content extracted"
**原因：** CSS 选择器错误。检查你的配置，或使用自动检测：

```bash
skill-seekers create <url> --preset quick
```

---

## 增强问题

### "Enhancement failed: No API key"
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# 或使用 LOCAL 模式（无需 API key —— 选择一个已安装的本地代理）
skill-seekers enhance output/my-skill/ --agent claude
```

---

## 打包与上传问题

### "Target platform not supported"
```bash
skill-seekers package output/my-skill/ --target claude
# Valid targets: claude, gemini, openai, langchain, llama-index,
#   haystack, pinecone, chroma, weaviate, qdrant, faiss, markdown,
#   deepseek, kimi, qwen, openrouter, together, fireworks, ibm-bob
```

### "Upload failed: Invalid API key"
检查平台特定的环境变量：
- Claude：`ANTHROPIC_API_KEY`
- Gemini：`GOOGLE_API_KEY`
- OpenAI：`OPENAI_API_KEY`

---

## 获取帮助

### 调试模式
```bash
skill-seekers create <source> --verbose
export SKILL_SEEKERS_DEBUG=1
```

### 报告问题
1. 收集信息：`skill-seekers --version`、`python --version`
2. 启用调试：`skill-seekers <command> --verbose 2>&1 | tee debug.log`
3. 创建 issue：https://github.com/yusufkaraaslan/Skill_Seekers/issues

---

**需要更多帮助？** 参阅[完整故障排除指南](../../TROUBLESHOOTING.md)，内容包括：
- 所有错误代码及解决方案
- 平台特定修复（Docker、K8s、Windows）
- 性能调优
- 网络与 SSL 问题
- 来源特定的故障排除（PDF、视频、GitHub 等）
