import { useState, useMemo } from "react";
import { Search, Package } from "lucide-react";
import type { ItemSummary } from "@/types/items";

interface ItemGridProps {
  items: ItemSummary[];
  selectedItem: string | null;
  onSelect: (itemName: string) => void;
}

export default function ItemGrid({ items, selectedItem, onSelect }: ItemGridProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return items.filter((i) => i.item_name.toLowerCase().includes(q));
  }, [items, search]);

  return (
    <div className="space-y-3">
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
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 max-h-[calc(100vh-220px)] overflow-y-auto pr-1">
        {filtered.map((item) => {
          const isSelected = selectedItem === item.item_name;
          return (
            <button
              key={item.item_name}
              onClick={() => onSelect(item.item_name)}
              className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border transition-all text-center
                ${
                  isSelected
                    ? "border-gold bg-gold/10 shadow-lg shadow-gold/10"
                    : "border-dark-600 bg-dark-800 hover:border-gold/40 hover:bg-dark-700"
                }`}
            >
              <Package className={`w-6 h-6 ${isSelected ? "text-gold" : "text-gray-500"}`} />
              <span className={`text-xs font-medium leading-tight ${isSelected ? "text-gold" : "text-gray-300"}`}>
                {item.item_name}
              </span>
              <span className="text-[10px] text-gray-500">
                {item.avg_placement.toFixed(1)} avg
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
