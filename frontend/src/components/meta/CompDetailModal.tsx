import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { X } from "lucide-react";
import apiClient from "@/api/client";
import type { CompSummary, CompDetail, CompTrait } from "@/types/composition";

interface CompDetailModalProps {
  comp: CompSummary | null;
  onClose: () => void;
  onUnitClick?: (championId: string) => void;
}

function buildSunburstOption(traits: CompTrait[]) {
  const traitGroups: Record<string, CompTrait[]> = {};
  for (const t of traits) {
    const key = t.name;
    if (!traitGroups[key]) traitGroups[key] = [];
    traitGroups[key].push(t);
  }

  const children = Object.entries(traitGroups).map(([name, group]) => ({
    name,
    value: group.length,
    children: group.map((t) => ({
      name: `Tier ${t.tier_current}`,
      value: 1,
    })),
  }));

  return {
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c}",
    },
    series: [
      {
        type: "sunburst",
        data: children,
        radius: ["15%", "90%"],
        sort: undefined,
        emphasis: { focus: "ancestor" },
        itemStyle: {
          borderColor: "#0a0e1a",
          borderWidth: 2,
        },
        levels: [
          {},
          {
            r0: "15%",
            r: "55%",
            itemStyle: { borderWidth: 2 },
            label: { rotate: "tangential", fontSize: 10, color: "#fff" },
          },
          {
            r0: "55%",
            r: "90%",
            label: { align: "right", fontSize: 9, color: "#ccc" },
            itemStyle: { borderWidth: 1 },
          },
        ],
        color: ["#c8aa6e", "#0ac8b9", "#4ade80", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"],
      },
    ],
  };
}

function buildUnitBarOption(units: string[]) {
  const counts: Record<string, number> = {};
  for (const u of units) {
    counts[u] = (counts[u] || 0) + 1;
  }
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8);

  return {
    tooltip: { trigger: "axis" as const },
    grid: { left: 120, right: 20, top: 10, bottom: 20 },
    xAxis: {
      type: "value" as const,
      axisLabel: { color: "#666" },
      splitLine: { lineStyle: { color: "#1c2640" } },
    },
    yAxis: {
      type: "category" as const,
      data: sorted.map(([name]) => name),
      axisLabel: { color: "#ccc", fontSize: 11, width: 110, overflow: "truncate" },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: sorted.map(([, count]) => count),
        itemStyle: {
          color: "#0ac8b9",
          borderRadius: [0, 4, 4, 0],
        },
        barWidth: 16,
      },
    ],
  };
}

export default function CompDetailModal({ comp, onClose, onUnitClick }: CompDetailModalProps) {
  const [detail, setDetail] = useState<CompDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!comp) {
      setDetail(null);
      return;
    }

    setLoading(true);
    apiClient
      .get<CompDetail>(`/compositions/${encodeURIComponent(comp.comp_signature)}`)
      .then((res) => setDetail(res.data))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [comp]);

  if (!comp) return null;

  const display = detail ?? comp;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl bg-dark-800 border border-dark-600 shadow-2xl">
        <div className="sticky top-0 z-10 flex min-w-0 items-center justify-between gap-3 p-5 bg-dark-800 border-b border-dark-600">
          <h3
            title={display.comp_signature}
            className="line-clamp-2 min-w-0 text-lg font-bold text-gold"
          >
            {display.comp_signature}
          </h3>
          <button
            onClick={onClose}
            className="shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-dark-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Win Rate", value: `${(display.win_rate * 100).toFixed(1)}%`, color: "text-teal" },
              { label: "Top 4 Rate", value: `${(display.top4_rate * 100).toFixed(1)}%`, color: "text-green-400" },
              { label: "Avg Placement", value: display.avg_placement.toFixed(2), color: "text-gold" },
              { label: "Total Games", value: display.total_games.toLocaleString(), color: "text-white" },
            ].map((stat) => (
              <div key={stat.label} className="p-3 rounded-lg bg-dark-700 text-center">
                <div className="text-xs text-gray-400 mb-1">{stat.label}</div>
                <div className={`text-lg font-bold ${stat.color}`}>{stat.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-xl bg-dark-700 p-4">
              <h4 className="text-sm font-semibold text-gold mb-2">Trait Breakdown</h4>
              {display.traits.length > 0 ? (
                <ReactECharts
                  option={buildSunburstOption(display.traits)}
                  style={{ height: 260 }}
                  opts={{ renderer: "canvas" }}
                />
              ) : (
                <p className="text-xs text-gray-500 text-center py-8">No trait data</p>
              )}
            </div>

            <div className="rounded-xl bg-dark-700 p-4">
              <h4 className="text-sm font-semibold text-gold mb-2">Core Units</h4>
              {display.core_units.length > 0 ? (
                <>
                  <ReactECharts
                    option={buildUnitBarOption(display.core_units)}
                    style={{ height: 260 }}
                    opts={{ renderer: "canvas" }}
                  />
                  {onUnitClick && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {[...new Set(display.core_units)].map((unit) => (
                        <button
                          key={unit}
                          onClick={() => onUnitClick(unit)}
                          title={unit}
                          className="text-truncate-safe max-w-[10rem] text-xs px-2 py-0.5 rounded bg-gold/10 text-gold hover:bg-gold/20 transition-colors"
                        >
                          {unit}
                        </button>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <p className="text-xs text-gray-500 text-center py-8">No unit data</p>
              )}
            </div>
          </div>

          {detail?.core_items && detail.core_items.length > 0 && (
            <div className="rounded-xl bg-dark-700 p-4">
              <h4 className="text-sm font-semibold text-gold mb-3">Core Items</h4>
              <div className="flex flex-wrap gap-2">
                {detail.core_items.map((item) => (
                  <span
                    key={item}
                    title={item}
                    className="text-truncate-safe max-w-full text-xs px-2.5 py-1 rounded-lg bg-dark-600 text-gray-300 border border-dark-600"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center text-xs text-gray-500 py-2">Loading details...</div>
          )}
        </div>
      </div>
    </div>
  );
}
