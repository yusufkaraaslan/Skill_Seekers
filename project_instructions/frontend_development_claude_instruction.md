# Frontend Development Instructions

> 整合自 [Anthropic Skills Repository](https://github.com/anthropics/skills) 的前端開發技能

## 適用情境

當使用者需要以下協助時使用此指令：
- 設計與開發 Web 前端介面
- 建立 React/TypeScript 專案與元件
- 測試 Web 應用程式
- 套用專業主題與樣式
- 建立視覺設計作品

---

# 1. Frontend Design (前端設計)

## 核心理念

建立獨特、高品質的 Web 介面，優先考慮真正的設計思維，而非通用美學。避免產出看起來像「AI 生成」的通用設計。

## 設計流程

### 開始前先釐清

1. **目的** - 這個介面要解決什麼問題？
2. **美學方向** - 選擇大膽的風格：
   - Brutalist (野獸派)
   - Maximalist (極繁主義)
   - Retro-futuristic (復古未來)
   - Neo-minimalist (新極簡)
   - Organic/Natural (有機自然)
3. **技術限制** - 目標瀏覽器、效能需求
4. **記憶點** - 什麼讓這個介面令人難忘？

## 視覺執行要點

### Typography (字體)

```css
/* ✅ 正確：使用獨特、美觀的字體 */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');

:root {
  --font-heading: 'Playfair Display', serif;
  --font-body: 'Space Grotesk', sans-serif;
}

/* ❌ 避免：通用系統字體 */
/* font-family: Arial, sans-serif; */
/* font-family: Inter, system-ui; */
```

### Color Strategy (色彩策略)

```css
/* ✅ 使用 CSS 變數建立一致的色彩系統 */
:root {
  /* Primary palette */
  --color-primary: #1a1a2e;
  --color-secondary: #16213e;
  --color-accent: #e94560;

  /* Semantic colors */
  --color-surface: #0f0f1a;
  --color-text: #eaeaea;
  --color-muted: #8b8b9a;

  /* Gradients with purpose */
  --gradient-hero: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  --gradient-accent: linear-gradient(90deg, #e94560 0%, #ff6b6b 100%);
}

/* ❌ 避免：過度使用的紫色漸層 */
/* background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); */
```

### Motion Design (動態設計)

```css
/* 專注於高影響力的關鍵時刻 */
.hero-element {
  animation: heroReveal 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes heroReveal {
  from {
    opacity: 0;
    transform: translateY(60px) scale(0.95);
    filter: blur(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

/* 互動回饋 */
.interactive-card {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.3s ease;
}

.interactive-card:hover {
  transform: translateY(-8px) rotateX(5deg);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}
```

### Layout (佈局)

```css
/* ✅ 打破傳統網格的不對稱佈局 */
.asymmetric-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  grid-template-rows: auto auto;
  gap: 2rem;
}

.feature-large {
  grid-row: span 2;
  aspect-ratio: 3/4;
}

.feature-small {
  aspect-ratio: 16/9;
}

/* 創造視覺張力 */
.offset-section {
  margin-left: 15%;
  width: 85%;
}
```

### Atmospheric Details (氛圍細節)

```css
/* 漸層、紋理、層次透明 */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.texture-overlay {
  position: relative;
}

.texture-overlay::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
}
```

## 禁止事項

| 避免 | 替代方案 |
|------|----------|
| Arial, Inter, system-ui | 使用特色字體如 Space Grotesk, Playfair Display |
| 紫色漸層 (#667eea → #764ba2) | 建立獨特的色彩系統 |
| 統一圓角 (rounded-lg everywhere) | 混合使用銳角與圓角創造對比 |
| 千篇一律的卡片元件 | 設計有個性的容器與邊框 |
| 置中對齊一切 | 使用不對稱佈局創造動態感 |

---

# 2. Web Artifacts Builder (Web 產出物建構器)

## 技術堆疊

- **React 18** + **TypeScript**
- **Vite** (開發) + **Parcel** (打包)
- **Tailwind CSS 3.4.1**
- **shadcn/ui** (40+ 預設元件)

## 工作流程

### 步驟 1: 初始化專案

```bash
# 建立新專案
./scripts/init-artifact.sh my-artifact

# 專案結構
my-artifact/
├── src/
│   ├── App.tsx
│   ├── components/
│   └── main.tsx
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

### 步驟 2: 開發元件

```tsx
// src/App.tsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <Card className="max-w-md mx-auto backdrop-blur-lg bg-white/10 border-white/20">
        <CardHeader>
          <CardTitle className="text-white">Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" className="w-full">
            Get Started
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

### 步驟 3: 打包為單一 HTML

```bash
# 打包成自包含的 HTML 檔案
./scripts/bundle-artifact.sh

# 輸出: dist/index.html (可直接分享)
```

## 可用的 shadcn/ui 元件

```tsx
// 表單元件
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"

// 佈局元件
import { Card } from "@/components/ui/card"
import { Tabs } from "@/components/ui/tabs"
import { Accordion } from "@/components/ui/accordion"
import { Dialog } from "@/components/ui/dialog"
import { Sheet } from "@/components/ui/sheet"
import { Separator } from "@/components/ui/separator"

// 回饋元件
import { Alert } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Toast } from "@/components/ui/toast"

// 資料展示
import { Table } from "@/components/ui/table"
import { Avatar } from "@/components/ui/avatar"
import { Calendar } from "@/components/ui/calendar"
```

## 路徑別名設定

```tsx
// 使用 @/ 別名
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

// tsconfig.json 已預設配置
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

# 3. Webapp Testing (Web 應用測試)

## 使用 Playwright 測試

### 決策流程

```
應用類型？
├── 靜態 HTML → 直接讀取 HTML 找選擇器
├── 動態應用 (伺服器未啟動) → 使用 with_server.py
└── 動態應用 (伺服器已啟動) → 偵察-執行模式
```

### 啟動伺服器輔助腳本

```bash
# 單一伺服器
python scripts/with_server.py \
  --server "npm run dev" \
  --port 5173 \
  -- python your_automation.py

# 多伺服器 (前後端分離)
python scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python your_automation.py
```

### Playwright 自動化範例

```python
from playwright.sync_api import sync_playwright

def test_login_flow():
    with sync_playwright() as p:
        # 啟動瀏覽器 (無頭模式)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 導航並等待載入完成
        page.goto("http://localhost:5173")
        page.wait_for_load_state("networkidle")

        # 使用描述性選擇器
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')

        # 驗證結果
        page.wait_for_selector("text=Welcome")
        assert page.is_visible("text=Dashboard")

        # 截圖記錄
        page.screenshot(path="login-success.png")

        browser.close()
```

### 元素發現模式

```python
def discover_elements(page):
    """偵察頁面上的可互動元素"""

    # 等待動態內容載入
    page.wait_for_load_state("networkidle")

    # 發現按鈕
    buttons = page.query_selector_all("button")
    for btn in buttons:
        print(f"Button: {btn.inner_text()} | {btn.get_attribute('class')}")

    # 發現連結
    links = page.query_selector_all("a[href]")
    for link in links:
        print(f"Link: {link.inner_text()} → {link.get_attribute('href')}")

    # 發現表單輸入
    inputs = page.query_selector_all("input, textarea, select")
    for inp in inputs:
        print(f"Input: {inp.get_attribute('name')} | {inp.get_attribute('type')}")
```

### 選擇器最佳實踐

```python
# ✅ 優先使用的選擇器 (按優先順序)
page.click('role=button[name="Submit"]')  # 角色 + 名稱
page.click('text=Click me')               # 文字內容
page.click('#submit-btn')                 # ID
page.click('[data-testid="submit"]')      # 測試專用屬性
page.click('button.primary')              # CSS 選擇器

# ❌ 避免的選擇器
page.click('div > div > button')          # 脆弱的結構選擇器
page.click('.css-1a2b3c')                 # 自動生成的 class
```

### Console 日誌捕捉

```python
def capture_console_logs(page):
    logs = []

    def handle_console(msg):
        logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        })

    page.on("console", handle_console)

    # 執行操作...
    page.goto("http://localhost:5173")
    page.click("button")

    # 檢查錯誤
    errors = [log for log in logs if log["type"] == "error"]
    if errors:
        print("Console Errors:", errors)
```

---

# 4. Theme Factory (主題工廠)

## 預設主題

### Ocean Depths (海洋深處)
```css
:root {
  --primary: #0077b6;
  --secondary: #00b4d8;
  --accent: #90e0ef;
  --background: #03045e;
  --surface: #023e8a;
  --text: #caf0f8;
  --font-heading: 'Cormorant Garamond', serif;
  --font-body: 'Lato', sans-serif;
}
```

### Sunset Boulevard (日落大道)
```css
:root {
  --primary: #ff6b35;
  --secondary: #f7c59f;
  --accent: #efa00b;
  --background: #1a1423;
  --surface: #372549;
  --text: #ffecd1;
  --font-heading: 'Abril Fatface', cursive;
  --font-body: 'Raleway', sans-serif;
}
```

### Forest Canopy (森林樹冠)
```css
:root {
  --primary: #2d6a4f;
  --secondary: #40916c;
  --accent: #95d5b2;
  --background: #1b4332;
  --surface: #2d6a4f;
  --text: #d8f3dc;
  --font-heading: 'Libre Baskerville', serif;
  --font-body: 'Source Sans Pro', sans-serif;
}
```

### Modern Minimalist (現代極簡)
```css
:root {
  --primary: #2b2d42;
  --secondary: #8d99ae;
  --accent: #ef233c;
  --background: #edf2f4;
  --surface: #ffffff;
  --text: #2b2d42;
  --font-heading: 'DM Sans', sans-serif;
  --font-body: 'Inter', sans-serif;
}
```

### Tech Innovation (科技創新)
```css
:root {
  --primary: #7209b7;
  --secondary: #3a0ca3;
  --accent: #4cc9f0;
  --background: #0a0a0f;
  --surface: #14141f;
  --text: #e0e0e0;
  --font-heading: 'Space Grotesk', sans-serif;
  --font-body: 'IBM Plex Mono', monospace;
}
```

### Midnight Galaxy (午夜銀河)
```css
:root {
  --primary: #7400b8;
  --secondary: #5e60ce;
  --accent: #4ea8de;
  --background: #10002b;
  --surface: #240046;
  --text: #e0aaff;
  --font-heading: 'Orbitron', sans-serif;
  --font-body: 'Exo 2', sans-serif;
}
```

## 主題套用流程

```tsx
// 1. 定義主題介面
interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
  };
  fonts: {
    heading: string;
    body: string;
  };
}

// 2. 建立主題 Context
const ThemeContext = createContext<Theme>(defaultTheme);

// 3. 套用主題
function ThemeProvider({ theme, children }: { theme: Theme; children: React.ReactNode }) {
  useEffect(() => {
    const root = document.documentElement;
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    root.style.setProperty('--font-heading', theme.fonts.heading);
    root.style.setProperty('--font-body', theme.fonts.body);
  }, [theme]);

  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  );
}
```

---

# 5. Canvas Design (畫布設計)

## 適用於

- 海報設計
- 藝術作品
- 視覺圖像
- PDF/PNG 靜態設計

## 兩步驟流程

### 步驟 1: 設計哲學 (.md)

建立 4-6 段的美學宣言，涵蓋：

```markdown
# [作品名稱] Design Philosophy

## Space and Form (空間與形態)
描述如何運用正負空間、形狀語言...

## Color and Material (色彩與材質)
定義調色板、材質質感、光影處理...

## Scale and Rhythm (比例與韻律)
說明元素的大小關係、視覺節奏...

## Composition and Balance (構圖與平衡)
解釋視覺重心、動態平衡...

## Visual Hierarchy (視覺層次)
引導觀者目光的順序與方式...
```

### 步驟 2: 畫布表現 (.pdf/.png)

**核心原則：**
- 90% 視覺設計 / 10% 必要文字
- 博物館等級的品質標準
- 看起來像是花了無數小時精心製作
- 完美的間距，沒有重疊
- 使用重複圖案建立視覺語言

**設計元素：**

```
視覺語言
├── 幾何圖形系統
├── 一致的線條粗細
├── 統一的圓角半徑
└── 協調的間距單位

色彩運用
├── 主色調 (60%)
├── 輔助色 (30%)
└── 強調色 (10%)

排版
├── 標題字體 (大、粗)
├── 副標題 (中等)
└── 正文 (最小化)
```

### 隱藏的深度

像爵士樂「引用」其他歌曲一樣，嵌入只有行家才能識別的概念參考：
- 藝術運動的致敬 (包浩斯、瑞士風格)
- 設計大師的手法 (Massimo Vignelli, Josef Müller-Brockmann)
- 文化符號的轉化

---

# Quick Reference (快速參考)

## 設計檢查清單

```
□ 字體是否獨特且適合專案？
□ 色彩系統是否使用 CSS 變數？
□ 佈局是否有視覺張力？
□ 動畫是否有明確目的？
□ 是否避免了通用的 AI 設計模式？
□ 細節是否經過打磨？
```

## 常用 Import

```tsx
// React 核心
import { useState, useEffect, useContext, useRef, useMemo, useCallback } from 'react';

// shadcn/ui 常用元件
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// 工具函數
import { cn } from "@/lib/utils";
```

## 測試指令

```bash
# Playwright 測試
python -m pytest tests/ -v

# 單一測試
python scripts/with_server.py --server "npm run dev" --port 5173 -- python test_login.py

# 截圖比對
playwright screenshot http://localhost:5173 --full-page
```

---

*Source: [Anthropic Skills Repository](https://github.com/anthropics/skills)*
