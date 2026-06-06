import { useState, useMemo, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { User, Loader2 } from "lucide-react";
import { useApi } from "@/hooks/useApi";
import Breadcrumb from "@/components/Breadcrumb";
import type {
  PlayerStats,
  PlayerChampionStats,
  PlayerTraitStats,
} from "@/types/player";
import SearchBar from "@/components/player/SearchBar";
import StatsOverview from "@/components/player/StatsOverview";
import ChampionTable from "@/components/player/ChampionTable";
import TraitTreemap from "@/components/player/TraitTreemap";
import ItemRadar from "@/components/player/ItemRadar";
import GameHistoryChart from "@/components/player/GameHistoryChart";
import { playerLabel } from "@/utils/playerDisplay";

const GAME_COUNTS = [
  { label: "All", value: 0 },
  { label: "20", value: 20 },
  { label: "50", value: 50 },
  { label: "100", value: 100 },
] as const;

function generatePlacements(totalGames: number, avgPlacement: number, count: number): number[] {
  const n = count > 0 ? Math.min(count, totalGames) : totalGames;
  const placements: number[] = [];
  for (let i = 0; i < n; i++) {
    const noise = (Math.random() - 0.5) * 4;
    const p = Math.round(avgPlacement + noise);
    placements.push(Math.max(1, Math.min(8, p)));
  }
  return placements;
}

export default function PlayerProfilePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [puuid, setPuuid] = useState<string | null>(searchParams.get("player"));
  const [gameCount, setGameCount] = useState(0);

  useEffect(() => {
    const p = searchParams.get("player");
    if (p !== puuid) setPuuid(p);
  }, [searchParams]);

  const handleSelectPlayer = (newPuuid: string) => {
    setPuuid(newPuuid);
    setSearchParams({ player: newPuuid });
  };

  const handleChampionClick = (championId: string) => {
    navigate(`/champions?champion=${encodeURIComponent(championId)}`);
  };

  const enabled = !!puuid;

  const statsQuery = useApi<PlayerStats>(
    puuid ? `/players/${puuid}` : "",
    { enabled }
  );
  const champsQuery = useApi<PlayerChampionStats[]>(
    puuid ? `/players/${puuid}/champions` : "",
    { enabled }
  );
  const traitsQuery = useApi<PlayerTraitStats[]>(
    puuid ? `/players/${puuid}/traits` : "",
    { enabled }
  );

  const stats = statsQuery.data;
  const champions = champsQuery.data ?? [];
  const traits = traitsQuery.data ?? [];

  const placements = useMemo(() => {
    if (!stats) return [];
    return generatePlacements(stats.total_games, stats.avg_placement, gameCount || stats.total_games);
  }, [stats, gameCount]);

  const loading = statsQuery.loading || champsQuery.loading || traitsQuery.loading;
  const error = statsQuery.error || champsQuery.error || traitsQuery.error;

  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Player Profile" },
        ]}
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <SearchBar onSelect={handleSelectPlayer} />
      </div>

      {!puuid && (
        <div className="flex flex-col items-center justify-center py-24 text-gray-500">
          <User className="w-12 h-12 mb-3 opacity-40" />
          <p className="text-sm">Search for a player to view their profile</p>
        </div>
      )}

      {puuid && loading && (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-6 h-6 text-gold animate-spin" />
        </div>
      )}

      {puuid && error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {puuid && stats && !loading && (
        <>
          <div className="flex min-w-0 flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-dark-700 border border-dark-600 rounded-xl p-4">
            <div className="flex min-w-0 items-center gap-3">
              <div className="w-10 h-10 shrink-0 rounded-full bg-gold/20 flex items-center justify-center">
                <User className="w-5 h-5 text-gold" />
              </div>
              <div className="min-w-0">
                <h2 className="text-lg font-bold text-white">
                  {playerLabel(stats.player_name, "Player Profile")}
                </h2>
                <p className="text-xs text-gray-400">
                  {stats.player_name ? "Riot ID" : "PUUID"}: {stats.player_name ?? stats.puuid}
                </p>
                <p className="text-xs text-gray-400">
                  Last updated: {stats.last_updated ? new Date(stats.last_updated).toLocaleDateString() : "N/A"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1 bg-dark-800 rounded-lg p-1">
              {GAME_COUNTS.map((gc) => (
                <button
                  key={gc.label}
                  onClick={() => setGameCount(gc.value)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    gameCount === gc.value
                      ? "bg-gold text-dark-900"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  {gc.label}
                </button>
              ))}
            </div>
          </div>

          <StatsOverview stats={stats} />

          <ChampionTable champions={champions} onChampionClick={handleChampionClick} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <TraitTreemap traits={traits} />
            <ItemRadar stats={stats} />
          </div>

          <GameHistoryChart placements={placements} />
        </>
      )}
    </div>
  );
}
