import ReactECharts from 'echarts-for-react';
import type { WeeklyStat } from '../../types';

interface Props {
  data: WeeklyStat[];
}

export default function WeeklyLineChart({ data }: Props) {
  const option = {
    tooltip: {
      trigger: 'axis' as const,
    },
    xAxis: {
      type: 'category' as const,
      data: data.map((d) => d.week),
      axisLabel: { rotate: 45 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Commits',
    },
    series: [
      {
        name: 'Weekly Commits',
        type: 'line',
        data: data.map((d) => d.commit_count),
        smooth: true,
        areaStyle: { opacity: 0.3 },
        itemStyle: { color: '#4078c0' },
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
