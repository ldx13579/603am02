import { useEffect, useRef, useCallback } from 'react';

export function useAutoRefresh(
  refreshFn: () => void,
  options: { intervalMs?: number; enabled?: boolean } = {},
) {
  const { intervalMs = 30000, enabled = true } = options;
  const savedFn = useRef(refreshFn);

  useEffect(() => {
    savedFn.current = refreshFn;
  }, [refreshFn]);

  useEffect(() => {
    if (!enabled) return;

    const timer = setInterval(() => {
      savedFn.current();
    }, intervalMs);

    return () => clearInterval(timer);
  }, [intervalMs, enabled]);

  const refresh = useCallback(() => {
    savedFn.current();
  }, []);

  return refresh;
}
