import { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import type { CommitFrequency } from '../../types';

interface Props {
  data: CommitFrequency[];
  granularity: 'daily' | 'weekly' | 'monthly';
  onGranularityChange: (g: 'daily' | 'weekly' | 'monthly') => void;
}

export default function CommitFrequencyChart({ data, granularity, onGranularityChange }: Props) {
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0];
        return `${p.axisValue}<br/>Commits: <b>${p.value}</b>`;
      },
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.period),
      axisLabel: { rotate: 45 },
    },
    yAxis: { type: 'value', name: 'Commits' },
    series: [
      {
        name: 'Commits',
        type: 'line',
        data: data.map(d => d.commit_count),
        smooth: true,
        areaStyle: { opacity: 0.15 },
        itemStyle: { color: '#4078c0' },
        lineStyle: { width: 2 },
      },
    ],
    grid: { left: 60, right: 20, bottom: 70, top: 40 },
  };

  return (
    <div>
      <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
        {(['daily', 'weekly', 'monthly'] as const).map(g => (
          <button
            key={g}
            className={`btn btn-small ${g === granularity ? 'active' : ''}`}
            onClick={() => onGranularityChange(g)}
            style={{
              padding: '4px 12px',
              borderRadius: 4,
              border: '1px solid #ddd',
              background: g === granularity ? '#4078c0' : '#fff',
              color: g === granularity ? '#fff' : '#333',
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            {g.charAt(0).toUpperCase() + g.slice(1)}
          </button>
        ))}
      </div>
      <ReactECharts option={option} style={{ height: '300px', width: '100%' }} />
    </div>
  );
}
