import ReactECharts from "echarts-for-react";
import type { CompSummary } from "@/types/composition";

interface MetaTrendsChartProps {
  comps: CompSummary[];
}

function shortLabel(label: string, max = 24): string {
  return label.length > max ? `${label.slice(0, max - 1)}...` : label;
}

export default function MetaTrendsChart({ comps }: MetaTrendsChartProps) {
  const sorted = [...comps]
    .filter((c) => c.last_updated)
    .sort((a, b) => (a.last_updated ?? "").localeCompare(b.last_updated ?? ""));

  const topComps = sorted.slice(0, 5);

  const dates = [...new Set(topComps.map((c) => c.last_updated!.split("T")[0]))];

  const winRateSeries = topComps.map((c) => ({
    name: c.comp_signature,
    type: "line" as const,
    smooth: true,
    symbol: "circle",
    symbolSize: 6,
    data: dates.map((d) => {
      const match = sorted.find(
        (s) => s.comp_signature === c.comp_signature && s.last_updated!.startsWith(d)
      );
      return match ? +(match.win_rate * 100).toFixed(2) : null;
    }),
  }));

  const pickRateSeries = topComps.map((c) => {
    const totalGames = sorted.reduce((s, s2) => s + s2.total_games, 0);
    return {
      name: `${c.comp_signature} (pick)`,
      type: "line" as const,
      smooth: true,
      symbol: "diamond",
      symbolSize: 5,
      lineStyle: { type: "dashed" as const },
      data: dates.map((d) => {
        const match = sorted.find(
          (s) => s.comp_signature === c.comp_signature && s.last_updated!.startsWith(d)
        );
        return match && totalGames > 0
          ? +((match.total_games / totalGames) * 100).toFixed(2)
          : null;
      }),
    };
  });

  const option = {
    tooltip: {
      trigger: "axis" as const,
      backgroundColor: "#0f1524",
      borderColor: "#1c2640",
      textStyle: { color: "#ccc", fontSize: 11 },
    },
    legend: {
      type: "scroll" as const,
      bottom: 0,
      textStyle: { color: "#999", fontSize: 10 },
      pageTextStyle: { color: "#999" },
      formatter: (name: string) => shortLabel(name),
    },
    grid: { left: 50, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: "category" as const,
      data: dates,
      axisLabel: { color: "#666", fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: "#1c2640" } },
    },
    yAxis: {
      type: "value" as const,
      axisLabel: { color: "#666", formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#1c2640" } },
    },
    color: ["#c8aa6e", "#0ac8b9", "#4ade80", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16", "#f97316"],
    series: [...winRateSeries, ...pickRateSeries],
  };

  return (
    <div className="rounded-xl bg-dark-800 border border-dark-600 p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">
        Meta Trends
        <span className="text-xs text-gray-500 font-normal ml-2">
          Win rate (solid) & pick rate (dashed) over time
        </span>
      </h3>
      {dates.length > 0 ? (
        <ReactECharts
          option={option}
          style={{ height: 320 }}
          opts={{ renderer: "canvas" }}
        />
      ) : (
        <div className="flex items-center justify-center h-[320px] text-gray-500 text-sm">
          No trend data available yet
        </div>
      )}
    </div>
  );
}
