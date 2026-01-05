export async function registerServiceWorker() {
  if (typeof window === 'undefined') return

  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      })

      // Check for updates periodically
      setInterval(() => {
        registration.update()
      }, 60 * 60 * 1000) // Every hour

      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New version available
              console.log('New version available! Refresh to update.')
            }
          })
        }
      })

      console.log('Service Worker registered successfully')
      return registration
    } catch (error) {
      console.error('Service Worker registration failed:', error)
    }
  }
}

export async function unregisterServiceWorker() {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.ready
    await registration.unregister()
  }
}
