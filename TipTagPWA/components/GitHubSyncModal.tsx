'use client'

import { useState, useEffect } from 'react'
import { Note } from '@/utils/db'
import {
  getGithubConfig,
  saveGithubConfig,
  validateConfig,
  createRepository,
  pushNotes,
  pullNotes,
  syncNotes,
  getSyncHistory,
  GitHubConfig,
  SyncResult,
} from '@/utils/githubService'

interface GitHubSyncModalProps {
  isOpen: boolean
  onClose: () => void
  notes: Note[]
  onPullComplete: (notes: Note[]) => void
  onSyncComplete?: (result: SyncResult, pulledNotes: Note[]) => void
}

type SyncStatus = 'idle' | 'loading' | 'success' | 'error'
type TabType = 'config' | 'sync' | 'history'

export default function GitHubSyncModal({
  isOpen,
  onClose,
  notes,
  onPullComplete,
  onSyncComplete,
}: GitHubSyncModalProps) {
  const [token, setToken] = useState('')
  const [owner, setOwner] = useState('')
  const [repo, setRepo] = useState('')
  const [branch, setBranch] = useState('main')
  const [autoSync, setAutoSync] = useState(false)
  const [status, setStatus] = useState<SyncStatus>('idle')
  const [message, setMessage] = useState('')
  const [isConfigured, setIsConfigured] = useState(false)
  const [lastSyncAt, setLastSyncAt] = useState<number | null>(null)
  const [syncHistory, setSyncHistory] = useState<SyncResult[]>([])
  const [activeTab, setActiveTab] = useState<TabType>('config')

  useEffect(() => {
    if (isOpen) {
      const config = getGithubConfig()
      if (config) {
        setToken(config.token)
        setOwner(config.owner)
        setRepo(config.repo)
        setBranch(config.branch)
        setAutoSync(config.autoSync)
        setLastSyncAt(config.lastSyncAt)
        setIsConfigured(true)
        setActiveTab('sync')
      }
      setSyncHistory(getSyncHistory())
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

    const config: GitHubConfig = { token, owner, repo, branch, autoSync, lastSyncAt }
    const isValid = await validateConfig(config)

    if (isValid) {
      saveGithubConfig(config)
      setIsConfigured(true)
      setStatus('success')
      setMessage('設定已儲存')
      setActiveTab('sync')
    } else {
      setStatus('error')
      setMessage('無法連接到 GitHub，請檢查設定')
    }
  }

  const handleCreateRepo = async () => {
    if (!token || !owner || !repo) {
      setStatus('error')
      setMessage('請填寫所有欄位')
      return
    }

    setStatus('loading')
    setMessage('建立儲存庫中...')

    const config: GitHubConfig = { token, owner, repo, branch, autoSync, lastSyncAt }
    const created = await createRepository(config)

    if (created) {
      const isValid = await validateConfig(config)
      if (isValid) {
        saveGithubConfig(config)
        setIsConfigured(true)
        setStatus('success')
        setMessage('儲存庫已建立並設定完成')
        setActiveTab('sync')
      }
    } else {
      setStatus('error')
      setMessage('建立儲存庫失敗')
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
      setMessage(`已上傳 ${result.pushed} 個筆記，跳過 ${result.skipped} 個${result.failed > 0 ? `，失敗 ${result.failed} 個` : ''}`)
      setLastSyncAt(Date.now())
      setSyncHistory(getSyncHistory())
    } catch {
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
      setLastSyncAt(Date.now())
      setSyncHistory(getSyncHistory())
      onPullComplete(pulledNotes)
    } catch {
      setStatus('error')
      setMessage('下載失敗，請稍後再試')
    }
  }

  const handleSync = async () => {
    const config = getGithubConfig()
    if (!config) {
      setStatus('error')
      setMessage('請先設定 GitHub')
      return
    }

    setStatus('loading')
    setMessage('同步中...')

    try {
      const result = await syncNotes(notes, config, 'newer')
      const pulledNotes = await pullNotes(config)

      setStatus('success')
      setMessage(`同步完成：上傳 ${result.pushed}，下載 ${result.pulled}，跳過 ${result.skipped}`)
      setLastSyncAt(Date.now())
      setSyncHistory(getSyncHistory())

      if (onSyncComplete) {
        onSyncComplete(result, pulledNotes)
      } else {
        onPullComplete(pulledNotes)
      }
    } catch {
      setStatus('error')
      setMessage('同步失敗，請稍後再試')
    }
  }

  const handleAutoSyncToggle = () => {
    const newAutoSync = !autoSync
    setAutoSync(newAutoSync)

    const config = getGithubConfig()
    if (config) {
      saveGithubConfig({ ...config, autoSync: newAutoSync })
    }
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
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

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('config')}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'config'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            ⚙️ 設定
          </button>
          <button
            onClick={() => setActiveTab('sync')}
            disabled={!isConfigured}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'sync'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            } ${!isConfigured ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            🔄 同步
          </button>
          <button
            onClick={() => setActiveTab('history')}
            disabled={!isConfigured}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'history'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            } ${!isConfigured ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            📜 歷史
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {/* Config Tab */}
          {activeTab === 'config' && (
            <div className="space-y-4">
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
                  需要 &apos;repo&apos; 權限。
                  <a
                    href="https://github.com/settings/tokens/new?scopes=repo&description=TipTag%20Sync"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:underline ml-1"
                  >
                    建立 Token →
                  </a>
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

              <div className="flex gap-2">
                <button
                  onClick={handleSaveConfig}
                  disabled={status === 'loading'}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
                >
                  {status === 'loading' ? '驗證中...' : '連接現有儲存庫'}
                </button>
                <button
                  onClick={handleCreateRepo}
                  disabled={status === 'loading'}
                  className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
                  title="建立新的私有儲存庫"
                >
                  + 建立
                </button>
              </div>
            </div>
          )}

          {/* Sync Tab */}
          {activeTab === 'sync' && isConfigured && (
            <div className="space-y-4">
              {/* Sync Status */}
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    同步狀態
                  </span>
                  <span className="text-xs text-gray-500">
                    {owner}/{repo}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  已連接
                  {lastSyncAt && (
                    <span className="ml-auto text-xs">
                      上次同步：{formatDate(lastSyncAt)}
                    </span>
                  )}
                </div>
              </div>

              {/* Auto Sync Toggle */}
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div>
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    自動同步
                  </div>
                  <div className="text-xs text-gray-500">
                    每 5 分鐘自動同步一次
                  </div>
                </div>
                <button
                  onClick={handleAutoSyncToggle}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    autoSync ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                >
                  <span
                    className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                      autoSync ? 'left-7' : 'left-1'
                    }`}
                  />
                </button>
              </div>

              {/* Sync Actions */}
              <div className="space-y-2">
                <button
                  onClick={handleSync}
                  disabled={status === 'loading'}
                  className="w-full px-4 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                  🔄 雙向同步
                </button>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={handlePush}
                    disabled={status === 'loading'}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
                  >
                    ⬆️ 僅上傳
                  </button>
                  <button
                    onClick={handlePull}
                    disabled={status === 'loading'}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg font-medium hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
                  >
                    ⬇️ 僅下載
                  </button>
                </div>
              </div>

              {/* Note Count */}
              <div className="text-center text-sm text-gray-500 dark:text-gray-400">
                本地筆記：{notes.length} 個
              </div>
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && isConfigured && (
            <div className="space-y-3">
              {syncHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <p className="text-3xl mb-2">📜</p>
                  <p>尚無同步記錄</p>
                </div>
              ) : (
                syncHistory.map((record, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">
                        {formatDate(record.timestamp)}
                      </span>
                      {record.conflicts.length > 0 && (
                        <span className="text-xs text-yellow-600 dark:text-yellow-400">
                          ⚠️ {record.conflicts.length} 個衝突
                        </span>
                      )}
                    </div>
                    <div className="flex gap-4 text-sm">
                      <span className="text-green-600 dark:text-green-400">
                        ⬆️ {record.pushed}
                      </span>
                      <span className="text-blue-600 dark:text-blue-400">
                        ⬇️ {record.pulled}
                      </span>
                      <span className="text-gray-500">
                        ⏭️ {record.skipped}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Status Message */}
          {message && (
            <div
              className={`mt-4 p-3 rounded-lg text-sm ${
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
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 pt-2 text-center text-xs text-gray-500 dark:text-gray-400">
          筆記將儲存在 {owner || 'username'}/{repo || 'repo'}/notes/ 目錄
        </div>
      </div>
    </div>
  )
}
