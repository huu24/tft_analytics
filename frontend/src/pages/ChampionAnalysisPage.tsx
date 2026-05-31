import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useApi } from "@/hooks/useApi";
import type {
  ChampionSummary,
  ChampionDetail,
  ChampionItemCombo,
  ChampionTraitCombo,
  ChampionListResponse,
} from "@/types/champion";
import ChampionGrid from "@/components/champions/ChampionGrid";
import ChampionStatsOverview from "@/components/champions/ChampionStatsOverview";
import ItemHeatmap from "@/components/champions/ItemHeatmap";
import TraitComboChart from "@/components/champions/TraitComboChart";
import BuildStatsTable from "@/components/champions/BuildStatsTable";
import SynergyGraph from "@/components/champions/SynergyGraph";
import Breadcrumb from "@/components/Breadcrumb";
import BackButton from "@/components/BackButton";

export default function ChampionAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<ChampionSummary | null>(null);

  const { data: listData, loading: listLoading } = useApi<ChampionListResponse>(
    "/champions"
  );

  const champions = listData?.items ?? [];

  useEffect(() => {
    const urlChamp = searchParams.get("champion");
    if (urlChamp && champions.length > 0) {
      const match = champions.find((c) => c.champion_id === urlChamp);
      if (match && match.champion_id !== selected?.champion_id) {
        setSelected(match);
      }
    }
  }, [searchParams, champions]);

  const handleSelect = (champ: ChampionSummary) => {
    setSelected(champ);
    setSearchParams({ champion: champ.champion_id });
  };

  const handleItemClick = (itemName: string) => {
    navigate(`/items?item=${encodeURIComponent(itemName)}`);
  };

  const { data: detail, loading: detailLoading } = useApi<ChampionDetail>(
    selected ? `/champions/${selected.champion_id}` : "",
    { enabled: !!selected }
  );

  const { data: items } = useApi<ChampionItemCombo[]>(
    selected ? `/champions/${selected.champion_id}/items` : "",
    { enabled: !!selected }
  );

  const { data: traits } = useApi<ChampionTraitCombo[]>(
    selected ? `/champions/${selected.champion_id}/traits` : "",
    { enabled: !!selected }
  );

  const championName = detail?.display_name || detail?.champion_id || "";

  return (
    <div className="space-y-6">
      <div className="flex min-w-0 items-center justify-between gap-3">
        <Breadcrumb
          items={[
            { label: "Champions" },
            ...(selected ? [{ label: championName || selected.champion_id }] : []),
          ]}
        />
        {selected && <BackButton />}
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gold mb-1">Champion Analysis</h2>
        <p className="text-sm text-gray-400">
          Select a champion to view detailed statistics, optimal items, trait combos, and synergies.
        </p>
      </div>

      <ChampionGrid
        champions={champions}
        selectedId={selected?.champion_id ?? null}
        onSelect={handleSelect}
        loading={listLoading}
      />

      {selected && detailLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="w-6 h-6 border-2 border-gold border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {detail && (
        <div className="space-y-6">
          <ChampionStatsOverview champion={detail} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ItemHeatmap items={items ?? []} onItemClick={handleItemClick} />
            <TraitComboChart traits={traits ?? []} />
          </div>

          <BuildStatsTable builds={items ?? []} />

          <SynergyGraph traits={traits ?? []} championName={championName} />
        </div>
      )}
    </div>
  );
}
