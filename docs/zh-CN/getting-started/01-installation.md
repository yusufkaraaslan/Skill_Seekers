# 安装指南

> **Skill Seekers v3.6.0**

在 5 分钟内完成 Skill Seekers 的安装并运行。

---

## 系统要求

| 要求 | 最低配置 | 推荐配置 |
|-------------|---------|-------------|
| **Python** | 3.10 | 3.11 或 3.12 |
| **内存** | 4 GB | 8 GB+ |
| **磁盘** | 500 MB | 2 GB+ |
| **操作系统** | Linux, macOS, Windows (WSL) | Linux, macOS |

---

## 快速安装

### 选项 1：pip（推荐）

```bash
# 基础安装
pip install skill-seekers

# 支持所有平台
pip install skill-seekers[all-llms]

# 验证安装
skill-seekers --version
```

### 选项 2：pipx（隔离环境）

```bash
# 如果尚未安装 pipx
pip install pipx
pipx ensurepath

# 安装 skill-seekers
pipx install skill-seekers[all-llms]
```

### 选项 3：开发模式（从源码安装）

```bash
# 克隆仓库
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers

# 以可编辑模式安装
pip install -e ".[all-llms,dev]"

# 验证
skill-seekers --version
```

---

## 安装选项

### 最小安装

仅包含核心功能：

```bash
pip install skill-seekers
```

**包含：**
- 文档抓取
- 基础打包
- 本地增强（Claude Code）

### 完整安装

包含所有功能和平台：

```bash
pip install skill-seekers[all-llms]
```

**包含：**
- Claude AI 支持
- Google Gemini 支持
- OpenAI ChatGPT 支持
- 所有向量数据库
- MCP server
- 云存储（S3, GCS, Azure）

### 自定义安装

仅安装您需要的部分：

```bash
# 仅安装特定平台
pip install skill-seekers[gemini]      # Google Gemini
pip install skill-seekers[openai]      # OpenAI
pip install skill-seekers[minimax]     # MiniMax AI
pip install skill-seekers[chroma]      # ChromaDB

# 安装多个扩展
pip install skill-seekers[gemini,openai,chroma]

# 开发工具
pip install skill-seekers[dev]
```

---

## 可用的扩展包

| 扩展包 | 描述 | 安装命令 |
|-------|-------------|-----------------|
| `gemini` | Google Gemini 支持 | `pip install skill-seekers[gemini]` |
| `openai` | OpenAI ChatGPT 支持 | `pip install skill-seekers[openai]` |
| `mcp` | MCP server | `pip install skill-seekers[mcp]` |
| `video` | YouTube/Vimeo 字幕与元数据 | `pip install skill-seekers[video]` |
| `video-full` | + Whisper 转录与视觉帧 | `pip install skill-seekers[video-full]` |
| `jupyter` | Jupyter Notebook 提取 | `pip install skill-seekers[jupyter]` |
| `ocr` | OCR 支持（扫描版 PDF、视觉帧） | `pip install skill-seekers[ocr]` |
| `confluence` | Confluence wiki 支持 | `pip install skill-seekers[confluence]` |
| `notion` | Notion 页面支持 | `pip install skill-seekers[notion]` |
| `chroma` | ChromaDB 导出 | `pip install skill-seekers[chroma]` |
| `weaviate` | Weaviate 导出 | `pip install skill-seekers[weaviate]` |
| `qdrant` | Qdrant 导出 | `pip install skill-seekers[qdrant]` |
| `faiss` | FAISS 导出 | `pip install skill-seekers[faiss]` |
| `s3` | AWS S3 存储 | `pip install skill-seekers[s3]` |
| `gcs` | Google Cloud Storage | `pip install skill-seekers[gcs]` |
| `azure` | Azure Blob Storage | `pip install skill-seekers[azure]` |
| `embedding` | Embedding server | `pip install skill-seekers[embedding]` |
| `all-llms` | 所有 LLM 平台 | `pip install skill-seekers[all-llms]` |
| `all` | 全部功能 | `pip install skill-seekers[all]` |
| `dev` | 开发工具 | `pip install skill-seekers[dev]` |

---

## 安装后设置

### 1. 配置 API 密钥（可选）

用于 AI 增强和上传：

```bash
# 交互式配置向导
skill-seekers config

# 或设置环境变量
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
```

### 2. 验证安装

```bash
# 检查版本
skill-seekers --version

# 查看所有命令
skill-seekers --help

# 测试配置
skill-seekers config --test
```

### 3. 快速测试

```bash
# 列出可用预设
skill-seekers estimate --all

# 试运行
skill-seekers create https://docs.python.org/3/ --dry-run
```

---

## 平台特定说明

### macOS

```bash
# 使用 Homebrew Python
brew install python@3.12
pip3.12 install skill-seekers[all-llms]

# 或使用 pyenv
pyenv install 3.12
pyenv global 3.12
pip install skill-seekers[all-llms]
```

### Linux (Ubuntu/Debian)

```bash
# 安装 Python 和 pip
sudo apt update
sudo apt install python3-pip python3-venv

# 安装 skill-seekers
pip3 install skill-seekers[all-llms]

# 全局可用
sudo ln -s ~/.local/bin/skill-seekers /usr/local/bin/
```

### Windows

**推荐：** 使用 WSL2

```powershell
# 或直接使用 Windows（PowerShell）
python -m pip install skill-seekers[all-llms]

# 如需添加到 PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:APPDATA\Python\Python312\Scripts", "User")
```

### Docker

```bash
# 拉取镜像
docker pull yusyuss/skill-seekers:latest

# 运行
docker run -it --rm \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/output:/output \
  yusyuss/skill-seekers:latest \
  skill-seekers create https://docs.react.dev/
```

---

## 故障排除

### "command not found: skill-seekers"

```bash
# 将 pip bin 添加到 PATH
export PATH="$HOME/.local/bin:$PATH"

# 或使用 --user 重新安装
pip install --user --force-reinstall skill-seekers
```

### 权限被拒绝

```bash
# 不要对 pip 使用 sudo
# 替代方案：
pip install --user skill-seekers

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install skill-seekers[all-llms]
```

### 导入错误

```bash
# 对于开发安装，确保使用可编辑模式
pip install -e .

# 检查安装
python -c "import skill_seekers; print(skill_seekers.__version__)"
```

### 版本冲突

```bash
# 使用虚拟环境
python3 -m venv skill-seekers-env
source skill-seekers-env/bin/activate
pip install skill-seekers[all-llms]
```

---

## 升级

```bash
# 升级到最新版本
pip install --upgrade skill-seekers

# 升级所有扩展
pip install --upgrade skill-seekers[all-llms]

# 检查当前版本
skill-seekers --version

# 查看更新内容
pip show skill-seekers
```

---

## 卸载

```bash
pip uninstall skill-seekers

# 清理配置（可选）
rm -rf ~/.config/skill-seekers/
rm -rf ~/.cache/skill-seekers/
```

---

## 下一步

- [快速入门指南](02-quick-start.md) - 3 条命令创建第一个 skill
- [你的第一个 Skill](03-your-first-skill.md) - 完整演练

---

## 获取帮助

```bash
# 命令帮助
skill-seekers --help
skill-seekers create --help

# 文档
# https://github.com/yusufkaraaslan/Skill_Seekers/tree/main/docs

# Issues
# https://github.com/yusufkaraaslan/Skill_Seekers/issues
```
