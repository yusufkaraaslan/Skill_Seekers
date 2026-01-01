import { Note } from './db'

interface GitHubConfig {
  token: string
  owner: string
  repo: string
  branch: string
}

const CONFIG_KEY = 'tiptag_github_config'

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
    return JSON.parse(stored)
  } catch {
    return null
  }
}

export function clearGithubConfig(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(CONFIG_KEY)
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

export async function pushNotes(
  notes: Note[],
  config: GitHubConfig
): Promise<{ pushed: number; skipped: number }> {
  let pushed = 0
  let skipped = 0

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
        const existingContent = atob(existing.content.replace(/\n/g, ''))
        if (existingContent === content) {
          skipped++
          continue
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
        skipped++
      }
    } catch (error) {
      console.error('Error pushing note:', note.id, error)
      skipped++
    }
  }

  return { pushed, skipped }
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

  return notes.sort((a, b) => b.updatedAt - a.updatedAt)
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
