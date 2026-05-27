export interface ItemSummary {
  item_name: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  most_common_champion: string | null;
  last_updated: string | null;
}

export interface ItemDetail extends ItemSummary {}

export interface ItemChampionCombo {
  champion_id: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
}

export interface ItemListResponse {
  items: ItemSummary[];
  total: number;
}
