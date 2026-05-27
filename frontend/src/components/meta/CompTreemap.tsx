import ReactECharts from "echarts-for-react";
import type { CompSummary } from "@/types/composition";

interface CompTreemapProps {
  comps: CompSummary[];
  onSelect: (comp: CompSummary) => void;
}

function getWinRateColor(wr: number): string {
  if (wr >= 0.25) return "#0ac8b9";
  if (wr >= 0.2) return "#4ade80";
  if (wr >= 0.15) return "#c8aa6e";
  if (wr >= 0.1) return "#f59e0b";
  return "#ef4444";
}

export default function CompTreemap({ comps, onSelect }: CompTreemapProps) {
  const totalGames = comps.reduce((s, c) => s + c.total_games, 0);

  const data = comps.map((c) => ({
    name: c.comp_signature,
    value: c.total_games,
    pickRate: totalGames > 0 ? c.total_games / totalGames : 0,
    winRate: c.win_rate,
    itemStyle: {
      color: getWinRateColor(c.win_rate),
      borderColor: "#0a0e1a",
      borderWidth: 2,
    },
    _comp: c,
  }));

  const option = {
    tooltip: {
      formatter: (info: { data: (typeof data)[0] }) => {
        const d = info.data;
        return `
          <div style="padding:4px 0">
            <strong style="color:#c8aa6e">${d.name}</strong><br/>
            <span style="color:#999">Pick Rate:</span> ${(d.pickRate * 100).toFixed(1)}%<br/>
            <span style="color:#999">Win Rate:</span> ${(d.winRate * 100).toFixed(1)}%<br/>
            <span style="color:#999">Games:</span> ${d.value.toLocaleString()}
          </div>
        `;
      },
    },
    series: [
      {
        type: "treemap",
        data,
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: {
          show: true,
          formatter: "{b}",
          fontSize: 11,
          color: "#fff",
        },
        upperLabel: { show: false },
        levels: [
          {
            itemStyle: { borderColor: "#0a0e1a", borderWidth: 3, gapWidth: 3 },
          },
        ],
      },
    ],
  };

  const onEvents = {
    click: (params: { data: (typeof data)[0] }) => {
      if (params.data?._comp) {
        onSelect(params.data._comp);
      }
    },
  };

  return (
    <div className="rounded-xl bg-dark-800 border border-dark-600 p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">
        Composition Map
      </h3>
      <ReactECharts
        option={option}
        style={{ height: 320 }}
        onEvents={onEvents}
        opts={{ renderer: "canvas" }}
      />
    </div>
  );
}
