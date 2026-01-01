import { Note } from './db'

export interface GitHubConfig {
  token: string
  owner: string
  repo: string
  branch: string
  autoSync: boolean
  lastSyncAt: number | null
}

export interface SyncResult {
  pushed: number
  pulled: number
  skipped: number
  conflicts: SyncConflict[]
  timestamp: number
}

export interface SyncConflict {
  noteId: string
  noteTitle: string
  localUpdatedAt: number
  remoteUpdatedAt: number
  resolution: 'local' | 'remote' | 'pending'
}

const CONFIG_KEY = 'tiptag_github_config'
const SYNC_HISTORY_KEY = 'tiptag_sync_history'

export function saveGithubConfig(config: GitHubConfig): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config))
  }
}

export function getGithubConfig(): GitHubConfig | null {
  if (typeof window === 'undefined') return null
  const stored = localStorage.getItem(CONFIG_KEY)
  if (!stored) return null
  try {
    const config = JSON.parse(stored)
    // Ensure autoSync field exists for backward compatibility
    return {
      ...config,
      autoSync: config.autoSync ?? false,
      lastSyncAt: config.lastSyncAt ?? null,
    }
  } catch {
    return null
  }
}

export function clearGithubConfig(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(CONFIG_KEY)
    localStorage.removeItem(SYNC_HISTORY_KEY)
  }
}

export function getSyncHistory(): SyncResult[] {
  if (typeof window === 'undefined') return []
  const stored = localStorage.getItem(SYNC_HISTORY_KEY)
  if (!stored) return []
  try {
    return JSON.parse(stored)
  } catch {
    return []
  }
}

export function saveSyncHistory(result: SyncResult): void {
  if (typeof window !== 'undefined') {
    const history = getSyncHistory()
    history.unshift(result)
    // Keep only last 10 sync records
    localStorage.setItem(SYNC_HISTORY_KEY, JSON.stringify(history.slice(0, 10)))
  }
}

async function githubRequest(
  endpoint: string,
  config: GitHubConfig,
  options: RequestInit = {}
): Promise<Response> {
  const url = `https://api.github.com${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: 'application/vnd.github.v3+json',
      Authorization: `Bearer ${config.token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
  return response
}

export async function validateConfig(config: GitHubConfig): Promise<boolean> {
  try {
    const response = await githubRequest(
      `/repos/${config.owner}/${config.repo}`,
      config
    )
    return response.ok
  } catch {
    return false
  }
}

export async function createRepository(config: GitHubConfig): Promise<boolean> {
  try {
    const response = await githubRequest('/user/repos', config, {
      method: 'POST',
      body: JSON.stringify({
        name: config.repo,
        description: 'TipTag Knowledge Base Notes',
        private: true,
        auto_init: true,
      }),
    })
    return response.ok || response.status === 422 // 422 = already exists
  } catch {
    return false
  }
}

export async function ensureNotesDirectory(config: GitHubConfig): Promise<boolean> {
  try {
    // Check if notes directory exists
    const response = await githubRequest(
      `/repos/${config.owner}/${config.repo}/contents/notes?ref=${config.branch}`,
      config
    )

    if (response.ok) return true

    // Create notes directory with a .gitkeep file
    const createResponse = await githubRequest(
      `/repos/${config.owner}/${config.repo}/contents/notes/.gitkeep`,
      config,
      {
        method: 'PUT',
        body: JSON.stringify({
          message: 'Initialize notes directory',
          content: btoa(''),
          branch: config.branch,
        }),
      }
    )

    return createResponse.ok
  } catch {
    return false
  }
}

export async function pushNotes(
  notes: Note[],
  config: GitHubConfig
): Promise<{ pushed: number; skipped: number; failed: number }> {
  let pushed = 0
  let skipped = 0
  let failed = 0

  // Ensure notes directory exists
  await ensureNotesDirectory(config)

  for (const note of notes) {
    try {
      const path = `notes/${note.id}.json`
      const content = JSON.stringify(note, null, 2)
      const contentBase64 = btoa(unescape(encodeURIComponent(content)))

      // Check if file exists
      const existingResponse = await githubRequest(
        `/repos/${config.owner}/${config.repo}/contents/${path}?ref=${config.branch}`,
        config
      )

      let sha: string | undefined
      if (existingResponse.ok) {
        const existing = await existingResponse.json()
        sha = existing.sha

        // Check if content is the same
        try {
          const existingContent = decodeURIComponent(escape(atob(existing.content.replace(/\n/g, ''))))
          if (existingContent === content) {
            skipped++
            continue
          }
        } catch {
          // Content comparison failed, proceed with update
        }
      }

      // Create or update file
      const response = await githubRequest(
        `/repos/${config.owner}/${config.repo}/contents/${path}`,
        config,
        {
          method: 'PUT',
          body: JSON.stringify({
            message: `Update note: ${note.title}`,
            content: contentBase64,
            branch: config.branch,
            ...(sha && { sha }),
          }),
        }
      )

      if (response.ok) {
        pushed++
      } else {
        console.error('Failed to push note:', note.id, await response.text())
        failed++
      }
    } catch (error) {
      console.error('Error pushing note:', note.id, error)
      failed++
    }
  }

  // Update last sync time
  const currentConfig = getGithubConfig()
  if (currentConfig) {
    saveGithubConfig({ ...currentConfig, lastSyncAt: Date.now() })
  }

  return { pushed, skipped, failed }
}

export async function pullNotes(config: GitHubConfig): Promise<Note[]> {
  const notes: Note[] = []

  try {
    // List all files in notes directory
    const response = await githubRequest(
      `/repos/${config.owner}/${config.repo}/contents/notes?ref=${config.branch}`,
      config
    )

    if (!response.ok) {
      if (response.status === 404) {
        // Notes directory doesn't exist yet
        return []
      }
      throw new Error('Failed to list notes')
    }

    const files = await response.json()

    for (const file of files) {
      if (file.type === 'file' && file.name.endsWith('.json')) {
        try {
          const fileResponse = await githubRequest(
            `/repos/${config.owner}/${config.repo}/contents/${file.path}?ref=${config.branch}`,
            config
          )

          if (fileResponse.ok) {
            const fileData = await fileResponse.json()
            const content = decodeURIComponent(escape(atob(fileData.content.replace(/\n/g, ''))))
            const note = JSON.parse(content) as Note
            notes.push(note)
          }
        } catch (error) {
          console.error('Error reading note file:', file.name, error)
        }
      }
    }
  } catch (error) {
    console.error('Error pulling notes:', error)
    throw error
  }

  // Update last sync time
  const currentConfig = getGithubConfig()
  if (currentConfig) {
    saveGithubConfig({ ...currentConfig, lastSyncAt: Date.now() })
  }

  return notes.sort((a, b) => b.updatedAt - a.updatedAt)
}

export async function syncNotes(
  localNotes: Note[],
  config: GitHubConfig,
  conflictResolution: 'local' | 'remote' | 'newer' = 'newer'
): Promise<SyncResult> {
  const conflicts: SyncConflict[] = []
  let pushed = 0
  let pulled = 0
  let skipped = 0

  try {
    // Pull remote notes first
    const remoteNotes = await pullNotes(config)
    const remoteNotesMap = new Map(remoteNotes.map(n => [n.id, n]))
    const localNotesMap = new Map(localNotes.map(n => [n.id, n]))

    // Find notes to push (local only or local newer)
    const notesToPush: Note[] = []
    for (const localNote of localNotes) {
      const remoteNote = remoteNotesMap.get(localNote.id)
      if (!remoteNote) {
        // New local note
        notesToPush.push(localNote)
      } else if (localNote.updatedAt > remoteNote.updatedAt) {
        // Local is newer
        if (conflictResolution === 'local' || conflictResolution === 'newer') {
          notesToPush.push(localNote)
        } else {
          conflicts.push({
            noteId: localNote.id,
            noteTitle: localNote.title,
            localUpdatedAt: localNote.updatedAt,
            remoteUpdatedAt: remoteNote.updatedAt,
            resolution: 'pending',
          })
        }
      } else if (localNote.updatedAt < remoteNote.updatedAt) {
        // Remote is newer
        if (conflictResolution === 'remote' || conflictResolution === 'newer') {
          pulled++
        } else {
          conflicts.push({
            noteId: localNote.id,
            noteTitle: localNote.title,
            localUpdatedAt: localNote.updatedAt,
            remoteUpdatedAt: remoteNote.updatedAt,
            resolution: 'pending',
          })
        }
      } else {
        skipped++
      }
    }

    // Find notes to pull (remote only)
    const notesToPull: Note[] = []
    for (const remoteNote of remoteNotes) {
      if (!localNotesMap.has(remoteNote.id)) {
        notesToPull.push(remoteNote)
        pulled++
      }
    }

    // Push notes
    if (notesToPush.length > 0) {
      const pushResult = await pushNotes(notesToPush, config)
      pushed = pushResult.pushed
    }

    const result: SyncResult = {
      pushed,
      pulled,
      skipped,
      conflicts,
      timestamp: Date.now(),
    }

    saveSyncHistory(result)

    return result
  } catch (error) {
    console.error('Sync error:', error)
    throw error
  }
}

export async function deleteNoteFromGitHub(
  noteId: string,
  config: GitHubConfig
): Promise<boolean> {
  try {
    const path = `notes/${noteId}.json`

    // Get file SHA
    const existingResponse = await githubRequest(
      `/repos/${config.owner}/${config.repo}/contents/${path}?ref=${config.branch}`,
      config
    )

    if (!existingResponse.ok) {
      return false
    }

    const existing = await existingResponse.json()

    // Delete file
    const response = await githubRequest(
      `/repos/${config.owner}/${config.repo}/contents/${path}`,
      config,
      {
        method: 'DELETE',
        body: JSON.stringify({
          message: `Delete note: ${noteId}`,
          sha: existing.sha,
          branch: config.branch,
        }),
      }
    )

    return response.ok
  } catch (error) {
    console.error('Error deleting note from GitHub:', error)
    return false
  }
}

// Auto-sync handler
let autoSyncInterval: NodeJS.Timeout | null = null

export function startAutoSync(
  getNotes: () => Promise<Note[]>,
  onSyncComplete: (result: SyncResult) => void,
  intervalMs: number = 5 * 60 * 1000 // 5 minutes
): void {
  stopAutoSync()

  autoSyncInterval = setInterval(async () => {
    const config = getGithubConfig()
    if (!config || !config.autoSync) {
      stopAutoSync()
      return
    }

    try {
      const notes = await getNotes()
      const result = await syncNotes(notes, config)
      onSyncComplete(result)
    } catch (error) {
      console.error('Auto-sync failed:', error)
    }
  }, intervalMs)
}

export function stopAutoSync(): void {
  if (autoSyncInterval) {
    clearInterval(autoSyncInterval)
    autoSyncInterval = null
  }
}
