# Internal Communications Instructions

> 來源: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

## 適用情境

當使用者需要以下協助時使用此指令：
- 撰寫團隊週報 (3P Updates)
- 撰寫公司電子報 (Newsletter)
- 回覆常見問題 (FAQ)
- 撰寫狀態報告 (Status Reports)
- 撰寫領導層通訊
- 撰寫專案更新
- 撰寫事件報告 (Incident Reports)

---

## 通訊類型

| 類型 | 說明 | 受眾 |
|------|------|------|
| 3P Updates | 進度/計畫/問題週報 | 領導層、跨部門團隊 |
| Company Newsletter | 公司整體動態 | 全公司 |
| FAQ Answers | 常見問題回覆 | 內部或外部 |
| Status Reports | 專案狀態報告 | 利益關係人 |
| Leadership Comms | 領導層公告 | 全公司或特定團隊 |
| Project Updates | 專案進度更新 | 專案相關人員 |
| Incident Reports | 事件處理報告 | 技術團隊、管理層 |

---

# 1. 3P Updates (進度/計畫/問題)

## 概述

3P 更新是設計給主管和領導層的每週狀態報告，應在 30-60 秒內可讀完。

## 格式

```
[emoji] [團隊名稱] (日期範圍)

Progress (進度): [1-3 句話]
Plans (計畫): [1-3 句話]
Problems (問題): [1-3 句話]
```

## 範例

```
🚀 Platform Team (Dec 16-20, 2024)

Progress: Shipped user authentication v2.0 with SSO support (3,000+ users migrated). Reduced API latency by 40% through database optimization. Completed security audit with zero critical findings.

Plans: Launch payment integration beta to 100 pilot users. Finalize Q1 roadmap with product team. Begin mobile app refactoring sprint.

Problems: Third-party SMS provider experiencing intermittent outages (ETA fix: Dec 23). Need additional frontend engineer for mobile timeline - discussing with HR.
```

## 撰寫原則

### 調整粒度
- **小團隊 (3-5人)**: 具體任務層級
  - "Completed user profile redesign"
- **大團隊 (10+人)**: 里程碑層級
  - "Delivered Phase 2 of platform migration"

### 數據驅動
```
❌ "Made good progress on performance"
✅ "Reduced page load time from 3.2s to 1.1s (66% improvement)"

❌ "Fixed several bugs"
✅ "Resolved 23 customer-reported issues (bug backlog down 40%)"
```

### 資訊來源
- Slack 高互動訊息
- Google Drive 高瀏覽量文件
- Email 重要往來
- Calendar 重要非例行會議

---

# 2. Company Newsletter (公司電子報)

## 架構

```markdown
# [公司名稱] Weekly/Monthly Update
[日期範圍]

## 🎯 重大公告
- [重要消息 1]
- [重要消息 2]

## 🚀 各部門亮點

### Product
- [成就 1]
- [成就 2]

### Engineering
- [成就 1]
- [成就 2]

### Go-to-Market
- [成就 1]
- [成就 2]

## 📊 關鍵指標
- [指標 1]: [數值] ([變化])
- [指標 2]: [數值] ([變化])

## 👥 人員動態
- 歡迎新成員: [名單]
- 晉升: [名單]
- 工作週年: [名單]

## 🎉 團隊慶祝
- [活動/慶祝事項]

## 📅 即將到來
- [日期]: [事件]
- [日期]: [事件]

## 🔗 重要連結
- [文件名稱](連結)
```

## 範例

```markdown
# Acme Corp Weekly Update
December 16-20, 2024

## 🎯 重大公告
- Series B 融資完成！歡迎 Sequoia Capital 加入
- 新辦公室 (台北信義區) 將於 1 月開放

## 🚀 各部門亮點

### Product
- 新功能「智慧分析」正式上線，首週 2,000+ 用戶啟用
- iOS app 更新至 v3.5，App Store 評分升至 4.8

### Engineering
- 基礎設施遷移至 AWS ap-northeast-1 完成
- 部署時間從 45 分鐘縮短至 8 分鐘

### Go-to-Market
- 簽下 3 家企業客戶 (年度合約總值 $450K)
- 獲選 TechCrunch Disrupt 決賽

## 📊 關鍵指標
- 月活躍用戶: 125,000 (+15% MoM)
- 客戶留存率: 94% (+2%)
- NPS 分數: 72 (+5)

## 👥 人員動態
- 🎉 歡迎: Sarah Chen (Engineering), Mike Wang (Sales)
- 🎊 晉升: Lisa Huang → Senior PM
- 🎂 週年: David Lin (3 年)

## 📅 即將到來
- 12/25: 聖誕節假期
- 1/3: 全員大會 (Q1 Kickoff)
- 1/15: 新辦公室開幕

## 🔗 重要連結
- [Q1 產品路線圖](link)
- [新員工手冊](link)
```

## 撰寫指南

1. **20-25 個要點** - 控制在可快速瀏覽的長度
2. **使用 emoji** - 幫助視覺掃描
3. **包含連結** - 讓讀者可深入了解
4. **平衡各部門** - 不要偏重單一團隊
5. **正向為主** - 但不迴避重要問題

---

# 3. FAQ Answers (常見問題回覆)

## 格式

```markdown
## Q: [問題]

**簡短答案**: [1-2 句直接回答]

**詳細說明**:
[補充細節、背景、相關資訊]

**相關資源**:
- [資源 1](連結)
- [資源 2](連結)

**聯絡窗口**: [負責人/團隊]
```

## 範例

```markdown
## Q: 如何申請遠端工作？

**簡短答案**: 透過 HR 系統提交遠端工作申請表，主管核准後即可開始。

**詳細說明**:
公司支援混合工作模式。全職員工可申請每週最多 3 天遠端工作。申請流程：
1. 登入 HR Portal → 「工作安排」
2. 填寫「遠端工作申請表」
3. 主管將於 3 個工作天內審核
4. 核准後，IT 會安排設備配送

注意：某些職位可能因工作性質限制遠端天數。

**相關資源**:
- [遠端工作政策](link)
- [居家辦公設備申請](link)

**聯絡窗口**: HR Team (hr@company.com)
```

---

# 4. Status Reports (狀態報告)

## 格式

```markdown
# [專案名稱] Status Report
日期: [YYYY-MM-DD]
報告人: [姓名]

## 整體狀態: 🟢 On Track / 🟡 At Risk / 🔴 Blocked

## 本週摘要
[2-3 句概述]

## 完成事項
- [x] [任務 1]
- [x] [任務 2]

## 進行中
- [ ] [任務 3] - [進度 %] - [預計完成日]
- [ ] [任務 4] - [進度 %] - [預計完成日]

## 阻礙與風險
| 項目 | 影響 | 緩解措施 | 負責人 |
|------|------|----------|--------|
| [阻礙 1] | [高/中/低] | [措施] | [人名] |

## 下週計畫
- [ ] [任務 5]
- [ ] [任務 6]

## 需要協助
- [請求 1]
- [請求 2]
```

---

# 5. Incident Reports (事件報告)

## 格式

```markdown
# Incident Report: [事件標題]
嚴重程度: P1 / P2 / P3 / P4
狀態: 調查中 / 已緩解 / 已解決

## 時間軸 (UTC)
- **[HH:MM]** - 事件發現
- **[HH:MM]** - [採取行動]
- **[HH:MM]** - [狀態變化]
- **[HH:MM]** - 事件解決

## 影響
- 影響服務: [服務名稱]
- 影響用戶: [數量/百分比]
- 影響時長: [時間]

## 根本原因
[說明根本原因]

## 解決方案
[說明如何解決]

## 後續行動
- [ ] [行動 1] - @[負責人] - [截止日]
- [ ] [行動 2] - @[負責人] - [截止日]

## 經驗教訓
- [學到什麼]
- [未來如何預防]
```

---

# 6. General Communications (一般通訊)

## 撰寫前確認

1. **目標受眾** - 誰需要知道這個資訊？
2. **目的** - 通知？請求行動？徵求意見？
3. **語調** - 正式？輕鬆？緊急？
4. **格式需求** - Email？Slack？文件？

## 核心原則

```
✅ 清晰簡潔
✅ 使用主動語態
✅ 重要資訊放前面
✅ 包含相關連結
✅ 符合公司溝通風格

❌ 過長的段落
❌ 模糊的行動要求
❌ 缺乏截止日期
❌ 沒有聯絡方式
```

## 結構範本

```markdown
## [主題]

**TL;DR**: [一句話摘要]

### 背景
[為什麼發這個通訊]

### 重點
- [要點 1]
- [要點 2]
- [要點 3]

### 需要的行動
- [ ] [行動 1] - 截止日: [日期]
- [ ] [行動 2] - 截止日: [日期]

### 問題？
聯絡 [人名] 或在 #[頻道] 發問
```

---

## 語調指南

| 情境 | 語調 | 範例 |
|------|------|------|
| 一般更新 | 專業友善 | "很高興分享..." |
| 緊急通知 | 直接明確 | "需要立即行動：..." |
| 慶祝成就 | 熱情正向 | "恭喜團隊！..." |
| 壞消息 | 誠實同理 | "我們需要分享一個困難的消息..." |
| 政策變更 | 清晰解釋 | "從 [日期] 開始，我們將..." |

---

## 快速檢查清單

發送前確認：

```
□ 主題/標題清楚描述內容
□ 最重要的資訊在開頭
□ 包含所有必要的日期/數字
□ 連結都可以正常開啟
□ 如有行動要求，已明確說明
□ 已標注正確的收件人/頻道
□ 語調適合受眾和情境
□ 已校對錯字和格式
```

---

*Source: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)*
