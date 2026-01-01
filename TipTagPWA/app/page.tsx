'use client'

import { useState, useEffect, useCallback } from 'react'
import dynamic from 'next/dynamic'
import {
  getAllNotes,
  getAllCategories,
  createNote,
  updateNote,
  deleteNote,
  searchNotes,
  saveNotes,
  Note,
  Category
} from '@/utils/db'
import { Template } from '@/utils/templates'
import TemplateModal from '@/components/TemplateModal'
import GitHubSyncModal from '@/components/GitHubSyncModal'
import AISettingsModal from '@/components/AISettingsModal'

const Editor = dynamic(() => import('@/components/Editor'), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-gray-100 dark:bg-gray-800 rounded-lg h-64" />
})

export default function Home() {
  const [notes, setNotes] = useState<Note[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isDarkMode, setIsDarkMode] = useState(false)

  // Modal states
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false)
  const [isGitHubModalOpen, setIsGitHubModalOpen] = useState(false)
  const [isAISettingsOpen, setIsAISettingsOpen] = useState(false)

  // Load data on mount
  useEffect(() => {
    loadData()
    // Check for dark mode preference
    if (typeof window !== 'undefined') {
      const darkMode = localStorage.getItem('darkMode') === 'true' ||
        window.matchMedia('(prefers-color-scheme: dark)').matches
      setIsDarkMode(darkMode)
      document.documentElement.classList.toggle('dark', darkMode)
    }
  }, [])

  const loadData = async () => {
    const [loadedNotes, loadedCategories] = await Promise.all([
      getAllNotes(),
      getAllCategories()
    ])
    setNotes(loadedNotes)
    setCategories(loadedCategories)
  }

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query)
    if (query.trim()) {
      const results = await searchNotes(query)
      setNotes(results)
    } else {
      const allNotes = await getAllNotes()
      setNotes(allNotes)
    }
  }, [])

  const handleCategoryFilter = async (categoryId: string | null) => {
    setSelectedCategory(categoryId)
    if (categoryId) {
      const allNotes = await getAllNotes()
      setNotes(allNotes.filter(n => n.category === categoryId))
    } else {
      const allNotes = await getAllNotes()
      setNotes(allNotes)
    }
  }

  const handleCreateNote = async () => {
    const newNote = await createNote({
      title: '新筆記',
      content: '',
      htmlContent: '',
      category: selectedCategory || 'general',
      tags: [],
      isPinned: false,
      isArchived: false,
    })
    setNotes(prev => [newNote, ...prev])
    setSelectedNote(newNote)
    setIsEditing(true)
  }

  const handleTemplateSelect = async (template: Template) => {
    const newNote = await createNote({
      title: template.name,
      content: '',
      htmlContent: template.content,
      category: selectedCategory || 'general',
      tags: [],
      isPinned: false,
      isArchived: false,
    })
    setNotes(prev => [newNote, ...prev])
    setSelectedNote(newNote)
    setIsEditing(true)
    setIsTemplateModalOpen(false)
  }

  const handlePullComplete = async (pulledNotes: Note[]) => {
    // Merge pulled notes with existing notes
    const currentNotes = await getAllNotes()
    const mergedMap = new Map<string, Note>()

    currentNotes.forEach(n => mergedMap.set(n.id, n))
    pulledNotes.forEach(n => mergedMap.set(n.id, n))

    const mergedNotes = Array.from(mergedMap.values())
      .sort((a, b) => b.updatedAt - a.updatedAt)

    await saveNotes(mergedNotes)
    setNotes(mergedNotes)

    if (mergedNotes.length > 0) {
      setSelectedNote(mergedNotes[0])
      setIsEditing(true)
    }

    setIsGitHubModalOpen(false)
  }

  const handleUpdateNote = async (json: object, html: string) => {
    if (!selectedNote) return

    // Extract title from first heading or first line
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = html
    const firstHeading = tempDiv.querySelector('h1, h2, h3')
    const firstParagraph = tempDiv.querySelector('p')
    const title = firstHeading?.textContent || firstParagraph?.textContent?.slice(0, 50) || '無標題'

    const updated = await updateNote(selectedNote.id, {
      title: title.trim() || '無標題',
      content: JSON.stringify(json),
      htmlContent: html,
    })

    if (updated) {
      setNotes(prev => prev.map(n => n.id === updated.id ? updated : n))
      setSelectedNote(updated)
    }
  }

  const handleDeleteNote = async (noteId: string) => {
    if (!confirm('確定要刪除這個筆記嗎？')) return
    await deleteNote(noteId)
    setNotes(prev => prev.filter(n => n.id !== noteId))
    if (selectedNote?.id === noteId) {
      setSelectedNote(null)
      setIsEditing(false)
    }
  }

  const handleTogglePin = async (note: Note) => {
    const updated = await updateNote(note.id, { isPinned: !note.isPinned })
    if (updated) {
      setNotes(prev => prev.map(n => n.id === updated.id ? updated : n))
    }
  }

  const toggleDarkMode = () => {
    const newMode = !isDarkMode
    setIsDarkMode(newMode)
    localStorage.setItem('darkMode', String(newMode))
    document.documentElement.classList.toggle('dark', newMode)
  }

  const getCategoryById = (id: string) => categories.find(c => c.id === id)

  const sortedNotes = [...notes].sort((a, b) => {
    if (a.isPinned !== b.isPinned) return a.isPinned ? -1 : 1
    return b.updatedAt - a.updatedAt
  })

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className={`
        ${isSidebarOpen ? 'w-64' : 'w-0'}
        bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
        transition-all duration-300 overflow-hidden flex-shrink-0
      `}>
        <div className="p-4 h-full flex flex-col w-64">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">TipTag</h1>
            <div className="flex gap-1">
              <button
                onClick={() => setIsAISettingsOpen(true)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                title="AI 設定"
              >
                🤖
              </button>
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                title={isDarkMode ? '切換淺色模式' : '切換深色模式'}
              >
                {isDarkMode ? '☀️' : '🌙'}
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="relative mb-4">
            <input
              type="text"
              placeholder="搜尋筆記..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full px-3 py-2 pl-9 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
            />
            <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={handleCreateNote}
              className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors text-sm"
            >
              + 新增
            </button>
            <button
              onClick={() => setIsTemplateModalOpen(true)}
              className="px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
              title="使用模板"
            >
              📄
            </button>
          </div>

          {/* Categories */}
          <div className="mb-4 flex-1 overflow-y-auto">
            <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">分類</h2>
            <nav className="space-y-1">
              <button
                onClick={() => handleCategoryFilter(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedCategory === null
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                📋 全部筆記
              </button>
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => handleCategoryFilter(category.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  {category.icon} {category.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Footer */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
            <button
              onClick={() => setIsGitHubModalOpen(true)}
              className="w-full px-3 py-2 text-sm text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
            >
              🔗 GitHub 同步
            </button>
            <p className="text-xs text-gray-500 dark:text-gray-400 px-1">
              共 {notes.length} 個筆記
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Note List */}
        <div className="w-80 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-y-auto flex-shrink-0">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg mr-2"
            >
              ☰
            </button>
            <h2 className="font-semibold text-gray-900 dark:text-white flex-1">
              {selectedCategory
                ? getCategoryById(selectedCategory)?.name || '筆記'
                : searchQuery
                  ? `搜尋: ${searchQuery}`
                  : '全部筆記'
              }
            </h2>
          </div>

          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {sortedNotes.length === 0 ? (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                <p className="text-4xl mb-2">📝</p>
                <p>沒有筆記</p>
                <p className="text-sm mt-1">點擊「新增」開始</p>
              </div>
            ) : (
              sortedNotes.map(note => (
                <div
                  key={note.id}
                  onClick={() => {
                    setSelectedNote(note)
                    setIsEditing(true)
                  }}
                  className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                    selectedNote?.id === note.id ? 'bg-primary-50 dark:bg-primary-900/30' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {note.isPinned && <span title="已釘選">📌</span>}
                        <h3 className="font-medium text-gray-900 dark:text-white truncate">
                          {note.title}
                        </h3>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                        {note.htmlContent.replace(/<[^>]*>/g, '').slice(0, 100) || '空白筆記'}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs px-2 py-0.5 rounded-full" style={{
                          backgroundColor: (getCategoryById(note.category)?.color || '#6b7280') + '20',
                          color: getCategoryById(note.category)?.color || '#6b7280'
                        }}>
                          {getCategoryById(note.category)?.icon || '📁'} {getCategoryById(note.category)?.name || '未分類'}
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(note.updatedAt).toLocaleDateString('zh-TW')}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleTogglePin(note)
                        }}
                        className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                        title={note.isPinned ? '取消釘選' : '釘選'}
                      >
                        {note.isPinned ? '📌' : '📍'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteNote(note.id)
                        }}
                        className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500"
                        title="刪除"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Editor Area */}
        <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
          {selectedNote && isEditing ? (
            <div className="max-w-4xl mx-auto p-6">
              <div className="mb-4 flex items-center justify-between">
                <select
                  value={selectedNote.category}
                  onChange={async (e) => {
                    const updated = await updateNote(selectedNote.id, { category: e.target.value })
                    if (updated) {
                      setNotes(prev => prev.map(n => n.id === updated.id ? updated : n))
                      setSelectedNote(updated)
                    }
                  }}
                  className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
                <span className="text-sm text-gray-500">
                  最後更新: {new Date(selectedNote.updatedAt).toLocaleString('zh-TW')}
                </span>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
                <Editor
                  content={selectedNote.content ? JSON.parse(selectedNote.content) : ''}
                  onChange={handleUpdateNote}
                  placeholder="開始撰寫您的筆記..."
                  editable={true}
                />
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
              <div className="text-center">
                <p className="text-6xl mb-4">📝</p>
                <p className="text-xl font-medium">選擇或建立筆記</p>
                <p className="text-sm mt-2">從左側選擇筆記或點擊「新增」</p>
                <button
                  onClick={() => setIsTemplateModalOpen(true)}
                  className="mt-4 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
                >
                  📄 使用模板開始
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      <TemplateModal
        isOpen={isTemplateModalOpen}
        onClose={() => setIsTemplateModalOpen(false)}
        onSelect={handleTemplateSelect}
      />

      <GitHubSyncModal
        isOpen={isGitHubModalOpen}
        onClose={() => setIsGitHubModalOpen(false)}
        notes={notes}
        onPullComplete={handlePullComplete}
      />

      <AISettingsModal
        isOpen={isAISettingsOpen}
        onClose={() => setIsAISettingsOpen(false)}
      />
    </div>
  )
}
