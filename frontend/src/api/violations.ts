import client from './client';
import type { ViolationSummary } from '../types';

export async function getViolations(repoId: number): Promise<ViolationSummary> {
  const { data } = await client.get(`/violations/${repoId}`);
  return data;
}
