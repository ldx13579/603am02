import client from './client';
import type { AnalysisReport, DailyStat, TaskStatus } from '../types';

export async function triggerAnalysis(repoIds?: number[], since?: string, until?: string) {
  const { data } = await client.post('/analysis/trigger', {
    repo_ids: repoIds,
    since,
    until,
  });
  return data as { task_id: string; status: string };
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const { data } = await client.get(`/tasks/${taskId}`);
  return data;
}

export async function getReport(repoId: number): Promise<AnalysisReport> {
  const { data } = await client.get(`/analysis/reports/${repoId}`);
  return data;
}

export async function getDailyStats(repoId: number, since?: string, until?: string): Promise<DailyStat[]> {
  const params = new URLSearchParams();
  if (since) params.set('since', since);
  if (until) params.set('until', until);
  const { data } = await client.get(`/analysis/reports/${repoId}/daily?${params}`);
  return data;
}

export async function getAggregateStats(since?: string, until?: string): Promise<DailyStat[]> {
  const params = new URLSearchParams();
  if (since) params.set('since', since);
  if (until) params.set('until', until);
  const { data } = await client.get(`/analysis/reports/aggregate?${params}`);
  return data;
}
