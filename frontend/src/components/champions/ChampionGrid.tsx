import { useState, useMemo } from "react";
import { Search, Swords } from "lucide-react";
import type { ChampionSummary, ChampionSortField } from "@/types/champion";

interface ChampionGridProps {
  champions: ChampionSummary[];
  selectedId: string | null;
  onSelect: (champion: ChampionSummary) => void;
  loading: boolean;
}

const sortOptions: { value: ChampionSortField; label: string }[] = [
  { value: "total_games", label: "Games" },
  { value: "win_rate", label: "Win Rate" },
  { value: "top4_rate", label: "Top 4" },
  { value: "avg_placement", label: "Avg Place" },
  { value: "pick_rate", label: "Pick Rate" },
];

export default function ChampionGrid({
  champions,
  selectedId,
  onSelect,
  loading,
}: ChampionGridProps) {
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<ChampionSortField>("total_games");

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    let result = champions.filter(
      (c) =>
        c.champion_id.toLowerCase().includes(q) ||
        (c.display_name?.toLowerCase().includes(q) ?? false)
    );
    result.sort((a, b) => {
      if (sortBy === "avg_placement") return a.avg_placement - b.avg_placement;
      return (b[sortBy] as number) - (a[sortBy] as number);
    });
    return result;
  }, [champions, search, sortBy]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search champions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gold"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as ChampionSortField)}
          className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm text-white focus:outline-none focus:border-gold"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              Sort: {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {filtered.map((champ) => (
          <button
            key={champ.champion_id}
            onClick={() => onSelect(champ)}
            className={`flex min-w-0 flex-col items-center gap-2 p-3 rounded-lg border transition-all hover:border-gold hover:bg-dark-700 ${
              selectedId === champ.champion_id
                ? "border-gold bg-dark-700 ring-1 ring-gold/30"
                : "border-dark-600 bg-dark-800"
            }`}
          >
            <div className="w-12 h-12 shrink-0 rounded-full bg-dark-600 flex items-center justify-center">
              <Swords className="w-5 h-5 text-gold" />
            </div>
            <span
              title={champ.display_name || champ.champion_id}
              className="text-truncate-safe w-full px-1 text-center text-xs font-medium text-white"
            >
              {champ.display_name || champ.champion_id}
            </span>
            <div className="flex items-center gap-1 text-[10px]">
              <span className="text-teal">{(champ.win_rate * 100).toFixed(1)}%</span>
              <span className="text-gray-500">|</span>
              <span className="text-gray-400">{champ.total_games.toLocaleString()}</span>
            </div>
          </button>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-gray-500 py-8">No champions found.</p>
      )}
    </div>
  );
}
