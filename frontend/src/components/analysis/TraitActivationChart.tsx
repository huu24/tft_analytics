import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { BarChart } from "echarts/charts";
import {
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { ChampionTraitCombo } from "@/types/analysis";

echarts.use([
  BarChart,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer,
]);

interface TraitActivationChartProps {
  championTraits: Map<string, ChampionTraitCombo[]>;
}

const TIER_COLORS: Record<string, string> = {
  Bronze: "#cd7f32",
  Silver: "#c0c0c0",
  Gold: "#c8aa6e",
  Platinum: "#0ac8b9",
  Prismatic: "#e84393",
};

const TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Prismatic"];

export default function TraitActivationChart({
  championTraits,
}: TraitActivationChartProps) {
  if (championTraits.size === 0) return null;

  const traitMap = new Map<
    string,
    Record<string, { count: number; champions: string[] }>
  >();

  for (const [champId, traits] of championTraits) {
    for (const t of traits) {
      if (!traitMap.has(t.trait_name)) {
        traitMap.set(t.trait_name, {});
      }
      const tiers = traitMap.get(t.trait_name)!;
      const tier = getTier(t.win_rate);
      if (!tiers[tier]) {
        tiers[tier] = { count: 0, champions: [] };
      }
      tiers[tier].count += 1;
      tiers[tier].champions.push(champId);
    }
  }

  const traitNames = Array.from(traitMap.keys()).slice(0, 15);

  const seriesData = TIERS.map((tier) => ({
    name: tier,
    type: "bar" as const,
    stack: "total",
    emphasis: { focus: "series" as const },
    itemStyle: { color: TIER_COLORS[tier] },
    data: traitNames.map((name) => {
      const tiers = traitMap.get(name) ?? {};
      return tiers[tier]?.count ?? 0;
    }),
  }));

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "shadow" as const },
      backgroundColor: "#1c2640",
      borderColor: "#c8aa6e",
      textStyle: { color: "#e0e0e0" },
    },
    legend: {
      data: TIERS,
      bottom: 0,
      textStyle: { color: "#9ca3af", fontSize: 11 },
      itemWidth: 12,
      itemHeight: 8,
    },
    grid: { top: 10, right: 20, bottom: 40, left: 120 },
    xAxis: {
      type: "value" as const,
      axisLabel: { color: "#9ca3af" },
      axisLine: { lineStyle: { color: "#1c2640" } },
      splitLine: { lineStyle: { color: "rgba(200,170,110,0.08)" } },
    },
    yAxis: {
      type: "category" as const,
      data: traitNames,
      axisLabel: { color: "#9ca3af", fontSize: 11, width: 110, overflow: "truncate" },
      axisLine: { lineStyle: { color: "#1c2640" } },
    },
    series: seriesData,
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gold mb-4">
        Trait Activation Tiers
      </h3>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        style={{ height: Math.max(280, traitNames.length * 35 + 80) }}
        notMerge
      />
    </div>
  );
}

function getTier(winRate: number): string {
  if (winRate >= 0.25) return "Prismatic";
  if (winRate >= 0.18) return "Platinum";
  if (winRate >= 0.13) return "Gold";
  if (winRate >= 0.08) return "Silver";
  return "Bronze";
}
