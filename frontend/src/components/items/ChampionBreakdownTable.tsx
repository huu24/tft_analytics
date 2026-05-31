import type { ItemChampionCombo } from "@/types/items";
import { getDisplayName } from "@/data/championTraits";

interface ChampionBreakdownTableProps {
  champions: ItemChampionCombo[];
  onChampionClick?: (championId: string) => void;
}

export default function ChampionBreakdownTable({ champions, onChampionClick }: ChampionBreakdownTableProps) {
  const sorted = [...champions].sort((a, b) => b.total_games - a.total_games);

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4">
      <h4 className="text-sm font-semibold text-gold mb-3">Per-Champion Breakdown</h4>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] table-fixed text-sm">
          <thead>
            <tr className="border-b border-dark-600">
              <th className="w-[38%] text-left py-2 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Champion</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Games</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Win Rate</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Top 4</th>
              <th className="text-right py-2 px-3 text-gray-500 font-medium text-xs uppercase tracking-wider">Avg Place</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((c) => {
              const top4Rate = c.total_games > 0 ? (c.top4_count / c.total_games) * 100 : 0;
              return (
                <tr
                  key={c.champion_id}
                  onClick={() => onChampionClick?.(c.champion_id)}
                  className="border-b border-dark-700 hover:bg-dark-700/50 transition-colors cursor-pointer"
                >
                  <td className="py-2 px-3 text-gray-200 font-medium">
                    <span
                      className="text-truncate-safe block"
                    >
                      {getDisplayName(c.champion_id)}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right text-gray-300">{c.total_games.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right">
                    <span className={c.win_rate >= 0.15 ? "text-teal" : "text-gray-300"}>
                      {(c.win_rate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span className={top4Rate >= 50 ? "text-teal" : "text-gray-300"}>
                      {top4Rate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span className={c.avg_placement <= 3.5 ? "text-gold" : c.avg_placement >= 5.5 ? "text-red-400" : "text-gray-300"}>
                      {c.avg_placement.toFixed(2)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <p className="text-center text-gray-500 text-sm py-6">No champion data available</p>
        )}
      </div>
    </div>
  );
}
