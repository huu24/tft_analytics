import { useState, useMemo } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import type { PlayerChampionStats } from "@/types/player";
import { getChampionDisplayName } from "@/utils/displayNames";

interface ChampionTableProps {
  champions: PlayerChampionStats[];
  onChampionClick?: (championId: string) => void;
}

type SortKey = keyof Pick<
  PlayerChampionStats,
  "total_games" | "top4_rate" | "win_rate" | "avg_placement"
>;

function rowColor(winRate: number): string {
  if (winRate >= 0.25) return "bg-teal/10";
  if (winRate >= 0.15) return "bg-dark-700";
  return "bg-red-900/10";
}

export default function ChampionTable({ champions, onChampionClick }: ChampionTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("total_games");
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(() => {
    return [...champions].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      return asc ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
  }, [champions, sortKey, asc]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setAsc(!asc);
    } else {
      setSortKey(key);
      setAsc(false);
    }
  };

  const SortIcon = ({ col }: { col: SortKey }) =>
    sortKey === col ? (
      asc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
    ) : (
      <span className="w-3 h-3" />
    );

  const columns: { key: SortKey; label: string }[] = [
    { key: "total_games", label: "Games" },
    { key: "top4_rate", label: "Top 4 Rate" },
    { key: "win_rate", label: "Win Rate" },
    { key: "avg_placement", label: "Avg Placement" },
  ];

  return (
    <div className="bg-dark-700 border border-dark-600 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-dark-600">
        <h3 className="text-sm font-semibold text-gold">Champion Stats</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] table-fixed text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-400 uppercase border-b border-dark-600">
              <th className="w-[38%] px-4 py-2.5 font-medium">Champion</th>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-2.5 font-medium cursor-pointer hover:text-white transition-colors"
                  onClick={() => handleSort(col.key)}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    <SortIcon col={col.key} />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((c) => (
              <tr
                key={c.champion_id}
                onClick={() => onChampionClick?.(c.champion_id)}
                className={`${rowColor(c.win_rate)} border-b border-dark-600/50 hover:bg-dark-600/50 transition-colors ${onChampionClick ? "cursor-pointer" : ""}`}
              >
                <td className="px-4 py-2.5 text-white font-medium">
                  <span
                    className="text-truncate-safe block"
                  >
                    {c.display_name || getChampionDisplayName(c.champion_id)}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-gray-300">{c.total_games}</td>
                <td className="px-4 py-2.5 text-teal">
                  {(c.top4_rate * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-2.5 text-gold">
                  {(c.win_rate * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-2.5 text-gray-300">
                  {c.avg_placement.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
