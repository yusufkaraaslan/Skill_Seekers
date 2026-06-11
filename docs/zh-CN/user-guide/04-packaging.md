# 打包指南

> **Skill Seekers v3.6.0**
> **将 skill 导出到 AI 平台和向量数据库**

---

## 概述

打包将你的 skill 目录转换为特定于平台的格式：

```
output/my-skill/ ──▶ 打包器 ──▶ output/my-skill-{platform}.{format}
    ↓                                ↓
(SKILL.md +        平台特定的      (ZIP, tar.gz,
 references)        格式化          目录,
                                     FAISS 索引)
```

---

## 支持的平台

| 平台 | 格式 | 扩展名 | 适用于 |
|----------|--------|-----------|----------|
| **Claude AI** | ZIP + YAML | `.zip` | Claude Code, Claude API |
| **Google Gemini** | tar.gz | `.tar.gz` | Gemini skill |
| **OpenAI ChatGPT** | ZIP + Vector | `.zip` | Custom GPTs |
| **OpenCode** | Directory | directory | OpenCode agent |
| **Kimi** | ZIP | `.zip` | Kimi 平台 |
| **DeepSeek** | ZIP | `.zip` | DeepSeek 平台 |
| **Qwen** | ZIP | `.zip` | Qwen 平台 |
| **OpenRouter** | ZIP | `.zip` | OpenRouter |
| **Together AI** | ZIP | `.zip` | Together AI |
| **Fireworks AI** | ZIP | `.zip` | Fireworks AI |
| **LangChain** | Documents | directory | RAG 管道 |
| **LlamaIndex** | TextNodes | directory | 查询引擎 |
| **Haystack** | Documents | directory | 企业级 RAG |
| **Pinecone** | Markdown | `.zip` | 向量上传 |
| **ChromaDB** | Collection | `.zip` | 本地向量数据库 |
| **Weaviate** | Objects | `.zip` | 向量数据库 |
| **Qdrant** | Points | `.zip` | 向量数据库 |
| **FAISS** | Index | `.faiss` | 本地相似性搜索 |
| **Markdown** | ZIP | `.zip` | 通用导出 |
| **Cursor** | .cursorrules | file | IDE AI 上下文 |
| **Windsurf** | .windsurfrules | file | IDE AI 上下文 |
| **Cline** | .clinerules | file | VS Code AI |

---

## 基础打包

### 为 Claude 打包（默认）

```bash
# 默认打包
skill-seekers package output/my-skill/

# 显式指定目标
skill-seekers package output/my-skill/ --target claude

# 输出: output/my-skill-claude.zip
```

### 为其他平台打包

```bash
# Google Gemini
skill-seekers package output/my-skill/ --target gemini
# 输出: output/my-skill-gemini.tar.gz

# OpenAI
skill-seekers package output/my-skill/ --target openai
# 输出: output/my-skill-openai.zip

# LangChain
skill-seekers package output/my-skill/ --target langchain
# 输出: output/my-skill-langchain/ 目录

# ChromaDB
skill-seekers package output/my-skill/ --target chroma
# 输出: output/my-skill-chroma.zip
```

---

## 多平台打包

### 为所有平台打包

```bash
# 创建 skill
skill-seekers create <source>

# 为多个平台打包
for platform in claude gemini openai langchain; do
  echo "Packaging for $platform..."
  skill-seekers package output/my-skill/ --target $platform
done

# 结果:
# output/my-skill-claude.zip
# output/my-skill-gemini.tar.gz
# output/my-skill-openai.zip
# output/my-skill-langchain/
```

### 批量打包脚本

```bash
#!/bin/bash
SKILL_DIR="output/my-skill"
PLATFORMS="claude gemini openai langchain llama-index chroma"

for platform in $PLATFORMS; do
  echo "▶️ Packaging for $platform..."
  skill-seekers package "$SKILL_DIR" --target "$platform"
  
  if [ $? -eq 0 ]; then
    echo "✅ $platform done"
  else
    echo "❌ $platform failed"
 fi
done

echo "🎉 All platforms packaged!"
```

---

## 打包选项

### 跳过质量检查

```bash
# 跳过验证（更快）
skill-seekers package output/my-skill/ --skip-quality-check
```

### 不打开输出文件夹

```bash
# 打包后阻止打开文件夹
skill-seekers package output/my-skill/ --no-open
```

### 打包后自动上传

```bash
# 打包并上传
export ANTHROPIC_API_KEY=sk-ant-...
skill-seekers package output/my-skill/ --target claude --upload
```

---

## 流式模式

对于非常大的 skill，使用流式模式以减少内存使用：

```bash
# 启用流式模式
skill-seekers package output/large-skill/ --streaming

# 自定义分块大小
skill-seekers package output/large-skill/ \
  --streaming \
  --streaming-chunk-chars 2000 \
  --streaming-overlap-chars 100
```

**何时使用：**
- Skill > 500 页
- 内存有限（< 8GB）
- 批量处理多个 skill

---

## RAG 分块

为检索增强生成（Retrieval-Augmented Generation）优化：

```bash
# 启用语义分块
skill-seekers package output/my-skill/ \
  --target langchain \
  --chunk-for-rag \
  --chunk-tokens 512

# 自定义分块大小
skill-seekers package output/my-skill/ \
  --target chroma \
  --chunk-tokens 256 \
  --chunk-overlap-tokens 50
```

**分块选项：**

| 选项 | 默认值 | 描述 |
|--------|---------|-------------|
| `--chunk-for-rag` | auto | 启用分块 |
| `--chunk-tokens` | 512 | 每个分块的 token 数 |
| `--chunk-overlap-tokens` | 50 | 分块之间的重叠（token） |
| `--no-preserve-code-blocks` | - | 允许分割代码块 |

> **Auto-scaling overlap:** 当 `--chunk-tokens` 设置为非默认值但 `--chunk-overlap-tokens` 保持默认值 (50) 时，重叠会自动缩放为 `max(50, chunk_tokens / 10)`，以在较大的分块中实现更好的上下文保留。

---

## 平台特定详情

### Claude AI

```bash
skill-seekers package output/my-skill/ --target claude
```

**上传：**
```bash
# 自动上传
skill-seekers package output/my-skill/ --target claude --upload

# 手动上传
skill-seekers upload output/my-skill-claude.zip --target claude
```

**格式：**
- ZIP 归档
- 包含 SKILL.md + references/
- 包含 YAML 清单

---

### Google Gemini

```bash
skill-seekers package output/my-skill/ --target gemini
```

**上传：**
```bash
export GOOGLE_API_KEY=AIza...
skill-seekers upload output/my-skill-gemini.tar.gz --target gemini
```

**格式：**
- tar.gz 归档
- 针对 Gemini 格式优化

---

### OpenAI ChatGPT

```bash
skill-seekers package output/my-skill/ --target openai
```

**上传：**
```bash
export OPENAI_API_KEY=sk-...
skill-seekers upload output/my-skill-openai.zip --target openai
```

**格式：**
- 带向量嵌入的 ZIP
- 可用于 Assistants API

---

### LangChain

```bash
skill-seekers package output/my-skill/ --target langchain
```

**用法：**
```python
from langchain.document_loaders import DirectoryLoader

loader = DirectoryLoader("output/my-skill-langchain/")
docs = loader.load()

# 用于 RAG 管道
```

**格式：**
- Document 对象目录
- JSON 元数据

---

### ChromaDB

```bash
skill-seekers package output/my-skill/ --target chroma
```

**上传：**
```bash
# 本地 ChromaDB
skill-seekers upload output/my-skill-chroma.zip --target chroma

# 使用自定义 URL
skill-seekers upload output/my-skill-chroma.zip \
  --target chroma \
  --chroma-url http://localhost:8000
```

**用法：**
```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_collection("my-skill")
```

---

### Weaviate

```bash
skill-seekers package output/my-skill/ --target weaviate
```

**上传：**
```bash
# 本地 Weaviate
skill-seekers upload output/my-skill-weaviate.zip --target weaviate

# Weaviate Cloud
skill-seekers upload output/my-skill-weaviate.zip \
  --target weaviate \
  --use-cloud \
  --cluster-url https://xxx.weaviate.network
```

---

### Cursor IDE

```bash
# 直接安装到 Cursor 的 skills 目录
skill-seekers install-agent output/my-skill/ --agent cursor
```

**结果：** 项目根目录中的 `.cursorrules` 文件。

---

### Windsurf IDE

```bash
skill-seekers install-agent output/my-skill/ --agent windsurf
```

**结果：** 项目根目录中的 `.windsurfrules` 文件。

---

## 质量检查

打包前，skill 会被验证：

```bash
# 检查质量
skill-seekers quality output/my-skill/

# 详细报告
skill-seekers quality output/my-skill/ --report

# 设置最低阈值（低于阈值时以非零退出码退出；不带 --threshold 时
# 该命令仅报告并始终以 0 退出）
skill-seekers quality output/my-skill/ --threshold 7.0
```

**质量指标：**
- SKILL.md 完整性
- 代码示例覆盖率
- 导航结构
- 参考文件组织

---

## 输出结构

### 打包后

```
output/
├── my-skill/                    # 源 skill
│   ├── SKILL.md
│   └── references/
│
├── my-skill-claude.zip          # Claude 包
├── my-skill-gemini.tar.gz       # Gemini 包
├── my-skill-openai.zip          # OpenAI 包
├── my-skill-langchain/          # LangChain 目录
├── my-skill-chroma.zip          # ChromaDB 包
└── my-skill-weaviate.zip        # Weaviate 包
```

---

## 故障排除

### "包验证失败"

**问题：** SKILL.md 缺失或格式错误

**解决方案：**
```bash
# 检查 skill 结构
ls output/my-skill/

# 如果需要则重建
skill-seekers create --config my-config --skip-scrape

# 或重新创建
skill-seekers create <source>
```

### "不支持目标平台"

**问题：** 目标名称拼写错误

**解决方案：**
```bash
# 检查可用目标
skill-seekers package --help

# 常见目标: claude, gemini, openai, langchain, chroma, weaviate
```

### "上传失败"

**问题：** 缺少 API key

**解决方案：**
```bash
# 设置 API key
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...

# 重试
skill-seekers upload output/my-skill-claude.zip --target claude
```

### "内存不足"

**问题：** Skill 太大，内存不足

**解决方案：**
```bash
# 使用流式模式
skill-seekers package output/my-skill/ --streaming

# 更小的分块
skill-seekers package output/my-skill/ --streaming --streaming-chunk-chars 1000
```

---

## 最佳实践

### 1. 一次打包，处处使用

```bash
# 创建一次
skill-seekers create <source>

# 为所有需要的平台打包
for platform in claude gemini langchain; do
  skill-seekers package output/my-skill/ --target $platform
done
```

### 2. 打包前检查质量

```bash
# 先验证
skill-seekers quality output/my-skill/ --threshold 6.0

# 然后打包
skill-seekers package output/my-skill/
```

### 3. 对大型 skill 使用流式模式

```bash
# 自动检测，但可以强制使用
skill-seekers package output/large-skill/ --streaming
```

### 4. 保留原始 Skill 目录

打包后不要删除 `output/my-skill/` —— 你可能需要：
- 为其他平台重新打包
- 应用不同的工作流
- 更新并重新增强

---

## 下一步

- [工作流指南](05-workflows.md) - 打包前应用工作流
- [MCP Reference](../reference/MCP_REFERENCE.md) - 通过 MCP 打包
- [Vector DB Integrations](../../integrations/) - 平台特定指南
