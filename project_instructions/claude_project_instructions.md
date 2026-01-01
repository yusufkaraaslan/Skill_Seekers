# Claude Project Instructions

> 整合自多個來源的完整開發與溝通指令集

## 目錄

1. [React 開發](#part-1-react-開發)
2. [前端設計](#part-2-前端設計)
3. [Web Artifacts 建構](#part-3-web-artifacts-建構)
4. [Web 應用測試](#part-4-web-應用測試)
5. [主題工廠](#part-5-主題工廠)
6. [視覺設計](#part-6-視覺設計)
7. [內部通訊](#part-7-內部通訊)

---

# Part 1: React 開發

## 適用情境

- React 元件、Hooks、狀態管理
- JSX 語法與元件組合
- 現代 React 模式 (React 18+)
- React 效能優化與測試

## 1.1 元件模式

**函數式元件 (推薦)**
```jsx
function UserProfile({ name, email, onUpdate }) {
  return (
    <div className="user-profile">
      <h2>{name}</h2>
      <p>{email}</p>
      <button onClick={onUpdate}>Update</button>
    </div>
  );
}
```

**帶有 Children 的元件**
```jsx
function Card({ title, children }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="card-content">{children}</div>
    </div>
  );
}

// 使用方式
<Card title="Welcome">
  <p>This is the card content.</p>
</Card>
```

## 1.2 Hooks 參考

**useState - 狀態管理**
```jsx
const [count, setCount] = useState(0);
const [user, setUser] = useState({ name: '', email: '' });

// 更新物件狀態 (必須建立新物件)
setUser(prev => ({ ...prev, name: 'New Name' }));
```

**useEffect - 副作用**
```jsx
// 僅在掛載時執行
useEffect(() => {
  fetchData();
}, []);

// 依賴變更時執行
useEffect(() => {
  document.title = `Count: ${count}`;
}, [count]);

// 清理函數
useEffect(() => {
  const subscription = subscribe();
  return () => subscription.unsubscribe();
}, []);
```

**useContext - 消費 Context**
```jsx
const ThemeContext = createContext('light');

function ThemedButton() {
  const theme = useContext(ThemeContext);
  return <button className={theme}>Click me</button>;
}
```

**useRef - DOM 參考與可變值**
```jsx
function TextInput() {
  const inputRef = useRef(null);

  const focusInput = () => {
    inputRef.current.focus();
  };

  return <input ref={inputRef} />;
}
```

**useMemo - 昂貴計算記憶化**
```jsx
const sortedItems = useMemo(() => {
  return items.sort((a, b) => a.name.localeCompare(b.name));
}, [items]);
```

**useCallback - 穩定函數參考**
```jsx
const handleClick = useCallback((id) => {
  setSelectedId(id);
}, []);
```

**useReducer - 複雜狀態邏輯**
```jsx
function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { count: state.count + 1 };
    case 'decrement':
      return { count: state.count - 1 };
    default:
      throw new Error();
  }
}

const [state, dispatch] = useReducer(reducer, { count: 0 });
```

## 1.3 自定義 Hooks

```jsx
// useFetch - 資料獲取
function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetch(url, { signal: controller.signal });
        const json = await response.json();
        setData(json);
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err);
        }
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    return () => controller.abort();
  }, [url]);

  return { data, loading, error };
}

// useLocalStorage - 持久化狀態
function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : initialValue;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}

// useDebounce - 防抖
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

## 1.4 表單與受控元件

```jsx
function RegistrationForm() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.username) newErrors.username = 'Username required';
    if (!formData.email.includes('@')) newErrors.email = 'Valid email required';
    if (formData.password.length < 8) newErrors.password = 'Min 8 characters';
    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    console.log('Form submitted:', formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="username" value={formData.username} onChange={handleChange} placeholder="Username" />
      {errors.username && <span className="error">{errors.username}</span>}

      <input name="email" type="email" value={formData.email} onChange={handleChange} placeholder="Email" />
      {errors.email && <span className="error">{errors.email}</span>}

      <input name="password" type="password" value={formData.password} onChange={handleChange} placeholder="Password" />
      {errors.password && <span className="error">{errors.password}</span>}

      <button type="submit">Register</button>
    </form>
  );
}
```

## 1.5 Context API 全局狀態

```jsx
// 建立 context
const AuthContext = createContext(null);

// Provider 元件
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth().then(user => {
      setUser(user);
      setLoading(false);
    });
  }, []);

  const login = async (credentials) => {
    const user = await authService.login(credentials);
    setUser(user);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

// 自定義 Hook 消費 context
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

## 1.6 Error Boundaries

```jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

## 1.7 React 18+ 新功能

**Automatic Batching**
```jsx
function handleClick() {
  setCount(c => c + 1);
  setFlag(f => !f);
  // 只會觸發一次重新渲染
}
```

**Transitions**
```jsx
import { useTransition } from 'react';

function SearchResults() {
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleChange = (e) => {
    setQuery(e.target.value);
    startTransition(() => {
      setResults(filterResults(e.target.value));
    });
  };

  return (
    <div>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <ResultsList results={results} />}
    </div>
  );
}
```

**Suspense**
```jsx
import { Suspense, lazy } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <HeavyComponent />
    </Suspense>
  );
}
```

## 1.8 效能優化

```jsx
// React.memo 用於純元件
const ExpensiveList = React.memo(function ExpensiveList({ items }) {
  return items.map(item => <ExpensiveItem key={item.id} {...item} />);
});

// 虛擬化長列表
import { FixedSizeList } from 'react-window';

function VirtualizedList({ items }) {
  return (
    <FixedSizeList height={400} itemCount={items.length} itemSize={50}>
      {({ index, style }) => (
        <div style={style}>{items[index].name}</div>
      )}
    </FixedSizeList>
  );
}
```

## 1.9 測試模式

```jsx
import { render, screen, fireEvent } from '@testing-library/react';

test('increments counter on click', () => {
  render(<Counter />);
  const button = screen.getByRole('button', { name: /increment/i });
  fireEvent.click(button);
  expect(screen.getByText(/count: 1/i)).toBeInTheDocument();
});

// 測試 Hooks
import { renderHook, act } from '@testing-library/react';

test('useCounter increments value', () => {
  const { result } = renderHook(() => useCounter());
  act(() => { result.current.increment(); });
  expect(result.current.count).toBe(1);
});
```

## 1.10 最佳實踐

### ✅ 正確做法
1. 使用函數式元件和 Hooks
2. 向上提升狀態
3. 使用 TypeScript
4. 記憶化昂貴操作
5. 提取自定義 Hooks
6. 正確使用 keys
7. 清理 effects
8. 共置相關程式碼

### ❌ 避免做法
1. 直接修改狀態
2. 使用陣列索引作為 key
3. 條件式調用 Hooks
4. 過度使用 context
5. 忘記依賴陣列
6. 在 JSX 中內聯物件

## 1.11 Hooks 快速參考

| Hook | 用途 | 常見場景 |
|------|------|----------|
| useState | 本地狀態 | 表單輸入、開關 |
| useEffect | 副作用 | API 呼叫、訂閱 |
| useContext | 消費 context | 主題、認證、i18n |
| useRef | DOM 參考、可變值 | 聚焦、計時器 |
| useMemo | 記憶化值 | 昂貴計算 |
| useCallback | 記憶化函數 | 子元件事件處理 |
| useReducer | 複雜狀態邏輯 | 表單、多步驟流程 |

---

# Part 2: 前端設計

> 來源: [Anthropic Skills Repository](https://github.com/anthropics/skills)

## 核心理念

建立獨特、高品質的 Web 介面，優先考慮真正的設計思維，而非通用美學。避免產出看起來像「AI 生成」的通用設計。

## 2.1 設計流程

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

## 2.2 Typography (字體)

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

## 2.3 Color Strategy (色彩策略)

```css
/* ✅ 使用 CSS 變數建立一致的色彩系統 */
:root {
  --color-primary: #1a1a2e;
  --color-secondary: #16213e;
  --color-accent: #e94560;
  --color-surface: #0f0f1a;
  --color-text: #eaeaea;
  --color-muted: #8b8b9a;
  --gradient-hero: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

/* ❌ 避免：過度使用的紫色漸層 */
/* background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); */
```

## 2.4 Motion Design (動態設計)

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

## 2.5 Layout (佈局)

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

/* 創造視覺張力 */
.offset-section {
  margin-left: 15%;
  width: 85%;
}
```

## 2.6 Atmospheric Details (氛圍細節)

```css
/* 玻璃態效果 */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* 噪點紋理 */
.texture-overlay::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
}
```

## 2.7 設計禁止事項

| 避免 | 替代方案 |
|------|----------|
| Arial, Inter, system-ui | 特色字體如 Space Grotesk, Playfair Display |
| 紫色漸層 (#667eea → #764ba2) | 建立獨特的色彩系統 |
| 統一圓角 (rounded-lg everywhere) | 混合使用銳角與圓角創造對比 |
| 千篇一律的卡片元件 | 設計有個性的容器與邊框 |
| 置中對齊一切 | 使用不對稱佈局創造動態感 |

---

# Part 3: Web Artifacts 建構

> 來源: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

## 技術堆疊

| 技術 | 版本/說明 |
|------|-----------|
| React | 18.x |
| TypeScript | 嚴格類型檢查 |
| Vite | 開發環境 |
| Parcel | 打包成單一 HTML |
| Tailwind CSS | 3.4.1 |
| shadcn/ui | 40+ 預裝元件 |

## 3.1 工作流程

### 步驟 1: 初始化專案

```bash
./scripts/init-artifact.sh <project-name>

# 產生結構
<project-name>/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css
│   └── components/ui/
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

### 步驟 2: 開發元件

```tsx
import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="text-center space-y-4">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            Interactive Dashboard
          </h1>
        </header>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/50">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <Card className="bg-slate-800/30 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Counter Demo</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-4xl font-bold text-cyan-400">{count}</p>
              </CardContent>
              <CardFooter className="gap-2">
                <Button onClick={() => setCount(c => c - 1)} variant="outline">-</Button>
                <Button onClick={() => setCount(c => c + 1)}>+</Button>
              </CardFooter>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
```

### 步驟 3: 打包

```bash
./scripts/bundle-artifact.sh
# 輸出: dist/index.html (自包含)
```

## 3.2 shadcn/ui 元件

### 表單元件
```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
```

### 佈局元件
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
```

### 回饋元件
```tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
```

### 資料展示
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Calendar } from "@/components/ui/calendar"
```

### 導航元件
```tsx
import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuList } from "@/components/ui/navigation-menu"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
```

## 3.3 進階範例

### 資料表格
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

const data = [
  { id: 1, name: "Project Alpha", status: "active", progress: 75 },
  { id: 2, name: "Project Beta", status: "pending", progress: 30 },
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
              <Badge variant={row.status === 'active' ? 'default' : 'outline'}>
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

## 3.4 設計原則

### ✅ 正確做法
```tsx
// 獨特漸層背景
<div className="bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">

// 混合圓角
<Card className="rounded-none">
<Button className="rounded-full">

// 玻璃態效果
<Card className="bg-slate-800/30 backdrop-blur-lg border-slate-700/50">

// 不對稱佈局
<div className="grid grid-cols-3 gap-4">
  <div className="col-span-2">主要內容</div>
  <div>側邊欄</div>
</div>
```

### ❌ 避免做法
```tsx
// 過度置中
<div className="flex items-center justify-center">

// 紫色漸層
<div className="bg-gradient-to-r from-purple-500 to-pink-500">

// 統一圓角
<div className="rounded-lg">  // 所有元素都用

// Inter 字體
font-family: Inter, sans-serif;
```

---

# Part 4: Web 應用測試

## 使用 Playwright 測試

### 決策流程

```
應用類型？
├── 靜態 HTML → 直接讀取 HTML 找選擇器
├── 動態應用 (伺服器未啟動) → 使用 with_server.py
└── 動態應用 (伺服器已啟動) → 偵察-執行模式
```

### 啟動伺服器

```bash
# 單一伺服器
python scripts/with_server.py \
  --server "npm run dev" \
  --port 5173 \
  -- python your_automation.py

# 多伺服器
python scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python your_automation.py
```

### 自動化範例

```python
from playwright.sync_api import sync_playwright

def test_login_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://localhost:5173")
        page.wait_for_load_state("networkidle")

        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')

        page.wait_for_selector("text=Welcome")
        assert page.is_visible("text=Dashboard")

        page.screenshot(path="login-success.png")
        browser.close()
```

### 選擇器最佳實踐

```python
# ✅ 優先使用
page.click('role=button[name="Submit"]')  # 角色 + 名稱
page.click('text=Click me')               # 文字內容
page.click('#submit-btn')                 # ID
page.click('[data-testid="submit"]')      # 測試屬性

# ❌ 避免
page.click('div > div > button')          # 脆弱結構
page.click('.css-1a2b3c')                 # 自動生成 class
```

### Console 日誌捕捉

```python
def capture_console_logs(page):
    logs = []
    page.on("console", lambda msg: logs.append({
        "type": msg.type,
        "text": msg.text
    }))

    page.goto("http://localhost:5173")
    errors = [log for log in logs if log["type"] == "error"]
    if errors:
        print("Console Errors:", errors)
```

---

# Part 5: 主題工廠

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

## 主題套用

```tsx
interface Theme {
  name: string;
  colors: { primary: string; secondary: string; accent: string; background: string; surface: string; text: string; };
  fonts: { heading: string; body: string; };
}

function ThemeProvider({ theme, children }: { theme: Theme; children: React.ReactNode }) {
  useEffect(() => {
    const root = document.documentElement;
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });
    root.style.setProperty('--font-heading', theme.fonts.heading);
    root.style.setProperty('--font-body', theme.fonts.body);
  }, [theme]);

  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
}
```

---

# Part 6: 視覺設計

## 適用於
- 海報設計
- 藝術作品
- PDF/PNG 靜態設計

## 兩步驟流程

### 步驟 1: 設計哲學 (.md)

```markdown
# [作品名稱] Design Philosophy

## Space and Form (空間與形態)
描述正負空間、形狀語言...

## Color and Material (色彩與材質)
調色板、材質質感、光影處理...

## Scale and Rhythm (比例與韻律)
元素大小關係、視覺節奏...

## Composition and Balance (構圖與平衡)
視覺重心、動態平衡...

## Visual Hierarchy (視覺層次)
引導觀者目光的順序...
```

### 步驟 2: 畫布表現 (.pdf/.png)

**核心原則：**
- 90% 視覺設計 / 10% 必要文字
- 博物館等級的品質標準
- 完美間距，無重疊
- 使用重複圖案建立視覺語言

**設計元素：**
```
視覺語言: 幾何圖形系統、線條粗細、圓角半徑、間距單位
色彩運用: 主色調(60%)、輔助色(30%)、強調色(10%)
排版: 標題(大粗)、副標題(中等)、正文(最小化)
```

---

# Part 7: 內部通訊

> 來源: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

## 通訊類型

| 類型 | 說明 | 受眾 |
|------|------|------|
| 3P Updates | 進度/計畫/問題週報 | 領導層 |
| Newsletter | 公司整體動態 | 全公司 |
| FAQ | 常見問題回覆 | 內部/外部 |
| Status Reports | 專案狀態報告 | 利益關係人 |
| Incident Reports | 事件處理報告 | 技術團隊 |

## 7.1 3P Updates

### 格式
```
[emoji] [團隊名稱] (日期範圍)

Progress (進度): [1-3 句話]
Plans (計畫): [1-3 句話]
Problems (問題): [1-3 句話]
```

### 範例
```
🚀 Platform Team (Dec 16-20, 2024)

Progress: Shipped user authentication v2.0 with SSO support (3,000+ users migrated). Reduced API latency by 40% through database optimization.

Plans: Launch payment integration beta to 100 pilot users. Finalize Q1 roadmap with product team.

Problems: Third-party SMS provider experiencing intermittent outages (ETA fix: Dec 23). Need additional frontend engineer for mobile timeline.
```

### 撰寫原則
```
❌ "Made good progress on performance"
✅ "Reduced page load time from 3.2s to 1.1s (66% improvement)"

❌ "Fixed several bugs"
✅ "Resolved 23 customer-reported issues (bug backlog down 40%)"
```

## 7.2 Company Newsletter

```markdown
# [公司名稱] Weekly Update
[日期範圍]

## 🎯 重大公告
- [重要消息 1]

## 🚀 各部門亮點

### Product
- [成就 1]

### Engineering
- [成就 1]

## 📊 關鍵指標
- 月活躍用戶: 125,000 (+15% MoM)
- 客戶留存率: 94% (+2%)

## 👥 人員動態
- 歡迎: Sarah Chen (Engineering)
- 晉升: Lisa Huang → Senior PM

## 📅 即將到來
- 12/25: 聖誕節假期
- 1/3: 全員大會

## 🔗 重要連結
- [Q1 產品路線圖](link)
```

## 7.3 FAQ

```markdown
## Q: 如何申請遠端工作？

**簡短答案**: 透過 HR 系統提交申請，主管核准後即可開始。

**詳細說明**:
1. 登入 HR Portal → 「工作安排」
2. 填寫「遠端工作申請表」
3. 主管將於 3 個工作天內審核

**相關資源**:
- [遠端工作政策](link)

**聯絡窗口**: HR Team (hr@company.com)
```

## 7.4 Status Reports

```markdown
# [專案名稱] Status Report
日期: [YYYY-MM-DD]
報告人: [姓名]

## 整體狀態: 🟢 On Track / 🟡 At Risk / 🔴 Blocked

## 本週摘要
[2-3 句概述]

## 完成事項
- [x] [任務 1]

## 進行中
- [ ] [任務 2] - [進度 %] - [預計完成日]

## 阻礙與風險
| 項目 | 影響 | 緩解措施 | 負責人 |
|------|------|----------|--------|
| [阻礙] | 高 | [措施] | [人名] |

## 下週計畫
- [ ] [任務 3]
```

## 7.5 Incident Reports

```markdown
# Incident Report: [事件標題]
嚴重程度: P1 / P2 / P3 / P4
狀態: 調查中 / 已緩解 / 已解決

## 時間軸 (UTC)
- **14:30** - 事件發現
- **14:45** - 開始調查
- **15:30** - 事件解決

## 影響
- 影響服務: [服務名稱]
- 影響用戶: [數量/百分比]
- 影響時長: [時間]

## 根本原因
[說明]

## 解決方案
[說明]

## 後續行動
- [ ] [行動 1] - @[負責人] - [截止日]

## 經驗教訓
- [學到什麼]
```

## 7.6 語調指南

| 情境 | 語調 | 範例 |
|------|------|------|
| 一般更新 | 專業友善 | "很高興分享..." |
| 緊急通知 | 直接明確 | "需要立即行動：..." |
| 慶祝成就 | 熱情正向 | "恭喜團隊！..." |
| 壞消息 | 誠實同理 | "我們需要分享一個困難的消息..." |
| 政策變更 | 清晰解釋 | "從 [日期] 開始，我們將..." |

## 7.7 發送前檢查清單

```
□ 主題清楚描述內容
□ 最重要資訊在開頭
□ 包含必要日期/數字
□ 連結可正常開啟
□ 行動要求明確
□ 收件人正確
□ 語調適合情境
□ 已校對錯字格式
```

---

# 快速參考

## 常用 Import

```tsx
// React 核心
import { useState, useEffect, useContext, useRef, useMemo, useCallback } from 'react';

// shadcn/ui
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// 工具
import { cn } from "@/lib/utils";
```

## 設計檢查清單

```
□ 字體獨特且適合專案
□ 色彩系統使用 CSS 變數
□ 佈局有視覺張力
□ 動畫有明確目的
□ 避免通用 AI 設計模式
□ 細節經過打磨
```

## 測試指令

```bash
# Playwright 測試
python -m pytest tests/ -v

# 帶伺服器測試
python scripts/with_server.py --server "npm run dev" --port 5173 -- python test.py

# 截圖
playwright screenshot http://localhost:5173 --full-page
```

---

*Sources:*
- *[Anthropic Skills Repository](https://github.com/anthropics/skills)*
- *[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)*
