import { useState, useEffect } from 'react';
import { getCollaborationGraph } from '../api/collaboration';
import { listRepos } from '../api/repos';
import CollaborationNetwork from '../components/charts/CollaborationNetwork';
import type { CollaborationGraph, Repo } from '../types';

export default function CollaborationPage() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<number | null>(null);
  const [graph, setGraph] = useState<CollaborationGraph | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRepos().then(setRepos).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedRepo) return;
    setLoading(true);
    setError(null);
    getCollaborationGraph(selectedRepo)
      .then(setGraph)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load graph');
        setGraph(null);
      })
      .finally(() => setLoading(false));
  }, [selectedRepo]);

  return (
    <div className="collaboration-page">
      <div className="report-header">
        <h1>Developer Collaboration Network</h1>
        <div className="report-meta">
          <select
            value={selectedRepo ?? ''}
            onChange={(e) => setSelectedRepo(e.target.value ? parseInt(e.target.value) : null)}
            style={{
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid #ddd',
              fontSize: 14,
            }}
          >
            <option value="">Select a repository...</option>
            {repos.map((repo) => (
              <option key={repo.id} value={repo.id}>
                {repo.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="loading">Loading collaboration data...</div>}
      {error && <div className="error">{error}</div>}

      {graph && !loading && (
        <div className="chart-section">
          <CollaborationNetwork data={graph} />
        </div>
      )}

      {!selectedRepo && !loading && (
        <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>
          Select a repository to view the developer collaboration network
        </div>
      )}
    </div>
  );
}
