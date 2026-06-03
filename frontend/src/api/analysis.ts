import client from './client';
import type { AnalysisReport, CommitFrequency, DailyStat, FileModStat, KeywordStat, TaskStatus } from '../types';

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

export async function getFileExtensionStats(repoId: number): Promise<FileModStat[]> {
  const { data } = await client.get(`/stats/${repoId}/file-extensions`);
  return data;
}

export async function getKeywordStats(repoId: number, topN: number = 20): Promise<KeywordStat[]> {
  const { data } = await client.get(`/stats/${repoId}/keywords`, { params: { top_n: topN } });
  return data;
}

export async function getCommitFrequency(
  repoId: number,
  granularity: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly' = 'weekly',
  since?: string,
  until?: string,
): Promise<CommitFrequency[]> {
  const params = new URLSearchParams();
  params.set('granularity', granularity);
  if (since) params.set('since', since);
  if (until) params.set('until', until);
  const { data } = await client.get(`/analysis/reports/${repoId}/frequency?${params}`);
  return data;
}
