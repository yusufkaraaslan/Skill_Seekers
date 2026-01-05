'use client'

import { useState, useEffect } from 'react'
import { getAIConfig, setAIConfig } from '@/utils/aiService'

interface AISettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

type Provider = 'local' | 'openai' | 'anthropic' | 'gemini'

const providerModels: Record<Provider, string[]> = {
  local: [],
  openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'claude-3-opus-20240229'],
  gemini: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro'],
}

export default function AISettingsModal({ isOpen, onClose }: AISettingsModalProps) {
  const [provider, setProvider] = useState<Provider>('local')
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (isOpen) {
      const config = getAIConfig()
      setProvider(config.provider as Provider)
      setApiKey(config.apiKey || '')
      setModel(config.model || '')
    }
  }, [isOpen])

  const handleSave = () => {
    setAIConfig({
      provider,
      apiKey: apiKey || undefined,
      model: model || undefined,
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🤖</span>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">AI 設定</h2>
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
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              AI 提供者
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(['local', 'openai', 'anthropic', 'gemini'] as Provider[]).map((p) => (
                <button
                  key={p}
                  onClick={() => {
                    setProvider(p)
                    setModel(providerModels[p][0] || '')
                  }}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    provider === p
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {p === 'local' && '🖥️ 本地'}
                  {p === 'openai' && '🟢 OpenAI'}
                  {p === 'anthropic' && '🟣 Anthropic'}
                  {p === 'gemini' && '🔵 Gemini'}
                </button>
              ))}
            </div>
          </div>

          {provider !== 'local' && (
            <>
              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={
                    provider === 'openai'
                      ? 'sk-...'
                      : provider === 'anthropic'
                      ? 'sk-ant-...'
                      : 'API key'
                  }
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  模型
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
                >
                  {providerModels[provider].map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          {provider === 'local' && (
            <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-600 dark:text-gray-400">
              <p className="font-medium mb-2">🖥️ 本地模式</p>
              <p>
                使用基本的本地轉換功能。如需完整 AI
                功能，請選擇其他提供者並輸入 API Key。
              </p>
            </div>
          )}

          {/* Save Button */}
          <button
            onClick={handleSave}
            className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            {saved ? '✅ 已儲存' : '儲存設定'}
          </button>
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 text-center text-xs text-gray-500 dark:text-gray-400">
          API Key 僅儲存在本地瀏覽器中
        </div>
      </div>
    </div>
  )
}
