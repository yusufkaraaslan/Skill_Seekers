# Tiptap Editor Skill

> 基於 [Tiptap 官方文件](https://tiptap.dev/docs) 與 [GitHub 原始碼](https://github.com/ueberdosis/tiptap) 整理的完整開發指南

## 適用情境

當使用者需要以下協助時使用此指令：
- 建立 Tiptap 富文本編輯器
- 自訂 Nodes、Marks、Extensions
- 整合 React/Vue/Svelte 框架
- 實作協作編輯功能
- 處理 ProseMirror 相關問題

---

## 1. 概述

Tiptap 是一個基於 [ProseMirror](https://prosemirror.net/) 的無頭 (headless) 富文本編輯器框架。

### 專案統計 (2025)

| 指標 | 數值 |
|------|------|
| GitHub Stars | 34.3k+ |
| 最新版本 | v3.14.0 |
| Contributors | 444+ |
| 語言 | TypeScript (99%) |
| License | MIT |

### 核心特色

- **無頭架構**: 不預設 UI，完全自由設計介面
- **框架無關**: React, Vue 2/3, Svelte, 原生 JS
- **100+ 擴充套件**: 從基本格式到進階區塊編輯
- **即時協作**: 整合 Hocuspocus (Y.js CRDT)
- **Pro 擴充**: AI、版本控制、評論功能

---

## 2. 安裝與設定

### 2.1 React 安裝

```bash
npm install @tiptap/react @tiptap/pm @tiptap/starter-kit
```

**基本使用:**

```tsx
'use client' // Next.js 需要

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

const Tiptap = () => {
  const editor = useEditor({
    extensions: [StarterKit],
    content: '<p>Hello World!</p>',
    // Next.js SSR 關鍵設定
    immediatelyRender: false,
  })

  return <EditorContent editor={editor} />
}

export default Tiptap
```

### 2.2 Vue 3 安裝

```bash
npm install @tiptap/vue-3 @tiptap/pm @tiptap/starter-kit
```

**Composition API:**

```vue
<template>
  <editor-content :editor="editor" />
</template>

<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'

const editor = useEditor({
  extensions: [StarterKit],
  content: '<p>Hello World!</p>',
})
</script>
```

### 2.3 原生 JavaScript

```bash
npm install @tiptap/core @tiptap/pm @tiptap/starter-kit
```

```js
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'

const editor = new Editor({
  element: document.querySelector('.editor'),
  extensions: [StarterKit],
  content: '<p>Hello World!</p>',
})
```

---

## 3. 核心概念

### 3.1 文件結構

Tiptap 文件是一個 JSON 樹狀結構：

```json
{
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "Hello ",
          "marks": [{ "type": "bold" }]
        },
        {
          "type": "text",
          "text": "World!"
        }
      ]
    }
  ]
}
```

**關鍵概念:**
- **Nodes**: 區塊級元素 (paragraph, heading, codeBlock)
- **Marks**: 內聯樣式 (bold, italic, link)
- **Extensions**: 功能擴充 (history, collaboration)
- **Attributes**: 節點/標記的屬性

### 3.2 Schema

Schema 定義文件的允許結構：

```ts
import { Node } from '@tiptap/core'

const CustomParagraph = Node.create({
  name: 'customParagraph',
  group: 'block',
  content: 'inline*',

  parseHTML() {
    return [{ tag: 'p' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['p', HTMLAttributes, 0]
  },
})
```

**content 屬性語法:**

| 表達式 | 說明 |
|--------|------|
| `inline*` | 零或多個內聯節點 |
| `block+` | 一或多個區塊節點 |
| `text*` | 零或多個文字節點 |
| `paragraph heading*` | 一個段落，後接零或多個標題 |
| `(paragraph \| heading)+` | 一或多個段落或標題 |

---

## 4. StarterKit (24 擴充套件)

StarterKit 包含最常用的擴充套件，可個別配置或禁用。

### 4.1 完整擴充清單

**文字格式 (Marks):**
- Bold, Italic, Underline, Strike, Code

**區塊元素 (Nodes):**
- Document, Paragraph, Text
- Heading, Blockquote, HorizontalRule
- CodeBlock, HardBreak

**列表:**
- BulletList, OrderedList, ListItem, ListKeymap

**工具:**
- Link, Dropcursor, Gapcursor
- TrailingNode, Undo/Redo (History)

### 4.2 配置 StarterKit

```ts
import StarterKit from '@tiptap/starter-kit'

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      // 限制標題層級
      heading: {
        levels: [1, 2, 3],
      },
      // 禁用擴充 (設為 false)
      history: false,
      codeBlock: false,
      // 自訂選項
      bold: {
        HTMLAttributes: { class: 'font-bold' },
      },
    }),
  ],
})
```

---

## 5. Editor API

### 5.1 EditorOptions (完整選項)

```ts
interface EditorOptions {
  // DOM 掛載點
  element: HTMLElement

  // 初始內容 (HTML 或 JSON)
  content: string | JSONContent

  // 擴充套件陣列
  extensions: Extension[]

  // 是否可編輯
  editable: boolean

  // 自動對焦設定
  autofocus: boolean | 'start' | 'end' | 'all' | number

  // 注入預設 CSS
  injectCSS: boolean

  // 生命週期事件
  onBeforeCreate: ({ editor }) => void
  onCreate: ({ editor }) => void
  onMount: ({ editor }) => void
  onUpdate: ({ editor }) => void
  onFocus: ({ editor, event }) => void
  onBlur: ({ editor, event }) => void
  onDestroy: () => void

  // 內容事件
  onPaste: (event, slice) => boolean
  onDrop: (event, slice, moved) => boolean
  onDelete: () => boolean
  onContentError: ({ error }) => void
}
```

### 5.2 useEditor Hook (React)

```ts
import { useEditor } from '@tiptap/react'

const editor = useEditor({
  extensions: [StarterKit],
  content: '<p>Hello</p>',

  // SSR 設定 (Next.js 必要)
  immediatelyRender: false,

  // 是否在 transaction 時重新渲染 (效能考量)
  shouldRerenderOnTransaction: false,

  // 事件處理
  onUpdate: ({ editor }) => {
    console.log(editor.getHTML())
  },
}, [/* 依賴陣列 - 觸發 editor 重建 */])

// 回傳型別
// immediatelyRender: false → Editor | null
// 預設 → Editor
```

### 5.3 Editor 實例方法

```ts
// === 內容存取 ===
editor.getHTML()         // HTML 字串
editor.getJSON()         // JSON 物件
editor.getText()         // 純文字
editor.isEmpty           // 是否為空

// === 設定內容 ===
editor.commands.setContent('<p>New content</p>')
editor.commands.setContent({ type: 'doc', content: [...] })
editor.commands.clearContent()

// === 插入內容 ===
editor.commands.insertContent('Hello')
editor.commands.insertContentAt(10, 'World')

// === 焦點控制 ===
editor.commands.focus()
editor.commands.focus('start')
editor.commands.focus('end')
editor.commands.focus(15)  // 特定位置
editor.commands.blur()

// === 選取操作 ===
editor.commands.selectAll()
editor.commands.setTextSelection({ from: 0, to: 10 })
editor.commands.setNodeSelection(5)

// === 狀態查詢 ===
editor.isEditable      // 可編輯
editor.isFocused       // 有焦點
editor.isDestroyed     // 已銷毀
editor.isInitialized   // 已初始化

// === 生命週期 ===
editor.mount(element)  // 掛載到 DOM
editor.unmount()       // 卸載 (保留狀態)
editor.destroy()       // 完全銷毀

// === 進階查詢 ===
editor.$pos(10)        // 位置查詢工具
editor.$node('heading') // 節點查詢
editor.$nodes('paragraph') // 多節點查詢
```

### 5.4 Command 系統

```ts
// === 直接執行 ===
editor.commands.toggleBold()

// === Chain 執行 (推薦) ===
editor.chain().focus().toggleBold().run()

// === 檢查是否可執行 ===
if (editor.can().chain().focus().toggleBold().run()) {
  // 可以執行
}

// === Chain 原理 ===
// 累積命令 → run() 一次執行
// 避免多次 transaction
editor.chain()
  .focus()
  .toggleBold()
  .toggleItalic()
  .setLink({ href: 'https://example.com' })
  .run()

// === 狀態檢查 ===
editor.isActive('bold')
editor.isActive('heading', { level: 1 })
editor.isActive('link', { href: 'https://example.com' })
editor.getAttributes('link') // { href: '...', target: '...' }
```

---

## 6. 自訂擴充

### 6.1 Extension (功能擴充)

```ts
import { Extension } from '@tiptap/core'

const CustomExtension = Extension.create({
  name: 'customExtension',

  // 配置選項
  addOptions() {
    return {
      myOption: 'default',
    }
  },

  // 持久儲存
  addStorage() {
    return {
      count: 0,
    }
  },

  // 自訂命令
  addCommands() {
    return {
      myCommand: (param) => ({ commands, editor }) => {
        this.storage.count++
        return commands.insertContent(`Hello ${param}!`)
      },
    }
  },

  // 鍵盤快捷鍵
  addKeyboardShortcuts() {
    return {
      'Mod-Shift-x': () => this.editor.commands.myCommand('World'),
    }
  },

  // 輸入規則 (打字自動轉換)
  addInputRules() {
    return []
  },

  // 貼上規則
  addPasteRules() {
    return []
  },

  // ProseMirror 外掛
  addProseMirrorPlugins() {
    return []
  },
})

// 使用與擴充
const ConfiguredExtension = CustomExtension.configure({
  myOption: 'custom value',
})

const ExtendedExtension = CustomExtension.extend({
  name: 'extendedExtension',
  // 覆寫或新增功能
})
```

### 6.2 Node (節點)

```ts
import { Node, mergeAttributes } from '@tiptap/core'

const CustomNode = Node.create({
  name: 'customNode',

  // === Schema 定義 ===
  group: 'block',           // 區塊群組
  content: 'inline*',       // 內容模式
  inline: false,            // 行內節點
  atom: false,              // 原子節點 (不可編輯內部)
  selectable: true,         // 可選取
  draggable: false,         // 可拖曳
  isolating: false,         // 隔離編輯操作
  code: false,              // 程式碼內容
  whitespace: 'normal',     // 空白處理 ('normal' | 'pre')

  // === 屬性定義 ===
  addAttributes() {
    return {
      color: {
        default: 'blue',
        parseHTML: element => element.getAttribute('data-color'),
        renderHTML: attributes => ({
          'data-color': attributes.color,
          style: `color: ${attributes.color}`,
        }),
      },
      size: {
        default: 'medium',
        // 不輸出到 HTML
        rendered: false,
      },
    }
  },

  // === HTML 解析 ===
  parseHTML() {
    return [
      { tag: 'div[data-type="custom"]' },
      { tag: 'div.custom-node' },
    ]
  },

  // === HTML 渲染 ===
  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(
      { 'data-type': 'custom', class: 'custom-node' },
      HTMLAttributes
    ), 0]  // 0 = 內容插入點
  },

  // === 純文字渲染 ===
  renderText({ node }) {
    return `[Custom: ${node.attrs.color}]`
  },

  // === 自訂命令 ===
  addCommands() {
    return {
      setCustomNode: (attributes) => ({ commands }) => {
        return commands.setNode(this.name, attributes)
      },
      toggleCustomNode: () => ({ commands }) => {
        return commands.toggleNode(this.name, 'paragraph')
      },
    }
  },

  // === Node View (自訂渲染) ===
  addNodeView() {
    return ({ node, HTMLAttributes, getPos, editor }) => {
      const dom = document.createElement('div')
      // 自訂渲染邏輯
      return { dom }
    }
  },
})
```

### 6.3 Mark (標記)

```ts
import { Mark, mergeAttributes } from '@tiptap/core'

const Highlight = Mark.create({
  name: 'highlight',

  // === Schema 定義 ===
  inclusive: true,        // 擴展到相鄰輸入
  excludes: '',           // 排斥的 marks
  exitable: true,         // 可退出 mark
  spanning: true,         // 跨節點
  code: false,            // 程式碼樣式

  addOptions() {
    return {
      HTMLAttributes: {},
      colors: ['yellow', 'green', 'pink'],
    }
  },

  addAttributes() {
    return {
      color: {
        default: 'yellow',
        parseHTML: element =>
          element.style.backgroundColor || 'yellow',
        renderHTML: attributes => ({
          style: `background-color: ${attributes.color}`,
        }),
      },
    }
  },

  parseHTML() {
    return [
      { tag: 'mark' },
      {
        style: 'background-color',
        getAttrs: value => value !== 'transparent' && null,
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['mark', mergeAttributes(
      this.options.HTMLAttributes,
      HTMLAttributes
    ), 0]
  },

  addCommands() {
    return {
      setHighlight: (attributes) => ({ commands }) => {
        return commands.setMark(this.name, attributes)
      },
      toggleHighlight: (attributes) => ({ commands }) => {
        return commands.toggleMark(this.name, attributes)
      },
      unsetHighlight: () => ({ commands }) => {
        return commands.unsetMark(this.name)
      },
    }
  },

  addKeyboardShortcuts() {
    return {
      'Mod-Shift-h': () => this.editor.commands.toggleHighlight(),
    }
  },
})
```

---

## 7. Node Views (自訂渲染)

### 7.1 React Node View

```tsx
import {
  NodeViewWrapper,
  NodeViewContent,
  ReactNodeViewRenderer
} from '@tiptap/react'
import { Node, mergeAttributes } from '@tiptap/core'

// React 元件
const CounterComponent = ({ node, updateAttributes, deleteNode }) => {
  return (
    <NodeViewWrapper className="counter-component">
      {/* contentEditable={false} 避免游標進入 */}
      <div contentEditable={false}>
        <label>Count: {node.attrs.count}</label>
        <button onClick={() => updateAttributes({ count: node.attrs.count + 1 })}>
          +
        </button>
        <button onClick={deleteNode}>刪除</button>
      </div>
      {/* NodeViewContent 為可編輯區域 */}
      <NodeViewContent className="content" />
    </NodeViewWrapper>
  )
}

// Node 定義
const Counter = Node.create({
  name: 'counter',
  group: 'block',
  content: 'inline*',
  atom: false,

  addAttributes() {
    return {
      count: { default: 0 },
    }
  },

  parseHTML() {
    return [{ tag: 'div[data-type="counter"]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes({ 'data-type': 'counter' }, HTMLAttributes), 0]
  },

  addNodeView() {
    return ReactNodeViewRenderer(CounterComponent)
  },

  addCommands() {
    return {
      insertCounter: () => ({ commands }) => {
        return commands.insertContent({
          type: this.name,
          attrs: { count: 0 },
        })
      },
    }
  },
})
```

### 7.2 Vue 3 Node View

```vue
<!-- CounterComponent.vue -->
<template>
  <node-view-wrapper class="counter-component">
    <div contenteditable="false">
      <label>Count: {{ node.attrs.count }}</label>
      <button @click="increment">+</button>
      <button @click="deleteNode">刪除</button>
    </div>
    <node-view-content class="content" />
  </node-view-wrapper>
</template>

<script setup>
import { NodeViewWrapper, NodeViewContent, nodeViewProps } from '@tiptap/vue-3'

const props = defineProps(nodeViewProps)

const increment = () => {
  props.updateAttributes({ count: props.node.attrs.count + 1 })
}
</script>
```

```ts
// Node 定義
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import CounterComponent from './CounterComponent.vue'

const Counter = Node.create({
  // ... 同上
  addNodeView() {
    return VueNodeViewRenderer(CounterComponent)
  },
})
```

---

## 8. 官方擴充套件

### 8.1 完整套件清單 (57+)

**核心:**
- `@tiptap/core` - 編輯器核心
- `@tiptap/pm` - ProseMirror 封裝
- `@tiptap/starter-kit` - 入門套件
- `@tiptap/react` / `@tiptap/vue-3` / `@tiptap/vue-2` - 框架整合

**文字格式:**
- `extension-bold`, `extension-italic`, `extension-underline`
- `extension-strike`, `extension-code`, `extension-subscript`
- `extension-superscript`, `extension-highlight`, `extension-text-style`
- `extension-color`, `extension-font-family`, `extension-text-align`

**區塊元素:**
- `extension-paragraph`, `extension-heading`, `extension-blockquote`
- `extension-code-block`, `extension-code-block-lowlight`
- `extension-horizontal-rule`, `extension-hard-break`
- `extension-document`, `extension-text`

**列表:**
- `extension-bullet-list`, `extension-ordered-list`, `extension-list`

**連結與媒體:**
- `extension-link`, `extension-image`, `extension-youtube`, `extension-twitch`

**表格:**
- `extension-table`, `extension-table-row`
- `extension-table-header`, `extension-table-cell`

**UI 元件:**
- `extension-bubble-menu`, `extension-floating-menu`
- `extension-drag-handle`, `extension-drag-handle-react/vue-2/vue-3`

**進階功能:**
- `extension-mention`, `extension-emoji`
- `extension-collaboration`, `extension-collaboration-caret`
- `extension-typography`, `extension-placeholder`
- `extension-file-handler`, `extension-unique-id`
- `extension-invisible-characters`, `extension-table-of-contents`
- `extension-mathematics`, `extension-details`
- `extension-node-range`

**工具:**
- `suggestion` - 建議/自動完成框架
- `html` - HTML 解析/序列化
- `markdown` - Markdown 支援
- `static-renderer` - 靜態渲染

### 8.2 Link (連結)

```ts
import Link from '@tiptap/extension-link'

Link.configure({
  // 自動偵測 URL 並轉換
  autolink: true,

  // 預設協議
  defaultProtocol: 'https',

  // 自訂協議白名單
  protocols: ['ftp', 'mailto', 'tel'],

  // 點擊開啟連結
  openOnClick: true,

  // 點擊時選取連結
  enableClickSelection: false,

  // 貼上時自動建立連結
  linkOnPaste: true,

  // HTML 屬性
  HTMLAttributes: {
    rel: 'noopener noreferrer nofollow',
    target: '_blank',
    class: 'custom-link',
  },

  // XSS 防護 - URL 驗證
  isAllowedUri: (url, ctx) => {
    // 回傳 true 允許, false 拒絕
    return !url.startsWith('javascript:')
  },
})

// 命令
editor.chain().focus().setLink({ href: 'https://example.com' }).run()
editor.chain().focus().toggleLink({ href: 'https://example.com' }).run()
editor.chain().focus().unsetLink().run()

// 更新連結
editor.chain()
  .focus()
  .extendMarkRange('link')
  .setLink({ href: 'https://new-url.com' })
  .run()
```

### 8.3 Image (圖片)

```ts
import Image from '@tiptap/extension-image'

Image.configure({
  // 行內或區塊
  inline: false,

  // 允許 base64
  allowBase64: true,

  // 調整大小設定
  resize: {
    directions: ['se'],  // 調整方向
    minWidth: 100,
    minHeight: 100,
  },

  HTMLAttributes: {
    class: 'editor-image',
  },
})

// 命令
editor.chain().focus().setImage({
  src: 'https://example.com/image.jpg',
  alt: 'Description',
  title: 'Image Title',
  width: 300,
  height: 200,
}).run()
```

### 8.4 Mention (@提及)

```ts
import Mention from '@tiptap/extension-mention'
import { ReactRenderer } from '@tiptap/react'
import tippy from 'tippy.js'

Mention.configure({
  HTMLAttributes: {
    class: 'mention',
  },

  // 支援多種觸發字元
  suggestions: [
    {
      char: '@',
      items: async ({ query }) => {
        // 搜尋使用者
        return users.filter(u => u.name.includes(query))
      },
      render: () => {
        let component
        let popup

        return {
          onStart: props => {
            component = new ReactRenderer(MentionList, {
              props,
              editor: props.editor,
            })
            popup = tippy('body', {
              getReferenceClientRect: props.clientRect,
              appendTo: () => document.body,
              content: component.element,
              interactive: true,
            })
          },
          onUpdate: props => {
            component.updateProps(props)
            popup[0].setProps({ getReferenceClientRect: props.clientRect })
          },
          onKeyDown: props => {
            if (props.event.key === 'Escape') {
              popup[0].hide()
              return true
            }
            return component.ref?.onKeyDown(props)
          },
          onExit: () => {
            popup[0].destroy()
            component.destroy()
          },
        }
      },
    },
    {
      char: '#',
      items: ({ query }) => tags.filter(t => t.includes(query)),
      // ... 渲染邏輯
    },
  ],

  // 刪除 mention 時是否保留觸發字元
  deleteTriggerWithBackspace: false,
})
```

### 8.5 Table (表格)

```ts
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableHeader from '@tiptap/extension-table-header'
import TableCell from '@tiptap/extension-table-cell'

// 全部一起使用
const editor = useEditor({
  extensions: [
    StarterKit,
    Table.configure({
      resizable: true,
      HTMLAttributes: {
        class: 'custom-table',
      },
    }),
    TableRow,
    TableHeader,
    TableCell,
  ],
})

// 命令
editor.chain().focus().insertTable({
  rows: 3,
  cols: 3,
  withHeaderRow: true
}).run()

editor.chain().focus().addColumnAfter().run()
editor.chain().focus().addColumnBefore().run()
editor.chain().focus().addRowAfter().run()
editor.chain().focus().addRowBefore().run()
editor.chain().focus().deleteColumn().run()
editor.chain().focus().deleteRow().run()
editor.chain().focus().deleteTable().run()
editor.chain().focus().mergeCells().run()
editor.chain().focus().splitCell().run()
editor.chain().focus().toggleHeaderRow().run()
editor.chain().focus().toggleHeaderColumn().run()
editor.chain().focus().toggleHeaderCell().run()
```

### 8.6 Collaboration (協作編輯)

```ts
import Collaboration from '@tiptap/extension-collaboration'
import CollaborationCursor from '@tiptap/extension-collaboration-cursor'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
// 或使用 Hocuspocus
import { HocuspocusProvider } from '@hocuspocus/provider'

// Y.js 文件
const ydoc = new Y.Doc()

// WebSocket 連線
const provider = new WebsocketProvider(
  'wss://your-server.com',
  'room-name',
  ydoc
)

// 或 Hocuspocus
const provider = new HocuspocusProvider({
  url: 'wss://your-hocuspocus-server.com',
  name: 'document-name',
  document: ydoc,
})

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      // 重要：禁用內建歷史，使用協作歷史
      history: false,
    }),

    Collaboration.configure({
      document: ydoc,
      field: 'content',  // Y.js fragment 名稱

      // 內容驗證 (防止無效內容)
      enableContentCheck: true,
    }),

    CollaborationCursor.configure({
      provider,
      user: {
        name: 'User Name',
        color: '#f783ac',
      },
    }),
  ],
})

// 協作專用命令
editor.commands.undo()  // 協作版 undo
editor.commands.redo()  // 協作版 redo
```

---

## 9. 樣式

### 9.1 基本 CSS

```css
/* 編輯器容器 */
.tiptap {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  min-height: 200px;
  outline: none;
}

/* 焦點狀態 */
.tiptap:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Placeholder */
.tiptap p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  color: #94a3b8;
  pointer-events: none;
  float: left;
  height: 0;
}

/* 標題 */
.tiptap h1 { font-size: 2rem; font-weight: 700; margin: 1rem 0; }
.tiptap h2 { font-size: 1.5rem; font-weight: 600; margin: 0.75rem 0; }
.tiptap h3 { font-size: 1.25rem; font-weight: 600; margin: 0.5rem 0; }

/* 程式碼區塊 */
.tiptap pre {
  background: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.tiptap pre code {
  background: none;
  padding: 0;
}

/* 行內程式碼 */
.tiptap code {
  background: #f1f5f9;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.9em;
}

/* 引用 */
.tiptap blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #64748b;
  font-style: italic;
}

/* 連結 */
.tiptap a {
  color: #3b82f6;
  text-decoration: underline;
  cursor: pointer;
}

/* 列表 */
.tiptap ul { list-style-type: disc; padding-left: 1.5rem; }
.tiptap ol { list-style-type: decimal; padding-left: 1.5rem; }

/* 分隔線 */
.tiptap hr {
  border: none;
  border-top: 2px solid #e2e8f0;
  margin: 1.5rem 0;
}

/* 表格 */
.tiptap table {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
}

.tiptap th, .tiptap td {
  border: 1px solid #e2e8f0;
  padding: 0.5rem;
  text-align: left;
}

.tiptap th {
  background: #f8fafc;
  font-weight: 600;
}
```

### 9.2 Tailwind CSS

```tsx
<EditorContent
  editor={editor}
  className="prose prose-sm sm:prose lg:prose-lg max-w-none focus:outline-none"
/>
```

**prose 自訂:**

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            'code::before': { content: '""' },
            'code::after': { content: '""' },
          },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
```

---

## 10. 最佳實踐

### ✅ 正確做法

1. **使用 chain()**: 組合多個命令，減少 transaction

   ```ts
   // 好
   editor.chain().focus().toggleBold().toggleItalic().run()

   // 避免
   editor.commands.toggleBold()
   editor.commands.toggleItalic()
   ```

2. **檢查命令可用性**:

   ```ts
   const canToggleBold = editor.can().chain().focus().toggleBold().run()

   <button disabled={!canToggleBold}>Bold</button>
   ```

3. **使用 TypeScript**: 獲得完整型別支援

4. **模組化擴充**: 每個功能獨立成擴充

5. **避免 onUpdate 中修改內容**:

   ```ts
   // ❌ 危險 - 可能無限迴圈
   onUpdate: ({ editor }) => {
     editor.commands.insertContent('!')
   }

   // ✅ 安全 - 只讀取
   onUpdate: ({ editor }) => {
     saveToDatabase(editor.getJSON())
   }
   ```

6. **SSR 處理 (Next.js)**:

   ```tsx
   const editor = useEditor({
     extensions: [StarterKit],
     content: '<p>Hello</p>',
     immediatelyRender: false, // 關鍵
   })

   if (!editor) return null
   ```

### ❌ 避免做法

1. **直接修改 state**: 使用 commands 或 transactions
2. **重複初始化 editor**: 使用 `useEditor` 回傳值
3. **在 hooks 中建立 transactions**: 可能導致無限迴圈
4. **忽略 editor null 檢查**: SSR 環境必須處理

---

## 11. 常見問題

### Q: Next.js Hydration 錯誤

```tsx
'use client'

const editor = useEditor({
  extensions: [StarterKit],
  content: '<p>Hello</p>',
  immediatelyRender: false, // 關鍵
})

// 確保 editor 存在
if (!editor) {
  return <div>Loading...</div>
}
```

### Q: 如何取得選取的文字

```ts
const { from, to } = editor.state.selection
const text = editor.state.doc.textBetween(from, to)
```

### Q: 如何監聽變更

```ts
const editor = useEditor({
  onUpdate: ({ editor }) => {
    const html = editor.getHTML()
    const json = editor.getJSON()
    debouncedSave(json)
  },
})
```

### Q: 如何設定唯讀

```ts
// 動態切換
editor.setEditable(false)

// 初始設定
const editor = useEditor({
  editable: false,
})
```

### Q: 如何自訂 Placeholder

```ts
import Placeholder from '@tiptap/extension-placeholder'

Placeholder.configure({
  placeholder: ({ node }) => {
    if (node.type.name === 'heading') {
      return 'Enter a heading...'
    }
    if (node.type.name === 'codeBlock') {
      return 'Write code...'
    }
    return 'Write something...'
  },
})
```

### Q: 如何處理圖片上傳

```ts
import { Plugin } from '@tiptap/pm/state'

const ImageUpload = Extension.create({
  name: 'imageUpload',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        props: {
          handleDrop: (view, event, slice, moved) => {
            const files = event.dataTransfer?.files
            if (files?.[0]?.type.startsWith('image/')) {
              event.preventDefault()
              uploadImage(files[0]).then(url => {
                this.editor.commands.setImage({ src: url })
              })
              return true
            }
            return false
          },
          handlePaste: (view, event) => {
            const files = event.clipboardData?.files
            if (files?.[0]?.type.startsWith('image/')) {
              event.preventDefault()
              uploadImage(files[0]).then(url => {
                this.editor.commands.setImage({ src: url })
              })
              return true
            }
            return false
          },
        },
      }),
    ]
  },
})
```

---

## 12. 快速參考

### 常用 Commands

| Command | 說明 |
|---------|------|
| `toggleBold()` | 切換粗體 |
| `toggleItalic()` | 切換斜體 |
| `toggleUnderline()` | 切換底線 |
| `toggleStrike()` | 切換刪除線 |
| `toggleCode()` | 切換行內程式碼 |
| `toggleHeading({ level })` | 切換標題 |
| `toggleBulletList()` | 切換無序列表 |
| `toggleOrderedList()` | 切換有序列表 |
| `toggleBlockquote()` | 切換引用 |
| `toggleCodeBlock()` | 切換程式碼區塊 |
| `setLink({ href })` | 設定連結 |
| `unsetLink()` | 移除連結 |
| `setImage({ src })` | 插入圖片 |
| `setTextAlign('center')` | 文字對齊 |
| `undo()` | 復原 |
| `redo()` | 重做 |

### 鍵盤快捷鍵 (預設)

| 快捷鍵 | 功能 |
|--------|------|
| `Mod-B` | 粗體 |
| `Mod-I` | 斜體 |
| `Mod-U` | 底線 |
| `Mod-E` | 行內程式碼 |
| `Mod-`\` | 程式碼區塊 |
| `Mod-Shift-7` | 有序列表 |
| `Mod-Shift-8` | 無序列表 |
| `Mod-Z` | 復原 |
| `Mod-Shift-Z` / `Mod-Y` | 重做 |
| `Mod-Enter` | 硬換行 |
| `Shift-Enter` | 軟換行 |

---

## 13. 實戰應用指南

### 13.1 快速選擇：依需求選擇擴充套件

```
需求分析決策樹：

基本文字編輯 (部落格、留言)
├── StarterKit ✓ (已包含基本功能)
├── + Placeholder (輸入提示)
├── + CharacterCount (字數限制)
└── + Link (超連結)

進階文件編輯 (Wiki、文件系統)
├── StarterKit ✓
├── + Table (表格)
├── + Image (圖片)
├── + TaskList (待辦清單)
├── + TextAlign (對齊)
└── + Typography (排版優化)

程式碼編輯器 (技術文件)
├── StarterKit ✓
├── + CodeBlockLowlight (語法高亮)
├── + Mathematics (數學公式)
└── + Mention (@ 提及)

協作編輯 (團隊文件)
├── StarterKit.configure({ history: false })
├── + Collaboration
├── + CollaborationCursor
└── + UniqueId (節點追蹤)

Notion-like 區塊編輯器
├── StarterKit ✓
├── + DragHandle
├── + FloatingMenu
├── + BubbleMenu
├── + Placeholder (每區塊)
└── + UniqueId
```

### 13.2 完整範例：部落格編輯器

```tsx
// components/BlogEditor.tsx
'use client'

import { useEditor, EditorContent, BubbleMenu } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import CharacterCount from '@tiptap/extension-character-count'
import { useCallback, useState } from 'react'

interface BlogEditorProps {
  content?: string
  onChange?: (html: string, json: object) => void
  maxLength?: number
}

export default function BlogEditor({
  content = '',
  onChange,
  maxLength = 10000,
}: BlogEditorProps) {
  const [linkUrl, setLinkUrl] = useState('')

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Link.configure({
        openOnClick: false,
        autolink: true,
        defaultProtocol: 'https',
      }),
      Image.configure({
        inline: false,
        allowBase64: true,
      }),
      Placeholder.configure({
        placeholder: '開始撰寫你的文章...',
      }),
      CharacterCount.configure({
        limit: maxLength,
      }),
    ],
    content,
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML(), editor.getJSON())
    },
  })

  const setLink = useCallback(() => {
    if (!editor) return
    if (linkUrl) {
      editor.chain().focus().setLink({ href: linkUrl }).run()
    } else {
      editor.chain().focus().unsetLink().run()
    }
    setLinkUrl('')
  }, [editor, linkUrl])

  const addImage = useCallback(() => {
    const url = window.prompt('輸入圖片網址')
    if (url && editor) {
      editor.chain().focus().setImage({ src: url }).run()
    }
  }, [editor])

  if (!editor) return null

  const { characters, words } = editor.storage.characterCount

  return (
    <div className="blog-editor">
      {/* 工具列 */}
      <div className="toolbar">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={editor.isActive('bold') ? 'active' : ''}
        >
          B
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={editor.isActive('italic') ? 'active' : ''}
        >
          I
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={editor.isActive('heading', { level: 1 }) ? 'active' : ''}
        >
          H1
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={editor.isActive('heading', { level: 2 }) ? 'active' : ''}
        >
          H2
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive('bulletList') ? 'active' : ''}
        >
          • List
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={editor.isActive('orderedList') ? 'active' : ''}
        >
          1. List
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={editor.isActive('blockquote') ? 'active' : ''}
        >
          Quote
        </button>
        <button
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={editor.isActive('codeBlock') ? 'active' : ''}
        >
          Code
        </button>
        <button onClick={addImage}>Image</button>
        <button
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
        >
          Undo
        </button>
        <button
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
        >
          Redo
        </button>
      </div>

      {/* Bubble Menu (選取文字時顯示) */}
      <BubbleMenu editor={editor} tippyOptions={{ duration: 100 }}>
        <div className="bubble-menu">
          <button
            onClick={() => editor.chain().focus().toggleBold().run()}
            className={editor.isActive('bold') ? 'active' : ''}
          >
            Bold
          </button>
          <button
            onClick={() => editor.chain().focus().toggleItalic().run()}
            className={editor.isActive('italic') ? 'active' : ''}
          >
            Italic
          </button>
          <input
            type="text"
            placeholder="https://..."
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setLink()}
          />
          <button onClick={setLink}>Link</button>
        </div>
      </BubbleMenu>

      {/* 編輯器 */}
      <EditorContent editor={editor} className="editor-content" />

      {/* 字數統計 */}
      <div className="character-count">
        {characters} / {maxLength} 字元 | {words} 字
      </div>
    </div>
  )
}
```

### 13.3 完整範例：留言輸入框

```tsx
// components/CommentInput.tsx
'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Mention from '@tiptap/extension-mention'
import CharacterCount from '@tiptap/extension-character-count'
import { forwardRef, useImperativeHandle } from 'react'

interface User {
  id: string
  name: string
  avatar: string
}

interface CommentInputProps {
  onSubmit: (html: string, mentions: string[]) => void
  users: User[]
  maxLength?: number
  placeholder?: string
}

export interface CommentInputRef {
  clear: () => void
  focus: () => void
  getContent: () => string
}

const CommentInput = forwardRef<CommentInputRef, CommentInputProps>(
  ({ onSubmit, users, maxLength = 500, placeholder = '輸入留言...' }, ref) => {
    const editor = useEditor({
      extensions: [
        StarterKit.configure({
          heading: false,
          codeBlock: false,
          blockquote: false,
          horizontalRule: false,
        }),
        Placeholder.configure({ placeholder }),
        CharacterCount.configure({ limit: maxLength }),
        Mention.configure({
          HTMLAttributes: { class: 'mention' },
          suggestion: {
            items: ({ query }) => {
              return users
                .filter((user) =>
                  user.name.toLowerCase().includes(query.toLowerCase())
                )
                .slice(0, 5)
            },
            render: () => {
              let popup: HTMLElement | null = null

              return {
                onStart: (props) => {
                  popup = document.createElement('div')
                  popup.className = 'mention-popup'
                  document.body.appendChild(popup)
                  updatePopup(props)
                },
                onUpdate: updatePopup,
                onKeyDown: (props) => {
                  if (props.event.key === 'Escape') {
                    popup?.remove()
                    return true
                  }
                  return false
                },
                onExit: () => popup?.remove(),
              }

              function updatePopup(props: any) {
                if (!popup) return
                const items = props.items as User[]
                popup.innerHTML = items
                  .map(
                    (user, i) =>
                      `<div class="mention-item" data-index="${i}">
                        <img src="${user.avatar}" />
                        <span>${user.name}</span>
                      </div>`
                  )
                  .join('')

                popup.querySelectorAll('.mention-item').forEach((el, i) => {
                  el.addEventListener('click', () => {
                    props.command({ id: items[i].id, label: items[i].name })
                  })
                })

                const rect = props.clientRect?.()
                if (rect) {
                  popup.style.cssText = `
                    position: fixed;
                    left: ${rect.left}px;
                    top: ${rect.bottom + 5}px;
                  `
                }
              }
            },
          },
        }),
      ],
      immediatelyRender: false,
    })

    useImperativeHandle(ref, () => ({
      clear: () => editor?.commands.clearContent(),
      focus: () => editor?.commands.focus(),
      getContent: () => editor?.getHTML() || '',
    }))

    const handleSubmit = () => {
      if (!editor || editor.isEmpty) return

      // 提取所有 mention
      const mentions: string[] = []
      editor.state.doc.descendants((node) => {
        if (node.type.name === 'mention') {
          mentions.push(node.attrs.id)
        }
      })

      onSubmit(editor.getHTML(), mentions)
      editor.commands.clearContent()
    }

    if (!editor) return null

    const remaining = maxLength - editor.storage.characterCount.characters

    return (
      <div className="comment-input">
        <EditorContent editor={editor} />
        <div className="comment-footer">
          <span className={remaining < 50 ? 'warning' : ''}>
            剩餘 {remaining} 字
          </span>
          <button onClick={handleSubmit} disabled={editor.isEmpty}>
            送出
          </button>
        </div>
      </div>
    )
  }
)

CommentInput.displayName = 'CommentInput'
export default CommentInput
```

### 13.4 表單整合模式

```tsx
// React Hook Form 整合
import { useForm, Controller } from 'react-hook-form'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

interface FormData {
  title: string
  content: string
}

function ArticleForm() {
  const { control, handleSubmit, setValue, watch } = useForm<FormData>()

  const editor = useEditor({
    extensions: [StarterKit],
    content: '',
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      setValue('content', editor.getHTML(), { shouldValidate: true })
    },
  })

  // 監聽外部變更
  const content = watch('content')
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content || '')
    }
  }, [content, editor])

  const onSubmit = (data: FormData) => {
    console.log(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Controller
        name="title"
        control={control}
        rules={{ required: '標題必填' }}
        render={({ field, fieldState }) => (
          <div>
            <input {...field} placeholder="標題" />
            {fieldState.error && <span>{fieldState.error.message}</span>}
          </div>
        )}
      />

      <Controller
        name="content"
        control={control}
        rules={{
          required: '內容必填',
          validate: (value) =>
            value.replace(/<[^>]*>/g, '').length >= 10 || '至少 10 個字',
        }}
        render={({ fieldState }) => (
          <div>
            <EditorContent editor={editor} />
            {fieldState.error && <span>{fieldState.error.message}</span>}
          </div>
        )}
      />

      <button type="submit">送出</button>
    </form>
  )
}
```

### 13.5 Toolbar 元件封裝

```tsx
// components/EditorToolbar.tsx
import { Editor } from '@tiptap/react'
import { useCallback } from 'react'

interface ToolbarProps {
  editor: Editor | null
}

interface ToolbarButton {
  icon: string
  title: string
  action: () => boolean
  isActive?: () => boolean
  canExecute?: () => boolean
}

export default function EditorToolbar({ editor }: ToolbarProps) {
  if (!editor) return null

  const buttons: ToolbarButton[] = [
    // 文字格式
    {
      icon: 'B',
      title: '粗體 (Ctrl+B)',
      action: () => editor.chain().focus().toggleBold().run(),
      isActive: () => editor.isActive('bold'),
    },
    {
      icon: 'I',
      title: '斜體 (Ctrl+I)',
      action: () => editor.chain().focus().toggleItalic().run(),
      isActive: () => editor.isActive('italic'),
    },
    {
      icon: 'S',
      title: '刪除線',
      action: () => editor.chain().focus().toggleStrike().run(),
      isActive: () => editor.isActive('strike'),
    },
    {
      icon: '</>',
      title: '行內程式碼',
      action: () => editor.chain().focus().toggleCode().run(),
      isActive: () => editor.isActive('code'),
    },
    // 分隔符
    { icon: '|', title: '', action: () => false },
    // 標題
    {
      icon: 'H1',
      title: '標題 1',
      action: () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
      isActive: () => editor.isActive('heading', { level: 1 }),
    },
    {
      icon: 'H2',
      title: '標題 2',
      action: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
      isActive: () => editor.isActive('heading', { level: 2 }),
    },
    {
      icon: 'H3',
      title: '標題 3',
      action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
      isActive: () => editor.isActive('heading', { level: 3 }),
    },
    // 分隔符
    { icon: '|', title: '', action: () => false },
    // 列表
    {
      icon: '•',
      title: '無序列表',
      action: () => editor.chain().focus().toggleBulletList().run(),
      isActive: () => editor.isActive('bulletList'),
    },
    {
      icon: '1.',
      title: '有序列表',
      action: () => editor.chain().focus().toggleOrderedList().run(),
      isActive: () => editor.isActive('orderedList'),
    },
    // 區塊
    {
      icon: '"',
      title: '引用',
      action: () => editor.chain().focus().toggleBlockquote().run(),
      isActive: () => editor.isActive('blockquote'),
    },
    {
      icon: '{ }',
      title: '程式碼區塊',
      action: () => editor.chain().focus().toggleCodeBlock().run(),
      isActive: () => editor.isActive('codeBlock'),
    },
    {
      icon: '—',
      title: '分隔線',
      action: () => editor.chain().focus().setHorizontalRule().run(),
    },
    // 分隔符
    { icon: '|', title: '', action: () => false },
    // 歷史
    {
      icon: '↶',
      title: '復原 (Ctrl+Z)',
      action: () => editor.chain().focus().undo().run(),
      canExecute: () => editor.can().undo(),
    },
    {
      icon: '↷',
      title: '重做 (Ctrl+Y)',
      action: () => editor.chain().focus().redo().run(),
      canExecute: () => editor.can().redo(),
    },
  ]

  return (
    <div className="editor-toolbar">
      {buttons.map((btn, i) =>
        btn.icon === '|' ? (
          <span key={i} className="toolbar-divider" />
        ) : (
          <button
            key={i}
            type="button"
            title={btn.title}
            onClick={btn.action}
            disabled={btn.canExecute ? !btn.canExecute() : false}
            className={btn.isActive?.() ? 'active' : ''}
          >
            {btn.icon}
          </button>
        )
      )}
    </div>
  )
}
```

### 13.6 效能優化技巧

```tsx
// 1. 避免不必要的重新渲染
const editor = useEditor({
  extensions: [StarterKit],
  // 預設 false，避免每次 transaction 觸發重渲染
  shouldRerenderOnTransaction: false,
})

// 2. 使用 useMemo 緩存擴充套件
const extensions = useMemo(() => [
  StarterKit.configure({ history: { depth: 50 } }),
  Link,
  Image,
], [])

const editor = useEditor({ extensions })

// 3. Debounce 儲存操作
import { useDebouncedCallback } from 'use-debounce'

const debouncedSave = useDebouncedCallback((content: string) => {
  saveToServer(content)
}, 1000)

const editor = useEditor({
  extensions: [StarterKit],
  onUpdate: ({ editor }) => {
    debouncedSave(editor.getHTML())
  },
})

// 4. 大文件優化 - 使用虛擬化
// 對於非常長的文件，考慮分頁或懶載入

// 5. 圖片懶載入
const LazyImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      loading: { default: 'lazy' },
    }
  },
})

// 6. 減少擴充套件 - 只載入需要的
// ❌ 不要這樣
import StarterKit from '@tiptap/starter-kit' // 載入所有 24 個擴充

// ✅ 只載入需要的
import Document from '@tiptap/extension-document'
import Paragraph from '@tiptap/extension-paragraph'
import Text from '@tiptap/extension-text'
import Bold from '@tiptap/extension-bold'
import Italic from '@tiptap/extension-italic'
import History from '@tiptap/extension-history'

const MinimalEditor = () => {
  const editor = useEditor({
    extensions: [Document, Paragraph, Text, Bold, Italic, History],
  })
  return <EditorContent editor={editor} />
}
```

### 13.7 伺服器端渲染 (SSR) 完整方案

```tsx
// components/Editor.tsx
'use client'

import dynamic from 'next/dynamic'
import { Skeleton } from '@/components/ui/skeleton'

// 動態載入，禁用 SSR
const TiptapEditor = dynamic(() => import('./TiptapEditor'), {
  ssr: false,
  loading: () => <Skeleton className="h-64 w-full" />,
})

export default function Editor(props: EditorProps) {
  return <TiptapEditor {...props} />
}

// components/TiptapEditor.tsx
'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

export default function TiptapEditor({ content, onChange }) {
  const editor = useEditor({
    extensions: [StarterKit],
    content,
    immediatelyRender: false, // 關鍵！
    onUpdate: ({ editor }) => onChange?.(editor.getJSON()),
  })

  // 必須處理 null 狀態
  if (!editor) {
    return <div className="h-64 animate-pulse bg-gray-100" />
  }

  return <EditorContent editor={editor} />
}
```

---

## 14. 疑難排解決策樹

```
問題診斷流程：

編輯器不顯示
├── 檢查 editor 是否為 null
│   ├── SSR 環境？→ 設定 immediatelyRender: false
│   └── 確認 if (!editor) return null
├── 檢查 DOM 掛載點
│   └── 確認 element 存在
└── 檢查 Console 錯誤

內容無法編輯
├── 檢查 editable 設定
│   └── editor.setEditable(true)
├── 檢查 CSS pointer-events
└── 檢查是否被父元素覆蓋

格式按鈕無效
├── 確認使用 chain().focus()
├── 檢查 isActive 狀態
└── 確認擴充套件已安裝

協作同步失敗
├── 檢查 WebSocket 連線
├── 確認禁用內建 history
│   └── StarterKit.configure({ history: false })
├── 檢查 Y.js 版本相容性
└── 確認房間名稱一致

效能問題
├── 大文件卡頓
│   ├── 減少 history depth
│   ├── 使用 shouldRerenderOnTransaction: false
│   └── Debounce onUpdate
├── 記憶體洩漏
│   └── 確認 editor.destroy() 清理
└── 渲染緩慢
    └── 減少不必要的擴充套件

Hydration 錯誤 (Next.js)
├── 確認 'use client' 指令
├── 設定 immediatelyRender: false
├── 使用 dynamic import + ssr: false
└── 確保初始內容一致
```

---

## 15. 資源

### 官方資源
- [官方文件](https://tiptap.dev/docs)
- [GitHub](https://github.com/ueberdosis/tiptap) - 34.3k stars
- [擴充套件列表](https://tiptap.dev/docs/editor/extensions)
- [範例展示](https://tiptap.dev/examples)
- [Discord 社群](https://discord.gg/WtJ49jGshW)

### 相關技術
- [ProseMirror 指南](https://prosemirror.net/docs/guide/)
- [Hocuspocus 協作後端](https://hocuspocus.dev/)
- [Y.js CRDT 文件](https://docs.yjs.dev/)

### Pro 功能
- AI 整合
- 版本控制
- 評論功能
- 文件轉換

---

*Source: [Tiptap Documentation](https://tiptap.dev/docs) & [GitHub Repository](https://github.com/ueberdosis/tiptap)*
