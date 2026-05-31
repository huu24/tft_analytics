import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { BarChart } from "echarts/charts";
import { TooltipComponent, GridComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { ItemSummary } from "@/types/items";
import { getItemDisplayName } from "@/utils/displayNames";

echarts.use([BarChart, TooltipComponent, GridComponent, CanvasRenderer]);

interface SimilarItemsBarProps {
  allItems: ItemSummary[];
  currentItem: string;
  currentPlacement: number;
}

export default function SimilarItemsBar({ allItems, currentItem, currentPlacement }: SimilarItemsBarProps) {
  const similar = allItems
    .filter((i) => i.item_name !== currentItem)
    .map((i) => ({ ...i, diff: Math.abs(i.avg_placement - currentPlacement) }))
    .sort((a, b) => a.diff - b.diff)
    .slice(0, 10);

  const names = similar.map((i) => getItemDisplayName(i.item_name));
  const placements = similar.map((i) => i.avg_placement);

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "#0f1524",
      borderColor: "#1c2640",
      textStyle: { color: "#e5e7eb" },
    },
    grid: { left: 130, right: 30, top: 10, bottom: 20 },
    xAxis: {
      type: "value",
      min: 1,
      max: 8,
      inverse: true,
      axisLabel: { color: "#9ca3af", fontSize: 10 },
      axisLine: { lineStyle: { color: "#1c2640" } },
      splitLine: { lineStyle: { color: "#1c2640" } },
    },
    yAxis: {
      type: "category",
      data: names,
      inverse: true,
      axisLabel: { color: "#9ca3af", fontSize: 10, width: 120, overflow: "truncate" },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#1c2640" } },
    },
    series: {
      type: "bar",
      data: placements.map((v) => ({
        value: v,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: "#0ac8b9" },
            { offset: 1, color: "#c8aa6e" },
          ]),
        },
      })),
      barWidth: 16,
      label: {
        show: true,
        position: "insideLeft",
        color: "#0a0e1a",
        fontSize: 10,
        fontWeight: "bold",
        formatter: (p: { value: number }) => p.value.toFixed(2),
      },
    },
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <h4 className="text-sm font-semibold text-gold mb-2">Similar Items (by Avg Placement)</h4>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        style={{ height: Math.max(240, similar.length * 32 + 40) }}
        notMerge
      />
    </div>
  );
}
