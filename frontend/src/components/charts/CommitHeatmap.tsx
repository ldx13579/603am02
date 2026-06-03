import ReactECharts from 'echarts-for-react';
import type { DailyStat } from '../../types';

interface Props {
  data: DailyStat[];
  year?: string;
}

export default function CommitHeatmap({ data, year }: Props) {
  const currentYear = year || new Date().getFullYear().toString();
  const rangeStart = `${currentYear}-01-01`;
  const rangeEnd = `${currentYear}-12-31`;

  const maxCommits = Math.max(...data.map((d) => d.commit_count), 1);

  const calendarData = data
    .filter((d) => d.date >= rangeStart && d.date <= rangeEnd)
    .map((d) => [d.date, d.commit_count]);

  const option = {
    tooltip: {
      formatter: (params: { value: [string, number] }) => {
        return `${params.value[0]}: ${params.value[1]} commits`;
      },
    },
    visualMap: {
      min: 0,
      max: maxCommits,
      type: 'piecewise' as const,
      pieces: [
        { min: 0, max: 0, color: '#ebedf0' },
        { min: 1, max: Math.ceil(maxCommits * 0.25), color: '#9be9a8' },
        { min: Math.ceil(maxCommits * 0.25) + 1, max: Math.ceil(maxCommits * 0.5), color: '#40c463' },
        { min: Math.ceil(maxCommits * 0.5) + 1, max: Math.ceil(maxCommits * 0.75), color: '#30a14e' },
        { min: Math.ceil(maxCommits * 0.75) + 1, max: maxCommits, color: '#216e39' },
      ],
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
    },
    calendar: {
      range: [rangeStart, rangeEnd],
      cellSize: [14, 14],
      left: 50,
      top: 30,
      yearLabel: { show: true, position: 'top' },
      dayLabel: { firstDay: 1, nameMap: 'en' },
      monthLabel: { nameMap: 'en' },
      itemStyle: {
        borderWidth: 2,
        borderColor: '#fff',
      },
    },
    series: [
      {
        type: 'heatmap',
        coordinateSystem: 'calendar',
        data: calendarData,
      },
    ],
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: '200px', width: '100%' }}
      opts={{ renderer: 'svg' }}
    />
  );
}
