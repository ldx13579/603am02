import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getReport, getFileExtensionStats, getKeywordStats, getCommitFrequency, downloadPdfReport } from '../api/analysis';
import { getViolations } from '../api/violations';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import CommitHeatmap from '../components/charts/CommitHeatmap';
import DailyBarChart from '../components/charts/DailyBarChart';
import WeeklyLineChart from '../components/charts/WeeklyLineChart';
import CodeChurnChart from '../components/charts/CodeChurnChart';
import CommitFrequencyChart from '../components/charts/CommitFrequencyChart';
import type { Granularity } from '../components/charts/CommitFrequencyChart';
import FileModPieChart from '../components/charts/FileModPieChart';
import KeywordRadarChart from '../components/charts/KeywordRadarChart';
import type { AnalysisReport, CommitFrequency, FileModStat, KeywordStat, ViolationSummary } from '../types';

function dataFingerprint(report: AnalysisReport | null, fileStats: FileModStat[]): string {
  if (!report) return '';
  return `${report.total_commits}:${report.daily_stats.length}:${fileStats.length}`;
}

export default function ReportDetail() {
  const { repoId } = useParams<{ repoId: string }>();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [fileStats, setFileStats] = useState<FileModStat[]>([]);
  const [keywords, setKeywords] = useState<KeywordStat[]>([]);
  const [frequency, setFrequency] = useState<CommitFrequency[]>([]);
  const [granularity, setGranularity] = useState<Granularity>('weekly');
  const [violations, setViolations] = useState<ViolationSummary | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadAll = useCallback(() => {
    if (!repoId) return;
    const id = parseInt(repoId);
    loadReport(id);
    loadExtras(id);
    loadFrequency(id, granularity);
  }, [repoId, granularity]);

  const { notifyDataUpdate, intervalMs } = useAutoRefresh(loadAll, {
    defaultIntervalMs: 30000,
    activeIntervalMs: 5000,
    cooldownCount: 3,
    enabled: !!report,
  });

  useEffect(() => {
    loadAll();
  }, [repoId]);

  useEffect(() => {
    if (!repoId) return;
    loadFrequency(parseInt(repoId), granularity);
  }, [repoId, granularity]);

  useEffect(() => {
    notifyDataUpdate(dataFingerprint(report, fileStats));
  }, [report, fileStats, notifyDataUpdate]);

  const loadReport = async (id: number) => {
    try {
      const data = await getReport(id);
      setReport(data);
      setLastUpdated(new Date());
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load report';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const loadExtras = async (id: number) => {
    const [files, kw] = await Promise.all([
      getFileExtensionStats(id).catch(() => []),
      getKeywordStats(id).catch(() => []),
    ]);
    setFileStats(files);
    setKeywords(kw);
    getViolations(id).then(setViolations).catch(() => {});
  };

  const loadFrequency = async (id: number, g: Granularity) => {
    const data = await getCommitFrequency(id, g).catch(() => []);
    setFrequency(data);
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
          {lastUpdated && (
            <span style={{ fontSize: 12, opacity: 0.6 }}>
              Updated: {lastUpdated.toLocaleTimeString()}
              {intervalMs < 30000 && ' (watching)'}
            </span>
          )}
          <button
            onClick={async () => {
              if (!repoId) return;
              setPdfLoading(true);
              try {
                await downloadPdfReport(parseInt(repoId));
              } catch {
                alert('Failed to download PDF');
              } finally {
                setPdfLoading(false);
              }
            }}
            disabled={pdfLoading}
            style={{
              padding: '6px 16px',
              borderRadius: 6,
              border: '1px solid #4A90D9',
              background: pdfLoading ? '#ccc' : '#4A90D9',
              color: '#fff',
              cursor: pdfLoading ? 'not-allowed' : 'pointer',
              fontSize: 13,
            }}
          >
            {pdfLoading ? 'Exporting...' : 'Export PDF'}
          </button>
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

      <div className="chart-section">
        <h2>Commit Frequency</h2>
        <CommitFrequencyChart
          data={frequency}
          granularity={granularity}
          onGranularityChange={setGranularity}
        />
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

      <div className="chart-row">
        <div className="chart-section half">
          <h2>File Type Distribution</h2>
          {fileStats.length > 0 ? (
            <FileModPieChart data={fileStats} />
          ) : (
            <p style={{ color: '#999', textAlign: 'center', padding: 40 }}>No file stats data</p>
          )}
        </div>
        <div className="chart-section half">
          <h2>Keyword Analysis</h2>
          <KeywordRadarChart data={keywords} />
        </div>
      </div>

      <div className="chart-section">
        <h2>Code Churn</h2>
        <CodeChurnChart data={report.daily_stats} />
      </div>

      {violations && violations.total > 0 && (
        <div className="chart-section">
          <h2>Commit Violations ({violations.total})</h2>
          <div style={{ marginBottom: 12 }}>
            {Object.entries(violations.by_rule).map(([rule, count]) => (
              <span
                key={rule}
                style={{
                  display: 'inline-block',
                  padding: '4px 10px',
                  margin: '0 6px 6px 0',
                  borderRadius: 12,
                  background: '#FEF0EF',
                  color: '#E74C3C',
                  fontSize: 12,
                }}
              >
                {rule}: {count}
              </span>
            ))}
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f5f5f5' }}>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Hash</th>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Rule</th>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Severity</th>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Description</th>
                <th style={{ padding: '8px 12px', textAlign: 'left' }}>Author</th>
              </tr>
            </thead>
            <tbody>
              {violations.violations.slice(0, 20).map((v) => (
                <tr key={v.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '6px 12px', fontFamily: 'monospace' }}>{v.commit_hash}</td>
                  <td style={{ padding: '6px 12px' }}>{v.rule_name}</td>
                  <td style={{ padding: '6px 12px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: 8,
                      fontSize: 11,
                      background: v.severity === 'error' ? '#E74C3C' : '#F39C12',
                      color: '#fff',
                    }}>
                      {v.severity}
                    </span>
                  </td>
                  <td style={{ padding: '6px 12px' }}>{v.description}</td>
                  <td style={{ padding: '6px 12px' }}>{v.author}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
