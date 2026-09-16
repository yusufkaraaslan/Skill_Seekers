import { useState } from 'react';
import { PAGE_SIZES } from '@/lib/data';

// ── Paging ───────────────────────────────────────────────────────────────────
const DEFAULT_PAGE_SIZE = 25;

function readPageSize(listKey: string): number {
  try {
    const v = Number(localStorage.getItem(`seeker.pageSize.${listKey}`));
    return (PAGE_SIZES as readonly number[]).includes(v) ? v : DEFAULT_PAGE_SIZE;
  } catch {
    return DEFAULT_PAGE_SIZE;
  }
}

export function usePagination<T>(items: T[], listKey: string, resetKey: string) {
  const [pageSize, setPageSizeState] = useState<number>(() => readPageSize(listKey));
  // page is remembered together with the filter key + size it was chosen for;
  // any change to either means "start over at page 1" without an effect
  const [pageState, setPageState] = useState({ page: 1, key: resetKey, size: pageSize });
  const page = pageState.key === resetKey && pageState.size === pageSize ? pageState.page : 1;

  const total = items.length;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const current = Math.min(page, pageCount);
  const slice = items.slice((current - 1) * pageSize, current * pageSize);

  const setPage = (p: number) => setPageState({ page: p, key: resetKey, size: pageSize });
  const setPageSize = (n: number) => {
    setPageSizeState(n);
    try {
      localStorage.setItem(`seeker.pageSize.${listKey}`, String(n));
    } catch {
      /* storage unavailable — size still applies for this session */
    }
  };

  return { slice, page: current, pageCount, pageSize, total, setPage, setPageSize };
}
