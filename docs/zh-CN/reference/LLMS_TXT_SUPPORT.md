# llms.txt 支持

## 概述

Skill_Seekers 现在会在可用时自动检测并使用 llms.txt 文件，使文档摄取速度提升 10 倍。

## 什么是 llms.txt？

llms.txt 约定是一个日益普及的标准，文档站点据此提供预先格式化、可直接供 LLM 使用的 markdown 文件：

- `llms-full.txt` - 完整文档
- `llms.txt` - 标准均衡版本
- `llms-small.txt` - 快速参考

## 工作原理

1. 在进行 HTML 抓取之前，Skill_Seekers 会先检查 llms.txt 文件
2. 如果找到，则下载并解析该 markdown
3. 如果未找到，则回退到 HTML 抓取
4. 无需任何配置更改

## 配置

### 自动检测（推荐）

无需更改配置。正常运行即可：

```bash
skill-seekers create --config configs/hono.json
```

### 显式 URL

也可以选择显式指定 llms.txt URL：

```json
{
  "name": "hono",
  "llms_txt_url": "https://hono.dev/llms-full.txt",
  "base_url": "https://hono.dev/docs"
}
```

## 性能对比

| 方法 | 耗时 | 请求数 |
|------|------|--------|
| HTML 抓取（20 页） | 20-60 秒 | 20+ |
| llms.txt | < 5 秒 | 1 |

## 支持的站点

已知提供 llms.txt 的站点：

- Hono: https://hono.dev/llms-full.txt
- （更多站点有待发现）

## 回退行为

如果 llms.txt 下载或解析失败，会自动回退到 HTML 抓取，无需用户干预。
