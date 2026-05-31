import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useApi } from "@/hooks/useApi";
import { Loader2, AlertCircle, Package } from "lucide-react";
import type { ItemListResponse, ItemDetail, ItemChampionCombo } from "@/types/items";
import ItemGrid from "@/components/items/ItemGrid";
import ItemStatsOverview from "@/components/items/ItemStatsOverview";
import BestChampionsSunburst from "@/components/items/BestChampionsSunburst";
import ChampionItemHeatmap from "@/components/items/ChampionItemHeatmap";
import SimilarItemsBar from "@/components/items/SimilarItemsBar";
import ChampionBreakdownTable from "@/components/items/ChampionBreakdownTable";
import Breadcrumb from "@/components/Breadcrumb";
import BackButton from "@/components/BackButton";
import { getItemDisplayName } from "@/utils/displayNames";

export default function ItemAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState<string | null>(
    searchParams.get("item")
  );

  useEffect(() => {
    const itemParam = searchParams.get("item");
    if (itemParam !== selectedItem) {
      setSelectedItem(itemParam);
    }
  }, [searchParams]);

  const handleSelectItem = (item: string) => {
    setSelectedItem(item);
    setSearchParams({ item });
  };

  const handleChampionClick = (championId: string) => {
    navigate(`/champions?champion=${encodeURIComponent(championId)}`);
  };

  const { data: listData, loading: listLoading, error: listError } = useApi<ItemListResponse>("/items");

  const { data: itemDetail, loading: detailLoading } = useApi<ItemDetail>(
    `/items/${encodeURIComponent(selectedItem ?? "")}`,
    { enabled: !!selectedItem },
  );

  const { data: champData, loading: champLoading } = useApi<ItemChampionCombo[]>(
    `/items/${encodeURIComponent(selectedItem ?? "")}/champions`,
    { enabled: !!selectedItem },
  );

  if (listLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-gold animate-spin" />
      </div>
    );
  }

  if (listError) {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-900/20 border border-red-800 rounded-lg">
        <AlertCircle className="w-5 h-5 text-red-400" />
        <span className="text-red-300 text-sm">{listError}</span>
      </div>
    );
  }

  const items = listData?.items ?? [];
  const champions = champData ?? [];
  const isLoadingDetail = detailLoading || champLoading;

  return (
    <div className="space-y-6">
      <div className="flex min-w-0 items-center justify-between gap-3">
        <Breadcrumb
          items={[
            { label: "Items" },
            ...(selectedItem ? [{ label: getItemDisplayName(selectedItem) }] : []),
          ]}
        />
        {selectedItem && <BackButton />}
      </div>

      <div className="flex items-center gap-3">
        <Package className="w-7 h-7 text-gold" />
        <h2 className="text-2xl font-bold text-gold">Item Analysis</h2>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr] gap-6">
        <div>
          <ItemGrid items={items} selectedItem={selectedItem} onSelect={handleSelectItem} />
        </div>

        <div className="space-y-6">
          {!selectedItem && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <Package className="w-12 h-12 mb-3 opacity-30" />
              <p className="text-sm">Select an item to view detailed analysis</p>
            </div>
          )}

          {selectedItem && isLoadingDetail && (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 text-gold animate-spin" />
            </div>
          )}

          {selectedItem && !isLoadingDetail && itemDetail && (
            <>
              <ItemStatsOverview item={itemDetail} />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {champions.length > 0 && <BestChampionsSunburst champions={champions} />}
                {champions.length > 0 && <ChampionItemHeatmap champions={champions} />}
              </div>

              <SimilarItemsBar
                allItems={items}
                currentItem={selectedItem}
                currentPlacement={itemDetail.avg_placement}
              />

              {champions.length > 0 && (
                <ChampionBreakdownTable champions={champions} onChampionClick={handleChampionClick} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
