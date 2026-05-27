import ReactECharts from "echarts-for-react";
import type { PlayerTraitStats } from "@/types/player";

interface TraitTreemapProps {
  traits: PlayerTraitStats[];
}

export default function TraitTreemap({ traits }: TraitTreemapProps) {
  const option = {
    tooltip: {
      formatter: (params: { data: { name: string; value: number; winRate: number } }) => {
        const d = params.data;
        return `<b>${d.name}</b><br/>Games: ${d.value}<br/>Win Rate: ${(d.winRate * 100).toFixed(1)}%`;
      },
    },
    series: [
      {
        type: "treemap",
        width: "100%",
        height: "100%",
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: {
          show: true,
          formatter: "{b}",
          fontSize: 11,
          color: "#fff",
        },
        itemStyle: {
          borderColor: "#0a0e1a",
          borderWidth: 2,
          gapWidth: 2,
        },
        levels: [
          {
            itemStyle: {
              borderColor: "#0a0e1a",
              borderWidth: 4,
              gapWidth: 4,
            },
          },
        ],
        data: traits.map((t) => ({
          name: t.trait_name,
          value: t.total_games,
          winRate: t.win_rate,
          itemStyle: {
            color: winRateColor(t.win_rate),
          },
        })),
      },
    ],
  };

  return (
    <div className="bg-dark-700 border border-dark-600 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">Trait Usage</h3>
      <ReactECharts
        option={option}
        style={{ height: 280 }}
        opts={{ renderer: "svg" }}
      />
    </div>
  );
}

function winRateColor(wr: number): string {
  if (wr >= 0.3) return "#0ac8b9";
  if (wr >= 0.2) return "#1a8a7f";
  if (wr >= 0.125) return "#c8aa6e";
  return "#8b4513";
}
