# Tiptap Editor Skill

> 基於 [Tiptap 官方文件](https://tiptap.dev/docs) 整理的完整開發指南

## 適用情境

當使用者需要以下協助時使用此指令：
- 建立 Tiptap 富文本編輯器
- 自訂 Nodes、Marks、Extensions
- 整合 React/Vue/Svelte 框架
- 實作協作編輯功能
- 處理 ProseMirror 相關問題

---

## 1. 概述

Tiptap 是一個基於 [ProseMirror](https://prosemirror.net/) 的無頭 (headless) 富文本編輯器框架，提供：
- 100+ 擴充套件
- 框架無關 (React, Vue, Svelte, 原生 JS)
- 高度可自訂化
- 即時協作支援
- TypeScript 支援

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
    content: '<p>Hello World! 🌍</p>',
    // Next.js SSR 需要
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
  content: '<p>Hello World! 🌍</p>',
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

---

## 4. StarterKit

StarterKit 包含最常用的擴充套件：

### 4.1 包含的擴充

**Nodes:**
- Document, Paragraph, Text
- Heading, BulletList, OrderedList, ListItem
- CodeBlock, Blockquote, HorizontalRule
- HardBreak

**Marks:**
- Bold, Italic, Strike, Code

**功能:**
- History (Undo/Redo)
- Dropcursor, Gapcursor

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
      // 禁用某些擴充
      history: false,
      codeBlock: false,
    }),
  ],
})
```

---

## 5. Editor API

### 5.1 建立編輯器

```ts
import { useEditor } from '@tiptap/react'

const editor = useEditor({
  // 擴充套件
  extensions: [StarterKit],

  // 初始內容 (HTML 或 JSON)
  content: '<p>Hello</p>',

  // 事件
  onUpdate: ({ editor }) => {
    console.log(editor.getHTML())
  },

  onSelectionUpdate: ({ editor }) => {
    console.log('Selection changed')
  },

  onCreate: ({ editor }) => {
    console.log('Editor created')
  },

  onDestroy: () => {
    console.log('Editor destroyed')
  },

  // 選項
  editable: true,
  autofocus: true,
  injectCSS: true,
})
```

### 5.2 常用方法

```ts
// 取得內容
editor.getHTML()         // HTML 字串
editor.getJSON()         // JSON 物件
editor.getText()         // 純文字

// 設定內容
editor.commands.setContent('<p>New content</p>')
editor.commands.clearContent()

// 插入內容
editor.commands.insertContent('Hello')
editor.commands.insertContentAt(10, 'World')

// 焦點
editor.commands.focus()
editor.commands.focus('start')
editor.commands.focus('end')
editor.commands.blur()

// 選取
editor.commands.selectAll()
editor.commands.setTextSelection({ from: 0, to: 10 })

// 狀態
editor.isEditable
editor.isEmpty
editor.isFocused
editor.isDestroyed
```

### 5.3 Commands

```ts
// 文字格式
editor.chain().focus().toggleBold().run()
editor.chain().focus().toggleItalic().run()
editor.chain().focus().toggleStrike().run()
editor.chain().focus().toggleCode().run()

// 段落
editor.chain().focus().setParagraph().run()
editor.chain().focus().toggleHeading({ level: 1 }).run()
editor.chain().focus().toggleBulletList().run()
editor.chain().focus().toggleOrderedList().run()
editor.chain().focus().toggleBlockquote().run()
editor.chain().focus().toggleCodeBlock().run()

// 連結
editor.chain().focus().setLink({ href: 'https://example.com' }).run()
editor.chain().focus().unsetLink().run()

// 歷史
editor.chain().focus().undo().run()
editor.chain().focus().redo().run()

// 檢查狀態
editor.isActive('bold')
editor.isActive('heading', { level: 1 })
editor.isActive('link')
```

---

## 6. 自訂擴充

### 6.1 Extension (功能擴充)

```ts
import { Extension } from '@tiptap/core'

const CustomExtension = Extension.create({
  name: 'customExtension',

  addOptions() {
    return {
      myOption: 'default',
    }
  },

  addCommands() {
    return {
      myCommand: () => ({ commands }) => {
        return commands.insertContent('Hello!')
      },
    }
  },

  addKeyboardShortcuts() {
    return {
      'Mod-Shift-x': () => this.editor.commands.myCommand(),
    }
  },

  addInputRules() {
    return []
  },

  addPasteRules() {
    return []
  },
})
```

### 6.2 Node (節點)

```ts
import { Node, mergeAttributes } from '@tiptap/core'

const CustomNode = Node.create({
  name: 'customNode',
  group: 'block',
  content: 'inline*',

  addAttributes() {
    return {
      color: {
        default: 'blue',
        parseHTML: element => element.getAttribute('data-color'),
        renderHTML: attributes => {
          return { 'data-color': attributes.color }
        },
      },
    }
  },

  parseHTML() {
    return [
      { tag: 'div[data-type="custom"]' },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes({ 'data-type': 'custom' }, HTMLAttributes), 0]
  },

  addCommands() {
    return {
      setCustomNode: (attributes) => ({ commands }) => {
        return commands.setNode(this.name, attributes)
      },
    }
  },
})
```

### 6.3 Mark (標記)

```ts
import { Mark, mergeAttributes } from '@tiptap/core'

const Highlight = Mark.create({
  name: 'highlight',

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      color: {
        default: 'yellow',
      },
    }
  },

  parseHTML() {
    return [
      { tag: 'mark' },
      { style: 'background-color', getAttrs: value => !!value && null },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['mark', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0]
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
import { NodeViewWrapper, NodeViewContent, ReactNodeViewRenderer } from '@tiptap/react'
import { Node, mergeAttributes } from '@tiptap/core'

// React 元件
const Component = ({ node, updateAttributes }) => {
  return (
    <NodeViewWrapper className="custom-component">
      <label contentEditable={false}>Count:</label>
      <button
        onClick={() => updateAttributes({ count: node.attrs.count + 1 })}
      >
        {node.attrs.count}
      </button>
      <NodeViewContent className="content" />
    </NodeViewWrapper>
  )
}

// Node 定義
const CustomNode = Node.create({
  name: 'customComponent',
  group: 'block',
  content: 'inline*',

  addAttributes() {
    return {
      count: { default: 0 },
    }
  },

  parseHTML() {
    return [{ tag: 'custom-component' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['custom-component', mergeAttributes(HTMLAttributes), 0]
  },

  addNodeView() {
    return ReactNodeViewRenderer(Component)
  },
})
```

### 7.2 Vue Node View

```vue
<!-- CustomComponent.vue -->
<template>
  <node-view-wrapper class="custom-component">
    <label contenteditable="false">Count:</label>
    <button @click="increment">{{ node.attrs.count }}</button>
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

---

## 8. 常用擴充

### 8.1 Link

```ts
import Link from '@tiptap/extension-link'

const editor = useEditor({
  extensions: [
    StarterKit,
    Link.configure({
      openOnClick: true,
      autolink: true,
      defaultProtocol: 'https',
      HTMLAttributes: {
        rel: 'noopener noreferrer',
        target: '_blank',
      },
    }),
  ],
})

// 使用
editor.chain().focus().setLink({ href: 'https://example.com' }).run()
editor.chain().focus().extendMarkRange('link').setLink({ href: 'https://new.com' }).run()
editor.chain().focus().unsetLink().run()
```

### 8.2 Image

```ts
import Image from '@tiptap/extension-image'

const editor = useEditor({
  extensions: [
    StarterKit,
    Image.configure({
      inline: true,
      allowBase64: true,
    }),
  ],
})

// 使用
editor.chain().focus().setImage({ src: 'https://example.com/image.jpg', alt: 'Image' }).run()
```

### 8.3 Placeholder

```ts
import Placeholder from '@tiptap/extension-placeholder'

const editor = useEditor({
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: 'Write something …',
      // 或自訂每個節點
      placeholder: ({ node }) => {
        if (node.type.name === 'heading') {
          return 'Enter a heading'
        }
        return 'Write something …'
      },
    }),
  ],
})
```

### 8.4 Typography

```ts
import Typography from '@tiptap/extension-typography'

// 自動替換：
// (c) → ©
// (tm) → ™
// ... → …
// -> → →
// 1/2 → ½
```

### 8.5 Table

```ts
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableHeader from '@tiptap/extension-table-header'
import TableCell from '@tiptap/extension-table-cell'

const editor = useEditor({
  extensions: [
    StarterKit,
    Table.configure({
      resizable: true,
    }),
    TableRow,
    TableHeader,
    TableCell,
  ],
})

// 使用
editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
editor.chain().focus().addColumnAfter().run()
editor.chain().focus().addRowAfter().run()
editor.chain().focus().deleteColumn().run()
editor.chain().focus().deleteRow().run()
editor.chain().focus().deleteTable().run()
```

### 8.6 Collaboration

```ts
import Collaboration from '@tiptap/extension-collaboration'
import CollaborationCursor from '@tiptap/extension-collaboration-cursor'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'

const ydoc = new Y.Doc()
const provider = new WebsocketProvider('wss://your-server.com', 'room-name', ydoc)

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      history: false, // 禁用內建歷史，使用協作歷史
    }),
    Collaboration.configure({
      document: ydoc,
    }),
    CollaborationCursor.configure({
      provider,
      user: { name: 'User', color: '#f783ac' },
    }),
  ],
})
```

---

## 9. 樣式

### 9.1 基本 CSS

```css
/* 編輯器容器 */
.tiptap {
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  min-height: 200px;
}

/* 焦點狀態 */
.tiptap:focus-within {
  border-color: #007bff;
  outline: none;
}

/* Placeholder */
.tiptap p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  color: #adb5bd;
  pointer-events: none;
  float: left;
  height: 0;
}

/* 程式碼區塊 */
.tiptap pre {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}

.tiptap pre code {
  background: none;
  font-family: 'Fira Code', monospace;
}

/* 引用 */
.tiptap blockquote {
  border-left: 4px solid #007bff;
  padding-left: 1rem;
  margin-left: 0;
  color: #6c757d;
}

/* 連結 */
.tiptap a {
  color: #007bff;
  text-decoration: underline;
}
```

### 9.2 Tailwind CSS

```tsx
<EditorContent
  editor={editor}
  className="prose prose-sm sm:prose lg:prose-lg xl:prose-xl focus:outline-none"
/>
```

---

## 10. 最佳實踐

### ✅ 正確做法

1. **使用 chain()**: 組合多個命令
   ```ts
   editor.chain().focus().toggleBold().run()
   ```

2. **檢查命令是否可用**:
   ```ts
   if (editor.can().chain().focus().toggleBold().run()) {
     // 可以執行
   }
   ```

3. **使用 TypeScript**: 獲得完整型別支援

4. **模組化擴充**: 每個自訂功能獨立成擴充

5. **輕量 Node Views**: 避免複雜邏輯

### ❌ 避免做法

1. **在 hooks 中建立 transactions**: 可能導致無限迴圈
   ```ts
   // ❌ 錯誤
   onUpdate: ({ editor }) => {
     editor.commands.insertContent('!') // 無限迴圈
   }
   ```

2. **直接修改 state**: 使用 commands 或 transactions

3. **重複初始化 editor**: 使用 `useEditor` 的回傳值

---

## 11. 常見問題

### Q: Next.js SSR 問題

```tsx
'use client'

const editor = useEditor({
  extensions: [StarterKit],
  content: '<p>Hello</p>',
  immediatelyRender: false, // 關鍵
})
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
    // 儲存或處理
  },
})
```

### Q: 如何設定唯讀

```ts
editor.setEditable(false)
// 或
const editor = useEditor({
  editable: false,
})
```

---

## 12. 快速參考

### 常用 Commands

| Command | 說明 |
|---------|------|
| `toggleBold()` | 切換粗體 |
| `toggleItalic()` | 切換斜體 |
| `toggleStrike()` | 切換刪除線 |
| `toggleCode()` | 切換行內程式碼 |
| `toggleHeading({ level })` | 切換標題 |
| `toggleBulletList()` | 切換無序列表 |
| `toggleOrderedList()` | 切換有序列表 |
| `toggleBlockquote()` | 切換引用 |
| `toggleCodeBlock()` | 切換程式碼區塊 |
| `setLink({ href })` | 設定連結 |
| `unsetLink()` | 移除連結 |
| `undo()` | 復原 |
| `redo()` | 重做 |

### 鍵盤快捷鍵 (預設)

| 快捷鍵 | 功能 |
|--------|------|
| `Mod-B` | 粗體 |
| `Mod-I` | 斜體 |
| `Mod-U` | 底線 |
| `Mod-E` | 行內程式碼 |
| `Mod-Z` | 復原 |
| `Mod-Shift-Z` | 重做 |
| `Mod-Enter` | 硬換行 |
| `Shift-Enter` | 軟換行 |

---

## 13. 資源

- [官方文件](https://tiptap.dev/docs)
- [GitHub](https://github.com/ueberdosis/tiptap)
- [擴充套件列表](https://tiptap.dev/docs/editor/extensions)
- [ProseMirror 指南](https://prosemirror.net/docs/guide/)
- [Discord 社群](https://discord.gg/WtJ49jGshW)

---

*Source: [Tiptap Documentation](https://tiptap.dev/docs)*
