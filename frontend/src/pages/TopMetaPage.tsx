import { useState, useMemo, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useApi } from "@/hooks/useApi";
import type { CompListResponse, CompSummary, SortField } from "@/types/composition";
import CompFilterBar from "@/components/meta/CompFilterBar";
import CompTreemap from "@/components/meta/CompTreemap";
import CompTierList from "@/components/meta/CompTierList";
import CompDetailModal from "@/components/meta/CompDetailModal";
import MetaTrendsChart from "@/components/meta/MetaTrendsChart";
import Breadcrumb from "@/components/Breadcrumb";
import { Loader2, AlertTriangle } from "lucide-react";

export default function TopMetaPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [minGames, setMinGames] = useState(() => {
    const v = searchParams.get("min_games");
    return v ? Number(v) : 50;
  });
  const [sortBy, setSortBy] = useState<SortField>(() => {
    return (searchParams.get("sort_by") as SortField) || "win_rate";
  });
  const [selectedComp, setSelectedComp] = useState<CompSummary | null>(null);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (minGames !== 50) params.min_games = String(minGames);
    if (sortBy !== "win_rate") params.sort_by = sortBy;
    setSearchParams(params, { replace: true });
  }, [minGames, sortBy]);

  const handleUnitClick = (championId: string) => {
    setSelectedComp(null);
    navigate(`/champions?champion=${encodeURIComponent(championId)}`);
  };

  const { data, loading, error } = useApi<CompListResponse>(
    `/compositions?min_games=${minGames}&sort_by=${sortBy}&limit=100&offset=0`
  );

  const comps = useMemo(() => data?.items ?? [], [data]);

  return (
    <div className="space-y-6">
      <Breadcrumb items={[{ label: "Top Meta" }]} />

      <CompFilterBar
        minGames={minGames}
        onMinGamesChange={setMinGames}
        sortBy={sortBy}
        onSortByChange={setSortBy}
      />

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-gold animate-spin" />
          <span className="ml-3 text-gray-400 text-sm">Loading compositions...</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-900/20 border border-red-800/40">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {!loading && !error && comps.length === 0 && (
        <div className="text-center py-20 text-gray-500 text-sm">
          No compositions found. Try lowering the minimum games filter.
        </div>
      )}

      {!loading && !error && comps.length > 0 && (
        <>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <CompTreemap comps={comps} onSelect={setSelectedComp} />
            <MetaTrendsChart comps={comps} />
          </div>

          <div>
            <h3 className="text-lg font-bold text-gold mb-4">Tier List</h3>
            <CompTierList comps={comps} onCompClick={setSelectedComp} />
          </div>
        </>
      )}

      <CompDetailModal comp={selectedComp} onClose={() => setSelectedComp(null)} onUnitClick={handleUnitClick} />
    </div>
  );
}
