import { useEffect, useRef, useState } from 'react';

/**
 * Load one read-only payload for a routed page.
 *
 * Read endpoints (skill detail, config detail, workflows, environment, recent
 * analyses) bypass the store on purpose — only mutations need `act`'s shared
 * in-flight guard. `key` is the identity of what is being loaded: the fetch
 * re-runs when it changes, a late response for a previous key is dropped, and
 * a result is only handed back while it still belongs to the current key (so
 * switching skills shows the loading state, never the previous skill).
 */
export function usePayload<T>(load: () => Promise<T>, key: string) {
  // The loader closes over props and is a new function every render; keeping
  // it in a ref keeps `key` the only trigger. The ref is refreshed in its own
  // effect — effects run in declaration order, so it is current before the
  // fetch below runs.
  const loadRef = useRef(load);
  const [state, setState] = useState<{ key: string | null; data: T | null; error: string }>(
    { key: null, data: null, error: '' },
  );
  const [nonce, setNonce] = useState(0);

  useEffect(() => { loadRef.current = load; });

  useEffect(() => {
    let active = true;
    loadRef.current()
      .then((data) => { if (active) setState({ key, data, error: '' }); })
      .catch((e) => { if (active) setState({ key, data: null, error: e instanceof Error ? e.message : String(e) }); });
    return () => { active = false; };
  }, [key, nonce]);

  const fresh = state.key === key;
  return {
    data: fresh ? state.data : null,
    error: fresh ? state.error : '',
    reload: () => setNonce((n) => n + 1),
  };
}
