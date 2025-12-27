# Artifacts Builder Instructions

> 來源: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

## 適用情境

當使用者需要以下協助時使用此指令：
- 建立複雜的互動式 HTML 產出物 (Artifacts)
- 開發 React + TypeScript 元件
- 使用 shadcn/ui 建立精美介面
- 將多元件專案打包成單一 HTML 檔案

---

## 技術堆疊

| 技術 | 版本/說明 |
|------|-----------|
| React | 18.x |
| TypeScript | 嚴格類型檢查 |
| Vite | 開發環境 |
| Parcel | 打包成單一 HTML |
| Tailwind CSS | 3.4.1 |
| shadcn/ui | 40+ 預裝元件 |
| Radix UI | 完整依賴套件 |

---

## 工作流程

### 步驟 1: 初始化專案

```bash
# 使用初始化腳本建立專案
./scripts/init-artifact.sh <project-name>

# 產生的專案結構
<project-name>/
├── src/
│   ├── App.tsx           # 主要應用元件
│   ├── main.tsx          # 進入點
│   ├── index.css         # 全域樣式
│   └── components/
│       └── ui/           # shadcn/ui 元件
├── public/
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── postcss.config.js
```

### 步驟 2: 開發元件

```tsx
// src/App.tsx
import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Hero Section */}
        <header className="text-center space-y-4">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            Interactive Dashboard
          </h1>
          <p className="text-slate-400 text-lg">
            Built with React, TypeScript, and shadcn/ui
          </p>
        </header>

        {/* Main Content */}
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/50">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="bg-slate-800/30 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Counter Demo</CardTitle>
                  <CardDescription>Interactive state management</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-4xl font-bold text-cyan-400">{count}</p>
                </CardContent>
                <CardFooter className="gap-2">
                  <Button onClick={() => setCount(c => c - 1)} variant="outline">
                    Decrease
                  </Button>
                  <Button onClick={() => setCount(c => c + 1)}>
                    Increase
                  </Button>
                </CardFooter>
              </Card>

              <Card className="bg-slate-800/30 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Quick Form</CardTitle>
                  <CardDescription>User input example</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-slate-300">Email</Label>
                    <Input id="email" placeholder="user@example.com" className="bg-slate-900/50" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="analytics">
            <Card className="bg-slate-800/30 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Analytics Content</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-400">Charts and metrics go here...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings">
            <Card className="bg-slate-800/30 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-400">Configuration options go here...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
```

### 步驟 3: 打包成單一 HTML

```bash
# 執行打包腳本
./scripts/bundle-artifact.sh

# 輸出結果
dist/
└── index.html  # 自包含的單一 HTML 檔案 (含所有 CSS/JS)
```

### 步驟 4: 展示給使用者

打包完成的 `index.html` 可以：
- 直接在瀏覽器開啟
- 作為 Claude Artifact 展示
- 分享給他人使用

### 步驟 5: 測試 (選用)

```bash
# 本地開發測試
npm run dev

# 建置前預覽
npm run preview
```

---

## 可用的 shadcn/ui 元件

### 表單元件
```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
```

### 佈局元件
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
```

### 回饋元件
```tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/components/ui/use-toast"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
```

### 資料展示
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Calendar } from "@/components/ui/calendar"
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
```

### 導航元件
```tsx
import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger } from "@/components/ui/navigation-menu"
import { Menubar, MenubarContent, MenubarItem, MenubarMenu, MenubarTrigger } from "@/components/ui/menubar"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
```

---

## 設計原則

### ✅ 正確做法

```tsx
// 1. 使用獨特的漸層背景
<div className="bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">

// 2. 混合使用圓角大小
<Card className="rounded-none">        {/* 銳角 */}
<Button className="rounded-full">      {/* 全圓角 */}
<Input className="rounded-sm">         {/* 小圓角 */}

// 3. 使用玻璃態效果
<Card className="bg-slate-800/30 backdrop-blur-lg border-slate-700/50">

// 4. 不對稱佈局
<div className="grid grid-cols-3 gap-4">
  <div className="col-span-2">主要內容</div>
  <div>側邊欄</div>
</div>

// 5. 有意義的動畫
<Button className="transition-all hover:scale-105 hover:shadow-lg hover:shadow-cyan-500/25">
```

### ❌ 避免做法

```tsx
// 1. 過度置中
<div className="flex items-center justify-center">  {/* 所有東西都置中 */}

// 2. 紫色漸層 (過度使用)
<div className="bg-gradient-to-r from-purple-500 to-pink-500">

// 3. 統一圓角
<div className="rounded-lg">  {/* 每個元素都用 rounded-lg */}

// 4. Inter 字體 (預設/通用)
font-family: Inter, sans-serif;

// 5. 缺乏視覺層次
// 所有文字大小相同，沒有對比
```

---

## 進階範例

### 資料表格

```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

const data = [
  { id: 1, name: "Project Alpha", status: "active", progress: 75 },
  { id: 2, name: "Project Beta", status: "pending", progress: 30 },
  { id: 3, name: "Project Gamma", status: "completed", progress: 100 },
]

function DataTable() {
  return (
    <Table>
      <TableHeader>
        <TableRow className="border-slate-700">
          <TableHead className="text-slate-300">Name</TableHead>
          <TableHead className="text-slate-300">Status</TableHead>
          <TableHead className="text-slate-300">Progress</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((row) => (
          <TableRow key={row.id} className="border-slate-800">
            <TableCell className="text-white font-medium">{row.name}</TableCell>
            <TableCell>
              <Badge variant={
                row.status === 'active' ? 'default' :
                row.status === 'completed' ? 'secondary' : 'outline'
              }>
                {row.status}
              </Badge>
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                <Progress value={row.progress} className="w-20" />
                <span className="text-slate-400 text-sm">{row.progress}%</span>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

### 對話框表單

```tsx
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

function CreateProjectDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create Project</Button>
      </DialogTrigger>
      <DialogContent className="bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-white">New Project</DialogTitle>
          <DialogDescription>
            Fill in the details to create a new project.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Project Name</Label>
            <Input id="name" placeholder="Enter project name" className="bg-slate-800/50" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" placeholder="Project description..." className="bg-slate-800/50" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button>Create</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

---

## 路徑別名

```tsx
// 使用 @/ 別名匯入
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

// cn() 工具函數用於合併 class names
<div className={cn(
  "base-styles",
  isActive && "active-styles",
  variant === "primary" ? "primary-styles" : "secondary-styles"
)}>
```

---

## 檢查清單

建立 Artifact 前確認：

```
□ 使用獨特的視覺風格，避免通用設計
□ 包含互動元素 (按鈕、表單、狀態)
□ 有清晰的視覺層次
□ 響應式設計 (手機/桌面)
□ 適當的載入狀態
□ 錯誤處理 (若有表單)
□ 可訪問性 (ARIA labels, keyboard navigation)
```

---

*Source: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)*
