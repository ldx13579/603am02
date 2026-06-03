import ReactECharts from 'echarts-for-react';
import type { DailyStat } from '../../types';

interface Props {
  data: DailyStat[];
}

export default function DailyBarChart({ data }: Props) {
  const recent = data.slice(-30);

  const option = {
    tooltip: {
      trigger: 'axis' as const,
    },
    xAxis: {
      type: 'category' as const,
      data: recent.map((d) => d.date.slice(5)),
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Commits',
    },
    series: [
      {
        name: 'Commits',
        type: 'bar',
        data: recent.map((d) => d.commit_count),
        itemStyle: { color: '#40c463' },
      },
    ],
    grid: { left: 60, right: 20, bottom: 60, top: 30 },
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: '300px', width: '100%' }}
    />
  );
}
