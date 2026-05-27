import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { SunburstChart } from "echarts/charts";
import { TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { ItemChampionCombo } from "@/types/items";
import { getDisplayName, getChampionTrait } from "@/data/championTraits";

echarts.use([SunburstChart, TooltipComponent, CanvasRenderer]);

interface BestChampionsSunburstProps {
  champions: ItemChampionCombo[];
}

interface SunburstNode {
  name: string;
  value?: number;
  itemStyle?: { color: string };
  children?: SunburstNode[];
}

function placementColor(placement: number): string {
  if (placement <= 2.5) return "#0ac8b9";
  if (placement <= 3.5) return "#4ade80";
  if (placement <= 4.5) return "#c8aa6e";
  if (placement <= 5.5) return "#f97316";
  return "#ef4444";
}

export default function BestChampionsSunburst({ champions }: BestChampionsSunburstProps) {
  const traitMap = new Map<string, ItemChampionCombo[]>();

  for (const c of champions) {
    const trait = getChampionTrait(c.champion_id);
    const list = traitMap.get(trait) ?? [];
    list.push(c);
    traitMap.set(trait, list);
  }

  const data: SunburstNode[] = Array.from(traitMap.entries()).map(([trait, champs]) => {
    const avgPlacement = champs.reduce((s, c) => s + c.avg_placement, 0) / champs.length;
    return {
      name: trait,
      itemStyle: { color: placementColor(avgPlacement) },
      children: champs.map((c) => ({
        name: getDisplayName(c.champion_id),
        value: c.total_games,
        itemStyle: { color: placementColor(c.avg_placement) },
      })),
    };
  });

  const option = {
    tooltip: {
      trigger: "item",
      formatter: (params: { data: SunburstNode; treePathInfo: Array<{ name: string }> }) => {
        const d = params.data;
        if (d.children) return `<b>${d.name}</b>`;
        return `<b>${d.name}</b><br/>Games: ${d.value}`;
      },
    },
    series: {
      type: "sunburst",
      data,
      radius: ["15%", "90%"],
      sort: undefined,
      emphasis: { focus: "ancestor" },
      levels: [
        {},
        {
          r0: "15%",
          r: "50%",
          itemStyle: { borderWidth: 2, borderColor: "#0a0e1a" },
          label: { rotate: "tangential", fontSize: 10, color: "#e5e7eb" },
        },
        {
          r0: "50%",
          r: "90%",
          itemStyle: { borderWidth: 1, borderColor: "#0a0e1a" },
          label: { rotate: "tangential", fontSize: 9, color: "#9ca3af" },
        },
      ],
    },
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <h4 className="text-sm font-semibold text-gold mb-2">Best Champions</h4>
      <ReactEChartsCore
        echarts={echarts}
        option={option}
        style={{ height: 340 }}
        notMerge
      />
    </div>
  );
}
