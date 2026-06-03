import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAggregateStats, triggerAnalysis } from '../api/analysis';
import { listRepos } from '../api/repos';
import { usePolling } from '../hooks/usePolling';
import CommitHeatmap from '../components/charts/CommitHeatmap';
import DailyBarChart from '../components/charts/DailyBarChart';
import WeeklyLineChart from '../components/charts/WeeklyLineChart';
import type { DailyStat, Repo } from '../types';

export default function Dashboard() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStat[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const taskStatus = usePolling(taskId);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (taskStatus?.status === 'SUCCESS') {
      setTaskId(null);
      loadData();
    }
  }, [taskStatus]);

  const loadData = async () => {
    try {
      const [repoList, stats] = await Promise.all([listRepos(), getAggregateStats()]);
      setRepos(repoList);
      setDailyStats(stats);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    try {
      const { task_id } = await triggerAnalysis();
      setTaskId(task_id);
    } catch (err) {
      console.error('Failed to trigger analysis:', err);
    }
  };

  const totalCommits = dailyStats.reduce((sum, d) => sum + d.commit_count, 0);

  const weeklyFromDaily = () => {
    const weeks: Record<string, number> = {};
    for (const d of dailyStats) {
      const dt = new Date(d.date);
      const year = dt.getFullYear();
      const week = Math.ceil(((dt.getTime() - new Date(year, 0, 1).getTime()) / 86400000 + 1) / 7);
      const key = `${year}-W${String(week).padStart(2, '0')}`;
      weeks[key] = (weeks[key] || 0) + d.commit_count;
    }
    return Object.entries(weeks)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([week, commit_count]) => ({
        week,
        commit_count,
        insertions: 0,
        deletions: 0,
        files_changed: 0,
      }));
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <button
          className="btn btn-primary"
          onClick={handleRunAnalysis}
          disabled={!!taskId}
        >
          {taskId ? `Analyzing... ${taskStatus?.progress ?? 0}%` : 'Run Analysis'}
        </button>
      </div>

      <div className="stats-cards">
        <div className="card">
          <h3>{repos.length}</h3>
          <p>Repositories</p>
        </div>
        <div className="card">
          <h3>{totalCommits}</h3>
          <p>Total Commits</p>
        </div>
        <div className="card">
          <h3>{dailyStats.length}</h3>
          <p>Active Days</p>
        </div>
      </div>

      {dailyStats.length > 0 && (
        <>
          <div className="chart-section">
            <h2>Commit Heatmap</h2>
            <CommitHeatmap data={dailyStats} />
          </div>

          <div className="chart-row">
            <div className="chart-section half">
              <h2>Daily Commits (Last 30 Days)</h2>
              <DailyBarChart data={dailyStats} />
            </div>
            <div className="chart-section half">
              <h2>Weekly Trend</h2>
              <WeeklyLineChart data={weeklyFromDaily()} />
            </div>
          </div>
        </>
      )}

      <div className="repo-list">
        <h2>Repositories</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Branch</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {repos.map((repo) => (
              <tr key={repo.id}>
                <td>{repo.name}</td>
                <td>{repo.branch}</td>
                <td>{repo.is_active ? 'Active' : 'Inactive'}</td>
                <td>
                  <button
                    className="btn btn-small"
                    onClick={() => navigate(`/repos/${repo.id}`)}
                  >
                    View Report
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
