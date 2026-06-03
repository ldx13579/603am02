import client from './client';
import type { CollaborationGraph } from '../types';

export async function getCollaborationGraph(repoId: number): Promise<CollaborationGraph> {
  const { data } = await client.get(`/collaboration/${repoId}/graph`);
  return data;
}
