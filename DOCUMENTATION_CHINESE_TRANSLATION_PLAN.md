# Chinese Translation Plan - Skill Seekers Documentation

> **Issue Reference:** #260 - Requesting community help for translations  
> **Strategy:** Automated + Community Review  
> **Structure:** Option 1 - Parallel Structure (`docs/zh-CN/`)  
> **Scope:** All Documentation  
> **Sync Policy:** Every release must sync Chinese docs

---

## Overview

Complete Chinese translation of all Skill Seekers documentation using automated translation with community review.

---

## Directory Structure

```
docs/
├── README.md                           # English (source of truth)
├── ARCHITECTURE.md
├── getting-started/
├── user-guide/
├── reference/
├── advanced/
│
└── zh-CN/                              # Chinese translations
    ├── README.md                       # Chinese entry point
    ├── ARCHITECTURE.md
    ├── getting-started/
    │   ├── 01-installation.md
    │   ├── 02-quick-start.md
    │   ├── 03-your-first-skill.md
    │   └── 04-next-steps.md
    ├── user-guide/
    │   ├── 01-core-concepts.md
    │   ├── 02-scraping.md
    │   ├── 03-enhancement.md
    │   ├── 04-packaging.md
    │   ├── 05-workflows.md
    │   └── 06-troubleshooting.md
    ├── reference/
    │   ├── CLI_REFERENCE.md
    │   ├── MCP_REFERENCE.md
    │   ├── CONFIG_FORMAT.md
    │   └── ENVIRONMENT_VARIABLES.md
    └── advanced/
        ├── mcp-server.md
        ├── mcp-tools.md
        ├── custom-workflows.md
        └── multi-source.md
```

**Total:** 18 files to translate

---

## Translation Workflow

### Step 1: Automated Translation (CI/CD)

```yaml
# .github/workflows/translate-docs.yml
name: Translate Documentation

on:
  push:
    paths:
      - 'docs/**/*.md'
      - '!docs/zh-CN/**'
  workflow_dispatch:

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Detect changed files
        id: changed
        run: |
          # Find changed English docs
          CHANGED=$(git diff --name-only HEAD~1 HEAD | grep "^docs/" | grep -v "^docs/zh-CN/" | grep "\.md$")
          echo "files=$CHANGED" >> $GITHUB_OUTPUT
      
      - name: Translate to Chinese
        if: steps.changed.outputs.files != ''
        run: |
          for file in ${{ steps.changed.outputs.files }}; do
            # Use LLM API for translation
            python scripts/translate_doc.py "$file" --target-lang zh-CN
          done
      
      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: "[Auto] Chinese Translation Update"
          body: |
            Automated translation of changed documentation.
            
            **Needs Review:** Community review required before merge.
            
            Reference: #260
          branch: auto-translate-zh-cn
          labels: translation, zh-CN, needs-review
```

### Step 2: Community Review (via Issue #260)

```markdown
## Translation Review Needed

The following Chinese translations need community review:

| File | Auto-Translated | Reviewer | Status |
|------|-----------------|----------|--------|
| docs/zh-CN/getting-started/02-quick-start.md | @github-actions | @reviewer1 | 🔍 Pending |
| docs/zh-CN/reference/CLI_REFERENCE.md | @github-actions | @reviewer2 | 🔍 Pending |

**How to Review:**
1. Check out the PR branch
2. Read the Chinese translation
3. Comment with suggested changes
4. Approve when satisfied

**Translation Standards:**
- Keep technical terms in English (CLI, API, JSON)
- Use Simplified Chinese (简体中文)
- Maintain code examples in English
- Preserve all links and formatting
```

### Step 3: Sync Check on Release

```bash
#!/bin/bash
# scripts/check_translation_sync.sh

echo "Checking translation sync..."

for en_file in docs/**/*.md; do
    zh_file="${en_file/docs/docs\/zh-CN}"
    
    if [ ! -f "$zh_file" ]; then
        echo "❌ Missing: $zh_file"
        exit 1
    fi
    
    en_date=$(git log -1 --format=%ct "$en_file")
    zh_date=$(git log -1 --format=%ct "$zh_file")
    
    if [ $en_date -gt $zh_date ]; then
        echo "⚠️  Out of sync: $zh_file (EN updated more recently)"
        exit 1
    fi
done

echo "✅ All translations in sync"
```

---

## Translation Standards

### Header Format

```markdown
<!-- docs/zh-CN/getting-started/02-quick-start.md -->

> **注意：** 本文档是 [Quick Start Guide](../getting-started/02-quick-start.md) 的中文翻译。
> 
> - **最后翻译日期：** 2026-02-16
> - **英文原文版本：** 3.1.0
> - **翻译状态：** ✅ 已审阅 / ⚠️ 待审阅 / 🔴 需更新
>
> 如果本文档与英文版本有冲突，请以英文版本为准。

---

# 快速入门指南

> **Skill Seekers v3.1.0**
> **3 个命令创建您的第一个技能**
```

### Technical Terms

Keep these in English:

| English | Chinese | Keep English? |
|---------|---------|---------------|
| CLI | 命令行界面 | ✅ Yes (use "CLI") |
| API | 应用程序接口 | ✅ Yes (use "API") |
| JSON | - | ✅ Yes |
| YAML | - | ✅ Yes |
| MCP | - | ✅ Yes |
| skill | 技能 | ⚠️ Use "技能 (skill)" first time |
| scraper | 抓取器 | ⚠️ Use "抓取器 (scraper)" first time |
| workflow | 工作流 | ⚠️ Use "工作流 (workflow)" first time |

### Code Examples

Keep code examples in English (they're the same):

```bash
# Chinese doc still shows:
pip install skill-seekers
skill-seekers create https://docs.django.com/
```

### Links

Update links to point to Chinese versions:

```markdown
<!-- English -->
See [Installation Guide](01-installation.md)

<!-- Chinese -->
参见 [安装指南](01-installation.md)
```

---

## Implementation Phases

### Phase 1: Setup (1-2 hours)

- [ ] Create `docs/zh-CN/` directory structure
- [ ] Create translation header template
- [ ] Set up GitHub Actions workflow
- [ ] Create `scripts/translate_doc.py`
- [ ] Update issue #260 with contribution guidelines

### Phase 2: Initial Translation (Automated)

- [ ] Run translation script on all 18 files
- [ ] Create initial PR with all translations
- [ ] Tag community reviewers in issue #260

### Phase 3: Community Review (Ongoing)

- [ ] Review getting-started/ docs (highest priority)
- [ ] Review user-guide/ docs
- [ ] Review reference/ docs
- [ ] Review advanced/ docs

### Phase 4: Maintenance (Continuous)

- [ ] Automated translation on English doc changes
- [ ] PR creation for review
- [ ] Pre-release sync check
- [ ] Monthly review of outdated translations

---

## File Priority & Review Assignment

| Priority | File | Complexity | Reviewers Needed |
|----------|------|------------|------------------|
| P0 | `docs/zh-CN/README.md` | Low | 2 |
| P0 | `docs/zh-CN/getting-started/02-quick-start.md` | Low | 2 |
| P1 | `docs/zh-CN/getting-started/01-installation.md` | Low | 1 |
| P1 | `docs/zh-CN/getting-started/03-your-first-skill.md` | Medium | 2 |
| P1 | `docs/zh-CN/user-guide/06-troubleshooting.md` | Medium | 2 |
| P2 | `docs/zh-CN/user-guide/01-core-concepts.md` | Medium | 1 |
| P2 | `docs/zh-CN/user-guide/02-scraping.md` | High | 2 |
| P2 | `docs/zh-CN/user-guide/03-enhancement.md` | High | 2 |
| P2 | `docs/zh-CN/user-guide/04-packaging.md` | High | 2 |
| P2 | `docs/zh-CN/user-guide/05-workflows.md` | High | 2 |
| P3 | `docs/zh-CN/reference/CLI_REFERENCE.md` | High | 2 |
| P3 | `docs/zh-CN/reference/MCP_REFERENCE.md` | High | 2 |
| P3 | `docs/zh-CN/reference/CONFIG_FORMAT.md` | Medium | 1 |
| P3 | `docs/zh-CN/reference/ENVIRONMENT_VARIABLES.md` | Low | 1 |
| P3 | `docs/zh-CN/advanced/*.md` (4 files) | High | 1 each |

**Total:** 18 files, ~24 reviewer spots

---

## Issue #260 Update Template

```markdown
## 🇨🇳 中文文档翻译 - 招募社区志愿者

### 项目介绍
我们正在将 Skill Seekers 文档翻译成简体中文，需要社区志愿者参与审阅！

### 如何参与

#### 1. 审阅翻译（推荐）
- 查看自动创建的翻译 PR
- 阅读中文文档，提出改进建议
- 确认技术术语翻译准确

#### 2. 直接翻译
- 认领下方列表中的文件
- 基于英文原文进行翻译
- 遵循翻译标准（见下方）

### 待审阅文件

| 文件 | 自动翻译 | 状态 | 认领人 |
|------|----------|------|--------|
| getting-started/02-quick-start.md | ✅ | 🔍 待审阅 | - |
| getting-started/01-installation.md | ✅ | 🔍 待审阅 | - |
| ... | ... | ... | ... |

### 翻译标准

1. **技术术语**：CLI、API、JSON 等保持英文
2. **代码示例**：保持原文（英文）
3. **链接**：指向中文版本
4. **格式**：保留所有 Markdown 格式

### 奖励
- 贡献者将在 README 中致谢
- 优先获得新版本测试权限
- 社区贡献徽章 🏅

---

## 🇨🇳 Chinese Documentation Translation - Call for Volunteers

### Introduction
We're translating Skill Seekers docs to Simplified Chinese and need community reviewers!

### How to Participate

#### 1. Review Translations (Recommended)
- Check auto-generated translation PRs
- Read Chinese docs, suggest improvements
- Verify technical terms are accurate

#### 2. Direct Translation
- Claim a file from the list below
- Translate from English original
- Follow translation standards (see below)

### Files Pending Review

| File | Auto-Translated | Status | Claimed By |
|------|-----------------|--------|------------|
| getting-started/02-quick-start.md | ✅ | 🔍 Pending | - |
| getting-started/01-installation.md | ✅ | 🔍 Pending | - |
| ... | ... | ... | ... |

### Translation Standards

1. **Technical Terms**: Keep CLI, API, JSON in English
2. **Code Examples**: Keep original (English)
3. **Links**: Point to Chinese versions
4. **Format**: Preserve all Markdown formatting

### Rewards
- Contributors acknowledged in README
- Early access to new versions
- Community contributor badge 🏅
```

---

## Pre-Release Checklist

Before each release:

- [ ] Run `scripts/check_translation_sync.sh`
- [ ] Ensure all Chinese docs have "翻译状态：✅ 已审阅"
- [ ] Update version numbers in Chinese headers
- [ ] Update "最后翻译日期" in all Chinese docs

---

## Tools & Scripts

### `scripts/translate_doc.py`

```python
#!/usr/bin/env python3
"""
Translate documentation using LLM API.
Usage: python scripts/translate_doc.py <file> --target-lang zh-CN
"""

import argparse
import os
from pathlib import Path


def translate_file(input_path: str, target_lang: str = "zh-CN"):
    """Translate a documentation file."""
    input_file = Path(input_path)
    
    # Read English content
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine output path
    relative_path = input_file.relative_to("docs")
    output_file = Path("docs") / target_lang / relative_path
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # TODO: Call LLM API for translation
    # For now, create placeholder with header
    header = f"""> **注意：** 本文档是 [{input_file.name}]({input_file.name}) 的中文翻译。
> 
> - **最后翻译日期：** 2026-02-16
> - **英文原文版本：** 3.1.0
> - **翻译状态：** ⚠️ 待审阅
>
> 如果本文档与英文版本有冲突，请以英文版本为准。

---

"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(content)  # Placeholder: should be translated
    
    print(f"✅ Created: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="File to translate")
    parser.add_argument("--target-lang", default="zh-CN", help="Target language")
    args = parser.parse_args()
    
    translate_file(args.file, args.target_lang)
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Files Translated | 18/18 (100%) |
| Reviewed by Community | 18/18 (100%) |
| Sync Delay | < 1 week after English update |
| Translation Accuracy | > 95% (community verified) |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Setup | 1-2 hours | Directory structure, CI/CD |
| Initial Translation | 1 day | All 18 files translated |
| Community Review | 2-4 weeks | All files reviewed |
| Maintenance | Ongoing | Continuous sync |

---

*Ready to implement. Review this plan and confirm to proceed.*
