# 抓取指南

> **Skill Seekers v3.6.0**
> **所有抓取选项的完整指南**

---

## 概述

Skill Seekers 可以从四种类型的来源中提取知识：

| 来源 | 命令 | 适用于 |
|--------|---------|----------|
| **文档** | `create <url>` | 网页文档、教程、API 参考 |
| **GitHub** | `create <repo>` | 源代码、issues、releases |
| **PDF** | `create <file.pdf>` | 手册、论文、报告 |
| **本地** | `create <./path>` | 你的项目、内部代码 |

---

## 文档抓取

### 基本用法

```bash
# 自动检测并抓取
skill-seekers create https://docs.react.dev/

# 使用自定义名称
skill-seekers create https://docs.react.dev/ --name react-docs

# 使用描述
skill-seekers create https://docs.react.dev/ \
  --description "React JavaScript library documentation"
```

### 使用预设配置

```bash
# 列出可用预设
skill-seekers estimate --all

# 使用预设
skill-seekers create --config react
skill-seekers create --config django
skill-seekers create --config fastapi
```

**可用预设：** 查看仓库中的 `configs/` 目录。

### 自定义配置

```bash
# 创建配置文件
cat > configs/my-docs.json << 'EOF'
{
  "name": "my-framework",
  "base_url": "https://docs.example.com/",
  "description": "My framework documentation",
  "max_pages": 200,
  "rate_limit": 0.5,
  "selectors": {
    "main_content": "article",
    "title": "h1"
  },
  "url_patterns": {
    "include": ["/docs/", "/api/"],
    "exclude": ["/blog/", "/search"]
  }
}
EOF

# 使用配置
skill-seekers create --config configs/my-docs.json
```

查看 [Config Format](../reference/CONFIG_FORMAT.md) 获取所有选项。

### 高级选项

```bash
# 限制页面数（用于测试）
skill-seekers create <url> --max-pages 50

# 调整速率限制
skill-seekers create <url> --rate-limit 1.0

# 并行工作者（更快）
skill-seekers create <url> --workers 5 --async

# 试运行（预览）
skill-seekers create <url> --dry-run

# 恢复中断的任务
skill-seekers create <url> --resume

# 重新开始（忽略缓存）
skill-seekers create <url> --fresh
```

---

## GitHub 仓库抓取

### 基本用法

```bash
# 通过仓库名称
skill-seekers create facebook/react

# 使用显式标志
skill-seekers create  facebook/react

# 使用自定义名称
skill-seekers create  facebook/react --name react-source
```

### 使用 GitHub Token

```bash
# 设置 token 以获得更高的速率限制
export GITHUB_TOKEN=ghp_...

# 使用 token
skill-seekers create  facebook/react
```

**使用 token 的优势：**
- 每小时 5000 次请求，而非 60 次
- 可访问私有仓库
- 更高的 GraphQL 限制

### 提取内容

| 数据 | 默认 | 禁用标志 |
|------|---------|-----------------|
| 源代码 | ✅ | `--scrape-only` |
| README | ✅ | - |
| Issues | ✅ | `--no-issues` |
| Releases | ✅ | `--no-releases` |
| Changelog | ✅ | `--no-changelog` |

### 控制抓取内容

```bash
# 跳过 issues（更快）
skill-seekers create  facebook/react --no-issues

# 限制 issues 数量
skill-seekers create  facebook/react --max-issues 50

# 仅抓取（不构建）
skill-seekers create  facebook/react --scrape-only

# 非交互模式（CI/CD）
skill-seekers create  facebook/react --non-interactive
```

---

## PDF 提取

### 基本用法

```bash
# 直接文件
skill-seekers create manual.pdf --name product-manual

# 使用显式命令
skill-seekers create --pdf manual.pdf --name docs
```

### 扫描版 PDF 的 OCR

```bash
# 启用 OCR
skill-seekers create --pdf scanned.pdf --enable-ocr
```

**要求：**
```bash
pip install skill-seekers[pdf-ocr]
# 还需要: tesseract-ocr（系统包）
```

### 受密码保护的 PDF

```bash
# 在配置文件中
{
  "name": "secure-docs",
  "pdf_path": "protected.pdf",
  "password": "secret123"
}
```

### 页面范围

```bash
# 提取特定页面（通过配置）
{
  "pdf_path": "manual.pdf",
  "page_range": [1, 100]
}
```

---

## 本地代码库分析

### 基本用法

```bash
# 当前目录
skill-seekers create .

# 特定目录
skill-seekers create ./my-project

# 使用显式命令
skill-seekers scan  ./my-project
```

### 分析预设

```bash
# 快速分析（1-2 分钟）
skill-seekers scan  ./my-project --preset quick

# 标准分析（5-10 分钟）- 默认
skill-seekers scan  ./my-project --preset standard

# 全面分析（20-60 分钟）
skill-seekers scan  ./my-project --preset comprehensive
```

### 分析内容

| 功能 | 快速 | 标准 | 全面 |
|---------|-------|----------|---------------|
| 代码结构 | ✅ | ✅ | ✅ |
| API 提取 | ✅ | ✅ | ✅ |
| 注释 | - | ✅ | ✅ |
| 模式 | - | ✅ | ✅ |
| 测试示例 | - | - | ✅ |
| 操作指南 | - | - | ✅ |
| 配置模式 | - | - | ✅ |

### 语言过滤

```bash
# 特定语言
skill-seekers scan  ./my-project \
  --languages Python,JavaScript

# 文件模式
skill-seekers scan  ./my-project \
  --file-patterns "*.py,*.js"
```

### 跳过功能

```bash
# 跳过重型功能
skill-seekers scan  ./my-project \
  --skip-dependency-graph \
  --skip-patterns \
  --skip-test-examples
```

---

## 常见抓取模式

### 模式 1：先测试

```bash
# 试运行预览
skill-seekers create <source> --dry-run

# 小规模测试抓取
skill-seekers create <source> --max-pages 10

# 完整抓取
skill-seekers create <source>
```

### 模式 2：迭代开发

```bash
# 不增强抓取（快速）
skill-seekers create <source> --enhance-level 0

# 检查输出
ls output/my-skill/
cat output/my-skill/SKILL.md

# 稍后增强
skill-seekers enhance output/my-skill/
```

### 模式 3：并行处理

```bash
# 快速异步抓取
skill-seekers create <url> --async --workers 5

# 更快（注意速率限制）
skill-seekers create <url> --async --workers 10 --rate-limit 0.2
```

### 模式 4：恢复能力

```bash
# 开始抓取
skill-seekers create <source>
# ...中断...

# 稍后恢复
skill-seekers resume --list
skill-seekers resume <job-id>
```

---

## 抓取故障排除

### "未提取到内容"

**问题：** CSS 选择器错误

**解决方案：**
```bash
# 查找正确的选择器
curl -s <url> | grep -i 'article\|main\|content'

# 更新配置
{
  "selectors": {
    "main_content": "div.content"
  }
}
```

### "超出速率限制"

**问题：** 请求过多

**解决方案：**
```bash
# 减速
skill-seekers create <url> --rate-limit 2.0

# 或对 GitHub 仓库使用 token
export GITHUB_TOKEN=ghp_...
```

### "页面过多"

**问题：** 网站比预期大

**解决方案：**
```bash
# 先估算
skill-seekers estimate configs/my-config.json

# 限制页面数
skill-seekers create <url> --max-pages 100

# 调整 URL 模式
{
  "url_patterns": {
    "exclude": ["/blog/", "/archive/", "/search"]
  }
}
```

### "内存错误"

**问题：** 网站太大，内存不足

**解决方案：**
```bash
# 使用流式模式
skill-seekers create <url> --streaming

# 或更小的分块
skill-seekers create <url> --chunk-tokens 500
```

---

## 性能提示

| 提示 | 命令 | 影响 |
|-----|---------|--------|
| 使用预设 | `--config react` | 更快的设置 |
| 异步模式 | `--async --workers 5` | 快 3-5 倍 |
| 跳过增强 | `--enhance-level 0` | 跳过 60 秒 |
| 使用缓存 | `--skip-scrape` | 即时重建 |
| 恢复 | `--resume` | 继续中断的任务 |

---

## 下一步

- [增强指南](03-enhancement.md) - 提升 skill 质量
- [打包指南](04-packaging.md) - 导出到平台
- [Config Format](../reference/CONFIG_FORMAT.md) - 高级配置
