# 文档架构

> **Skill Seekers 文档的组织方式（v3.6.0 - 18 种来源类型）**

---

## 理念

我们的文档遵循以下原则：

1. **渐进式披露** — 从简单开始，按需增加复杂度
2. **任务导向** — 按用户想要完成的任务来组织
3. **单一事实来源** — 每个主题只有一个权威参考
4. **反映当前版本** — 始终反映最新版本

---

## 目录结构

```
docs/
├── README.md              # 入口 - 导航中心
├── ARCHITECTURE.md        # 本文档
│
├── getting-started/       # 新用户（最低认知负荷）
│   ├── 01-installation.md
│   ├── 02-quick-start.md
│   ├── 03-your-first-skill.md
│   └── 04-next-steps.md
│
├── user-guide/            # 常见任务（实用导向）
│   ├── 01-core-concepts.md
│   ├── 02-scraping.md
│   ├── 03-enhancement.md
│   ├── 04-packaging.md
│   ├── 05-workflows.md
│   └── 06-troubleshooting.md
│
├── reference/             # 技术细节（全面详尽）
│   ├── CLI_REFERENCE.md
│   ├── MCP_REFERENCE.md
│   ├── CONFIG_FORMAT.md
│   └── ENVIRONMENT_VARIABLES.md
│
└── advanced/              # 高级用户（专业化）
    ├── mcp-server.md
    ├── mcp-tools.md
    ├── custom-workflows.md
    └── multi-source.md
```

---

## 分类指南

### 入门指南 (Getting Started)

**目的：** 让新用户快速获得首次成功

**特点：**
- 最低前置要求
- 分步说明
- 可直接复制粘贴的命令
- 截图/输出示例

**文件：**
- `01-installation.md` - 安装工具
- `02-quick-start.md` - 3 条命令创建第一个 skill
- `03-your-first-skill.md` - 完整演练
- `04-next-steps.md` - 首次成功后的去向

---

### 用户指南 (User Guide)

**目的：** 教授常见任务和概念

**特点：**
- 任务导向
- 实用示例
- 最佳实践
- 常见模式

**文件：**
- `01-core-concepts.md` - 工作原理
- `02-scraping.md` - 所有抓取选项
- `03-enhancement.md` - AI 增强
- `04-packaging.md` - 平台导出
- `05-workflows.md` - 工作流预设
- `06-troubleshooting.md` - 问题排查

---

### 参考文档 (Reference)

**目的：** 权威的技术信息

**特点：**
- 全面详尽
- 精确准确
- 便于查阅
- 始终准确

**文件：**
- `CLI_REFERENCE.md` - 全部 20 个 CLI 命令
- `MCP_REFERENCE.md` - 26 个 MCP 工具
- `CONFIG_FORMAT.md` - JSON schema
- `ENVIRONMENT_VARIABLES.md` - 所有环境变量

---

### 高级主题 (Advanced)

**目的：** 面向高级用户的专门主题

**特点：**
- 假定具备基础知识
- 深入探讨
- 复杂场景
- 集成主题

**文件：**
- `mcp-server.md` - MCP server 设置
- `mcp-tools.md` - 高级 MCP 用法
- `custom-workflows.md` - 创建工作流
- `multi-source.md` - 统一抓取

---

## 命名规范

### 文件

- **getting-started:** `01-topic.md`（编号表示顺序）
- **user-guide:** `01-topic.md`（编号表示顺序）
- **reference:** `TOPIC_REFERENCE.md`（大写，描述性强）
- **advanced:** `topic.md`（小写，具体明确）

### 标题

- H1: 带版本的标题
- H2: 主要章节
- H3: 子章节
- H4: 细节

示例：
```markdown
# Topic Guide

> **Skill Seekers v3.6.0**

## Major Section

### Subsection

#### Detail
```

---

## 交叉引用

使用相对路径链接到相关文档：

```markdown
<!-- 同一目录内 -->
See [Troubleshooting](06-troubleshooting.md)

<!-- 向上进入 reference 目录 -->
See [CLI Reference](../reference/CLI_REFERENCE.md)

<!-- 向上两级（到根目录） -->
See [Contributing](../../CONTRIBUTING.md)
```

---

## 维护

### 保持文档最新

1. **随代码更新** — 文档必须与实现保持一致
2. **标题中的版本** — 保持版本最新
3. **最后更新日期** — 追踪时效性
4. **废弃旧文件** — 不要删除，而是重定向

### 审阅清单

提交文档前：

- [ ] 命令确实可用（已测试）
- [ ] 没有记录不存在的命令
- [ ] 链接可用
- [ ] 版本号正确
- [ ] 日期已更新

---

## 添加新文档

### 新用户指南

1. 添加到 `user-guide/` 并使用下一个编号
2. 更新 `docs/README.md` 导航
3. 添加到目录
4. 从相关指南中链接

### 新参考文档

1. 添加到 `reference/` 并带有 `_REFERENCE` 后缀
2. 更新 `docs/README.md` 导航
3. 从用户指南链接
4. 如相关，添加到 troubleshooting

### 新高级主题

1. 添加到 `advanced/` 并使用描述性名称
2. 更新 `docs/README.md` 导航
3. 从适当的用户指南链接

---

## 废弃策略

当内容过时时：

1. **不要立即删除** — 会破坏外部链接
2. **添加废弃通知**：
   ```markdown
   > ⚠️ **已废弃**：本文档已过时。
   > 请参阅 [New Guide](path/to/new.md) 获取当前信息。
   ```
3. **6 个月后移至存档**：
   ```
   docs/archive/legacy/
   ```
4. **更新导航** 以移除废弃链接

---

## 贡献

### 文档修改

1. 编辑相关文件
2. 测试所有命令
3. 更新版本/日期
4. 提交 PR

### 新文档

1. 选择合适的分类
2. 遵循命名规范
3. 添加到 README.md
4. 交叉链接相关文档

---

## 参见

- [文档 README](README.md) - 导航中心
- [贡献指南](../../CONTRIBUTING.md) - 如何贡献
- [仓库 README](../README.md) - 项目概览
