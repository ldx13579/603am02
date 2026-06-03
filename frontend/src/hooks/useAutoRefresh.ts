import { useEffect, useRef, useCallback, useState } from 'react';

interface AdaptiveRefreshOptions {
  defaultIntervalMs?: number;
  activeIntervalMs?: number;
  cooldownCount?: number;
  enabled?: boolean;
}

export function useAutoRefresh(
  refreshFn: () => void,
  options: AdaptiveRefreshOptions = {},
) {
  const {
    defaultIntervalMs = 30000,
    activeIntervalMs = 5000,
    cooldownCount = 3,
    enabled = true,
  } = options;

  const savedFn = useRef(refreshFn);
  const lastDataHash = useRef<string>('');
  const stableCount = useRef(0);
  const [intervalMs, setIntervalMs] = useState(defaultIntervalMs);

  useEffect(() => {
    savedFn.current = refreshFn;
  }, [refreshFn]);

  const notifyDataUpdate = useCallback((dataFingerprint: string) => {
    if (lastDataHash.current && dataFingerprint !== lastDataHash.current) {
      stableCount.current = 0;
      setIntervalMs(activeIntervalMs);
    } else {
      stableCount.current += 1;
      if (stableCount.current >= cooldownCount) {
        setIntervalMs(defaultIntervalMs);
      }
    }
    lastDataHash.current = dataFingerprint;
  }, [activeIntervalMs, defaultIntervalMs, cooldownCount]);

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

  return { refresh, notifyDataUpdate, intervalMs };
}
