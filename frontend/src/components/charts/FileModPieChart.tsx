import ReactECharts from 'echarts-for-react';
import type { FileModStat } from '../../types';

interface Props {
  data: FileModStat[];
}

export default function FileModPieChart({ data }: Props) {
  const sorted = [...data].sort((a, b) => b.modification_count - a.modification_count);
  const top = sorted.slice(0, 10);
  const other = sorted.slice(10);
  const otherTotal = other.reduce((sum, d) => sum + d.modification_count, 0);

  const pieData = top.map(d => ({ name: d.extension, value: d.modification_count }));
  if (otherTotal > 0) {
    pieData.push({ name: 'Other', value: otherTotal });
  }

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { fontSize: 11 },
    },
    series: [
      {
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['40%', '50%'],
        data: pieData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0,0,0,0.3)',
          },
        },
        label: {
          formatter: '{b}\n{d}%',
          fontSize: 11,
        },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: '350px', width: '100%' }} />;
}
