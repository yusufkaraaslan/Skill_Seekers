import { useEffect, useState } from 'react';

/** Preserve non-secret form drafts across navigation and refresh in this tab. */
export function useDraft<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = sessionStorage.getItem(key);
      return raw === null ? initial : JSON.parse(raw) as T;
    } catch { return initial; }
  });
  useEffect(() => {
    try { sessionStorage.setItem(key, JSON.stringify(value)); } catch { /* storage unavailable */ }
  }, [key, value]);
  return [value, setValue] as const;
}
