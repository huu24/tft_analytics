import ReactECharts from "echarts-for-react";
import type { ChampionDetail } from "@/types/champion";

interface ChampionStatsOverviewProps {
  champion: ChampionDetail;
}

export default function ChampionStatsOverview({ champion }: ChampionStatsOverviewProps) {
  const gaugeOption = {
    series: [
      {
        type: "gauge",
        startAngle: 220,
        endAngle: -40,
        min: 0,
        max: 100,
        pointer: { show: false },
        progress: {
          show: true,
          width: 14,
          itemStyle: { color: "#0ac8b9" },
        },
        axisLine: {
          lineStyle: { width: 14, color: [[1, "#1c2640"]] },
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          valueAnimation: true,
          fontSize: 28,
          fontWeight: "bold",
          color: "#0ac8b9",
          offsetCenter: [0, "10%"],
          formatter: "{value}%",
        },
        title: {
          offsetCenter: [0, "40%"],
          fontSize: 12,
          color: "#9ca3af",
        },
        data: [{ value: +(champion.win_rate * 100).toFixed(1), name: "Win Rate" }],
      },
    ],
  };

  const barData = [
    { label: "Top 4 Rate", value: +(champion.top4_rate * 100).toFixed(1), color: "#c8aa6e" },
    { label: "Pick Rate", value: +(champion.pick_rate * 100).toFixed(1), color: "#0ac8b9" },
  ];

  const barOption = {
    grid: { left: 90, right: 40, top: 10, bottom: 10 },
    xAxis: {
      type: "value" as const,
      max: 100,
      axisLabel: { show: false },
      splitLine: { show: false },
      axisLine: { show: false },
    },
    yAxis: {
      type: "category" as const,
      data: barData.map((d) => d.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#9ca3af", fontSize: 11 },
    },
    series: [
      {
        type: "bar",
        data: barData.map((d) => ({
          value: d.value,
          itemStyle: { color: d.color, borderRadius: [0, 4, 4, 0] },
        })),
        barWidth: 20,
        label: {
          show: true,
          position: "right" as const,
          formatter: "{c}%",
          color: "#fff",
          fontSize: 12,
        },
        backgroundStyle: { color: "#1c2640", borderRadius: [0, 4, 4, 0] },
        showBackground: true,
      },
    ],
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 flex flex-col items-center">
        <h3 className="text-sm text-gray-400 mb-2">
          {champion.display_name || champion.champion_id}
        </h3>
        <ReactECharts option={gaugeOption} style={{ width: 180, height: 180 }} />
      </div>

      <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 flex flex-col justify-center">
        <ReactECharts option={barOption} style={{ width: "100%", height: 120 }} />
      </div>

      <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 flex flex-col justify-center gap-4">
        <div className="text-center">
          <p className="text-3xl font-bold text-white">
            {champion.avg_placement.toFixed(2)}
          </p>
          <p className="text-xs text-gray-400 mt-1">Avg Placement</p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div>
            <p className="text-lg font-semibold text-gold">
              {champion.total_games.toLocaleString()}
            </p>
            <p className="text-[10px] text-gray-500">Games</p>
          </div>
          <div>
            <p className="text-lg font-semibold text-teal">
              {champion.wins.toLocaleString()}
            </p>
            <p className="text-[10px] text-gray-500">Wins</p>
          </div>
        </div>
      </div>
    </div>
  );
}
