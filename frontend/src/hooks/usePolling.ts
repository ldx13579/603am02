import { useState, useEffect } from 'react';
import { getTaskStatus } from '../api/analysis';
import type { TaskStatus } from '../types';

export function usePolling(taskId: string | null, intervalMs = 2000) {
  const [status, setStatus] = useState<TaskStatus | null>(null);

  useEffect(() => {
    if (!taskId) {
      setStatus(null);
      return;
    }

    let timer: ReturnType<typeof setInterval>;

    const poll = async () => {
      try {
        const res = await getTaskStatus(taskId);
        setStatus(res);
        if (res.status === 'SUCCESS' || res.status === 'FAILURE') {
          clearInterval(timer);
        }
      } catch {
        clearInterval(timer);
      }
    };

    poll();
    timer = setInterval(poll, intervalMs);

    return () => clearInterval(timer);
  }, [taskId, intervalMs]);

  return status;
}
