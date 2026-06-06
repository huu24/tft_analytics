import { useState, useMemo } from "react";
import { Search, Package } from "lucide-react";
import type { ItemSummary } from "@/types/items";
import { getItemDisplayName } from "@/utils/displayNames";

interface ItemGridProps {
  items: ItemSummary[];
  selectedItem: string | null;
  onSelect: (itemName: string) => void;
}

type ItemSortField = "win_rate" | "top4_rate" | "total_games" | "avg_placement";

const SORT_OPTIONS: { value: ItemSortField; label: string }[] = [
  { value: "win_rate", label: "Win Rate" },
  { value: "top4_rate", label: "Top 4 Rate" },
  { value: "total_games", label: "Games" },
  { value: "avg_placement", label: "Avg Placement" },
];

function getRate(value: number, totalGames: number): number {
  return totalGames > 0 ? value / totalGames : 0;
}

function getMetricLabel(item: ItemSummary, sortBy: ItemSortField): string {
  if (sortBy === "win_rate") {
    return `${(getRate(item.wins, item.total_games) * 100).toFixed(1)}% win rate`;
  }
  if (sortBy === "top4_rate") {
    return `${(getRate(item.top4_count, item.total_games) * 100).toFixed(1)}% top 4`;
  }
  if (sortBy === "total_games") {
    return `${item.total_games.toLocaleString()} games`;
  }
  return `${item.avg_placement.toFixed(2)} avg place`;
}

export default function ItemGrid({ items, selectedItem, onSelect }: ItemGridProps) {
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<ItemSortField>("win_rate");
  const [minGames, setMinGames] = useState(50);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return items
      .filter((i) => i.total_games >= minGames)
      .filter((i) =>
        getItemDisplayName(i.item_name).toLowerCase().includes(q)
      )
      .sort((a, b) => {
        if (sortBy === "avg_placement") {
          return a.avg_placement - b.avg_placement;
        }
        if (sortBy === "win_rate") {
          return getRate(b.wins, b.total_games) - getRate(a.wins, a.total_games);
        }
        if (sortBy === "top4_rate") {
          return getRate(b.top4_count, b.total_games) - getRate(a.top4_count, a.total_games);
        }
        return b.total_games - a.total_games;
      });
  }, [items, minGames, search, sortBy]);

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search items..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-gold/50"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as ItemSortField)}
          className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm text-white focus:outline-none focus:border-gold"
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              Sort: {option.label}
            </option>
          ))}
        </select>
        <label className="flex items-center justify-between gap-3 text-xs text-gray-400">
          Minimum sample size
          <select
            value={minGames}
            onChange={(e) => setMinGames(Number(e.target.value))}
            className="px-2 py-1.5 bg-dark-700 border border-dark-600 rounded text-xs text-white focus:outline-none focus:border-gold"
          >
            {[0, 10, 50, 100, 500].map((value) => (
              <option key={value} value={value}>{value.toLocaleString()} games</option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 max-h-[calc(100vh-220px)] overflow-y-auto pr-1">
        {filtered.map((item) => {
          const isSelected = selectedItem === item.item_name;
          return (
            <button
              key={item.item_name}
              onClick={() => onSelect(item.item_name)}
              className={`flex min-w-0 flex-col items-center gap-1.5 p-3 rounded-lg border transition-all text-center
                ${
                  isSelected
                    ? "border-gold bg-gold/10 shadow-lg shadow-gold/10"
                    : "border-dark-600 bg-dark-800 hover:border-gold/40 hover:bg-dark-700"
                }`}
            >
              <Package className={`w-6 h-6 shrink-0 ${isSelected ? "text-gold" : "text-gray-500"}`} />
              <span
                className={`line-clamp-2 min-h-[2rem] w-full text-xs font-medium leading-tight ${isSelected ? "text-gold" : "text-gray-300"}`}
              >
                {getItemDisplayName(item.item_name)}
              </span>
              <span className="text-[10px] text-gray-500">
                {getMetricLabel(item, sortBy)}
              </span>
            </button>
          );
        })}
      </div>
      {filtered.length === 0 && (
        <p className="text-center text-gray-500 text-sm py-4">No items found</p>
      )}
    </div>
  );
}
