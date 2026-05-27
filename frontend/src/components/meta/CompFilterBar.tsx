import type { SortField } from "@/types/composition";

interface CompFilterBarProps {
  minGames: number;
  onMinGamesChange: (value: number) => void;
  sortBy: SortField;
  onSortByChange: (value: SortField) => void;
}

const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: "win_rate", label: "Win Rate" },
  { value: "avg_placement", label: "Avg Placement" },
  { value: "top4_rate", label: "Top 4 Rate" },
];

export default function CompFilterBar({
  minGames,
  onMinGamesChange,
  sortBy,
  onSortByChange,
}: CompFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-6 p-4 rounded-xl bg-dark-800 border border-dark-600">
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-400 uppercase tracking-wider">
          Min Games
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={10}
            max={500}
            step={10}
            value={minGames}
            onChange={(e) => onMinGamesChange(Number(e.target.value))}
            className="w-32 accent-gold"
          />
          <span className="text-sm text-gold font-semibold w-10 text-right">
            {minGames}
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-400 uppercase tracking-wider">
          Sort By
        </label>
        <select
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value as SortField)}
          className="bg-dark-700 border border-dark-600 text-white text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-gold"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
