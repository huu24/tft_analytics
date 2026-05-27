export interface BuildRecommendation {
  champion_id: string;
  recommended_items: string[];
  avg_placement: number;
  win_rate: number;
  total_games: number;
}

export interface BuildResponse {
  recommendations: BuildRecommendation[];
}

export interface MetaOverview {
  total_players: number;
  total_matches_analyzed: number;
  top_champions: MetaChampion[];
  top_compositions: MetaComposition[];
  top_items: MetaItem[];
}

export interface MetaChampion {
  champion_id: string;
  display_name?: string;
  win_rate: number;
  top4_rate: number;
  avg_placement: number;
  pick_rate: number;
  total_games: number;
}

export interface MetaComposition {
  composition_name: string;
  champions: string[];
  traits: string[];
  win_rate: number;
  top4_rate: number;
  avg_placement: number;
  pick_rate: number;
}

export interface MetaItem {
  item_name: string;
  win_rate: number;
  total_games: number;
  avg_placement: number;
}

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
}

export interface ItemSummary {
  item_name: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  most_common_champion: string | null;
}

export interface ChampionListResponse {
  items: ChampionSummary[];
  total: number;
}

export interface ItemListResponse {
  items: ItemSummary[];
  total: number;
}

export interface ChampionTraitCombo {
  trait_name: string;
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
}

export interface RadarDataPoint {
  name: string;
  values: number[];
}

export interface SynergyCell {
  championA: string;
  championB: string;
  score: number;
  sharedTraits: string[];
}

export interface TraitTier {
  trait_name: string;
  tier: string;
  champions: string[];
  active: boolean;
}

export interface AIRecommendation {
  champion_id: string;
  display_name: string;
  confidence: number;
}

export interface AIRecommendResponse {
  recommendations: AIRecommendation[];
  model_version: string;
}
