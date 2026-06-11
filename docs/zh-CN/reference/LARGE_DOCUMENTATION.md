# 处理大型文档站点（10K+ 页面）

使用 Skill Seeker 抓取和管理大型文档站点的完整指南。

---

## 目录

- [何时拆分文档](#何时拆分文档)
- [拆分策略](#拆分策略)
- [快速开始](#快速开始)
- [详细工作流](#详细工作流)
- [最佳实践](#最佳实践)
- [示例](#示例)
- [故障排除](#故障排除)

---

## 何时拆分文档

### 规模指南

| 文档规模 | 建议 | 策略 |
|---------|------|------|
| < 5,000 页 | **单个技能** | 无需拆分 |
| 5,000 - 10,000 页 | **考虑拆分** | 按类别 |
| 10,000 - 30,000 页 | **建议拆分** | 路由器 + 类别 |
| 30,000+ 页 | **强烈建议拆分** | 路由器 + 类别 |

### 为什么要拆分大型文档？

**优势：**
- ✅ 抓取更快（并行执行）
- ✅ 技能更聚焦（Claude 表现更好）
- ✅ 维护更容易（一次更新一个主题）
- ✅ 用户体验更佳（回答更精准）
- ✅ 避免上下文窗口限制

**权衡：**
- ⚠️ 需要管理多个技能
- ⚠️ 初始设置更复杂
- ⚠️ 路由器会额外增加一个技能

---

## 拆分策略

### 1. **不拆分**（一个大技能）
**适用于：** 中小型文档（< 5K 页）

```bash
# Just use the config as-is
skill-seekers create --config configs/react.json
```

**优点：** 简单，只需维护一个技能
**缺点：** 大型文档可能很慢，可能触及限制

---

### 2. **按类别拆分**（多个聚焦技能）
**适用于：** 5K-15K 页且主题划分清晰的文档

```bash
# Auto-split by categories
python -m skill_seekers.cli.split_config configs/godot.json --strategy category

# Creates:
# - godot-scripting.json
# - godot-2d.json
# - godot-3d.json
# - godot-physics.json
# - etc.
```

**优点：** 技能聚焦，划分清晰
**缺点：** 用户必须知道该使用哪个技能

---

### 3. **路由器 + 类别**（智能枢纽）⭐ 推荐
**适用于：** 10K+ 页面，提供最佳用户体验

```bash
# Create router + sub-skills
python -m skill_seekers.cli.split_config configs/godot.json --strategy router

# Creates:
# - godot.json (router/hub)
# - godot-scripting.json
# - godot-2d.json
# - etc.
```

**优点：** 兼具两者优势，智能路由，自然的用户体验
**缺点：** 设置稍微复杂一些

---

### 4. **按大小拆分**
**适用于：** 没有清晰类别划分的文档

```bash
# Split every 5000 pages
python -m skill_seekers.cli.split_config configs/bigdocs.json --strategy size --target-pages 5000

# Creates:
# - bigdocs-part1.json
# - bigdocs-part2.json
# - bigdocs-part3.json
# - etc.
```

**优点：** 简单、可预测
**缺点：** 可能把相关主题拆开

---

## 快速开始

### 方案 1：自动（推荐）

```bash
# 1. Create config
skill-seekers create --interactive
# Name: godot
# URL: https://docs.godotengine.org
# ... fill in prompts ...

# 2. Estimate pages (discovers it's large)
skill-seekers estimate configs/godot.json
# Output: ⚠️  40,000 pages detected - splitting recommended

# 3. Auto-split with router
python -m skill_seekers.cli.split_config configs/godot.json --strategy router

# 4. Scrape all sub-skills
for config in configs/godot-*.json; do
  skill-seekers create --config $config &
done
wait

# 5. Generate router
skill-seekers create configs/godot-*.json

# 6. Package all
skill-seekers package output/godot*/

# 7. Upload all .zip files to Claude
```

---

### 方案 2：手动控制

```bash
# 1. Define split in config
nano configs/godot.json

# Add:
{
  "split_strategy": "router",
  "split_config": {
    "target_pages_per_skill": 5000,
    "create_router": true,
    "split_by_categories": ["scripting", "2d", "3d", "physics"]
  }
}

# 2. Split
skill-seekers create configs/godot.json

# 3. Continue as above...
```

---

## 详细工作流

### 工作流 1：路由器 + 类别（40K 页面）

**场景：** Godot 文档（40,000 页）

**第 1 步：估算**
```bash
skill-seekers estimate configs/godot.json

# Output:
# Estimated: 40,000 pages
# Recommended: Split into 8 skills (5K each)
```

**第 2 步：拆分配置**
```bash
python -m skill_seekers.cli.split_config configs/godot.json --strategy router --target-pages 5000

# Creates:
# configs/godot.json (router)
# configs/godot-scripting.json (5K pages)
# configs/godot-2d.json (8K pages)
# configs/godot-3d.json (10K pages)
# configs/godot-physics.json (6K pages)
# configs/godot-shaders.json (11K pages)
```

**第 3 步：抓取子技能（并行）**
```bash
# Open multiple terminals or use background jobs
skill-seekers create --config configs/godot-scripting.json &
skill-seekers create --config configs/godot-2d.json &
skill-seekers create --config configs/godot-3d.json &
skill-seekers create --config configs/godot-physics.json &
skill-seekers create --config configs/godot-shaders.json &

# Wait for all to complete
wait

# Time: 4-8 hours (parallel) vs 20-40 hours (sequential)
```

**第 4 步：生成路由器**
```bash
skill-seekers create configs/godot-*.json

# Creates:
# output/godot/SKILL.md (router skill)
```

**第 5 步：全部打包**
```bash
skill-seekers package output/godot*/

# Creates:
# output/godot.zip (router)
# output/godot-scripting.zip
# output/godot-2d.zip
# output/godot-3d.zip
# output/godot-physics.zip
# output/godot-shaders.zip
```

**第 6 步：上传到 Claude**
将全部 6 个 .zip 文件上传到 Claude。路由器会智能地将查询导向正确的子技能！

---

### 工作流 2：仅按类别拆分（15K 页面）

**场景：** Vue.js 文档（15,000 页）

**无需路由器——只要聚焦的技能：**

```bash
# 1. Split
python -m skill_seekers.cli.split_config configs/vue.json --strategy category

# 2. Scrape each
for config in configs/vue-*.json; do
  skill-seekers create --config $config
done

# 3. Package
skill-seekers package output/vue*/

# 4. Upload all to Claude
```

**结果：** 5 个聚焦的 Vue 技能（组件、响应式、路由等）

---

## 最佳实践

### 1. **明智地选择目标大小**

```bash
# Small focused skills (3K-5K pages) - more skills, very focused
python -m skill_seekers.cli.split_config config.json --target-pages 3000

# Medium skills (5K-8K pages) - balanced (RECOMMENDED)
python -m skill_seekers.cli.split_config config.json --target-pages 5000

# Larger skills (8K-10K pages) - fewer skills, broader
python -m skill_seekers.cli.split_config config.json --target-pages 8000
```

### 2. **使用并行抓取**

```bash
# Serial (slow - 40 hours)
for config in configs/godot-*.json; do
  skill-seekers create --config $config
done

# Parallel (fast - 8 hours) ⭐
for config in configs/godot-*.json; do
  skill-seekers create --config $config &
done
wait
```

### 3. **完整抓取前先测试**

```bash
# Test with limited pages first
nano configs/godot-2d.json
# Set: "max_pages": 50

skill-seekers create --config configs/godot-2d.json

# If output looks good, increase to full
```

### 4. **长时间抓取使用检查点**

```bash
# Enable checkpoints in config
{
  "checkpoint": {
    "enabled": true,
    "interval": 1000
  }
}

# If scrape fails, resume
skill-seekers create --config config.json --resume
```

---

## 示例

### 示例 1：AWS 文档（假设 50K 页面）

```bash
# 1. Split by AWS services
python -m skill_seekers.cli.split_config configs/aws.json --strategy router --target-pages 5000

# Creates ~10 skills:
# - aws (router)
# - aws-compute (EC2, Lambda)
# - aws-storage (S3, EBS)
# - aws-database (RDS, DynamoDB)
# - etc.

# 2. Scrape in parallel (overnight)
# 3. Upload all skills to Claude
# 4. User asks "How do I create an S3 bucket?"
# 5. Router activates aws-storage skill
# 6. Focused, accurate answer!
```

### 示例 2：Microsoft 文档（100K+ 页面）

```bash
# Too large even with splitting - use selective categories

# Only scrape key topics
python -m skill_seekers.cli.split_config configs/microsoft.json --strategy category

# Edit configs to include only:
# - microsoft-azure (Azure docs only)
# - microsoft-dotnet (.NET docs only)
# - microsoft-typescript (TS docs only)

# Skip less relevant sections
```

---

## 故障排除

### 问题："拆分产生了太多技能"

**解决方案：** 增大目标大小或合并类别

```bash
# Instead of 5K per skill, use 8K
python -m skill_seekers.cli.split_config config.json --target-pages 8000

# Or manually combine categories in config
```

### 问题："路由器路由不正确"

**解决方案：** 检查路由器 SKILL.md 中的路由关键词

```bash
# Review router
cat output/godot/SKILL.md

# Update keywords if needed
nano output/godot/SKILL.md
```

### 问题："并行抓取失败"

**解决方案：** 降低并行度或检查速率限制

```bash
# Scrape 2-3 at a time instead of all
skill-seekers create --config config1.json &
skill-seekers create --config config2.json &
wait

skill-seekers create --config config3.json &
skill-seekers create --config config4.json &
wait
```

---

## 总结

**对于 40K+ 页面的文档：**

1. ✅ **先估算**：`skill-seekers estimate config.json`
2. ✅ **用路由器拆分**：`python -m skill_seekers.cli.split_config config.json --strategy router`
3. ✅ **并行抓取**：多个终端或后台任务
4. ✅ **生成路由器**：`skill-seekers create configs/*-*.json`
5. ✅ **全部打包**：`skill-seekers package output/*/`
6. ✅ **上传到 Claude**：所有 .zip 文件

**结果：** 智能、快速、聚焦且无缝协作的技能！

---

**有问题？请参阅：**
- [主 README](../README.md)
- [MCP 设置指南](MCP_SETUP.md)
- [增强指南](ENHANCEMENT.md)
