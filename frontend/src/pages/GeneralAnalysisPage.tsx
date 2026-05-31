import { useState, useCallback, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Search, BarChart3, Sparkles, Crosshair } from "lucide-react";
import apiClient from "@/api/client";
import { useApi } from "@/hooks/useApi";
import MultiSelectDropdown from "@/components/analysis/MultiSelectDropdown";
import BuildSuggestionCard from "@/components/analysis/BuildSuggestionCard";
import BuildVariationsRadar from "@/components/analysis/BuildVariationsRadar";
import SynergyMatrix from "@/components/analysis/SynergyMatrix";
import TraitActivationChart from "@/components/analysis/TraitActivationChart";
import Breadcrumb from "@/components/Breadcrumb";
import type {
  BuildResponse,
  ChampionListResponse,
  ItemListResponse,
  ChampionTraitCombo,
} from "@/types/analysis";
import { getChampionDisplayName, getItemDisplayName } from "@/utils/displayNames";

export default function GeneralAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [selectedChampions, setSelectedChampions] = useState<string[]>(() =>
    searchParams.getAll("champion")
  );
  const [selectedItems, setSelectedItems] = useState<string[]>(() =>
    searchParams.getAll("item")
  );
  const [buildData, setBuildData] = useState<BuildResponse | null>(null);
  const [championTraits, setChampionTraits] = useState<
    Map<string, ChampionTraitCombo[]>
  >(new Map());
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const champs = searchParams.getAll("champion");
    const items = searchParams.getAll("item");
    if (JSON.stringify(champs) !== JSON.stringify(selectedChampions)) {
      setSelectedChampions(champs);
    }
    if (JSON.stringify(items) !== JSON.stringify(selectedItems)) {
      setSelectedItems(items);
    }
  }, [searchParams]);

  const updateUrlParams = useCallback(
    (champions: string[], items: string[]) => {
      const params = new URLSearchParams();
      champions.forEach((c) => params.append("champion", c));
      items.forEach((i) => params.append("item", i));
      setSearchParams(params, { replace: true });
    },
    [setSearchParams]
  );

  const handleChampionsChange = (vals: string[]) => {
    setSelectedChampions(vals);
    updateUrlParams(vals, selectedItems);
  };

  const handleItemsChange = (vals: string[]) => {
    setSelectedItems(vals);
    updateUrlParams(selectedChampions, vals);
  };

  const handleChampionClick = (championId: string) => {
    navigate(`/champions?champion=${encodeURIComponent(championId)}`);
  };
  const { data: champData, loading: champLoading } =
    useApi<ChampionListResponse>("/champions?limit=200");
  const { data: itemData, loading: itemLoading } =
    useApi<ItemListResponse>("/items?limit=200");

  const championOptions = (champData?.items ?? []).map((c) => ({
    value: c.champion_id,
    label: c.display_name || getChampionDisplayName(c.champion_id),
  }));

  const itemOptions = (itemData?.items ?? []).map((i) => ({
    value: i.item_name,
    label: getItemDisplayName(i.item_name),
  }));

  const handleAnalyze = useCallback(async () => {
    if (selectedChampions.length === 0 && selectedItems.length === 0) return;
    setAnalyzing(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      selectedChampions.forEach((c) => params.append("champ_ids", c));
      selectedItems.forEach((i) => params.append("item_names", i));

      const traitPromises = selectedChampions.map(async (champId) => {
        try {
          const res = await apiClient.get<ChampionTraitCombo[]>(
            `/champions/${champId}/traits`
          );
          return { champId, traits: res.data };
        } catch {
          return { champId, traits: [] as ChampionTraitCombo[] };
        }
      });

      const [buildRes, ...traitResults] = await Promise.all([
        apiClient.get<BuildResponse>(`/analysis/build?${params.toString()}`),
        ...traitPromises,
      ]);

      setBuildData(buildRes.data);

      const traitMap = new Map<string, ChampionTraitCombo[]>();
      for (const result of traitResults) {
        traitMap.set(result.champId, result.traits);
      }
      setChampionTraits(traitMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }, [selectedChampions, selectedItems]);

  const hasResults = buildData && buildData.recommendations.length > 0;
  const hasFilters =
    selectedChampions.length > 0 || selectedItems.length > 0;

  return (
    <div className="space-y-6">
      <Breadcrumb items={[{ label: "General Analysis" }]} />

      <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Crosshair className="w-5 h-5 text-gold" />
          <h3 className="text-lg font-semibold text-gold">Analysis Filters</h3>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-[1fr_1fr_auto]">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">
              Champions
            </label>
            <MultiSelectDropdown
              options={championOptions}
              selected={selectedChampions}
              onChange={handleChampionsChange}
              placeholder="Select champions..."
              loading={champLoading}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Items</label>
            <MultiSelectDropdown
              options={itemOptions}
              selected={selectedItems}
              onChange={handleItemsChange}
              placeholder="Select items..."
              loading={itemLoading}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleAnalyze}
              disabled={!hasFilters || analyzing}
              className="w-full lg:w-auto px-6 py-2.5 bg-gold/90 hover:bg-gold text-dark-900 font-semibold rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {analyzing ? (
                <>
                  <span className="w-4 h-4 border-2 border-dark-900/30 border-t-dark-900 rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Analyze
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 px-4 py-2 bg-red-900/20 border border-red-800/50 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

      </div>

      {!hasResults && !analyzing && <EmptyState hasFilters={hasFilters} />}

      {hasResults && buildData && (
        <div className="space-y-6">
          <BuildSuggestionCard recommendations={buildData.recommendations} onChampionClick={handleChampionClick} />

          <div className="grid gap-6 lg:grid-cols-2">
            <BuildVariationsRadar
              recommendations={buildData.recommendations}
            />
            <SynergyMatrix
              recommendations={buildData.recommendations}
              selectedChampions={selectedChampions}
            />
          </div>

          {championTraits.size > 0 && (
            <TraitActivationChart championTraits={championTraits} />
          )}
        </div>
      )}
    </div>
  );
}

function EmptyState({ hasFilters }: { hasFilters: boolean }) {
  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-12 text-center">
      <div className="flex justify-center mb-4">
        <div className="w-16 h-16 rounded-full bg-gold/10 flex items-center justify-center">
          {hasFilters ? (
            <Sparkles className="w-8 h-8 text-gold" />
          ) : (
            <BarChart3 className="w-8 h-8 text-gold" />
          )}
        </div>
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">
        {hasFilters
          ? "Ready to Analyze"
          : "Select Champions or Items to Begin"}
      </h3>
      <p className="text-gray-400 text-sm max-w-md mx-auto">
        {hasFilters
          ? "Click the Analyze button to discover optimal builds, synergies, and trait activations based on your selections."
          : "Use the filter panel above to select champions and items. We'll provide build suggestions, synergy analysis, and trait breakdowns tailored to your picks."}
      </p>
      {!hasFilters && (
        <div className="mt-6 flex justify-center gap-6 text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-gold" />
            Build Suggestions
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-teal" />
            Synergy Matrix
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-gold" />
            Trait Activation
          </div>
        </div>
      )}
    </div>
  );
}
