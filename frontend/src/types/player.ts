export interface PlayerStats {
  puuid: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
  top4_rate: number;
  meta_score: number;
  flex_score: number;
  item_accuracy: number;
  last_updated: string | null;
}

export interface PlayerChampionStats {
  champion_id: string;
  display_name: string | null;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
  top4_rate: number;
}

export interface PlayerTraitStats {
  trait_name: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
}

export interface PlayerItemStats {
  item_name: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
}

export interface PlayerSearchResult {
  puuid: string;
  total_games: number;
  win_rate: number;
  avg_placement: number;
}
