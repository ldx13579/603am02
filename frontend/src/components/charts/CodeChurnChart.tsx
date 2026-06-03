import ReactECharts from 'echarts-for-react';
import type { DailyStat } from '../../types';

interface Props {
  data: DailyStat[];
}

export default function CodeChurnChart({ data }: Props) {
  const recent = data.slice(-30);

  const option = {
    tooltip: {
      trigger: 'axis' as const,
    },
    legend: {
      data: ['Insertions', 'Deletions'],
      top: 0,
    },
    xAxis: {
      type: 'category' as const,
      data: recent.map((d) => d.date.slice(5)),
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Lines',
    },
    series: [
      {
        name: 'Insertions',
        type: 'line',
        stack: 'churn',
        areaStyle: { opacity: 0.6 },
        data: recent.map((d) => d.insertions),
        itemStyle: { color: '#28a745' },
      },
      {
        name: 'Deletions',
        type: 'line',
        stack: 'churn',
        areaStyle: { opacity: 0.6 },
        data: recent.map((d) => -d.deletions),
        itemStyle: { color: '#d73a49' },
      },
    ],
    grid: { left: 60, right: 20, bottom: 60, top: 40 },
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: '300px', width: '100%' }}
    />
  );
}
