import ReactECharts from 'echarts-for-react';
import type { KeywordStat } from '../../types';

interface Props {
  data: KeywordStat[];
}

export default function KeywordRadarChart({ data }: Props) {
  const top = data.slice(0, 8);

  if (top.length === 0) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>No keyword data available</div>;
  }

  const maxScore = Math.max(...top.map(d => d.score), 0.01);

  const option = {
    tooltip: {
      trigger: 'item',
    },
    radar: {
      indicator: top.map(d => ({
        name: d.keyword,
        max: maxScore * 1.2,
      })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#333',
        fontSize: 11,
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: top.map(d => d.score),
            name: 'TF-IDF Score',
            areaStyle: { opacity: 0.25, color: '#6366f1' },
            lineStyle: { color: '#6366f1', width: 2 },
            itemStyle: { color: '#6366f1' },
          },
        ],
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: '350px', width: '100%' }} />;
}
