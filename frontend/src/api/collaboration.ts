import client from './client';
import type { CollaborationGraph } from '../types';

export async function getCollaborationGraph(repoId: number, maxNodes?: number): Promise<CollaborationGraph> {
  const params: Record<string, string> = {};
  if (maxNodes) params.max_nodes = String(maxNodes);
  const { data } = await client.get(`/collaboration/${repoId}/graph`, { params });
  return data;
}
