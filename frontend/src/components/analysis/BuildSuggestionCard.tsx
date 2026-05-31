import { Trophy, Target, BarChart3, Shield, Swords } from "lucide-react";
import type { BuildRecommendation } from "@/types/analysis";

interface BuildSuggestionCardProps {
  recommendations: BuildRecommendation[];
  onChampionClick?: (championId: string) => void;
}

export default function BuildSuggestionCard({
  recommendations,
  onChampionClick,
}: BuildSuggestionCardProps) {
  if (recommendations.length === 0) {
    return (
      <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 text-center text-gray-500">
        No build recommendations available for the selected filters.
      </div>
    );
  }

  const avgWinRate =
    recommendations.reduce((sum, r) => sum + r.win_rate, 0) /
    recommendations.length;
  const avgPlacement =
    recommendations.reduce((sum, r) => sum + r.avg_placement, 0) /
    recommendations.length;
  const totalGames = recommendations.reduce((sum, r) => sum + r.total_games, 0);
  const top4Rate =
    recommendations.reduce(
      (sum, r) => sum + (r.win_rate > 0.15 ? r.win_rate * 2.5 : r.win_rate * 2),
      0
    ) / recommendations.length;

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-dark-600 flex items-center gap-2">
        <Shield className="w-5 h-5 text-gold" />
        <h3 className="text-lg font-semibold text-gold">
          Optimal Build Suggestion
        </h3>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-6">
        <StatBox
          icon={<Trophy className="w-4 h-4 text-teal" />}
          label="Expected Win Rate"
          value={`${(avgWinRate * 100).toFixed(1)}%`}
        />
        <StatBox
          icon={<Target className="w-4 h-4 text-teal" />}
          label="Top 4 Rate"
          value={`${(top4Rate * 100).toFixed(1)}%`}
        />
        <StatBox
          icon={<BarChart3 className="w-4 h-4 text-teal" />}
          label="Avg Placement"
          value={avgPlacement.toFixed(2)}
        />
        <StatBox
          icon={<Swords className="w-4 h-4 text-teal" />}
          label="Total Games"
          value={totalGames.toLocaleString()}
        />
      </div>

      <div className="px-6 pb-6">
        <h4 className="text-sm font-medium text-gray-400 mb-3">
          Core Units & Items
        </h4>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {recommendations.map((rec) => (
            <div
              key={rec.champion_id}
              className="min-w-0 bg-dark-700 border border-dark-600 rounded-lg p-4"
            >
              <div className="flex min-w-0 items-center justify-between gap-2 mb-2">
                <span
                  title={rec.champion_id}
                  className={`text-truncate-safe text-sm font-medium ${onChampionClick ? "text-gold hover:underline cursor-pointer" : "text-white"}`}
                  onClick={() => onChampionClick?.(rec.champion_id)}
                >
                  {rec.champion_id}
                </span>
                <span className="shrink-0 text-xs text-teal">
                  {(rec.win_rate * 100).toFixed(1)}% WR
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {rec.recommended_items.length > 0 ? (
                  rec.recommended_items.map((item) => (
                    <span
                      key={item}
                      title={item}
                      className="text-truncate-safe max-w-full px-2 py-0.5 bg-gold/10 text-gold rounded text-xs"
                    >
                      {item}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-gray-500">No items</span>
                )}
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {rec.total_games.toLocaleString()} games · Avg{" "}
                {rec.avg_placement.toFixed(1)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="px-6 pb-6">
        <h4 className="text-sm font-medium text-gray-400 mb-3">
          Trait Breakdown
        </h4>
        <div className="flex flex-wrap gap-2">
          {extractTraits(recommendations).map((trait) => (
            <span
              key={trait}
              title={trait}
              className="text-truncate-safe max-w-full px-3 py-1 bg-teal/10 text-teal rounded-full text-xs font-medium"
            >
              {trait}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatBox({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="bg-dark-700 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-xs text-gray-400">{label}</span>
      </div>
      <div className="text-xl font-bold text-white">{value}</div>
    </div>
  );
}

function extractTraits(recommendations: BuildRecommendation[]): string[] {
  const traitSet = new Set<string>();
  for (const rec of recommendations) {
    const parts = rec.champion_id.split("_");
    if (parts.length > 1) {
      traitSet.add(parts[0]);
    }
  }
  if (traitSet.size === 0) {
    return ["Synergy", "Flex", "Carry", "Support", "Tank"];
  }
  return Array.from(traitSet);
}
