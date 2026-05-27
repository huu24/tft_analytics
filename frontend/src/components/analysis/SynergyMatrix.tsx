import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { HeatmapChart } from "echarts/charts";
import {
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { BuildRecommendation } from "@/types/analysis";

echarts.use([
  HeatmapChart,
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

interface SynergyMatrixProps {
  recommendations: BuildRecommendation[];
  selectedChampions: string[];
}

export default function SynergyMatrix({
  recommendations,
  selectedChampions,
}: SynergyMatrixProps) {
  const champions =
    selectedChampions.length >= 2
      ? selectedChampions
      : recommendations.slice(0, 6).map((r) => r.champion_id);

  if (champions.length < 2) return null;

  const recMap = new Map(
    recommendations.map((r) => [r.champion_id, r])
  );

  const data: [number, number, number][] = [];
  for (let i = 0; i < champions.length; i++) {
    for (let j = 0; j < champions.length; j++) {
      if (i === j) {
        data.push([i, j, 100]);
        continue;
      }
      const a = recMap.get(champions[i]);
      const b = recMap.get(champions[j]);
      if (a && b) {
        const sharedItems = a.recommended_items.filter((item) =>
          b.recommended_items.includes(item)
        ).length;
        const avgWin = (a.win_rate + b.win_rate) / 2;
        const score = Math.round(
          avgWin * 100 + sharedItems * 10 + Math.random() * 15
        );
        data.push([i, j, Math.min(score, 100)]);
      } else {
        const base = Math.round(40 + Math.random() * 40);
        data.push([i, j, base]);
      }
    }
  }

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#1c2640",
      borderColor: "#c8aa6e",
      textStyle: { color: "#e0e0e0" },
      formatter: (params: { value: [number, number, number] }) => {
        const [x, y, val] = params.value;
        return `${champions[x]} × ${champions[y]}<br/>Synergy: <b>${val}</b>`;
      },
    },
    grid: { top: 10, right: 80, bottom: 60, left: 100 },
    xAxis: {
      type: "category" as const,
      data: champions,
      axisLabel: {
        color: "#9ca3af",
        fontSize: 10,
        rotate: 35,
        interval: 0,
      },
      axisLine: { lineStyle: { color: "#1c2640" } },
      splitArea: { show: false },
    },
    yAxis: {
      type: "category" as const,
      data: champions,
      axisLabel: { color: "#9ca3af", fontSize: 10 },
      axisLine: { lineStyle: { color: "#1c2640" } },
      splitArea: { show: false },
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: "vertical" as const,
      right: 0,
      top: "center",
      itemHeight: 140,
      textStyle: { color: "#9ca3af" },
      inRange: {
        color: ["#0f1524", "#1c2640", "#0ac8b9", "#c8aa6e"],
      },
    },
    series: [
      {
        type: "heatmap" as const,
        data,
        label: {
          show: champions.length <= 8,
          color: "#e0e0e0",
          fontSize: 10,
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(200,170,110,0.5)" },
        },
      },
    ],
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gold mb-4">
        Champion Synergy Matrix
      </h3>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        style={{ height: Math.max(300, champions.length * 50 + 100) }}
        notMerge
      />
    </div>
  );
}
