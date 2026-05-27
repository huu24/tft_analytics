export interface ChampionSummary {
  champion_id: string;
  display_name: string | null;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
  top4_rate: number;
  pick_rate: number;
  last_updated: string | null;
}

export interface ChampionDetail extends ChampionSummary {}

export interface ChampionItemCombo {
  item_name: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
}

export interface ChampionTraitCombo {
  trait_name: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
}

export interface ChampionListResponse {
  items: ChampionSummary[];
  total: number;
}

export type ChampionSortField =
  | "total_games"
  | "win_rate"
  | "top4_rate"
  | "avg_placement"
  | "pick_rate";

export type BuildSortField =
  | "item_name"
  | "total_games"
  | "win_rate"
  | "top4_rate"
  | "avg_placement";

export type SortDirection = "asc" | "desc";
