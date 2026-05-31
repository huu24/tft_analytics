import ReactECharts from "echarts-for-react";
import type { ChampionItemCombo } from "@/types/champion";
import { getItemDisplayName } from "@/utils/displayNames";

interface ItemHeatmapProps {
  items: ChampionItemCombo[];
  onItemClick?: (itemName: string) => void;
}

const metrics = ["Win Rate", "Top 4 Rate", "Avg Place", "Games"] as const;

export default function ItemHeatmap({ items, onItemClick }: ItemHeatmapProps) {
  const sorted = [...items].sort((a, b) => b.win_rate - a.win_rate).slice(0, 15);
  const yLabels = sorted.map((i) => getItemDisplayName(i.item_name));

  const data: [number, number, number][] = [];
  sorted.forEach((item, yIdx) => {
    data.push([0, yIdx, +(item.win_rate * 100).toFixed(1)]);
    data.push([1, yIdx, +(item.top4_count / item.total_games * 100).toFixed(1)]);
    data.push([2, yIdx, +item.avg_placement.toFixed(2)]);
    data.push([3, yIdx, item.total_games]);
  });

  const option = {
    tooltip: {
      formatter: (params: { data: [number, number, number] }) => {
        const [x, y, val] = params.data;
        const metric = metrics[x];
        const item = yLabels[y];
        const suffix = x < 2 ? "%" : x === 2 ? "" : " games";
        return `${item}<br/>${metric}: <b>${val}${suffix}</b>`;
      },
    },
    grid: { left: 120, right: 40, top: 10, bottom: 40 },
    xAxis: {
      type: "category" as const,
      data: [...metrics],
      axisLabel: { color: "#9ca3af", fontSize: 10, rotate: 0 },
      axisTick: { show: false },
      axisLine: { show: false },
      splitArea: { show: false },
    },
    yAxis: {
      type: "category" as const,
      data: yLabels,
      axisLabel: { color: "#d1d5db", fontSize: 10, width: 100, overflow: "truncate" as const },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: false,
      orient: "horizontal",
      left: "center",
      bottom: -5,
      show: false,
      inRange: {
        color: ["#1c2640", "#0a5e56", "#0ac8b9", "#c8aa6e"],
      },
    },
    series: [
      {
        type: "heatmap",
        data,
        label: {
          show: true,
          color: "#fff",
          fontSize: 10,
          formatter: (params: { data: [number, number, number] }) => {
            const [x, , val] = params.data;
            if (x === 3) return val.toLocaleString();
            return String(val);
          },
        },
        itemStyle: { borderColor: "#0a0e1a", borderWidth: 2, borderRadius: 4 },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(200,170,110,0.5)" },
        },
      },
    ],
  };

  if (sorted.length === 0) {
    return <p className="text-gray-500 text-center py-8">No item data available.</p>;
  }

  const onEvents: Record<string, Function> = onItemClick
    ? {
        click: (params: { data: [number, number, number] }) => {
          const yIdx = params.data[1];
          const itemName = sorted[yIdx]?.item_name;
          if (itemName) onItemClick(itemName);
        },
      }
    : {};

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">Best Items Heatmap</h3>
      <ReactECharts
        option={option}
        style={{ width: "100%", height: Math.max(300, sorted.length * 32 + 60) }}
        onEvents={onEvents}
      />
    </div>
  );
}
