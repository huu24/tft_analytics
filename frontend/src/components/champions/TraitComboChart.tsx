import ReactECharts from "echarts-for-react";
import type { ChampionTraitCombo } from "@/types/champion";
import { getTraitDisplayName } from "@/utils/displayNames";

interface TraitComboChartProps {
  traits: ChampionTraitCombo[];
}

export default function TraitComboChart({ traits }: TraitComboChartProps) {
  const sorted = [...traits].sort((a, b) => a.avg_placement - b.avg_placement).slice(0, 12);
  const labels = sorted.map((t) => getTraitDisplayName(t.trait_name));
  const values = sorted.map((t) => +t.avg_placement.toFixed(2));
  const games = sorted.map((t) => t.total_games);

  const option = {
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "shadow" as const },
      formatter: (params: Array<{ name: string; value: number; dataIndex: number }>) => {
        const p = params[0];
        return `${p.name}<br/>Avg Placement: <b>${p.value}</b><br/>Games: ${games[p.dataIndex].toLocaleString()}`;
      },
    },
    grid: { left: 130, right: 40, top: 10, bottom: 20 },
    xAxis: {
      type: "value" as const,
      min: 1,
      max: 8,
      inverse: true,
      axisLabel: { color: "#9ca3af", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1c2640" } },
      axisLine: { show: false },
    },
    yAxis: {
      type: "category" as const,
      data: labels,
      inverse: true,
      axisLabel: { color: "#d1d5db", fontSize: 10, width: 110, overflow: "truncate" as const },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        type: "bar",
        data: values.map((v) => ({
          value: v,
          itemStyle: {
            color: {
              type: "linear" as const,
              x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: "#0ac8b9" },
                { offset: 1, color: "#c8aa6e" },
              ],
            },
            borderRadius: [0, 4, 4, 0],
          },
        })),
        barWidth: 16,
        label: {
          show: true,
          position: "insideRight" as const,
          color: "#fff",
          fontSize: 10,
          fontWeight: "bold" as const,
        },
      },
    ],
  };

  if (sorted.length === 0) {
    return <p className="text-gray-500 text-center py-8">No trait data available.</p>;
  }

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">Best Trait Combos</h3>
      <ReactECharts
        option={option}
        style={{ width: "100%", height: Math.max(280, sorted.length * 30 + 40) }}
      />
    </div>
  );
}
