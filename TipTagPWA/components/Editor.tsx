'use client'

import { useEditor, EditorContent, BubbleMenu } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Link from '@tiptap/extension-link'
import Highlight from '@tiptap/extension-highlight'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import CharacterCount from '@tiptap/extension-character-count'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { common, createLowlight } from 'lowlight'
import { useCallback, useEffect, useState } from 'react'
import { AISuggestionType, generateAIContent } from '@/utils/aiService'

const lowlight = createLowlight(common)

interface EditorProps {
  content?: string
  onChange?: (json: object, html: string) => void
  placeholder?: string
  editable?: boolean
}

export default function Editor({
  content = '',
  onChange,
  placeholder = '開始撰寫...',
  editable = true,
}: EditorProps) {
  const [isAIMenuOpen, setIsAIMenuOpen] = useState(false)
  const [isAILoading, setIsAILoading] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false,
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
      Link.configure({
        openOnClick: false,
        autolink: true,
        defaultProtocol: 'https',
      }),
      Highlight.configure({
        multicolor: false,
      }),
      TaskList,
      TaskItem.configure({
        nested: true,
      }),
      CharacterCount,
      CodeBlockLowlight.configure({
        lowlight,
      }),
    ],
    content,
    editable,
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getJSON(), editor.getHTML())
    },
  })

  useEffect(() => {
    if (editor && content && editor.getHTML() !== content) {
      editor.commands.setContent(content)
    }
  }, [content, editor])

  const setLink = useCallback(() => {
    if (!editor) return
    const previousUrl = editor.getAttributes('link').href
    const url = window.prompt('輸入連結 URL', previousUrl)

    if (url === null) return
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }

    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }, [editor])

  const handleAIAction = useCallback(async (type: AISuggestionType) => {
    if (!editor) return

    const { from, to } = editor.state.selection
    const selectedText = editor.state.doc.textBetween(from, to, ' ')
    const contextText = selectedText || editor.getText()

    if (!contextText.trim()) {
      setAiError('請先選取或輸入一些文字')
      setTimeout(() => setAiError(null), 3000)
      return
    }

    setIsAILoading(true)
    setIsAIMenuOpen(false)
    setAiError(null)

    try {
      const result = await generateAIContent(type, contextText)

      if (selectedText) {
        // Replace selected text
        editor.chain().focus().deleteSelection().insertContent(result).run()
      } else {
        // Append to end
        editor.chain().focus().insertContentAt(editor.state.doc.content.size, '\n\n' + result).run()
      }
    } catch (error) {
      setAiError(error instanceof Error ? error.message : '發生錯誤')
      setTimeout(() => setAiError(null), 3000)
    } finally {
      setIsAILoading(false)
    }
  }, [editor])

  if (!editor) {
    return (
      <div className="animate-pulse bg-gray-100 dark:bg-gray-800 rounded-lg h-64" />
    )
  }

  return (
    <div className="editor-wrapper">
      {/* Toolbar */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-2 flex flex-wrap gap-1">
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          isActive={editor.isActive('bold')}
          title="粗體 (Ctrl+B)"
        >
          <span className="font-bold">B</span>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          isActive={editor.isActive('italic')}
          title="斜體 (Ctrl+I)"
        >
          <span className="italic">I</span>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleStrike().run()}
          isActive={editor.isActive('strike')}
          title="刪除線"
        >
          <span className="line-through">S</span>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHighlight().run()}
          isActive={editor.isActive('highlight')}
          title="螢光筆"
        >
          <span className="bg-yellow-200 px-1">H</span>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleCode().run()}
          isActive={editor.isActive('code')}
          title="行內程式碼"
        >
          {'</>'}
        </ToolbarButton>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          isActive={editor.isActive('heading', { level: 1 })}
          title="標題 1"
        >
          H1
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          isActive={editor.isActive('heading', { level: 2 })}
          title="標題 2"
        >
          H2
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          isActive={editor.isActive('heading', { level: 3 })}
          title="標題 3"
        >
          H3
        </ToolbarButton>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          isActive={editor.isActive('bulletList')}
          title="無序列表"
        >
          •
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          isActive={editor.isActive('orderedList')}
          title="有序列表"
        >
          1.
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleTaskList().run()}
          isActive={editor.isActive('taskList')}
          title="待辦清單"
        >
          ☑
        </ToolbarButton>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          isActive={editor.isActive('blockquote')}
          title="引用"
        >
          "
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          isActive={editor.isActive('codeBlock')}
          title="程式碼區塊"
        >
          {'{ }'}
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().setHorizontalRule().run()}
          title="分隔線"
        >
          —
        </ToolbarButton>
        <ToolbarButton
          onClick={setLink}
          isActive={editor.isActive('link')}
          title="連結"
        >
          🔗
        </ToolbarButton>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

        <ToolbarButton
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
          title="復原 (Ctrl+Z)"
        >
          ↶
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
          title="重做 (Ctrl+Y)"
        >
          ↷
        </ToolbarButton>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

        {/* AI Menu */}
        <div className="relative">
          <ToolbarButton
            onClick={() => setIsAIMenuOpen(!isAIMenuOpen)}
            isActive={isAIMenuOpen}
            title="AI 助手"
            disabled={isAILoading}
          >
            {isAILoading ? '⏳' : '✨'}
          </ToolbarButton>

          {isAIMenuOpen && (
            <div className="absolute top-full left-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
              <div className="px-3 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                選取文字操作
              </div>
              <AIMenuItem
                onClick={() => handleAIAction(AISuggestionType.FIX_GRAMMAR)}
                icon="✏️"
                label="修正文法"
              />
              <AIMenuItem
                onClick={() => handleAIAction(AISuggestionType.SUMMARIZE)}
                icon="📝"
                label="摘要"
              />
              <AIMenuItem
                onClick={() => handleAIAction(AISuggestionType.REPHRASE)}
                icon="🔄"
                label="改寫"
              />

              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />

              <div className="px-3 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                生成內容
              </div>
              <AIMenuItem
                onClick={() => handleAIAction(AISuggestionType.EXPAND)}
                icon="📖"
                label="繼續撰寫"
              />
              <AIMenuItem
                onClick={() => handleAIAction(AISuggestionType.GENERATE_IDEAS)}
                icon="💡"
                label="產生想法"
              />

              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />

              <div className="px-3 py-1 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                翻譯
              </div>
              <AIMenuItem
                onClick={() => handleAIAction(AISuggestionType.TRANSLATE_EN)}
                icon="🇺🇸"
                label="翻譯為英文"
              />
              <AIMenuItem
                onClick={() => handleAIAction(AISuggestionType.TRANSLATE_ZH)}
                icon="🇹🇼"
                label="翻譯為中文"
              />
            </div>
          )}
        </div>
      </div>

      {/* Bubble Menu */}
      <BubbleMenu
        editor={editor}
        tippyOptions={{ duration: 100 }}
        className="bg-white dark:bg-gray-800 shadow-lg rounded-lg border border-gray-200 dark:border-gray-700 flex overflow-hidden"
      >
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          isActive={editor.isActive('bold')}
          size="sm"
        >
          B
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          isActive={editor.isActive('italic')}
          size="sm"
        >
          I
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleHighlight().run()}
          isActive={editor.isActive('highlight')}
          size="sm"
        >
          H
        </ToolbarButton>
        <ToolbarButton onClick={setLink} isActive={editor.isActive('link')} size="sm">
          🔗
        </ToolbarButton>
        <div className="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-0.5" />
        <ToolbarButton
          onClick={() => {
            setIsAIMenuOpen(true)
          }}
          size="sm"
          title="AI 助手"
        >
          ✨
        </ToolbarButton>
      </BubbleMenu>

      {/* Editor Content */}
      <div className="p-4 bg-white dark:bg-gray-900 min-h-[400px]">
        <EditorContent editor={editor} className="tiptap" />
      </div>

      {/* Character Count */}
      <div className="text-xs text-gray-500 dark:text-gray-400 p-2 border-t border-gray-200 dark:border-gray-700 flex justify-between">
        <span>{editor.storage.characterCount.characters()} 字元</span>
        <span>{editor.storage.characterCount.words()} 字</span>
      </div>

      {/* AI Error Toast */}
      {aiError && (
        <div className="fixed bottom-4 right-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 px-4 py-2 rounded-lg shadow-lg z-50">
          ❌ {aiError}
        </div>
      )}

      {/* AI Loading Indicator */}
      {isAILoading && (
        <div className="fixed bottom-4 right-4 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 px-4 py-2 rounded-lg shadow-lg z-50 flex items-center gap-2">
          <span className="animate-spin">⏳</span>
          AI 處理中...
        </div>
      )}
    </div>
  )
}

interface ToolbarButtonProps {
  onClick: () => void
  isActive?: boolean
  disabled?: boolean
  title?: string
  size?: 'sm' | 'md'
  children: React.ReactNode
}

function ToolbarButton({
  onClick,
  isActive = false,
  disabled = false,
  title,
  size = 'md',
  children,
}: ToolbarButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`
        ${size === 'sm' ? 'w-7 h-7 text-sm' : 'w-8 h-8'}
        flex items-center justify-center rounded
        transition-colors duration-150
        ${isActive
          ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
          : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {children}
    </button>
  )
}

interface AIMenuItemProps {
  onClick: () => void
  icon: string
  label: string
}

function AIMenuItem({ onClick, icon, label }: AIMenuItemProps) {
  return (
    <button
      onClick={onClick}
      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
    >
      <span>{icon}</span>
      <span className="text-gray-700 dark:text-gray-300">{label}</span>
    </button>
  )
}
