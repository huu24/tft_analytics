import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { RadarChart } from "echarts/charts";
import {
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { BuildRecommendation } from "@/types/analysis";
import { getChampionDisplayName } from "@/utils/displayNames";

echarts.use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer]);

interface BuildVariationsRadarProps {
  recommendations: BuildRecommendation[];
}

const AXES = [
  { name: "Win Rate", max: 100 },
  { name: "Top 4 Rate", max: 100 },
  { name: "Avg Placement", max: 8 },
  { name: "Pick Rate", max: 100 },
  { name: "Meta Score", max: 100 },
  { name: "Item Accuracy", max: 100 },
];

const COLORS = ["#c8aa6e", "#0ac8b9", "#e84393", "#6c5ce7", "#fdcb6e"];

function shortLabel(label: string, max = 22): string {
  return label.length > max ? `${label.slice(0, max - 1)}...` : label;
}

export default function BuildVariationsRadar({
  recommendations,
}: BuildVariationsRadarProps) {
  if (recommendations.length === 0) return null;

  const top = recommendations.slice(0, 5);

  const series = top.map((rec, i) => {
    const winRate = rec.win_rate * 100;
    const top4Rate = Math.min(rec.win_rate * 250, 100);
    const avgPlacement = rec.avg_placement;
    const pickRate = Math.min((rec.total_games / 5000) * 100, 100);
    const metaScore = Math.min(
      (rec.win_rate * 60 + (1 - rec.avg_placement / 8) * 40) * 1.5,
      100
    );
    const itemAccuracy = Math.min(
      rec.recommended_items.length * 25 + rec.win_rate * 30,
      100
    );

    return {
      name: getChampionDisplayName(rec.champion_id),
      value: [winRate, top4Rate, avgPlacement, pickRate, metaScore, itemAccuracy],
      lineStyle: { color: COLORS[i % COLORS.length], width: 2 },
      areaStyle: { color: COLORS[i % COLORS.length], opacity: 0.1 },
      itemStyle: { color: COLORS[i % COLORS.length] },
    };
  });

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item" as const,
      backgroundColor: "#1c2640",
      borderColor: "#c8aa6e",
      textStyle: { color: "#e0e0e0" },
    },
    legend: {
      type: "scroll" as const,
      data: top.map((r) => getChampionDisplayName(r.champion_id)),
      bottom: 0,
      textStyle: { color: "#9ca3af", fontSize: 11 },
      itemWidth: 12,
      itemHeight: 8,
      formatter: (name: string) => shortLabel(name),
    },
    radar: {
      indicator: AXES,
      shape: "polygon" as const,
      splitNumber: 4,
      axisName: { color: "#9ca3af", fontSize: 11 },
      splitLine: { lineStyle: { color: "rgba(200,170,110,0.15)" } },
      splitArea: { areaStyle: { color: ["transparent", "rgba(200,170,110,0.03)"] } },
      axisLine: { lineStyle: { color: "rgba(200,170,110,0.2)" } },
    },
    series: [
      {
        type: "radar" as const,
        data: series,
        symbol: "circle",
        symbolSize: 5,
      },
    ],
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gold mb-4">
        Build Variations Comparison
      </h3>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        style={{ height: 380 }}
        notMerge
      />
    </div>
  );
}
