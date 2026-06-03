import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getReport } from '../api/analysis';
import CommitHeatmap from '../components/charts/CommitHeatmap';
import DailyBarChart from '../components/charts/DailyBarChart';
import WeeklyLineChart from '../components/charts/WeeklyLineChart';
import CodeChurnChart from '../components/charts/CodeChurnChart';
import type { AnalysisReport } from '../types';

export default function ReportDetail() {
  const { repoId } = useParams<{ repoId: string }>();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!repoId) return;
    loadReport(parseInt(repoId));
  }, [repoId]);

  const loadReport = async (id: number) => {
    try {
      const data = await getReport(id);
      setReport(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load report';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading report...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!report) return <div className="error">No report data available</div>;

  return (
    <div className="report-detail">
      <div className="report-header">
        <h1>{report.repo_name}</h1>
        <div className="report-meta">
          <span>Total Commits: {report.total_commits}</span>
          <span>Date Range: {report.date_range[0]} ~ {report.date_range[1]}</span>
        </div>
      </div>

      <div className="stats-cards">
        <div className="card">
          <h3>{report.total_commits}</h3>
          <p>Total Commits</p>
        </div>
        <div className="card">
          <h3>{report.streak_current}</h3>
          <p>Current Streak (days)</p>
        </div>
        <div className="card">
          <h3>{report.streak_longest}</h3>
          <p>Longest Streak (days)</p>
        </div>
        <div className="card">
          <h3>{report.daily_stats.length}</h3>
          <p>Active Days</p>
        </div>
      </div>

      <div className="chart-section">
        <h2>Commit Heatmap</h2>
        <CommitHeatmap data={report.daily_stats} />
      </div>

      <div className="chart-row">
        <div className="chart-section half">
          <h2>Daily Commits</h2>
          <DailyBarChart data={report.daily_stats} />
        </div>
        <div className="chart-section half">
          <h2>Weekly Trend</h2>
          <WeeklyLineChart data={report.weekly_stats} />
        </div>
      </div>

      <div className="chart-section">
        <h2>Code Churn</h2>
        <CodeChurnChart data={report.daily_stats} />
      </div>
    </div>
  );
}
