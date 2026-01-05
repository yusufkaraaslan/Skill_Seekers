'use client'

import { useEffect, useState } from 'react'
import { registerServiceWorker } from '@/utils/registerSW'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export default function PWAProvider({ children }: { children: React.ReactNode }) {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isInstalled, setIsInstalled] = useState(false)

  useEffect(() => {
    // Register service worker
    registerServiceWorker()

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true)
    }

    // Listen for install prompt
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault()
      setInstallPrompt(e as BeforeInstallPromptEvent)
    }

    // Listen for successful install
    const handleAppInstalled = () => {
      setIsInstalled(true)
      setInstallPrompt(null)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall)
    window.addEventListener('appinstalled', handleAppInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const handleInstall = async () => {
    if (!installPrompt) return

    await installPrompt.prompt()
    const { outcome } = await installPrompt.userChoice

    if (outcome === 'accepted') {
      setInstallPrompt(null)
    }
  }

  return (
    <>
      {children}

      {/* Install Banner */}
      {installPrompt && !isInstalled && (
        <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 z-50">
          <div className="flex items-center gap-3">
            <span className="text-3xl">📱</span>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-white">
                安裝 TipTag
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                安裝到主畫面，享受離線使用
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setInstallPrompt(null)}
                className="px-3 py-1 text-sm text-gray-500 hover:text-gray-700"
              >
                稍後
              </button>
              <button
                onClick={handleInstall}
                className="px-3 py-1 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                安裝
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
