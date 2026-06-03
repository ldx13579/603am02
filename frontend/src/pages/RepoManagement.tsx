import { useState, useEffect } from 'react';
import { listRepos, createRepo, deleteRepo } from '../api/repos';
import type { Repo, RepoCreate } from '../types';

export default function RepoManagement() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [sourceType, setSourceType] = useState<'local' | 'remote'>('local');
  const [form, setForm] = useState<RepoCreate>({ name: '', local_path: '', branch: 'main' });

  useEffect(() => {
    loadRepos();
  }, []);

  const loadRepos = async () => {
    try {
      const data = await listRepos();
      setRepos(data);
    } catch (err) {
      console.error('Failed to load repos:', err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: RepoCreate = { name: form.name, branch: form.branch };
      if (sourceType === 'local') {
        payload.local_path = form.local_path;
      } else {
        payload.git_url = form.git_url;
      }
      await createRepo(payload);
      setForm({ name: '', local_path: '', branch: 'main' });
      setShowForm(false);
      loadRepos();
    } catch (err) {
      console.error('Failed to create repo:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this repository?')) return;
    try {
      await deleteRepo(id);
      loadRepos();
    } catch (err) {
      console.error('Failed to delete repo:', err);
    }
  };

  const getCloneStatusBadge = (repo: Repo) => {
    if (repo.source_type !== 'remote') return null;
    const statusColors: Record<string, string> = {
      pending: '#f59e0b',
      cloning: '#3b82f6',
      ready: '#10b981',
      failed: '#ef4444',
    };
    const color = statusColors[repo.clone_status || ''] || '#6b7280';
    return (
      <span style={{ color, fontWeight: 500, fontSize: 12 }}>
        {repo.clone_status || 'unknown'}
      </span>
    );
  };

  return (
    <div className="repo-management">
      <div className="page-header">
        <h1>Repository Management</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : 'Add Repository'}
        </button>
      </div>

      {showForm && (
        <form className="repo-form" onSubmit={handleCreate}>
          <div className="form-group">
            <label>Source Type</label>
            <div style={{ display: 'flex', gap: 12 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                <input
                  type="radio"
                  checked={sourceType === 'local'}
                  onChange={() => setSourceType('local')}
                />
                Local Path
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                <input
                  type="radio"
                  checked={sourceType === 'remote'}
                  onChange={() => setSourceType('remote')}
                />
                Git URL
              </label>
            </div>
          </div>
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="my-project"
              required
            />
          </div>
          {sourceType === 'local' ? (
            <div className="form-group">
              <label>Local Path</label>
              <input
                type="text"
                value={form.local_path || ''}
                onChange={(e) => setForm({ ...form, local_path: e.target.value })}
                placeholder="/path/to/repo"
                required
              />
            </div>
          ) : (
            <div className="form-group">
              <label>Git URL</label>
              <input
                type="text"
                value={form.git_url || ''}
                onChange={(e) => setForm({ ...form, git_url: e.target.value })}
                placeholder="https://github.com/user/repo.git"
                required
              />
            </div>
          )}
          <div className="form-group">
            <label>Branch</label>
            <input
              type="text"
              value={form.branch}
              onChange={(e) => setForm({ ...form, branch: e.target.value })}
              placeholder="main"
            />
          </div>
          <button type="submit" className="btn btn-primary">Add</button>
        </form>
      )}

      <table className="repo-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Source</th>
            <th>Branch</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {repos.map((repo) => (
            <tr key={repo.id}>
              <td>{repo.name}</td>
              <td className="path-cell">
                {repo.source_type === 'remote' ? (
                  <span title={repo.git_url || ''}>{repo.git_url || ''}</span>
                ) : (
                  <span>{repo.local_path}</span>
                )}
              </td>
              <td>{repo.branch}</td>
              <td>
                <span className={`badge ${repo.is_active ? 'badge-active' : 'badge-inactive'}`}>
                  {repo.is_active ? 'Active' : 'Inactive'}
                </span>
                {getCloneStatusBadge(repo) && (
                  <span style={{ marginLeft: 8 }}>{getCloneStatusBadge(repo)}</span>
                )}
              </td>
              <td>{new Date(repo.created_at).toLocaleDateString()}</td>
              <td>
                <button className="btn btn-danger btn-small" onClick={() => handleDelete(repo.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {repos.length === 0 && (
        <p className="empty-state">No repositories configured. Add one to get started.</p>
      )}
    </div>
  );
}
