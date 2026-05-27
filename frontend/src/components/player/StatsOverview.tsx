import ReactECharts from "echarts-for-react";
import type { PlayerStats } from "@/types/player";

interface StatsOverviewProps {
  stats: PlayerStats;
}

function gaugeOption(value: number, label: string, color: string) {
  return {
    series: [
      {
        type: "gauge",
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        splitNumber: 5,
        pointer: { show: false },
        progress: {
          show: true,
          width: 12,
          itemStyle: { color },
        },
        axisLine: {
          lineStyle: { width: 12, color: [[1, "#1c2640"]] },
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          valueAnimation: true,
          fontSize: 22,
          fontWeight: "bold",
          color: "#fff",
          offsetCenter: [0, "10%"],
          formatter: `{value}%`,
        },
        title: {
          offsetCenter: [0, "40%"],
          fontSize: 12,
          color: "#9ca3af",
        },
        data: [{ value: Math.round(value * 100) / 100, name: label }],
      },
    ],
  };
}

function placementBarOption(avgPlacement: number) {
  const placements = [1, 2, 3, 4, 5, 6, 7, 8];
  const center = avgPlacement;
  const values = placements.map((p) => {
    const dist = Math.abs(p - center);
    return Math.max(0, Math.round((1 - dist / 4) * 100));
  });
  return {
    grid: { top: 10, right: 10, bottom: 24, left: 30 },
    xAxis: {
      type: "category",
      data: placements.map(String),
      axisLabel: { color: "#9ca3af", fontSize: 10 },
      axisLine: { lineStyle: { color: "#1c2640" } },
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        type: "bar",
        data: values.map((v, i) => ({
          value: v,
          itemStyle: {
            color: placements[i] <= 4 ? "#0ac8b9" : "#c8aa6e",
          },
        })),
        barWidth: "60%",
        label: { show: false },
      },
    ],
  };
}

export default function StatsOverview({ stats }: StatsOverviewProps) {
  const cards = [
    {
      title: "Total Games",
      value: stats.total_games.toString(),
      chart: null,
    },
    {
      title: "Top 4 Rate",
      value: null,
      chart: gaugeOption(stats.top4_rate * 100, "Top 4", "#0ac8b9"),
    },
    {
      title: "Win Rate",
      value: null,
      chart: gaugeOption(stats.win_rate * 100, "Win", "#c8aa6e"),
    },
    {
      title: "Avg Placement",
      value: null,
      chart: placementBarOption(stats.avg_placement),
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-dark-700 border border-dark-600 rounded-xl p-4 flex flex-col items-center"
        >
          <h3 className="text-xs text-gray-400 uppercase tracking-wide mb-2">
            {card.title}
          </h3>
          {card.value !== null ? (
            <span className="text-3xl font-bold text-white">{card.value}</span>
          ) : card.chart ? (
            <ReactECharts
              option={card.chart}
              style={{ height: 120, width: "100%" }}
              opts={{ renderer: "svg" }}
            />
          ) : null}
        </div>
      ))}
    </div>
  );
}
