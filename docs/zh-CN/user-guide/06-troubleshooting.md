# 故障排除指南

> **Skill Seekers v3.6.0**
> **常见问题和解决方案**

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

**原因：** pip bin 目录不在 PATH 中

**解决方案：**
```bash
# 添加到 PATH
export PATH="$HOME/.local/bin:$PATH"

# 或使用 --user 重新安装
pip install --user --force-reinstall skill-seekers

# 验证
which skill-seekers
```

---

### "No module named 'skill_seekers'"

**原因：** 包未安装或 Python 环境错误

**解决方案：**
```bash
# 安装包
pip install skill-seekers

# 开发环境
pip install -e .

# 验证
python -c "import skill_seekers; print(skill_seekers.__version__)"
```

---

### "Permission denied"

**原因：** 尝试系统级安装

**解决方案：**
```bash
# 不要使用 sudo
# 替代方案：
pip install --user skill-seekers

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install skill-seekers
```

---

## 抓取问题

### "Rate limit exceeded"

**原因：** 向服务器发送请求过多

**解决方案：**
```bash
# 减速
skill-seekers create <url> --rate-limit 2.0

# 对于 GitHub
export GITHUB_TOKEN=ghp_...
skill-seekers create  owner/repo
```

---

### "No content extracted"

**原因：** CSS 选择器错误

**解决方案：**
```bash
# 查找正确的选择器
curl -s <url> | grep -i 'article\|main\|content'

# 创建带有正确选择器的配置
cat > configs/fix.json << 'EOF'
{
  "name": "my-site",
  "base_url": "https://example.com/",
  "selectors": {
    "main_content": "article"
  }
}
EOF

skill-seekers create --config configs/fix.json
```

**常用选择器：**
| 网站类型 | 选择器 |
|-----------|----------|
| Docusaurus | `article` |
| ReadTheDocs | `[role="main"]` |
| GitBook | `.book-body` |
| MkDocs | `.md-content` |

---

### "Too many pages"

**原因：** 网站大于 max_pages 设置

**解决方案：**
```bash
# 先估算
skill-seekers estimate configs/my-config.json

# 增加限制
skill-seekers create <url> --max-pages 1000

# 或在配置中限制
{
  "max_pages": 1000
}
```

---

### "Connection timeout"

**原因：** 服务器缓慢或网络问题

**解决方案：**
```bash
# 增加超时
skill-seekers create <url> --timeout 60

# 或在配置中
{
  "timeout": 60
}
```

---

### "SSL certificate error"

**原因：** 证书验证失败

**解决方案：**
```bash
# 设置环境变量（生产环境不推荐）
export PYTHONWARNINGS="ignore:Unverified HTTPS request"

# 或在配置中使用 requests 设置
{
  "verify_ssl": false
}
```

---

## 增强问题

### "Enhancement failed: No API key"

**原因：** ANTHROPIC_API_KEY 未设置

**解决方案：**
```bash
# 设置 API key
export ANTHROPIC_API_KEY=sk-ant-...

# 或使用 LOCAL 模式
skill-seekers enhance output/my-skill/ --agent local
```

---

### "Claude Code not found"（LOCAL 模式）

**原因：** Claude Code 未安装

**解决方案：**
```bash
# 安装 Claude Code
# 参见: https://claude.ai/code

# 或使用 API 模式
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers enhance output/my-skill/ --agent api
```

---

### "Enhancement timeout"

**原因：** 增强耗时过长

**解决方案：**
```bash
# 增加超时
skill-seekers enhance output/my-skill/ --timeout 1200

# 使用后台模式
skill-seekers enhance output/my-skill/ --background
skill-seekers enhance-status output/my-skill/ --watch
```

---

### "Workflow not found"

**原因：** 拼写错误或工作流不存在

**解决方案：**
```bash
# 列出可用工作流
skill-seekers workflows list

# 检查拼写
skill-seekers create <source> --enhance-workflow security-focus
```

---

## 打包问题

### "Package validation failed"

**原因：** SKILL.md 缺失或格式错误

**解决方案：**
```bash
# 检查结构
ls output/my-skill/

# 应包含：
# - SKILL.md
# - references/

# 如果需要则重建
skill-seekers create --config my-config --skip-scrape

# 或重新创建
skill-seekers create <source>
```

---

### "Target platform not supported"

**原因：** 目标名称拼写错误

**解决方案：**
```bash
# 列出有效目标
skill-seekers package --help

# 有效目标：
# claude, gemini, openai, langchain, llama-index,
# haystack, pinecone, chroma, weaviate, qdrant, faiss, markdown
```

---

### "Out of memory"

**原因：** Skill 太大，可用内存不足

**解决方案：**
```bash
# 使用流式模式
skill-seekers package output/my-skill/ --streaming

# 减小分块大小
skill-seekers package output/my-skill/ \
  --streaming \
  --streaming-chunk-chars 1000
```

---

## 上传问题

### "Upload failed: Invalid API key"

**原因：** API key 错误或缺失

**解决方案：**
```bash
# Claude
export ANTHROPIC_API_KEY=sk-ant-...

# Gemini
export GOOGLE_API_KEY=AIza...

# OpenAI
export OPENAI_API_KEY=sk-...

# 验证
echo $ANTHROPIC_API_KEY
```

---

### "Upload failed: Network error"

**原因：** 连接问题

**解决方案：**
```bash
# 检查连接
ping api.anthropic.com

# 重试
skill-seekers upload output/my-skill-claude.zip --target claude

# 或通过 Web 界面手动上传
```

---

### "Upload failed: File too large"

**原因：** 包超出平台限制

**解决方案：**
```bash
# 检查大小
ls -lh output/my-skill-claude.zip

# 使用流式模式
skill-seekers package output/my-skill/ --streaming

# 或拆分为更小的 skill
skill-seekers workflows split-config configs/my-config.json
```

---

## GitHub 问题

### "GitHub API rate limit"

**原因：** 未认证请求限制为每小时 60 次

**解决方案：**
```bash
# 设置 token
export GITHUB_TOKEN=ghp_...

# 创建 token: https://github.com/settings/tokens
# 需要权限: repo, read:org（用于私有仓库）
```

---

### "Repository not found"

**原因：** 私有仓库或名称错误

**解决方案：**
```bash
# 检查仓库是否存在
https://github.com/owner/repo

# 为私有仓库设置 token
export GITHUB_TOKEN=ghp_...

# 正确格式
skill-seekers create  owner/repo
```

---

### "No code found"

**原因：** 空仓库或分支错误

**解决方案：**
```bash
# 检查仓库是否有代码

# 在配置中指定分支
{
  "type": "github",
  "repo": "owner/repo",
  "branch": "main"
}
```

---

## PDF 问题

### "PDF is encrypted"

**原因：** 受密码保护的 PDF

**解决方案：**
```bash
# 在配置中添加密码
{
  "type": "pdf",
  "pdf_path": "protected.pdf",
  "password": "secret123"
}
```

---

### "OCR failed"

**原因：** 扫描版 PDF 没有 OCR

**解决方案：**
```bash
# 启用 OCR
skill-seekers create --pdf scanned.pdf --enable-ocr

# 安装 OCR 依赖
pip install skill-seekers[pdf-ocr]
# 系统: apt-get install tesseract-ocr
```

---

## 配置问题

### "Invalid config JSON"

**原因：** 配置文件语法错误

**解决方案：**
```bash
# 验证 JSON
python -m json.tool configs/my-config.json

# 或使用在线验证器
# jsonlint.com
```

---

### "Config not found"

**原因：** 路径错误或文件缺失

**解决方案：**
```bash
# 检查文件是否存在
ls configs/my-config.json

# 使用绝对路径
skill-seekers create --config /full/path/to/config.json

# 或列出可用配置
skill-seekers estimate --all
```

---

## 性能问题

### "Scraping is too slow"

**解决方案：**
```bash
# 使用异步模式
skill-seekers create <url> --async --workers 5

# 降低速率限制（用于你自己的服务器）
skill-seekers create <url> --rate-limit 0.1

# 跳过增强
skill-seekers create <url> --enhance-level 0
```

---

### "Out of disk space"

**解决方案：**
```bash
# 检查使用情况
du -sh output/

# 清理旧 skill
rm -rf output/old-skill/

# 使用流式模式
skill-seekers create <url> --streaming
```

---

### "High memory usage"

**解决方案：**
```bash
# 使用流式模式
skill-seekers create <url> --streaming
skill-seekers package output/my-skill/ --streaming

# 减少工作者数
skill-seekers create <url> --workers 1

# 限制页面数
skill-seekers create <url> --max-pages 100
```

---

## 获取帮助

### 调试模式

```bash
# 启用详细日志
skill-seekers create <source> --verbose

# 或环境变量
export SKILL_SEEKERS_DEBUG=1
```

### 查看日志

```bash
# 启用文件日志
export SKILL_SEEKERS_LOG_FILE=/tmp/skill-seekers.log

# 追踪日志
tail -f /tmp/skill-seekers.log
```

### 创建最小可复现示例

```bash
# 创建测试配置
cat > test-config.json << 'EOF'
{
  "name": "test",
  "base_url": "https://example.com/",
  "max_pages": 5
}
EOF

# 使用调试运行
skill-seekers create --config test-config.json --verbose --dry-run
```

---

## 报告问题

如果这些解决方案都不起作用：

1. **收集信息：**
   ```bash
   skill-seekers --version
   python --version
   pip show skill-seekers
   ```

2. **启用调试：**
   ```bash
   skill-seekers <command> --verbose 2>&1 | tee debug.log
   ```

3. **创建 issue：**
   - https://github.com/yusufkaraaslan/Skill_Seekers/issues
   - 包含：错误消息、使用的命令、调试日志

---

## 错误参考

| 错误代码 | 含义 | 解决方案 |
|------------|---------|----------|
| `E001` | 配置未找到 | 检查路径 |
| `E002` | 无效配置 | 验证 JSON |
| `E003` | 网络错误 | 检查连接 |
| `E004` | 速率限制 | 减速或使用 token |
| `E005` | 抓取失败 | 检查选择器 |
| `E006` | 增强失败 | 检查 API key |
| `E007` | 打包失败 | 检查 skill 结构 |
| `E008` | 上传失败 | 检查 API key |

---

## 仍然卡住？

- **文档：** https://skillseekersweb.com/
- **GitHub Issues：** https://github.com/yusufkaraaslan/Skill_Seekers/issues
- **Discussions：** 分享你的使用场景

---

*Last updated: 2026-02-16*
