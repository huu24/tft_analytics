import ReactECharts from "echarts-for-react";
import type { PlayerStats } from "@/types/player";

interface ItemRadarProps {
  stats: PlayerStats;
}

export default function ItemRadar({ stats }: ItemRadarProps) {
  const option = {
    radar: {
      indicator: [
        { name: "Build Accuracy", max: 1 },
        { name: "Meta Adherence", max: 1 },
        { name: "Flexibility", max: 1 },
      ],
      shape: "polygon",
      splitNumber: 4,
      axisName: {
        color: "#9ca3af",
        fontSize: 11,
      },
      splitLine: {
        lineStyle: { color: "#1c2640" },
      },
      splitArea: {
        areaStyle: { color: ["transparent", "#1c264020"] },
      },
      axisLine: {
        lineStyle: { color: "#1c2640" },
      },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: [stats.item_accuracy, stats.meta_score, stats.flex_score],
            name: "Player",
            areaStyle: { color: "rgba(200, 170, 110, 0.2)" },
            lineStyle: { color: "#c8aa6e", width: 2 },
            itemStyle: { color: "#c8aa6e" },
          },
        ],
      },
    ],
  };

  return (
    <div className="bg-dark-700 border border-dark-600 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">Item Accuracy</h3>
      <ReactECharts
        option={option}
        style={{ height: 280 }}
        opts={{ renderer: "svg" }}
      />
    </div>
  );
}
