import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { HeatmapChart } from "echarts/charts";
import {
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { ItemChampionCombo } from "@/types/items";
import { getDisplayName } from "@/data/championTraits";

echarts.use([HeatmapChart, TooltipComponent, GridComponent, VisualMapComponent, CanvasRenderer]);

interface ChampionItemHeatmapProps {
  champions: ItemChampionCombo[];
}

const METRICS = ["Win Rate", "Top 4 Rate", "Avg Place", "Games"] as const;

export default function ChampionItemHeatmap({ champions }: ChampionItemHeatmapProps) {
  const sorted = [...champions].sort((a, b) => b.total_games - a.total_games).slice(0, 15);
  const yLabels = sorted.map((c) => getDisplayName(c.champion_id));

  const maxGames = Math.max(...sorted.map((c) => c.total_games), 1);

  const data: [number, number, number][] = [];
  sorted.forEach((c, yi) => {
    const top4Rate = c.total_games > 0 ? (c.top4_count / c.total_games) * 100 : 0;
    const values = [
      c.win_rate * 100,
      top4Rate,
      c.avg_placement,
      (c.total_games / maxGames) * 100,
    ];
    values.forEach((v, xi) => {
      data.push([xi, yi, parseFloat(v.toFixed(1))]);
    });
  });

  const option = {
    tooltip: {
      position: "top",
      formatter: (params: { value: [number, number, number] }) => {
        const [xi, yi, val] = params.value;
        return `<b>${yLabels[yi]}</b><br/>${METRICS[xi]}: ${val}`;
      },
    },
    grid: { left: 120, right: 20, top: 10, bottom: 40 },
    xAxis: {
      type: "category",
      data: METRICS as unknown as string[],
      axisLabel: { color: "#9ca3af", fontSize: 10, width: 110, overflow: "truncate" },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#1c2640" } },
    },
    yAxis: {
      type: "category",
      data: yLabels,
      axisLabel: { color: "#9ca3af", fontSize: 10 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#1c2640" } },
    },
    visualMap: {
      min: 0,
      max: 100,
      show: false,
      inRange: {
        color: ["#1c2640", "#0ac8b9", "#c8aa6e"],
      },
    },
    series: {
      type: "heatmap",
      data,
      label: { show: true, color: "#e5e7eb", fontSize: 9 },
      itemStyle: { borderColor: "#0a0e1a", borderWidth: 2 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(200,170,110,0.5)" } },
    },
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <h4 className="text-sm font-semibold text-gold mb-2">Champion Metrics</h4>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        style={{ height: Math.max(260, sorted.length * 30 + 60) }}
        notMerge
      />
    </div>
  );
}
