import { Trophy, Target, BarChart3, Gamepad2 } from "lucide-react";
import type { ItemDetail } from "@/types/items";

interface ItemStatsOverviewProps {
  item: ItemDetail;
}

export default function ItemStatsOverview({ item }: ItemStatsOverviewProps) {
  const winRate = item.total_games > 0 ? (item.wins / item.total_games) * 100 : 0;
  const top4Rate = item.total_games > 0 ? (item.top4_count / item.total_games) * 100 : 0;

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
      <h3 title={item.item_name} className="line-clamp-2 text-lg font-bold text-gold mb-4">
        {item.item_name}
      </h3>
      <div className="flex items-center justify-center gap-8">
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Trophy className="w-5 h-5 text-gold" />
            <span className="text-4xl font-bold text-gold">{item.avg_placement.toFixed(2)}</span>
          </div>
          <span className="text-xs text-gray-500 uppercase tracking-wider">Avg Placement</span>
        </div>
        <div className="h-16 w-px bg-dark-600" />
        <div className="grid grid-cols-1 gap-3">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-teal" />
            <div>
              <span className="text-sm font-semibold text-white">{winRate.toFixed(1)}%</span>
              <span className="text-xs text-gray-500 ml-1">Win Rate</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-teal" />
            <div>
              <span className="text-sm font-semibold text-white">{top4Rate.toFixed(1)}%</span>
              <span className="text-xs text-gray-500 ml-1">Top 4 Rate</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Gamepad2 className="w-4 h-4 text-gray-400" />
            <div>
              <span className="text-sm font-semibold text-white">{item.total_games.toLocaleString()}</span>
              <span className="text-xs text-gray-500 ml-1">Games</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
