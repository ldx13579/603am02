import { useState, useEffect } from 'react';
import { listRepos, createRepo, deleteRepo } from '../api/repos';
import type { Repo, RepoCreate } from '../types';

export default function RepoManagement() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [showForm, setShowForm] = useState(false);
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
      await createRepo(form);
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
            <label>Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="my-project"
              required
            />
          </div>
          <div className="form-group">
            <label>Local Path</label>
            <input
              type="text"
              value={form.local_path}
              onChange={(e) => setForm({ ...form, local_path: e.target.value })}
              placeholder="/path/to/repo"
              required
            />
          </div>
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
            <th>Path</th>
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
              <td className="path-cell">{repo.local_path}</td>
              <td>{repo.branch}</td>
              <td>
                <span className={`badge ${repo.is_active ? 'badge-active' : 'badge-inactive'}`}>
                  {repo.is_active ? 'Active' : 'Inactive'}
                </span>
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
