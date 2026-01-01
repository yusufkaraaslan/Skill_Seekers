import { openDB, DBSchema, IDBPDatabase } from 'idb'

export interface Note {
  id: string
  title: string
  content: string // JSON string from Tiptap
  htmlContent: string // HTML for preview
  category: string
  tags: string[]
  createdAt: number
  updatedAt: number
  isPinned: boolean
  isArchived: boolean
}

export interface Category {
  id: string
  name: string
  color: string
  icon: string
  order: number
}

interface TipTagDB extends DBSchema {
  notes: {
    key: string
    value: Note
    indexes: {
      'by-category': string
      'by-updated': number
      'by-created': number
    }
  }
  categories: {
    key: string
    value: Category
    indexes: {
      'by-order': number
    }
  }
}

const DB_NAME = 'tiptag-db'
const DB_VERSION = 1

let dbInstance: IDBPDatabase<TipTagDB> | null = null

export async function getDB(): Promise<IDBPDatabase<TipTagDB>> {
  if (dbInstance) return dbInstance

  dbInstance = await openDB<TipTagDB>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      // Notes store
      if (!db.objectStoreNames.contains('notes')) {
        const noteStore = db.createObjectStore('notes', { keyPath: 'id' })
        noteStore.createIndex('by-category', 'category')
        noteStore.createIndex('by-updated', 'updatedAt')
        noteStore.createIndex('by-created', 'createdAt')
      }

      // Categories store
      if (!db.objectStoreNames.contains('categories')) {
        const categoryStore = db.createObjectStore('categories', { keyPath: 'id' })
        categoryStore.createIndex('by-order', 'order')
      }
    },
  })

  // Initialize default categories if empty
  const categories = await dbInstance.getAll('categories')
  if (categories.length === 0) {
    const defaultCategories: Category[] = [
      { id: 'general', name: '一般', color: '#6b7280', icon: '📝', order: 0 },
      { id: 'work', name: '工作', color: '#3b82f6', icon: '💼', order: 1 },
      { id: 'study', name: '學習', color: '#10b981', icon: '📚', order: 2 },
      { id: 'ideas', name: '想法', color: '#f59e0b', icon: '💡', order: 3 },
      { id: 'personal', name: '個人', color: '#ec4899', icon: '🏠', order: 4 },
    ]
    for (const cat of defaultCategories) {
      await dbInstance.put('categories', cat)
    }
  }

  return dbInstance
}

// Note operations
export async function createNote(note: Omit<Note, 'id' | 'createdAt' | 'updatedAt'>): Promise<Note> {
  const db = await getDB()
  const now = Date.now()
  const newNote: Note = {
    ...note,
    id: crypto.randomUUID(),
    createdAt: now,
    updatedAt: now,
  }
  await db.put('notes', newNote)
  return newNote
}

export async function updateNote(id: string, updates: Partial<Note>): Promise<Note | null> {
  const db = await getDB()
  const note = await db.get('notes', id)
  if (!note) return null

  const updatedNote: Note = {
    ...note,
    ...updates,
    updatedAt: Date.now(),
  }
  await db.put('notes', updatedNote)
  return updatedNote
}

export async function deleteNote(id: string): Promise<boolean> {
  const db = await getDB()
  await db.delete('notes', id)
  return true
}

export async function getNote(id: string): Promise<Note | undefined> {
  const db = await getDB()
  return db.get('notes', id)
}

export async function getAllNotes(): Promise<Note[]> {
  const db = await getDB()
  const notes = await db.getAllFromIndex('notes', 'by-updated')
  return notes.reverse() // Most recent first
}

export async function getNotesByCategory(category: string): Promise<Note[]> {
  const db = await getDB()
  const notes = await db.getAllFromIndex('notes', 'by-category', category)
  return notes.sort((a, b) => b.updatedAt - a.updatedAt)
}

export async function searchNotes(query: string): Promise<Note[]> {
  const db = await getDB()
  const notes = await db.getAll('notes')
  const lowerQuery = query.toLowerCase()

  return notes
    .filter(note =>
      note.title.toLowerCase().includes(lowerQuery) ||
      note.htmlContent.toLowerCase().includes(lowerQuery) ||
      note.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    )
    .sort((a, b) => b.updatedAt - a.updatedAt)
}

// Category operations
export async function getAllCategories(): Promise<Category[]> {
  const db = await getDB()
  const categories = await db.getAllFromIndex('categories', 'by-order')
  return categories
}

export async function createCategory(category: Omit<Category, 'id'>): Promise<Category> {
  const db = await getDB()
  const newCategory: Category = {
    ...category,
    id: crypto.randomUUID(),
  }
  await db.put('categories', newCategory)
  return newCategory
}

export async function updateCategory(id: string, updates: Partial<Category>): Promise<Category | null> {
  const db = await getDB()
  const category = await db.get('categories', id)
  if (!category) return null

  const updatedCategory: Category = {
    ...category,
    ...updates,
  }
  await db.put('categories', updatedCategory)
  return updatedCategory
}

export async function deleteCategory(id: string): Promise<boolean> {
  const db = await getDB()
  // Move notes in this category to 'general'
  const notes = await getNotesByCategory(id)
  for (const note of notes) {
    await updateNote(note.id, { category: 'general' })
  }
  await db.delete('categories', id)
  return true
}

// Export/Import
export async function exportData(): Promise<{ notes: Note[]; categories: Category[] }> {
  const db = await getDB()
  const notes = await db.getAll('notes')
  const categories = await db.getAll('categories')
  return { notes, categories }
}

export async function importData(data: { notes: Note[]; categories: Category[] }): Promise<void> {
  const db = await getDB()

  // Import categories
  for (const category of data.categories) {
    await db.put('categories', category)
  }

  // Import notes
  for (const note of data.notes) {
    await db.put('notes', note)
  }
}

// Batch save notes (for GitHub sync)
export async function saveNotes(notes: Note[]): Promise<void> {
  const db = await getDB()
  for (const note of notes) {
    await db.put('notes', note)
  }
}
