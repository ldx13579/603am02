import client from './client';
import type { Repo, RepoCreate } from '../types';

export async function listRepos(): Promise<Repo[]> {
  const { data } = await client.get('/repos');
  return data;
}

export async function createRepo(repo: RepoCreate): Promise<Repo> {
  const { data } = await client.post('/repos', repo);
  return data;
}

export async function deleteRepo(id: number): Promise<void> {
  await client.delete(`/repos/${id}`);
}

export async function updateRepo(id: number, updates: Partial<RepoCreate>): Promise<Repo> {
  const { data } = await client.put(`/repos/${id}`, updates);
  return data;
}

export async function validateRepo(id: number): Promise<{ valid: boolean; error: string | null }> {
  const { data } = await client.post(`/repos/${id}/validate`);
  return data;
}

export async function importYaml(configPath?: string): Promise<{ imported: number }> {
  const { data } = await client.post('/repos/import-yaml', { config_path: configPath });
  return data;
}
