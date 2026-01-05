# AI 技術日報整理指令

## 適用情境

當使用者需要以下協助時使用此指令：
- 每日 AI 技術新聞彙整
- 追蹤 Claude、OpenAI、Gemini、Unsloth 最新動態
- 整理技術部落格與官方公告
- 製作團隊技術週報

---

## 監控目標

### 主要公司/專案

| 公司/專案 | 重點產品 | 關注領域 |
|-----------|----------|----------|
| **Anthropic** | Claude, Claude Code, MCP | 對話模型、Agent、安全性 |
| **OpenAI** | GPT-4, ChatGPT, Sora, o1 | 多模態、推理、API |
| **Google DeepMind** | Gemini, Gemma, AlphaFold | 多模態、科學研究 |
| **Unsloth** | Unsloth Fine-tuning | 高效微調、LoRA、量化 |

---

## 資訊來源

### 官方來源 (最高優先)

```yaml
Anthropic:
  - https://www.anthropic.com/news
  - https://www.anthropic.com/research
  - https://docs.anthropic.com/en/release-notes
  - https://github.com/anthropics (releases)

OpenAI:
  - https://openai.com/blog
  - https://openai.com/research
  - https://platform.openai.com/docs/changelog
  - https://github.com/openai (releases)

Google DeepMind:
  - https://deepmind.google/discover/blog
  - https://blog.google/technology/ai
  - https://ai.google.dev/changelog
  - https://github.com/google-deepmind (releases)

Unsloth:
  - https://unsloth.ai/blog
  - https://github.com/unslothai/unsloth/releases
  - https://huggingface.co/unsloth (new models)
```

### 技術社群 (高優先)

```yaml
綜合新聞:
  - https://www.theverge.com/ai-artificial-intelligence
  - https://techcrunch.com/category/artificial-intelligence
  - https://venturebeat.com/ai
  - https://the-decoder.com
  - https://www.marktechpost.com

論文與研究:
  - https://arxiv.org/list/cs.AI/recent
  - https://arxiv.org/list/cs.CL/recent
  - https://arxiv.org/list/cs.LG/recent
  - https://huggingface.co/papers

開發者社群:
  - https://news.ycombinator.com (搜尋相關關鍵字)
  - https://www.reddit.com/r/LocalLLaMA
  - https://www.reddit.com/r/MachineLearning
  - https://www.reddit.com/r/artificial
  - https://dev.to/t/ai
```

### 社群媒體 (補充)

```yaml
X (Twitter):
  - @AnthropicAI
  - @OpenAI
  - @GoogleDeepMind
  - @GoogleAI
  - @unaborax (Unsloth 創辦人)
  - @danielhanchen (Unsloth 開發者)

YouTube:
  - Anthropic
  - OpenAI
  - Google DeepMind
  - AI Explained
  - Two Minute Papers
```

---

## 每日報告格式

### 標準模板

```markdown
# AI 技術日報
日期: YYYY-MM-DD (星期X)
整理者: [名稱]

---

## 📌 今日重點摘要

> [用 2-3 句話總結今日最重要的 1-3 則新聞]

---

## 🔷 Anthropic / Claude

### [新聞標題]
- **來源**: [網站名稱](URL)
- **日期**: YYYY-MM-DD
- **摘要**: [2-3 句重點摘要]
- **影響**: [對開發者/使用者的影響]
- **關鍵字**: `Claude`, `MCP`, `Agent`

---

## 🟢 OpenAI

### [新聞標題]
- **來源**: [網站名稱](URL)
- **日期**: YYYY-MM-DD
- **摘要**: [2-3 句重點摘要]
- **影響**: [對開發者/使用者的影響]
- **關鍵字**: `GPT-4`, `API`, `Sora`

---

## 🔵 Google / Gemini

### [新聞標題]
- **來源**: [網站名稱](URL)
- **日期**: YYYY-MM-DD
- **摘要**: [2-3 句重點摘要]
- **影響**: [對開發者/使用者的影響]
- **關鍵字**: `Gemini`, `Gemma`, `AI Studio`

---

## 🦥 Unsloth

### [新聞標題]
- **來源**: [網站名稱](URL)
- **日期**: YYYY-MM-DD
- **摘要**: [2-3 句重點摘要]
- **技術細節**: [效能提升、支援模型等]
- **關鍵字**: `Fine-tuning`, `LoRA`, `Quantization`

---

## 📚 值得關注的論文

| 標題 | 作者/機構 | 連結 | 重點 |
|------|-----------|------|------|
| [論文名] | [機構] | [arXiv](url) | [一句話重點] |

---

## 🔧 開發者資源更新

- **SDK/API 更新**: [描述]
- **新工具發布**: [描述]
- **文件更新**: [描述]

---

## 📊 本週趨勢

- 🔥 熱門話題: [話題]
- 📈 值得關注: [趨勢]
- ⚠️ 注意事項: [警告或提醒]

---

## 🔗 延伸閱讀

- [標題1](URL)
- [標題2](URL)
```

---

## 搜尋關鍵字

### 英文關鍵字

```
Anthropic:
  claude, anthropic, claude 3, claude opus, claude sonnet,
  claude haiku, mcp protocol, model context protocol,
  claude code, constitutional ai, artifacts

OpenAI:
  openai, gpt-4, gpt-4o, gpt-4 turbo, chatgpt, dall-e 3,
  sora, o1, o1-preview, o1-mini, openai api, assistants api,
  function calling, whisper, embeddings

Google/Gemini:
  gemini, gemini pro, gemini ultra, gemini nano,
  google deepmind, gemma, gemma 2, ai studio,
  vertex ai, palm 2, bard, google ai

Unsloth:
  unsloth, unsloth ai, fine-tuning, lora, qlora,
  4bit quantization, efficient training, llama fine-tune,
  mistral fine-tune, gradient checkpointing
```

### 中文關鍵字

```
Claude 相關: Claude 更新, Anthropic 發布, Claude API
OpenAI 相關: ChatGPT 更新, GPT-4 新功能, OpenAI 發布
Gemini 相關: Gemini 更新, Google AI, DeepMind
Unsloth 相關: Unsloth 微調, 高效訓練, LoRA 優化
```

---

## 整理流程

### 每日流程 (建議 15-30 分鐘)

```
1. 檢查官方來源 (5-10 分鐘)
   □ Anthropic News/Blog
   □ OpenAI Blog
   □ Google AI Blog
   □ Unsloth GitHub Releases

2. 掃描技術新聞網站 (5-10 分鐘)
   □ The Verge AI
   □ TechCrunch AI
   □ VentureBeat AI
   □ The Decoder

3. 檢查社群討論 (3-5 分鐘)
   □ Hacker News 首頁
   □ Reddit r/LocalLLaMA
   □ X/Twitter 相關帳號

4. 整理與撰寫 (5-10 分鐘)
   □ 篩選重要新聞
   □ 撰寫摘要
   □ 格式化輸出
```

### 每週流程 (建議額外 30 分鐘)

```
1. 彙整本週重點
2. 識別趨勢與模式
3. 整理重要論文
4. 更新關注清單
```

---

## 評估標準

### 新聞重要性評分

```
⭐⭐⭐⭐⭐ 必報導:
  - 新模型發布 (Claude 4, GPT-5, Gemini 2.0)
  - 重大 API 變更
  - 重要安全事件
  - 定價變更

⭐⭐⭐⭐ 高優先:
  - 功能更新
  - 效能改進
  - 新工具發布
  - 重要合作夥伴關係

⭐⭐⭐ 中優先:
  - 小版本更新
  - 文件更新
  - 社群工具
  - 教學文章

⭐⭐ 低優先:
  - 評論文章
  - 比較分析
  - 使用心得

⭐ 可選:
  - 傳聞
  - 預測
  - 意見文章
```

### 來源可信度

```
最高: 官方部落格、官方文件、GitHub Releases
高:   主流科技媒體 (Verge, TechCrunch, Ars Technica)
中:   專業 AI 媒體 (The Decoder, VentureBeat AI)
低:   個人部落格、社群討論
最低: 未經驗證的推文、傳聞
```

---

## 輸出範例

### 範例: 每日報告

```markdown
# AI 技術日報
日期: 2024-12-30 (星期一)
整理者: AI News Bot

---

## 📌 今日重點摘要

> Anthropic 發布 Claude 3.5 Sonnet 重大更新，程式碼生成能力提升 30%。
> OpenAI 宣布 GPT-4 Turbo 支援 128K context window。
> Unsloth 新版本支援 Llama 3.2 Vision 微調。

---

## 🔷 Anthropic / Claude

### Claude 3.5 Sonnet 更新：程式碼能力大幅提升
- **來源**: [Anthropic Blog](https://www.anthropic.com/news)
- **日期**: 2024-12-30
- **摘要**: 新版 Claude 3.5 Sonnet 在程式碼生成基準測試中提升 30%，特別是在複雜重構任務表現優異。同時改進了對 TypeScript 和 Rust 的支援。
- **影響**: 開發者可期待更準確的程式碼建議，減少手動修正時間。
- **關鍵字**: `Claude 3.5`, `Code Generation`, `Sonnet`

---

## 🟢 OpenAI

### GPT-4 Turbo 擴展至 128K Context
- **來源**: [OpenAI Blog](https://openai.com/blog)
- **日期**: 2024-12-29
- **摘要**: GPT-4 Turbo 現支援 128K tokens 上下文視窗，允許處理約 300 頁文件。API 定價維持不變。
- **影響**: 長文件分析、大型程式碼庫理解成為可能，無需分割處理。
- **關鍵字**: `GPT-4 Turbo`, `128K`, `Context Window`

---

## 🦥 Unsloth

### Unsloth 2024.12 支援 Llama 3.2 Vision
- **來源**: [GitHub Release](https://github.com/unslothai/unsloth/releases)
- **日期**: 2024-12-28
- **摘要**: 新版本支援 Llama 3.2 Vision 模型微調，記憶體使用減少 60%，訓練速度提升 2.2 倍。
- **技術細節**: 支援 4-bit QLoRA，單張 RTX 3090 可微調 11B 視覺模型。
- **關鍵字**: `Llama 3.2`, `Vision`, `Fine-tuning`

---

## 📚 值得關注的論文

| 標題 | 機構 | 連結 | 重點 |
|------|------|------|------|
| Constitutional AI 2.0 | Anthropic | [arXiv](url) | 改進自我對齊方法 |
| Efficient Long Context | Google | [arXiv](url) | 百萬 token 效率提升 |

---

## 🔗 延伸閱讀

- [Claude API 最佳實踐指南更新](url)
- [OpenAI Cookbook 新增 Function Calling 範例](url)
```

---

## 自動化建議

### 使用 RSS 訂閱

```yaml
RSS Feeds:
  - https://www.anthropic.com/news/rss.xml
  - https://openai.com/blog/rss.xml
  - https://blog.google/technology/ai/rss
  - https://techcrunch.com/category/artificial-intelligence/feed
  - https://www.theverge.com/ai-artificial-intelligence/rss/index.xml
```

### 使用 GitHub Watch

```
Repositories to Watch:
  - anthropics/anthropic-cookbook
  - anthropics/courses
  - openai/openai-cookbook
  - google/generative-ai-docs
  - unslothai/unsloth
```

### 使用 Google Alerts

```
設定 Alerts:
  - "Anthropic Claude"
  - "OpenAI GPT-4"
  - "Google Gemini AI"
  - "Unsloth fine-tuning"
```

---

## 注意事項

1. **時效性**: AI 領域變化快，優先報導 24-48 小時內的新聞
2. **驗證**: 重大消息需確認官方來源
3. **版權**: 摘要而非複製全文，附上原始連結
4. **偏見**: 平衡報導各家公司，避免偏頗
5. **隱私**: 不轉發未經證實的內部消息

---

*此指令用於協助每日 AI 技術新聞整理，確保追蹤最新發展動態。*
