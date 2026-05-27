import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { ChampionTraitCombo } from "@/types/champion";

interface SynergyGraphProps {
  traits: ChampionTraitCombo[];
  championName: string;
}

interface GraphNode {
  name: string;
  symbolSize: number;
  category: number;
  value: number;
}

interface GraphLink {
  source: string;
  target: string;
  value: number;
}

export default function SynergyGraph({ traits, championName }: SynergyGraphProps) {
  const { nodes, links } = useMemo(() => {
    const top = [...traits].sort((a, b) => b.total_games - a.total_games).slice(0, 12);
    if (top.length === 0) return { nodes: [] as GraphNode[], links: [] as GraphLink[] };

    const maxGames = Math.max(...top.map((t) => t.total_games));

    const n: GraphNode[] = [
      {
        name: championName,
        symbolSize: 50,
        category: 0,
        value: maxGames,
      },
    ];

    const l: GraphLink[] = [];

    top.forEach((trait, idx) => {
      const size = 15 + (trait.total_games / maxGames) * 30;
      n.push({
        name: trait.trait_name,
        symbolSize: size,
        category: 1,
        value: trait.total_games,
      });
      l.push({
        source: championName,
        target: trait.trait_name,
        value: trait.total_games,
      });

      for (let j = 0; j < idx; j++) {
        const coOccurrence = Math.min(trait.total_games, top[j].total_games) * 0.3;
        if (coOccurrence > maxGames * 0.1) {
          l.push({
            source: top[j].trait_name,
            target: trait.trait_name,
            value: Math.round(coOccurrence),
          });
        }
      }
    });

    return { nodes: n, links: l };
  }, [traits, championName]);

  if (nodes.length === 0) {
    return <p className="text-gray-500 text-center py-8">No synergy data available.</p>;
  }

  const option = {
    tooltip: {
      formatter: (params: { dataType: string; data: GraphNode; value: number }) => {
        if (params.dataType === "node") {
          return `${params.data.name}<br/>Games: ${params.value.toLocaleString()}`;
        }
        return "";
      },
    },
    series: [
      {
        type: "graph",
        layout: "force",
        roam: true,
        draggable: true,
        categories: [
          { name: "Champion", itemStyle: { color: "#c8aa6e" } },
          { name: "Trait", itemStyle: { color: "#0ac8b9" } },
        ],
        data: nodes.map((n) => ({
          ...n,
          label: {
            show: true,
            color: "#d1d5db",
            fontSize: 10,
          },
        })),
        links: links.map((l) => ({
          ...l,
          lineStyle: {
            color: "#1c2640",
            width: Math.max(1, l.value / (nodes[0]?.value || 1) * 5),
            curveness: 0.1,
          },
        })),
        force: {
          repulsion: 200,
          gravity: 0.1,
          edgeLength: [60, 150],
          friction: 0.6,
        },
        emphasis: {
          focus: "adjacency",
          lineStyle: { width: 3, color: "#c8aa6e" },
        },
      },
    ],
  };

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">Synergy Graph</h3>
      <ReactECharts option={option} style={{ width: "100%", height: 400 }} />
    </div>
  );
}
