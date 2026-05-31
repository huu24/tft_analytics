import { useState, useMemo } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import type { ChampionItemCombo, BuildSortField, SortDirection } from "@/types/champion";

interface BuildStatsTableProps {
  builds: ChampionItemCombo[];
}

const columns: { key: BuildSortField; label: string; align: string }[] = [
  { key: "item_name", label: "Build", align: "text-left" },
  { key: "total_games", label: "Games", align: "text-right" },
  { key: "win_rate", label: "Win Rate", align: "text-right" },
  { key: "top4_rate", label: "Top 4 Rate", align: "text-right" },
  { key: "avg_placement", label: "Avg Place", align: "text-right" },
];

export default function BuildStatsTable({ builds }: BuildStatsTableProps) {
  const [sortField, setSortField] = useState<BuildSortField>("total_games");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");

  const handleSort = (field: BuildSortField) => {
    if (field === sortField) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir(field === "avg_placement" || field === "item_name" ? "asc" : "desc");
    }
  };

  const sorted = useMemo(() => {
    const copy = [...builds];
    copy.sort((a, b) => {
      let av: number | string;
      let bv: number | string;
      if (sortField === "top4_rate") {
        av = a.total_games > 0 ? a.top4_count / a.total_games : 0;
        bv = b.total_games > 0 ? b.top4_count / b.total_games : 0;
      } else {
        av = a[sortField] as number | string;
        bv = b[sortField] as number | string;
      }
      if (typeof av === "string" && typeof bv === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortDir === "asc" ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
    return copy;
  }, [builds, sortField, sortDir]);

  if (builds.length === 0) {
    return <p className="text-gray-500 text-center py-8">No build data available.</p>;
  }

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-dark-600">
        <h3 className="text-sm font-semibold text-gold">Per-Build Stats</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] table-fixed text-sm">
          <thead>
            <tr className="border-b border-dark-600">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={`px-4 py-2.5 cursor-pointer select-none hover:text-gold transition-colors text-gray-400 font-medium ${col.align}`}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {sortField === col.key &&
                      (sortDir === "asc" ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      ))}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => {
              const top4Rate =
                row.total_games > 0 ? row.top4_count / row.total_games : 0;
              return (
                <tr
                  key={row.item_name}
                  className="border-b border-dark-700 hover:bg-dark-700 transition-colors"
                >
                  <td className="px-4 py-2 text-white font-medium">
                    <span title={row.item_name} className="text-truncate-safe block">
                      {row.item_name}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right text-gray-300">
                    {row.total_games.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span className={row.win_rate >= 0.5 ? "text-teal" : "text-gray-300"}>
                      {(row.win_rate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span className={top4Rate >= 0.5 ? "text-gold" : "text-gray-300"}>
                      {(top4Rate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <span
                      className={
                        row.avg_placement <= 3.5
                          ? "text-teal"
                          : row.avg_placement <= 4.5
                            ? "text-gold"
                            : "text-gray-300"
                      }
                    >
                      {row.avg_placement.toFixed(2)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
