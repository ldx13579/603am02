import ReactECharts from 'echarts-for-react';
import type { CommitFrequency } from '../../types';

export type Granularity = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';

interface Props {
  data: CommitFrequency[];
  granularity: Granularity;
  onGranularityChange: (g: Granularity) => void;
}

const GRANULARITY_OPTIONS: { value: Granularity; label: string }[] = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
];

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
      <div style={{ marginBottom: 12, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {GRANULARITY_OPTIONS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => onGranularityChange(value)}
            style={{
              padding: '4px 12px',
              borderRadius: 4,
              border: '1px solid #ddd',
              background: value === granularity ? '#4078c0' : '#fff',
              color: value === granularity ? '#fff' : '#333',
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            {label}
          </button>
        ))}
      </div>
      <ReactECharts option={option} style={{ height: '300px', width: '100%' }} />
    </div>
  );
}
