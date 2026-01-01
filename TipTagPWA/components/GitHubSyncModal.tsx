'use client'

import { useState, useEffect } from 'react'
import { Note } from '@/utils/db'
import {
  getGithubConfig,
  saveGithubConfig,
  validateConfig,
  pushNotes,
  pullNotes,
} from '@/utils/githubService'

interface GitHubSyncModalProps {
  isOpen: boolean
  onClose: () => void
  notes: Note[]
  onPullComplete: (notes: Note[]) => void
}

type SyncStatus = 'idle' | 'loading' | 'success' | 'error'

export default function GitHubSyncModal({
  isOpen,
  onClose,
  notes,
  onPullComplete,
}: GitHubSyncModalProps) {
  const [token, setToken] = useState('')
  const [owner, setOwner] = useState('')
  const [repo, setRepo] = useState('')
  const [branch, setBranch] = useState('main')
  const [status, setStatus] = useState<SyncStatus>('idle')
  const [message, setMessage] = useState('')
  const [isConfigured, setIsConfigured] = useState(false)

  useEffect(() => {
    if (isOpen) {
      const config = getGithubConfig()
      if (config) {
        setToken(config.token)
        setOwner(config.owner)
        setRepo(config.repo)
        setBranch(config.branch)
        setIsConfigured(true)
      }
    }
  }, [isOpen])

  const handleSaveConfig = async () => {
    if (!token || !owner || !repo) {
      setStatus('error')
      setMessage('請填寫所有欄位')
      return
    }

    setStatus('loading')
    setMessage('驗證設定中...')

    const config = { token, owner, repo, branch }
    const isValid = await validateConfig(config)

    if (isValid) {
      saveGithubConfig(config)
      setIsConfigured(true)
      setStatus('success')
      setMessage('設定已儲存')
    } else {
      setStatus('error')
      setMessage('無法連接到 GitHub，請檢查設定')
    }
  }

  const handlePush = async () => {
    const config = getGithubConfig()
    if (!config) {
      setStatus('error')
      setMessage('請先設定 GitHub')
      return
    }

    setStatus('loading')
    setMessage('上傳中...')

    try {
      const result = await pushNotes(notes, config)
      setStatus('success')
      setMessage(`已上傳 ${result.pushed} 個筆記，跳過 ${result.skipped} 個`)
    } catch (error) {
      setStatus('error')
      setMessage('上傳失敗，請稍後再試')
    }
  }

  const handlePull = async () => {
    const config = getGithubConfig()
    if (!config) {
      setStatus('error')
      setMessage('請先設定 GitHub')
      return
    }

    setStatus('loading')
    setMessage('下載中...')

    try {
      const pulledNotes = await pullNotes(config)
      setStatus('success')
      setMessage(`已下載 ${pulledNotes.length} 個筆記`)
      onPullComplete(pulledNotes)
    } catch (error) {
      setStatus('error')
      setMessage('下載失敗，請稍後再試')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🔗</span>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">GitHub 同步</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
          >
            <span className="text-gray-500 text-xl">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Config Form */}
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Personal Access Token
              </label>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxx"
                className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                需要 &apos;repo&apos; 權限
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  擁有者
                </label>
                <input
                  type="text"
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                  placeholder="username"
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  儲存庫
                </label>
                <input
                  type="text"
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  placeholder="my-notes"
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                分支
              </label>
              <input
                type="text"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="main"
                className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <button
              onClick={handleSaveConfig}
              disabled={status === 'loading'}
              className="w-full px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {status === 'loading' ? '驗證中...' : '儲存設定'}
            </button>
          </div>

          {/* Status Message */}
          {message && (
            <div
              className={`p-3 rounded-lg text-sm ${
                status === 'success'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : status === 'error'
                  ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              {status === 'loading' && '⏳ '}
              {status === 'success' && '✅ '}
              {status === 'error' && '❌ '}
              {message}
            </div>
          )}

          {/* Sync Buttons */}
          {isConfigured && (
            <div className="flex gap-3 pt-2">
              <button
                onClick={handlePush}
                disabled={status === 'loading'}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                ⬆️ 上傳到 GitHub
              </button>
              <button
                onClick={handlePull}
                disabled={status === 'loading'}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
              >
                ⬇️ 從 GitHub 下載
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 pt-2 text-center text-xs text-gray-500 dark:text-gray-400">
          筆記將儲存在 {owner || 'username'}/{repo || 'repo'}/notes/ 目錄
        </div>
      </div>
    </div>
  )
}
